# Session Mart

Phase 4 reconstructs session-level facts from `stg_events`.

Run:

```bash
python scripts/run_duckdb_sql.py sql/04_session_mart.sql
```

## Output Table

`mart_sessions` has one row per non-null `user_session`.

| Field | Definition |
| --- | --- |
| `user_session` | Session identifier from the source data. |
| `user_id` | User attached to the session. |
| `session_started_at` | Earliest event timestamp in the session. |
| `session_ended_at` | Latest event timestamp in the session. |
| `session_duration_seconds` | Seconds between first and last event. |
| `event_count` | Number of events in the session. |
| `distinct_products_viewed` | Distinct viewed products in the session. |
| `cart_count` | Count of cart events. |
| `remove_from_cart_count` | Count of remove-from-cart events. |
| `purchase_count` | Count of purchase event rows. |
| `purchase_revenue` | Sum of purchase event prices. |
| `had_view` | Session had at least one view event. |
| `had_cart` | Session had at least one cart event. |
| `had_remove_from_cart` | Session had at least one remove-from-cart event. |
| `had_purchase` | Session had at least one purchase event. |
| `first_event_type` | First ordered event type in the session. |
| `last_event_type` | Last ordered event type in the session. |
| `first_product_id` | First ordered product in the session. |
| `first_brand` | First ordered brand in the session. |
| `first_category_code` | First ordered category in the session. |
| `time_to_purchase_seconds` | Seconds from session start to first purchase, when applicable. |

## Multiple Purchases in One Session

- Funnel conversion: one session with `had_purchase = true`.
- Purchase count: all purchase event rows in `purchase_count`.
- Revenue: sum all purchase event prices in `purchase_revenue`.

## Generated Validation Tables

- `mart_session_reconciliation`
- `mart_session_revenue_reconciliation`
- `mart_session_funnel_counts`

## Phase 4 Gate

After raw data is loaded and staged, confirm that:

- `mart_session_count` equals distinct non-null `user_session` in `stg_events`.
- `sessions_with_reversed_time` is zero.
- `purchase_flag_mismatches` is zero.
- `mart_session_revenue_reconciliation` has zero rows.
- In `mart_session_funnel_counts`, `reached_view_sessions >= reached_cart_after_view_sessions >= reached_purchase_after_cart_sessions`.

Counts are pending until the Kaggle CSV files are downloaded, ingested, and staged locally.
