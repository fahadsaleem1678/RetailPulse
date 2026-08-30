"""Prepare raw cosmetics ecommerce event files under data/raw/cosmetics.

By default the script uses a local data/archive.zip if present. If the archive is
missing, it falls back to downloading the Kaggle dataset with kagglehub.
"""

from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path


DATASET = "mkechinov/ecommerce-events-history-in-cosmetics-shop"
DEFAULT_ARCHIVE = Path("data/archive.zip")
RAW_DIR = Path("data/raw/cosmetics")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Prepare raw cosmetics CSV files.")
    parser.add_argument("--archive", type=Path, default=DEFAULT_ARCHIVE)
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite existing raw CSV files from the archive or Kaggle cache.",
    )
    return parser.parse_args()


def copy_csv(source_file: Path, target_file: Path, force: bool) -> None:
    if target_file.exists() and not force:
        print(f"Keeping existing {target_file}")
        return
    shutil.copy2(source_file, target_file)
    print(f"Copied {source_file.name} -> {target_file}")


def extract_archive(archive_path: Path, force: bool) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as archive:
        csv_entries = sorted(
            (entry for entry in archive.infolist() if entry.filename.lower().endswith(".csv")),
            key=lambda entry: entry.filename,
        )
        if not csv_entries:
            raise SystemExit(f"No CSV files found in archive: {archive_path}")

        for entry in csv_entries:
            target_file = RAW_DIR / Path(entry.filename).name
            if target_file.exists() and not force:
                print(f"Keeping existing {target_file}")
                continue
            with archive.open(entry) as source, target_file.open("wb") as target:
                shutil.copyfileobj(source, target)
            print(f"Extracted {entry.filename} -> {target_file}")

    print(f"Prepared {len(csv_entries)} CSV file(s) from {archive_path} into {RAW_DIR}")


def download_from_kaggle(force: bool) -> None:
    try:
        import kagglehub
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: kagglehub. Install it with `pip install kagglehub` "
            "and make sure Kaggle credentials are configured. Alternatively place "
            "the Kaggle archive at data/archive.zip."
        ) from exc

    RAW_DIR.mkdir(parents=True, exist_ok=True)
    source_dir = Path(kagglehub.dataset_download(DATASET))

    csv_files = sorted(source_dir.glob("*.csv"))
    if not csv_files:
        raise SystemExit(f"No CSV files found after downloading {DATASET} to {source_dir}")

    for source_file in csv_files:
        copy_csv(source_file, RAW_DIR / source_file.name, force)

    print(f"Prepared {len(csv_files)} CSV file(s) from {DATASET} into {RAW_DIR}")


def main() -> None:
    args = parse_args()
    if args.archive.exists():
        extract_archive(args.archive, args.force)
    else:
        download_from_kaggle(args.force)


if __name__ == "__main__":
    main()



