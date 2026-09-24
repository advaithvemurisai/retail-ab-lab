"""Write the RetailLab star schema to data/retaillab.duckdb."""

import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
from retaillab.data import load_experiment
from retaillab.finance import load_margins
from retaillab.warehouse import build_warehouse, table_counts

CONTACT_COST = 0.18

if __name__ == "__main__":
    data, source = load_experiment()
    margins = load_margins()
    target = ROOT / "data" / "retaillab.duckdb"
    connection = build_warehouse(target, data, margins, CONTACT_COST)
    print(table_counts(connection).to_string(index=False))
    connection.close()
    print(f"Built {source} warehouse ({margins['source']} margins) at {target.relative_to(ROOT)}")
