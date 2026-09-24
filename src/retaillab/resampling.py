"""Peeking diagnostics motivated by Johari, Pekelis, Walsh (2015)."""

from __future__ import annotations

import numpy as np
from scipy.stats import norm


def aa_false_positive_rate(n: int = 1000, simulations: int = 200, seed: int = 42) -> float:
    rng = np.random.default_rng(seed)
    hits = 0
    for _ in range(simulations):
        groups, outcome = rng.integers(0, 2, n), rng.random(n) < 0.08
        for fraction in np.linspace(0.2, 1, 5):
            mask = rng.random(n) < fraction
            sizes = np.array([(mask & (groups == 1)).sum(), (mask & (groups == 0)).sum()])
            counts = np.array(
                [outcome[mask & (groups == 1)].sum(), outcome[mask & (groups == 0)].sum()]
            )
            if (
                sizes.min()
                and (
                        2
                    * norm.sf(
                        abs(
                            (counts[0] / sizes[0] - counts[1] / sizes[1])
                            / np.sqrt(
                                (counts.sum() / sizes.sum())
                                * (1 - counts.sum() / sizes.sum())
                                * (1 / sizes[0] + 1 / sizes[1])
                            )
                        )
                    )
                )
                < 0.05
            ):
                hits += 1
                break
    return hits / simulations
