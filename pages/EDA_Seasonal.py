import streamlit as st
import pandas as pd
import plotly.express as px
from pages.utils import get_location_col

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


# ----------------------------------------------------------
# MAIN FUNCTION
# ----------------------------------------------------------
def show():

    # Load dataset
    df = None
    if "cleaned_df" in st.session_state:
        df = st.session_state.cleaned_df
    elif "current_df" in st.session_state:
        df = st.session_state.current_df
    else:
        df = st.session_state.original_df

    if df is None:
        st.error("Dataset not available.")
        return

    st.header("🍂 Seasonal Patterns Analysis")
    location_col = get_location_col(df)

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Month"] = df["Date"].dt.month
    df["Month_Name"] = df["Date"].dt.strftime("%B")

    # Define seasons (Indian standard)
    seasons = {
        "Winter": [12, 1, 2],
        "Summer": [3, 4, 5],
        "Monsoon": [6, 7, 8],
        "Post-Monsoon": [9, 10, 11]
    }

    def get_season(month):
        for season, months in seasons.items():
            if month in months:
                return season
        return None

    df["Season"] = df["Month"].apply(get_season)

    # ----------------------------------------------------------
    # DETECT POLLUTANTS
    # ----------------------------------------------------------
    exclude = {"AQI", "AQI_Bucket", "AQI_Recalc", "AQI_Bucket_Recalc", "City"}
    pollutant_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c]) and c not in exclude]

    # ----------------------------------------------------------
    # FILTER PANEL
    # ----------------------------------------------------------
    st.markdown('<div class="section-box">', unsafe_allow_html=True)

    col1, col2, col3 = st.columns(3)

    with col1:
        pollutant = st.selectbox("Select Pollutant", pollutant_cols)

    with col2:
        cities = st.multiselect(
            "Filter by City (optional)",
            sorted(df[location_col].dropna().unique())
        )

    with col3:
        date_range = st.date_input(
            "Date Range",
            (df["Date"].min(), df["Date"].max())
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------------------
    # APPLY FILTERS
    # ----------------------------------------------------------
    filtered_df = df.copy()

    start, end = date_range
    filtered_df = filtered_df[
        (filtered_df["Date"] >= pd.to_datetime(start)) &
        (filtered_df["Date"] <= pd.to_datetime(end))
    ]

    if cities:
        filtered_df = filtered_df[filtered_df[location_col].isin(cities)]

    if filtered_df.empty:
        st.warning("No data available for selected filters.")
        return

    # ----------------------------------------------------------
    # MONTHLY AVERAGE TREND
    # ----------------------------------------------------------
    st.subheader("📅 Monthly Average Pattern")

    st.markdown('<div class="plot-container">', unsafe_allow_html=True)

    monthly_avg = filtered_df.groupby("Month_Name")[pollutant].mean().reset_index()
    monthly_avg = monthly_avg.set_index("Month_Name").reindex(
        ["January", "February", "March", "April", "May", "June",
         "July", "August", "September", "October", "November", "December"]
    ).reset_index()

    fig1 = px.line(
        monthly_avg,
        x="Month_Name",
        y=pollutant,
        markers=True,
        title=f"Monthly Average of {pollutant}",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )
    fig1.update_layout(xaxis_title="Month", yaxis_title=pollutant)

    st.plotly_chart(fig1, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------------------
    # SEASON-WISE BOX PLOT
    # ----------------------------------------------------------
    st.subheader("🌤 Season-wise Distribution")

    st.markdown('<div class="plot-container">', unsafe_allow_html=True)

    fig2 = px.box(
        filtered_df,
        x="Season",
        y=pollutant,
        title=f"{pollutant} Distribution Across Seasons",
        color="Season",
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    st.plotly_chart(fig2, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------------------
    # HEATMAP: Avg Pollutant per Month
    # ----------------------------------------------------------
    st.subheader("🔥 Monthly Heatmap")

    st.markdown('<div class="plot-container">', unsafe_allow_html=True)

    heat_df = filtered_df.groupby(["Month_Name"])[pollutant].mean().reset_index()
    heat_df = heat_df.set_index("Month_Name")

    fig3 = px.imshow(
        heat_df.T,
        color_continuous_scale=px.colors.sequential.Blues,
        aspect="auto",
        text_auto=True,
        title=f"Monthly Heatmap of {pollutant}"
    )

    st.plotly_chart(fig3, use_container_width=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # ----------------------------------------------------------
    # RAW DATA VIEWER
    # ----------------------------------------------------------
    with st.expander("📄 View Filtered Seasonal Data"):
        st.dataframe(filtered_df, use_container_width=True)
