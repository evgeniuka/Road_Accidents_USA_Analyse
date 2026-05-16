from __future__ import annotations

import html
import os
from pathlib import Path

import numpy as np
import pandas as pd

import matplotlib

if not os.getenv("MPLBACKEND"):
    matplotlib.use("Agg")

import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.ticker import FuncFormatter

from src import analysis
from src.preprocessing import parse_datetime_series


VALID_US_STATES = {
    "AL", "AK", "AZ", "AR", "CA", "CO", "CT", "DE", "FL", "GA",
    "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MD",
    "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ",
    "NM", "NY", "NC", "ND", "OH", "OK", "OR", "PA", "RI", "SC",
    "SD", "TN", "TX", "UT", "VT", "VA", "WA", "WV", "WI", "WY",
    "DC",
}

PALETTE = {
    "blue": "#245b7a",
    "coral": "#d96c5f",
    "green": "#4f8f7b",
    "gold": "#d8a33f",
    "ink": "#263238",
    "muted": "#7d8994",
    "light": "#eef3f6",
}


def generate_portfolio_report(
    df: pd.DataFrame,
    output_dir: Path | str = "reports",
    source_label: str = "loaded dataset",
) -> dict[str, Path]:
    """Export a GitHub-friendly report layer from the loaded accidents dataset."""
    output_dir = Path(output_dir)
    figures_dir = output_dir / "figures"
    tables_dir = output_dir / "tables"
    figures_dir.mkdir(parents=True, exist_ok=True)
    tables_dir.mkdir(parents=True, exist_ok=True)

    d = analysis.ensure_features(df)

    metrics = portfolio_metrics(d)
    quality = data_quality_summary(d)
    yearly = analysis.kpi_by_year_all(d)
    top_cities = top_cities_table(d, n=10)
    feature_lift = feature_severity_lift(d)
    hour_day = hour_day_heatmap_table(d)

    yearly.rename(columns={"severe_share": "high_severity_share"}).to_csv(tables_dir / "yearly_kpis.csv", index=False)
    top_cities.to_csv(tables_dir / "top_cities.csv", index=False)
    feature_lift.to_csv(tables_dir / "feature_severity_lift.csv", index=False)
    hour_day.to_csv(tables_dir / "hour_day_heatmap.csv")
    quality.to_csv(tables_dir / "data_quality_summary.csv", index=False)

    figure_paths = {
        "overview": figures_dir / "overview_kpis.png",
        "severity": figures_dir / "severity_distribution.png",
        "top_cities": figures_dir / "top_cities.png",
        "yearly": figures_dir / "yearly_trend.png",
        "time_heatmap": figures_dir / "time_heatmap.png",
        "context": figures_dir / "severity_by_context.png",
        "map": figures_dir / "accident_locations.png",
    }

    save_overview_figure(metrics, figure_paths["overview"])
    save_severity_distribution(d, figure_paths["severity"])
    save_top_cities_figure(top_cities, figure_paths["top_cities"])
    save_yearly_trend_figure(yearly, figure_paths["yearly"], metrics.get("coverage_note", ""))
    save_time_heatmap(hour_day, figure_paths["time_heatmap"])
    save_context_lift_figure(feature_lift, figure_paths["context"])
    save_location_map(d, figure_paths["map"])

    markdown_report = output_dir / "portfolio_report.md"
    dashboard_html = output_dir / "dashboard.html"
    write_markdown_report(
        markdown_report,
        source_label=source_label,
        metrics=metrics,
        quality=quality,
        yearly=yearly,
        top_cities=top_cities,
        feature_lift=feature_lift,
    )
    write_dashboard_html(
        dashboard_html,
        source_label=source_label,
        metrics=metrics,
        quality=quality,
        top_cities=top_cities,
        figure_paths=figure_paths,
    )

    return {
        "output_dir": output_dir,
        "figures_dir": figures_dir,
        "tables_dir": tables_dir,
        "markdown_report": markdown_report,
        "dashboard_html": dashboard_html,
    }


