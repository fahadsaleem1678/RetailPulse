-- Phase 5 core product analytics.
-- Run after Phase 4 session reconstruction:
--   python scripts/run_duckdb_sql.py analysis/core_metrics.sql

CREATE OR REPLACE TABLE metric_session_funnel_overall AS
SELECT
    count(*) AS total_sessions,
    sum(CASE WHEN had_view THEN 1 ELSE 0 END) AS viewed_sessions,
    sum(CASE WHEN had_view AND had_cart THEN 1 ELSE 0 END) AS carted_after_view_sessions,
    sum(CASE WHEN had_view AND had_cart AND had_purchase THEN 1 ELSE 0 END) AS purchased_after_cart_sessions,
    sum(CASE WHEN had_purchase THEN 1 ELSE 0 END) AS purchased_sessions,
    sum(purchase_revenue) AS purchase_revenue,
    carted_after_view_sessions::DOUBLE / nullif(viewed_sessions, 0) AS view_to_cart_rate,
    purchased_after_cart_sessions::DOUBLE / nullif(carted_after_view_sessions, 0) AS cart_to_purchase_rate,
    purchased_after_cart_sessions::DOUBLE / nullif(viewed_sessions, 0) AS view_to_purchase_rate
FROM mart_sessions;

CREATE OR REPLACE TABLE metric_session_funnel_by_month AS
SELECT
    date_trunc('month', session_started_at)::DATE AS session_month,
    count(*) AS total_sessions,
    sum(CASE WHEN had_view THEN 1 ELSE 0 END) AS viewed_sessions,
    sum(CASE WHEN had_view AND had_cart THEN 1 ELSE 0 END) AS carted_after_view_sessions,
    sum(CASE WHEN had_view AND had_cart AND had_purchase THEN 1 ELSE 0 END) AS purchased_after_cart_sessions,
    sum(CASE WHEN had_purchase THEN 1 ELSE 0 END) AS purchased_sessions,
    sum(purchase_revenue) AS purchase_revenue,
    carted_after_view_sessions::DOUBLE / nullif(viewed_sessions, 0) AS view_to_cart_rate,
    purchased_after_cart_sessions::DOUBLE / nullif(carted_after_view_sessions, 0) AS cart_to_purchase_rate,
    purchased_after_cart_sessions::DOUBLE / nullif(viewed_sessions, 0) AS view_to_purchase_rate
FROM mart_sessions
GROUP BY session_month
ORDER BY session_month;

CREATE OR REPLACE TABLE metric_session_funnel_by_brand AS
SELECT
    first_brand AS brand,
    count(*) AS total_sessions,
    sum(CASE WHEN had_view THEN 1 ELSE 0 END) AS viewed_sessions,
    sum(CASE WHEN had_view AND had_cart THEN 1 ELSE 0 END) AS carted_after_view_sessions,
    sum(CASE WHEN had_view AND had_cart AND had_purchase THEN 1 ELSE 0 END) AS purchased_after_cart_sessions,
    sum(CASE WHEN had_purchase THEN 1 ELSE 0 END) AS purchased_sessions,
    sum(purchase_revenue) AS purchase_revenue,
    carted_after_view_sessions::DOUBLE / nullif(viewed_sessions, 0) AS view_to_cart_rate,
    purchased_after_cart_sessions::DOUBLE / nullif(carted_after_view_sessions, 0) AS cart_to_purchase_rate,
    purchased_after_cart_sessions::DOUBLE / nullif(viewed_sessions, 0) AS view_to_purchase_rate
FROM mart_sessions
GROUP BY brand
ORDER BY purchase_revenue DESC, viewed_sessions DESC;

CREATE OR REPLACE TABLE metric_session_funnel_by_category AS
SELECT
    first_category_code AS category_code,
    count(*) AS total_sessions,
    sum(CASE WHEN had_view THEN 1 ELSE 0 END) AS viewed_sessions,
    sum(CASE WHEN had_view AND had_cart THEN 1 ELSE 0 END) AS carted_after_view_sessions,
    sum(CASE WHEN had_view AND had_cart AND had_purchase THEN 1 ELSE 0 END) AS purchased_after_cart_sessions,
    sum(CASE WHEN had_purchase THEN 1 ELSE 0 END) AS purchased_sessions,
    sum(purchase_revenue) AS purchase_revenue,
    carted_after_view_sessions::DOUBLE / nullif(viewed_sessions, 0) AS view_to_cart_rate,
    purchased_after_cart_sessions::DOUBLE / nullif(carted_after_view_sessions, 0) AS cart_to_purchase_rate,
    purchased_after_cart_sessions::DOUBLE / nullif(viewed_sessions, 0) AS view_to_purchase_rate
