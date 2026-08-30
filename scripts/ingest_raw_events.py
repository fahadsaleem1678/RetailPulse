"""Load raw cosmetics ecommerce CSV files into DuckDB.

This Phase 2 command creates a typed raw_events table, appends a load log for
each source file, reconciles loaded row counts, and exports compressed Parquet
files for downstream modeling.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import uuid
from datetime import datetime, timezone
from pathlib import Path


EXPECTED_COLUMNS = [
    "event_time",
    "event_type",
    "product_id",
    "category_id",
    "category_code",
    "brand",
    "price",
    "user_id",
    "user_session",
]
DEFAULT_RAW_DIR = Path("data/raw/cosmetics")
DEFAULT_DATABASE = Path("data/warehouse/retailpulse.duckdb")
DEFAULT_PARQUET_DIR = Path("data/processed/events")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest raw cosmetics events into DuckDB.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--parquet-dir", type=Path, default=DEFAULT_PARQUET_DIR)
    parser.add_argument(
        "--skip-parquet",
        action="store_true",
        help="Load DuckDB tables without exporting the processed Parquet copy.",
    )
    return parser.parse_args()


def require_duckdb():
    try:
        import duckdb
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency: duckdb. Install dependencies with "
            "`python -m pip install -r requirements.txt`."
        ) from exc
    return duckdb


def raw_csv_files(raw_dir: Path) -> list[Path]:
    files = sorted(raw_dir.glob("*.csv"))
    if not files:
        raise SystemExit(
            f"No CSV files found in {raw_dir}. Run `python scripts/download_cosmetics_dataset.py` first."
        )
    return files


def read_header(path: Path) -> list[str]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.reader(handle)
        try:
            return next(reader)
        except StopIteration as exc:
            raise SystemExit(f"CSV file is empty: {path}") from exc


def validate_header(path: Path) -> None:
    header = read_header(path)
    missing = [column for column in EXPECTED_COLUMNS if column not in header]
    if missing:
        raise SystemExit(f"{path.name} is missing required columns: {', '.join(missing)}")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sql_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def source_relation(path: Path) -> str:
    return f"read_csv_auto('{sql_path(path)}', header = true, all_varchar = true)"


def create_tables(con) -> None:
    con.execute("DROP TABLE IF EXISTS raw_events")
    con.execute(
        """
        CREATE TABLE raw_events (
            event_time TIMESTAMP,
            event_month DATE,
            event_type VARCHAR,
            product_id BIGINT,
            category_id BIGINT,
            category_code VARCHAR,
            brand VARCHAR,
            price DOUBLE,
            user_id BIGINT,
            user_session VARCHAR,
            source_file VARCHAR
        )
        """
    )
    con.execute(
        """
        CREATE TABLE IF NOT EXISTS raw_load_log (
            load_id VARCHAR,
            loaded_at TIMESTAMP,
            source_file VARCHAR,
            source_path VARCHAR,
            source_sha256 VARCHAR,
            file_size_bytes BIGINT,
            raw_row_count BIGINT,
            loaded_row_count BIGINT,
            min_event_time TIMESTAMP,
            max_event_time TIMESTAMP
        )
        """
    )


def source_stats(con, relation: str) -> tuple[int, datetime | None, datetime | None]:
    row = con.execute(
        f"""
        SELECT
            count(*) AS row_count,
            min(try_cast(event_time AS TIMESTAMP)) AS min_event_time,
            max(try_cast(event_time AS TIMESTAMP)) AS max_event_time
        FROM {relation}
        """
    ).fetchone()
    return int(row[0]), row[1], row[2]


def insert_file(con, path: Path, load_id: str, loaded_at: datetime) -> None:
    relation = source_relation(path)
    raw_row_count, min_event_time, max_event_time = source_stats(con, relation)

    con.execute(
        f"""
        INSERT INTO raw_events
        SELECT
            try_cast(event_time AS TIMESTAMP) AS event_time,
            date_trunc('month', try_cast(event_time AS TIMESTAMP))::DATE AS event_month,
            event_type,
            try_cast(product_id AS BIGINT) AS product_id,
            try_cast(category_id AS BIGINT) AS category_id,
            nullif(trim(category_code), '') AS category_code,
            nullif(lower(trim(brand)), '') AS brand,
            try_cast(price AS DOUBLE) AS price,
            try_cast(user_id AS BIGINT) AS user_id,
            nullif(trim(user_session), '') AS user_session,
            ? AS source_file
        FROM {relation}
        """,
        [path.name],
    )

    loaded_row_count = int(
        con.execute("SELECT count(*) FROM raw_events WHERE source_file = ?", [path.name]).fetchone()[0]
    )
    if loaded_row_count != raw_row_count:
        raise SystemExit(
            f"Loaded row count mismatch for {path.name}: raw={raw_row_count}, loaded={loaded_row_count}"
        )

    con.execute(
        """
        INSERT INTO raw_load_log
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            load_id,
            loaded_at,
            path.name,
            str(path),
            sha256(path),
            path.stat().st_size,
            raw_row_count,
            loaded_row_count,
            min_event_time,
            max_event_time,
        ],
    )


def export_parquet(con, parquet_dir: Path) -> None:
    parquet_dir.mkdir(parents=True, exist_ok=True)
    con.execute(
        f"""
        COPY raw_events
        TO '{sql_path(parquet_dir)}'
        (FORMAT PARQUET, COMPRESSION ZSTD, PARTITION_BY (event_month), OVERWRITE_OR_IGNORE TRUE)
        """
    )


def main() -> None:
    args = parse_args()
    files = raw_csv_files(args.raw_dir)
    for path in files:
        validate_header(path)

    duckdb = require_duckdb()
    args.database.parent.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(args.database))

    create_tables(con)
    load_id = str(uuid.uuid4())
    loaded_at = datetime.now(timezone.utc)
    for path in files:
        insert_file(con, path, load_id, loaded_at)

    if not args.skip_parquet:
        export_parquet(con, args.parquet_dir)

    total_rows = con.execute("SELECT count(*) FROM raw_events").fetchone()[0]
    print(f"Loaded {total_rows} row(s) from {len(files)} file(s) into {args.database}")
    if not args.skip_parquet:
        print(f"Exported Parquet copy to {args.parquet_dir}")


if __name__ == "__main__":
    main()
