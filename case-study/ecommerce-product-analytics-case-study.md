# RetailPulse Ecommerce Product Analytics Case Study

## Executive Summary

RetailPulse analyzes cosmetics ecommerce clickstream behavior from October 2019 through February 2020 to identify funnel drop-off, cohort retention, and revenue-driving customer segments.

This case study is pending metric values until the raw Kaggle files are downloaded and the pipeline is run.

## Dataset and Scope

Source: [eCommerce Events History in Cosmetics Shop](https://www.kaggle.com/datasets/mkechinov/ecommerce-events-history-in-cosmetics-shop)

The analysis uses historical clickstream events from a cosmetics ecommerce store. Version 1 focuses on batch product analytics and excludes streaming, multi-dataset joins, and predictive modeling.

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

## Finding 1: Funnel Drop-Off

Business question: Where do users drop off between product views, carting, and purchase?

Method: Use session-level funnel metrics from `metric_session_funnel_overall` and segment cuts from the funnel breakdown tables.

Metric result: Pending pipeline run.

Interpretation: Pending pipeline run.

Recommendation: Pending metric-backed recommendation.

## Finding 2: Cohort Retention

Business question: Do users return or repurchase after their first activity or first purchase month?

Method: Compare activity retention and purchase retention using `metric_activity_cohort_retention` and `metric_purchase_cohort_retention`.

Metric result: Pending pipeline run.

Interpretation: Pending pipeline run.

Recommendation: Pending metric-backed recommendation.

## Finding 3: Segment and Revenue Concentration

Business question: Which purchasing customer segments contribute the most revenue and repeat behavior?

Method: Use RFM-style purchasing-user segments from `mart_user_rfm_segments` and `metric_rfm_segment_summary`.

Metric result: Pending pipeline run.

Interpretation: Pending pipeline run.

Recommendation: Pending metric-backed recommendation.

## Caveats

- `brand` and `category_code` can be missing. The pipeline preserves those values as `unknown_brand` and `unknown_category` rather than dropping the rows.
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
```
