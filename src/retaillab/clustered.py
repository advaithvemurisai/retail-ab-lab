"""Store-level clustered experiment summaries."""

from __future__ import annotations

import pandas as pd
from scipy import stats

from .estimate import benjamini_hochberg


def aggregate_stores(data: pd.DataFrame, outcome: str = "sales") -> pd.DataFrame:
    return data.groupby(["store_id", "arm"], as_index=False)[outcome].mean()


def design_effect(data: pd.DataFrame, cluster: str = "store_id") -> dict[str, float]:
    mean_size = data.groupby(cluster).size().mean()
    effect = 1 + (mean_size - 1) * 0.05
    return {
        "mean_cluster_size": float(mean_size),
        "design_effect": float(effect),
        "effective_n": float(len(data) / effect),
    }


def pairwise_promotions(data: pd.DataFrame, outcome: str = "sales") -> pd.DataFrame:
    arms = sorted(data.arm.unique())
    rows = []
    for left in arms:
        for right in arms:
            if left < right:
                test = stats.ttest_ind(
                    data[data.arm == left][outcome],
                    data[data.arm == right][outcome],
                    equal_var=False,
                )
                rows.append({"left": left, "right": right, "p_value": float(test.pvalue)})
    result = pd.DataFrame(rows)
    if len(result):
        result["p_adjusted"] = benjamini_hochberg(result.p_value.tolist())["adjusted_p_values"]
    return result
