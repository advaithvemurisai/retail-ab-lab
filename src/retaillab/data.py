"""Load the Hillstrom email experiment, or a synthetic stand-in with the same schema."""

from __future__ import annotations

import os
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).parents[2]
RAW_DIR = ROOT / "data" / "raw"

# Hillstrom randomized customers into thirds. SRM is tested against this design.
DESIGN = {"control": 1 / 3, "mens": 1 / 3, "womens": 1 / 3}
ARM_LABELS = {"control": "No e-mail", "mens": "Men's e-mail", "womens": "Women's e-mail"}
VARIANTS = {"any": "Any e-mail (pooled)", "mens": "Men's e-mail", "womens": "Women's e-mail"}
SEGMENT_COLUMNS = {
    "history_segment": "Past-year spend band",
    "channel": "Purchase channel",
    "zip_code": "Area type",
    "newbie": "New customer (last 12 months)",
}
COLUMNS = [
    "unit_id", "arm", "visit", "conversion", "revenue", "pre_spend", "recency",
    "history_segment", "channel", "zip_code", "newbie",
]
_HILLSTROM_ARMS = {"No E-Mail": "control", "Mens E-Mail": "mens", "Womens E-Mail": "womens"}


def load_hillstrom(path: str | Path) -> pd.DataFrame:
    raw = pd.read_csv(path)
    frame = raw.rename(columns={"spend": "revenue", "history": "pre_spend"})
    frame["arm"] = raw["segment"].map(_HILLSTROM_ARMS)
    if frame["arm"].isna().any():
        raise ValueError("unexpected Hillstrom segment labels")
    frame["unit_id"] = np.arange(len(frame))
    frame["newbie"] = frame["newbie"].map({0: "No", 1: "Yes"})
    return frame[COLUMNS]


def demo_email(n: int = 30_000, seed: int = 42) -> pd.DataFrame:
    """Synthetic data shaped like Hillstrom. Effect sizes are illustrative, not published."""
    rng = np.random.default_rng(seed)
    arm = rng.choice(list(DESIGN), n)
    history = np.round(rng.lognormal(5.2, 0.9, n), 2)
    bands = [0, 100, 200, 350, 500, 750, 1000, np.inf]
    labels = [
        "1) $0 - $100", "2) $100 - $200", "3) $200 - $350", "4) $350 - $500",
        "5) $500 - $750", "6) $750 - $1,000", "7) $1,000 +",
    ]
    history_segment = pd.cut(history, bands, labels=labels, right=False).astype(str)
    newbie = rng.random(n) < 0.5
    propensity = 0.0055 * np.clip(1 + 0.35 * np.log(history / 150), 0.4, 2.5)
    lift = np.select([arm == "mens", arm == "womens"], [2.1, 1.55], 1.0)
    conversion = rng.random(n) < propensity * lift
    visit = conversion | (rng.random(n) < 0.10 * np.sqrt(lift))
    revenue = np.where(conversion, np.round(rng.lognormal(4.55, 0.55, n), 2), 0.0)
    return pd.DataFrame(
        {
            "unit_id": np.arange(n),
            "arm": arm,
            "visit": visit.astype(int),
            "conversion": conversion.astype(int),
            "revenue": revenue,
            "pre_spend": history,
            "recency": rng.integers(1, 13, n),
            "history_segment": history_segment,
            "channel": rng.choice(["Web", "Phone", "Multichannel"], n, p=[0.44, 0.44, 0.12]),
            "zip_code": rng.choice(["Surburban", "Urban", "Rural"], n, p=[0.45, 0.4, 0.15]),
            "newbie": np.where(newbie, "Yes", "No"),
        }
    )


def load_experiment(raw_dir: str | Path = RAW_DIR) -> tuple[pd.DataFrame, str]:
    """Return the experiment and its source. RETAILLAB_DEMO=1 forces synthetic data."""
    path = Path(raw_dir) / "hillstrom.csv"
    if path.exists() and os.environ.get("RETAILLAB_DEMO") != "1":
        return load_hillstrom(path), "hillstrom"
    return demo_email(), "demo"


def campaign_view(data: pd.DataFrame, variant: str = "any") -> pd.DataFrame:
    """Two-arm view: control versus one e-mail, or versus either e-mail pooled."""
    if variant not in VARIANTS:
        raise ValueError(f"unknown variant: {variant}")
    arms = ["control", "mens", "womens"] if variant == "any" else ["control", variant]
    view = data[data.arm.isin(arms)].copy()
    view["arm"] = np.where(view.arm == "control", "control", "treatment")
    return view
