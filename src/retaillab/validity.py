"""Validity checks for randomized retail experiments."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def srm(data: pd.DataFrame, split: float = 0.5) -> dict[str, float | bool]:
    counts = data.arm.value_counts().reindex(["control", "treatment"], fill_value=0)
    expected = np.array([len(data) * (1 - split), len(data) * split])
    chi2, p = stats.chisquare(counts.to_numpy(), expected)
    return {
        "control": int(counts.control),
        "treatment": int(counts.treatment),
        "chi2": float(chi2),
        "p_value": float(p),
        "failed": bool(p < 0.001),
    }


def standardized_mean_differences(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    rows = []
    c, t = data[data.arm == "control"], data[data.arm == "treatment"]
    for column in columns:
        pooled = np.sqrt((c[column].var() + t[column].var()) / 2)
        rows.append(
            {
                "covariate": column,
                "smd": float((t[column].mean() - c[column].mean()) / pooled) if pooled else 0.0,
            }
        )
    return pd.DataFrame(rows)
