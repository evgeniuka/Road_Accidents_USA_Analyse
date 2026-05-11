import os
import pandas as pd
from src.preprocessing import object_columns_to_category, base_preprocess_datetime
from src.constants import (
    CSV,                    # fallback path (optional)
    SAMPLE_CSV,
    EXTERNAL_RAW_CSV,       # D:\git\dataset\US_Accidents_March23.csv
    EXTERNAL_PROCESSED_DIR, # D:\git\accidents_clean\
    EXTERNAL_CLEAN_CSV,     # D:\git\accidents_clean\US_Accidents_March23_clean.csv
)

# Keep only necessary columns to reduce memory during ETL
KEEP_COLS = [
    "Start_Time", "Severity", "City", "Weather_Condition", "Visibility(mi)",
    "Precipitation(in)", "Temperature(F)", "Wind_Speed(mph)",
    "Bump", "Crossing", "Street", "Description",
]

def _find_raw_csv() -> str:
    """Prefer external ..\\dataset\\US_Accidents_March23.csv; else fall back to constants.CSV."""
    candidates = [EXTERNAL_RAW_CSV, CSV]
    for path in candidates:
        if path and os.path.exists(path):
            return path
    raise FileNotFoundError(
        "Raw dataset not found.\n"
        f"Looked for:\n - {EXTERNAL_RAW_CSV}\n - {CSV}\n\n"
        "Place 'US_Accidents_March23.csv' into '..\\dataset\\' (one level above the repo) "
        "or update constants.CSV to a valid location."
    )

def _etl_clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Parse dates, trim outliers, keep years 2016..2023, drop critical NAs, cast categories."""
    df = base_preprocess_datetime(
        df,
        apply_outliers=True,
        outlier_cols=["Visibility(mi)", "Precipitation(in)", "Temperature(F)", "Wind_Speed(mph)"]
    )
    if "year" in df.columns:
        df = df[df["year"].between(2016, 2023)]
    df = df.dropna(subset=["Start_Time", "Severity", "City"])
    df = object_columns_to_category(df, columns=["City", "Weather_Condition"])
    return df

def build_clean_to_parent() -> pd.DataFrame:
    """ETL -> save cleaned CSV at ..\\accidents_clean\\US_Accidents_March23_clean.csv, return cleaned df."""
    raw_path = _find_raw_csv()
    df_raw   = pd.read_csv(raw_path, usecols=lambda c: c in KEEP_COLS, on_bad_lines="skip", low_memory=False)
    df_clean = _etl_clean_dataframe(df_raw)
    os.makedirs(EXTERNAL_PROCESSED_DIR, exist_ok=True)
    df_clean.to_csv(EXTERNAL_CLEAN_CSV, index=False)
    print(f"[ETL] Cleaned dataset saved to:\n  {EXTERNAL_CLEAN_CSV}")
    return df_clean

def load_external_clean_or_build() -> pd.DataFrame:
    if os.path.exists(EXTERNAL_CLEAN_CSV):
        return pd.read_csv(EXTERNAL_CLEAN_CSV, parse_dates=["Start_Time"], low_memory=False)
    return build_clean_to_parent()


def load_sample() -> pd.DataFrame:
    if not os.path.exists(SAMPLE_CSV):
        raise FileNotFoundError(f"Sample CSV not found: {SAMPLE_CSV}")
    df = pd.read_csv(SAMPLE_CSV, low_memory=False)
    return _etl_clean_dataframe(df)


def load_dataset(use_sample: bool = False) -> pd.DataFrame:
    if use_sample:
        return load_sample()
    try:
        return load_external_clean_or_build()
    except FileNotFoundError as exc:
        print(str(exc))
        print("\n[Notice] Using the bundled sample dataset instead.")
        return load_sample()


def ld(*_args, **_kwargs) -> pd.DataFrame:
    return load_dataset()

# def ld(p, yrs=None):
#     keep = [
#         "Start_Time", "Severity",
#         "City",
#         "Weather_Condition", "Visibility(mi)", "Precipitation(in)",
#         "Temperature(F)", "Wind_Speed(mph)",
#         "Bump", "Crossing", "Street", "Description",
#     ]
#     df = pd.read_csv(p, usecols=lambda c: c in keep, on_bad_lines="skip")
#     df["Start_Time"] = pd.to_datetime(df["Start_Time"], errors="coerce")
#     df = df.dropna(subset=["Start_Time", "Severity"])
#     df = base_preprocess_datetime(
#         df,
#         apply_outliers=True,
#         outlier_cols=["Visibility(mi)", "Precipitation(in)", "Temperature(F)", "Wind_Speed(mph)"]
#     )
#     df = df[df["year"].between(2016, 2023)]
#     df = df.dropna(subset=["City"])
#     df = object_columns_to_category(df, columns=["City", "Weather_Condition"])
#     return df
