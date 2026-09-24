"""DuckDB warehouse helpers. Raw downloads stay outside version control."""

from __future__ import annotations

from pathlib import Path

import duckdb
import pandas as pd


def build_warehouse(path: str | Path, tables: dict[str, pd.DataFrame]) -> None:
    connection = duckdb.connect(str(path))
    for name, frame in tables.items():
        connection.register("frame", frame)
        connection.execute(f"CREATE OR REPLACE TABLE {name} AS SELECT * FROM frame")
    connection.close()


def query(path: str | Path, sql: str) -> pd.DataFrame:
    connection = duckdb.connect(str(path), read_only=True)
    result = connection.execute(sql).df()
    connection.close()
    return result
