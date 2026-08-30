# Interview Script

## Short Version

RetailPulse is a cosmetics ecommerce product analytics project. I chose a REES46 clickstream dataset that is realistic enough for session reconstruction and cohort analysis but scoped tightly enough to finish and polish. The pipeline uses DuckDB for local analytical processing, SQL for modeling, Python for reproducible commands, and Streamlit for a lightweight dashboard.

## Trade-Offs

- I chose DuckDB instead of PostgreSQL because the workload is local analytical scanning, not app transactions.
- I kept the first milestone to October 2019 so row counts, funnel denominators, and session logic could be validated before expanding to all five months.
- I preserved missing brand and category values as explicit unknowns because filtering them out would bias conversion and revenue views.
- I avoided predictive ML in v1 because the target role is product analytics and the strongest story is business interpretation from reliable metrics.

## Walkthrough

1. Dataset and scope: cosmetics clickstream events, October 2019 through February 2020.
2. Pipeline: raw CSVs, DuckDB ingestion, staging quality, session mart, core metrics, dashboard.
3. Funnel: session-level view to cart to purchase, with multiple purchase rows handled correctly.
4. Retention: activity retention and purchase retention kept separate.
5. Segmentation: purchasing users labeled with practical RFM-style segments.
6. Caveats: observational data, missing dimensions, no acquisition channels, no causal claims.

## Questions to Be Ready For

- Why DuckDB instead of pandas alone?
- How did you define a converted session?
- How did you prevent missing `brand` and `category_code` from biasing the analysis?
- How do event-level revenue and session-level funnel metrics differ?
- What would you do in v2 if acquisition-channel data were available?
