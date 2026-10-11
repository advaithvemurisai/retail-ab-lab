"""Write web/public/data/readout.json, the statistics the web API prices per request."""

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(ROOT / "src"))
from retaillab.data import fetch_public_files, load_experiment
from retaillab.finance import load_margins
from retaillab.webdata import build_readout

if __name__ == "__main__":
    demo = os.environ.get("RETAILLAB_DEMO") == "1"
    if not demo:
        # A deploy must not quietly ship synthetic numbers, so a failed download fails the build.
        fetch_public_files()
    data, source = load_experiment()
    margins = load_margins(force_demo=demo)
    target = ROOT / "web" / "public" / "data" / "readout.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(build_readout(data, source, margins), separators=(",", ":"), allow_nan=False))
    print(f"Wrote {target.relative_to(ROOT)} ({target.stat().st_size / 1024:,.0f} KB)")
    print(f"Source: {source} ({len(data):,} customers), {margins['source']} margins")
