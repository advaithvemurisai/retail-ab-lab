"""Everything the sidebar assumptions touch, in plain Python: no pandas, numpy or scipy.

The statistics that need customer-level data (Welch effects, bootstrap draws, segment effects)
are computed once; these functions price them under a set of assumptions. `analysis.analyze`,
the web API and the static data build all call them, so the decision logic exists once and the
API can run without the scientific stack.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from statistics import NormalDist

from .decision import Verdict, decide

NORMAL = NormalDist()
MINIMUM_PLANNED_LIFT = 0.05


@dataclass(frozen=True)
class Assumptions:
    variant: str = "any"
    gross_margin: float = 0.4
    contact_cost: float = 0.18
    minimum_roi: float = 0.0
    weekly_customers: int = 10_000
    use_cuped: bool = True
    alpha: float = 0.05


def break_even_lift(cost_per_contact: float, baseline_revenue: float, gross_margin: float) -> float:
    """Relative revenue lift at which gross profit from the lift equals contact cost."""
    if baseline_revenue <= 0 or gross_margin <= 0:
        return math.inf
    return cost_per_contact / (baseline_revenue * gross_margin)


def power_two_means(
    delta: float, sd_control: float, sd_treatment: float, n_control: int, n_treatment: int,
    alpha: float = 0.05,
) -> float:
    """Two-sided normal-approximation power to detect an absolute difference `delta`."""
    if n_control <= 0 or n_treatment <= 0:
        return 0.0
    se = math.sqrt(sd_control**2 / n_control + sd_treatment**2 / n_treatment)
    if se == 0:
        return 1.0
    z = NORMAL.inv_cdf(1 - alpha / 2)
    shift = abs(delta) / se
    return NORMAL.cdf(shift - z) + NORMAL.cdf(-shift - z)


def required_total_n(
    delta: float, sd: float, treatment_share: float = 0.5, alpha: float = 0.05,
    power: float = 0.8, sd_treatment: float | None = None,
) -> float:
    """Total customers needed across both arms for the given allocation.

    `sd` is the control SD; pass `sd_treatment` when the arms differ, since the variance of the
    difference is sd_c^2 / n_c + sd_t^2 / n_t and only collapses to one SD when they match.
    """
    if delta == 0:
        return math.inf
    sd_t = sd if sd_treatment is None else sd_treatment
    z = NORMAL.inv_cdf(1 - alpha / 2) + NORMAL.inv_cdf(power)
    variance = sd**2 / (1 - treatment_share) + sd_t**2 / treatment_share
    return math.ceil(z**2 * variance / delta**2)


def weeks_needed(total_n: float, weekly_customers: int) -> float:
    return math.inf if weekly_customers <= 0 else total_n / weekly_customers


def quantile(sorted_values: list[float], q: float) -> float:
    """Linear interpolation between order statistics, numpy's default method."""
    h = (len(sorted_values) - 1) * q
    lo = math.floor(h)
    hi = min(lo + 1, len(sorted_values) - 1)
    return sorted_values[lo] + (h - lo) * (sorted_values[hi] - sorted_values[lo])


def contribution_distribution(
    difference_draws, customers_contacted: int, gross_margin: float, contact_cost: float,
) -> dict[str, float]:
    """Scale per-customer lift draws to campaign contribution and summarise the downside."""
    contribution = sorted(
        (float(d) * gross_margin - contact_cost) * customers_contacted for d in difference_draws
    )
    return {
        "ci_low": quantile(contribution, 0.025),
        "ci_high": quantile(contribution, 0.975),
        "chance_of_loss": sum(value < 0 for value in contribution) / len(contribution),
    }


