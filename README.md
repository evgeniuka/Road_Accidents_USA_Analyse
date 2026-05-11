# US Road Accidents Analysis

This is a Python data analysis project for exploring road accidents in the United States. I built it as a command-line tool: it can load the US Accidents dataset, clean the key columns, create weather/time/road features, and produce small reports about accident counts, severity, cities, streets, and yearly KPIs.

The repository includes a small sample CSV so the project can be reviewed quickly without downloading the full dataset.

## What It Does

- Loads and cleans accident data from `US_Accidents_March23.csv`.
- Parses dates and builds reusable time features such as year, date, weekend, night, and rush hour.
- Creates risk-related features from weather, visibility, precipitation, temperature, road type, bumps, and crossings.
- Provides an interactive CLI menu for preset reports and custom KPI views.
- Runs chi-square checks for accident severity against common factors.
- Supports a quick summary mode that works with the bundled sample data.

## Project Structure

```text
main.py                  CLI entry point
src/data_loader.py        dataset discovery and cleaning
src/preprocessing.py      date parsing, outlier handling, category casting
src/analysis.py           feature engineering and report tables
src/stats.py              chi-square tests
src/visualization.py      matplotlib/seaborn charts
src/interface/            menu-based terminal UI
data/processed/           small sample dataset for demo runs
data/raw/                 place the full dataset here if you have it
```

## Quick Demo

Run a non-interactive summary using the included sample:

```bash
python main.py --sample --summary
```

Example output from the bundled sample:

```text
Rows analyzed: 5,333
Years covered: 2016-2018
Severe accidents (Severity >= 3): 38.5%

Top cities:
- Dayton: 670
- Sacramento: 553
- San Jose: 248
- Columbus: 169
- Oakland: 157
```

## Full Dataset

The full CSV is intentionally not stored in the repository. To use it locally, place it in:

```text
data/raw/US_Accidents_March23.csv
```

or one level above the repository:

```text
../dataset/US_Accidents_March23.csv
```

If the full file is missing, the app falls back to the bundled sample dataset.

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Usage

Quick summary:

```bash
python main.py --sample --summary
```

Interactive menu with sample data:

```bash
python main.py --sample
```

Interactive menu with the full dataset when available:

```bash
python main.py
```

## Notes For Reviewers

This project is strongest as a data-cleaning and exploratory-analysis example. The next improvements I would make are:

- add saved charts into `reports/`;
- turn the most useful CLI flows into a notebook or Streamlit page;
- add tests around feature engineering;
- replace the sample file with a cleaner stratified sample from the full dataset.
