-- Phase 1 raw profiling checks for the cosmetics ecommerce dataset.
-- Usage from DuckDB CLI after raw CSV files are downloaded:
--   duckdb -c ".read analysis/01_data_profile.sql"

CREATE OR REPLACE VIEW raw_cosmetics_events_external AS
SELECT *
FROM read_csv_auto('data/raw/cosmetics/*.csv', header = true, union_by_name = true);

-- Required schema check.
DESCRIBE raw_cosmetics_events_external;

-- Row count and event time coverage.
SELECT
    count(*) AS row_count,
    min(try_cast(event_time AS TIMESTAMP)) AS min_event_time,
    max(try_cast(event_time AS TIMESTAMP)) AS max_event_time,
    count(DISTINCT user_id) AS distinct_users,
    count(DISTINCT user_session) AS distinct_sessions
FROM raw_cosmetics_events_external;

-- Event type distribution. Expected: view, cart, remove_from_cart, purchase.
SELECT
    event_type,
    count(*) AS events
FROM raw_cosmetics_events_external
GROUP BY event_type
ORDER BY events DESC;

-- Null and blank rates for key fields.
SELECT
    count(*) AS row_count,
    sum(CASE WHEN category_code IS NULL OR trim(category_code) = '' THEN 1 ELSE 0 END) AS missing_category_code_rows,
    sum(CASE WHEN brand IS NULL OR trim(brand) = '' THEN 1 ELSE 0 END) AS missing_brand_rows,
    sum(CASE WHEN user_session IS NULL OR trim(user_session) = '' THEN 1 ELSE 0 END) AS missing_user_session_rows,
    sum(CASE WHEN price IS NULL OR trim(cast(price AS VARCHAR)) = '' THEN 1 ELSE 0 END) AS missing_price_rows
FROM raw_cosmetics_events_external;

-- Price range and parseability.
SELECT
    min(try_cast(price AS DOUBLE)) AS min_price,
    max(try_cast(price AS DOUBLE)) AS max_price,
    sum(CASE WHEN try_cast(price AS DOUBLE) IS NULL THEN 1 ELSE 0 END) AS unparseable_price_rows,
    sum(CASE WHEN try_cast(price AS DOUBLE) < 0 THEN 1 ELSE 0 END) AS negative_price_rows
FROM raw_cosmetics_events_external;

-- Duplicate full rows across all expected fields.
SELECT
    coalesce(sum(row_count - 1), 0) AS duplicate_rows
FROM (
    SELECT
        event_time,
        event_type,
        product_id,
        category_id,
        category_code,
        brand,
        price,
        user_id,
        user_session,
        count(*) AS row_count
    FROM raw_cosmetics_events_external
    GROUP BY
        event_time,
        event_type,
        product_id,
        category_id,
        category_code,
        brand,
        price,
        user_id,
        user_session
    HAVING count(*) > 1
) duplicates;