def portfolio_metrics(df: pd.DataFrame) -> dict[str, str]:
    parsed_time = parse_datetime_series(df["Start_Time"])
    years = parsed_time.dt.year.dropna()
    min_date = parsed_time.min()
    max_date = parsed_time.max()
    severe_share = df["is_severe"].mean() * 100 if "is_severe" in df else np.nan
    city_counts = df["City"].astype(str).str.title().value_counts() if "City" in df else pd.Series(dtype="int64")
    top_city = city_counts.idxmax() if not city_counts.empty else "N/A"
    top_city_count = int(city_counts.iloc[0]) if not city_counts.empty else 0
    states = df["State"].astype(str).str.upper().nunique() if "State" in df else 0
    partial_note = ""
    if pd.notna(max_date) and (max_date.month, max_date.day) != (12, 31):
        partial_note = f"{int(max_date.year)} is partial through {max_date.date()}."

    return {
        "rows": f"{len(df):,}",
        "period": f"{int(years.min())}-{int(years.max())}" if not years.empty else "unknown",
        "date_range": f"{min_date.date()} to {max_date.date()}" if pd.notna(min_date) and pd.notna(max_date) else "unknown",
        "coverage_note": partial_note,
        "severe_share": f"{severe_share:.1f}%",
        "top_city": f"{top_city} ({top_city_count:,})" if top_city != "N/A" else "N/A",
        "cities": f"{df['City'].nunique():,}" if "City" in df else "0",
        "states": f"{states:,}",
    }


def data_quality_summary(df: pd.DataFrame) -> pd.DataFrame:
    checks = []

    checks.append(("Rows after cleaning", len(df), "Rows available for analysis"))
    checks.append(("Columns after cleaning", df.shape[1], "Columns retained for analysis"))

    if "ID" in df.columns:
        checks.append(("Duplicate IDs", int(df["ID"].duplicated().sum()), "Should be 0"))

    if "Severity" in df.columns:
        severity = pd.to_numeric(df["Severity"], errors="coerce")
        invalid_severity = (~severity.isin([1, 2, 3, 4])).sum()
        checks.append(("Invalid severity values", int(invalid_severity), "Expected values are 1-4"))

    if "State" in df.columns:
        states = df["State"].astype(str).str.upper()
        invalid_states = (~states.isin(VALID_US_STATES)).sum()
        checks.append(("Rows with invalid state code", int(invalid_states), "Useful for catching shifted CSV fields"))

    if "Country" in df.columns:
        country = df["Country"].astype(str).str.upper()
        invalid_country = (country != "US").sum()
        checks.append(("Rows with non-US country value", int(invalid_country), "Usually a parsing or sample-quality issue"))

    if {"Start_Lat", "Start_Lng"}.issubset(df.columns):
        lat = pd.to_numeric(df["Start_Lat"], errors="coerce")
        lng = pd.to_numeric(df["Start_Lng"], errors="coerce")
        invalid_geo = (~(lat.between(24, 50) & lng.between(-125, -66))).sum()
        checks.append(("Rows outside continental-US coordinate bounds", int(invalid_geo), "Loose coordinate sanity check"))

    missing = df.isna().mean().sort_values(ascending=False).head(8)
    for col, pct in missing.items():
        if pct > 0:
            checks.append((f"Missing values: {col}", f"{pct * 100:.1f}%", "Top missing-value columns"))

    return pd.DataFrame(checks, columns=["check", "value", "note"])


