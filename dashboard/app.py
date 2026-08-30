"""RetailPulse Streamlit dashboard.

The dashboard reads generated summary tables from DuckDB. It does not scan raw
CSV files; run the pipeline first to create the metric tables.
"""

from __future__ import annotations

import os
from pathlib import Path

import duckdb
import pandas as pd
import plotly.express as px
import streamlit as st


DEFAULT_DB_PATH = Path("data/warehouse/retailpulse.duckdb")
REQUIRED_TABLES = [
    "metric_session_funnel_overall",
    "metric_session_funnel_by_month",
    "metric_session_funnel_by_brand",
    "metric_session_funnel_by_category",
    "metric_session_funnel_by_price_band",
    "metric_activity_cohort_retention",
    "metric_purchase_cohort_retention",
    "metric_rfm_segment_summary",
]


st.set_page_config(page_title="RetailPulse", layout="wide")
st.title("RetailPulse")
st.caption("Cosmetics ecommerce product analytics")


@st.cache_resource
def connect(db_path: str) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(db_path, read_only=True)


@st.cache_data
def read_table(db_path: str, table_name: str) -> pd.DataFrame:
    con = connect(db_path)
    return con.execute(f"SELECT * FROM {table_name}").fetchdf()


def database_path() -> Path:
    return Path(os.environ.get("RETAILPULSE_DUCKDB", DEFAULT_DB_PATH))


def available_tables(db_path: Path) -> set[str]:
    con = connect(str(db_path))
    rows = con.execute("SHOW TABLES").fetchall()
    return {row[0] for row in rows}


def stop_if_not_ready(db_path: Path) -> None:
    if not db_path.exists():
        st.info("Run the pipeline before opening the dashboard.")
        st.code(
            "\n".join(
                [
                    "python scripts/ingest_raw_events.py",
                    "python scripts/run_duckdb_sql.py sql/03_staging_quality.sql",
                    "python scripts/run_duckdb_sql.py sql/04_session_mart.sql",
                    "python scripts/run_duckdb_sql.py analysis/core_metrics.sql",
                ]
            ),
            language="bash",
        )
        st.stop()

    missing = sorted(set(REQUIRED_TABLES) - available_tables(db_path))
    if missing:
        st.info("Metric tables are missing. Run the analytics SQL before opening the dashboard.")
        st.write(missing)
        st.code("python scripts/run_duckdb_sql.py analysis/core_metrics.sql", language="bash")
        st.stop()


def rate_column(frame: pd.DataFrame, column: str) -> pd.Series:
    return (frame[column].fillna(0) * 100).round(2)


def filtered_funnel_by_month(frame: pd.DataFrame, selected_months: list[str]) -> pd.DataFrame:
    if not selected_months:
        return frame
    month_labels = pd.to_datetime(frame["session_month"]).dt.strftime("%Y-%m")
    return frame[month_labels.isin(selected_months)]


def selected_labels(frame: pd.DataFrame, column: str, label: str) -> list[str]:
    options = sorted(str(value) for value in frame[column].dropna().unique())
    return st.sidebar.multiselect(label, options=options)


db_path = database_path()
st.sidebar.write(f"Warehouse: `{db_path}`")
stop_if_not_ready(db_path)

funnel_overall = read_table(str(db_path), "metric_session_funnel_overall")
funnel_month = read_table(str(db_path), "metric_session_funnel_by_month")
funnel_brand = read_table(str(db_path), "metric_session_funnel_by_brand")
funnel_category = read_table(str(db_path), "metric_session_funnel_by_category")
funnel_price = read_table(str(db_path), "metric_session_funnel_by_price_band")
activity_cohort = read_table(str(db_path), "metric_activity_cohort_retention")
purchase_cohort = read_table(str(db_path), "metric_purchase_cohort_retention")
segment_summary = read_table(str(db_path), "metric_rfm_segment_summary")

