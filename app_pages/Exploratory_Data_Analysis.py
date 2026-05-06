import streamlit as st
import plotly.express as px
import pandas as pd
from app_pages.utils import get_location_col, get_aqi_col, get_pollutant_columns, get_aqi_bucket_col, load_base_dataframe


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
        try:
            df = load_base_dataframe()
            st.session_state.cleaned_df = df
            st.info("📂 No active dataset found. Loaded the default cleaned dataset.")
        except Exception as e:
            st.error(f"❌ No dataset found and failed to load default: {e}")
            return

    # ==========================================================
    # ENSURE REQUIRED COLUMNS EXIST
    # ==========================================================
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    elif all(col in df.columns for col in ["year", "month", "day"]):
        if "hour" in df.columns:
            df["Date"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
        else:
            df["Date"] = pd.to_datetime(df[["year", "month", "day"]])

    aqi_col = get_aqi_col(df)
    if not aqi_col:
        st.error("⚠️ AQI column not found in the current dataset.")
        col_err1, col_err2 = st.columns([1, 2])
        with col_err1:
            if st.button("📂 Load Cleaned Dataset"):
                st.session_state.cleaned_df = load_base_dataframe()
                st.rerun()
        with col_err2:
            st.info("💡 You can also recalculate AQI on the **Data Cleaning** page after filling missing values.")
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
    top_pollutant = df[pollutants].mean().idxmax() if pollutants else "N/A"

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("🌫 Avg AQI", f"{avg_aqi:.1f}")
    k2.metric("🔥 Severe Days", severe_days)
    k3.metric("🏙 Most Polluted", most_polluted_city)
    k4.metric("🌿 Cleanest City", cleanest_city)
    k5.metric("🔝 Top Pollutant", top_pollutant)

    st.markdown("---")

    # ==========================================================
    # TIME-LAPSE MAP
    # ==========================================================
    st.markdown("### 🗺️ Time-Lapse Density Map")
    
    # Station coordinates mapping
    station_coords = {
        "Aotizhongxin":  [39.9822, 116.3971],
        "Changping":     [40.2207, 116.2312],
        "Dingling":      [40.2900, 116.2200],
        "Dongsi":        [39.9290, 116.4170],
        "Guanyuan":      [39.9290, 116.3390],
        "Gucheng":       [39.9140, 116.1840],
        "Huairou":       [40.3280, 116.6280],
        "Nongzhanguan":  [39.9330, 116.4610],
        "Shunyi":        [40.1270, 116.6550],
        "Tiantan":       [39.8860, 116.4070],
        "Wanliu":        [39.9870, 116.2870],
        "Wanshouxigong": [39.8780, 116.3520],
    }
    
    # Time aggregation selector
    col1, col2 = st.columns(2)
    
    with col1:
        agg_level = st.selectbox(
            "📅 Aggregate time-lapse by",
            ["Daily", "Weekly", "Monthly"],
            index=2,
            key="timelapse_agg"
        )
    
    with col2:
        map_variable = st.selectbox(
            "🎨 Variable to display",
            [aqi_col] + pollutants + ["TEMP", "PRES", "DEWP", "RAIN"],
            index=0,
            key="map_variable"
        )
    
    # Prepare data for time-lapse map
    df_map = df.copy()
    df_map["lat"] = df_map[location_col].map(lambda x: station_coords.get(x, [0, 0])[0])
    df_map["lon"] = df_map[location_col].map(lambda x: station_coords.get(x, [0, 0])[1])
    
    if agg_level == "Daily":
        df_map["time_key"] = df_map["Date"].dt.strftime("%Y-%m-%d")
    elif agg_level == "Weekly":
        df_map["time_key"] = df_map["Date"].dt.to_period("W").astype(str)
    else:
        df_map["time_key"] = df_map["Date"].dt.strftime("%Y-%m")
    
    # Aggregate data
    agg_map_df = (
        df_map.groupby(["time_key", location_col, "lat", "lon"], as_index=False)[map_variable]
        .mean()
        .dropna(subset=[map_variable])
    )
    agg_map_df = agg_map_df.sort_values("time_key")
    
    # Display stats
    st.caption(
        f"🎬 {agg_map_df['time_key'].nunique()} frames · "
        f"{len(agg_map_df)} data points · "
        f"{agg_map_df[location_col].nunique()} stations"
    )
    
    # Create animated scatter map
    fig_map = px.scatter_map(
        agg_map_df,
        lat="lat",
        lon="lon",
        color=location_col,
        size=map_variable,
        animation_frame="time_key",
        hover_name=location_col,
        hover_data={map_variable: ":.1f", "lat": False, "lon": False},
        zoom=9,
        map_style="open-street-map",
        size_max=50,
        opacity=0.85,
    )
    
    fig_map.update_layout(
        height=550,
        legend=dict(
            title=location_col,
            bgcolor="rgba(255,255,255,0.9)",
            x=0.01,
            y=0.99
        )
    )
    
    st.plotly_chart(fig_map, use_container_width=True)
    
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
        import app_pages.EDA_Distribution as pg
        pg.show()
    
    elif mode == "Time-Series Analysis":
        import app_pages.EDA_Timeseries as pg
        pg.show()
    
    elif mode == "Correlation Matrix":
        import app_pages.EDA_Correlation as pg
        pg.show()
    
    elif mode == "AQI Category Analysis":
        import app_pages.EDA_AQI_Category as pg
        pg.show()
    
    elif mode == "Seasonal Patterns":
        import app_pages.EDA_Seasonal as pg
        pg.show()
    
    elif mode == "Comparison Tool":
        import app_pages.EDA_Comparison as pg
        pg.show()
    

