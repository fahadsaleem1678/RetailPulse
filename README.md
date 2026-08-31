# RetailPulse

RetailPulse is a product analytics portfolio project built around cosmetics ecommerce clickstream behavior. It uses DuckDB, SQL, Python, and Streamlit to answer three analyst questions:

1. Where do users drop off in the view-to-cart-to-purchase funnel?
2. Which first-activity or first-purchase cohorts retain or repurchase?
3. Which brands, categories, and purchasing-user segments convert best?


## Results Snapshot

The completed five-month run produced these headline results:

| Metric | Value |
| --- | ---: |
| Raw events profiled | 20,692,840 |
| Reconstructed sessions | 4,535,941 |
| Valid purchase revenue | $6,351,830.29 |
| View-to-cart rate | 18.42% |
| Cart-to-purchase rate | 13.51% |
| View-to-purchase rate | 2.49% |
| Month-1 purchase retention, October 2019 cohort | 18.49% |
| Revenue share from `at_risk_previous_buyer` | 43.77% |

Read the finished case study in `case-study/ecommerce-product-analytics-case-study.md`.
## Dataset

Source: [eCommerce Events History in Cosmetics Shop](https://www.kaggle.com/datasets/mkechinov/ecommerce-events-history-in-cosmetics-shop), provided by REES46 Marketing Platform.

Expected raw columns:

- `event_time`
- `event_type`
- `product_id`
- `category_id`
- `category_code`
- `brand`
- `price`
- `user_id`
- `user_session`

Raw data is intentionally not committed. This workspace can use `data/archive.zip` as the local Kaggle archive and extract the CSV files to `data/raw/cosmetics/`.

## Setup

```bash
python -m pip install -r requirements.txt
```

The acquisition script first looks for `data/archive.zip`. If that file is absent, Kaggle credentials must be configured so it can download the dataset with `kagglehub`.

## Pipeline

```bash
python scripts/download_cosmetics_dataset.py
python scripts/profile_raw_cosmetics.py
python scripts/ingest_raw_events.py
python scripts/run_duckdb_sql.py sql/03_staging_quality.sql
python scripts/run_duckdb_sql.py sql/04_session_mart.sql
python scripts/run_duckdb_sql.py analysis/core_metrics.sql
python scripts/export_metric_tables.py
```

Or, if `make` is available:

```bash
make pipeline
make export
```

Close the Streamlit dashboard before rerunning pipeline steps that write to DuckDB; DuckDB allows one writer at a time.

Generated local artifacts:

- `data/raw/cosmetics/` raw Kaggle CSV files, ignored by git.
- `data/warehouse/retailpulse.duckdb` local DuckDB warehouse, ignored by git.
- `data/processed/events/` generated Parquet copy, ignored by git.
- `data/exports/` generated metric CSV files for sharing or dashboard checks.

## Metric Definitions

Funnel metrics are session-level:

- View stage: sessions with at least one `view` event.
- Cart stage: sessions with both view and cart events.
- Purchase stage: sessions with view, cart, and purchase events.
- Multiple purchase rows in one session count as one converted session for funnel conversion.
- Revenue sums valid non-negative purchase event prices; invalid purchase rows are counted separately in quality/session outputs.

Cohort metrics are user-month based:

- Activity cohorts use first activity month.
- Purchase cohorts use first purchase month.
- Activity retention and purchase retention are reported separately.

Segmentation uses purchasing users only:

- `high_value_loyal`
- `recent_first_time`
- `at_risk_previous_buyer`
- `low_value_occasional`

## Dashboard

```bash
python -m streamlit run dashboard/app.py
```

The dashboard reads generated DuckDB summary tables and does not scan raw CSV files.

## Case Study

Start here after the metrics are generated:

- `case-study/ecommerce-product-analytics-case-study.md`
- `docs/insight-synthesis.md`
- `docs/data-dictionary.md`

## E2E Test

Run the final dashboard E2E test with Playwright:

```bash
PYTHON="python" node tests/e2e/dashboard.spec.cjs
```

The test starts Streamlit on port `8502`, verifies the funnel, cohort, and segment tabs, and writes an ignored screenshot to `test-results/dashboard-e2e.png`.
## Scope Boundaries

Version 1 does not include streaming, multi-dataset joins, predictive ML, or production warehouse orchestration.

