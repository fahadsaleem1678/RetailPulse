"""Run a SQL file against the local RetailPulse DuckDB warehouse."""

from __future__ import annotations

import argparse
from pathlib import Path


DEFAULT_DATABASE = Path("data/warehouse/retailpulse.duckdb")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a SQL file against DuckDB.")
    parser.add_argument("sql_file", type=Path)
    parser.add_argument("--database", type=Path, default=DEFAULT_DATABASE)
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


def connect_for_write(duckdb, database: Path):
    try:
        return duckdb.connect(str(database))
    except duckdb.IOException as exc:
        message = str(exc)
        if "being used by another process" in message or "Conflicting lock" in message:
            raise SystemExit(
                f"DuckDB database is locked at {database}. Close the Streamlit dashboard "
                "or any other DuckDB connection, then rerun this command."
            ) from exc
        raise


def main() -> None:
    args = parse_args()
    if not args.database.exists():
        raise SystemExit(
            f"DuckDB database not found at {args.database}. Run `python scripts/ingest_raw_events.py` first."
        )
    if not args.sql_file.exists():
        raise SystemExit(f"SQL file not found: {args.sql_file}")

    duckdb = require_duckdb()
    sql = args.sql_file.read_text(encoding="utf-8")
    con = connect_for_write(duckdb, args.database)
    try:
        con.execute(sql)
        print(f"Ran {args.sql_file} against {args.database}")
    finally:
        con.close()


if __name__ == "__main__":
    main()
