import streamlit as st
import pandas as pd
import math

# -------------------------------------------------
# CPCB Breakpoints (India National AQI)
# -------------------------------------------------
AQI_BREAKPOINTS = {
    "PM2.5": [
        (0, 30,    0,   50),
        (31, 60,   51, 100),
        (61, 90,  101, 200),
        (91, 120, 201, 300),
        (121, 250,301, 400),
        (251, 9999,401, 500),
    ],
    "PM10": [
        (0, 50,    0,   50),
        (51, 100,  51, 100),
        (101, 250,101, 200),
        (251, 350,201, 300),
        (351, 430,301, 400),
        (431, 9999,401, 500),
    ],
    "NO2": [
        (0, 40,    0,   50),
        (41, 80,   51, 100),
        (81, 180, 101, 200),
        (181, 280,201, 300),
        (281, 400,301, 400),
        (401, 9999,401, 500),
    ],
    "SO2": [
        (0, 40,    0,   50),
        (41, 80,   51, 100),
        (81, 380, 101, 200),
        (381, 800,201, 300),
        (801, 1600,301, 400),
        (1601, 9999,401, 500),
    ],
    "O3": [
        (0, 50,    0,   50),
        (51, 100,  51, 100),
        (101, 168,101, 200),
        (169, 208,201, 300),
        (209, 748,301, 400),
        (749, 9999,401, 500),
    ],
    "CO": [  # 8-hour avg, mg/m3
        (0.0, 1.0,   0,   50),
        (1.1, 2.0,  51, 100),
        (2.1, 10.0,101, 200),
        (10.1,17.0,201, 300),
        (17.1,34.0,301, 400),
        (34.1,9999,401, 500),
    ],
    "NH3": [
        (0, 200,   0,   50),
        (201, 400, 51, 100),
        (401, 800,101, 200),
        (801, 1200,201, 300),
        (1201, 1800,301, 400),
        (1801, 9999,401, 500),
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
        This calculator computes AQI as per **CPCB (India)** guidelines  
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
