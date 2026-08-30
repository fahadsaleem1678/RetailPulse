"""Export generated metric tables from DuckDB to CSV files."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_DATABASE = Path("data/warehouse/retailpulse.duckdb")
DEFAULT_EXPORT_DIR = Path("data/exports")
DEFAULT_TABLES = [
    "metric_session_funnel_overall",
    "metric_session_funnel_by_month",
    "metric_session_funnel_by_brand",
    "metric_session_funnel_by_category",
    "metric_session_funnel_by_price_band",
    "metric_activity_cohort_retention",
    "metric_purchase_cohort_retention",
    "metric_rfm_segment_summary",
    "metric_revenue_reconciliation",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export RetailPulse metric tables to CSV.")
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
    parser.add_argument("--export-dir", type=Path, default=DEFAULT_EXPORT_DIR)
    parser.add_argument("--tables", nargs="*", default=DEFAULT_TABLES)
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


def sql_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def main() -> None:
    args = parse_args()
    if not args.database.exists():
        raise SystemExit(
            f"DuckDB database not found at {args.database}. Run the pipeline before exporting metrics."
        )

    duckdb = require_duckdb()
    con = duckdb.connect(str(args.database), read_only=True)
    existing_tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
    missing_tables = [table for table in args.tables if table not in existing_tables]
    if missing_tables:
        raise SystemExit(
            "Metric tables are missing: " + ", ".join(missing_tables) + ". Run `python scripts/run_duckdb_sql.py analysis/core_metrics.sql`."
        )

    args.export_dir.mkdir(parents=True, exist_ok=True)
    for table in args.tables:
        target = args.export_dir / f"{table}.csv"
        con.execute(f"COPY {table} TO '{sql_path(target)}' (HEADER, DELIMITER ',')")
        print(f"Exported {table} -> {target}")


if __name__ == "__main__":
    main()