def top_cities_table(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    return (
        df["City"]
        .astype(str)
        .str.title()
        .value_counts()
        .head(n)
        .rename_axis("city")
        .reset_index(name="accidents")
    )


def feature_severity_lift(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    columns = [
        "feature", "segment", "accidents", "severe_share_pct",
        "baseline_severe_share_pct", "lift_pct",
    ]
    feature_labels = {
        "road_type": "Road type",
        "is_weekend": "Weekend",
        "is_night": "Night",
        "is_rush_hour": "Rush hour",
        "has_precipitation": "Precipitation",
        "has_bad_weather": "Bad weather",
        "is_visibility_low": "Low visibility",
        "is_freezing": "Freezing",
        "has_crossing": "Crossing",
        "wind_speed_bin": "Wind speed bin",
    }
    for feature, label in feature_labels.items():
        if feature not in df.columns:
            continue
        table, base = analysis.corr_show(df, feature)
        for _, row in table.iterrows():
            rows.append(
                {
                    "feature": label,
                    "segment": _segment_label(feature, row[feature]),
                    "accidents": int(row["count"]),
                    "severe_share_pct": round(row["share"] * 100, 1),
                    "baseline_severe_share_pct": round(base * 100, 1),
                    "lift_pct": round(row["delta_pct"], 1),
                }
            )
    if not rows:
        return pd.DataFrame(columns=columns)
    return pd.DataFrame(rows, columns=columns).sort_values(
        ["severe_share_pct", "accidents"], ascending=[False, False]
    )


def _segment_label(feature: str, value) -> str:
    text = str(value)
    if feature in {
        "is_weekend", "is_night", "is_rush_hour", "has_precipitation",
        "has_bad_weather", "is_visibility_low", "is_freezing", "has_crossing",
    }:
        try:
            return "Yes" if float(value) >= 0.5 else "No"
        except (TypeError, ValueError):
            return text
    if feature == "wind_speed_bin":
        return {
            "0": "0-7 mph",
            "1": "7-15 mph",
            "2": "15-25 mph",
            "3": "25+ mph",
            "nan": "Unknown",
            "NA": "Unknown",
        }.get(text, text)
    if feature == "road_type":
        return text.title()
    return text


def hour_day_heatmap_table(df: pd.DataFrame) -> pd.DataFrame:
    d = df.copy()
    dt = parse_datetime_series(d["Start_Time"])
    d = d.loc[dt.notna()].copy()
    d["hour"] = dt.loc[d.index].dt.hour
    d["day"] = dt.loc[d.index].dt.day_name()
    order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    table = (
        d.pivot_table(index="day", columns="hour", values="Severity", aggfunc="size", fill_value=0)
        .reindex(order)
        .fillna(0)
    )
    table.columns = [int(c) for c in table.columns]
    return table


def _format_axis(ax) -> None:
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.spines["left"].set_color("#d0d7de")
    ax.spines["bottom"].set_color("#d0d7de")
    ax.tick_params(colors=PALETTE["ink"])
    ax.title.set_color(PALETTE["ink"])
    ax.xaxis.label.set_color(PALETTE["ink"])
    ax.yaxis.label.set_color(PALETTE["ink"])


def _count_formatter(value, _position) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.0f}k"
    return f"{int(value)}"


def _save(fig: plt.Figure, path: Path) -> None:
    fig.tight_layout()
    fig.savefig(path, dpi=180, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def save_overview_figure(metrics: dict[str, str], path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 4.5))
    ax.axis("off")
    items = [
        ("Rows", metrics["rows"]),
        ("Period", metrics["period"]),
        ("High-severity", metrics["severe_share"]),
        ("Top city", metrics["top_city"]),
        ("Cities", metrics["cities"]),
    ]
    for i, (label, value) in enumerate(items):
        x = (i % 5) / 5
        ax.text(x + 0.02, 0.68, value, fontsize=20, weight="bold", color=PALETTE["ink"], transform=ax.transAxes)
        ax.text(x + 0.02, 0.48, label.upper(), fontsize=9, color=PALETTE["muted"], transform=ax.transAxes)
        ax.add_patch(
            plt.Rectangle(
                (x, 0.35),
                0.18,
                0.45,
                fill=False,
                edgecolor="#d9e2e8",
                linewidth=1,
                transform=ax.transAxes,
            )
        )
    ax.text(
        0,
        0.12,
        "Descriptive analysis only; severity is dataset-defined traffic impact, not injury outcome.",
        fontsize=11,
        color=PALETTE["muted"],
        transform=ax.transAxes,
    )
    _save(fig, path)


def save_severity_distribution(df: pd.DataFrame, path: Path) -> None:
    counts = (
        pd.to_numeric(df["Severity"], errors="coerce")
        .value_counts()
        .sort_index()
        .rename_axis("severity")
        .reset_index(name="accidents")
    )
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.bar(counts["severity"].astype(str), counts["accidents"], color=PALETTE["coral"])
    ax.set_title("Accident severity distribution")
    ax.set_xlabel("Severity")
    ax.set_ylabel("Accidents")
    for i, row in counts.iterrows():
        ax.text(i, row["accidents"], f"{int(row['accidents']):,}", ha="center", va="bottom", fontsize=9)
    _format_axis(ax)
    _save(fig, path)


def save_top_cities_figure(top_cities: pd.DataFrame, path: Path) -> None:
    data = top_cities.sort_values("accidents")
    fig, ax = plt.subplots(figsize=(9, 6))
    ax.barh(data["city"], data["accidents"], color=PALETTE["blue"])
    ax.set_title("Top cities by accident count")
    ax.set_xlabel("Accidents")
    ax.set_ylabel("")
    for _, row in data.iterrows():
        ax.text(row["accidents"], row["city"], f" {int(row['accidents']):,}", va="center", fontsize=9)
    _format_axis(ax)
    _save(fig, path)


def save_yearly_trend_figure(yearly: pd.DataFrame, path: Path, coverage_note: str = "") -> None:
    fig, ax1 = plt.subplots(figsize=(9, 5))
    ax1.bar(yearly["year"].astype(str), yearly["accidents"], color=PALETTE["green"], label="Accidents")
    ax1.set_ylabel("Accidents")
    ax1.set_xlabel("Year")
    ax1.set_title("Accidents and high-severity share by year")
    ax1.yaxis.set_major_formatter(FuncFormatter(_count_formatter))
    ax2 = ax1.twinx()
    ax2.plot(yearly["year"].astype(str), yearly["severe_share"], color=PALETTE["coral"], marker="o", linewidth=2.5, label="High-severity share")
    ax2.set_ylabel("High-severity share (%)")
    _format_axis(ax1)
    ax2.spines["top"].set_visible(False)
    ax2.spines["right"].set_color("#d0d7de")
    ax2.tick_params(colors=PALETTE["ink"])
    ax2.yaxis.label.set_color(PALETTE["ink"])
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, frameon=False, loc="upper right")
    if coverage_note:
        ax1.text(
            0,
            -0.18,
            coverage_note,
            transform=ax1.transAxes,
            fontsize=9,
            color=PALETTE["muted"],
        )
    _save(fig, path)


