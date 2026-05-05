import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from pages.utils import get_location_col, get_aqi_col


# ----------------------------------------------------------
# CSS (light pastel but readable)
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
    border-radius: 14px;
    padding: 12px;
    background: #ffffff;
    box-shadow: 0px 2px 10px rgba(0,0,0,0.08);
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
        st.error("Dataset not found.")
        return

    st.header("📦 AQI Category Analysis")

    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    location_col = get_location_col(df)
    aqi_col = get_aqi_col(df)
    recalc_col = "AQI_recalc" if "AQI_recalc" in df.columns else "AQI_Recalc"
    before_bucket_col = "AQI_Bucket" if "AQI_Bucket" in df.columns else "AQI_Bucket_recalc"
    after_bucket_col = "AQI_Bucket_recalc" if "AQI_Bucket_recalc" in df.columns else "AQI_Bucket_Recalc"

    # ----------------------------------------------------------
    # Filters Box
    # ----------------------------------------------------------
    st.markdown('<div class="section-box">', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        cities = st.multiselect(
            "Select Cities (optional)",
            sorted(df[location_col].dropna().unique())
        )

    with col2:
        time_group = st.selectbox(
            "Group By",
            ["Yearly", "Monthly", "Weekly"],
            index=1
        )
    st.markdown('</div>', unsafe_allow_html=True)


    # ----------------------------------------------------------
    # Filter dataset
    # ----------------------------------------------------------
    filtered = df.copy()
    if cities:
        filtered = filtered[filtered[location_col].isin(cities)]

    if filtered.empty:
        st.warning("No data for selected filters.")
        return



    # ----------------------------------------------------------
    # CATEGORY BAR CHART (Before vs After)
    # ----------------------------------------------------------
    st.subheader("📊 Before vs After — AQI Category Distribution")

    category_order = ["Good", "Satisfactory", "Moderate", "Poor", "Very Poor", "Severe"]

    # BEFORE
    before_df = filtered[before_bucket_col].value_counts().reset_index()
    before_df.columns = ["Category", "Count"]
    before_df["Type"] = "Before"

    # AFTER
    after_df = filtered[after_bucket_col].value_counts().reset_index()
    after_df.columns = ["Category", "Count"]
    after_df["Type"] = "After"

    combined = pd.concat([before_df, after_df], ignore_index=True)
    combined["Category"] = pd.Categorical(combined["Category"], category_order, ordered=True)
    combined = combined.sort_values("Category")

    fig_bar = px.bar(
        combined,
        x="Category",
        y="Count",
        color="Type",
        barmode="group",
        color_discrete_sequence=["#4E79A7", "#F28E2B"],
        category_orders={"Category": category_order}
    )

    fig_bar.update_layout(
        height=450,
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        bargap=0.25
    )

    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
    st.plotly_chart(fig_bar, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)



    # ----------------------------------------------------------
    # TIME-GROUPED LINE CHART (AQI vs AQI_Recalc)
    # ----------------------------------------------------------
    st.subheader("📈 AQI Trend Comparison (Before vs After)")

    # ---- Create group key ----
    if time_group == "Yearly":
        filtered["Period"] = filtered["Date"].dt.year
        x_label = "Year"

    elif time_group == "Monthly":
        filtered["Period"] = filtered["Date"].dt.month
        x_label = "Month"

    elif time_group == "Weekly":
        filtered["Period"] = filtered["Date"].dt.isocalendar().week
        x_label = "Week Number"

    # ---- Aggregate ----
    if not aqi_col:
        st.warning("AQI column is missing in this dataset.")
        return
    agg = filtered.groupby("Period")[[aqi_col, recalc_col]].mean().reset_index()

    # Percent Difference
    agg["Percent_Diff"] = ((agg[recalc_col] - agg[aqi_col]) / agg[aqi_col]) * 100

    # Categories
    def cat(x):
        if x <= 50: return "Good"
        if x <= 100: return "Satisfactory"
        if x <= 200: return "Moderate"
        if x <= 300: return "Poor"
        if x <= 400: return "Very Poor"
        return "Severe"

    agg["AQI_Category"] = agg[aqi_col].apply(cat)
    agg["AQI_Recalc_Category"] = agg[recalc_col].apply(cat)


    # ----------------------------------------------------------
    # Plot with shading bands
    # ----------------------------------------------------------
    bands = [
        ("Good", 0, 50, "rgba(0, 176, 80, 0.15)"),
        ("Satisfactory", 51, 100, "rgba(255, 255, 0, 0.15)"),
        ("Moderate", 101, 200, "rgba(255, 165, 0, 0.15)"),
        ("Poor", 201, 300, "rgba(255, 0, 0, 0.15)"),
        ("Very Poor", 301, 400, "rgba(128, 0, 128, 0.15)"),
        ("Severe", 401, 500, "rgba(128, 64, 0, 0.15)")
    ]

    fig = go.Figure()

    # Background shading
    for name, y0, y1, color in bands:
        fig.add_shape(
            type="rect",
            x0=agg["Period"].min(),
            x1=agg["Period"].max(),
            y0=y0,
            y1=y1,
            fillcolor=color,
            line=dict(width=0),
            layer="below"
        )

    # Line colors
    colors = ["#4E79A7", "#F28E2B"]
    line_names = [aqi_col, recalc_col]
    category_cols = ["AQI_Category", "AQI_Recalc_Category"]

    # Add lines
    for line_name, clr, category_col in zip(line_names, colors, category_cols):
        fig.add_trace(go.Scatter(
            x=agg["Period"],
            y=agg[line_name],
            mode="lines+markers",
            name=line_name,
            line=dict(color=clr, width=3),
            marker=dict(size=8),

            customdata=agg[["Percent_Diff", category_col]].values,

            hovertemplate=
            "<b>%{fullData.name}</b><br>" +
            f"{x_label}: %{{x}}<br>" +
            "AQI: %{y:.1f}<br>" +
            "Δ %: %{customdata[0]:.2f}%<br>" +
            "Category: %{customdata[1]}<extra></extra>"
        ))

    # Layout
    fig.update_layout(
        height=550,
        template="simple_white",
        plot_bgcolor="#ffffff",
        paper_bgcolor="#ffffff",
        xaxis_title=x_label,
        yaxis_title="AQI Level",
        legend_title="Legend",
        margin=dict(t=60)
    )

    # Month names for monthly
    if time_group == "Monthly":
        fig.update_xaxes(
            tickvals=list(range(1, 13)),
            ticktext=["Jan","Feb","Mar","Apr","May","Jun",
                      "Jul","Aug","Sep","Oct","Nov","Dec"]
        )

    st.markdown('<div class="plot-container">', unsafe_allow_html=True)
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
