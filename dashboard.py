import pandas as pd
import streamlit as st

from src import analysis
from src.data_loader import load_dataset
from src.preprocessing import parse_datetime_series
from src.reporting import data_quality_summary, feature_severity_lift, top_cities_table


st.set_page_config(page_title="US Road Accidents Dashboard", layout="wide")


@st.cache_data(show_spinner=False)
def load_analysis_data(use_sample: bool) -> pd.DataFrame:
    return analysis.ensure_features(load_dataset(use_sample=use_sample))


st.title("US Road Accidents Dashboard")
st.caption("Interactive portfolio dashboard for the road accidents analysis pipeline.")

with st.sidebar:
    st.header("Filters")
    use_sample = st.toggle("Use bundled sample", value=True)

df = load_analysis_data(use_sample)
years = parse_datetime_series(df["Start_Time"]).dt.year
year_min, year_max = int(years.min()), int(years.max())

with st.sidebar:
    selected_years = st.slider("Year range", year_min, year_max, (year_min, year_max))
    severity_values = sorted(pd.to_numeric(df["Severity"], errors="coerce").dropna().astype(int).unique())
    selected_severity = st.multiselect("Severity", severity_values, default=severity_values)
    city_options = ["All"] + top_cities_table(df, n=25)["city"].tolist()
    selected_city = st.selectbox("City", city_options)

mask = years.between(selected_years[0], selected_years[1])
mask &= pd.to_numeric(df["Severity"], errors="coerce").isin(selected_severity)
if selected_city != "All":
    mask &= df["City"].astype(str).str.title().eq(selected_city)
filtered = df.loc[mask].copy()

severe_share = filtered["is_severe"].mean() * 100 if len(filtered) else 0
top_city = top_cities_table(filtered, n=1)["city"].iloc[0] if len(filtered) else "N/A"

metric_cols = st.columns(4)
metric_cols[0].metric("Rows", f"{len(filtered):,}")
metric_cols[1].metric("High-severity share", f"{severe_share:.1f}%")
metric_cols[2].metric("Cities", f"{filtered['City'].nunique():,}")
metric_cols[3].metric("Top city", top_city)

tab_overview, tab_time, tab_geo, tab_quality = st.tabs(
    ["Overview", "Time patterns", "Map", "Data quality"]
)

with tab_overview:
    left, right = st.columns([1.1, 0.9])
    with left:
        yearly = analysis.kpi_by_year_all(filtered)
        st.subheader("Yearly KPIs")
        st.dataframe(yearly, use_container_width=True, hide_index=True)
        if not yearly.empty:
            st.line_chart(yearly.set_index("year")[["accidents", "severe_share"]])
    with right:
        st.subheader("Top cities")
        cities = top_cities_table(filtered, n=10)
        st.bar_chart(cities.set_index("city"))

    st.subheader("High-severity lift by context")
    lift = feature_severity_lift(filtered)
    st.dataframe(lift.head(20), use_container_width=True, hide_index=True)

with tab_time:
    tmp = filtered.copy()
    dt = parse_datetime_series(tmp["Start_Time"])
    tmp["hour"] = dt.dt.hour
    tmp["day"] = dt.dt.day_name()
    st.subheader("Accidents by hour")
    st.bar_chart(tmp.groupby("hour").size())
    st.subheader("Accidents by day of week")
    day_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    st.bar_chart(tmp.groupby("day").size().reindex(day_order).fillna(0))

with tab_geo:
    st.subheader("Accident locations")
    if {"Start_Lat", "Start_Lng"}.issubset(filtered.columns):
        map_df = filtered[["Start_Lat", "Start_Lng"]].rename(
            columns={"Start_Lat": "lat", "Start_Lng": "lon"}
        ).dropna()
        if len(map_df) > 100_000:
            map_df = map_df.sample(100_000, random_state=42)
            st.caption("Map is sampled to 100,000 rows for browser performance.")
        st.map(map_df.dropna(), size=8)
    else:
        st.info("Latitude and longitude columns are not available in this dataset.")

with tab_quality:
    st.subheader("Data quality summary")
    st.dataframe(data_quality_summary(filtered), use_container_width=True, hide_index=True)