def save_time_heatmap(hour_day: pd.DataFrame, path: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.5))
    sns.heatmap(
        hour_day,
        cmap=sns.light_palette(PALETTE["blue"], as_cmap=True),
        linewidths=0.2,
        linecolor="white",
        cbar_kws={"label": "Accidents"},
        ax=ax,
    )
    ax.set_title("Accidents by day of week and hour")
    ax.set_xlabel("Hour of day")
    ax.set_ylabel("")
    _save(fig, path)


def save_context_lift_figure(feature_lift: pd.DataFrame, path: Path) -> None:
    data = feature_lift[(feature_lift["accidents"] >= 20) & (feature_lift["lift_pct"] > 0)].head(10).copy()
    if data.empty:
        data = feature_lift[feature_lift["accidents"] >= 20].head(10).copy()
    if data.empty:
        fig, ax = plt.subplots(figsize=(10, 6.5))
        ax.axis("off")
        ax.text(0.5, 0.5, "No context segments available.", ha="center", va="center")
        _save(fig, path)
        return
    data["label"] = data["feature"] + ": " + data["segment"]
    data = data.sort_values("severe_share_pct")
    fig, ax = plt.subplots(figsize=(10, 6.5))
    colors = np.where(data["lift_pct"] >= 0, PALETTE["coral"], PALETTE["blue"])
    ax.barh(data["label"], data["severe_share_pct"], color=colors)
    ax.axvline(data["baseline_severe_share_pct"].iloc[0], color=PALETTE["ink"], linestyle="--", linewidth=1)
    ax.set_title("Segments with the highest high-severity share")
    ax.set_xlabel("High-severity share (%)")
    ax.set_ylabel("")
    for _, row in data.iterrows():
        ax.text(row["severe_share_pct"], row["label"], f" {row['severe_share_pct']:.1f}%", va="center", fontsize=9)
    _format_axis(ax)
    _save(fig, path)


def save_location_map(df: pd.DataFrame, path: Path) -> None:
    if not {"Start_Lat", "Start_Lng"}.issubset(df.columns):
        fig, ax = plt.subplots(figsize=(9, 5))
        ax.axis("off")
        ax.text(0.5, 0.5, "Latitude/longitude columns are not available.", ha="center", va="center")
        _save(fig, path)
        return

    geo = df.copy()
    geo["Start_Lat"] = pd.to_numeric(geo["Start_Lat"], errors="coerce")
    geo["Start_Lng"] = pd.to_numeric(geo["Start_Lng"], errors="coerce")
    geo = geo.dropna(subset=["Start_Lat", "Start_Lng", "Severity"])
    sampled = False
    if len(geo) > 120_000:
        geo = geo.sample(120_000, random_state=42)
        sampled = True
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = geo["is_severe"].map({1: PALETTE["coral"], 0: PALETTE["blue"]}).fillna(PALETTE["muted"])
    ax.scatter(geo["Start_Lng"], geo["Start_Lat"], s=10, c=colors, alpha=0.35, linewidths=0)
    ax.set_title("Accident locations in the sample")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_xlim(-125, -66)
    ax.set_ylim(24, 50)
    ax.text(
        0.01,
        0.02,
        "Coral = Severity >= 3" + ("; map sampled to 120k rows" if sampled else ""),
        transform=ax.transAxes,
        fontsize=9,
        color=PALETTE["muted"],
    )
    _format_axis(ax)
    _save(fig, path)


