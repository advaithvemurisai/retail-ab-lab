"""Precompute the static web app's data from the same Python code the Streamlit app runs.

The sidebar assumptions (margin, cost per e-mail, ROI hurdle, weekly volume) only enter the
readout through arithmetic on statistics that do not depend on them, so the browser can rebuild
every verdict from what is written here. The e-mail tested and the CUPED toggle do change those
statistics, so all six combinations are precomputed, bootstrap draws included.

Writes web/public/data/readout.json, plus web/src/fixtures/parity.json: full Python readouts
for a set of assumptions, which the web tests check the TypeScript port against.
"""

from __future__ import annotations

import json
import math
import os
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))
from retaillab.analysis import BALANCE_COVARIATES, Assumptions, analyze
from retaillab.data import (
    ARM_LABELS,
    DESIGN,
    SEGMENT_COLUMNS,
    VARIANTS,
    campaign_view,
    fetch_public_files,
    load_experiment,
)
from retaillab.estimate import (
    bootstrap_difference,
    pairwise_arms,
    proportion_effect,
    segment_effects,
    welch_effect,
)
from retaillab.finance import attributed_incremental, load_margins
from retaillab.resampling import peeking_false_positive_rate
from retaillab.validity import srm, standardized_mean_differences
from retaillab.variance import cuped
from retaillab.warehouse import SQL, build_warehouse, table_counts

WEB = ROOT / "web"
LOOKS = [1, 2, 3, 5, 10, 20]
CONTACT_COST = 0.18
PARITY_CASES = [
    {},
    {"variant": "mens"},
    {"variant": "womens"},
    {"use_cuped": False},
    {"contact_cost": 2.0},
    {"contact_cost": 0.0},
    {"variant": "womens", "gross_margin": 0.1},
    {"minimum_roi": 2.0},
    {"gross_margin": 0.05, "contact_cost": 0.6, "weekly_customers": 1_000},
    {"variant": "mens", "use_cuped": False, "gross_margin": 0.25, "contact_cost": 0.4},
]


