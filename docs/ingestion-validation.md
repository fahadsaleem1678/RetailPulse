# Ingestion Validation Report

Phase 2 loaded the extracted cosmetics ecommerce CSV files into `data/warehouse/retailpulse.duckdb`.

## Row Count Reconciliation

Total loaded rows: 20,692,840

| Source File | Raw Rows | Loaded Rows | Min Event Time | Max Event Time |
| --- | ---: | ---: | --- | --- |
| 2019-Dec.csv | 3,533,286 | 3,533,286 | 2019-12-01 00:00:00 | 2019-12-31 23:59:57 |
| 2019-Nov.csv | 4,635,837 | 4,635,837 | 2019-11-01 00:00:02 | 2019-11-30 23:59:58 |
| 2019-Oct.csv | 4,102,283 | 4,102,283 | 2019-10-01 00:00:00 | 2019-10-31 23:59:54 |
| 2020-Feb.csv | 4,156,682 | 4,156,682 | 2020-02-01 00:00:01 | 2020-02-29 23:59:59 |
| 2020-Jan.csv | 4,264,752 | 4,264,752 | 2020-01-01 00:00:00 | 2020-01-31 23:59:58 |

## Required Field Nulls

| Field | Null Rows |
| --- | ---: |
| `event_time` | 0 |
| `event_type` | 0 |
| `product_id` | 0 |
| `price` | 0 |
| `user_id` | 0 |
| `user_session` | 4,598 |

## Event Types

| Event Type | Rows |
| --- | ---: |
| `view` | 9,657,821 |
| `cart` | 5,768,333 |
| `remove_from_cart` | 3,979,679 |
| `purchase` | 1,287,007 |

## Phase 2 Gate

- Required headers were validated before load.
- Each source file's loaded row count matched its raw scan count.
- Date min/max values match the raw manifest.
- No required column loaded as entirely null.
- The known missing-session exception affects 4,598 rows and is handled downstream by staging/session mart filters.
- A compressed Parquet copy was generated under `data/processed/events/`.
