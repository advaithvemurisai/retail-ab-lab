"""Normal-approximation power and sample size for a difference in means."""

from __future__ import annotations

import math

from scipy.stats import norm


def power_two_means(
    delta: float, sd_control: float, sd_treatment: float, n_control: int, n_treatment: int,
    alpha: float = 0.05,
) -> float:
    """Two-sided power to detect an absolute difference `delta`."""
    if n_control <= 0 or n_treatment <= 0:
        return 0.0
    se = math.sqrt(sd_control**2 / n_control + sd_treatment**2 / n_treatment)
    if se == 0:
        return 1.0
    z = norm.ppf(1 - alpha / 2)
    shift = abs(delta) / se
    return float(norm.cdf(shift - z) + norm.cdf(-shift - z))


def required_total_n(
    delta: float, sd: float, treatment_share: float = 0.5, alpha: float = 0.05,
    power: float = 0.8, sd_treatment: float | None = None,
) -> int:
    """Total customers needed across both arms for the given allocation.

    `sd` is the control SD; pass `sd_treatment` when the arms differ, since the variance of the
    difference is sd_c^2 / n_c + sd_t^2 / n_t and only collapses to one SD when they match.
    """
    if delta == 0:
        return math.inf
    sd_t = sd if sd_treatment is None else sd_treatment
    z = norm.ppf(1 - alpha / 2) + norm.ppf(power)
    variance = sd**2 / (1 - treatment_share) + sd_t**2 / treatment_share
    return math.ceil(z**2 * variance / delta**2)


def weeks_needed(total_n: float, weekly_customers: int) -> float:
    return math.inf if weekly_customers <= 0 else total_n / weekly_customers
