import os
import pandas as pd


DEFAULT_DATASET_PATH = "pages/AQI_cleaned_dataset.csv"
RAW_DATASET_PATHS = ["Dataset/combined_raw_data.csv", "../Dataset/combined_raw_data.csv"]


def load_base_dataframe(path: str = DEFAULT_DATASET_PATH) -> pd.DataFrame:
    # Check if path exists, if not try prepending 'pages/'
    current_path = path
    if not os.path.exists(current_path):
        alt_path = os.path.join("pages", os.path.basename(path))
        if os.path.exists(alt_path):
            current_path = alt_path
            
    df = pd.read_csv(current_path)
    
    # Always ensure clean Date column
    if "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    elif all(col in df.columns for col in ["year", "month", "day"]):
        # Create Date column from components if missing
        if "hour" in df.columns:
            df["Date"] = pd.to_datetime(df[["year", "month", "day", "hour"]])
        else:
            df["Date"] = pd.to_datetime(df[["year", "month", "day"]])
            
    return df


def load_raw_dataframe() -> pd.DataFrame:
    """Loads the raw dataset if it exists, otherwise falls back to the default dataset."""
    for path in RAW_DATASET_PATHS:
        if os.path.exists(path):
            return load_base_dataframe(path)
    return load_base_dataframe()


def get_location_col(df: pd.DataFrame) -> str:
    if "City" in df.columns:
        return "City"
    if "station" in df.columns:
        return "station"
    return "Location"


def get_aqi_col(df: pd.DataFrame) -> str:
    if "AQI_Recalc" in df.columns:
        return "AQI_Recalc"
    if "AQI_recalc" in df.columns:
        return "AQI_recalc"
    if "AQI" in df.columns:
        return "AQI"
    return ""


def get_aqi_bucket_col(df: pd.DataFrame) -> str:
    if "AQI_Bucket_Recalc" in df.columns:
        return "AQI_Bucket_Recalc"
    if "AQI_Bucket_recalc" in df.columns:
        return "AQI_Bucket_recalc"
    if "AQI_Bucket" in df.columns:
        return "AQI_Bucket"
    return ""


def get_pollutant_columns(df: pd.DataFrame) -> list[str]:
    exclude = {
        "No", "year", "month", "day", "hour", "TEMP", "PRES", "DEWP", "RAIN", "WSPM",
        "Date", "Month", "Year", "Month_Number", "Month_Name", "Day", "Week_Number",
        "AQI", "AQI_Recalc", "AQI_recalc", "AQI_Bucket", "AQI_Bucket_Recalc", "AQI_Bucket_recalc",
        "City", "station", "wd"
    }
    return [c for c in df.columns if c not in exclude and pd.api.types.is_numeric_dtype(df[c])]
