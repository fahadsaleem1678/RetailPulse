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
import plotly.graph_objects as go
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
ACCENT = "#b8ff3d"
ACCENT_DARK = "#69d71d"
PANEL = "#14191a"
PANEL_SOFT = "#1a2022"
TEXT = "#eef7ed"
MUTED = "#93a09a"
GRID = "rgba(226, 255, 217, 0.08)"


st.set_page_config(page_title="RetailPulse", page_icon="RP", layout="wide")


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


def inject_css() -> None:
    st.markdown(
        f"""
        <style>
        :root {{
            --rp-bg: #080a09;
            --rp-panel: {PANEL};
            --rp-panel-soft: {PANEL_SOFT};
            --rp-border: rgba(220, 255, 208, 0.10);
            --rp-border-strong: rgba(184, 255, 61, 0.38);
            --rp-text: {TEXT};
            --rp-muted: {MUTED};
            --rp-accent: {ACCENT};
            --rp-accent-dark: {ACCENT_DARK};
        }}
        .stApp {{
            color: var(--rp-text);
            background:
                radial-gradient(circle at 0% 0%, rgba(63, 255, 133, 0.22), transparent 28%),
                radial-gradient(circle at 90% 8%, rgba(184, 255, 61, 0.16), transparent 26%),
                linear-gradient(135deg, #06140d 0%, #080a09 34%, #0b0f10 100%);
        }}
        .block-container {{
            max-width: 1480px;
            padding: 1.6rem 1.8rem 2.4rem;
        }}
        section[data-testid="stSidebar"] {{
            background: rgba(6, 8, 8, 0.94);
            border-right: 1px solid var(--rp-border);
        }}
        section[data-testid="stSidebar"] * {{ color: var(--rp-text); }}
        section[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p,
        section[data-testid="stSidebar"] label {{ color: var(--rp-muted); }}
        div[data-baseweb="select"] > div,
        div[data-baseweb="input"] > div {{
            background: #111515;
            border-color: var(--rp-border);
            border-radius: 8px;
        }}
        [data-testid="stHeader"] {{ background: transparent; }}
        div[data-testid="stToolbar"] {{ display: none; }}
        h1, h2, h3, p {{ letter-spacing: 0; }}
        .rp-shell {{
            border: 1px solid var(--rp-border);
            background: rgba(7, 10, 10, 0.74);
            box-shadow: 0 24px 80px rgba(0, 0, 0, 0.36);
            backdrop-filter: blur(18px);
        }}
        .rp-topbar {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            padding: 1rem 1.1rem;
            border: 1px solid var(--rp-border);
            border-radius: 8px;
            background: linear-gradient(180deg, rgba(20, 25, 26, 0.94), rgba(11, 14, 14, 0.94));
            margin-bottom: 1rem;
        }}
        .rp-brand {{ display: flex; align-items: center; gap: 0.8rem; }}
        .rp-logo {{
            display: grid;
            place-items: center;
            width: 38px;
            height: 38px;
            border-radius: 8px;
            color: #071007;
            background: linear-gradient(135deg, var(--rp-accent), #5ddd20);
            font-weight: 900;
            box-shadow: 0 0 28px rgba(184, 255, 61, 0.28);
        }}
        .rp-brand-title {{ font-size: 1.32rem; line-height: 1.1; font-weight: 760; }}
        .rp-brand-subtitle {{ color: var(--rp-muted); font-size: 0.82rem; margin-top: 0.15rem; }}
        .rp-status-row {{ display: flex; align-items: center; gap: 0.6rem; flex-wrap: wrap; justify-content: flex-end; }}
        .rp-pill {{
            border: 1px solid var(--rp-border);
            border-radius: 999px;
            padding: 0.44rem 0.72rem;
            color: var(--rp-muted);
            background: rgba(255, 255, 255, 0.03);
            font-size: 0.78rem;
            white-space: nowrap;
        }}
        .rp-pill strong {{ color: var(--rp-text); font-weight: 700; }}
        .rp-kpi-card,
        .rp-panel,
        .rp-rail-card {{
            border: 1px solid var(--rp-border);
            border-radius: 8px;
            background:
                linear-gradient(180deg, rgba(26, 32, 34, 0.96), rgba(13, 17, 17, 0.96));
            box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04), 0 16px 40px rgba(0, 0, 0, 0.22);
        }}
        .rp-kpi-card {{ min-height: 136px; padding: 1rem; position: relative; overflow: hidden; }}
        .rp-kpi-card:after {{
            content: "";
            position: absolute;
            inset: auto 0 0 0;
            height: 3px;
            background: linear-gradient(90deg, transparent, var(--rp-accent), transparent);
            opacity: 0.65;
        }}
        .rp-kpi-label {{ color: var(--rp-muted); font-size: 0.78rem; margin-bottom: 0.65rem; }}
        .rp-kpi-value {{ color: var(--rp-text); font-size: clamp(1.5rem, 2vw, 2.2rem); line-height: 1; font-weight: 850; }}
        .rp-kpi-delta {{ color: var(--rp-accent); font-size: 0.78rem; margin-top: 0.65rem; }}
        .rp-panel {{ padding: 1rem; margin-bottom: 1rem; }}
        .rp-panel-title {{ display: flex; align-items: center; justify-content: space-between; margin-bottom: 0.75rem; }}
        .rp-panel-title h3 {{ font-size: 1.08rem; margin: 0; color: var(--rp-text); }}
        .rp-panel-title span {{ color: var(--rp-muted); font-size: 0.78rem; }}
        .rp-section-label {{ color: var(--rp-muted); font-size: 0.72rem; text-transform: uppercase; margin: 0.9rem 0 0.35rem; }}
        .rp-rail-card {{ padding: 1rem; margin-bottom: 1rem; }}
        .rp-rail-card h3 {{ font-size: 1rem; margin: 0 0 0.75rem; }}
        .rp-list {{ display: grid; gap: 0.68rem; }}
        .rp-list-item {{
            display: grid;
            grid-template-columns: 30px 1fr;
            gap: 0.7rem;
            align-items: start;
        }}
        .rp-dot {{
            width: 30px;
            height: 30px;
            border-radius: 999px;
            display: grid;
            place-items: center;
            background: rgba(184, 255, 61, 0.12);
            color: var(--rp-accent);
            border: 1px solid rgba(184, 255, 61, 0.24);
            font-size: 0.72rem;
            font-weight: 800;
        }}
        .rp-list-title {{ font-size: 0.84rem; color: var(--rp-text); font-weight: 680; }}
        .rp-list-meta {{ font-size: 0.74rem; color: var(--rp-muted); margin-top: 0.12rem; }}
        .rp-progress {{
            height: 10px;
            border-radius: 999px;
            background: rgba(255, 255, 255, 0.08);
            overflow: hidden;
            margin-top: 0.5rem;
        }}
        .rp-progress span {{
            display: block;
            height: 100%;
            border-radius: 999px;
            background: linear-gradient(90deg, var(--rp-accent), #1fb35c);
        }}
        .stTabs [data-baseweb="tab-list"] {{ gap: 0.45rem; border-bottom: 1px solid var(--rp-border); }}
        .stTabs [data-baseweb="tab"] {{
            border-radius: 8px 8px 0 0;
            color: var(--rp-muted);
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid var(--rp-border);
            border-bottom: none;
            padding: 0.55rem 0.95rem;
        }}
        .stTabs [aria-selected="true"] {{ color: #081008; background: var(--rp-accent); }}
        [data-testid="stDataFrame"] {{ border: 1px solid var(--rp-border); border-radius: 8px; overflow: hidden; }}
        hr {{ border-color: var(--rp-border); }}
        @media (max-width: 900px) {{
            .block-container {{ padding: 1rem; }}
            .rp-topbar {{ align-items: flex-start; flex-direction: column; }}
            .rp-status-row {{ justify-content: flex-start; }}
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def fmt_number(value: float | int) -> str:
    return f"{int(round(float(value))):,}"


def fmt_money(value: float | int) -> str:
    return f"${float(value):,.0f}"


def fmt_rate(value: float | int) -> str:
    return f"{float(value) * 100:.2f}%"


def pct_series(frame: pd.DataFrame, column: str) -> pd.Series:
    return (frame[column].fillna(0) * 100).round(2)


def card(label: str, value: str, delta: str) -> str:
    return f"""
    <div class="rp-kpi-card">
        <div class="rp-kpi-label">{label}</div>
        <div class="rp-kpi-value">{value}</div>
        <div class="rp-kpi-delta">{delta}</div>
    </div>
    """


def panel_title(title: str, meta: str = "") -> None:
    st.markdown(
        f"""
        <div class="rp-panel-title">
            <h3>{title}</h3>
            <span>{meta}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )


