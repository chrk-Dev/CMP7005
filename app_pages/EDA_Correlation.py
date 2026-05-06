import streamlit as st
import pandas as pd
import plotly.express as px
from app_pages.utils import get_location_col

# ----------------------------------------------------------
# Pastel CSS
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

h3 {
    color: #344767;
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
    elif "original_df" in st.session_state:
        df = st.session_state.original_df

    if df is None:
        st.error("Dataset not available.")
        return

    st.header("🔗 Correlation Matrix (Pollutants Only)")

    # ----------------------------------------------------------
    # Identify only pollutant columns (numeric)
    # ----------------------------------------------------------
    location_col = get_location_col(df)
    exclude = {
        "City", "station",
        "Date",
        "AQI",
        "AQI_Bucket",
        "AQI_Recalc",
        "AQI_Bucket_Recalc",
        "Year",
        "Month",
        "Month_Number",
        "Month_Name",
        "Day",
        "Week_Number",
        "AQI_recalc",
        "AQI_Bucket_recalc"
    }

    pollutant_cols = [
        c for c in df.columns
        if c not in exclude and pd.api.types.is_numeric_dtype(df[c])
    ]

    if len(pollutant_cols) < 2:
        st.error("Not enough pollutant columns for correlation.")
        return

    # ----------------------------------------------------------
    # FILTER PANEL
    # ----------------------------------------------------------
    st.markdown('<div class="section-box">', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        method = st.selectbox(
            "Correlation Method",
            ["pearson", "spearman"]  # Kendall removed
        )

    with col2:
        cities = st.multiselect(
            "Filter by City (optional)",
            sorted(df[location_col].dropna().unique())
        )

    st.markdown('</div>', unsafe_allow_html=True)

    # ----------------------------------------------------------
    # Apply city filter
    # ----------------------------------------------------------
    filtered_df = df.copy()

    if cities:
        filtered_df = filtered_df[filtered_df[location_col].isin(cities)]

    if filtered_df.empty:
        st.warning("No data found for selected cities.")
        return

    # ----------------------------------------------------------
    # Compute Correlation Matrix (Pollutants Only)
    # ----------------------------------------------------------
    corr_matrix = filtered_df[pollutant_cols].corr(method=method)

    # ----------------------------------------------------------
    # PLOT HEATMAP
    # ----------------------------------------------------------
    st.markdown("### 🎨 Correlation Heatmap (Pollutants Only)")
    st.markdown('<div class="plot-container">', unsafe_allow_html=True)

    fig = px.imshow(
        corr_matrix,
        color_continuous_scale=px.colors.sequential.Blues,
        text_auto=True,
        aspect="auto",
    )

    fig.update_layout(
        height=550,
        xaxis_title="Pollutants",
        yaxis_title="Pollutants",
        coloraxis_colorbar=dict(
            title="Correlation",
            ticks="outside"
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    st.markdown('</div>', unsafe_allow_html=True)
    # ----------------------------------------------------------
    # Correlation Method Description
    # -------------------------------------------
    st.markdown("""
    <div class="section-box">
        <h3>ℹ️ About Correlation Methods</h3>
        <ul style="font-size:16px; color:#3A4A66; line-height:1.6;">
            <li>
                <b>Pearson Correlation</b> measures the <b>linear relationship</b> between pollutants. 
                It works best when variables change in a straight-line pattern.
            </li>
            <li>
                <b>Spearman Correlation</b> measures the <b>rank-based (monotonic) relationship</b> between pollutants. 
                It is more reliable when data is <b>non-linear</b>, <b>skewed</b>, or contains <b>outliers</b>.
            </li>
        </ul>
        <p style="font-size:15px; color:#56627A;">
            ✅ Use <b>Spearman</b> for seasonal, uneven, or spiky pollutant data.  
            ✅ Use <b>Pearson</b> for cleaner, more linear pollutant trends.
        </p>
    </div>
    """, unsafe_allow_html=True)
     

    # ----------------------------------------------------------
    # DOWNLOAD CSV
    # ----------------------------------------------------------
    st.markdown("### 📥 Download Correlation Matrix")
    st.download_button(
        "Download as CSV",
        corr_matrix.to_csv().encode("utf-8"),
        file_name="pollutant_correlation_matrix.csv",
        mime="text/csv"
    )