FROM mart_sessions
GROUP BY category_code
ORDER BY purchase_revenue DESC, viewed_sessions DESC;

CREATE OR REPLACE TABLE metric_session_funnel_by_price_band AS
WITH session_entry_price AS (
    SELECT
        user_session,
        max(CASE WHEN event_sequence_in_session = 1 THEN price END) AS entry_price
    FROM stg_events
    WHERE user_session IS NOT NULL
    GROUP BY user_session
),
price_banded_sessions AS (
    SELECT
        sessions.*,
        CASE
            WHEN entry_price IS NULL THEN 'unknown_price'
            WHEN entry_price < 10 THEN 'under_10'
            WHEN entry_price < 25 THEN '10_to_24_99'
            WHEN entry_price < 50 THEN '25_to_49_99'
            WHEN entry_price < 100 THEN '50_to_99_99'
            ELSE '100_plus'
        END AS entry_price_band
    FROM mart_sessions AS sessions
    LEFT JOIN session_entry_price AS prices
        ON sessions.user_session = prices.user_session
)
SELECT
    entry_price_band,
    count(*) AS total_sessions,
    sum(CASE WHEN had_view THEN 1 ELSE 0 END) AS viewed_sessions,
    sum(CASE WHEN had_view AND had_cart THEN 1 ELSE 0 END) AS carted_after_view_sessions,
    sum(CASE WHEN had_view AND had_cart AND had_purchase THEN 1 ELSE 0 END) AS purchased_after_cart_sessions,
    sum(CASE WHEN had_purchase THEN 1 ELSE 0 END) AS purchased_sessions,
    sum(purchase_revenue) AS purchase_revenue,
    carted_after_view_sessions::DOUBLE / nullif(viewed_sessions, 0) AS view_to_cart_rate,
    purchased_after_cart_sessions::DOUBLE / nullif(carted_after_view_sessions, 0) AS cart_to_purchase_rate,
    purchased_after_cart_sessions::DOUBLE / nullif(viewed_sessions, 0) AS view_to_purchase_rate
FROM price_banded_sessions
GROUP BY entry_price_band
ORDER BY entry_price_band;