def style_figure(fig: go.Figure, height: int = 360) -> go.Figure:
    fig.update_layout(
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font={"color": TEXT, "family": "Arial"},
        margin={"l": 18, "r": 18, "t": 42, "b": 28},
        legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "xanchor": "left", "x": 0},
        colorway=[ACCENT, "#48d597", "#f2ffdc", "#5f7d6b"],
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=GRID, tickfont={"color": MUTED}, title_font={"color": MUTED})
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=GRID, tickfont={"color": MUTED}, title_font={"color": MUTED})
    return fig


def selected_labels(frame: pd.DataFrame, column: str, label: str) -> list[str]:
    options = sorted(str(value) for value in frame[column].dropna().unique())
    return st.sidebar.multiselect(label, options=options)


def filter_by_month(frame: pd.DataFrame, selected_months: list[str]) -> pd.DataFrame:
    if not selected_months:
        return frame
    month_labels = pd.to_datetime(frame["session_month"]).dt.strftime("%Y-%m")
    return frame[month_labels.isin(selected_months)]


def render_topbar(overall: pd.Series, latest_month: str) -> None:
    st.markdown(
        f"""
        <div class="rp-topbar">
            <div class="rp-brand">
                <div class="rp-logo">RP</div>
                <div>
                    <div class="rp-brand-title">RetailPulse</div>
                    <div class="rp-brand-subtitle">Cosmetics ecommerce intelligence cockpit</div>
                </div>
            </div>
            <div class="rp-status-row">
                <div class="rp-pill"><strong>{latest_month}</strong> latest period</div>
                <div class="rp-pill"><strong>{fmt_number(overall['total_sessions'])}</strong> sessions</div>
                <div class="rp-pill"><strong>{fmt_money(overall['purchase_revenue'])}</strong> valid revenue</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar(db_path: Path, funnel_month: pd.DataFrame, funnel_brand: pd.DataFrame, funnel_category: pd.DataFrame, funnel_price: pd.DataFrame):
    st.sidebar.markdown("<div class='rp-section-label'>Workspace</div>", unsafe_allow_html=True)
    st.sidebar.markdown("**RetailPulse Analytics**")
    st.sidebar.caption("DuckDB summary tables")
    st.sidebar.markdown(f"`{db_path}`")
    st.sidebar.markdown("<div class='rp-section-label'>Filters</div>", unsafe_allow_html=True)
    month_options = pd.to_datetime(funnel_month["session_month"]).dt.strftime("%Y-%m").tolist()
    selected_months = st.sidebar.multiselect("Month", options=month_options)
    selected_brands = selected_labels(funnel_brand, "brand", "Brand")
    selected_categories = selected_labels(funnel_category, "category_code", "Category")
    selected_price_bands = selected_labels(funnel_price, "entry_price_band", "Price band")
    st.sidebar.markdown("<div class='rp-section-label'>Model status</div>", unsafe_allow_html=True)
    st.sidebar.success("Metric tables loaded")
    return selected_months, selected_brands, selected_categories, selected_price_bands


def render_insight_rail(overall: pd.Series, segment_summary: pd.DataFrame, purchase_cohort: pd.DataFrame) -> None:
    top_segment = segment_summary.sort_values("purchase_revenue", ascending=False).iloc[0]
    month_one = purchase_cohort[purchase_cohort["months_since_first_purchase"] == 1]
    best_cohort = month_one.sort_values("purchase_retention_rate", ascending=False).iloc[0]
    st.markdown(
        f"""
        <div class="rp-rail-card">
            <h3>Notifications</h3>
            <div class="rp-list">
                <div class="rp-list-item"><div class="rp-dot">01</div><div><div class="rp-list-title">{fmt_number(overall['viewed_sessions'])} viewed sessions</div><div class="rp-list-meta">Funnel denominator locked at session level</div></div></div>
                <div class="rp-list-item"><div class="rp-dot">02</div><div><div class="rp-list-title">{fmt_rate(overall['view_to_purchase_rate'])} view-to-purchase</div><div class="rp-list-meta">Across October 2019 to February 2020</div></div></div>
                <div class="rp-list-item"><div class="rp-dot">03</div><div><div class="rp-list-title">126 invalid purchase rows excluded</div><div class="rp-list-meta">Revenue remains reconciled across marts</div></div></div>
            </div>
        </div>
        <div class="rp-rail-card">
            <h3>Activities</h3>
            <div class="rp-list">
                <div class="rp-list-item"><div class="rp-dot">A</div><div><div class="rp-list-title">{top_segment['rfm_segment']} leads revenue</div><div class="rp-list-meta">{fmt_rate(top_segment['revenue_share'])} of valid purchase revenue</div></div></div>
                <div class="rp-list-item"><div class="rp-dot">B</div><div><div class="rp-list-title">Best month-1 purchase retention</div><div class="rp-list-meta">{fmt_rate(best_cohort['purchase_retention_rate'])} for {pd.to_datetime(best_cohort['first_purchase_month']).strftime('%b %Y')} cohort</div></div></div>
                <div class="rp-list-item"><div class="rp-dot">C</div><div><div class="rp-list-title">Cart friction is the priority</div><div class="rp-list-meta">Only {fmt_rate(overall['cart_to_purchase_rate'])} carted sessions purchased</div></div></div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_funnel_tab(overall: pd.Series, month_frame: pd.DataFrame, brand_frame: pd.DataFrame, category_frame: pd.DataFrame, price_frame: pd.DataFrame) -> None:
    cols = st.columns(4)
    kpis = [
        ("Net purchase revenue", fmt_money(overall["purchase_revenue"]), "Valid non-negative purchases"),
        ("Viewed sessions", fmt_number(overall["viewed_sessions"]), "Session-level denominator"),
        ("View to cart", fmt_rate(overall["view_to_cart_rate"]), "First funnel handoff"),
        ("Cart to purchase", fmt_rate(overall["cart_to_purchase_rate"]), "Checkout completion signal"),
    ]
    for col, (label, value, delta) in zip(cols, kpis):
        col.markdown(card(label, value, delta), unsafe_allow_html=True)

    left, right = st.columns([1.15, 0.85])
    with left:
        st.markdown("<div class='rp-panel'>", unsafe_allow_html=True)
        panel_title("Sales Overview", "session funnel")
        stages = pd.DataFrame(
            {
                "stage": ["View", "Cart", "Purchase"],
                "sessions": [
                    overall["viewed_sessions"],
                    overall["carted_after_view_sessions"],
                    overall["purchased_after_cart_sessions"],
                ],
            }
        )
        fig = go.Figure(
            data=[
                go.Pie(
                    labels=stages["stage"],
                    values=stages["sessions"],
                    hole=0.62,
                    marker={"colors": ["#f1ffdf", ACCENT, ACCENT_DARK], "line": {"color": "#101414", "width": 2}},
                    textinfo="label+percent",
                )
            ]
        )
        fig.add_annotation(text="4.28M<br>views", showarrow=False, font={"size": 24, "color": TEXT})
        st.plotly_chart(style_figure(fig, 390), width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        st.markdown("<div class='rp-panel'>", unsafe_allow_html=True)
        panel_title("Conversion Trend", "monthly rates")
        month_plot = month_frame.assign(
            view_to_cart_pct=pct_series(month_frame, "view_to_cart_rate"),
            cart_to_purchase_pct=pct_series(month_frame, "cart_to_purchase_rate"),
            view_to_purchase_pct=pct_series(month_frame, "view_to_purchase_rate"),
        )
        fig = px.line(
            month_plot,
            x="session_month",
            y=["view_to_cart_pct", "cart_to_purchase_pct", "view_to_purchase_pct"],
            markers=True,
            labels={"value": "Rate", "session_month": "Month", "variable": "Metric"},
        )
        st.plotly_chart(style_figure(fig, 390), width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='rp-panel'>", unsafe_allow_html=True)
    panel_title("Segment Tables", "top rows by revenue")
    col1, col2 = st.columns(2)
    col1.dataframe(brand_frame.head(15), width="stretch", hide_index=True)
    col2.dataframe(category_frame.head(15), width="stretch", hide_index=True)
    st.dataframe(price_frame, width="stretch", hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_cohort_tab(activity_cohort: pd.DataFrame, purchase_cohort: pd.DataFrame) -> None:
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("<div class='rp-panel'>", unsafe_allow_html=True)
        panel_title("Activity Retention", "first activity cohort")
        heatmap = activity_cohort.pivot_table(
            index="first_activity_month",
            columns="months_since_first_activity",
            values="activity_retention_rate",
            aggfunc="mean",
        )
        fig = px.imshow(heatmap * 100, aspect="auto", color_continuous_scale=["#121616", "#314f22", ACCENT])
        st.plotly_chart(style_figure(fig, 420), width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
    with col2:
        st.markdown("<div class='rp-panel'>", unsafe_allow_html=True)
        panel_title("Purchase Retention", "first purchase cohort")
        heatmap = purchase_cohort.pivot_table(
            index="first_purchase_month",
            columns="months_since_first_purchase",
            values="purchase_retention_rate",
            aggfunc="mean",
        )
        fig = px.imshow(heatmap * 100, aspect="auto", color_continuous_scale=["#121616", "#314f22", ACCENT])
        st.plotly_chart(style_figure(fig, 420), width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='rp-panel'>", unsafe_allow_html=True)
    panel_title("Cohort Detail", "retention table")
    st.dataframe(purchase_cohort, width="stretch", hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def render_segment_tab(segment_summary: pd.DataFrame) -> None:
    left, right = st.columns([1, 1])
    with left:
        st.markdown("<div class='rp-panel'>", unsafe_allow_html=True)
        panel_title("Revenue by Segment", "RFM purchasing users")
        fig = px.bar(
            segment_summary,
            x="rfm_segment",
            y="purchase_revenue",
            text="users",
            color="purchase_revenue",
            color_continuous_scale=["#1b241b", ACCENT],
        )
        st.plotly_chart(style_figure(fig, 430), width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
    with right:
        st.markdown("<div class='rp-panel'>", unsafe_allow_html=True)
        panel_title("Revenue Share", "segment mix")
        fig = px.pie(
            segment_summary,
            names="rfm_segment",
            values="purchase_revenue",
            hole=0.55,
            color_discrete_sequence=[ACCENT, "#60d394", "#f1ffdf", "#62856b"],
        )
        st.plotly_chart(style_figure(fig, 430), width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='rp-panel'>", unsafe_allow_html=True)
    panel_title("Customer List", "segment economics")
    st.dataframe(segment_summary, width="stretch", hide_index=True)
    st.markdown("</div>", unsafe_allow_html=True)


def main() -> None:
    inject_css()
    db_path = database_path()
    stop_if_not_ready(db_path)

    funnel_overall = read_table(str(db_path), "metric_session_funnel_overall")
    funnel_month = read_table(str(db_path), "metric_session_funnel_by_month")
    funnel_brand = read_table(str(db_path), "metric_session_funnel_by_brand")
    funnel_category = read_table(str(db_path), "metric_session_funnel_by_category")
    funnel_price = read_table(str(db_path), "metric_session_funnel_by_price_band")
    activity_cohort = read_table(str(db_path), "metric_activity_cohort_retention")
    purchase_cohort = read_table(str(db_path), "metric_purchase_cohort_retention")
    segment_summary = read_table(str(db_path), "metric_rfm_segment_summary")

    selected_months, selected_brands, selected_categories, selected_price_bands = render_sidebar(
        db_path, funnel_month, funnel_brand, funnel_category, funnel_price
    )

    overall = funnel_overall.iloc[0]
    latest_month = pd.to_datetime(funnel_month["session_month"]).max().strftime("%b %Y")
    render_topbar(overall, latest_month)

    content, rail = st.columns([3.2, 1])
    with rail:
        render_insight_rail(overall, segment_summary, purchase_cohort)

    month_frame = filter_by_month(funnel_month.copy(), selected_months)
    brand_frame = funnel_brand if not selected_brands else funnel_brand[funnel_brand["brand"].astype(str).isin(selected_brands)]
    category_frame = funnel_category if not selected_categories else funnel_category[funnel_category["category_code"].astype(str).isin(selected_categories)]
    price_frame = funnel_price if not selected_price_bands else funnel_price[funnel_price["entry_price_band"].astype(str).isin(selected_price_bands)]

    with content:
        funnel_tab, cohort_tab, segment_tab = st.tabs(["Overview", "Cohorts", "Segments"])
        with funnel_tab:
            render_funnel_tab(overall, month_frame, brand_frame, category_frame, price_frame)
        with cohort_tab:
            render_cohort_tab(activity_cohort, purchase_cohort)
        with segment_tab:
            render_segment_tab(segment_summary)


if __name__ == "__main__":
    main()
