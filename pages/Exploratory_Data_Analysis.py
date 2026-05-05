import streamlit as st
import plotly.express as px
import pandas as pd
from pages.utils import get_location_col, get_aqi_col, get_pollutant_columns, get_aqi_bucket_col


def show():

    # ==========================================================
    # HEADER
    # ==========================================================
    st.markdown("<h2 style='font-size:32px;'>📊 Exploratory Data Analysis</h2>", unsafe_allow_html=True)

    # ==========================================================
    # LOAD DATASET FROM SESSION STATE
    # ==========================================================
    df = None
    if "cleaned_df" in st.session_state:
        df = st.session_state.cleaned_df
    elif "current_df" in st.session_state:
        df = st.session_state.current_df
    elif "original_df" in st.session_state:
        df = st.session_state.original_df

    if df is None:
        st.error("❌ No dataset found. Please upload a dataset or run Data Cleaning.")
        return

    # ==========================================================
    # ENSURE REQUIRED COLUMNS EXIST
    # ==========================================================
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")

    aqi_col = get_aqi_col(df)
    if not aqi_col:
        st.error("AQI column not found in dataset.")
        return
    location_col = get_location_col(df)
    aqi_bucket_col = get_aqi_bucket_col(df)

    df["Month"] = df["Date"].dt.month
    df["Month_Name"] = df["Date"].dt.strftime("%B")
    pollutants = get_pollutant_columns(df)

    # ==========================================================
    # KPI SECTION
    # ==========================================================
    st.markdown("## 🧭 Dashboard Overview")

    avg_aqi = df[aqi_col].mean()
    severe_days = df[df[aqi_col] > 400].shape[0]

    HIGH_AQI_THRESHOLD = 200
    high_df = df[df[aqi_col] > HIGH_AQI_THRESHOLD]
    city_incidents = high_df.groupby(location_col)[aqi_col].count().sort_values(ascending=False)

    most_polluted_city = f"{city_incidents.idxmax()} ({city_incidents.max()} incidents)" if not city_incidents.empty else "N/A"
    cleanest_city = f"{city_incidents.idxmin()} ({city_incidents.min()} incidents)" if not city_incidents.empty else "N/A"
    top_pollutant = df[pollutants].mean().idxmax()

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("🌫 Avg AQI", f"{avg_aqi:.1f}")
    k2.metric("🔥 Severe Days", severe_days)
    k3.metric("🏙 Most Polluted", most_polluted_city)
    k4.metric("🌿 Cleanest City", cleanest_city)
    k5.metric("🔝 Top Pollutant", top_pollutant)

    st.markdown("---")

    # ==========================================================
    # MONTHLY AQI TREND
    # ==========================================================
    st.markdown("### 📉 Monthly AQI Trend")

    month_order = ["January","February","March","April","May","June",
                   "July","August","September","October","November","December"]

    df_month = df.groupby("Month_Name")[aqi_col].mean().reindex(month_order).reset_index()

    fig_trend = px.line(df_month, x="Month_Name", y=aqi_col, markers=True)
    fig_trend.update_layout(height=260)
    st.plotly_chart(fig_trend, use_container_width=True)

    st.markdown("---")

    # ==========================================================
    # DONUT CHART — BIG + LABEL WITH %
    # ==========================================================
    st.markdown("### 🫧 Pollutant Composition")

    poll_mean = df[pollutants].mean().sort_values(ascending=False)

    fig_donut = px.pie(
        names=poll_mean.index,
        values=poll_mean.values,
        hole=0.5,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig_donut.update_traces(
        textinfo="label+percent",
        textposition="outside",
        pull=[0.05] * len(poll_mean)
    )

    fig_donut.update_layout(
        height=420,
        showlegend=False,
        margin=dict(t=20, b=20, l=20, r=20),
        uniformtext_minsize=12,
        uniformtext_mode="hide"
    )

    st.plotly_chart(fig_donut, use_container_width=True)
    st.markdown("---")

    # ==========================================================
    # CITY BAR PLOT — BEAUTIFUL COLOR + DELHI VISIBLE
    # ==========================================================
    st.markdown(f"### 🏙 Top Cities with High AQI (>{HIGH_AQI_THRESHOLD})")

    if not city_incidents.empty:
        city_plot = city_incidents.reset_index().rename(
            columns={aqi_col: "High AQI Incidents"}
        )

        fig_city = px.bar(
            city_plot.head(10),
            x=location_col,
            y="High AQI Incidents",
            text="High AQI Incidents",
            color="High AQI Incidents",
            color_continuous_scale="Tealgrn"
        )

        fig_city.update_traces(
            textposition="outside",
            cliponaxis=False
        )

        fig_city.update_layout(
            height=420,
            xaxis_tickangle=-30,
            margin=dict(t=40, b=80, l=60, r=40),
            xaxis_title=location_col,
            yaxis_title="High AQI Incidents"
        )

        st.plotly_chart(fig_city, use_container_width=True)
    else:
        st.info("No high AQI data available.")

    st.markdown("---")
    # ==========================================================
    # ANALYSIS MODULE SELECTOR
    # ==========================================================
    st.markdown("<h3 style='font-size:24px;'>📂 Choose an Analysis Module</h3>", unsafe_allow_html=True)
    
    # ------------------ PASTEL BUTTON STYLING ------------------
    st.markdown("""
    <style>
    div.stButton > button {
        width: 100%;
        border-radius: 18px;
        border: 1px solid #C9DAFF;
        background: linear-gradient(135deg, #EEF4FF, #F8FBFF);
        color: #344767;
        padding: 0.8rem 0.5rem;
        font-size: 15px;
        font-weight: 600;
        box-shadow: 0px 4px 12px rgba(0,0,0,0.05);
        transition: all 0.2s ease-in-out;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, #DDE9FF, #EEF4FF);
        border-color: #7CA4FF;
        box-shadow: 0px 8px 20px rgba(124,164,255,0.25);
        transform: translateY(-2px);
    }
    </style>
    """, unsafe_allow_html=True)
    
    # ------------------ SESSION STATE ------------------
    if "eda_mode" not in st.session_state:
        st.session_state.eda_mode = "Distribution Analysis"
    
    modules = [
        ("📈 Distribution Analysis", "Distribution Analysis"),
        ("🕒 Time-Series Analysis", "Time-Series Analysis"),
        ("🔗 Correlation Matrix", "Correlation Matrix"),
        ("🟢 AQI Category Analysis", "AQI Category Analysis"),
        ("🍂 Seasonal Patterns", "Seasonal Patterns"),
        ("🔍 Comparison Tool", "Comparison Tool"),
    ]
    
    row1 = st.columns(3)
    row2 = st.columns(3)
    
    for i, (label, value) in enumerate(modules):
        col = row1[i] if i < 3 else row2[i - 3]
        with col:
            if st.button(label, key=f"mod_{value}"):
                st.session_state.eda_mode = value
    
    st.markdown(
        f"✅ <b>Selected Module:</b> <span style='color:green'>{st.session_state.eda_mode}</span>",
        unsafe_allow_html=True
    )
    st.markdown("---")
    
    # ==========================================================
    # LOAD SELECTED MODULE PAGE
    # ==========================================================
    mode = st.session_state.eda_mode
    
    if mode == "Distribution Analysis":
        import pages.EDA_Distribution as pg
        pg.show()
    
    elif mode == "Time-Series Analysis":
        import pages.EDA_Timeseries as pg
        pg.show()
    
    elif mode == "Correlation Matrix":
        import pages.EDA_Correlation as pg
        pg.show()
    
    elif mode == "AQI Category Analysis":
        import pages.EDA_AQI_Category as pg
        pg.show()
    
    elif mode == "Seasonal Patterns":
        import pages.EDA_Seasonal as pg
        pg.show()
    
    elif mode == "Comparison Tool":
        import pages.EDA_Comparison as pg
        pg.show()
    
