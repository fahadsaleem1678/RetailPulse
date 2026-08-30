# Dataset Recommendation: Cosmetics Ecommerce Product Analytics

## Recommendation

RetailPulse will use the Kaggle dataset [eCommerce Events History in Cosmetics Shop](https://www.kaggle.com/datasets/mkechinov/ecommerce-events-history-in-cosmetics-shop) as the source for the portfolio analytics project.

This dataset keeps the REES46-style ecommerce event-stream schema from the larger multi-category store dataset while narrowing the scope to a cosmetics online store. It covers product behavior events from October 2019 through February 2020, which is enough history for funnel, retention, and segment analysis while remaining realistic for a laptop-friendly portfolio project.

## Why This Dataset

The cosmetics dataset is a better fit for the first public version of the project because it supports the same core product analytics questions with a smaller and more finishable scope:

- Where do users drop off in the view-to-cart-to-purchase funnel?
- Which first-activity or first-purchase cohorts retain or repurchase?
- Which brands, categories, and customer segments convert best?

It also keeps the project focused on product analytics rather than heavy infrastructure. DuckDB, SQL models, Python profiling, and a lightweight dashboard are enough to produce credible business findings without adding out-of-scope streaming, multi-dataset joins, or predictive ML.

## Dataset Contract

Expected columns:

| Column | Description |
| --- | --- |
| `event_time` | UTC timestamp of the event. |
| `event_type` | Event type: `view`, `cart`, `remove_from_cart`, or `purchase`. |
| `product_id` | Product identifier. |
| `category_id` | Product category identifier. |
| `category_code` | Category taxonomy when available. |
| `brand` | Lowercase brand name when available. |
| `price` | Product price. |
| `user_id` | Permanent user identifier. |
| `user_session` | Session identifier. |

## Modeling Implications

- Multiple purchase rows can occur in one session. Funnel conversion should treat that as one converted session, while revenue should still sum all purchase event prices.
- `category_code` and `brand` can be missing. Modeling should preserve unknown values explicitly instead of filtering them out.
- The dataset is large enough to justify DuckDB and SQL-first modeling, but small enough to support an internship portfolio cycle.

## Scope Boundaries

Version 1 will include:

- Raw Kaggle CSV files stored locally under `data/raw/cosmetics/`.
- A DuckDB warehouse at `data/warehouse/retailpulse.duckdb`.
- Staging models for typed and cleaned event data.
- Mart models for sessions, users, cohorts, products/categories, and segments.
- Repeatable SQL and Python analysis for funnel, cohort retention, and RFM-style segmentation.
- A concise case study and dashboard based on generated summary tables.

Version 1 will not include:

- Streaming ingestion.
- Multi-dataset joins.
- Predictive machine learning.
- Production warehouse orchestration.

## First Milestone

Build the one-month MVP with October 2019 only:

1. Download the raw dataset.
2. Ingest the October 2019 file.
3. Build `stg_events` and `mart_sessions`.
4. Produce the first funnel analysis.
5. Validate row counts and funnel denominators.
6. Write a short interim finding.

After the October path is validated, expand the same pipeline to November 2019 through February 2020.
