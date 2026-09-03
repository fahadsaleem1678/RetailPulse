# Dashboard

Phase 7 uses Streamlit to expose the generated product analytics summary tables in a dark RetailPulse cockpit UI. It prefers the local DuckDB warehouse and falls back to committed CSV metric exports for hosted deployments.

For the local DuckDB workflow, run the pipeline first:

```bash
python scripts/ingest_raw_events.py
python scripts/run_duckdb_sql.py sql/03_staging_quality.sql
python scripts/run_duckdb_sql.py sql/04_session_mart.sql
python scripts/run_duckdb_sql.py analysis/core_metrics.sql
```

Start the dashboard after the pipeline has finished. Close the Streamlit dashboard before rerunning pipeline steps that write to DuckDB; DuckDB allows one writer at a time. If the DuckDB warehouse is unavailable, the dashboard loads the tracked CSV exports from `data/exports/`.

Start the dashboard:

```bash
python -m streamlit run dashboard/app.py
```

Optional database override:

```bash
RETAILPULSE_DUCKDB=data/warehouse/retailpulse.duckdb python -m streamlit run dashboard/app.py
```

## Views

- Overview: KPI cards, sales overview, conversion trend, and brand/category/price-band tables.
- Cohorts: activity and purchase retention heatmaps with cohort detail.
- Segments: RFM segment revenue, revenue share, and customer-list summary.

## Validation Results

- Dashboard server started successfully with `python -m streamlit run dashboard/app.py --server.headless true --server.port 8501`.
- Local health check returned HTTP 200 from `http://localhost:8501`.
- Dashboard reads from generated DuckDB metric tables locally and falls back to tracked metric CSV exports for hosted deployment; raw event CSVs are not scanned at dashboard runtime.
- Portfolio screenshots were captured under `case-study/images/` for overview, cohort, and segment views.
- Final Playwright E2E passed against Streamlit on port `8502`; overview, cohort, and segment tabs rendered successfully.


## Streamlit Cloud Deployment

Use these settings when creating the app:

- Repository: `fahadsaleem1678/RetailPulse`
- Branch: `main`
- Main file path: `dashboard/app.py`

No secrets are required for the portfolio dashboard. The deployed app uses the committed `data/exports/*.csv` files when `data/warehouse/retailpulse.duckdb` is not present.

## Playwright E2E

Run:

```bash
PYTHON="python" node tests/e2e/dashboard.spec.cjs
```

The test starts its own Streamlit process on port `8502` and checks the overview, cohort, and segment tabs.
## Phase 7 Gate

After data is loaded, confirm that:

- The dashboard loads from generated DuckDB summary tables with the redesigned dark cockpit styling.
- Filters do not produce broken charts or divide-by-zero errors.
- Dashboard values match sampled SQL outputs from `analysis/core_metrics.sql`.
- Screenshots are readable for the portfolio case study.
