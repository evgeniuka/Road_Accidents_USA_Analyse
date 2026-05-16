# Analysis Report

The main portfolio report is generated here:

- `reports/portfolio_report.md`
- `reports/dashboard.html`
- `reports/figures/`
- `reports/tables/`

Regenerate the full report with:

```bash
python main.py --export-report
```

Or run a quick sample version with:

```bash
python main.py --sample --export-report
```

## Current Full-Dataset Findings

- Rows analyzed after cleaning: 7,728,141
- Years covered: 2016-2023; 2023 is partial through 2023-03-31
- High-severity record share: 19.5%, using `Severity >= 3`
- Top cities by accident count: Miami, Houston, Los Angeles, Charlotte, Dallas
- Highest high-severity segment: interstate rows, at 34.8% high-severity
- Data quality checks found no duplicate IDs, invalid severity values, invalid state codes, or non-US country values in the cleaned full run

## Method Notes

- `Severity >= 3` is a dataset-defined high-severity proxy, not a confirmed injury or fatality measure.
- City rankings are raw accident-record counts and are not normalized by population, road length, traffic volume, or reporting coverage.
- Findings are descriptive and should not be read as causal.

## Interview Framing

This project is best presented as a reproducible data-analysis pipeline over a large real-world dataset. It demonstrates chunked ETL, cleaning, validation, feature engineering, KPI reporting, visual storytelling, and dashboard packaging. The bundled sample keeps the repository easy to run quickly; the full report shows the project can scale to the original multi-gigabyte CSV.
