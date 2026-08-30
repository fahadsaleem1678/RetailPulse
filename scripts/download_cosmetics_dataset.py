"""Download the Kaggle cosmetics ecommerce events dataset into data/raw/cosmetics.

Requires Kaggle authentication that works with kagglehub. Typically this means
being logged in through Kaggle credentials on the machine running the script.
"""

from __future__ import annotations

import shutil
from pathlib import Path


DATASET = "mkechinov/ecommerce-events-history-in-cosmetics-shop"
RAW_DIR = Path("data/raw/cosmetics")


def main() -> None:
    try:
        import kagglehub
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: kagglehub. Install it with `pip install kagglehub` "
            "and make sure Kaggle credentials are configured."
        ) from exc

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    source_dir = Path(kagglehub.dataset_download(DATASET))

    csv_files = sorted(source_dir.glob("*.csv"))
    if not csv_files:
        raise SystemExit(f"No CSV files found after downloading {DATASET} to {source_dir}")

    for source_file in csv_files:
        target_file = RAW_DIR / source_file.name
        shutil.copy2(source_file, target_file)
        print(f"Copied {source_file.name} -> {target_file}")

    print(f"Downloaded {len(csv_files)} CSV file(s) from {DATASET} into {RAW_DIR}")


if __name__ == "__main__":
    main()
