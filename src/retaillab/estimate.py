"""Experiment estimators for binary and continuous retail outcomes."""

from __future__ import annotations

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportions_ztest


def _arms(data: pd.DataFrame, metric: str) -> tuple[np.ndarray, np.ndarray]:
    control = data.loc[data.arm == "control", metric].to_numpy(float)
    treatment = data.loc[data.arm == "treatment", metric].to_numpy(float)
    if not len(control) or not len(treatment):
        raise ValueError("both arms must contain observations")
    return control, treatment


def proportion_effect(
    data: pd.DataFrame, metric: str = "conversion", confidence: float = 0.95
) -> dict[str, float]:
    """Two-proportion z-test with a delta-method interval on relative lift."""
    control, treatment = _arms(data, metric)
    counts = np.array([treatment.sum(), control.sum()])
    sizes = np.array([len(treatment), len(control)])
    z, p = proportions_ztest(counts, sizes)
    c, t = counts[1] / sizes[1], counts[0] / sizes[0]
    lift = t / c - 1 if c else np.nan
    critical = stats.norm.ppf(1 - (1 - confidence) / 2)
    variance = t * (1 - t) / sizes[0] / c**2 + c * (1 - c) / sizes[1] * t**2 / c**4 if c else np.nan
    margin = critical * np.sqrt(variance)
    return {
        "control_rate": float(c),
        "treatment_rate": float(t),
        "difference": float(t - c),
        "relative_lift": float(lift),
        "lift_ci_low": float(lift - margin),
        "lift_ci_high": float(lift + margin),
        "z": float(z),
        "p_value": float(p),
    }


def welch_effect(
    data: pd.DataFrame, metric: str = "revenue", confidence: float = 0.95
) -> dict[str, float]:
    """Difference in means with a Welch interval. Adequate for skewed spend at retail sample sizes."""
    control, treatment = _arms(data, metric)
    difference = treatment.mean() - control.mean()
    se = np.sqrt(control.var(ddof=1) / len(control) + treatment.var(ddof=1) / len(treatment))
    test = stats.ttest_ind(treatment, control, equal_var=False)
    critical = stats.norm.ppf(1 - (1 - confidence) / 2)
    return {
        "control_mean": float(control.mean()),
        "treatment_mean": float(treatment.mean()),
        "control_sd": float(control.std(ddof=1)),
        "treatment_sd": float(treatment.std(ddof=1)),
        "n_control": len(control),
        "n_treatment": len(treatment),
        "difference": float(difference),
        "se": float(se),
        "ci_low": float(difference - critical * se),
        "ci_high": float(difference + critical * se),
        "p_value": float(test.pvalue),
    }


def bootstrap_difference(
    data: pd.DataFrame, metric: str = "revenue", draws: int = 1000, seed: int = 42,
    chunk: int = 100,
) -> np.ndarray:
    """Bootstrap draws of the treatment-minus-control mean, resampled within each arm."""
    rng = np.random.default_rng(seed)
    control, treatment = _arms(data, metric)
    result = []
    for start in range(0, draws, chunk):
        size = min(chunk, draws - start)
        t = treatment[rng.integers(0, len(treatment), (size, len(treatment)))].mean(1)
        c = control[rng.integers(0, len(control), (size, len(control)))].mean(1)
        result.append(t - c)
    return np.concatenate(result)


def benjamini_hochberg(p_values: list[float], alpha: float = 0.05) -> dict[str, list]:
    values = np.asarray(p_values, dtype=float)
    if not len(values):
        return {"adjusted_p_values": [], "reject": []}
    order = np.argsort(values)
    adjusted = np.empty_like(values)
    adjusted[order] = np.minimum.accumulate(
        (values[order] * len(values) / np.arange(1, len(values) + 1))[::-1]
    )[::-1]
    adjusted = np.clip(adjusted, 0, 1)
    return {"adjusted_p_values": adjusted.tolist(), "reject": (adjusted < alpha).tolist()}


def pairwise_arms(
    data: pd.DataFrame, arms: list[str], metric: str = "revenue", alpha: float = 0.05
) -> pd.DataFrame:
    """Every pair of arms by Welch test, with BH correction across the comparisons."""
    rows = []
    for i, left in enumerate(arms):
        for right in arms[i + 1:]:
            pair = data[data.arm.isin([left, right])].assign(
                arm=lambda frame, r=right: np.where(frame.arm == r, "treatment", "control")
            )
            effect = welch_effect(pair, metric)
            rows.append(
                {
                    "comparison": f"{right} vs {left}",
                    "left": left,
                    "right": right,
                    "difference": effect["difference"],
                    "ci_low": effect["ci_low"],
                    "ci_high": effect["ci_high"],
                    "p_value": effect["p_value"],
                }
            )
    result = pd.DataFrame(rows)
    corrected = benjamini_hochberg(result.p_value.tolist(), alpha)
    result["p_adjusted"] = corrected["adjusted_p_values"]
    result["significant"] = corrected["reject"]
    return result


def segment_effects(
    data: pd.DataFrame, by: str, metric: str = "revenue", alpha: float = 0.05,
    min_per_arm: int = 30,
) -> pd.DataFrame:
    """Treatment effect within each segment, BH-corrected across segments."""
    rows = []
    for segment, frame in data.groupby(by, observed=True):
        counts = frame.arm.value_counts()
        if counts.get("control", 0) < min_per_arm or counts.get("treatment", 0) < min_per_arm:
            continue
        effect = welch_effect(frame, metric)
        rows.append(
            {
                "segment": segment,
                "customers": len(frame),
                "control_mean": effect["control_mean"],
                "treatment_mean": effect["treatment_mean"],
                "difference": effect["difference"],
                "ci_low": effect["ci_low"],
                "ci_high": effect["ci_high"],
                "p_value": effect["p_value"],
            }
        )
    result = pd.DataFrame(rows)
    if len(result):
        corrected = benjamini_hochberg(result.p_value.tolist(), alpha)
        result["p_adjusted"] = corrected["adjusted_p_values"]
        result["significant"] = corrected["reject"]
    return result
