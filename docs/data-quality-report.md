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

## Quality Summary

Total staged rows: 20,692,840

| Check | Rows |
| --- | ---: |
| Null `event_time` | 0 |
| Null `event_type` | 0 |
| Null `product_id` | 0 |
| Null `price` | 0 |
| Null `user_id` | 0 |
| Null `user_session` | 4,598 |
| Invalid event type | 0 |
| Invalid price | 131 |
| Unknown category | 20,339,246 |
| Unknown brand | 8,757,117 |

## Event Types

| Event Type | Rows |
| --- | ---: |
| `view` | 9,657,821 |
| `cart` | 5,768,333 |
| `remove_from_cart` | 3,979,679 |
| `purchase` | 1,287,007 |

## Monthly Freshness

| Month | First Event | Last Event | Rows | Users | Sessions |
| --- | --- | --- | ---: | ---: | ---: |
| 2019-10 | 2019-10-01 00:00:00 | 2019-10-31 23:59:54 | 4,102,283 | 399,664 | 873,960 |
| 2019-11 | 2019-11-01 00:00:02 | 2019-11-30 23:59:58 | 4,635,837 | 368,232 | 942,022 |
| 2019-12 | 2019-12-01 00:00:00 | 2019-12-31 23:59:57 | 3,533,286 | 370,154 | 839,812 |
| 2020-01 | 2020-01-01 00:00:00 | 2020-01-31 23:59:58 | 4,264,752 | 410,073 | 965,351 |
| 2020-02 | 2020-02-01 00:00:01 | 2020-02-29 23:59:59 | 4,156,682 | 391,055 | 931,668 |

## Unknown Dimensions

| Month | Unknown Category Rows | Unknown Brand Rows | Rows |
| --- | ---: | ---: | ---: |
| 2019-10 | 4,034,806 | 1,659,261 | 4,102,283 |
| 2019-11 | 4,560,089 | 1,986,029 | 4,635,837 |
| 2019-12 | 3,474,821 | 1,510,289 | 3,533,286 |
| 2020-01 | 4,190,033 | 1,775,630 | 4,264,752 |
| 2020-02 | 4,079,497 | 1,825,908 | 4,156,682 |

## Exceptions to Carry Forward

- 4,598 events have missing `user_session`; these are excluded from session reconstruction but remain visible in staged quality counts.
- 131 events have invalid negative prices.
- 126 invalid-price rows are purchase events; revenue metrics should use valid purchase prices only or explicitly document the exception.
- `category_code` is mostly missing, so category-level findings must treat `unknown_category` as a real reported bucket rather than a nuisance filter.

## Phase 3 Gate

- Accepted values pass for `event_type`.
- Required field null counts are reported.
- Unknown category and brand counts are reported, not hidden.
- Event ordering is deterministic using `event_time`, `source_file`, and `source_row_number`.
- Session ordering check covered 4,535,941 sessions and found 0 sessions with reversed time.
