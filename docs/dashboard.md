# Dashboard

Phase 7 uses Streamlit to expose the generated product analytics summary tables.

Run the pipeline first:

```bash
python scripts/ingest_raw_events.py
python scripts/run_duckdb_sql.py sql/03_staging_quality.sql
python scripts/run_duckdb_sql.py sql/04_session_mart.sql
python scripts/run_duckdb_sql.py analysis/core_metrics.sql
```

Start the dashboard:

```bash
streamlit run dashboard/app.py
```

Optional database override:

```bash
RETAILPULSE_DUCKDB=data/warehouse/retailpulse.duckdb streamlit run dashboard/app.py
```

## Views

- Funnel: session-level stage reach, monthly conversion rates, brand/category/price-band tables.
- Cohorts: activity and purchase retention heatmaps.
- Segments: RFM segment revenue and user summary.

## Phase 7 Gate

After data is loaded, confirm that:

- The dashboard loads from generated DuckDB summary tables.
- Filters do not produce broken charts or divide-by-zero errors.
- Dashboard values match sampled SQL outputs from `analysis/core_metrics.sql`.
- Screenshots are readable for the portfolio case study.
