"""Deterministic demo data used when external files are not present."""

from __future__ import annotations

import numpy as np
import pandas as pd


def demo_email(n: int = 12000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    arm = rng.choice(["control", "treatment"], n)
    pre = rng.lognormal(3.5, 0.8, n)
    conversion = rng.random(n) < (0.08 * np.where(arm == "treatment", 1.12, 1))
    revenue = np.where(conversion, rng.lognormal(3.8, 0.7, n), 0)
    return pd.DataFrame(
        {
            "unit_id": np.arange(n),
            "arm": arm,
            "conversion": conversion,
            "revenue": revenue,
            "pre_spend": pre,
            "segment": rng.choice(["mens", "womens", "new"], n),
            "cluster_id": rng.integers(1, 120, n),
        }
    )
