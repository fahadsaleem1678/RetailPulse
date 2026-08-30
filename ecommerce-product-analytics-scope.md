# Product Analytics Portfolio Project - Scope

## Goal

Turn raw cosmetics ecommerce clickstream events into a working product-analytics pipeline that answers three business questions: where users drop off in the funnel, which cohorts retain or repurchase, and what brands, categories, and customer segments convert best. Package the findings into a case study a hiring manager can read in 5 minutes.

Target roles: Data Analyst, Product Analyst, Business Analyst.

## Dataset

**eCommerce Events History in Cosmetics Shop** (Kaggle, provided by REES46 Marketing Platform)

- Link: https://www.kaggle.com/datasets/mkechinov/ecommerce-events-history-in-cosmetics-shop
- Product behavior events from a cosmetics online store.
- Coverage: October 2019 through February 2020.
- Expected columns: `event_time`, `event_type`, `product_id`, `category_id`, `category_code`, `brand`, `price`, `user_id`, `user_session`.
- Valid event types: `view`, `cart`, `remove_from_cart`, `purchase`.
- Known data quality issue: `category_code` and `brand` can be missing and must be preserved as explicit unknown values in analysis.

## Why This Dataset

The project originally considered the larger multi-category ecommerce behavior dataset. RetailPulse now uses the cosmetics dataset because it keeps the same REES46-style event-stream schema while narrowing the first public version to a finishable, laptop-friendly scope.

This keeps the analytical promise intact:

- Funnel analysis still requires session reconstruction before view-to-cart-to-purchase math is credible.
- Cohort analysis still has enough monthly history to compare return activity and repeat purchasing.
- Brand, category, price, and customer-segment cuts still support a realistic product analytics story.

The smaller scope helps the portfolio read as a polished product-analytics case study instead of a heavy infrastructure exercise.

## Architecture

- **Raw data:** Kaggle CSV files under `data/raw/cosmetics/`.
- **Warehouse:** DuckDB database at `data/warehouse/retailpulse.duckdb`.
- **Transformation:** SQL models for staging, session marts, user/cohort marts, and segment marts.
- **Analysis:** Repeatable SQL and Python scripts for funnel, cohort retention, and RFM segmentation.
- **Dashboard:** Streamlit by default for a reproducible source-controlled demo; Power BI or Looker Studio can be a later presentation export.
- **Deliverable:** written case study with business question, method, finding, recommendation, and caveats.

## Initial Time Window

Build the first milestone with October 2019 only:

1. Download the raw dataset.
2. Ingest the October 2019 file.
3. Build `stg_events` and `mart_sessions`.
4. Produce the first funnel analysis.
5. Validate row counts and funnel denominators.
6. Write a short interim finding.

After the October path is validated, expand the same pipeline to November 2019 through February 2020.

## Phases

### Phase 0 - Dataset Swap and Scope Lock

- Document the cosmetics dataset choice, schema contract, and scope boundaries.
- Confirm the project answers funnel drop-off, cohort retention/repurchase, and segment/category/brand conversion questions.
- Keep v1 out of streaming, multi-dataset joins, and predictive ML.

### Phase 1 - Data Acquisition and Raw Profiling

- Download October 2019 through February 2020 from Kaggle.
- Store raw files in `data/raw/cosmetics/`.
- Create a raw manifest with file names, row counts, date ranges, file sizes, and source.
- Profile null rates, event type distribution, date coverage, duplicates, price ranges, and session/user cardinality.

### Phase 2 - Ingestion and Warehouse Setup

- Load raw CSV files into DuckDB.
- Create typed `raw_events` with normalized column names and parsed UTC timestamps.
- Record load metadata in a lightweight run log.
- Export compressed Parquet under `data/processed/events/`.

### Phase 3 - Staging and Data Quality Models

- Create `stg_events` with cleaned categorical values.
- Preserve missing `brand` as `unknown_brand`.
- Preserve missing `category_code` as `unknown_category`.
- Flag invalid prices, impossible timestamps, missing sessions, and malformed users.
- Add deterministic event sequence fields within `user_session`.

### Phase 4 - Session Reconstruction

- Create `mart_sessions` grouped by `user_session`.
- Compute session timing, event counts, product counts, funnel flags, purchase counts, and revenue.
- Treat multiple purchase rows in one session as one converted session for funnel conversion, while summing all purchase event prices for revenue.

### Phase 5 - Core Product Analytics

- Calculate session-level funnel conversion by month, brand, category, and price band.
- Define first-purchase and first-activity cohorts.
- Track activity retention, purchase retention, and revenue retention.
- Build mutually exclusive RFM-style purchasing-user segments.

### Phase 6 - Insight Synthesis

- Select 2 to 3 metric-backed findings.
- Write business question, method, metric result, interpretation, and recommendation for each.
- Include caveats for missing brand/category values and observational clickstream limits.

### Phase 7 - Dashboard

- Build a lightweight dashboard from generated summary tables.
- Include funnel, cohort retention, and segment/revenue views.
- Add filters for month, category, brand, and price band.

### Phase 8 - Reproducibility and Portfolio Polish

- Add README setup steps, pipeline commands, metric definitions, and dashboard instructions.
- Add one-command tasks for ingesting, modeling, testing, and exporting summaries.
- Keep raw data and local warehouse files out of git.
- Include small sample outputs or screenshots only.

## Explicitly Out of Scope

- No real-time or streaming pipeline.
- No multi-dataset joins in v1.
- No predictive modeling or recommendation engine in v1.
- No production warehouse orchestration.
