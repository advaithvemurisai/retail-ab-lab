"""Retail unit economics and campaign allocation."""

from __future__ import annotations

import numpy as np
import pandas as pd


def load_sector_margins(path: str) -> pd.DataFrame:
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


def benchmark_margins(path: str) -> dict[str, object]:
    """Return the exact retail sectors used by the app and the workbook date."""
    margins = load_sector_margins(path)
    wanted = ["Apparel", "Retail (Grocery and Food)", "Restaurant/Dining"]
    selected = margins[margins.sector.isin(wanted)].copy()
    missing = sorted(set(wanted) - set(selected.sector))
    if missing:
        raise ValueError(f"missing expected sectors: {', '.join(missing)}")
    return {"as_of": "January 2026", "margins": selected.set_index("sector").to_dict("index")}


def break_even_lift(cost_per_contact: float, baseline_revenue: float, gross_margin: float) -> float:
    return (
        cost_per_contact / (baseline_revenue * gross_margin)
        if baseline_revenue > 0 and gross_margin > 0
        else np.inf
    )


def pnl(data: pd.DataFrame, gross_margin: float, contact_cost: float = 0.0) -> dict[str, float]:
    c, t = data[data.arm == "control"], data[data.arm == "treatment"]
    incremental_revenue = (t.revenue.mean() - c.revenue.mean()) * len(t)
    gross_profit = incremental_revenue * gross_margin
    marketing_cost = len(t) * contact_cost
    contribution = gross_profit - marketing_cost
    return {
        "incremental_revenue": float(incremental_revenue),
        "gross_profit": float(gross_profit),
        "marketing_cost": float(marketing_cost),
        "contribution": float(contribution),
        "roi": float(contribution / marketing_cost) if marketing_cost else np.inf,
    }


def attributed_incremental(data: pd.DataFrame) -> dict[str, float]:
    c, t = data[data.arm == "control"], data[data.arm == "treatment"]
    attributed = float(t.revenue.sum())
    incremental = float((t.revenue.mean() - c.revenue.mean()) * len(t))
    return {
        "attributed": attributed,
        "incremental": incremental,
        "gap_pct": float(1 - incremental / attributed) if attributed else np.nan,
    }


def greedy_allocation(rows: pd.DataFrame, cap: int) -> pd.DataFrame:
    result = rows.sort_values("profit_per_dollar", ascending=False).copy()
    result["selected"] = False
    result["send_count"] = 0
    remaining = cap
    for index, row in result.iterrows():
        amount = min(remaining, int(row.audience))
        selected = amount > 0 and row.profit_per_dollar > 0
        result.loc[index, "selected"] = selected
        result.loc[index, "send_count"] = amount if selected else 0
        remaining -= int(result.loc[index, "send_count"])
    return result
