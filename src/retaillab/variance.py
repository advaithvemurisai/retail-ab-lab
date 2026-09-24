"""CUPED variance reduction (Deng, Xu, Kohavi, Walker, WSDM 2013)."""

from __future__ import annotations

import numpy as np
import pandas as pd


def cuped(
    data: pd.DataFrame, outcome: str = "revenue", covariate: str = "pre_spend"
) -> tuple[pd.DataFrame, dict[str, float]]:
    """Return the data with an `<outcome>_cuped` column, plus diagnostics.

    Theta is estimated on both arms pooled. That is treatment-blind because the pre-period
    covariate cannot be affected by assignment. Variance reduction equals the squared
    correlation between covariate and outcome, so the saving in sample size (and test
    duration) at fixed sensitivity is the same fraction.
    """
    x = data[covariate].to_numpy(float)
    y = data[outcome].to_numpy(float)
    var_x = np.var(x, ddof=1)
    theta = float(np.cov(y, x, ddof=1)[0, 1] / var_x) if var_x else 0.0
    adjusted = y - theta * (x - x.mean())
    var_y = np.var(y, ddof=1)
    reduction = float(1 - np.var(adjusted, ddof=1) / var_y) if var_y else 0.0
    frame = data.assign(**{f"{outcome}_cuped": adjusted})
    return frame, {
        "theta": theta,
        "correlation": float(np.corrcoef(x, y)[0, 1]) if var_x and var_y else 0.0,
        "variance_reduction": max(0.0, reduction),
    }
