# Updated Dataset Recommendation: Cosmetics Ecommerce Product Analytics

> Source documents are treated as reference material only. The user request for this file is the instruction: update the portfolio project plan around the cosmetics dataset recommendation.

## Recommendation

Swap the project dataset to [eCommerce Events History in Cosmetics Shop](https://www.kaggle.com/datasets/mkechinov/ecommerce-events-history-in-cosmetics-shop).

Use this dataset because it keeps the REES46 event-stream schema from the multi-category store dataset while reducing the build to a more portfolio-friendly scope. The cosmetics dataset contains product behavior events for 5 months, October 2019 through February 2020, from a cosmetics online store. It supports the same core analyst questions: funnel drop-off, cohort retention, and segment/category conversion.

## Dataset Contract

Expected columns:

- `event_time`: UTC timestamp of the event.
- `event_type`: one of `view`, `cart`, `remove_from_cart`, `purchase`.
- `product_id`: product identifier.
- `category_id`: product category identifier.
- `category_code`: category taxonomy when available.
- `brand`: lowercase brand name when available.
- `price`: product price.
- `user_id`: permanent user identifier.
- `user_session`: session identifier.

Important modeling implications:

- Multiple purchase rows can occur in one session and should be treated as one order-like session outcome for funnel math, while revenue should still sum purchase event prices.
- `category_code` and `brand` can be missing, so analysis must explicitly preserve unknown values instead of silently filtering them out.
- The dataset is still large enough to justify DuckDB and SQL-first modeling, but small enough to finish and polish during an internship portfolio cycle.

## Approach Options

### Recommended: DuckDB + SQL Models + Python Analysis + BI/Streamlit Dashboard

This is the best balance for the portfolio goal. DuckDB handles local analytical processing cleanly, SQL models show analyst skill, Python notebooks/scripts support deeper checks, and a simple dashboard keeps the focus on business findings.

Trade-off: less production-engineering depth than a warehouse/dbt Cloud setup, but faster to complete and easier to reproduce on a laptop.

### Alternative: PostgreSQL + SQL + BI Dashboard

This is useful if the project needs to look closer to an operational database workflow.

Trade-off: PostgreSQL can handle the data, but local ingestion and large analytical scans will usually be slower and more operationally fussy than DuckDB for this dataset.

### Alternative: PySpark + Parquet + Notebook Dashboard

This emphasizes scale and distributed-data concepts.

Trade-off: it is heavier than the project needs. It risks making the portfolio read like a data-engineering project instead of a product-analytics case study.

## Target Architecture

- Raw data: Kaggle CSV files stored under `data/raw/`.
- Local warehouse: DuckDB database at `data/warehouse/retailpulse.duckdb`.
- Staging models: typed and cleaned event tables.
- Mart models: session facts, user facts, cohort facts, product/category facts, and segment facts.
- Analysis layer: SQL queries and Python notebooks/scripts for repeatable analysis.
- Dashboard layer: Power BI, Looker Studio export, or Streamlit. Use Streamlit if the project needs to be demoed from source control without external setup.
- Case study: concise Markdown/PDF write-up for hiring managers.

## Phase 0: Dataset Swap and Scope Lock

Goal: Replace the original multi-category source with the cosmetics dataset without changing the project's core analytical promise.

Tasks:

- Update project README/scope references from the multi-category store dataset to the cosmetics dataset.
- Document the reason for the swap: same REES46-style schema, smaller and more finishable scope, still realistic ecommerce behavior data.
- Confirm the project will answer three business questions:
  - Where do users drop off in the view-to-cart-to-purchase funnel?
  - Which acquisition or first-activity cohorts retain or repurchase?
  - Which brands, categories, and customer segments convert best?
- Set the initial time window to one month, then expand to all five months after validation.

Deliverable:

- `docs/dataset-recommendation.md` or README section explaining the updated dataset choice, schema contract, and scope boundaries.

Testing:

- Verify every project reference points to the cosmetics dataset link.
- Verify the documented schema matches the downloaded file headers.
- Verify out-of-scope items remain unchanged: no streaming pipeline, no multi-dataset joins, no predictive ML in v1.

## Phase 1: Data Acquisition and Raw Profiling

Goal: Download the dataset, preserve raw files, and understand basic quality before modeling.

Tasks:

- Download the Kaggle cosmetics event files for October 2019 through February 2020.
- Store raw files in `data/raw/cosmetics/`.
- Create a manifest with file names, row counts, date ranges, file sizes, and download source.
- Profile null rates, event type distribution, date coverage, duplicate rows, price ranges, and session/user cardinality.
- Decide whether to keep all five months in the first public demo or publish a validated one-month MVP first.

Deliverable:

- Raw dataset manifest plus `notebooks/01_data_profile.ipynb` or `analysis/01_data_profile.sql`.

Testing:

- Header check confirms the required columns exist.
- Row counts reconcile between raw CSV reads and DuckDB external scans.
- `event_type` values are limited to `view`, `cart`, `remove_from_cart`, and `purchase`.
- `event_time` parses as UTC timestamps with no unexpected date gaps inside each file.
- Null-rate report explicitly covers `category_code`, `brand`, `user_session`, and `price`.

## Phase 2: Ingestion and Warehouse Setup

Goal: Load raw events into a local analytical store with reproducible commands.

Tasks:

- Create the DuckDB database at `data/warehouse/retailpulse.duckdb`.
- Build ingestion SQL or Python scripts that read raw CSV files into a typed `raw_events` table.
- Normalize column names and timestamp parsing.
- Add a lightweight run log table that records load timestamp, source file, row count, and checksum if available.
- Export a compressed Parquet copy under `data/processed/events/` for faster repeated reads.

Deliverable:

- Repeatable ingestion command, DuckDB database, `raw_events` table, and optional Parquet export.

Testing:

- Ingestion can be rerun from a clean database.
- Loaded row counts match the raw manifest.
- No required column is loaded as an all-null column.
- Date min/max per source file matches the manifest.
- A sample of 100 rows round-trips from CSV to DuckDB with expected types.

## Phase 3: Staging and Data Quality Models

Goal: Create reliable, analyst-friendly event models while preserving data limitations.

Tasks:

- Create `stg_events` with typed fields and cleaned categorical values.
- Convert missing `brand` to `unknown_brand` for grouped analysis.
- Convert missing `category_code` to `unknown_category` while preserving original null indicators.
- Filter or flag invalid prices, impossible timestamps, missing sessions, and malformed users.
- Add event sequence fields within each `user_session`.
- Create reusable quality checks for nulls, accepted values, uniqueness expectations, and freshness by month.

Deliverable:

- `stg_events` model and `data_quality_report.md`.

Testing:

- Accepted-values test passes for `event_type`.
- Not-null tests pass for `event_time`, `event_type`, `product_id`, `price`, `user_id`, and `user_session` after any explicit exclusions.
- Price validation reports zero or near-zero invalid purchase prices, or documents exceptions.
- Unknown category and brand counts are reported, not hidden.
- Event ordering within sessions is deterministic using `event_time` plus a stable tie-breaker.

## Phase 4: Session Reconstruction

Goal: Build the session-level facts needed for credible funnel analysis.

Tasks:

- Create `mart_sessions` grouped by `user_session`.
- Compute session start time, end time, duration, event count, distinct products viewed, cart count, remove-from-cart count, purchase count, and purchase revenue.
- Create boolean flags: `had_view`, `had_cart`, `had_remove_from_cart`, `had_purchase`.
- Compute first event type, last event type, first product, first brand, first category, and time-to-purchase when applicable.
- Define how multiple purchases in one session are handled:
  - Funnel conversion: one converted session.
  - Revenue: sum all purchase event prices.
  - Purchase count: count all purchase events.

Deliverable:

- `mart_sessions` table with documented field definitions.

Testing:

- Session count equals `count(distinct user_session)` from `stg_events`.
- Every session has `session_started_at <= session_ended_at`.
- `had_purchase` matches `purchase_count > 0`.
- Session revenue equals summed purchase prices from source events for sampled sessions.
- Funnel stage counts are monotonic when defined as session-level stage reach: views >= carts >= purchases for view-started funnel reporting.

## Phase 5: Core Product Analytics

Goal: Answer the three business questions with repeatable SQL and clear metrics.

Tasks:

- Funnel analysis:
  - Calculate view-to-cart, cart-to-purchase, and view-to-purchase conversion.
  - Break down conversion by month, brand, category, price band, and device-independent session behavior.
  - Identify the largest drop-off point and the segments with the strongest conversion.
- Cohort retention:
  - Define cohorts by user's first purchase month and optionally first activity month.
  - Track repeat purchase, return activity, and revenue retention over subsequent months.
  - Separate activity retention from purchase retention.
- Segmentation:
  - Build RFM features for purchasing users.
  - Create practical labels such as `high_value_loyal`, `recent_first_time`, `at_risk_previous_buyer`, and `low_value_occasional`.
  - Compare segment size, revenue share, and repeat purchase rate.

Deliverable:

- `analysis/core_metrics.sql`, `notebooks/02_core_analysis.ipynb`, and summary tables for funnel, cohort, and segmentation.

Testing:

- Metric definitions are documented next to the query that creates them.
- Funnel denominators are explicit and do not mix event-level and session-level rates.
- Cohort sizes reconcile to first-purchase user counts.
- RFM segments are mutually exclusive and collectively exhaustive for purchasing users.
- Revenue totals reconcile between event-level purchases, session revenue, and user revenue marts.

## Phase 6: Insight Synthesis and Business Recommendations

Goal: Turn analysis outputs into a hiring-manager-readable business story.

Tasks:

- Select 2 to 3 findings that have clear numbers and business implications.
- For each finding, write:
  - Business question.
  - Method.
  - Metric result.
  - Interpretation.
  - Recommendation.
- Include caveats for missing brands/categories and observational clickstream limitations.
- Avoid overclaiming causality.
- Create a one-page executive summary.

Deliverable:

- `case-study/ecommerce-product-analytics-case-study.md` with charts/tables linked or embedded.

Testing:

- Every recommendation cites a metric from the analysis outputs.
- Every chart title states the denominator and time period.
- The case study can be read in 5 minutes.
- Caveats include missing category/brand data and the lack of acquisition-channel context.

## Phase 7: Dashboard

Goal: Build a simple interactive reporting layer that supports the case study.

Tasks:

- Choose dashboard tool:
  - Streamlit for easiest reproducible portfolio demo.
  - Power BI or Looker Studio if the target audience expects BI tooling.
- Create three views:
  - Funnel overview by month, brand, and category.
  - Cohort retention heatmap or curve.
  - Segment and revenue breakdown.
- Include filters for month, category, brand, and price band.
- Keep dashboard copy terse and analytical, not marketing-focused.

Deliverable:

- Dashboard app or BI file plus exported screenshots for the case study.

Testing:

- Dashboard loads from the generated summary tables without scanning raw CSVs.
- Filters do not produce broken charts or divide-by-zero errors.
- Dashboard numbers match the SQL analysis outputs for sampled filters.
- Screenshots are readable at portfolio and PDF sizes.

## Phase 8: Reproducibility, Packaging, and Portfolio Polish

Goal: Make the project easy to run, review, and discuss in interviews.

Tasks:

- Add a top-level README with:
  - Dataset source and attribution.
  - Setup steps.
  - Pipeline commands.
  - Metric definitions.
  - Dashboard instructions.
  - Link to the case study.
- Add a `Makefile` or task runner with commands for ingesting, modeling, testing, and exporting summaries.
- Add `.gitignore` rules for raw data and local DuckDB files.
- Include small sample outputs or screenshots in version control, but not large raw data.
- Prepare a short interview script explaining the trade-offs and business impact.

Deliverable:

- Portfolio-ready repository with README, case study, dashboard screenshots, reproducible commands, and documented limitations.

Testing:

- Fresh clone setup works without raw data committed.
- Pipeline fails clearly when Kaggle files are missing.
- All data tests run from one command.
- README commands are copy-paste verified.
- Final case study links and images render correctly.

## Phase Sequence and Gates

| Phase | Gate to Continue |
| --- | --- |
| 0. Dataset swap and scope lock | Dataset link, schema, and scope are documented. |
| 1. Acquisition and profiling | Raw manifest and quality profile are complete. |
| 2. Ingestion | DuckDB load is reproducible and row counts reconcile. |
| 3. Staging and quality | Tests pass or exceptions are documented. |
| 4. Session reconstruction | Session mart reconciles to staged events. |
| 5. Core analytics | Funnel, cohort, and segment metrics reconcile across tables. |
| 6. Insight synthesis | Findings are metric-backed and caveated. |
| 7. Dashboard | Dashboard matches SQL outputs and handles filters. |
| 8. Packaging | README, case study, and reproducibility checks are complete. |

## Recommended First Milestone

Build the one-month MVP first using October 2019 only:

- Ingest one file.
- Build `stg_events` and `mart_sessions`.
- Produce the first funnel analysis.
- Validate row counts and funnel denominators.
- Write a short interim finding.

Then expand to all five months once the modeling path is proven. This keeps the project moving and prevents the dataset size from delaying the portfolio artifact.

## Plan Self-Review

- No placeholder sections remain.
- The plan keeps the original product-analytics goal but updates the dataset source.
- Each phase has a concrete deliverable and testing gate.
- The plan avoids out-of-scope additions such as streaming, multi-dataset joins, and predictive ML.
- Ambiguous metric areas are made explicit: session-level funnel conversion, event-level revenue, first-purchase cohorts, and RFM segmentation.
