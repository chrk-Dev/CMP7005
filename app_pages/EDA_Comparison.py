import streamlit as st
import pandas as pd
import plotly.express as px
from app_pages.utils import get_location_col

# ----------------------------------------------------------
# PASTEL CSS
# ----------------------------------------------------------
st.markdown("""
<style>
.section-box {
    background-color: #F8FAFF;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #E0E7FF;
    margin-bottom: 20px;
}

.plot-container {
    border-radius: 15px;
    padding: 12px;
    background: #ffffff;
    box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
}
</style>
""", unsafe_allow_html=True)


def show():

    # ----------------------------------------------------------
    # LOAD DATA
    # ----------------------------------------------------------
    if "cleaned_df" in st.session_state:
        df = st.session_state.cleaned_df
    elif "current_df" in st.session_state:
        df = st.session_state.current_df
    else:
        df = st.session_state.original_df

    if df is None:
        st.error("Dataset not found.")
        return

    st.header("🔍 Comparison Tool")
    location_col = get_location_col(df)

    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    elif all(col in df.columns for col in ["year", "month", "day"]):
        if "hour" in df.columns:
            df["Date"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
        else:
            df["Date"] = pd.to_datetime(df[["year", "month", "day"]])

    # ----------------------------------------------------------
    # CLEAN POLLUTANT DETECTION (ONLY pollutants)
    # ----------------------------------------------------------
    exclude_cols = {
        "City", "Date",
        "AQI", "AQI_Bucket", "AQI_Recalc", "AQI_Bucket_Recalc",
        "Year", "Month", "Month_Name", "Day", "Week_Number" , "Month_Number","AQI_recalc","AQI_Bucket_recalc"
    }

    pollutant_cols = [
        c for c in df.columns
        if pd.api.types.is_numeric_dtype(df[c]) and c not in exclude_cols
    ]

    # ----------------------------------------------------------
    # FILTER PANEL
    # ----------------------------------------------------------
    st.markdown('<div class="section-box">', unsafe_allow_html=True)

    # POLLUTANT DROPDOWN (only pollutants + ALL)
    pollutant_options = ["ALL"] + pollutant_cols

    selected_pollutants = st.multiselect(
        "Select Pollutants to Compare",
        pollutant_options,
        default=None
    )

    if "ALL" in selected_pollutants:
        pollutants = pollutant_cols
    else:
        pollutants = selected_pollutants

    # CITY DROPDOWN
    cities = st.multiselect(
        "Select Cities to Compare",
        sorted(df[location_col].dropna().unique()),
        default=None
    )

    # PERIOD
    period = st.selectbox(
        "Select Time Basis for Pie Chart",
        ["Yearly", "Monthly"]
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------------------
    # APPLY FILTERS
    # ----------------------------------------------------------
    filtered_df = df.copy()

    if cities:
        filtered_df = filtered_df[filtered_df[location_col].isin(cities)]

    if filtered_df.empty:
        st.warning("No data matches filters.")
        return

    # ----------------------------------------------------------
    # REMOVED: Time series graph
    # ----------------------------------------------------------

    # ----------------------------------------------------------
    # PIE CHART SECTION — FIXED
    # ----------------------------------------------------------
    st.subheader("🥧 Pollutant Distribution (Pie Charts)")

    st.markdown('<div class="plot-container">', unsafe_allow_html=True)

    if pollutants and cities:

        for city in cities:
            st.markdown(f"### 🌆 {city}")

            city_df = filtered_df[filtered_df[location_col] == city].copy()

            # GROUPING
            if period == "Yearly":
                grouped = city_df.groupby(city_df["Date"].dt.year)[pollutants].mean()
                grouped.index.name = "Group"
                title_suffix = "Yearly Average"

            else:  # Monthly
                grouped = city_df.groupby(city_df["Date"].dt.strftime("%B"))[pollutants].mean()
                grouped.index.name = "Group"
                title_suffix = "Monthly Average"

            # Melt
            melted = grouped.reset_index().melt(
                id_vars="Group",
                value_vars=pollutants,
                var_name="Pollutant",
                value_name="Value"
            )

            if melted["Value"].isna().all():
                st.info(f"No valid pollutant data available for {city}.")
                continue

            fig = px.pie(
                melted,
                names="Pollutant",
                values="Value",
                title=f"{city} — {title_suffix} Pollutant Share",
                color_discrete_sequence=px.colors.qualitative.Pastel
            )

            st.plotly_chart(fig, use_container_width=True)
            st.markdown("---")

    else:
        st.info("Select pollutants and cities to generate pie charts.")

    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------------------
    # CITY-WISE AVERAGE BAR CHART
    # ----------------------------------------------------------
    st.subheader("🏙 Average Pollutant Comparison (City-wise)")

    st.markdown('<div class="plot-container">', unsafe_allow_html=True)

    if pollutants and cities:
        avg_city = filtered_df.groupby(location_col)[pollutants].mean().reset_index()

        avg_city_melt = avg_city.melt(
            id_vars=location_col,
            value_vars=pollutants,
            var_name="Pollutant",
            value_name="Average Value"
        )

        fig_city = px.bar(
            avg_city_melt,
            x=location_col,
            y="Average Value",
            color="Pollutant",
            barmode="group",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            title="Average Pollutant Levels (City-wise)"
        )

        st.plotly_chart(fig_city, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------------------
    # OVERALL POLLUTANT BAR
    # ----------------------------------------------------------
    st.subheader("🔢 Pollutant-wise Comparison (Overall)")

    st.markdown('<div class="plot-container">', unsafe_allow_html=True)

    if pollutants:
        overall_avg = filtered_df[pollutants].mean().reset_index()
        overall_avg.columns = ["Pollutant", "Average Value"]

        fig_poll = px.bar(
            overall_avg,
            x="Pollutant",
            y="Average Value",
            color="Pollutant",
            color_discrete_sequence=px.colors.qualitative.Pastel,
            title="Average Values of Selected Pollutants"
        )

        st.plotly_chart(fig_poll, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------------------
    # RAW DATA
    # ----------------------------------------------------------
    with st.expander("📄 View Filtered Data"):
        st.dataframe(filtered_df, use_container_width=True)

