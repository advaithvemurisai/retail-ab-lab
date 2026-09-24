"""Download public source files at runtime. Raw files are git-ignored."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "src"))
from retaillab.data import PUBLIC_FILES, RAW_DIR, fetch_public_files

if __name__ == "__main__":
    downloaded = fetch_public_files()
    for filename in PUBLIC_FILES:
        status = "Downloaded" if filename in downloaded else "Exists"
        print(f"{status}: {RAW_DIR / filename}")
    print("X5 and Kaggle files require a manual download and terms review. See DATA_SOURCES.md.")