month_options = pd.to_datetime(funnel_month["session_month"]).dt.strftime("%Y-%m").tolist()
selected_months = st.sidebar.multiselect("Month", options=month_options)
selected_brands = selected_labels(funnel_brand, "brand", "Brand")
selected_categories = selected_labels(funnel_category, "category_code", "Category")
selected_price_bands = selected_labels(funnel_price, "entry_price_band", "Price band")

funnel_tab, cohort_tab, segment_tab = st.tabs(["Funnel", "Cohorts", "Segments"])

with funnel_tab:
    overall = funnel_overall.iloc[0]
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Viewed sessions", f"{int(overall['viewed_sessions']):,}")
    col2.metric("View to cart", f"{overall['view_to_cart_rate'] * 100:.2f}%")
    col3.metric("Cart to purchase", f"{overall['cart_to_purchase_rate'] * 100:.2f}%")
    col4.metric("Purchase revenue", f"${overall['purchase_revenue']:,.0f}")

    stages = pd.DataFrame(
        {
            "stage": ["View", "Cart after view", "Purchase after cart"],
            "sessions": [
                overall["viewed_sessions"],
                overall["carted_after_view_sessions"],
                overall["purchased_after_cart_sessions"],
            ],
        }
    )
    st.plotly_chart(
        px.bar(stages, x="stage", y="sessions", text="sessions", title="Session funnel stage reach"),
        use_container_width=True,
    )

    month_frame = filtered_funnel_by_month(funnel_month.copy(), selected_months)
    if not month_frame.empty:
        month_plot = month_frame.assign(
            view_to_cart_pct=rate_column(month_frame, "view_to_cart_rate"),
            cart_to_purchase_pct=rate_column(month_frame, "cart_to_purchase_rate"),
            view_to_purchase_pct=rate_column(month_frame, "view_to_purchase_rate"),
        )
        st.plotly_chart(
            px.line(
                month_plot,
                x="session_month",
                y=["view_to_cart_pct", "cart_to_purchase_pct", "view_to_purchase_pct"],
                markers=True,
                title="Session conversion rates by month",
            ),
            use_container_width=True,
        )

    brand_frame = funnel_brand if not selected_brands else funnel_brand[funnel_brand["brand"].astype(str).isin(selected_brands)]
    category_frame = funnel_category if not selected_categories else funnel_category[funnel_category["category_code"].astype(str).isin(selected_categories)]
    price_frame = funnel_price if not selected_price_bands else funnel_price[funnel_price["entry_price_band"].astype(str).isin(selected_price_bands)]

    col1, col2 = st.columns(2)
    col1.dataframe(brand_frame.head(25), use_container_width=True, hide_index=True)
    col2.dataframe(category_frame.head(25), use_container_width=True, hide_index=True)
    st.dataframe(price_frame, use_container_width=True, hide_index=True)

with cohort_tab:
    if not activity_cohort.empty:
        activity_heatmap = activity_cohort.pivot_table(
            index="first_activity_month",
            columns="months_since_first_activity",
            values="activity_retention_rate",
            aggfunc="mean",
        )
        st.plotly_chart(
            px.imshow(activity_heatmap, aspect="auto", title="Activity retention by first activity month"),
            use_container_width=True,
        )

    if not purchase_cohort.empty:
        purchase_heatmap = purchase_cohort.pivot_table(
            index="first_purchase_month",
            columns="months_since_first_purchase",
            values="purchase_retention_rate",
            aggfunc="mean",
        )
        st.plotly_chart(
            px.imshow(purchase_heatmap, aspect="auto", title="Purchase retention by first purchase month"),
            use_container_width=True,
        )

with segment_tab:
    if not segment_summary.empty:
        st.plotly_chart(
            px.bar(
                segment_summary,
                x="rfm_segment",
                y="purchase_revenue",
                text="users",
                title="Revenue by purchasing-user segment",
            ),
            use_container_width=True,
        )
        st.dataframe(segment_summary, use_container_width=True, hide_index=True)
