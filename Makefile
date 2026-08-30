PYTHON ?= python

.PHONY: install download profile ingest stage sessions metrics pipeline export dashboard

install:
	$(PYTHON) -m pip install -r requirements.txt

download:
	$(PYTHON) scripts/download_cosmetics_dataset.py

profile:
	$(PYTHON) scripts/profile_raw_cosmetics.py

ingest:
	$(PYTHON) scripts/ingest_raw_events.py

stage:
	$(PYTHON) scripts/run_duckdb_sql.py sql/03_staging_quality.sql

sessions:
	$(PYTHON) scripts/run_duckdb_sql.py sql/04_session_mart.sql

metrics:
	$(PYTHON) scripts/run_duckdb_sql.py analysis/core_metrics.sql

pipeline: profile ingest stage sessions metrics

export:
	$(PYTHON) scripts/export_metric_tables.py

dashboard:
	$(PYTHON) -m streamlit run dashboard/app.py

