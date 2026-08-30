-- Phase 2 ingestion validation for data/warehouse/retailpulse.duckdb.

-- Tables should exist.
SHOW TABLES;

-- Raw event row counts by source file should reconcile with raw_load_log.
SELECT
    log.source_file,
    log.raw_row_count,
    log.loaded_row_count,
    events.loaded_rows_from_table,
    log.raw_row_count = events.loaded_rows_from_table AS row_count_matches
FROM raw_load_log AS log
JOIN (
    SELECT source_file, count(*) AS loaded_rows_from_table
    FROM raw_events
    GROUP BY source_file
) AS events
    ON log.source_file = events.source_file
ORDER BY log.source_file;

-- No required field should be entirely null after loading.
SELECT
    count(*) AS row_count,
    sum(CASE WHEN event_time IS NULL THEN 1 ELSE 0 END) AS null_event_time_rows,
    sum(CASE WHEN event_type IS NULL THEN 1 ELSE 0 END) AS null_event_type_rows,
    sum(CASE WHEN product_id IS NULL THEN 1 ELSE 0 END) AS null_product_id_rows,
    sum(CASE WHEN price IS NULL THEN 1 ELSE 0 END) AS null_price_rows,
    sum(CASE WHEN user_id IS NULL THEN 1 ELSE 0 END) AS null_user_id_rows,
    sum(CASE WHEN user_session IS NULL THEN 1 ELSE 0 END) AS null_user_session_rows
FROM raw_events;

-- Event type values should stay within the expected contract.
SELECT event_type, count(*) AS rows
FROM raw_events
GROUP BY event_type
ORDER BY rows DESC;

-- Source file date ranges should match the raw profiling manifest.
SELECT
    source_file,
    count(*) AS rows,
    min(event_time) AS min_event_time,
    max(event_time) AS max_event_time
FROM raw_events
GROUP BY source_file
ORDER BY source_file;
