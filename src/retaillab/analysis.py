"""One campaign readout: validity, lift, economics, power, and the verdict, from one set of inputs."""

from __future__ import annotations

import math
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from .data import DESIGN, campaign_view
from .decision import Verdict, decide
from .estimate import bootstrap_difference, proportion_effect, segment_effects, welch_effect
from .finance import break_even_lift, contribution_distribution, pnl
from .power import power_two_means, required_total_n
from .validity import srm, standardized_mean_differences
from .variance import cuped

BALANCE_COVARIATES = ["pre_spend", "recency"]
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


@dataclass(frozen=True)
class Readout:
    assumptions: Assumptions
    validity: dict
    balance: pd.DataFrame
    conversion: dict
    revenue: dict
    baseline_revenue: float
    revenue_lift: float
    revenue_lift_ci: tuple[float, float]
    cuped: dict
    economics: dict
    contribution: dict
    break_even_lift: float
    planned_lift: float
    power: float
    required_n: float
    additional_weeks: int
    segments: pd.DataFrame
    verdict: Verdict = field(repr=False)


def analyze(data: pd.DataFrame, assumptions: Assumptions | None = None) -> Readout:
    a = assumptions or Assumptions()
    validity = srm(data, DESIGN)
    view = campaign_view(data, a.variant)
    view, cuped_stats = cuped(view, "revenue", "pre_spend")
    metric = "revenue_cuped" if a.use_cuped else "revenue"

    conversion = proportion_effect(view, "conversion")
    revenue = welch_effect(view, metric)
    baseline = welch_effect(view, "revenue")["control_mean"]
    revenue_lift = revenue["difference"] / baseline
    economics = pnl(view, a.gross_margin, a.contact_cost, metric)
    draws = bootstrap_difference(view, metric)
    contribution = contribution_distribution(
        draws, economics["customers_contacted"], a.gross_margin, a.contact_cost
    )

    break_even = break_even_lift(a.contact_cost, baseline, a.gross_margin)
    planned_lift = break_even if 0 < break_even < math.inf else MINIMUM_PLANNED_LIFT
    delta = planned_lift * baseline
    power = power_two_means(
        delta, revenue["control_sd"], revenue["treatment_sd"], revenue["n_control"],
        revenue["n_treatment"], a.alpha,
    )
    n_total = revenue["n_control"] + revenue["n_treatment"]
    pooled_sd = float(np.sqrt((revenue["control_sd"] ** 2 + revenue["treatment_sd"] ** 2) / 2))
    required_n = required_total_n(delta, pooled_sd, revenue["n_treatment"] / n_total, a.alpha)
    shortfall = max(0.0, required_n - n_total)
    additional_weeks = math.ceil(shortfall / a.weekly_customers) if a.weekly_customers else 0

    segments = segment_effects(view, "history_segment", metric, a.alpha)
    segment_harm = bool(
        len(segments) and (segments.significant & (segments.difference < 0)).any()
    )

    verdict = decide(
        validity_failed=validity["failed"],
        primary_lift=revenue_lift,
        primary_p=revenue["p_value"],
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
    return Readout(
        assumptions=a,
        validity=validity,
        balance=standardized_mean_differences(view, BALANCE_COVARIATES),
        conversion=conversion,
        revenue=revenue,
        baseline_revenue=float(baseline),
        revenue_lift=float(revenue_lift),
        revenue_lift_ci=(revenue["ci_low"] / baseline, revenue["ci_high"] / baseline),
        cuped=cuped_stats,
        economics=economics,
        contribution=contribution,
        break_even_lift=float(break_even),
        planned_lift=float(planned_lift),
        power=power,
        required_n=float(required_n),
        additional_weeks=additional_weeks,
        segments=segments,
        verdict=verdict,
    )
