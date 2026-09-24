"""Download public source files at runtime. Raw files are git-ignored."""

from pathlib import Path
from urllib.request import urlretrieve

RAW = Path(__file__).parents[1] / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

PUBLIC_FILES = {
    "hillstrom.csv": "http://www.minethatdata.com/Kevin_Hillstrom_MineThatData_E-MailAnalytics_DataMiningChallenge_2008.03.20.csv",
    "margin.xls": "https://www.stern.nyu.edu/~adamodar/pc/datasets/margin.xls",
}


def fetch_public_files() -> None:
    for filename, url in PUBLIC_FILES.items():
        destination = RAW / filename
        if destination.exists():
            print(f"Exists: {destination}")
            continue
        print(f"Downloading {filename} from {url}")
        urlretrieve(url, destination)
    print("X5 and Kaggle files require a manual download and terms review. See DATA_SOURCES.md.")


if __name__ == "__main__":
    fetch_public_files()
