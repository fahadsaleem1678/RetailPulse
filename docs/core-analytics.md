# Core Product Analytics

Phase 5 creates the repeatable metric tables for the three business questions.

Run after staging and session reconstruction:

```bash
python scripts/run_duckdb_sql.py analysis/core_metrics.sql
```

## Funnel Analysis

Funnel tables use session-level denominators:

- `metric_session_funnel_overall`
- `metric_session_funnel_by_month`
- `metric_session_funnel_by_brand`
- `metric_session_funnel_by_category`
- `metric_session_funnel_by_price_band`

Definitions:

- View stage: sessions with `had_view = true`.
- Cart stage: sessions with both `had_view = true` and `had_cart = true`.
- Purchase stage: sessions with `had_view = true`, `had_cart = true`, and `had_purchase = true`.
- Purchase revenue: sum of purchase event prices, not one revenue row per session.

## Cohort Retention

Generated tables:

- `mart_user_month_activity`
- `metric_activity_cohort_retention`
- `metric_purchase_cohort_retention`

Activity retention is separate from purchase retention so browsing return behavior is not mixed with repeat buying.

## RFM Segmentation

Generated tables:

- `mart_user_rfm_segments`
- `metric_rfm_segment_summary`

Segments are mutually exclusive for purchasing users:

- `high_value_loyal`
- `recent_first_time`
- `at_risk_previous_buyer`
- `low_value_occasional`

## Reconciliation

`metric_revenue_reconciliation` compares revenue totals from:

- event-level purchases in `stg_events`
- session-level purchase revenue in `mart_sessions`
- user-level revenue in `mart_user_rfm_segments`

## Phase 5 Gate

After data is loaded, confirm that:

- Funnel denominators are session counts, not event counts.
- Cohort sizes reconcile to first-activity and first-purchase user counts.
- RFM segments cover every purchasing user exactly once.
- Revenue totals reconcile across event, session, and user-level tables.

Counts are pending until the Kaggle CSV files are downloaded, ingested, staged, and sessionized locally.
