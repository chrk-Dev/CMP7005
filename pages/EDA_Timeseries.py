import streamlit as st
import pandas as pd
import plotly.express as px
from pages.utils import get_location_col

# ------------------------------------------
# Darker Professional Colors
# ------------------------------------------
DARK_COLORS = px.colors.qualitative.Plotly

# ------------------------------------------
# Pastel CSS
# ------------------------------------------
st.markdown("""
<style>
.section-box {
    background-color: #F8FAFF;
    padding: 18px;
    border-radius: 12px;
    border: 1px solid #E0E7FF;
    margin-bottom: 22px;
}

.plot-box {
    background: #ffffff;
    padding: 14px;
    border-radius: 12px;
    box-shadow: 0px 2px 10px rgba(0,0,0,0.05);
    margin-bottom: 24px;
}
</style>
""", unsafe_allow_html=True)


def show():

    # ------------------- Load Data -----------------------
    if "cleaned_df" in st.session_state:
        df = st.session_state.cleaned_df
    elif "current_df" in st.session_state:
        df = st.session_state.current_df
    else:
        df = st.session_state.original_df

    if df is None:
        st.error("Dataset not found.")
        return

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    st.header("📉 Time-Series Analysis (Normalized Option)")

    # ---------------- Detect pollutant columns ----------------
    location_col = get_location_col(df)
    exclude = {location_col, "AQI", "AQI_Recalc", "AQI_recalc", "AQI_Bucket", "AQI_Bucket_Recalc", "AQI_Bucket_recalc"}
    pollutant_cols = [
        c for c in df.columns
        if c not in exclude and pd.api.types.is_numeric_dtype(df[c])
    ]

    # ---------------- INLINE FILTER ROW ----------------
    st.markdown('<div class="section-box">', unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        pollutants = st.multiselect(
            "Pollutants (max 3)",
            pollutant_cols,
            max_selections=3
        )

    with col2:
        cities = st.multiselect(
            "Cities (max 3)",
            sorted(df[location_col].dropna().unique()),
            max_selections=3
        )

    all_years = sorted(df["Date"].dt.year.dropna().unique())

    with col3:
        from_year = st.selectbox("From Year", all_years)

    with col4:
        to_year = st.selectbox("To Year", all_years, index=len(all_years) - 1)

    st.markdown("</div>", unsafe_allow_html=True)

    # Normalization toggle
    normalize = st.checkbox("🔄 Normalize (Min-Max: 0 → 1)", value=True)

    # ---------------- VALIDATION ----------------
    if not pollutants:
        st.warning("Please select at least one pollutant.")
        return

    if not cities:
        st.warning("Please select at least one city.")
        return

    if from_year > to_year:
        st.error("❌ 'From Year' cannot be greater than 'To Year'.")
        return

    # ---------------- APPLY FILTERS ----------------
    df = df[df[location_col].isin(cities)]
    df = df[(df["Date"].dt.year >= from_year) & (df["Date"].dt.year <= to_year)]

    # Group-by variable always Date now (cleanest)
    group_var = "Date"

    # =====================================================
    # NORMALIZATION LOGIC
    # =====================================================
    if normalize:

        for pollutant in pollutants:
            min_val = df[pollutant].min()
            max_val = df[pollutant].max()

            if max_val - min_val == 0:
                df[f"norm_{pollutant}"] = 0
            else:
                df[f"norm_{pollutant}"] = (df[pollutant] - min_val) / (max_val - min_val)

        y_cols = [f"norm_{p}" for p in pollutants]
        y_label_suffix = " (Normalized)"

    else:
        y_cols = pollutants
        y_label_suffix = ""

    # =====================================================
    # SMART CHART LOGIC
    # =====================================================

    # CASE 1 — ONE pollutant, MULTIPLE cities → single chart
    if len(pollutants) == 1 and len(cities) > 1:

        pollutant = pollutants[0]
        y_col = y_cols[0]

        st.subheader(f"📊 {pollutant}{y_label_suffix} — Across Cities")

        fig = px.line(
            df,
            x=group_var,
            y=y_col,
            color=location_col,
            markers=False,
            color_discrete_sequence=DARK_COLORS,
            title=f"{pollutant}{y_label_suffix} Over Time ({from_year}–{to_year})"
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title=pollutant + y_label_suffix
        )

        st.plotly_chart(fig, use_container_width=True)

    # CASE 2 — MULTIPLE pollutants, ONE city → single chart
    elif len(cities) == 1 and len(pollutants) > 1:

        city = cities[0]
        st.subheader(f"📊 {city} — Multiple Pollutants{y_label_suffix}")

        fig = px.line(
            df[df[location_col] == city],
            x=group_var,
            y=y_cols,
            markers=False,
            color_discrete_sequence=DARK_COLORS,
            title=f"Pollutant Trends{y_label_suffix} — {city} ({from_year}–{to_year})"
        )

        fig.update_layout(
            xaxis_title="Date",
            yaxis_title="Pollutant Level" + y_label_suffix
        )

        st.plotly_chart(fig, use_container_width=True)

    # CASE 3 — MULTIPLE pollutants, MULTIPLE cities → multiple charts (clean)
    else:
        st.subheader(f"📊 Multiple Pollutants × Cities (Normalized: {normalize})")

        for pollutant, y_col in zip(pollutants, y_cols):

            st.markdown(f"### 🌈 {pollutant}{y_label_suffix}")

            fig = px.line(
                df,
                x=group_var,
                y=y_col,
                color=location_col,
                markers=False,
                color_discrete_sequence=DARK_COLORS,
                title=f"{pollutant}{y_label_suffix} — {from_year}–{to_year}"
            )

            fig.update_layout(
                xaxis_title="Date",
                yaxis_title=pollutant + y_label_suffix
            )

            st.markdown('<div class="plot-box">', unsafe_allow_html=True)
            st.plotly_chart(fig, use_container_width=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # ---------------- Summary Table ----------------
    st.markdown("### 📌 Summary Statistics")
    summary = df.groupby(location_col)[pollutants].describe()
    st.dataframe(summary, use_container_width=True)
