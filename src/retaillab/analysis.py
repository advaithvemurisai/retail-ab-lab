"""One campaign readout: validity, lift, economics, power, and the verdict, from one set of inputs.

The customer-level statistics are computed here; `pricing.price` turns them into the verdict.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from .data import DESIGN, campaign_view
from .decision import Verdict
from .estimate import bootstrap_difference, proportion_effect, segment_effects, welch_effect
from .pricing import Assumptions, price
from .validity import srm, standardized_mean_differences
from .variance import cuped

__all__ = ["Assumptions", "Readout", "analyze"]

BALANCE_COVARIATES = ["pre_spend", "recency"]


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

    revenue = welch_effect(view, metric)
    baseline = welch_effect(view, "revenue")["control_mean"]
    segments = segment_effects(view, "history_segment", metric, a.alpha)
    priced = price(
        revenue, baseline, bootstrap_difference(view, metric), segments.to_dict("records"), a,
        validity["failed"],
    )
    return Readout(
        assumptions=a,
        validity=validity,
        balance=standardized_mean_differences(view, BALANCE_COVARIATES),
        conversion=proportion_effect(view, "conversion"),
        revenue=revenue,
        cuped=cuped_stats,
        segments=segments,
        **priced,
    )
