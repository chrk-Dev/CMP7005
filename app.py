import streamlit as st
import joblib
import os

# ----------------------------------------------------------
# PAGE CONFIG
# ----------------------------------------------------------
st.set_page_config(
    page_title="AQI Dashboard",
    layout="wide"
)

# ----------------------------------------------------------
# 🔥 LOAD MODELS & ARTIFACTS ONCE (GLOBAL)
# ----------------------------------------------------------
@st.cache_resource
def load_ml_artifacts():
    base_path = "models"

    reg_model = joblib.load(os.path.join(base_path, "aqi_xgboost_reg.pkl"))
    # If you later add classifier, encoders, etc., load here

    return reg_model

# Store in session_state so pages can use it
if "reg_model" not in st.session_state:
    st.session_state.reg_model = load_ml_artifacts()

# ----------------------------------------------------------
# CUSTOM CSS (Pastel theme + Hide Streamlit Auto Pages)
# ----------------------------------------------------------
st.markdown("""
<style>
    [data-testid="stSidebar"] {
        background-color: #F4F6FA;
    }

    .sidebar-title {
        font-size: 26px;
        font-weight: 700;
        color: #4A4A4A;
        padding-bottom: 12px;
    }

    div[role="radiogroup"] > label > div:first-child {
        display: none !important;
    }

    div[role="radiogroup"] > label {
        background-color: #ffffff;
        border: 1px solid #E2E6ED;
        padding: 12px 16px;
        margin: 6px 0;
        border-radius: 10px;
        width: 100%;
        cursor: pointer;
        color: #344767;
        font-size: 17px;
        transition: 0.2s ease;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    div[aria-checked="true"] {
        background-color: #A7C4FF !important;
        border-color: #7CA4FF !important;
        color: black !important;
        font-weight: 600 !important;
    }

    div[data-testid="stSidebarNav"] {
        display: none !important;
    }
</style>
""", unsafe_allow_html=True)

# ----------------------------------------------------------
# SIDEBAR NAVIGATION
# ----------------------------------------------------------
st.sidebar.markdown(
    "<div class='sidebar-title'>🗺️ Navigation</div>",
    unsafe_allow_html=True
)

tabs = [
    "🏠 Overview",
    "ℹ️ Dataset Information",
    "🧹 Data Cleaning",
    "📊 Exploratory Data Analysis",
    "🤖 Data Modeling and Predictions",
    "🧮 AQI Calculator",
    "📚 References"
]

page = st.sidebar.radio("", tabs, index=0)
page_clean = page.split(" ", 1)[1]

# ----------------------------------------------------------
# ROUTING
# ----------------------------------------------------------
if page_clean == "Overview":
    import pages.Overview as pg
    pg.show()

elif page_clean == "Dataset Information":
    import pages.Dataset_Information as pg
    pg.show()

elif page_clean == "Data Cleaning":
    import pages.Data_Cleaning as pg
    pg.show()

elif page_clean == "Exploratory Data Analysis":
    import pages.Exploratory_Data_Analysis as pg
    pg.show()

elif page_clean == "Data Modeling and Predictions":
    import pages.Data_Modeling_and_Predictions as pg
    pg.show()

elif page_clean == "AQI Calculator":
    import pages.CPCB_AQI_Calculator as pg
    pg.show()

elif page_clean == "References":
    import pages.References as pg
    pg.show()