def price(
    revenue: dict, baseline_revenue: float, draws, segments: list[dict], a: Assumptions,
    validity_failed: bool,
) -> dict:
    """Price one campaign readout: P&L, contribution interval, power and the verdict.

    `revenue` is the Welch effect on the decision metric, `draws` its bootstrap draws and
    `segments` the BH-corrected effects by past-year spend band.
    """
    revenue_lift = revenue["difference"] / baseline_revenue
    contacted = revenue["n_treatment"]
    incremental = revenue["difference"] * contacted
    gross_profit = incremental * a.gross_margin
    marketing_cost = contacted * a.contact_cost
    contribution_value = gross_profit - marketing_cost
    economics = {
        "customers_contacted": contacted,
        "incremental_revenue": incremental,
        "gross_profit": gross_profit,
        "marketing_cost": marketing_cost,
        "contribution": contribution_value,
        "roi": contribution_value / marketing_cost if marketing_cost else math.inf,
    }
    contribution = contribution_distribution(draws, contacted, a.gross_margin, a.contact_cost)

    break_even = break_even_lift(a.contact_cost, baseline_revenue, a.gross_margin)
    planned_lift = break_even if 0 < break_even < math.inf else MINIMUM_PLANNED_LIFT
    delta = planned_lift * baseline_revenue
    power = power_two_means(
        delta, revenue["control_sd"], revenue["treatment_sd"], revenue["n_control"],
        revenue["n_treatment"], a.alpha,
    )
    n_total = revenue["n_control"] + revenue["n_treatment"]
    required_n = required_total_n(
        delta, revenue["control_sd"], revenue["n_treatment"] / n_total, a.alpha,
        sd_treatment=revenue["treatment_sd"],
    )
    shortfall = max(0.0, required_n - n_total)
    additional_weeks = math.ceil(shortfall / a.weekly_customers) if a.weekly_customers else 0
    segment_harm = any(row["significant"] and row["difference"] < 0 for row in segments)

    # The pooled e-mail is the prespecified primary; picking one creative after the fact is one of
    # two looks, so its verdict p-value is Bonferroni-adjusted for them.
    verdict_p = revenue["p_value"] if a.variant == "any" else min(1.0, revenue["p_value"] * 2)
    verdict: Verdict = decide(
        validity_failed=validity_failed,
        primary_lift=revenue_lift,
        primary_p=verdict_p,
        contribution_low=contribution["ci_low"],
        contribution_high=contribution["ci_high"],
        segment_harm=segment_harm,
        roi=economics["roi"],
        minimum_roi=a.minimum_roi,
        power=power,
        additional_weeks=additional_weeks,
        alpha=a.alpha,
        chance_of_loss=contribution["chance_of_loss"],
    )
    return {
        "baseline_revenue": float(baseline_revenue),
        "revenue_lift": float(revenue_lift),
        "revenue_lift_ci": (revenue["ci_low"] / baseline_revenue, revenue["ci_high"] / baseline_revenue),
        "economics": economics,
        "contribution": contribution,
        "break_even_lift": float(break_even),
        "planned_lift": float(planned_lift),
        "power": power,
        "required_n": float(required_n),
        "additional_weeks": additional_weeks,
        "verdict": verdict,
    }


def allocate(rows: list[dict], cap: int, require_significant: bool = False) -> list[dict]:
    """Fill a send cap with the highest-return segments that are expected to make money."""
    plan = sorted(rows, key=lambda row: row["profit_per_dollar"], reverse=True)
    remaining = cap
    result = []
    for row in plan:
        eligible = row["profit_per_dollar"] > 0 and (
            not require_significant or bool(row.get("significant", False))
        )
        amount = min(remaining, int(row["audience"])) if eligible else 0
        result.append({**row, "selected": amount > 0, "send_count": amount})
        remaining -= amount
    return result


def targeting_plan(
    segments: list[dict], audience: dict[str, int], a: Assumptions, cap: int,
    require_significant: bool = False,
) -> dict:
    """Segments priced per send, then allocated to the send budget."""
    rows = []
    for row in segments:
        profit = row["difference"] * a.gross_margin - a.contact_cost
        rows.append(
            {
                **row,
                "audience": int(audience[str(row["segment"])]),
                "profit_per_send": profit,
                "profit_low": row["ci_low"] * a.gross_margin - a.contact_cost,
                "profit_high": row["ci_high"] * a.gross_margin - a.contact_cost,
                "profit_per_dollar": profit / a.contact_cost if a.contact_cost else profit,
            }
        )
    plan = allocate(rows, cap, require_significant)
    return {
        "rows": plan,
        "customers": sum(row["send_count"] for row in plan),
        "planned": sum(row["send_count"] * row["profit_per_send"] for row in plan),
        "everyone": sum(row["audience"] * row["profit_per_send"] for row in plan),
        "audience": sum(row["audience"] for row in plan),
    }


