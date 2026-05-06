import streamlit as st
import pandas as pd
import math


# Format: (C_low, C_high, I_low, I_high)
# Units: mg/m3 for CO, μg/m3 for others
AQI_BREAKPOINTS = {
    "PM2.5": [
        (0, 35, 0, 50),      # Excellent
        (36, 75, 51, 100),   # Good
        (76, 115, 101, 150), # Lightly Polluted
        (116, 150, 151, 200),# Moderately Polluted
        (151, 250, 201, 300),# Heavily Polluted
        (251, 500, 301, 500),# Severely Polluted
    ],
    "PM10": [
        (0, 50, 0, 50),
        (51, 150, 51, 100),
        (151, 250, 101, 150),
        (251, 350, 151, 200),
        (351, 420, 201, 300),
        (421, 600, 301, 500),
    ],
    "NO2": [  # 24-hour average
        (0, 40, 0, 50),
        (41, 80, 51, 100),
        (81, 180, 101, 150),
        (181, 280, 151, 200),
        (281, 565, 201, 300),
        (566, 940, 301, 500),
    ],
    "SO2": [  # 24-hour average
        (0, 50, 0, 50),
        (51, 150, 51, 100),
        (151, 475, 101, 150),
        (476, 800, 151, 200),
        (801, 1600, 201, 300),
        (1601, 2620, 301, 500),
    ],
    "O3": [  # 8-hour moving average
        (0, 100, 0, 50),
        (101, 160, 51, 100),
        (161, 215, 101, 150),
        (216, 265, 151, 200),
        (266, 800, 201, 300),
        (801, 1200, 301, 500),
    ],
    "CO": [  # 24-hour average, unit: mg/m3
        (0, 2, 0, 50),
        (3, 4, 51, 100),
        (5, 14, 101, 150),
        (15, 24, 151, 200),
        (25, 36, 201, 300),
        (37, 60, 301, 500),
    ],
}

AQI_CATEGORIES = [
    (0, 50,   "Good", "🟢", "Minimal impact"),
    (51, 100, "Satisfactory", "🟡", "Minor breathing discomfort to sensitive people"),
    (101, 200,"Moderate", "🟠", "Discomfort to people with lungs, asthma, heart diseases"),
    (201, 300,"Poor", "🟤", "Breathing discomfort on prolonged exposure"),
    (301, 400,"Very Poor", "🔴", "Respiratory illness on prolonged exposure"),
    (401, 500,"Severe", "🛑", "Affects healthy people, seriously impacts those with diseases"),
]

def calculate_sub_index(pollutant, concentration):
    """Linear interpolation of AQI sub-index based on CPCB breakpoints."""
    if concentration is None or math.isnan(concentration):
        return None

    if pollutant not in AQI_BREAKPOINTS:
        return None

    for (Clow, Chigh, Ilow, Ihigh) in AQI_BREAKPOINTS[pollutant]:
        if Clow <= concentration <= Chigh:
            sub_index = ((Ihigh - Ilow) / (Chigh - Clow)) * (concentration - Clow) + Ilow
            return round(sub_index)

    return None

def classify_aqi(aqi_value):
    """Return category, emoji, and health message for given AQI."""
    for low, high, label, emoji, msg in AQI_CATEGORIES:
        if low <= aqi_value <= high:
            return label, emoji, msg
    return "Out of Range", "❓", "AQI value outside standard limits."


def show():
    st.title("🧮 CPCB AQI Calculator")

    st.markdown(
        """
        This calculator computes AQI as per **CPCB (China)** guidelines  
        using pollutant concentrations and breakpoint-based sub-indices.
        """
    )

    st.markdown("---")

    st.subheader("🧾 Enter Pollutant Concentrations")

    col1, col2, col3 = st.columns(3)

    with col1:
        pm25 = st.number_input("PM2.5 (µg/m³)", min_value=0.0, value=0.0, step=1.0)
        pm10 = st.number_input("PM10 (µg/m³)", min_value=0.0, value=0.0, step=1.0)
        so2  = st.number_input("SO₂ (µg/m³)", min_value=0.0, value=0.0, step=1.0)

    with col2:
        no2 = st.number_input("NO₂ (µg/m³)", min_value=0.0, value=0.0, step=1.0)
        o3  = st.number_input("O₃ (µg/m³)",  min_value=0.0, value=0.0, step=1.0)
        nh3 = st.number_input("NH₃ (µg/m³)", min_value=0.0, value=0.0, step=1.0)

    with col3:
        co = st.number_input("CO (mg/m³, 8-hr avg)", min_value=0.0, value=0.0, step=0.1)

    st.markdown("---")

    if st.button("Calculate AQI", use_container_width=True):

        pollutant_values = {
            "PM2.5": pm25,
            "PM10": pm10,
            "NO2":  no2,
            "SO2":  so2,
            "O3":   o3,
            "CO":   co,
            "NH3":  nh3,
        }

        sub_indices = {}
        for pol, val in pollutant_values.items():
            si = calculate_sub_index(pol, val)
            if si is not None:
                sub_indices[pol] = si

        if not sub_indices:
            st.error("No valid pollutant values entered to compute AQI.")
            return

        dominant_pollutant = max(sub_indices, key=sub_indices.get)
        overall_aqi = sub_indices[dominant_pollutant]

        category, emoji, msg = classify_aqi(overall_aqi)

        st.subheader("📊 AQI Result")

        st.markdown(
            f"""
            <div style="padding:15px;border-radius:10px;background-color:#F5F7FF;border:1px solid #D0D7FF;">
                <h2 style="margin-bottom:5px;">Overall AQI: <b>{overall_aqi}</b> {emoji}</h2>
                <p style="font-size:18px;margin:0;">
                    Category: <b>{category}</b> <br>
                    Dominant Pollutant: <b>{dominant_pollutant}</b>
                </p>
                <p style="margin-top:8px;font-size:14px;color:#555;">
                    Health Advisory: {msg}
                </p>
            </div>
            """,
            unsafe_allow_html=True
        )

        st.markdown("### 🔍 Sub-indices by Pollutant")
        sub_df = (
            pd.Series(sub_indices, name="Sub-Index")
            .sort_values(ascending=False)
            .to_frame()
        )
        st.dataframe(sub_df, use_container_width=True)

    st.markdown("---")
    st.info(
        "ℹ️ Note: This calculator uses CPCB breakpoint tables. "
        "For reporting, ensure units and averaging times (24-hr / 8-hr) "
        "match CPCB protocol."
    )
