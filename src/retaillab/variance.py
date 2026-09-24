"""CUPED variance reduction (Deng, Xu, Kohavi, Walker, WSDM 2013)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def cuped(
    data: pd.DataFrame, outcome: str = "revenue", covariate: str = "pre_spend"
) -> dict[str, float]:
    x, y = data[covariate].astype(float).to_numpy(), data[outcome].astype(float).to_numpy()
    theta = float(np.cov(y, x, ddof=1)[0, 1] / np.var(x, ddof=1)) if np.var(x) else 0.0
    adjusted = y - theta * (x - x.mean())
    frame = data.assign(_adjusted=adjusted)
    raw = frame.groupby("arm")[outcome].mean()
    adj = frame.groupby("arm")._adjusted.mean()
    reduction = 1 - np.var(adjusted) / np.var(y) if np.var(y) else 0.0
    return {
        "theta": theta,
        "raw_difference": float(raw.treatment - raw.control),
        "adjusted_difference": float(adj.treatment - adj.control),
        "variance_reduction": float(reduction),
        "duration_saving": float(max(0, reduction)),
    }
