"""Experiment estimators for binary and continuous retail outcomes."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest


def proportion_effect(data: pd.DataFrame, metric: str = "conversion") -> dict[str, float]:
    control = data.loc[data.arm == "control", metric].astype(float)
    treatment = data.loc[data.arm == "treatment", metric].astype(float)
    counts = np.array([treatment.sum(), control.sum()])
    sizes = np.array([len(treatment), len(control)])
    if sizes.min() == 0:
        raise ValueError("both arms must contain observations")
    z, p = proportions_ztest(counts, sizes)
    c, t = counts[1] / sizes[1], counts[0] / sizes[0]
    return {
        "control_rate": float(c),
        "treatment_rate": float(t),
        "difference": float(t - c),
        "relative_lift": float(t / c - 1) if c else np.nan,
        "z": float(z),
        "p_value": float(p),
    }


def relative_lift_ci(
    data: pd.DataFrame, metric: str = "conversion", confidence: float = 0.95
) -> tuple[float, float]:
    result = proportion_effect(data, metric)
    c, t = result["control_rate"], result["treatment_rate"]
    if c == 0:
        return (np.nan, np.nan)
    z = stats.norm.ppf(1 - (1 - confidence) / 2)
    variance = (
        t * (1 - t) / len(data[data.arm == "treatment"]) / c**2
        + c * (1 - c) / len(data[data.arm == "control"]) * t**2 / c**4
    )
    margin = z * np.sqrt(variance)
    return (float(result["relative_lift"] - margin), float(result["relative_lift"] + margin))


def welch_effect(data: pd.DataFrame, metric: str = "revenue") -> dict[str, float]:
    control = data.loc[data.arm == "control", metric].astype(float)
    treatment = data.loc[data.arm == "treatment", metric].astype(float)
    test = stats.ttest_ind(treatment, control, equal_var=False)
    return {
        "control_mean": float(control.mean()),
        "treatment_mean": float(treatment.mean()),
        "difference": float(treatment.mean() - control.mean()),
        "p_value": float(test.pvalue),
    }


def bootstrap_ci(
    data: pd.DataFrame, metric: str = "revenue", draws: int = 2000, seed: int = 42
) -> dict[str, float]:
    rng = np.random.default_rng(seed)
    c = data.loc[data.arm == "control", metric].to_numpy(float)
    t = data.loc[data.arm == "treatment", metric].to_numpy(float)
    differences = rng.choice(t, (draws, len(t))).mean(1) - rng.choice(c, (draws, len(c))).mean(1)
    low, high = np.quantile(differences, [0.025, 0.975])
    return {
        "difference": float(differences.mean()),
        "ci_low": float(low),
        "ci_high": float(high),
        "chance_loss": float(np.mean(differences < 0)),
        "draws": differences,
    }


def ratio_ci(data: pd.DataFrame, numerator: str, denominator: str) -> tuple[float, float]:
    values = []
    for frame in (data[data.arm == "control"], data[data.arm == "treatment"]):
        ratio = frame[numerator].mean() / frame[denominator].mean()
        variance = (
            np.var(frame[numerator] - ratio * frame[denominator], ddof=1)
            / len(frame)
            / frame[denominator].mean() ** 2
        )
        values.append((ratio, np.sqrt(variance)))
    estimate = values[1][0] - values[0][0]
    margin = 1.96 * np.hypot(values[0][1], values[1][1])
    return (float(estimate - margin), float(estimate + margin))


def benjamini_hochberg(p_values: list[float], alpha: float = 0.05) -> dict[str, object]:
    values = np.asarray(p_values, dtype=float)
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    adjusted[order] = np.minimum.accumulate(
        (values[order] * len(values) / np.arange(1, len(values) + 1))[::-1]
    )[::-1]
    adjusted = np.clip(adjusted, 0, 1)
    return {"adjusted_p_values": adjusted.tolist(), "reject": (adjusted < alpha).tolist()}
