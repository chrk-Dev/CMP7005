import streamlit as st
import pandas as pd
import plotly.express as px
from sklearn.preprocessing import LabelEncoder
from app_pages.utils import get_location_col


def show():

    st.title("🤖 AQI Prediction using XGBoost")

    # =====================================================
    # LOAD DATA
    # =====================================================
    if "cleaned_df" not in st.session_state:
        st.error("Cleaned dataset not found. Please complete data cleaning first.")
        return

    df = st.session_state.cleaned_df.copy()

    # =====================================================
    # LOAD TRAINED MODEL (FROM app.py)
    # =====================================================
    reg_model = st.session_state.reg_model

    # Feature order learned during training
    feature_cols = list(reg_model.feature_names_in_)

    # =====================================================
    # BASIC FEATURE ENGINEERING (NO TRAINING)
    # =====================================================
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df["Month"] = df["Date"].dt.month

    df["Season"] = df["Month"].map({
        12: "Winter", 1: "Winter", 2: "Winter",
        3: "Spring", 4: "Spring", 5: "Spring",
        6: "Summer", 7: "Summer", 8: "Summer",
        9: "Autumn", 10: "Autumn", 11: "Autumn"
    })

    location_col = get_location_col(df)

    # Encode categorical columns
    city_encoder = LabelEncoder()
    season_encoder = LabelEncoder()

    df["City_Code"] = city_encoder.fit_transform(df[location_col])
    df["Season_Code"] = season_encoder.fit_transform(df["Season"])

    # =====================================================
    # POLLUTANT FEATURES (AQI_RECALC EXCLUDED 🔥)
    # =====================================================
    exclude_cols = [
        "AQI", "AQI_Recalc", "AQI_Bucket", "AQI_Bucket_Recalc",
        "AQI_recalc", "AQI_Bucket_recalc",
        "City", "station", "Date", "Season", "Month_Name", "wd",
        "Week", "Week_No", "Week_Number",
        "City_Code", "Season_Code", "Month", "No", "year", "month", "day", "hour"
    ]

    pollutants = [
        col for col in df.columns
        if col not in exclude_cols
        and pd.api.types.is_numeric_dtype(df[col])
    ]

    # =====================================================
    # USER INPUT UI
    # =====================================================
    st.subheader("🔮 Predict AQI")

    user_input = {}
    cols = st.columns(3)

    for i, p in enumerate(pollutants):
        with cols[i % 3]:
            user_input[p] = st.number_input(
                p,
                min_value=float(df[p].min()),
                max_value=float(df[p].max()),
                value=float(df[p].mean())
            )

    city = st.selectbox("Station", sorted(df[location_col].dropna().unique()))
    month = st.number_input("Month", min_value=1, max_value=12, value=6)

    season = df[df[location_col] == city]["Season"].mode().iloc[0]

    city_code = city_encoder.transform([city])[0]
    season_code = season_encoder.transform([season])[0]

    # =====================================================
    # BUILD INPUT DATAFRAME (MATCH MODEL FEATURES)
    # =====================================================
    input_df = pd.DataFrame([{
        **user_input,
        "City_Code": city_code,
        "Month": month,
        "Season_Code": season_code
    }])

    input_df = input_df.reindex(columns=feature_cols).fillna(0)

    # =====================================================
    # PREDICTION
    # =====================================================
    if st.button("Predict AQI"):
        predicted_aqi = reg_model.predict(input_df)[0]
        st.success(f"🌫 **Predicted AQI:** {predicted_aqi:.2f}")

    # =====================================================
    # FEATURE IMPORTANCE
    # =====================================================
    st.subheader("🔍 Feature Importance")

    importance_df = pd.DataFrame({
        "Feature": feature_cols,
        "Importance": reg_model.feature_importances_
    }).sort_values("Importance", ascending=False)

    fig = px.bar(
        importance_df,
        x="Feature",
        y="Importance",
        title="XGBoost Feature Importance"
    )

    st.plotly_chart(fig, use_container_width=True)

