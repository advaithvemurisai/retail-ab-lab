import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from retaillab.demo import demo_email
from retaillab.warehouse import build_warehouse

root = Path(__file__).parents[1]
hillstrom = root / "data" / "raw" / "hillstrom.csv"
if hillstrom.exists():
    import pandas as pd

    raw = pd.read_csv(hillstrom)
    frame = raw.rename(
        columns={"segment": "arm", "conversion": "conversion", "spend": "revenue"}
    )
    frame["arm"] = frame["arm"].replace(
        {"No E-Mail": "control", "Mens E-Mail": "treatment", "Womens E-Mail": "treatment"}
    )
    frame["unit_id"] = range(len(frame))
    frame["pre_spend"] = frame["history"]
    frame["segment"] = frame["history_segment"]
    frame = frame[["unit_id", "arm", "conversion", "revenue", "pre_spend", "segment"]]
    source = "Hillstrom"
else:
    frame = demo_email()
    source = "deterministic demo"

build_warehouse(root / "data" / "retaillab.duckdb", {"mart_experiment": frame})
print(f"Built {source} warehouse at data/retaillab.duckdb")
