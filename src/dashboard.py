import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import pydeck as pdk
import streamlit as st

# Allow `streamlit run src/dashboard.py` from the project root
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import DB_PATH

st.set_page_config(
    page_title="APAC Catastrophe Monitor",
    layout="wide",
    page_icon="🌏",
)

_SEVERITY_COLOR = {
    "red":    [220, 38,  38,  200],
    "orange": [234, 88,  12,  200],
    "green":  [22,  163, 74,  200],
}

_TYPE_COLOR = {
    "earthquake": [234, 88,  12],
    "wildfire":   [220, 38,  38],
    "flood":      [37,  99,  235],
    "storm":      [109, 40,  217],
    "volcano":    [180, 30,  10],
    "cyclone":    [109, 40,  217],
    "tsunami":    [37,  99,  235],
    "drought":    [161, 98,  7],
    "disaster":   [107, 114, 128],
}
_DEFAULT_COLOR = [107, 114, 128, 180]


@st.cache_data(ttl=300)
def load_events() -> pd.DataFrame:
    if not DB_PATH.exists():
        return pd.DataFrame(columns=[
            "id", "source", "event_id", "event_type", "title",
            "lat", "lon", "severity", "magnitude", "country",
            "occurred_at", "fetched_at", "url",
        ])
    conn = sqlite3.connect(DB_PATH)
    df = pd.read_sql("SELECT * FROM events ORDER BY occurred_at DESC", conn)
    conn.close()
    if not df.empty:
        df["occurred_at"] = pd.to_datetime(df["occurred_at"], utc=True, errors="coerce")
    return df


def _event_color(row) -> list[int]:
    if row["severity"] in _SEVERITY_COLOR:
        return _SEVERITY_COLOR[row["severity"]]
    return _TYPE_COLOR.get(row["event_type"], _DEFAULT_COLOR)


def main():
    st.title("🌏 APAC Catastrophe Monitor")
    st.caption("Real-time multi-hazard event tracking for reinsurance cat risk analysis")

    df = load_events()

    if df.empty:
        st.warning("No data yet. Run `python -m src.ingest` to populate the database.")
        st.stop()

    # ── Sidebar filters ────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Filters")

        has_dates = not df["occurred_at"].isna().all()
        min_date = df["occurred_at"].min().date() if has_dates else (datetime.now().date() - timedelta(days=90))
        max_date = df["occurred_at"].max().date() if has_dates else datetime.now().date()
        date_range = st.date_input(
            "Date range",
            value=(max(min_date, datetime.now().date() - timedelta(days=30)), max_date),
            min_value=min_date,
            max_value=max_date,
        )

        all_types = sorted(df["event_type"].dropna().unique().tolist())
        selected_types = st.multiselect("Event type", all_types, default=all_types)

        all_sources = sorted(df["source"].dropna().unique().tolist())
        selected_sources = st.multiselect("Data source", all_sources, default=all_sources)

        min_mag = st.slider("Min earthquake magnitude", 4.0, 9.0, 4.5, 0.1)

        st.markdown("---")
        if st.button("Refresh data cache"):
            st.cache_data.clear()
            st.rerun()

    # ── Apply filters ──────────────────────────────────────────────────────────
    mask = pd.Series(True, index=df.index)
    if len(date_range) == 2:
        start = pd.Timestamp(date_range[0], tz="UTC")
        end   = pd.Timestamp(date_range[1], tz="UTC") + timedelta(days=1)
        mask &= df["occurred_at"].between(start, end, inclusive="left")
    if selected_types:
        mask &= df["event_type"].isin(selected_types)
    if selected_sources:
        mask &= df["source"].isin(selected_sources)
    mask &= df["magnitude"].isna() | (df["magnitude"] >= min_mag)

    filtered = df[mask].copy()

    # ── KPIs ───────────────────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total events", len(filtered))
    c2.metric("Unique countries", int(filtered["country"].nunique()))
    c3.metric("High severity (red)", int((filtered["severity"] == "red").sum()))
    recent = pd.Timestamp.now(tz="UTC") - timedelta(hours=24)
    c4.metric("Last 24 h", int((filtered["occurred_at"] >= recent).sum()))

    st.markdown("---")

    # ── Globe ──────────────────────────────────────────────────────────────────
    map_df = filtered.dropna(subset=["lat", "lon"]).copy()
    if not map_df.empty:
        map_df["color"]   = map_df.apply(_event_color, axis=1)
        map_df["radius"]  = map_df["magnitude"].fillna(5.0).apply(lambda m: max(40_000, m * 18_000))
        map_df["tooltip"] = map_df.apply(
            lambda r: f"{r['title']} | {r['event_type']} | {r['source']}", axis=1
        )
        scatter = pdk.Layer(
            "ScatterplotLayer",
            data=map_df,
            get_position="[lon, lat]",
            get_color="color",
            get_radius="radius",
            pickable=True,
            opacity=0.9,
            stroked=True,
            get_line_color=[255, 255, 255, 20],
            line_width_min_pixels=1,
        )
        deck = pdk.Deck(
            layers=[scatter],
            views=[pdk.View(type="_GlobeView", controller=True)],
            initial_view_state=pdk.ViewState(latitude=10, longitude=115, zoom=1),
            map_provider="carto",
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json",
            tooltip={"text": "{tooltip}\n{occurred_at}"},
            parameters={"cull": True},
        )
        st.pydeck_chart(deck, height=600, use_container_width=True)
    else:
        st.info("No events with coordinates match the current filters.")

    st.markdown("---")

    # ── Charts ─────────────────────────────────────────────────────────────────
    col_l, col_r = st.columns(2)

    with col_l:
        st.subheader("Events over time")
        time_df = (
            filtered.dropna(subset=["occurred_at"])
            .set_index("occurred_at")
            .resample("D")["id"]
            .count()
            .reset_index()
            .rename(columns={"id": "count", "occurred_at": "date"})
        )
        if not time_df.empty:
            fig = px.bar(time_df, x="date", y="count", labels={"count": "Events", "date": "Date"})
            fig.update_layout(margin=dict(t=10, b=10))
            st.plotly_chart(fig, use_container_width=True)

    with col_r:
        st.subheader("Events by type")
        type_counts = filtered["event_type"].value_counts().reset_index()
        type_counts.columns = ["type", "count"]
        if not type_counts.empty:
            fig2 = px.pie(type_counts, names="type", values="count", hole=0.4)
            fig2.update_layout(margin=dict(t=10, b=10))
            st.plotly_chart(fig2, use_container_width=True)

    st.subheader("Top 10 affected countries")
    country_counts = filtered["country"].value_counts().head(10).reset_index()
    country_counts.columns = ["country", "count"]
    if not country_counts.empty:
        fig3 = px.bar(country_counts, x="country", y="count", labels={"count": "Events"})
        fig3.update_layout(margin=dict(t=10, b=10))
        st.plotly_chart(fig3, use_container_width=True)

    # ── Event table + export ───────────────────────────────────────────────────
    st.subheader("Event table")
    display_cols = ["occurred_at", "event_type", "title", "country", "magnitude", "severity", "source"]
    st.dataframe(
        filtered[display_cols].sort_values("occurred_at", ascending=False),
        use_container_width=True,
    )
    st.download_button(
        label="Export CSV",
        data=filtered.to_csv(index=False),
        file_name=f"apac_events_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
        mime="text/csv",
    )


if __name__ == "__main__":
    main()
