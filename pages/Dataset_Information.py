import streamlit as st
import pandas as pd
import io
from pages.utils import load_base_dataframe, get_location_col, get_aqi_bucket_col, load_raw_dataframe

def show():

    # ----------------------------
    # Load Dataset (Internal)
    # ----------------------------
    if "info_dataset_source" not in st.session_state:
        st.session_state.info_dataset_source = "Cleaned"

    # ----------------------------
    # Page Styling (Enhanced)
    # ----------------------------
    st.markdown("""
        <style>
            .section-header {
                font-size: 32px !important;
                font-weight: 800 !important;
                color: #1a202c !important;
                margin-top: 10px !important;
                margin-bottom: 5px !important;
                letter-spacing: -0.5px;
            }
            .sub-header {
                font-size: 20px !important;
                font-weight: 700 !important;
                color: #2d3748 !important;
                margin-top: 25px !important;
                margin-bottom: 12px !important;
                border-left: 5px solid #4a90e2;
                padding-left: 12px;
            }
            .pastel-box {
                background-color: #ffffff;
                padding: 20px;
                border-radius: 16px;
                border: 1px solid #e2e8f0;
                margin-bottom: 25px;
                font-size: 16px;
                color: #4a5568;
                box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
            }
            /* Radio button styling */
            div[role="radiogroup"] {
                gap: 10px;
            }
        </style>
    """, unsafe_allow_html=True)

    # ----------------------------
    # Header & Source Selection
    # ----------------------------
    col_h1, col_h2 = st.columns([2, 1])
    with col_h1:
        st.markdown("<div class='section-header'>📘 Dataset Insights</div>", unsafe_allow_html=True)
        st.markdown("<p style='color:#718096; font-size:18px;'>Explore the structure and health of your data.</p>", unsafe_allow_html=True)
    with col_h2:
        st.markdown("<div style='margin-top:10px;'></div>", unsafe_allow_html=True)
        source_opt = st.radio("Dataset Source:", ["Cleaned", "Raw"], horizontal=True, index=0 if st.session_state.info_dataset_source == "Cleaned" else 1)
        if source_opt != st.session_state.info_dataset_source:
            st.session_state.info_dataset_source = source_opt
            st.rerun()

    if st.session_state.info_dataset_source == "Raw":
        df = load_raw_dataframe()
        source_label = "🔴 Raw Data"
    else:
        df = load_base_dataframe()
        source_label = "🟢 Cleaned Data"

    total_rows = df.shape[0]
    total_cols = df.shape[1]
    location_col = get_location_col(df)
    aqi_bucket_col = get_aqi_bucket_col(df)

    # ----------------------------
    # KPI Section
    # ----------------------------
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    with kpi1:
        st.metric("Total Observations", f"{total_rows:,}")
    with kpi2:
        st.metric("Feature Count", total_cols)
    with kpi3:
        missing_total = df.isnull().sum().sum()
        missing_pct = (missing_total / (total_rows * total_cols)) * 100 if total_rows > 0 else 0
        st.metric("Total Missing Cells", f"{missing_total:,}", delta=f"{missing_pct:.1f}%", delta_color="inverse")
    with kpi4:
        st.metric("Dataset Source", source_label)

    st.markdown("---")

    # ----------------------------
    # Tabs for Organization
    # ----------------------------
    tab1, tab2, tab3 = st.tabs(["📋 Overview & Structure", "🔍 Data Preview", "📊 Statistical Summary"])

    with tab1:
        # Dataset Description
        st.markdown("<div class='sub-header'>📝 About this Dataset</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div class="pastel-box">
            This view is currently showing the <b>{st.session_state.info_dataset_source}</b> dataset.
            The data contains information about pollutants (PM2.5, PM10, etc.) collected across various stations/cities.
            Use this page to verify column types and general distributions before moving to analysis.
        </div>
        """, unsafe_allow_html=True)

        col_st1, col_st2 = st.columns(2)
        with col_st1:
            st.markdown("<div class='sub-header'>📄 Column Data Types</div>", unsafe_allow_html=True)
            dtype_df = (
                pd.DataFrame(df.dtypes, columns=["Data Type"])
                .reset_index()
                .rename(columns={"index": "Column Name"})
            )
            st.dataframe(dtype_df, use_container_width=True, height=400)

        with col_st2:
            st.markdown("<div class='sub-header'>🔎 Categorical Explorer</div>", unsafe_allow_html=True)
            # Identify categorical columns automatically
            cat_cols = [location_col, aqi_bucket_col, "AQI_Bucket_recalc", "AQI_Bucket_Recalc", "AQI_Bucket", "wd"]
            cat_cols = [col for col in cat_cols if col and col in df.columns]
            cat_cols = list(dict.fromkeys(cat_cols))
            
            if cat_cols:
                selected_cat = st.selectbox("Select column to check unique values:", cat_cols)
                u_vals = df[selected_cat].dropna().unique()
                st.info(f"**Found {len(u_vals)} unique values in {selected_cat}:**")
                st.write(", ".join(map(str, sorted(u_vals))))
            else:
                st.info("No categorical columns detected.")

        with st.expander("🧠 Detailed Schema Info (df.info)"):
            buffer = io.StringIO()
            df.info(buf=buffer)
            st.code(buffer.getvalue())

    with tab2:
        st.markdown("<div class='sub-header'>🔍 Deep Dive into Rows</div>", unsafe_allow_html=True)
        
        row_choice = st.radio("View range:", ["Top Rows", "Bottom Rows", "Random Sample"], horizontal=True)
        num_rows = st.slider("Select number of rows:", 5, 100, 10)
        
        if row_choice == "Top Rows":
            st.dataframe(df.head(num_rows), use_container_width=True)
        elif row_choice == "Bottom Rows":
            st.dataframe(df.tail(num_rows), use_container_width=True)
        else:
            st.dataframe(df.sample(num_rows), use_container_width=True)

        st.markdown("<div class='sub-header'>📊 Missingness Snapshot</div>", unsafe_allow_html=True)
        missing_df = df.isnull().sum().reset_index()
        missing_df.columns = ["Column", "Missing Count"]
        missing_df["Missing %"] = (missing_df["Missing Count"] / total_rows) * 100
        st.dataframe(missing_df.sort_values("Missing Count", ascending=False), use_container_width=True)

    with tab3:
        st.markdown("<div class='sub-header'>📊 Descriptive Statistics</div>", unsafe_allow_html=True)
        st.dataframe(df.describe().T, use_container_width=True)

        st.markdown("<div class='sub-header'>📈 Value Counts (Top Categories)</div>", unsafe_allow_html=True)
        col_vc1, col_vc2 = st.columns(2)
        with col_vc1:
            if location_col in df.columns:
                st.write(f"**Top 10 {location_col}**")
                st.bar_chart(df[location_col].value_counts().head(10))
        with col_vc2:
            bucket_col = aqi_bucket_col if aqi_bucket_col in df.columns else None
            if bucket_col:
                st.write(f"**{bucket_col} Distribution**")
                st.bar_chart(df[bucket_col].value_counts())
