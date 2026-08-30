# Warehouse Setup

Phase 2 loads the raw cosmetics CSV files into a local DuckDB warehouse and exports a compressed Parquet copy for repeated analysis.

## Inputs

Raw Kaggle files must be present under:

```text
data/raw/cosmetics/
```

The raw files are ignored by git. Download them with:

```bash
python scripts/download_cosmetics_dataset.py
```

## Command

Install dependencies:

```bash
python -m pip install -r requirements.txt
```

Profile raw files first:

```bash
python scripts/profile_raw_cosmetics.py
```

Create the warehouse:

```bash
python scripts/ingest_raw_events.py
```

Default outputs:

- DuckDB database: `data/warehouse/retailpulse.duckdb`
- Raw typed table: `raw_events`
- Load metadata table: `raw_load_log`
- Parquet copy: `data/processed/events/`

## Ingestion Contract

`raw_events` contains one row per source event with these fields:

| Field | Type | Notes |
| --- | --- | --- |
| `event_time` | timestamp | Parsed from raw `event_time`. |
| `event_month` | date | Month bucket for partitioning and analysis. |
| `event_type` | varchar | Expected values are `view`, `cart`, `remove_from_cart`, and `purchase`. |
| `product_id` | bigint | Parsed product identifier. |
| `category_id` | bigint | Parsed category identifier. |
| `category_code` | varchar | Blank strings normalized to null. |
| `brand` | varchar | Lowercased and blank strings normalized to null. |
| `price` | double | Parsed product price. |
| `user_id` | bigint | Parsed permanent user identifier. |
| `user_session` | varchar | Blank strings normalized to null. |
| `source_file` | varchar | Source CSV file name. |

## Phase 2 Gate

The ingestion script checks that:

- At least one raw CSV exists.
- Required headers are present for every source file.
- Each file's loaded row count matches its raw scan count.
- The generated database and Parquet directory are created from reproducible commands.

Run the validation SQL after ingestion:

```bash
duckdb data/warehouse/retailpulse.duckdb -c ".read sql/02_ingestion_validation.sql"
```
