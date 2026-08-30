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
| `invalid_purchase_count` | Count of purchase rows with invalid prices. |
| `purchase_revenue` | Sum of valid non-negative purchase event prices. |
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
- Revenue: sum valid non-negative purchase event prices in `purchase_revenue`; invalid purchase rows remain counted in `invalid_purchase_count`.

## Generated Validation Tables

- `mart_session_reconciliation`
- `mart_session_revenue_reconciliation`
- `mart_session_funnel_counts`


## Validation Results

| Check | Result |
| --- | ---: |
| Distinct staged sessions | 4,535,941 |
| Session mart rows | 4,535,941 |
| Missing session rows excluded from mart | 4,598 |
| Sessions with reversed time | 0 |
| Purchase flag mismatches | 0 |
| Revenue reconciliation mismatch rows | 0 |

## Funnel Stage Counts

| Metric | Sessions / Events |
| --- | ---: |
| Total sessions | 4,535,941 |
| Reached view sessions | 4,280,701 |
| Reached cart after view sessions | 788,430 |
| Reached purchase after cart sessions | 106,526 |
| Purchased sessions | 155,617 |
| Purchase events | 1,287,007 |
| Invalid purchase events excluded from revenue | 126 |
| Valid purchase revenue | $6,351,830.29 |
## Phase 4 Gate

After raw data is loaded and staged, confirm that:

- `mart_session_count` equals distinct non-null `user_session` in `stg_events`.
- `sessions_with_reversed_time` is zero.
- `purchase_flag_mismatches` is zero.
- `mart_session_revenue_reconciliation` has zero rows.
- In `mart_session_funnel_counts`, `reached_view_sessions >= reached_cart_after_view_sessions >= reached_purchase_after_cart_sessions`.

Counts were validated after loading the five-month local archive.

