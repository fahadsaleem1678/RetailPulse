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
ORDER_BY = {
    "metric_session_funnel_by_month": "session_month",
    "metric_session_funnel_by_brand": "purchase_revenue DESC, viewed_sessions DESC, brand",
    "metric_session_funnel_by_category": "purchase_revenue DESC, viewed_sessions DESC, category_code",
    "metric_session_funnel_by_price_band": "entry_price_band",
    "metric_activity_cohort_retention": "first_activity_month, activity_month",
    "metric_purchase_cohort_retention": "first_purchase_month, purchase_month",
    "metric_rfm_segment_summary": "purchase_revenue DESC, rfm_segment",
}


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


def connect_read_only(duckdb, database: Path):
    try:
        return duckdb.connect(str(database), read_only=True)
    except duckdb.IOException as exc:
        message = str(exc)
        if "being used by another process" in message or "Conflicting lock" in message:
            raise SystemExit(
                f"DuckDB database is locked at {database}. Close the Streamlit dashboard "
                "or any other DuckDB connection, then rerun this command."
            ) from exc
        raise


def sql_path(path: Path) -> str:
    return path.as_posix().replace("'", "''")


def export_query(table: str) -> str:
    order_by = ORDER_BY.get(table)
    if order_by is None:
        return f"SELECT * FROM {table}"
    return f"SELECT * FROM {table} ORDER BY {order_by}"


def main() -> None:
    args = parse_args()
    if not args.database.exists():
        raise SystemExit(
            f"DuckDB database not found at {args.database}. Run the pipeline before exporting metrics."
        )

    duckdb = require_duckdb()
    con = connect_read_only(duckdb, args.database)
    try:
        existing_tables = {row[0] for row in con.execute("SHOW TABLES").fetchall()}
        missing_tables = [table for table in args.tables if table not in existing_tables]
        if missing_tables:
            raise SystemExit(
                "Metric tables are missing: "
                + ", ".join(missing_tables)
                + ". Run `python scripts/run_duckdb_sql.py analysis/core_metrics.sql`."
            )

        args.export_dir.mkdir(parents=True, exist_ok=True)
        for table in args.tables:
            target = args.export_dir / f"{table}.csv"
            con.execute(f"COPY ({export_query(table)}) TO '{sql_path(target)}' (HEADER, DELIMITER ',')")
            print(f"Exported {table} -> {target}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