def clean(value):
    """JSON-safe: numpy scalars to Python, non-finite floats to null."""
    if isinstance(value, dict):
        return {str(key): clean(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(item) for item in value]
    if isinstance(value, np.ndarray):
        return clean(value.tolist())
    if isinstance(value, (np.bool_, bool)):
        return bool(value)
    if isinstance(value, (np.integer, int)):
        return int(value)
    if isinstance(value, (np.floating, float)):
        return float(value) if math.isfinite(value) else None
    return value


def records(frame) -> list[dict]:
    return clean(frame.to_dict("records"))


def placebo_slices(data, shuffles: int = 100, seed: int = 7) -> list[dict]:
    """Same procedure as the Streamlit pitfalls page: shuffle assignment, slice every way."""
    placebo = campaign_view(data, "any")
    arms = placebo.arm.to_numpy()
    rng = np.random.default_rng(seed)
    raw_hits = {column: 0 for column in SEGMENT_COLUMNS}
    bh_hits = dict(raw_hits)
    any_raw = any_bh = 0
    for _ in range(shuffles):
        placebo["arm"] = rng.permutation(arms)
        found_raw = found_bh = False
        for column in SEGMENT_COLUMNS:
            effects = segment_effects(placebo, column)
            raw, bh = bool((effects.p_value < 0.05).any()), bool(effects.significant.any())
            raw_hits[column] += raw
            bh_hits[column] += bh
            found_raw, found_bh = found_raw or raw, found_bh or bh
        any_raw += found_raw
        any_bh += found_bh
    rows = [
        {"slice": label, "raw": raw_hits[column] / shuffles, "bh": bh_hits[column] / shuffles}
        for column, label in SEGMENT_COLUMNS.items()
    ]
    rows.append({"slice": "Any of the above", "raw": any_raw / shuffles, "bh": any_bh / shuffles})
    return rows


def broken_split(data) -> dict:
    view = campaign_view(data, "any")
    treated_non_buyers = view.index[(view.arm == "treatment") & (view.conversion == 0)]
    dropped = np.random.default_rng(1).choice(
        treated_non_buyers, int(0.05 * len(treated_non_buyers)), replace=False
    )
    broken = data.drop(index=dropped)
    honest = welch_effect(view, "revenue")
    biased = welch_effect(campaign_view(broken, "any"), "revenue")
    check = srm(broken, DESIGN)
    return {
        "true_lift": honest["difference"] / honest["control_mean"],
        "reported_lift": biased["difference"] / biased["control_mean"],
        "srm_failed": check["failed"],
        "srm_p": check["p_value"],
    }


def variant_block(data, variant: str) -> dict:
    view, cuped_stats = cuped(campaign_view(data, variant), "revenue", "pre_spend")
    metrics = {}
    for key, metric in (("raw", "revenue"), ("cuped", "revenue_cuped")):
        metrics[key] = {
            "revenue": welch_effect(view, metric),
            "draws": [round(float(d), 9) for d in bootstrap_difference(view, metric)],
            "segments": {
                column: records(segment_effects(view, column, metric)) for column in SEGMENT_COLUMNS
            },
        }
    return {
        "label": VARIANTS[variant],
        "baseline_revenue": welch_effect(view, "revenue")["control_mean"],
        "conversion": proportion_effect(view, "conversion"),
        "cuped": cuped_stats,
        "balance": records(standardized_mean_differences(view, BALANCE_COVARIATES)),
        "attribution": attributed_incremental(view),
        "pooled_sd": {"raw": float(view.revenue.std()), "cuped": float(view.revenue_cuped.std())},
        "metrics": metrics,
    }


def promotion_block(data) -> dict:
    frame, _ = cuped(data)
    arms = list(ARM_LABELS)
    result = {}
    for key, metric in (("raw", "revenue"), ("cuped", "revenue_cuped")):
        summary = frame.groupby("arm").agg(
            customers=(metric, "size"), conversion=("conversion", "mean"),
            revenue=(metric, "mean"), sd=(metric, "std"),
        ).reindex(arms)
        pairs = pairwise_arms(frame, arms, metric)
        result[key] = {
            "summary": records(summary.reset_index()),
            "pairs": records(pairs.drop(columns="comparison")),
        }
    return result


def warehouse_block(data, margins) -> dict:
    connection = build_warehouse(":memory:", data, margins, CONTACT_COST)
    arms = connection.execute(
        "SELECT DISTINCT arm, customers, incremental_revenue FROM mart_pnl ORDER BY arm"
    ).df()
    block = {
        "tables": records(table_counts(connection)),
        "arms": records(arms),
        "sql": SQL.read_text(),
    }
    connection.close()
    return block


def parity(data, margin: float) -> list[dict]:
    cases = []
    for overrides in PARITY_CASES:
        a = Assumptions(**{"gross_margin": margin, **overrides})
        r = analyze(data, a)
        cases.append(
            clean(
                {
                    "assumptions": asdict(a),
                    "verdict": asdict(r.verdict),
                    "revenue_lift": r.revenue_lift,
                    "revenue_lift_ci": r.revenue_lift_ci,
                    "economics": r.economics,
                    "contribution": r.contribution,
                    "break_even_lift": r.break_even_lift,
                    "planned_lift": r.planned_lift,
                    "power": r.power,
                    "required_n": r.required_n,
                    "additional_weeks": r.additional_weeks,
                }
            )
        )
    return cases


def write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(clean(payload), separators=(",", ":"), allow_nan=False))
    print(f"Wrote {path.relative_to(ROOT)} ({path.stat().st_size / 1024:,.0f} KB)")


if __name__ == "__main__":
    demo = os.environ.get("RETAILLAB_DEMO") == "1"
    if not demo:
        # A deploy must not quietly ship synthetic numbers, so a failed download fails the build.
        fetch_public_files()
    data, source = load_experiment()
    margins = load_margins(force_demo=demo)
    sectors = [{"sector": name, **values} for name, values in margins["margins"].items()]
    readout = {
        "source": source,
        "customers": len(data),
        "arm_labels": ARM_LABELS,
        "segment_columns": SEGMENT_COLUMNS,
        "margins": {"as_of": margins["as_of"], "source": margins["source"], "sectors": sectors},
        "validity": srm(data, DESIGN),
        "variants": {variant: variant_block(data, variant) for variant in VARIANTS},
        "audience": {
            column: {str(k): int(v) for k, v in data.groupby(column, observed=True).size().items()}
            for column in SEGMENT_COLUMNS
        },
        "promotion": promotion_block(data),
        "pitfalls": {
            "looks": LOOKS,
            "peeking": [peeking_false_positive_rate(looks) for looks in LOOKS],
            "broken_split": broken_split(data),
            "placebo": placebo_slices(data),
        },
        "warehouse": warehouse_block(data, margins),
    }
    write(WEB / "public" / "data" / "readout.json", readout)
    write(WEB / "src" / "fixtures" / "parity.json", parity(data, sectors[0]["gross_margin"]))
    print(f"Source: {source} ({len(data):,} customers), {margins['source']} margins")
