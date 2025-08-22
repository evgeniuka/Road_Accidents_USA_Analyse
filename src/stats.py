# src/stats.py
import pandas as pd

def chi2_bulk_severe_vs_common_factors(df: pd.DataFrame, alpha: float = 0.05) -> None:
    """Runs chi-square: is_severe × each common factor (no prompts)."""
    import src.analysis as analysis
    d = analysis.ensure_features(df)

    factors = [
        "is_weekend", "is_night", "is_rush_hour",
        "has_precipitation", "has_bad_weather",
        "is_visibility_low", "is_freezing",
        "has_bump", "has_crossing",
        "wind_speed_bin", "road_type",
    ]

    # try to use SciPy; if not available — fallback to percents
    try:
        from scipy.stats import chi2_contingency
        have_scipy = True
    except Exception:
        have_scipy = False
        print("Tip: to see p-values, install once:  pip install scipy")

    for f in factors:
        print(f"\n=== is_severe × {f} ===")
        if f not in d.columns:
            print("(skip) column not found")
            continue

        ct = pd.crosstab(d["is_severe"], d[f], dropna=False)

        # 1) выбросить пустые строки/столбцы (сумма = 0)
        ct = ct.loc[ct.sum(axis=1) > 0, ct.sum(axis=0) > 0]

        print("Observed counts:\n", ct)

        # 2) если после чистки нет как минимум 2x2 — показать проценты и дальше
        if ct.shape[0] < 2 or ct.shape[1] < 2 or not have_scipy:
            perc = (ct.T / ct.T.sum()).T.fillna(0) * 100
            print("Row-wise percentages (%):\n", perc.round(2))
            continue

        # 3) χ² (Yates для 2x2)
        use_yates = (ct.shape == (2, 2))
        chi2, p, dof, _ = chi2_contingency(ct.values, correction=use_yates)
        v = _cramers_v(chi2, ct)
        p_str = f"{p:.6f}" if p >= 1e-6 else "< 1e-6"
        print(f"chi2={chi2:.3f}, dof={dof}, p-value={p_str}  (Yates={use_yates})")
        print(f"Cramer's V={v:.3f}")
        print("Result:", "REJECT H0 (dependence)" if p <= 0.05 else "Fail to reject H0 (no evidence)")

        print(f"chi2={chi2:.3f}, dof={dof}, p-value={p:.6f}  (Yates={use_yates})")
        print("Result:", "REJECT H0 (dependence)" if p <= alpha else "Fail to reject H0 (no evidence)")

def _cramers_v(chi2, ct):
    n = ct.values.sum()
    r, c = ct.shape
    k = min(r, c) - 1
    if n == 0 or k <= 0:
        return float("nan")
    return (chi2 / (n * k)) ** 0.5
