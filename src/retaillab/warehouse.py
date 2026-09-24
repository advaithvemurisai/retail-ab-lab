"""DuckDB warehouse. Raw downloads stay outside version control."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd

from .data import ARM_LABELS, ROOT

SQL = ROOT / "sql" / "warehouse.sql"
TABLES = [
    "dim_customer", "dim_campaign", "dim_sector_finance", "fact_exposure", "fact_sales",
    "mart_experiment", "mart_pnl",
]


def build_warehouse(
    path: str | Path, customers: pd.DataFrame, margins: dict[str, object], contact_cost: float
) -> duckdb.DuckDBPyConnection:
    """Build every table from `sql/warehouse.sql`. Use ':memory:' for an in-process copy."""
    campaigns = pd.DataFrame(
        {
            "arm": list(ARM_LABELS),
            "label": list(ARM_LABELS.values()),
            "contact_cost": [0.0 if arm == "control" else contact_cost for arm in ARM_LABELS],
        }
    )
    sectors = pd.DataFrame(
        [
            {"sector": sector, **values, "as_of": margins["as_of"]}
            for sector, values in margins["margins"].items()
        ]
    )
    connection = duckdb.connect(str(path))
    connection.register("stg_customers", customers)
    connection.register("stg_campaigns", campaigns)
    connection.register("stg_sectors", sectors)
    connection.execute(SQL.read_text())
    for name in ("stg_customers", "stg_campaigns", "stg_sectors"):
        connection.unregister(name)
    return connection


def table_counts(connection: duckdb.DuckDBPyConnection) -> pd.DataFrame:
    rows = [
        {"table": name, "rows": connection.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]}
        for name in TABLES
    ]
    return pd.DataFrame(rows)
