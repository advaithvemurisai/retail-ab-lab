"""Peeking diagnostics motivated by Johari, Pekelis, Walsh (2015).

Hillstrom has no timestamps, so this is an A/A simulation rather than a replay: each
simulated test accrues customers in order and is checked at evenly spaced looks.
"""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def peeking_false_positive_rate(
    looks: int, n: int = 2000, simulations: int = 2000, rate: float = 0.08,
    alpha: float = 0.05, seed: int = 42,
) -> float:
    """Share of A/A tests declared significant at any of `looks` interim checks."""
    rng = np.random.default_rng(seed)
    treated = rng.random((simulations, n)) < 0.5
    converted = rng.random((simulations, n)) < rate
    checkpoints = np.linspace(n / looks, n, looks).astype(int) - 1
    n_t = np.cumsum(treated, 1, dtype=np.int32)[:, checkpoints]
    x_t = np.cumsum(treated & converted, 1, dtype=np.int32)[:, checkpoints]
    x_all = np.cumsum(converted, 1, dtype=np.int32)[:, checkpoints]
    n_c = checkpoints + 1 - n_t
    x_c = x_all - x_t
    with np.errstate(divide="ignore", invalid="ignore"):
        pooled = x_all / (checkpoints + 1)
        se = np.sqrt(pooled * (1 - pooled) * (1 / n_t + 1 / n_c))
        z = (x_t / n_t - x_c / n_c) / se
    significant = np.nan_to_num(2 * norm.sf(np.abs(z)), nan=1.0) < alpha
    return float(significant.any(1).mean())
