import re
import numpy as np
import pandas as pd
import src.visualization as visualization
import src.preprocessing as prepro
import src.constants as consts
import src.preprocessing as prepro
import src.visualization as visualization
from src.preprocessing import object_columns_to_category


def correlation_overview(df):
    if df is None or df.empty:
        print('\n[Heatmap] No data after filtering. Load more rows or disable last-year drop.')
        return None

    need = {
        "is_severe","is_weekend","is_night","is_rush_hour",
        "has_precipitation","has_bad_weather","is_visibility_low",
        "is_freezing","has_bump","has_crossing","road_type","wind_speed_bin",
    }
    if not need.issubset(df.columns):
        from src.analysis import feat
        df = feat(df)

    for c in ["is_weekend", "wind_speed_bin", "is_freezing", "road_type", "has_precipitation"]:
        if c in df.columns:
            show(df, c)
        else:
            print(f"(skip) {c} — column not found")

    num = [
        "Severity", "is_severe", "is_night", "is_rush_hour",
        "has_precipitation", "has_bad_weather", "is_visibility_low",
        "is_weekend", "is_freezing", "has_bump", "has_crossing",
    ]
    use_num = [c for c in num if c in df.columns]

    cat = [c for c in ["road_type", "wind_speed_bin"] if c in df.columns]
    if cat:
        X = pd.get_dummies(df[cat], drop_first=True, dtype="int8")
    else:
        X = pd.DataFrame(index=df.index)

    data = pd.concat([df[use_num].astype("float32", copy=False), X.astype("float32", copy=False)], axis=1)
    nuniq = data.nunique(dropna=True)
    const_cols = nuniq[nuniq < 2].index.tolist()
    if const_cols:
        print("(skip) constant columns (no variation):", ", ".join(const_cols))
        data = data.drop(columns=const_cols, errors="ignore")

    if data.shape[1] == 0:
        print("(skip) all selected columns are constant")
        return

    if data.shape[1] == 0:
        print("(skip) nothing to correlate")
        return None

    corr = data.corr(numeric_only=True)
    visualization.plot_corr(corr)
    return corr


def count_by_cities(df: pd.DataFrame, num_rows=consts.NUM_ROWS, cities=None) -> pd.DataFrame:
    if cities is None:
        df_processed = df['City'].value_counts().head(num_rows).reset_index()
        df_processed.columns = ['City', 'NumOfAccidents']
    else:
        df_processed = df[df['City'].isin(cities)].groupby('City')['City'].count().head(num_rows).sort_values(by='City', ascending=False)
        df_processed.columns = ['City', 'NumOfAccidents']
    prepro.set_index_starting_from_one(df_processed)
    return df_processed

# def count_by_cities(df: pd.DataFrame, num_rows=consts.NUM_ROWS, cities=None) -> pd.DataFrame:
#     if cities is None:
#         out = (df['City'].value_counts()
#                .head(num_rows)
#                .rename_axis('City')
#                .reset_index(name='NumOfAccidents'))
#         prepro.set_index_starting_from_one(out)
#         return out
#     tmp = df[df['City'].isin(cities)]
#     out = (tmp.groupby('City', observed=True)['City']
#            .size()
#            .rename('NumOfAccidents')
#            .reset_index()
#            .sort_values('NumOfAccidents', ascending=False)
#            .head(num_rows))
#     prepro.set_index_starting_from_one(out)
#     return out


