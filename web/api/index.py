"""Vercel entry point for the RetailLab API (src/retaillab/api.py)."""

import sys
from pathlib import Path

WEB = Path(__file__).resolve().parents[1]
# On Vercel the build copies the API's pure-Python modules into web/pylib; locally they come
# straight from src/.
for path in (WEB / "pylib", WEB.parent / "src"):
    if (path / "retaillab" / "api.py").exists():
        sys.path.insert(0, str(path))
        break

from retaillab.api import create_app

app = create_app(WEB / "public" / "data" / "readout.json")