def write_markdown_report(
    path: Path,
    *,
    source_label: str,
    metrics: dict[str, str],
    quality: pd.DataFrame,
    yearly: pd.DataFrame,
    top_cities: pd.DataFrame,
    feature_lift: pd.DataFrame,
) -> None:
    strongest = feature_lift[feature_lift["accidents"] >= 20].head(5)
    quality_rows = "\n".join(
        f"- {row.check}: {_format_report_value(row.value)} ({row.note})" for row in quality.itertuples(index=False)
    )
    city_rows = "\n".join(
        f"- {row.city}: {int(row.accidents):,}" for row in top_cities.head(5).itertuples(index=False)
    )
    lift_rows = "\n".join(
        f"- {row.feature} / {row.segment}: {row.severe_share_pct:.1f}% high-severity, {int(row.accidents):,} accidents"
        for row in strongest.itertuples(index=False)
    )
    yearly_md = _format_yearly_markdown(yearly)

    path.write_text(
        f"""# US Road Accidents Portfolio Report

This report is generated from the {source_label}. The exported charts and tables make the analysis reviewable on GitHub without opening Python.

## Executive Snapshot

- Rows analyzed: {metrics["rows"]}
- Period covered: {metrics["period"]}
- Date range: {metrics["date_range"]}
- High-severity record share: {metrics["severe_share"]}
- Most frequent city: {metrics["top_city"]}
- Cities represented: {metrics["cities"]}
{f'- Coverage note: {metrics["coverage_note"]}' if metrics["coverage_note"] else ''}

![Portfolio KPI overview](figures/overview_kpis.png)

## Key Visuals

![Accidents and high-severity share by year](figures/yearly_trend.png)

![Top cities by accident count](figures/top_cities.png)

![Accidents by day of week and hour](figures/time_heatmap.png)

![Segments by high-severity share](figures/severity_by_context.png)

![Accident locations](figures/accident_locations.png)

## Key Findings

Top cities in the analyzed dataset:

{city_rows}

Highest high-severity segments with at least 20 accidents:

{lift_rows}

Yearly KPI table:

{yearly_md}

## Data Quality Notes

{quality_rows}

## Method Notes

- `Severity >= 3` is used as a high-severity proxy from the dataset, not as a confirmed injury or fatality outcome.
- Counts by city are raw accident records and are not normalized by population, vehicle miles traveled, road length, or reporting coverage.
- The analysis is descriptive and should not be read as causal.
{f'- {metrics["coverage_note"]}' if metrics["coverage_note"] else ''}

## Reviewer Notes

The repository includes a small bundled sample for quick review. The full analysis can be regenerated when `US_Accidents_March23.csv` is available in `data/raw/` or `../dataset/`.
""",
        encoding="utf-8",
    )


def _format_report_value(value) -> str:
    if isinstance(value, (int, np.integer)):
        return f"{int(value):,}"
    return str(value)


def _format_yearly_markdown(yearly: pd.DataFrame) -> str:
    display = yearly.rename(columns={"severe_share": "high_severity_share"}).copy()
    if "accidents" in display.columns:
        display["accidents"] = display["accidents"].map(lambda x: f"{int(x):,}")
    for col in ["high_severity_share", "avg_severity", "weekend_share", "precip_share", "bad_weather_share"]:
        if col in display.columns:
            display[col] = display[col].map(lambda x: f"{x:g}")
    return display.to_markdown(index=False)


