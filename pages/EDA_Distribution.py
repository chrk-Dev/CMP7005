import streamlit as st
import plotly.express as px
import pandas as pd
import numpy as np
from pages.utils import get_location_col, get_aqi_col, get_aqi_bucket_col, get_pollutant_columns


def show():
    st.title("📈 Distribution Analysis")
    st.write("Explore how pollutants vary across cities, seasons, and AQI categories.")

    # Load dataset
    df = None
    if "cleaned_df" in st.session_state:
        df = st.session_state.cleaned_df
    elif "current_df" in st.session_state:
        df = st.session_state.current_df
    else:
        df = st.session_state.original_df

    df["Date"] = pd.to_datetime(df["Date"])
    df["Month"] = df["Date"].dt.month
    df["Season"] = df["Month"].map({
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Summer", 4: "Summer", 5: "Summer",
        6: "Monsoon", 7: "Monsoon", 8: "Monsoon",
        9: "Post-Monsoon", 10: "Post-Monsoon", 11: "Post-Monsoon"
    })

    pollutants = get_pollutant_columns(df)
    location_col = get_location_col(df)
    aqi_col = get_aqi_col(df)
    aqi_bucket_col = get_aqi_bucket_col(df)

    # ----------------------------------------------------------
    # 1️⃣ SELECT POLLUTANT + OPTIONS
    # ----------------------------------------------------------
    st.subheader("1️⃣ Select Pollutant")

    col1, col2, col3 = st.columns(3)

    with col1:
        pollutant = st.selectbox("Choose pollutant:", pollutants)

    with col2:
        remove_outliers = st.checkbox("Remove top 1% outliers", value=False)

    with col3:
        log_scale = st.checkbox("Use log scale", value=False)

    data = df[pollutant].copy()

    if remove_outliers:
        threshold = data.quantile(0.99)
        data = data[data <= threshold]

    st.markdown("---")

    # ----------------------------------------------------------
    # 2️⃣ OVERALL DISTRIBUTION (Histogram + KDE)
    # ----------------------------------------------------------
    st.subheader("2️⃣ Overall Distribution")

    fig_hist = px.histogram(
        data,
        nbins=50,
        marginal="box",
        title=f"Distribution of {pollutant}"
    )
    if log_scale:
        fig_hist.update_layout(yaxis_type="log", xaxis_type="log")

    st.plotly_chart(fig_hist, use_container_width=True)

    # Summary Statistics
    st.write("### 📌 Summary Statistics")
    st.write(data.describe())

    st.markdown("---")

    # ----------------------------------------------------------
    # 3️⃣ DISTRIBUTION ACROSS CITIES
    # ----------------------------------------------------------
    st.subheader("3️⃣ How does this pollutant vary across cities?")

    top_n = st.slider("Show top N cities by average pollutant level:", 5, 28, 10)

    city_avg = df.groupby(location_col)[pollutant].mean().sort_values(ascending=False).head(top_n)
    df_city_filtered = df[df[location_col].isin(city_avg.index)]

    fig_violin = px.violin(
        df_city_filtered,
        x=location_col,
        y=pollutant,
        box=True,
        points="suspectedoutliers",
        title=f"City-wise distribution of {pollutant}"
    )
    fig_violin.update_layout(xaxis_tickangle=45, height=500)

    st.plotly_chart(fig_violin, use_container_width=True)

    st.markdown("---")

    # ----------------------------------------------------------
    # 4️⃣ SEASONAL DISTRIBUTION
    # ----------------------------------------------------------
    st.subheader("4️⃣ Seasonal Distribution")

    fig_season = px.box(
        df,
        x="Season",
        y=pollutant,
        color="Season",
        title=f"Seasonal variation of {pollutant}"
    )
    st.plotly_chart(fig_season, use_container_width=True)

    st.markdown("---")

    # ----------------------------------------------------------
    # 5️⃣ POLLUTANT RELATION WITH AQI
    # ----------------------------------------------------------
    st.subheader("5️⃣ Relationship with AQI")
    
    if not aqi_col:
        st.warning("AQI column is missing in this dataset.")
        return
    
    fig_relation = px.scatter(
        df,
        x=pollutant,
        y=aqi_col,
        color=aqi_bucket_col if aqi_bucket_col else None,
        title=f"{pollutant} vs AQI"
    )
    
    st.plotly_chart(fig_relation, use_container_width=True)
