"""Precompute everything the web app needs that depends on customer-level data.

The sidebar assumptions only enter the readout through `pricing`, which runs on statistics that
do not depend on them. The e-mail tested and the CUPED toggle do change those statistics, so all
six combinations are computed here, bootstrap draws included. `scripts/build_web_data.py` writes
the result to web/public/data/readout.json, where the API prices it per request.
"""

from __future__ import annotations

import math

import numpy as np
import pandas as pd

from .analysis import BALANCE_COVARIATES
from .data import ARM_LABELS, DESIGN, SEGMENT_COLUMNS, VARIANTS, campaign_view
from .estimate import (
    bootstrap_difference,
    pairwise_arms,
    proportion_effect,
    segment_effects,
    welch_effect,
)
from .finance import attributed_incremental
from .resampling import peeking_false_positive_rate
from .validity import srm, standardized_mean_differences
from .variance import cuped
from .warehouse import SQL, build_warehouse, table_counts

LOOKS = [1, 2, 3, 5, 10, 20]
CONTACT_COST = 0.18


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
            "draws": bootstrap_difference(view, metric).tolist(),
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


def build_readout(data: pd.DataFrame, source: str, margins: dict, placebo_shuffles: int = 100) -> dict:
    """The full precomputed readout, JSON-safe."""
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
            "placebo": placebo_slices(data, placebo_shuffles),
        },
        "warehouse": warehouse_block(data, margins),
    }
    return clean(readout)