CREATE OR REPLACE TABLE mart_user_month_activity AS
SELECT
    user_id,
    event_month,
    count(*) AS events,
    count(DISTINCT user_session) AS sessions,
    sum(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchase_events,
    sum(CASE WHEN event_type = 'purchase' AND NOT has_invalid_price THEN coalesce(price, 0) ELSE 0 END) AS purchase_revenue
FROM stg_events
WHERE user_id IS NOT NULL
GROUP BY user_id, event_month;

CREATE OR REPLACE TABLE metric_activity_cohort_retention AS
WITH cohorts AS (
    SELECT
        user_id,
        min(event_month) AS first_activity_month
    FROM mart_user_month_activity
    GROUP BY user_id
),
cohort_sizes AS (
    SELECT first_activity_month, count(*) AS cohort_users
    FROM cohorts
    GROUP BY first_activity_month
)
SELECT
    cohorts.first_activity_month,
    activity.event_month AS activity_month,
    date_diff('month', cohorts.first_activity_month, activity.event_month) AS months_since_first_activity,
    sizes.cohort_users,
    count(DISTINCT activity.user_id) AS active_users,
    count(DISTINCT activity.user_id)::DOUBLE / nullif(sizes.cohort_users, 0) AS activity_retention_rate
FROM cohorts
JOIN mart_user_month_activity AS activity
    ON cohorts.user_id = activity.user_id
JOIN cohort_sizes AS sizes
    ON cohorts.first_activity_month = sizes.first_activity_month
GROUP BY cohorts.first_activity_month, activity.event_month, sizes.cohort_users
ORDER BY cohorts.first_activity_month, activity.event_month;

CREATE OR REPLACE TABLE metric_purchase_cohort_retention AS
WITH purchase_months AS (
    SELECT
        user_id,
        event_month,
        sum(purchase_events) AS purchase_events,
        sum(purchase_revenue) AS purchase_revenue
    FROM mart_user_month_activity
    WHERE purchase_events > 0
    GROUP BY user_id, event_month
),
cohorts AS (
    SELECT
        user_id,
        min(event_month) AS first_purchase_month
    FROM purchase_months
    GROUP BY user_id
),
cohort_sizes AS (
    SELECT first_purchase_month, count(*) AS cohort_users
    FROM cohorts
    GROUP BY first_purchase_month
)
SELECT
    cohorts.first_purchase_month,
    purchases.event_month AS purchase_month,
    date_diff('month', cohorts.first_purchase_month, purchases.event_month) AS months_since_first_purchase,
    sizes.cohort_users,
    count(DISTINCT purchases.user_id) AS purchasing_users,
    sum(purchases.purchase_events) AS purchase_events,
    sum(purchases.purchase_revenue) AS purchase_revenue,
    count(DISTINCT purchases.user_id)::DOUBLE / nullif(sizes.cohort_users, 0) AS purchase_retention_rate
FROM cohorts
JOIN purchase_months AS purchases
    ON cohorts.user_id = purchases.user_id
JOIN cohort_sizes AS sizes
    ON cohorts.first_purchase_month = sizes.first_purchase_month
GROUP BY cohorts.first_purchase_month, purchases.event_month, sizes.cohort_users
ORDER BY cohorts.first_purchase_month, purchases.event_month;

CREATE OR REPLACE TABLE mart_user_rfm_segments AS
WITH purchase_users AS (
    SELECT
        user_id,
        max(event_time) AS last_purchase_at,
        count(DISTINCT user_session) AS purchase_sessions,
        count(*) AS purchase_events,
        sum(coalesce(price, 0)) AS monetary_value
    FROM stg_events
    WHERE event_type = 'purchase'
      AND user_id IS NOT NULL
      AND NOT has_invalid_price
    GROUP BY user_id
),
analysis_date AS (
    SELECT max(event_time) AS max_event_time
    FROM stg_events
),
rfm AS (
    SELECT
        users.user_id,
        date_diff('day', users.last_purchase_at, analysis_date.max_event_time) AS recency_days,
        users.purchase_sessions AS frequency_sessions,
        users.purchase_events AS frequency_events,
        users.monetary_value
    FROM purchase_users AS users
    CROSS JOIN analysis_date
),
thresholds AS (
    SELECT quantile_cont(monetary_value, 0.75) AS monetary_p75
    FROM rfm
)
SELECT
    rfm.*,
    CASE
        WHEN frequency_sessions >= 3 AND monetary_value >= thresholds.monetary_p75 AND recency_days <= 60 THEN 'high_value_loyal'
        WHEN frequency_sessions = 1 AND recency_days <= 30 THEN 'recent_first_time'
        WHEN recency_days > 60 THEN 'at_risk_previous_buyer'
        ELSE 'low_value_occasional'
    END AS rfm_segment
FROM rfm
CROSS JOIN thresholds;

CREATE OR REPLACE TABLE metric_rfm_segment_summary AS
SELECT
    rfm_segment,
    count(*) AS users,
    sum(monetary_value) AS purchase_revenue,
    avg(recency_days) AS avg_recency_days,
    avg(frequency_sessions) AS avg_purchase_sessions,
    avg(monetary_value) AS avg_monetary_value,
    sum(monetary_value) / nullif((SELECT sum(monetary_value) FROM mart_user_rfm_segments), 0) AS revenue_share
FROM mart_user_rfm_segments
GROUP BY rfm_segment
ORDER BY purchase_revenue DESC;

CREATE OR REPLACE TABLE metric_revenue_reconciliation AS
SELECT
    (SELECT sum(CASE WHEN event_type = 'purchase' AND NOT has_invalid_price THEN coalesce(price, 0) ELSE 0 END) FROM stg_events) AS event_purchase_revenue,
    (SELECT sum(purchase_revenue) FROM mart_sessions) AS session_purchase_revenue,
    (SELECT sum(monetary_value) FROM mart_user_rfm_segments) AS user_rfm_purchase_revenue;