def sector_table(
    sectors: list[dict], difference: float, baseline_revenue: float,
    lift_ci: tuple[float, float], contact_cost: float,
) -> list[dict]:
    """The same measured lift priced at each sector's gross margin."""
    low, high = lift_ci
    rows = []
    for sector in sectors:
        margin = sector["gross_margin"]
        needed = break_even_lift(contact_cost, baseline_revenue, margin)
        rows.append(
            {
                "sector": sector["sector"],
                "gross_margin": margin,
                "break_even_lift": needed,
                "contribution_per_10k": (difference * margin - contact_cost) * 10_000,
                "verdict": "Pays" if low > needed else "Doesn't pay" if high < needed else "Uncertain",
            }
        )
    return rows


def promotion(summary: list[dict], pairs: list[dict], a: Assumptions) -> dict:
    """Contribution per 10,000 sends for each creative, and whether the leader wins outright."""
    control = next(row["revenue"] for row in summary if row["arm"] == "control")
    arms = [
        {
            "arm": row["arm"],
            "contribution_per_10k": 0.0 if row["arm"] == "control"
            else ((row["revenue"] - control) * a.gross_margin - a.contact_cost) * 10_000,
        }
        for row in summary
    ]
    emails = sorted(
        (row for row in arms if row["arm"] != "control"),
        key=lambda row: row["contribution_per_10k"], reverse=True,
    )
    best, runner_up = emails[0], emails[1]
    head_to_head = next(
        pair for pair in pairs if {pair["left"], pair["right"]} == {best["arm"], runner_up["arm"]}
    )
    if best["contribution_per_10k"] <= 0:
        decision = "send_neither"
    elif head_to_head["significant"]:
        decision = "roll_out"
    else:
        decision = "lean"
    return {
        "arms": arms, "best": best["arm"], "runner_up": runner_up["arm"],
        "best_contribution_per_10k": best["contribution_per_10k"], "decision": decision,
    }


def next_test_plan(
    baseline_revenue: float, raw_sd: float, cuped_sd: float, a: Assumptions, lift: float,
    target_power: float = 0.8, share: float = 0.5, points: int = 60,
) -> dict:
    """Sample size and a power-by-duration curve for the next test, with and without CUPED."""
    delta = lift * baseline_revenue
    n_raw = required_total_n(delta, raw_sd, share, a.alpha, target_power)
    n_cuped = required_total_n(delta, cuped_sd, share, a.alpha, target_power)
    n_used = n_cuped if a.use_cuped else n_raw
    end = max(2.0, 2 * weeks_needed(n_raw, a.weekly_customers))
    curve = []
    for i in range(points):
        weeks = 0.25 + (end - 0.25) * i / (points - 1)
        n_c = int(weeks * a.weekly_customers * (1 - share))
        n_t = int(weeks * a.weekly_customers * share)
        curve.append(
            {
                "weeks": weeks,
                "raw": power_two_means(delta, raw_sd, raw_sd, n_c, n_t, a.alpha),
                "cuped": power_two_means(delta, cuped_sd, cuped_sd, n_c, n_t, a.alpha),
            }
        )
    return {
        "n_raw": n_raw, "n_cuped": n_cuped, "n_used": n_used,
        "weeks": weeks_needed(n_used, a.weekly_customers),
        "weeks_saved": weeks_needed(n_raw - n_cuped, a.weekly_customers),
        "curve": curve,
    }


def mart_pnl(arms: list[dict], sectors: list[dict], contact_cost: float) -> list[dict]:
    """mart_pnl from sql/warehouse.sql, re-priced at a different cost per e-mail."""
    rows = []
    for arm in arms:
        for sector in sectors:
            gross_profit = arm["incremental_revenue"] * sector["gross_margin"]
            marketing_cost = arm["customers"] * contact_cost
            rows.append(
                {
                    "arm": arm["arm"], "sector": sector["sector"], "customers": arm["customers"],
                    "incremental_revenue": arm["incremental_revenue"], "gross_profit": gross_profit,
                    "marketing_cost": marketing_cost, "contribution": gross_profit - marketing_cost,
                }
            )
    return rows
