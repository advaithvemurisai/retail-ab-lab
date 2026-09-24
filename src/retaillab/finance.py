"""Retail unit economics and campaign allocation."""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from .data import RAW_DIR, ROOT

SECTORS = ["Apparel", "Retail (Grocery and Food)", "Restaurant/Dining"]
DEMO_MARGINS = ROOT / "data" / "fixtures" / "sector_margins_demo.csv"


def load_sector_margins(path: str | Path) -> pd.DataFrame:
    """Read Damodaran's workbook without embedding benchmark values in code."""
    frame = pd.read_excel(path, sheet_name="Industry Averages", header=8)
    frame.columns = [str(column).strip() for column in frame.columns]
    industry = next((column for column in frame.columns if "industry" in column.lower()), None)
    gross = next((column for column in frame.columns if "gross margin" in column.lower()), None)
    operating = next(
        (column for column in frame.columns if "operating margin" in column.lower()), None
    )
    if not all((industry, gross, operating)):
        raise ValueError("margin workbook must include industry, gross margin, and operating margin")
    result = frame[[industry, gross, operating]].copy()
    result.columns = ["sector", "gross_margin", "operating_margin"]
    for column in ("gross_margin", "operating_margin"):
        values = pd.to_numeric(result[column], errors="coerce")
        result[column] = np.where(values.abs() > 1, values / 100, values)
    return result.dropna(subset=["sector"])


def workbook_date(path: str | Path) -> str:
    header = pd.read_excel(path, sheet_name="Industry Averages", header=None, nrows=4)
    for _, row in header.iterrows():
        if str(row.iloc[0]).strip().lower().startswith("date updated"):
            return pd.Timestamp(row.iloc[1]).strftime("%B %Y")
    return "undated"


def benchmark_margins(path: str | Path) -> dict[str, object]:
    """The retail sectors used by the app, with the workbook's own date."""
    margins = load_sector_margins(path)
    selected = margins[margins.sector.isin(SECTORS)]
    missing = sorted(set(SECTORS) - set(selected.sector))
    if missing:
        raise ValueError(f"missing expected sectors: {', '.join(missing)}")
    return {
        "as_of": workbook_date(path),
        "source": "damodaran",
        "margins": selected.set_index("sector").reindex(SECTORS).to_dict("index"),
    }


def load_margins(raw_dir: str | Path = RAW_DIR, force_demo: bool = False) -> dict[str, object]:
    """Damodaran margins when the workbook is present, otherwise labelled placeholders."""
    path = Path(raw_dir) / "margin.xls"
    if path.exists() and not force_demo:
        return benchmark_margins(path)
    frame = pd.read_csv(DEMO_MARGINS)
    return {
        "as_of": "illustrative placeholder",
        "source": "placeholder",
        "margins": frame.set_index("sector").to_dict("index"),
    }


def break_even_lift(cost_per_contact: float, baseline_revenue: float, gross_margin: float) -> float:
    """Relative revenue lift at which gross profit from the lift equals contact cost."""
    if baseline_revenue <= 0 or gross_margin <= 0:
        return np.inf
    return cost_per_contact / (baseline_revenue * gross_margin)


def pnl(
    data: pd.DataFrame, gross_margin: float, contact_cost: float = 0.0, metric: str = "revenue"
) -> dict[str, float]:
    """Incremental P&L of treating the treatment arm, measured against control."""
    c, t = data[data.arm == "control"], data[data.arm == "treatment"]
    incremental_revenue = (t[metric].mean() - c[metric].mean()) * len(t)
    gross_profit = incremental_revenue * gross_margin
    marketing_cost = len(t) * contact_cost
    contribution = gross_profit - marketing_cost
    return {
        "customers_contacted": len(t),
        "incremental_revenue": float(incremental_revenue),
        "gross_profit": float(gross_profit),
        "marketing_cost": float(marketing_cost),
        "contribution": float(contribution),
        "roi": float(contribution / marketing_cost) if marketing_cost else np.inf,
    }


def contribution_distribution(
    difference_draws: np.ndarray, customers_contacted: int, gross_margin: float,
    contact_cost: float,
) -> dict[str, float]:
    """Scale per-customer lift draws to campaign contribution and summarise the downside."""
    contribution = (difference_draws * gross_margin - contact_cost) * customers_contacted
    low, high = np.quantile(contribution, [0.025, 0.975])
    return {
        "ci_low": float(low),
        "ci_high": float(high),
        "chance_of_loss": float(np.mean(contribution < 0)),
    }


def attributed_incremental(data: pd.DataFrame) -> dict[str, float]:
    """Revenue credited to the e-mail (every purchase by an e-mailed customer) versus causal."""
    c, t = data[data.arm == "control"], data[data.arm == "treatment"]
    attributed = float(t.revenue.sum())
    incremental = float((t.revenue.mean() - c.revenue.mean()) * len(t))
    return {
        "attributed": attributed,
        "incremental": incremental,
        "baseline": attributed - incremental,
        "gap_pct": float(1 - incremental / attributed) if attributed else np.nan,
    }


def greedy_allocation(
    rows: pd.DataFrame, cap: int, require_significant: bool = False
) -> pd.DataFrame:
    """Fill a send cap with the highest-return segments that are expected to make money."""
    result = rows.sort_values("profit_per_dollar", ascending=False).copy()
    result["selected"] = False
    result["send_count"] = 0
    remaining = cap
    for index, row in result.iterrows():
        eligible = row.profit_per_dollar > 0 and (
            not require_significant or bool(row.get("significant", False))
        )
        amount = min(remaining, int(row.audience)) if eligible else 0
        result.loc[index, "selected"] = amount > 0
        result.loc[index, "send_count"] = amount
        remaining -= amount
    return result
