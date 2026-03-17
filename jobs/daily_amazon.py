from datetime import datetime
from pathlib import Path

import pandas as pd

from scraper.amazon.runner import main as run_amazon


BASE_DIR = Path(__file__).resolve().parents[1]
REPORT_DIR = BASE_DIR / "reports" / "amazon"
REPORT_DIR.mkdir(parents=True, exist_ok=True)


def json_to_csv(json_path: Path) -> Path:
    df = pd.read_json(json_path)
    today = datetime.now().strftime("%Y-%m-%d")
    out_path = REPORT_DIR / f"{today}-products.csv"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    return out_path


def job() -> None:
    json_path = run_amazon()
    if json_path:
        csv_path = json_to_csv(json_path)
        print(f"JSON: {json_path}")
        print(f"CSV : {csv_path}")
    else:
        print("No products scraped.")


if __name__ == "__main__":
    job()

