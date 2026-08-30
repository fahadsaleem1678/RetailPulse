# Data Dictionary

RetailPulse uses a small layered model: raw typed events, staged analyst-friendly events, session facts, user/cohort metrics, and exported dashboard summaries.

## `raw_events`

Typed event table loaded from the Kaggle CSV files.

| Field | Definition |
| --- | --- |
| `event_time` | Parsed UTC event timestamp. |
| `event_month` | Month bucket derived from `event_time`. |
| `event_type` | Source event type: `view`, `cart`, `remove_from_cart`, or `purchase`. |
| `product_id` | Product identifier parsed as bigint. |
| `category_id` | Category identifier parsed as bigint. |
| `category_code` | Nullable category taxonomy from the source. |
| `brand` | Nullable lowercase brand name from the source. |
| `price` | Product price parsed as double. |
| `user_id` | Permanent user identifier parsed as bigint. |
| `user_session` | Session identifier from the source. |
| `source_row_number` | Row number within the source file scan. |
| `source_file` | Source CSV file name. |

## `raw_load_log`

One row per source CSV loaded into DuckDB.

| Field | Definition |
| --- | --- |
| `load_id` | UUID for an ingestion run. |
| `loaded_at` | UTC load timestamp. |
| `source_file` | Source CSV file name. |
| `source_path` | Local source path. |
| `source_sha256` | SHA-256 checksum of the source file. |
| `file_size_bytes` | Source file size. |
| `raw_row_count` | Rows counted from the raw CSV scan. |
| `loaded_row_count` | Rows inserted into `raw_events`. |
| `min_event_time` | Minimum event timestamp in the source file. |
| `max_event_time` | Maximum event timestamp in the source file. |

## `stg_events`

Analyst-friendly event table with explicit quality flags and unknown dimension handling.

| Field | Definition |
| --- | --- |
| `event_id` | Stable hash of source file and source row number. |
| `event_time` | Parsed event timestamp. |
| `event_month` | Month bucket. |
| `event_type` | Validated event type. |
| `product_id` | Product identifier. |
| `category_id` | Category identifier. |
| `original_category_code` | Raw nullable category taxonomy. |
| `original_brand` | Raw nullable brand. |
| `category_code` | Category taxonomy with nulls converted to `unknown_category`. |
| `brand` | Brand with nulls converted to `unknown_brand`. |
| `price` | Parsed product price. |
| `user_id` | Permanent user identifier. |
| `user_session` | Session identifier. |
| `source_file` | Source CSV file name. |
| `source_row_number` | Row number within source file scan. |
| `is_unknown_category` | True when source category was missing. |
| `is_unknown_brand` | True when source brand was missing. |
| `has_invalid_event_time` | True when timestamp parsing failed. |
| `has_invalid_event_type` | True when event type is outside the expected set. |
| `has_missing_product_id` | True when product id is missing. |
| `has_invalid_price` | True when price is missing or negative. |
| `has_missing_user_id` | True when user id is missing. |
| `has_missing_user_session` | True when session id is missing. |
| `event_sequence_in_session` | Deterministic event order within each session. |
| `previous_event_type` | Previous ordered event type in the same session. |
| `next_event_type` | Next ordered event type in the same session. |

## `mart_sessions`

One row per non-null source session.

| Field | Definition |
| --- | --- |
| `user_session` | Session identifier. |
| `user_id` | User attached to the session. |
| `session_started_at` | Earliest event timestamp in the session. |
| `session_ended_at` | Latest event timestamp in the session. |
| `session_duration_seconds` | Seconds between first and last session event. |
| `event_count` | Total events in the session. |
| `distinct_products_viewed` | Distinct viewed products in the session. |
| `cart_count` | Cart event count. |
| `remove_from_cart_count` | Remove-from-cart event count. |
| `purchase_count` | Purchase event count. |
| `invalid_purchase_count` | Purchase rows with invalid prices. |
| `purchase_revenue` | Valid non-negative purchase revenue. |
| `had_view` | Session had at least one view event. |
| `had_cart` | Session had at least one cart event. |
| `had_remove_from_cart` | Session had at least one remove-from-cart event. |
| `had_purchase` | Session had at least one purchase event. |
| `first_purchase_at` | First purchase timestamp in the session. |
| `first_event_type` | First event type by deterministic order. |
| `last_event_type` | Last event type by deterministic order. |
| `first_product_id` | First product id by deterministic order. |
| `first_brand` | First brand by deterministic order. |
| `first_category_code` | First category by deterministic order. |
| `time_to_purchase_seconds` | Seconds from session start to first purchase. |

## Core Metric Tables

| Table | Purpose |
| --- | --- |
| `metric_session_funnel_overall` | Overall session-level funnel rates and revenue. |
| `metric_session_funnel_by_month` | Monthly session-level funnel rates. |
| `metric_session_funnel_by_brand` | Session-level funnel rates by first session brand. |
| `metric_session_funnel_by_category` | Session-level funnel rates by first session category. |
| `metric_session_funnel_by_price_band` | Session-level funnel rates by first session price band. |
| `mart_user_month_activity` | Monthly user activity and purchase revenue base table. |
| `metric_activity_cohort_retention` | First-activity cohort retention by month. |
| `metric_purchase_cohort_retention` | First-purchase cohort retention by month. |
| `mart_user_rfm_segments` | Purchasing-user RFM features and segment labels. |
| `metric_rfm_segment_summary` | Segment size, revenue, and revenue share. |
| `metric_revenue_reconciliation` | Revenue reconciliation across event, session, and user layers. |

## Generated Quality Tables

| Table | Purpose |
| --- | --- |
| `dq_stg_events_summary` | Nulls, invalid values, unknown dimensions, and row count. |
| `dq_event_type_counts` | Event type distribution. |
| `dq_monthly_freshness` | Monthly coverage, users, sessions, and row counts. |
| `dq_unknown_dimension_counts` | Monthly unknown brand/category counts. |
| `dq_session_ordering_checks` | Session ordering sanity check. |
| `mart_session_reconciliation` | Staged session count versus session mart rows. |
| `mart_session_revenue_reconciliation` | Session revenue mismatch diagnostics. |
| `mart_session_funnel_counts` | Session funnel stage counts. |
