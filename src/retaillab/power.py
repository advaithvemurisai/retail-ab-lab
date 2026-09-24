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
    power: float = 0.8,
) -> int:
    """Total customers needed across both arms for the given allocation."""
    if delta == 0:
        return math.inf
    z = norm.ppf(1 - alpha / 2) + norm.ppf(power)
    allocation = 1 / treatment_share + 1 / (1 - treatment_share)
    return math.ceil(z**2 * sd**2 * allocation / delta**2)


def weeks_needed(total_n: float, weekly_customers: int) -> float:
    return math.inf if weekly_customers <= 0 else total_n / weekly_customers
