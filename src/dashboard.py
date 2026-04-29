import re
import sqlite3
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import plotly.express as px
import pydeck as pdk
import requests
import streamlit as st

sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import DB_PATH
from src.news import PERIL_QUERIES, fetch_news as _fetch_news

st.set_page_config(
    page_title="Global Catastrophe Monitor",
    layout="wide",
    page_icon="🌍",
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

# Maps raw event_type values to PERIL_QUERIES keys
_EVENT_TYPE_TO_PERIL = {
    "earthquake": "Earthquake",
    "eq":         "Earthquake",
    "cyclone":    "Cyclone / Typhoon",
    "tc":         "Cyclone / Typhoon",
    "storm":      "Cyclone / Typhoon",
    "wildfire":   "Wildfire",
    "wf":         "Wildfire",
    "flood":      "Flood",
    "fl":         "Flood",
    "volcano":    "Volcano",
    "drought":    "Drought",
    "dr":         "Drought",
}


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


@st.cache_data(ttl=1800)
def cached_news(query: str) -> list[dict]:
    return _fetch_news(query)


@st.cache_data(ttl=86400)
def _reverse_geocode(lat: float, lon: float) -> str:
    """Return 'State/Province, Country' for a lat/lon, cached for 24 h."""
    try:
        r = requests.get(
            "https://nominatim.openstreetmap.org/reverse",
            params={"lat": lat, "lon": lon, "format": "json"},
            headers={"User-Agent": "apac-catastrophe-monitor/1.0"},
            timeout=5,
        )
        addr = r.json().get("address", {})
        state   = addr.get("state") or addr.get("region") or addr.get("county") or ""
        country = addr.get("country") or ""
        return ", ".join(p for p in [state, country] if p)
    except Exception:
        return ""


def _event_color(row) -> list[int]:
    if row["severity"] in _SEVERITY_COLOR:
        return _SEVERITY_COLOR[row["severity"]]
    return _TYPE_COLOR.get(row["event_type"], _DEFAULT_COLOR)


def render_live_events(df: pd.DataFrame):
    # ── Sidebar filters ────────────────────────────────────────────────────────
    with st.sidebar:
        st.header("Filters")

        has_dates = not df["occurred_at"].isna().all()
        min_date = df["occurred_at"].min().date() if has_dates else (datetime.now().date() - timedelta(days=90))
        max_date = df["occurred_at"].max().date() if has_dates else datetime.now().date()
        date_range = st.date_input(
            "Date range",
            value=(min_date, max_date),
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
    mask &= ~(df["source"] == "usgs") | df["magnitude"].isna() | (df["magnitude"] >= min_mag)

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
        layers = []

        cyc_df = map_df[map_df["source"] == "ibtracs"].copy()
        if not cyc_df.empty:
            cyc_df["storm_id"] = cyc_df["event_id"].str.split("|").str[0]
            tracks = []
            for sid, grp in cyc_df.sort_values("occurred_at").groupby("storm_id"):
                coords = grp[["lon", "lat"]].values.tolist()
                if len(coords) < 2:
                    continue
                peak_sev = next(
                    (s for s in ("red", "orange", "green") if s in grp["severity"].values),
                    "green",
                )
                color = _SEVERITY_COLOR.get(peak_sev, [255, 200, 0, 200])
                name = grp["title"].iloc[0].replace("Tropical Cyclone ", "")
                wind_vals = grp["magnitude"].dropna()
                peak_wind = f"{int(wind_vals.max())} kt" if not wind_vals.empty else "?"
                tracks.append({
                    "path":        coords,
                    "event_type":  "cyclone",
                    "tooltip":     f"Cyclone {name} | peak {peak_wind} | {peak_sev} alert",
                    "occurred_at": f"{str(grp['occurred_at'].min())[:10]} → {str(grp['occurred_at'].max())[:10]}",
                    "color":       color,
                })
            if tracks:
                layers.append(pdk.Layer(
                    "PathLayer",
                    id="tracks",
                    data=tracks,
                    get_path="path",
                    get_color="color",
                    get_width=10_000,
                    width_min_pixels=2,
                    width_max_pixels=6,
                    pickable=True,
                    opacity=0.85,
                ))

        other_df = map_df[map_df["source"] != "ibtracs"].copy()
        if not other_df.empty:
            other_df["color"]    = other_df.apply(_event_color, axis=1)
            other_df["radius"]   = other_df["magnitude"].fillna(5.0).apply(
                lambda m: max(10_000, m * 5_000)
            )
            other_df["tooltip"]  = other_df.apply(
                lambda r: f"{r['title']} | {r['event_type']} | {r['source']}", axis=1
            )
            other_df["occurred_at"] = other_df["occurred_at"].astype(str)
            layers.append(pdk.Layer(
                "ScatterplotLayer",
                id="events",
                data=other_df,
                get_position="[lon, lat]",
                get_color="color",
                get_radius="radius",
                radius_min_pixels=3,
                radius_max_pixels=12,
                pickable=True,
                opacity=0.9,
                stroked=True,
                get_line_color=[255, 255, 255, 20],
                line_width_min_pixels=1,
            ))

        deck = pdk.Deck(
            layers=layers,
            views=[pdk.View(type="_GlobeView", controller=True)],
            initial_view_state=pdk.ViewState(latitude=10, longitude=150, zoom=1),
            map_provider="carto",
            map_style="https://basemaps.cartocdn.com/gl/dark-matter-nolabels-gl-style/style.json",
            tooltip={"text": "{tooltip}\n{occurred_at}"},
            parameters={"cull": True},
        )
        chart_event = st.pydeck_chart(
            deck, height=600, use_container_width=True,
            on_select="rerun", selection_mode="single-object",
        )

        # ── Click-to-news panel ────────────────────────────────────────────
        selected = None
        sel_objects = getattr(getattr(chart_event, "selection", None), "objects", None) or {}
        for layer_hits in sel_objects.values():
            if layer_hits:
                selected = layer_hits[0]
                break

        if selected:
            event_type = selected.get("event_type", "")
            tooltip    = selected.get("tooltip", event_type)
            occurred   = selected.get("occurred_at", "")
            title      = selected.get("title", "") or ""
            country    = selected.get("country", "") or ""
            lat        = selected.get("lat")
            lon        = selected.get("lon")

            # Reverse-geocode lat/lon → specific region, e.g. "Madhya Pradesh, India"
            geo_location = ""
            if lat is not None and lon is not None:
                try:
                    geo_location = _reverse_geocode(
                        round(float(lat), 1), round(float(lon), 1)
                    )
                except Exception:
                    pass

            # Month/year context makes queries much more specific
            date_ctx = ""
            try:
                dt = pd.Timestamp(str(occurred).split("→")[0].strip())
                date_ctx = dt.strftime("%B %Y")
            except Exception:
                pass

            # Build location + date specific query
            if title:
                clean = re.sub(r"\s+\d{6,}$", "", title).strip() or title
                # EONET titles end with "in [Country]" — replace with precise region
                generic_loc = re.search(r"\s+in\s+(\w+)\s*$", clean, re.IGNORECASE)
                if generic_loc and geo_location:
                    base = clean[: generic_loc.start()].strip()
                    news_query = f"{base} {geo_location} {date_ctx}".strip()
                else:
                    news_query = f"{clean} {date_ctx}".strip()
            elif event_type == "cyclone":
                storm_name = tooltip.split("|")[0].strip()
                news_query = f"{storm_name} {date_ctx}".strip()
            elif geo_location:
                news_query = f"{event_type} {geo_location} {date_ctx}".strip()
            elif country:
                news_query = f"{event_type} {country} {date_ctx}".strip()
            else:
                news_query = PERIL_QUERIES.get(
                    _EVENT_TYPE_TO_PERIL.get(event_type, "All Perils"),
                    event_type,
                )

            st.markdown("---")
            with st.container(border=True):
                st.markdown(f"**{tooltip}**")
                if occurred:
                    st.caption(occurred)
                st.markdown(f"**Related news — {news_query}**")
                with st.spinner("Fetching news…"):
                    articles = cached_news(news_query)
                for article in articles[:6]:
                    src_date = " · ".join(p for p in [article["source"], article["published"]] if p)
                    st.markdown(f"- [{article['title']}]({article['link']})")
                    if src_date:
                        st.caption(f"  {src_date}")
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


def render_news():
    st.subheader("Global Peril News Feed")
    st.caption("Live headlines from Google News — refreshed every 30 minutes")

    # ── Peril toggle ───────────────────────────────────────────────────────────
    selected_peril = st.radio(
        "Select peril",
        list(PERIL_QUERIES.keys()),
        horizontal=True,
        label_visibility="collapsed",
    )

    col_btn, col_note = st.columns([1, 6])
    with col_btn:
        if st.button("Refresh news"):
            st.cache_data.clear()
            st.rerun()
    with col_note:
        st.caption("News cached for 30 min. Click refresh to fetch latest.")

    st.markdown("---")

    # ── Fetch and display ──────────────────────────────────────────────────────
    with st.spinner(f"Fetching {selected_peril} news…"):
        articles = cached_news(PERIL_QUERIES[selected_peril])

    if not articles:
        st.info("No articles found. Try refreshing or selecting a different peril.")
        return

    for article in articles:
        with st.container(border=True):
            st.markdown(f"#### [{article['title']}]({article['link']})")
            meta_parts = [p for p in [article["source"], article["published"]] if p]
            if meta_parts:
                st.caption(" · ".join(meta_parts))
            if article["summary"]:
                st.write(article["summary"])


def main():
    st.title("🌍 Global Catastrophe Monitor")
    st.caption("Real-time multi-hazard event tracking for global cat risk analysis")

    df = load_events()

    if df.empty:
        st.warning("No data yet. Run `python -m src.ingest` to populate the database.  "
                   "For earthquake history run `python -m src.backfill`.")
        st.stop()

    tab1, tab2 = st.tabs(["🌍 Live Events", "📰 News Feed"])

    with tab1:
        render_live_events(df)

    with tab2:
        render_news()


if __name__ == "__main__":
    main()
