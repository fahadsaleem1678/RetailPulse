"""Profile raw cosmetics ecommerce CSV files and write a manifest/report.

The script expects Kaggle CSV files under data/raw/cosmetics. It keeps all raw
files out of git and writes small, reviewable outputs under data/manifest and
docs.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DATASET_SOURCE = "https://www.kaggle.com/datasets/mkechinov/ecommerce-events-history-in-cosmetics-shop"
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
EXPECTED_EVENT_TYPES = {"view", "cart", "remove_from_cart", "purchase"}
DEFAULT_RAW_DIR = Path("data/raw/cosmetics")
DEFAULT_MANIFEST_PATH = Path("data/manifest/raw_cosmetics_manifest.csv")
DEFAULT_REPORT_PATH = Path("docs/raw-data-profile.md")


@dataclass(frozen=True)
class FileProfile:
    file_name: str
    file_size_bytes: int
    sha256: str
    header: list[str]
    missing_columns: list[str]
    unexpected_columns: list[str]
    row_count: int
    min_event_time: str | None
    max_event_time: str | None
    distinct_users: int
    distinct_sessions: int
    duplicate_rows: int
    min_price: float | None
    max_price: float | None
    unparseable_price_rows: int
    negative_price_rows: int
    null_counts: dict[str, int]
    event_type_counts: dict[str, int]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Profile raw cosmetics ecommerce CSV files.")
    parser.add_argument("--raw-dir", type=Path, default=DEFAULT_RAW_DIR)
    parser.add_argument("--manifest", type=Path, default=DEFAULT_MANIFEST_PATH)
    parser.add_argument("--report", type=Path, default=DEFAULT_REPORT_PATH)
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


def csv_files(raw_dir: Path) -> list[Path]:
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


def file_sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def sql_relation(path: Path) -> str:
    safe_path = path.as_posix().replace("'", "''")
    return f"read_csv_auto('{safe_path}', header = true, all_varchar = true)"


def scalar(con, query: str):
    return con.execute(query).fetchone()[0]


def query_dict(con, query: str) -> dict[str, int]:
    return {str(key): int(value) for key, value in con.execute(query).fetchall()}


def profile_file(con, path: Path) -> FileProfile:
    header = read_header(path)
    missing_columns = [column for column in EXPECTED_COLUMNS if column not in header]
    unexpected_columns = [column for column in header if column not in EXPECTED_COLUMNS]
    if missing_columns:
        raise SystemExit(f"{path.name} is missing required columns: {', '.join(missing_columns)}")

    relation = sql_relation(path)
    row = con.execute(
        f"""
        SELECT
            count(*) AS row_count,
            min(try_cast(event_time AS TIMESTAMP))::VARCHAR AS min_event_time,
            max(try_cast(event_time AS TIMESTAMP))::VARCHAR AS max_event_time,
            count(DISTINCT user_id) AS distinct_users,
            count(DISTINCT user_session) AS distinct_sessions,
            min(try_cast(price AS DOUBLE)) AS min_price,
            max(try_cast(price AS DOUBLE)) AS max_price,
            sum(CASE WHEN try_cast(price AS DOUBLE) IS NULL THEN 1 ELSE 0 END) AS unparseable_price_rows,
            sum(CASE WHEN try_cast(price AS DOUBLE) < 0 THEN 1 ELSE 0 END) AS negative_price_rows
        FROM {relation}
        """
    ).fetchone()

    null_counts = {}
    for column in ["category_code", "brand", "user_session", "price"]:
        null_counts[column] = int(
            scalar(
                con,
                f"""
                SELECT sum(CASE WHEN {column} IS NULL OR trim({column}) = '' THEN 1 ELSE 0 END)
                FROM {relation}
                """,
            )
            or 0
        )

    event_type_counts = query_dict(
        con,
        f"""
        SELECT event_type, count(*)
        FROM {relation}
        GROUP BY event_type
        ORDER BY event_type
        """,
    )

    duplicate_rows = int(
        scalar(
            con,
            f"""
            SELECT coalesce(sum(row_count - 1), 0)
            FROM (
                SELECT
                    event_time,
                    event_type,
                    product_id,
                    category_id,
                    category_code,
                    brand,
                    price,
                    user_id,
                    user_session,
                    count(*) AS row_count
                FROM {relation}
                GROUP BY
                    event_time,
                    event_type,
                    product_id,
                    category_id,
                    category_code,
                    brand,
                    price,
                    user_id,
                    user_session
                HAVING count(*) > 1
            ) duplicates
            """,
        )
        or 0
    )

    return FileProfile(
        file_name=path.name,
        file_size_bytes=path.stat().st_size,
        sha256=file_sha256(path),
        header=header,
        missing_columns=missing_columns,
        unexpected_columns=unexpected_columns,
        row_count=int(row[0]),
        min_event_time=row[1],
        max_event_time=row[2],
        distinct_users=int(row[3]),
        distinct_sessions=int(row[4]),
        min_price=row[5],
        max_price=row[6],
        unparseable_price_rows=int(row[7] or 0),
        negative_price_rows=int(row[8] or 0),
        duplicate_rows=duplicate_rows,
        null_counts=null_counts,
        event_type_counts=event_type_counts,
    )


def write_manifest(path: Path, profiles: Iterable[FileProfile]) -> None:
    rows = list(profiles)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "file_name",
                "source",
                "file_size_bytes",
                "sha256",
                "row_count",
                "min_event_time",
                "max_event_time",
                "distinct_users",
                "distinct_sessions",
                "duplicate_rows",
            ],
        )
        writer.writeheader()
        for profile in rows:
            writer.writerow(
                {
                    "file_name": profile.file_name,
                    "source": DATASET_SOURCE,
                    "file_size_bytes": profile.file_size_bytes,
                    "sha256": profile.sha256,
                    "row_count": profile.row_count,
                    "min_event_time": profile.min_event_time,
                    "max_event_time": profile.max_event_time,
                    "distinct_users": profile.distinct_users,
                    "distinct_sessions": profile.distinct_sessions,
                    "duplicate_rows": profile.duplicate_rows,
                }
            )


def percent(part: int, total: int) -> str:
    if total == 0:
        return "0.00%"
    return f"{part / total:.2%}"


def write_report(path: Path, profiles: list[FileProfile]) -> None:
    total_rows = sum(profile.row_count for profile in profiles)
    event_types = sorted({key for profile in profiles for key in profile.event_type_counts})
    unexpected_event_types = sorted(set(event_types) - EXPECTED_EVENT_TYPES)

    lines = [
        "# Raw Data Profile: Cosmetics Ecommerce Events",
        "",
        f"Source: {DATASET_SOURCE}",
        "",
        "## Files",
        "",
        "| File | Rows | Date Range | Size Bytes | Duplicate Rows |",
        "| --- | ---: | --- | ---: | ---: |",
    ]
    for profile in profiles:
        lines.append(
            "| "
            f"{profile.file_name} | {profile.row_count} | {profile.min_event_time} to {profile.max_event_time} | "
            f"{profile.file_size_bytes} | {profile.duplicate_rows} |"
        )

    lines.extend(
        [
            "",
            "## Header Check",
            "",
            "Required columns: " + ", ".join(f"`{column}`" for column in EXPECTED_COLUMNS),
            "",
            "| File | Missing Required Columns | Unexpected Columns |",
            "| --- | --- | --- |",
        ]
    )
    for profile in profiles:
        missing = ", ".join(profile.missing_columns) if profile.missing_columns else "None"
        unexpected = ", ".join(profile.unexpected_columns) if profile.unexpected_columns else "None"
        lines.append(f"| {profile.file_name} | {missing} | {unexpected} |")

    lines.extend(
        [
            "",
            "## Event Type Distribution",
            "",
            "| Event Type | Rows | Share |",
            "| --- | ---: | ---: |",
        ]
    )
    for event_type in event_types:
        count = sum(profile.event_type_counts.get(event_type, 0) for profile in profiles)
        lines.append(f"| {event_type} | {count} | {percent(count, total_rows)} |")
    if unexpected_event_types:
        lines.extend(["", "Unexpected event types: " + ", ".join(unexpected_event_types)])
    else:
        lines.extend(["", "Unexpected event types: None"])

    lines.extend(
        [
            "",
            "## Null and Blank Rates",
            "",
            "| Field | Missing Rows | Missing Share |",
            "| --- | ---: | ---: |",
        ]
    )
    for column in ["category_code", "brand", "user_session", "price"]:
        count = sum(profile.null_counts[column] for profile in profiles)
        lines.append(f"| {column} | {count} | {percent(count, total_rows)} |")

    min_prices = [profile.min_price for profile in profiles if profile.min_price is not None]
    max_prices = [profile.max_price for profile in profiles if profile.max_price is not None]
    lines.extend(
        [
            "",
            "## Price Quality",
            "",
            f"Minimum parsed price: {min(min_prices) if min_prices else 'n/a'}",
            f"Maximum parsed price: {max(max_prices) if max_prices else 'n/a'}",
            f"Unparseable price rows: {sum(profile.unparseable_price_rows for profile in profiles)}",
            f"Negative price rows: {sum(profile.negative_price_rows for profile in profiles)}",
            "",
            "## Cardinality",
            "",
            "| File | Distinct Users | Distinct Sessions |",
            "| --- | ---: | ---: |",
        ]
    )
    for profile in profiles:
        lines.append(f"| {profile.file_name} | {profile.distinct_users} | {profile.distinct_sessions} |")

    lines.extend(
        [
            "",
            "## Phase 1 Gate",
            "",
            "- Required headers are present for every profiled file.",
            "- Event types are checked against `view`, `cart`, `remove_from_cart`, and `purchase`.",
            "- Date coverage, duplicate rows, key null rates, price quality, users, and sessions are reported.",
        ]
    )

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    args = parse_args()
    files = csv_files(args.raw_dir)
    duckdb = require_duckdb()

    con = duckdb.connect(database=":memory:")
    profiles = [profile_file(con, path) for path in files]

    write_manifest(args.manifest, profiles)
    write_report(args.report, profiles)

    print(f"Profiled {len(profiles)} file(s).")
    print(f"Wrote manifest: {args.manifest}")
    print(f"Wrote report: {args.report}")


if __name__ == "__main__":
    main()

