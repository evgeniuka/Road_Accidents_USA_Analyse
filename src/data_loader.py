import os
import pandas as pd
from src.preprocessing import object_columns_to_category, base_preprocess_datetime
from src.constants import (
    CSV,
    SAMPLE_CSV,
    EXTERNAL_RAW_CSV,
    EXTERNAL_PROCESSED_DIR,
    EXTERNAL_CLEAN_CSV,
)

# Keep only necessary columns to reduce memory during ETL
KEEP_COLS = [
    "ID", "Start_Time", "Severity", "Start_Lat", "Start_Lng",
    "City", "County", "State", "Country",
    "Weather_Condition", "Visibility(mi)",
    "Precipitation(in)", "Temperature(F)", "Wind_Speed(mph)",
    "Distance(mi)", "Bump", "Crossing", "Junction", "Traffic_Signal",
    "Street", "Description", "Sunrise_Sunset",
]

CLEAN_CHUNK_SIZE = 500_000

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
    """Parse dates, keep years 2016..2023, drop critical NAs, cast categories."""
    df = base_preprocess_datetime(
        df,
        apply_outliers=False,
    )
    if "year" in df.columns:
        df = df[df["year"].between(2016, 2023)]
    df = df.dropna(subset=["Start_Time", "Severity", "City"])
    df = object_columns_to_category(df, columns=["City", "Weather_Condition"])
    return df

def _load_clean_csv() -> pd.DataFrame:
    dtype = {
        "ID": "string",
        "Severity": "int8",
        "Start_Lat": "float32",
        "Start_Lng": "float32",
        "Distance(mi)": "float32",
        "City": "category",
        "County": "category",
        "State": "category",
        "Country": "category",
        "Weather_Condition": "category",
        "Street": "string",
        "Description": "string",
        "Sunrise_Sunset": "category",
    }
    return pd.read_csv(
        EXTERNAL_CLEAN_CSV,
        parse_dates=["Start_Time"],
        dtype={k: v for k, v in dtype.items() if k in KEEP_COLS},
        low_memory=False,
    )


def build_clean_to_parent() -> pd.DataFrame:
    """ETL -> save cleaned CSV at ..\\accidents_clean\\US_Accidents_March23_clean.csv, return cleaned df."""
    raw_path = _find_raw_csv()
    os.makedirs(EXTERNAL_PROCESSED_DIR, exist_ok=True)
    if os.path.exists(EXTERNAL_CLEAN_CSV):
        os.remove(EXTERNAL_CLEAN_CSV)

    total_rows = 0
    first_chunk = True
    reader = pd.read_csv(
        raw_path,
        usecols=lambda c: c in KEEP_COLS,
        on_bad_lines="skip",
        low_memory=False,
        chunksize=CLEAN_CHUNK_SIZE,
    )
    for chunk_number, chunk in enumerate(reader, start=1):
        df_clean = _etl_clean_dataframe(chunk)
        total_rows += len(df_clean)
        df_clean.to_csv(EXTERNAL_CLEAN_CSV, mode="a", header=first_chunk, index=False)
        first_chunk = False
        print(f"[ETL] Processed chunk {chunk_number:,}; cleaned rows so far: {total_rows:,}")

    print(f"[ETL] Cleaned dataset saved to:\n  {EXTERNAL_CLEAN_CSV}")
    return _load_clean_csv()

def load_external_clean_or_build() -> pd.DataFrame:
    if os.path.exists(EXTERNAL_CLEAN_CSV):
        return _load_clean_csv()
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
