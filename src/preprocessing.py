import pandas as pd


def parse_datetime_series(series: pd.Series) -> pd.Series:
    """Parse mixed timestamp formats used by the US Accidents CSV."""
    return pd.to_datetime(series, errors="coerce", format="mixed")


def parse_dates(df: pd.DataFrame, col: str = 'Start_Time') -> pd.DataFrame:
    if col in df.columns and not pd.api.types.is_datetime64_any_dtype(df[col]):
        df[col] = parse_datetime_series(df[col])
    df = df.dropna(subset=[col])
    df['year'] = df[col].dt.year
    df['date'] = df[col].dt.date
    return df

def remove_outliers_basic(df, cols=None):
    if cols is None:
        return remove_outliers_iqr_entire_df(df)
    for c in cols:
        if c in df.columns:
            df = remove_outliers_iqr_col(df, c)
    return df


def base_preprocess_datetime(
    df,
    time_col: str = "Start_Time",
    apply_outliers: bool = True,
    outlier_cols=None,
):
    """
    Parse datetime column, add 'year' and 'date', optionally trim extreme outliers.
    Safe assignments to avoid SettingWithCopyWarning.
    """
    import numpy as np
    import pandas as pd

    d = df.copy()

    # datetime
    d[time_col] = parse_datetime_series(d[time_col])
    d = d.dropna(subset=[time_col]).reset_index(drop=True)

    d.loc[:, "year"] = d[time_col].dt.year
    d.loc[:, "date"] = d[time_col].dt.date

    if apply_outliers and outlier_cols:
        for c in outlier_cols:
            if c in d.columns:
                x = pd.to_numeric(d[c], errors="coerce")
                lo, hi = x.quantile(0.001), x.quantile(0.999)
                d = d[(x >= lo) & (x <= hi) | x.isna()]

    return d


def remove_outliers_iqr_entire_df(df):
    numeric_cols = df.select_dtypes(include='number').columns
    for col in numeric_cols:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
    return df


def remove_outliers_iqr_col(df, col):
    Q1 = df[col].quantile(0.25)
    Q3 = df[col].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR
    df = df[(df[col] >= lower_bound) & (df[col] <= upper_bound)]
    return df


def set_index_starting_from_one(df: pd.DataFrame) -> pd.DataFrame:
    df.index = range(1, len(df) + 1)
    return df


def object_columns_to_category(df: pd.DataFrame, columns=None) -> pd.DataFrame:
    df_processed = df.copy()
    if columns is None:
        for col in df_processed.select_dtypes(include='object'):
            df_processed[col] = df_processed[col].str.lower().astype('category')
    else:
        for col in columns:
            df_processed[col] = df_processed[col].str.lower().astype('category')
    return df_processed
