-- Phase 4 session reconstruction mart.
-- Run after Phase 3 staging:
--   python scripts/run_duckdb_sql.py sql/04_session_mart.sql

CREATE OR REPLACE TABLE mart_sessions AS
WITH ordered_events AS (
    SELECT
        *,
        first_value(event_type) OVER session_order AS first_event_type,
        last_value(event_type) OVER session_order AS last_event_type,
        first_value(product_id) OVER session_order AS first_product_id,
        first_value(brand) OVER session_order AS first_brand,
        first_value(category_code) OVER session_order AS first_category_code
    FROM stg_events
    WHERE user_session IS NOT NULL
    WINDOW session_order AS (
        PARTITION BY user_session
        ORDER BY event_time NULLS LAST, source_file, source_row_number
        ROWS BETWEEN UNBOUNDED PRECEDING AND UNBOUNDED FOLLOWING
    )
),
session_rollup AS (
    SELECT
        user_session,
        min(user_id) AS user_id,
        min(event_time) AS session_started_at,
        max(event_time) AS session_ended_at,
        date_diff('second', min(event_time), max(event_time)) AS session_duration_seconds,
        count(*) AS event_count,
        count(DISTINCT CASE WHEN event_type = 'view' THEN product_id END) AS distinct_products_viewed,
        sum(CASE WHEN event_type = 'cart' THEN 1 ELSE 0 END) AS cart_count,
        sum(CASE WHEN event_type = 'remove_from_cart' THEN 1 ELSE 0 END) AS remove_from_cart_count,
        sum(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchase_count,
        sum(CASE WHEN event_type = 'purchase' THEN coalesce(price, 0) ELSE 0 END) AS purchase_revenue,
        max(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) = 1 AS had_view,
        max(CASE WHEN event_type = 'cart' THEN 1 ELSE 0 END) = 1 AS had_cart,
        max(CASE WHEN event_type = 'remove_from_cart' THEN 1 ELSE 0 END) = 1 AS had_remove_from_cart,
        max(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) = 1 AS had_purchase,
        min(CASE WHEN event_type = 'purchase' THEN event_time END) AS first_purchase_at,
        any_value(first_event_type) AS first_event_type,
        any_value(last_event_type) AS last_event_type,
        any_value(first_product_id) AS first_product_id,
        any_value(first_brand) AS first_brand,
        any_value(first_category_code) AS first_category_code
    FROM ordered_events
    GROUP BY user_session
)
SELECT
    *,
    CASE
        WHEN first_purchase_at IS NULL THEN NULL
        ELSE date_diff('second', session_started_at, first_purchase_at)
    END AS time_to_purchase_seconds
FROM session_rollup;

CREATE OR REPLACE TABLE mart_session_reconciliation AS
SELECT
    (SELECT count(DISTINCT user_session) FROM stg_events WHERE user_session IS NOT NULL) AS staged_session_count,
    (SELECT count(*) FROM mart_sessions) AS mart_session_count,
    (SELECT count(DISTINCT user_session) FROM stg_events WHERE user_session IS NULL) AS missing_session_groups,
    (SELECT count(*) FROM mart_sessions WHERE session_started_at > session_ended_at) AS sessions_with_reversed_time,
    (SELECT count(*) FROM mart_sessions WHERE had_purchase <> (purchase_count > 0)) AS purchase_flag_mismatches;

CREATE OR REPLACE TABLE mart_session_revenue_reconciliation AS
SELECT
    source.user_session,
    source.purchase_revenue_from_events,
    mart.purchase_revenue AS purchase_revenue_from_sessions,
    abs(source.purchase_revenue_from_events - mart.purchase_revenue) AS absolute_difference
FROM (
    SELECT
        user_session,
        sum(CASE WHEN event_type = 'purchase' THEN coalesce(price, 0) ELSE 0 END) AS purchase_revenue_from_events
    FROM stg_events
    WHERE user_session IS NOT NULL
    GROUP BY user_session
) AS source
JOIN mart_sessions AS mart
    ON source.user_session = mart.user_session
WHERE abs(source.purchase_revenue_from_events - mart.purchase_revenue) > 0.0001;

CREATE OR REPLACE TABLE mart_session_funnel_counts AS
SELECT
    count(*) AS total_sessions,
    sum(CASE WHEN had_view THEN 1 ELSE 0 END) AS reached_view_sessions,
    sum(CASE WHEN had_view AND had_cart THEN 1 ELSE 0 END) AS reached_cart_after_view_sessions,
    sum(CASE WHEN had_view AND had_cart AND had_purchase THEN 1 ELSE 0 END) AS reached_purchase_after_cart_sessions,
    sum(CASE WHEN had_purchase THEN 1 ELSE 0 END) AS purchased_sessions,
    sum(purchase_count) AS purchase_events,
    sum(purchase_revenue) AS purchase_revenue
FROM mart_sessions;
