# RetailPulse Ecommerce Product Analytics Case Study

## Executive Summary

RetailPulse analyzes 20.69M cosmetics ecommerce clickstream events from October 2019 through February 2020. The project reconstructs 4.54M sessions, measures session-level funnel conversion, compares activity and purchase retention cohorts, and segments purchasing users with an RFM-style model.

Three findings stand out:

- The session funnel is leaky: only 18.42% of viewed sessions carted, and only 13.51% of those view-plus-cart sessions purchased.
- Repeat purchase retention was strongest for the October 2019 first-purchase cohort at 18.49% in month 1, then fell below 10% for later cohorts.
- Revenue is concentrated in prior buyers: `at_risk_previous_buyer` users produced 43.77% of valid purchase revenue, while the much smaller `high_value_loyal` segment produced 24.10%.

## Dataset and Scope

Source: [eCommerce Events History in Cosmetics Shop](https://www.kaggle.com/datasets/mkechinov/ecommerce-events-history-in-cosmetics-shop)

The analysis uses historical clickstream events from a cosmetics ecommerce store. Version 1 focuses on batch product analytics and excludes streaming, multi-dataset joins, and predictive modeling.

Raw profile:

- Rows: 20,692,840
- Date range: October 1, 2019 through February 29, 2020
- Event types: `view`, `cart`, `remove_from_cart`, `purchase`
- Valid purchase revenue used in analysis: $6,351,830.29

## Business Questions

1. Where do users drop off in the view-to-cart-to-purchase funnel?
2. Which first-activity or first-purchase cohorts retain or repurchase?
3. Which brands, categories, and customer segments convert best?

## Method

The pipeline loads raw Kaggle CSV files into DuckDB, creates a typed staging table, reconstructs sessions, and generates summary tables for funnel, cohort, and RFM-style segment analysis.

Key metric tables:

- `metric_session_funnel_overall`
- `metric_session_funnel_by_month`
- `metric_session_funnel_by_brand`
- `metric_session_funnel_by_category`
- `metric_activity_cohort_retention`
- `metric_purchase_cohort_retention`
- `metric_rfm_segment_summary`

## Finding 1: Funnel Friction Is Severe After Product Views

Business question: Where do users drop off between product views, carting, and purchase?

Method: Use session-level funnel metrics from `metric_session_funnel_overall`, with a strict stage definition: viewed sessions, viewed sessions that carted, and viewed-plus-carted sessions that purchased.

Metric result: Out of 4,280,701 viewed sessions, 788,430 reached cart after view and 106,526 reached purchase after cart. That is an 18.42% view-to-cart rate, 13.51% cart-to-purchase rate, and 2.49% view-to-purchase rate.

Interpretation: Most product browsing sessions never reach cart, and most carting sessions still do not complete purchase. The cart-to-purchase step has the lower conversion rate, while the view-to-cart step loses the most sessions by absolute volume.

Recommendation: Prioritize two separate funnel checks: first, improve product-page confidence and merchandising to increase cart starts; second, audit checkout/cart friction because 86.49% of sessions that viewed and carted still did not purchase.

## Finding 2: Later Purchase Cohorts Repurchase Less Often

Business question: Do users return or repurchase after their first activity or first purchase month?

Method: Compare month-1 activity retention from `metric_activity_cohort_retention` with month-1 purchase retention from `metric_purchase_cohort_retention`.

Metric result: Month-1 purchase retention was 18.49% for the October 2019 first-purchase cohort, then dropped to 9.78% for November 2019, 8.52% for December 2019, and 8.86% for January 2020. Month-1 activity retention also softened from 13.71% for October first-activity users to 9.16% for December users, then recovered to 10.10% for January users.

Interpretation: The earliest purchase cohort was materially more likely to buy again. Later cohorts still returned at meaningful rates, but repeat purchasing weakened, suggesting that post-purchase lifecycle work may be underdeveloped or seasonal demand may have shifted.

Recommendation: Build a retention view focused on first 30 days after purchase: replenishment reminders, personalized follow-up for high-interest categories, and win-back offers for users who return to browse but do not repurchase.

## Finding 3: Revenue Is Concentrated in Prior Buyers

Business question: Which purchasing customer segments contribute the most revenue and repeat behavior?

Method: Use purchasing-user RFM segments from `mart_user_rfm_segments` and `metric_rfm_segment_summary`.

Metric result: `at_risk_previous_buyer` users account for 60,921 users and $2,779,903.51 in valid purchase revenue, or 43.77% of total valid revenue. `high_value_loyal` users are much smaller at 6,487 users but contribute $1,530,613.93, or 24.10% of valid revenue.

Interpretation: A large share of revenue sits with users who bought before but have not purchased recently. The loyal segment is small but economically powerful, with much higher average monetary value.

Recommendation: Treat prior buyers as the highest-leverage audience. Create separate CRM plays for `at_risk_previous_buyer` users and `high_value_loyal` users: reactivation for the former, early access or replenishment-oriented offers for the latter.

## Caveats

- `brand` and `category_code` can be missing. The pipeline preserves those values as `unknown_brand` and `unknown_category` rather than dropping the rows.
- `category_code` is missing on 98.29% of raw rows, so category-level insights should be treated as directional only.
- 126 invalid purchase-price rows were excluded from valid purchase revenue while still being counted in quality/session diagnostics.
- This is observational clickstream data, so recommendations should not claim causal impact without an experiment.
- Acquisition-channel context is not available in the dataset, so cohort behavior is based on first activity or first purchase rather than marketing source.
- Session-level funnel conversion and event-level revenue answer different questions and should not be mixed.

## Reproducibility

Run the project locally:

```bash
python -m pip install -r requirements.txt
python scripts/download_cosmetics_dataset.py
python scripts/profile_raw_cosmetics.py
python scripts/ingest_raw_events.py
python scripts/run_duckdb_sql.py sql/03_staging_quality.sql
python scripts/run_duckdb_sql.py sql/04_session_mart.sql
python scripts/run_duckdb_sql.py analysis/core_metrics.sql
python scripts/export_metric_tables.py
```
