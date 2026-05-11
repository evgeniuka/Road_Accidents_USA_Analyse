# Sample Data Notes

This report is based on the bundled sample file:

`data/processed/first_1000_rows.csv`

The sample is useful for a quick project review, but it should not be presented as the final analytical result. The full project is designed for `US_Accidents_March23.csv`.

## Quick Findings From The Sample

- Rows analyzed after cleaning: 5,333
- Years covered: 2016-2018
- Severe accidents, defined as `Severity >= 3`: 38.5%
- Top cities in the sample: Dayton, Sacramento, San Jose, Columbus, Oakland

## Feature Signals In The Sample

- Weekend accidents have a higher severe-accident share than the sample baseline.
- Interstate rows show a much higher severe-accident share than local/highway rows in this sample.
- Bad-weather rows are close to the sample baseline, so this subset is not enough to claim a strong weather effect.

## Resume Framing

Good one-liner:

> Built a Python CLI for analyzing US road accident patterns with pandas feature engineering, KPI reports, visualizations, and statistical tests.

What I would mention in an interview:

- I separated data loading, preprocessing, analysis, statistics, visualization, and terminal UI into different modules.
- I engineered interpretable features from raw weather, time, visibility, road, and severity columns.
- I added a sample-data path so the project can be reviewed without downloading a large CSV.