def feat(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()

    # --- базовые поля ---
    d["Start_Time"] = pd.to_datetime(d["Start_Time"], errors="coerce")
    d["Severity"] = pd.to_numeric(d["Severity"], errors="coerce")
    d = d.dropna(subset=["Start_Time", "Severity"]).reset_index(drop=True)

    d["hour"] = d["Start_Time"].dt.hour
    d["day_of_week"] = d["Start_Time"].dt.dayofweek
    d["year"] = d["Start_Time"].dt.year
    d["date"] = d["Start_Time"].dt.date

    # --- бинарные признаки времени ---
    d["is_night"] = ((d["hour"] >= 20) | (d["hour"] <= 5)).astype(int)
    d["is_rush_hour"] = (d["hour"].between(7, 9) | d["hour"].between(16, 19)).astype(int)
    d["is_weekend"] = (d["day_of_week"] >= 5).astype(int)

    # --- текст погоды (на случай отсутствия чисел) ---
    w_txt = d.get("Weather_Condition")
    w_txt = w_txt.astype("string").str.lower().fillna("") if w_txt is not None else pd.Series("", index=d.index)

    # --- осадки: число ИЛИ текст ---
    num_prec = pd.to_numeric(d["Precipitation(in)"], errors="coerce") if "Precipitation(in)" in d.columns else None
    has_prec_by_num = (num_prec.fillna(0) > 0) if num_prec is not None else pd.Series(False, index=d.index)
    has_prec_by_text = w_txt.str.contains(r"rain|snow|sleet|hail|drizzle|storm|shower", regex=True)
    d["has_precipitation"] = (has_prec_by_num | has_prec_by_text).astype(int)

    # --- «плохая погода» по тексту (шире) ---
    d["has_bad_weather"] = w_txt.str.contains(
        r"rain|snow|fog|mist|thunder|storm|hail|sleet|blizzard|ice|freezing|squall|dust|smoke|haze",
        regex=True
    ).fillna(False).astype(int)

    # --- низкая видимость: нижний 1% чисел ИЛИ текст «туман/дым/пыль» ---
    if "Visibility(mi)" in d.columns:
        vis = pd.to_numeric(d["Visibility(mi)"], errors="coerce")
        if vis.notna().any():
            import numpy as np
            thr_q5 = np.nanpercentile(vis, 5)  # нижние 5%
            thr = max(thr_q5, 1.0)  # не ниже 1 мили как здоровый порог
            low_num = vis <= thr
            low_txt = w_txt.str.contains(r"fog|mist|smoke|haze|squall|dust", regex=True)
            low = (low_num | low_txt)
            # если всё равно получилась одна категория — форсим порог 2 мили
            if low.nunique(dropna=True) < 2:
                low = (vis < 2) | low_txt
            d["is_visibility_low"] = low.fillna(False).astype(int)
        else:
            d["is_visibility_low"] = 0
    else:
        d["is_visibility_low"] = w_txt.str.contains(r"fog|mist|smoke|haze|squall|dust", regex=True).astype(int)
    # --- мороз (по числу) ---
    if "Temperature(F)" in d.columns:
        tnum = pd.to_numeric(d["Temperature(F)"], errors="coerce")
        d["is_freezing"] = (tnum < 32).astype(int)
    else:
        d["is_freezing"] = w_txt.str.contains(r"freez|ice|frost", regex=True).astype(int)

    # --- скорость ветра: бины ---
    wcol = next((c for c in d.columns if "Wind_Speed" in c), None)
    if wcol:
        ws = pd.to_numeric(d[wcol], errors="coerce")
        d["wind_speed_bin"] = pd.cut(ws, [-0.1, 7, 15, 25, np.inf], labels=["0", "1", "2", "3"])
    else:
        d["wind_speed_bin"] = pd.Categorical(["NA"] * len(d))

    # --- тип дороги по тексту улицы/описания ---
    txt = d["Street"].fillna(d.get("Description")).astype(str).str.lower()
    d["road_type"] = txt.map(lambda s:
                             "interstate" if re.search(r"\b(i-|interstate|fwy)\b", s) else
                             ("highway" if re.search(r"\b(hwy|highway|us-|sr-)\b", s) else "local")
                             )

    d["is_severe"] = (d["Severity"] >= 3).astype(int)

    def _to01(s):
        return s.astype(str).str.lower().isin(["true", "1", "yes", "y", "t"]).astype(int)

    d["has_bump"] = _to01(d["Bump"]) if "Bump" in d.columns else 0
    d["has_crossing"] = _to01(d["Crossing"]) if "Crossing" in d.columns else 0
    d = object_columns_to_category(d, columns=["City", "Weather_Condition", "road_type"])

    return d


def ensure_features(df: pd.DataFrame) -> pd.DataFrame:
    need = {
        "is_severe", "is_weekend", "is_night","is_rush_hour",
        "has_precipitation","has_bad_weather","is_visibility_low",
        "has_bump","has_crossing","wind_speed_bin","road_type",
    }
    return df if need.issubset(df.columns) else feat(df)

# ===== Correlation helpers =====

def corr_show(df, feature_col):
    target_col = "is_severe"
    base = df[target_col].mean()
    g = (
        df.groupby(feature_col, observed=True)[target_col]
          .agg(count="size", share="mean")
          .reset_index()
    )
    g["count"] = g["count"].astype(int)
    g["delta_pct"] = (g["share"] / base - 1) * 100
    return g.sort_values("share", ascending=False), base

def show(df, feature_col):
    table, base = corr_show(df, feature_col)
    print(f"\n* {str(feature_col).upper()}  base={base:.3f}")
    for _, row in table.iterrows():
        print(
            f"{str(row[feature_col]):>10}  "
            f"count={int(row['count']):7d}  "
            f"share={row['share']:.3f}  "
            f"diff={row['delta_pct']:+6.1f}%"
        )

def _year_col(df):
    return pd.to_datetime(df['Start_Time'], errors='coerce').dt.year

def kpi_by_year(df: pd.DataFrame, metric: str = 'accidents') -> pd.DataFrame:
    y = pd.to_datetime(df['Start_Time'], errors='coerce').dt.year
    g = df.copy().assign(year=y)

    if metric == 'accidents':
        out = g.groupby('year').size().reset_index(name='accidents')
    elif metric == 'severe_share':
        out = g.groupby('year')['is_severe'].mean().reset_index(name='severe_share')
    elif metric == 'avg_severity':
        out = g.groupby('year')['Severity'].mean().reset_index(name='avg_severity')
    elif metric == 'weekend_share':
        out = g.groupby('year')['is_weekend'].mean().reset_index(name='weekend_share')
    elif metric == 'precip_share':
        out = g.groupby('year')['has_precipitation'].mean().reset_index(name='precip_share')
    elif metric == 'bad_weather_share':
        out = g.groupby('year')['has_bad_weather'].mean().reset_index(name='bad_weather_share')
    else:
        out = g.groupby('year').size().reset_index(name='accidents')

    out = out.dropna()
    if 'year' in out.columns:
        out['year'] = out['year'].astype(int)

    value_col = [c for c in out.columns if c != 'year'][0]
    if value_col.endswith('_share'):
        out[value_col] = (out[value_col] * 100).round(1)  # percent
    elif value_col == 'avg_severity':
        out[value_col] = out[value_col].round(2)

    return out.sort_values('year')


def kpi_by_year_all(df: pd.DataFrame) -> pd.DataFrame:

    y = pd.to_datetime(df['Start_Time'], errors='coerce').dt.year
    g = df.copy().assign(year=y)

    out = (
        g.groupby('year')
         .agg(
             accidents=('Severity', 'size'),
             severe_share=('is_severe', 'mean'),
             avg_severity=('Severity', 'mean'),
             weekend_share=('is_weekend', 'mean'),
             precip_share=('has_precipitation', 'mean'),
             bad_weather_share=('has_bad_weather', 'mean'),
         )
         .reset_index()
    )

    out['year'] = out['year'].astype(int)
    for c in ['severe_share', 'weekend_share', 'precip_share', 'bad_weather_share']:
        out[c] = (out[c] * 100).round(1)
    out['avg_severity'] = out['avg_severity'].round(2)
    return out.sort_values('year')

def kpi_components_by_year(df: pd.DataFrame, scale: int = 10000) -> pd.DataFrame:
    g = df.copy()
    g["year"] = pd.to_datetime(g["Start_Time"], errors="coerce").dt.year
    severe = g.get("is_severe", pd.Series(0, index=g.index)).astype(bool)
    weekend = g.get("is_weekend", pd.Series(0, index=g.index)).astype(bool)
    precip = g.get("has_precipitation", pd.Series(0, index=g.index)).astype(bool)
    bad    = g.get("has_bad_weather", pd.Series(0, index=g.index)).astype(bool)
    bucket_severe = severe
    bucket_weekend = (~bucket_severe) & weekend
    bucket_precip = (~bucket_severe) & (~bucket_weekend) & precip
    bucket_bad    = (~bucket_severe) & (~bucket_weekend) & (~bucket_precip) & bad
    bucket_other  = ~(bucket_severe | bucket_weekend | bucket_precip | bucket_bad)
    parts = pd.DataFrame({
        "year": g["year"],
        "severe": bucket_severe.astype(int),
        "weekend_only": bucket_weekend.astype(int),
        "precip_only": bucket_precip.astype(int),
        "bad_only": bucket_bad.astype(int),
        "other": bucket_other.astype(int),
    })
    agg = parts.groupby("year", as_index=False).sum()
    totals = g.groupby("year", as_index=False).size().rename(columns={"size": "accidents"})
    out = agg.merge(totals, on="year", how="left")
    for c in ["severe", "weekend_only", "precip_only", "bad_only", "other", "accidents"]:
        out[c] = (out[c] / float(scale)).round(2)
    return out.sort_values("year")


def accidents_by_month(df: pd.DataFrame) -> pd.DataFrame:
    """Return accident counts grouped by month (1-12)."""
    months = pd.to_datetime(df["Start_Time"], errors="coerce").dt.month
    out = (df.assign(month=months)
             .groupby("month")
             .size()
             .reset_index(name="accidents")
             .dropna()
             .sort_values("month"))
    out["month"] = out["month"].astype(int)
    return out

def count_by_cities_years(df: pd.DataFrame, num_rows=consts.NUM_ROWS, cities=None, year=2023) -> pd.DataFrame:
    # берём год из df['year'] если есть, иначе парсим
    if "year" in df.columns:
        y = df["year"]
    else:
        y = pd.to_datetime(df["Start_Time"], errors="coerce").dt.year

    tmp = pd.DataFrame({"City": df["City"], "Year": y}).dropna(subset=["City","Year"])
    year = int(year)
    tmp = tmp[tmp["Year"] == year]
    if cities is not None:
        tmp = tmp[tmp["City"].isin(cities)]

    out = (tmp.groupby("City", as_index=False, observed=True)
             .size()
             .rename(columns={"size":"NumOfAccidents"})
             .sort_values("NumOfAccidents", ascending=False)
             .head(num_rows))
    out["Year"] = str(year)
    out = out[["City", "NumOfAccidents", "Year"]]
    prepro.set_index_starting_from_one(out)
    return out



def city_accidents_count_by_year(df: pd.DataFrame, num_rows=consts.NUM_ROWS, city='new york') -> pd.DataFrame:
    tmp = pd.DataFrame({
        "City": df['City'],
        "Year": pd.to_datetime(df['Start_Time'], errors='coerce').dt.year
    }).dropna()
    city = str(city).lower()
    tmp = tmp[tmp['City'].str.lower() == city]
    out = (tmp.groupby('Year', as_index=False)['City']
             .size()
             .rename(columns={'size': 'NumAccidents'}))
    prepro.set_index_starting_from_one(out)
    out['Year'] = out['Year'].astype(str)
    return out


def city_dangerous_streets(df: pd.DataFrame, city: str,  year: int, num_rows=consts.NUM_ROWS) -> pd.DataFrame:

    df_processed = pd.DataFrame({
        "City": df['City'].astype(str),
        "Street": df['Street'],
        "Year": df['Start_Time'].dt.year
    })
    df_processed = df_processed[(df_processed['City'].str.lower() == city) & (df_processed['Year'] == year)]    # Filtering
    df_processed = df_processed.groupby('Street').size().reset_index(name='Accidents')      # Grouping
    df_processed = df_processed.sort_values(by='Accidents', ascending=False)    # Sorting
    df_processed = df_processed.head(num_rows).reset_index(drop=True)     # Leave only certain number of top rows
    prepro.set_index_starting_from_one(df_processed)

    return df_processed

def пeekend(df: pd.DataFrame, alpha: float = 0.05) -> None:
    """Super-simple χ² test: is_severe (Severity>=3) vs is_weekend (Sat/Sun).
    Prints observed/expected tables and conclusion. Requires scipy."""
    import pandas as pd
    try:
        from scipy.stats import chi2_contingency
    except Exception:
        print("SciPy is required. Install once: pip install scipy")
        return

    d = df.copy()
    # Minimal features inline (без лишних зависимостей)
    t = pd.to_datetime(d["Start_Time"], errors="coerce")
    d = d.loc[t.notna()].copy()
    d["is_weekend"] = t.dt.dayofweek.ge(5).astype(int)
    d["is_severe"] = pd.to_numeric(d["Severity"], errors="coerce").ge(3).astype(int)

    # Contingency table
    ct = pd.crosstab(d["is_severe"], d["is_weekend"])
    if ct.shape[0] < 2 or ct.shape[1] < 2:
        print("Not enough variation for chi-square (need at least a 2x2 table).")
        return

    chi2, p, dof, expected = chi2_contingency(ct.values, correction=True)  # Yates for 2x2
    exp_df = pd.DataFrame(expected, index=ct.index, columns=ct.columns)

    print("\n=== Chi-square: is_severe × is_weekend ===")
    print("Observed counts:\n", ct)
    print("\nExpected counts (rounded):\n", exp_df.round(2))
    print(f"\nchi2 = {chi2:.3f}, dof = {dof}, p-value = {p:.6f}")
    decision = "REJECT H0 (dependence)" if p <= alpha else "Fail to reject H0 (no evidence)"
    print(f"Decision at alpha={alpha}: {decision}")