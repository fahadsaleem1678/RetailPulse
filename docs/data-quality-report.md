# Data Quality Report

Phase 3 creates analyst-friendly staging and quality tables after raw events have been loaded into DuckDB.

Run:

```bash
python scripts/run_duckdb_sql.py sql/03_staging_quality.sql
```

## Staging Model

`stg_events` keeps one row per raw event and adds:

- `event_id`: stable hash of `source_file` and `source_row_number`.
- `category_code`: original category with missing values converted to `unknown_category`.
- `brand`: original brand with missing values converted to `unknown_brand`.
- `original_category_code` and `original_brand`: raw nullable values for auditability.
- Quality flags for invalid timestamps, event types, prices, users, sessions, and products.
- `event_sequence_in_session`, `previous_event_type`, and `next_event_type` for ordered session analysis.

## Generated Quality Tables

- `dq_stg_events_summary`
- `dq_event_type_counts`
- `dq_monthly_freshness`
- `dq_unknown_dimension_counts`
- `dq_session_ordering_checks`

## Phase 3 Gate

After raw files are loaded, confirm that:

- `dq_event_type_counts` includes only `view`, `cart`, `remove_from_cart`, and `purchase`.
- Required field null counts are reviewed in `dq_stg_events_summary`.
- Invalid purchase prices are zero or documented before analysis.
- Unknown category and brand counts are reported instead of filtered.
- Session ordering uses `event_time`, `source_file`, and `source_row_number` as deterministic ordering keys.

Counts are pending until the Kaggle CSV files are downloaded and ingested locally.
