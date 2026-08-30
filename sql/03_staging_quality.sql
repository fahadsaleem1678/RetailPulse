-- Phase 3 staging and quality models.
-- Run after Phase 2 ingestion:
--   python scripts/run_duckdb_sql.py sql/03_staging_quality.sql

CREATE OR REPLACE TABLE stg_events AS
WITH typed AS (
    SELECT
        md5(source_file || ':' || source_row_number::VARCHAR) AS event_id,
        event_time,
        event_month,
        event_type,
        product_id,
        category_id,
        category_code AS original_category_code,
        brand AS original_brand,
        coalesce(category_code, 'unknown_category') AS category_code,
        coalesce(brand, 'unknown_brand') AS brand,
        price,
        user_id,
        user_session,
        source_file,
        source_row_number,
        category_code IS NULL AS is_unknown_category,
        brand IS NULL AS is_unknown_brand,
        event_time IS NULL AS has_invalid_event_time,
        event_type NOT IN ('view', 'cart', 'remove_from_cart', 'purchase') OR event_type IS NULL AS has_invalid_event_type,
        product_id IS NULL AS has_missing_product_id,
        price IS NULL OR price < 0 AS has_invalid_price,
        user_id IS NULL AS has_missing_user_id,
        user_session IS NULL AS has_missing_user_session
    FROM raw_events
)
SELECT
    *,
    row_number() OVER (
        PARTITION BY user_session
        ORDER BY event_time NULLS LAST, source_file, source_row_number
    ) AS event_sequence_in_session,
    lag(event_type) OVER (
        PARTITION BY user_session
        ORDER BY event_time NULLS LAST, source_file, source_row_number
    ) AS previous_event_type,
    lead(event_type) OVER (
        PARTITION BY user_session
        ORDER BY event_time NULLS LAST, source_file, source_row_number
    ) AS next_event_type
FROM typed;

CREATE OR REPLACE TABLE dq_stg_events_summary AS
SELECT
    count(*) AS row_count,
    sum(CASE WHEN event_time IS NULL THEN 1 ELSE 0 END) AS null_event_time_rows,
    sum(CASE WHEN event_type IS NULL THEN 1 ELSE 0 END) AS null_event_type_rows,
    sum(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_id_rows,
    sum(CASE WHEN price IS NULL THEN 1 ELSE 0 END) AS null_price_rows,
    sum(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) AS null_user_id_rows,
    sum(CASE WHEN user_session IS NULL THEN 1 ELSE 0 END) AS null_user_session_rows,
    sum(CASE WHEN has_invalid_event_type THEN 1 ELSE 0 END) AS invalid_event_type_rows,
    sum(CASE WHEN has_invalid_price THEN 1 ELSE 0 END) AS invalid_price_rows,
    sum(CASE WHEN is_unknown_category THEN 1 ELSE 0 END) AS unknown_category_rows,
    sum(CASE WHEN is_unknown_brand THEN 1 ELSE 0 END) AS unknown_brand_rows
FROM stg_events;

CREATE OR REPLACE TABLE dq_event_type_counts AS
SELECT
    event_type,
    count(*) AS row_count
FROM stg_events
GROUP BY event_type
ORDER BY row_count DESC;

CREATE OR REPLACE TABLE dq_monthly_freshness AS
SELECT
    event_month,
    min(event_time) AS first_event_time,
    max(event_time) AS last_event_time,
    count(*) AS row_count,
    count(DISTINCT user_id) AS distinct_users,
    count(DISTINCT user_session) AS distinct_sessions
FROM stg_events
GROUP BY event_month
ORDER BY event_month;

CREATE OR REPLACE TABLE dq_unknown_dimension_counts AS
SELECT
    event_month,
    sum(CASE WHEN is_unknown_category THEN 1 ELSE 0 END) AS unknown_category_rows,
    sum(CASE WHEN is_unknown_brand THEN 1 ELSE 0 END) AS unknown_brand_rows,
    count(*) AS row_count
FROM stg_events
GROUP BY event_month
ORDER BY event_month;

CREATE OR REPLACE TABLE dq_session_ordering_checks AS
SELECT
    count(*) AS checked_sessions,
    sum(CASE WHEN session_started_at <= session_ended_at THEN 0 ELSE 1 END) AS sessions_with_reversed_time
FROM (
    SELECT
        user_session,
        min(event_time) AS session_started_at,
        max(event_time) AS session_ended_at
    FROM stg_events
    WHERE user_session IS NOT NULL
    GROUP BY user_session
) sessions;
