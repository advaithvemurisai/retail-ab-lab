"""Validity checks for randomized retail experiments."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats


def srm(
    data: pd.DataFrame, design: dict[str, float], threshold: float = 0.001
) -> dict[str, object]:
    """Sample ratio mismatch: chi-square of observed arm counts against the designed split."""
    shares = np.array(list(design.values()), dtype=float)
    shares = shares / shares.sum()
    counts = data.arm.value_counts().reindex(list(design), fill_value=0)
    expected = shares * counts.sum()
    chi2, p = stats.chisquare(counts.to_numpy(), expected)
    return {
        "counts": {arm: int(count) for arm, count in counts.items()},
        "expected": {arm: float(value) for arm, value in zip(design, expected)},
        "chi2": float(chi2),
        "p_value": float(p),
        "failed": bool(p < threshold),
    }


def standardized_mean_differences(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Covariate balance between control and treatment. |SMD| above 0.1 deserves a look."""
    rows = []
    c, t = data[data.arm == "control"], data[data.arm == "treatment"]
    for column in columns:
        pooled = np.sqrt((c[column].var() + t[column].var()) / 2)
        smd = (t[column].mean() - c[column].mean()) / pooled if pooled else 0.0
        rows.append({"covariate": column, "smd": float(smd), "balanced": bool(abs(smd) < 0.1)})
    return pd.DataFrame(rows)
