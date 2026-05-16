import argparse
import os
import sys
from pathlib import Path

import pandas as pd

from src.data_loader import load_dataset
from src.preprocessing import parse_datetime_series

try:
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stderr.reconfigure(encoding='utf-8')
except Exception:
    pass
if os.name == 'nt':
    os.system('chcp 65001 > nul')


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Explore and summarize the US road accidents dataset."
    )
    parser.add_argument(
        "--sample",
        action="store_true",
        help="Use the small sample CSV included in the repository.",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print a quick non-interactive summary instead of opening the menu.",
    )
    parser.add_argument(
        "--export-report",
        action="store_true",
        help="Generate portfolio-ready charts, tables, markdown, and an HTML dashboard.",
    )
    parser.add_argument(
        "--output-dir",
        default="reports",
        help="Directory for exported report assets. Defaults to reports/.",
    )
    return parser.parse_args()


def print_summary(df: pd.DataFrame) -> None:
    from src import analysis

    d = analysis.ensure_features(df)
    years = parse_datetime_series(d["Start_Time"]).dt.year
    severe_share = d["is_severe"].mean() * 100

    print("\nUS Road Accidents - quick summary")
    print("-" * 40)
    print(f"Rows analyzed: {len(d):,}")
    print(f"Years covered: {int(years.min())}-{int(years.max())}")
    print(f"High-severity records (Severity >= 3): {severe_share:.1f}%")

    print("\nTop cities:")
    top_cities = d["City"].astype(str).str.title().value_counts().head(5)
    for city, count in top_cities.items():
        print(f"- {city}: {count:,}")

    print("\nAccidents by year:")
    yearly = analysis.kpi_by_year_all(d)
    print(yearly.to_string(index=False))

    print("\nWeather and road features:")
    for feature in ["has_bad_weather", "is_weekend", "is_rush_hour", "road_type"]:
        table, base = analysis.corr_show(d, feature)
        print(f"\n{feature} (baseline high-severity share: {base:.3f})")
        print(table.head(5).to_string(index=False))


def run_interactive(df: pd.DataFrame) -> None:
    from src.interface import user_interface as ui

    ui.enable_utf8()
    ui.clear()
    ui.print_logo_centered(ui.PROGRAM_LOGO)
    ui.main_menu(df)


def main() -> None:
    args = parse_args()
    df = load_dataset(use_sample=args.sample)

    if args.summary:
        print_summary(df)

    if args.export_report:
        from src.reporting import generate_portfolio_report

        result = generate_portfolio_report(
            df,
            output_dir=Path(args.output_dir),
            source_label="bundled sample" if args.sample else "full dataset",
        )
        print("\nPortfolio report exported")
        print("-" * 40)
        print(f"Markdown report: {result['markdown_report']}")
        print(f"HTML dashboard:  {result['dashboard_html']}")
        print(f"Figures:         {result['figures_dir']}")

    if not args.summary and not args.export_report:
        run_interactive(df)


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\nBye!')
        sys.exit(0)
