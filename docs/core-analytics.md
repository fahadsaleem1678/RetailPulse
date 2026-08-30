# Core Product Analytics

Phase 5 creates the repeatable metric tables for the three business questions.

Run after staging and session reconstruction:

```bash
python scripts/run_duckdb_sql.py analysis/core_metrics.sql
python scripts/export_metric_tables.py
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
- Purchase revenue: sum of valid non-negative purchase event prices, not one revenue row per session.

## Funnel Results

| Metric | Value |
| --- | ---: |
| Total sessions | 4,535,941 |
| Viewed sessions | 4,280,701 |
| Carted after view sessions | 788,430 |
| Purchased after cart sessions | 106,526 |
| Purchased sessions | 155,617 |
| Valid purchase revenue | $6,351,830.29 |
| View-to-cart rate | 18.42% |
| Cart-to-purchase rate | 13.51% |
| View-to-purchase rate | 2.49% |

Monthly view-to-purchase conversion peaked in November 2019 at 2.81% and declined to 2.24% in February 2020.

Top known brands by valid purchase revenue include `runail`, `irisk`, `grattol`, `masura`, and `uno`. The `unknown_brand` bucket is still the largest revenue bucket, so brand findings must be framed with that limitation.

## Cohort Retention

Generated tables:

- `mart_user_month_activity`
- `metric_activity_cohort_retention`
- `metric_purchase_cohort_retention`

Activity retention is separate from purchase retention so browsing return behavior is not mixed with repeat buying.

Month-1 activity retention declined from 13.71% for the October 2019 first-activity cohort to 9.16% for the December 2019 first-activity cohort, then recovered to 10.10% for January 2020.

Month-1 purchase retention was strongest for the October 2019 first-purchase cohort at 18.49%. Later cohorts were lower: 9.78% for November 2019, 8.52% for December 2019, and 8.86% for January 2020.

## RFM Segmentation

Generated tables:

- `mart_user_rfm_segments`
- `metric_rfm_segment_summary`

Segments are mutually exclusive for purchasing users:

- `high_value_loyal`
- `recent_first_time`
- `at_risk_previous_buyer`
- `low_value_occasional`

| Segment | Users | Valid Purchase Revenue | Revenue Share |
| --- | ---: | ---: | ---: |
| `at_risk_previous_buyer` | 60,921 | $2,779,903.51 | 43.77% |
| `high_value_loyal` | 6,487 | $1,530,613.93 | 24.10% |
| `low_value_occasional` | 25,129 | $1,324,630.90 | 20.85% |
| `recent_first_time` | 17,981 | $716,681.95 | 11.28% |

## Reconciliation

`metric_revenue_reconciliation` compares revenue totals from:

- valid event-level purchases in `stg_events`
- session-level purchase revenue in `mart_sessions`
- user-level revenue in `mart_user_rfm_segments`

All three revenue totals reconcile to $6,351,830.29.

## Exported Tables

Small CSV exports are committed under `data/exports/` for review and dashboard checks.

## Phase 5 Gate

- Funnel denominators are session counts, not event counts.
- Cohort sizes reconcile to first-activity and first-purchase user counts by construction.
- RFM segments cover every purchasing user exactly once.
- Revenue totals reconcile across event, session, and user-level tables.

