import pandas as pd


def chi2_bulk_severe_vs_common_factors(df: pd.DataFrame, alpha: float = 0.05) -> None:
    """Run chi-square checks between severity and common accident factors."""
    import src.analysis as analysis

    d = analysis.ensure_features(df)
    factors = [
        "is_weekend", "is_night", "is_rush_hour",
        "has_precipitation", "has_bad_weather",
        "is_visibility_low", "is_freezing",
        "has_bump", "has_crossing",
        "wind_speed_bin", "road_type",
    ]

    try:
        from scipy.stats import chi2_contingency
        have_scipy = True
    except Exception:
        have_scipy = False
        print("Tip: to see p-values, install once:  pip install scipy")

    for factor in factors:
        print(f"\n=== is_severe x {factor} ===")
        if factor not in d.columns:
            print("(skip) column not found")
            continue

        ct = pd.crosstab(d["is_severe"], d[factor], dropna=False)
        ct = ct.loc[ct.sum(axis=1) > 0, ct.sum(axis=0) > 0]
        print("Observed counts:\n", ct)

        if ct.shape[0] < 2 or ct.shape[1] < 2 or not have_scipy:
            perc = (ct.T / ct.T.sum()).T.fillna(0) * 100
            print("Row-wise percentages (%):\n", perc.round(2))
            continue

        use_yates = ct.shape == (2, 2)
        chi2, p_value, dof, _ = chi2_contingency(ct.values, correction=use_yates)
        cramers = _cramers_v(chi2, ct)
        p_label = f"{p_value:.6f}" if p_value >= 1e-6 else "< 1e-6"

        print(f"chi2={chi2:.3f}, dof={dof}, p-value={p_label}  (Yates={use_yates})")
        print(f"Cramer's V={cramers:.3f}")
        print("Result:", "REJECT H0 (dependence)" if p_value <= alpha else "Fail to reject H0 (no evidence)")


def _cramers_v(chi2: float, ct: pd.DataFrame) -> float:
    n = ct.values.sum()
    rows, cols = ct.shape
    k = min(rows, cols) - 1
    if n == 0 or k <= 0:
        return float("nan")
    return (chi2 / (n * k)) ** 0.5