def write_dashboard_html(
    path: Path,
    *,
    source_label: str,
    metrics: dict[str, str],
    quality: pd.DataFrame,
    top_cities: pd.DataFrame,
    figure_paths: dict[str, Path],
) -> None:
    cards = "".join(
        f"<section class='metric'><span>{html.escape(label)}</span><strong>{html.escape(value)}</strong></section>"
        for label, value in [
            ("Rows", metrics["rows"]),
            ("Period", metrics["period"]),
            ("High-Severity Share", metrics["severe_share"]),
            ("Top City", metrics["top_city"]),
            ("Cities", metrics["cities"]),
        ]
    )
    coverage_note = (
        f"<p class='note'>{html.escape(metrics['coverage_note'])}</p>"
        if metrics.get("coverage_note") else ""
    )
    city_rows = "".join(
        f"<tr><td>{html.escape(row.city)}</td><td>{int(row.accidents):,}</td></tr>"
        for row in top_cities.head(8).itertuples(index=False)
    )
    quality_rows = "".join(
        f"<tr><td>{html.escape(str(row.check))}</td><td>{html.escape(str(row.value))}</td><td>{html.escape(str(row.note))}</td></tr>"
        for row in quality.itertuples(index=False)
    )
    fig = {name: f"figures/{p.name}" for name, p in figure_paths.items()}

    path.write_text(
        f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>US Road Accidents Dashboard</title>
  <style>
    :root {{
      --ink: #263238;
      --muted: #687782;
      --line: #d9e2e8;
      --panel: #ffffff;
      --bg: #f5f7f8;
      --blue: #245b7a;
      --coral: #d96c5f;
      --green: #4f8f7b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: Inter, Segoe UI, Arial, sans-serif;
      background: var(--bg);
      color: var(--ink);
    }}
    header {{
      padding: 34px clamp(18px, 4vw, 56px) 18px;
      background: #ffffff;
      border-bottom: 1px solid var(--line);
    }}
    h1 {{ margin: 0 0 8px; font-size: clamp(28px, 4vw, 44px); letter-spacing: 0; }}
    p {{ margin: 0; color: var(--muted); line-height: 1.55; }}
    .note {{ margin-top: 8px; font-weight: 600; color: var(--coral); }}
    main {{
      width: min(1180px, calc(100% - 32px));
      margin: 24px auto 48px;
    }}
    .metrics {{
      display: grid;
      grid-template-columns: repeat(5, minmax(150px, 1fr));
      gap: 12px;
      margin-bottom: 18px;
    }}
    .metric, .panel {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
    }}
    .metric {{ padding: 16px; min-height: 94px; }}
    .metric span {{
      display: block;
      color: var(--muted);
      font-size: 12px;
      text-transform: uppercase;
      margin-bottom: 8px;
    }}
    .metric strong {{ font-size: 22px; line-height: 1.15; }}
    .grid {{
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 18px;
      align-items: start;
    }}
    .panel {{ padding: 18px; overflow: hidden; }}
    .panel.wide {{ grid-column: 1 / -1; }}
    h2 {{ margin: 0 0 14px; font-size: 18px; }}
    img {{ width: 100%; display: block; border-radius: 6px; border: 1px solid var(--line); }}
    table {{ width: 100%; border-collapse: collapse; font-size: 14px; }}
    th, td {{ padding: 9px 8px; border-bottom: 1px solid var(--line); text-align: left; }}
    th {{ color: var(--muted); font-weight: 600; }}
    footer {{ color: var(--muted); font-size: 13px; padding: 8px 0 0; }}
    @media (max-width: 900px) {{
      .metrics, .grid {{ grid-template-columns: 1fr; }}
      .metric strong {{ font-size: 20px; }}
    }}
  </style>
</head>
<body>
  <header>
    <h1>US Road Accidents Dashboard</h1>
    <p>Generated from the {html.escape(source_label)}. Built to make the analysis reviewable without opening Python.</p>
    {coverage_note}
  </header>
  <main>
    <section class="metrics">{cards}</section>
    <section class="grid">
      <article class="panel wide">
        <h2>Yearly trend</h2>
        <img src="{fig['yearly']}" alt="Accidents and high-severity share by year">
      </article>
      <article class="panel">
        <h2>Top cities</h2>
        <img src="{fig['top_cities']}" alt="Top cities by accident count">
      </article>
      <article class="panel">
        <h2>Severity distribution</h2>
        <img src="{fig['severity']}" alt="Severity distribution">
      </article>
      <article class="panel wide">
        <h2>Time heatmap</h2>
        <img src="{fig['time_heatmap']}" alt="Accidents by weekday and hour">
      </article>
      <article class="panel wide">
        <h2>Context high-severity lift</h2>
        <img src="{fig['context']}" alt="Segments by high-severity share">
      </article>
      <article class="panel wide">
        <h2>Location overview</h2>
        <img src="{fig['map']}" alt="Accident locations">
      </article>
      <article class="panel">
        <h2>Top city table</h2>
        <table><thead><tr><th>City</th><th>Accidents</th></tr></thead><tbody>{city_rows}</tbody></table>
      </article>
      <article class="panel">
        <h2>Data quality checks</h2>
        <table><thead><tr><th>Check</th><th>Value</th><th>Note</th></tr></thead><tbody>{quality_rows}</tbody></table>
      </article>
    </section>
    <footer>Sample insights are descriptive and should not be treated as causal conclusions.</footer>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )
