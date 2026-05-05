import streamlit as st
import pandas as pd
import io
from pages.utils import load_base_dataframe, get_location_col, get_aqi_bucket_col

def show():

    # ----------------------------
    # Load Dataset (Internal)
    # ----------------------------
    df = load_base_dataframe()
    total_rows = df.shape[0]
    location_col = get_location_col(df)
    aqi_bucket_col = get_aqi_bucket_col(df)

    # ----------------------------
    # Page Styling
    # ----------------------------
    st.markdown("""
        <style>

            .section-header {
                font-size: 28px !important;
                font-weight: 700 !important;
                color: #344767 !important;
                margin-top: 25px !important;
                margin-bottom: 10px !important;
            }

            .sub-header {
                font-size: 22px !important;
                font-weight: 600 !important;
                color: #4A6480 !important;
                margin-top: 20px !important;
                margin-bottom: 10px !important;
            }

            .pastel-box {
                background-color: #F7F9FC;
                padding: 18px;
                border-radius: 12px;
                border: 1px solid #E3EAF4;
                margin-bottom: 20px;
                font-size: 16px;
                line-height: 1.55;
                color: #3A4A66;
            }

            .info-text {
                font-family: monospace;
                font-size: 15px;
                white-space: pre-wrap;
            }

            /* ---------------- RADIO BUTTON STYLING ---------------- */

            div[role="radiogroup"] > label {
                border: 1px solid #E3EAF4;
                padding: 10px 14px;
                margin: 5px 0;
                border-radius: 10px;
                background-color: white;
                transition: 0.2s ease;
                font-size: 16px;
                color: #3A4A66;
            }

            div[role="radiogroup"] > label:hover {
                background-color: #f0f4fa;
                border-color: #cfd8e3;
            }

            div[role="radiogroup"] > label[aria-checked="true"] {
                background-color: #d8e8ff !important;
                border-color: #a7c4ff !important;
                color: #2a3a55 !important;
                font-weight: 600 !important;
            }

        </style>
    """, unsafe_allow_html=True)

    # ----------------------------
    # Title
    # ----------------------------
    st.markdown("<div class='section-header'>📘 Dataset Information</div>", unsafe_allow_html=True)

    # ----------------------------
    # Dataset Description
    # ----------------------------
    st.markdown("""
    <div class="pastel-box">
        This page provides a high-level overview of the dataset used for AQI analysis.
        You can explore the top/bottom rows, dataset structure, column data types, and
        basic descriptive statistics.  
        <br><br>
        Detailed cleaning and preprocessing will be performed in the Data Cleaning page.
    </div>
    """, unsafe_allow_html=True)

    # ===============================================================
    # 🔍 VIEW ROWS BLOCK (SIDE-BY-SIDE)
    # ===============================================================
    st.markdown("<div class='sub-header'>🔍 View Dataset Rows</div>", unsafe_allow_html=True)
    
    colA, colB = st.columns(2)
    
    with colA:
        st.markdown("### ▶️ First Rows")
        num_rows_first = st.number_input(
            "Rows to display (first):", min_value=1, max_value=total_rows, value=5
        )
        st.dataframe(df.head(num_rows_first), use_container_width=True)
    
    with colB:
        st.markdown("### ◀️ Last Rows")
        num_rows_last = st.number_input(
            "Rows to display (last):", min_value=1, max_value=total_rows, value=5
        )
        st.dataframe(df.tail(num_rows_last), use_container_width=True)

    # ===============================================================
    # 🔎 UNIQUE VALUES CHECKER FOR CATEGORICAL COLUMNS
    # ===============================================================
    st.markdown("<div class='sub-header'>🔎 Check Unique Values of Categorical Columns</div>", unsafe_allow_html=True)
    
    # Identify categorical columns automatically
    cat_cols = [location_col, aqi_bucket_col]
    cat_cols = [col for col in cat_cols if col in df.columns]
    
    if len(cat_cols) > 0:
        selected_cat = st.selectbox("Select a categorical column:", cat_cols)
        st.markdown(f"<div class='pastel-box'><b>Unique Values in {selected_cat}:</b><br>{df[selected_cat].unique()}</div>", unsafe_allow_html=True)
    else:
        st.info("No categorical columns found in the dataset.")

    # ----------------------------
    # Dataset Structure
    # ----------------------------
    st.markdown("<div class='sub-header'>📄 Dataset Structure</div>", unsafe_allow_html=True)

    st.markdown(f"""
    <div class='pastel-box'>
        🔹 <b>Total Rows:</b> {df.shape[0]} <br>
        🔹 <b>Total Columns:</b> {df.shape[1]} <br>
        🔹 <b>Column Names:</b> {', '.join(df.columns)}
    </div>
    """, unsafe_allow_html=True)

    # ----------------------------
    # Data Types
    # ----------------------------
    st.markdown("<div class='sub-header'>🔠 Column Data Types</div>", unsafe_allow_html=True)

    dtype_df = (
        pd.DataFrame(df.dtypes, columns=["Data Type"])
        .reset_index()
        .rename(columns={"index": "Column"})
    )
    st.dataframe(dtype_df, use_container_width=True)

    # ----------------------------
    # df.info()
    # ----------------------------
    st.markdown("<div class='sub-header'>🧠 Dataset Info (df.info)</div>", unsafe_allow_html=True)

    buffer = io.StringIO()
    df.info(buf=buffer)
    info_str = buffer.getvalue()

    st.markdown(f"<div class='pastel-box info-text'>{info_str}</div>", unsafe_allow_html=True)

    # ===============================================================
    # 📊 STATISTICAL SUMMARY
    # ===============================================================
    st.markdown("<div class='sub-header'>📊 Statistical Summary</div>", unsafe_allow_html=True)

    desc = df.describe()

    # Streamlit cannot render a pandas Styler object reliably → FIXED
    st.dataframe(desc, use_container_width=True)
