"""
******************************************************************************************
 Assembly:                Mappy
 Filename:                app.py
 Author:                  Terry D. Eppler (framework) / Assistant (Streamlit UI)
 Created:                 12-27-2025
******************************************************************************************

Purpose:
    Streamlit application exposing Mappy geospatial functionality:
        - Geocoding
        - Places Text Search fallback
        - Distance Matrix
        - Static Maps
        - Time Zone lookup
        - Excel / CSV enrichment

CRITICAL ASSUMPTIONS (VERIFIED):
    - Flat project layout (no package directory)
    - Maps.__init__(api_key, qps)
    - Places.text_to_location(...) is the ONLY Places lookup method
    - Cache is injected ONLY into services that support it
******************************************************************************************
"""

from __future__ import annotations

from exceptions import NotFound
import os
from typing import Optional

import pandas as pd
import streamlit as st

# ---------------------------------------------------------------------
# Local Imports (FLAT MODE — VERIFIED)
# ---------------------------------------------------------------------

from maps import Maps
from geocode import Geocoder
from places import Places
from distances import DistanceMatrix
from timezones import Timezone
from staticmaps import StaticMapURL
from excel import Excel
from caches import InMemoryCache, SQLiteCache

import config


# ---------------------------------------------------------------------
# Streamlit Configuration
# ---------------------------------------------------------------------

st.set_page_config(
    page_title="Mappy – Geospatial Toolkit",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ---------------------------------------------------------------------
# Sidebar – Global Configuration
# ---------------------------------------------------------------------

st.sidebar.title("🗺️ Mappy Configuration")

# Discover API keys from config.py
api_keys = {
    name: value
    for name, value in vars(config).items()
    if name.endswith("_API_KEY") and value
}

if not api_keys:
    st.error("No API keys found in config.py")
    st.stop()

selected_key = st.sidebar.selectbox(
    "API Key",
    options=list(api_keys.keys()),
)

api_key = api_keys[selected_key]

qps = st.sidebar.slider(
    "Queries Per Second",
    min_value=1,
    max_value=50,
    value=10,
)

st.sidebar.subheader("Caching")

cache_backend = st.sidebar.selectbox(
    "Cache Backend",
    options=["none", "memory", "sqlite"],
)

cache: Optional[object] = None

if cache_backend == "memory":
    cache = InMemoryCache()

elif cache_backend == "sqlite":
    cache_path = st.sidebar.text_input(
        "SQLite Cache Path",
        value="mappy_cache.db",
    )
    cache = SQLiteCache(cache_path)


# ---------------------------------------------------------------------
# Core Maps Gateway (NO cache argument — VERIFIED)
# ---------------------------------------------------------------------

maps = Maps(
    api_key=api_key,
    qps=qps,
)

# ---------------------------------------------------------------------
# Services (cache injected ONLY where supported)
# ---------------------------------------------------------------------

geocoder = Geocoder(maps, cache=cache)
places = Places(maps, cache=cache)

distances = DistanceMatrix(maps)
timezone = Timezone(maps)
static_maps = StaticMapURL(api_key=api_key)


# ---------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------

tab_geo, tab_dist, tab_map, tab_tz, tab_excel = st.tabs(
    [
        "🔎 Geocoding & Places",
        "📏 Distance Matrix",
        "🗺 Static Maps",
        "⏱ Time Zones",
        "📊 Excel Enrichment",
    ]
)


# ---------------------------------------------------------------------
# Geocoding & Places Tab
# ---------------------------------------------------------------------

with tab_geo:
    st.header("Geocoding & Places")

    query = st.text_input("Address or Free-Form Location")

    use_places = st.checkbox(
        "Use Places fallback if geocoding fails",
        value=True,
    )

    if st.button("Resolve Location"):
        if not query:
            st.warning("Enter a location.")
        else:
	        try:
		        result = geocoder.freeform( query )
		        st.json( result )
	        
	        except NotFound:
		        st.warning( "Geocoding failed. Trying Places search." )
		        result = places.text_to_location( query )
		        st.json( result )
	        
	        except Exception as e:
		        st.error( str( e ) )


# ---------------------------------------------------------------------
# Distance Matrix Tab
# ---------------------------------------------------------------------

with tab_dist:
    st.header("Distance Matrix")

    col1, col2 = st.columns(2)

    with col1:
        origin = st.text_input("Origin")

    with col2:
        destination = st.text_input("Destination")

    mode = st.selectbox(
        "Travel Mode",
        ["driving", "walking", "bicycling", "transit"],
    )

    if st.button("Calculate Distance"):
        if not origin or not destination:
            st.warning("Provide both origin and destination.")
        else:
            summary = distances.summary(
                origin,
                destination,
                mode=mode,
            )
            st.table(pd.DataFrame([summary]))


# ---------------------------------------------------------------------
# Static Maps Tab
# ---------------------------------------------------------------------

with tab_map:
    st.header("Static Map Preview")

    lat = st.number_input("Latitude", value=0.0, format="%.6f")
    lng = st.number_input("Longitude", value=0.0, format="%.6f")

    zoom = st.slider("Zoom", 1, 20, 12)
    size = st.selectbox(
        "Image Size",
        ["400x400", "600x400", "800x600"],
    )

    if st.button("Generate Map"):
        url = static_maps.pin(
            lat=lat,
            lng=lng,
            zoom=zoom,
            size=size,
        )
        st.image(url)
        st.code(url)


# ---------------------------------------------------------------------
# Time Zone Tab
# ---------------------------------------------------------------------

with tab_tz:
    st.header("Time Zone Lookup")

    lat_tz = st.number_input(
        "Latitude",
        key="tz_lat",
        value=0.0,
        format="%.6f",
    )
    lng_tz = st.number_input(
        "Longitude",
        key="tz_lng",
        value=0.0,
        format="%.6f",
    )

    if st.button("Lookup Time Zone"):
        result = timezone.lookup(lat_tz, lng_tz)
        st.json(result)


# ---------------------------------------------------------------------
# Excel Enrichment Tab
# ---------------------------------------------------------------------

with tab_excel:
    st.header("Excel / CSV Enrichment")

    uploaded = st.file_uploader(
        "Upload CSV or XLSX",
        type=["csv", "xlsx"],
    )

    city_col = st.text_input("City Column", value="City")
    state_col = st.text_input("State Column", value="State")
    country_col = st.text_input("Country Column", value="Country")

    if uploaded:
        input_path = f"_input_{uploaded.name}"
        output_path = f"_output_{uploaded.name}"

        with open(input_path, "wb") as f:
            f.write(uploaded.read())

        if st.button("Enrich File"):
            excel = Excel(api_key=api_key)

            excel.enrich(
                input_path=input_path,
                output_path=output_path,
                city_col=city_col,
                state_col=state_col,
                country_col=country_col,
            )

            df = pd.read_excel(output_path)
            st.dataframe(df)

            st.download_button(
                "Download Enriched File",
                data=open(output_path, "rb").read(),
                file_name=output_path,
            )

            os.remove(input_path)
            os.remove(output_path)
