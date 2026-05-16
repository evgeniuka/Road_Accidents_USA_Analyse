# US Road Accidents Portfolio Report

This report is generated from the full dataset. The exported charts and tables make the analysis reviewable on GitHub without opening Python.

## Executive Snapshot

- Rows analyzed: 7,728,141
- Period covered: 2016-2023
- Date range: 2016-01-14 to 2023-03-31
- High-severity record share: 19.5%
- Most frequent city: Miami (186,917)
- Cities represented: 13,622
- Coverage note: 2023 is partial through 2023-03-31.

![Portfolio KPI overview](figures/overview_kpis.png)

## Key Visuals

![Accidents and high-severity share by year](figures/yearly_trend.png)

![Top cities by accident count](figures/top_cities.png)

![Accidents by day of week and hour](figures/time_heatmap.png)

![Segments by high-severity share](figures/severity_by_context.png)

![Accident locations](figures/accident_locations.png)

## Key Findings

Top cities in the analyzed dataset:

- Miami: 186,917
- Houston: 169,609
- Los Angeles: 156,491
- Charlotte: 138,652
- Dallas: 130,939

Highest high-severity segments with at least 20 accidents:

- Road type / Interstate: 34.8% high-severity, 2,273,120 accidents
- Precipitation / Yes: 22.5% high-severity, 853,284 accidents
- Weekend / Yes: 21.6% high-severity, 1,231,393 accidents
- Crossing / No: 21.0% high-severity, 6,854,532 accidents
- Wind speed bin / 25+ mph: 21.0% high-severity, 32,898 accidents

Yearly KPI table:

|   year |   accidents |   high_severity_share |   avg_severity |   weekend_share |   precip_share |   bad_weather_share |
|-------:|------------:|----------------------:|---------------:|----------------:|---------------:|--------------------:|
|   2016 |     410,794 |                  34.2 |           2.38 |             9.8 |            7.2 |                 7.5 |
|   2017 |     718,066 |                  35.6 |           2.39 |             9.5 |           10.3 |                10.3 |
|   2018 |     893,416 |                  35.6 |           2.39 |            10.2 |           11.7 |                12.1 |
|   2019 |     954,284 |                  27.9 |           2.31 |            12.8 |           11.5 |                12.4 |
|   2020 |   1,178,863 |                  18.4 |           2.19 |            17.4 |           11.6 |                13.2 |
|   2021 |   1,563,700 |                  11.4 |           2.13 |            19.2 |           10.6 |                12.7 |
|   2022 |   1,762,387 |                   6.9 |           2.07 |            20.1 |           10.6 |                11.8 |
|   2023 |     246,631 |                   2.9 |           2.06 |            20.6 |           19.1 |                19.3 |

## Data Quality Notes

- Rows after cleaning: 7,728,141 (Rows available for analysis)
- Columns after cleaning: 38 (Columns retained for analysis)
- Duplicate IDs: 0 (Should be 0)
- Invalid severity values: 0 (Expected values are 1-4)
- Rows with invalid state code: 0 (Useful for catching shifted CSV fields)
- Rows with non-US country value: 0 (Usually a parsing or sample-quality issue)
- Rows outside continental-US coordinate bounds: 0 (Loose coordinate sanity check)
- Missing values: Precipitation(in): 28.5% (Top missing-value columns)
- Missing values: Wind_Speed(mph): 7.4% (Top missing-value columns)
- Missing values: wind_speed_bin: 7.4% (Top missing-value columns)
- Missing values: Visibility(mi): 2.3% (Top missing-value columns)
- Missing values: Weather_Condition: 2.2% (Top missing-value columns)
- Missing values: Temperature(F): 2.1% (Top missing-value columns)
- Missing values: Sunrise_Sunset: 0.3% (Top missing-value columns)
- Missing values: Street: 0.1% (Top missing-value columns)

## Method Notes

- `Severity >= 3` is used as a high-severity proxy from the dataset, not as a confirmed injury or fatality outcome.
- Counts by city are raw accident records and are not normalized by population, vehicle miles traveled, road length, or reporting coverage.
- The analysis is descriptive and should not be read as causal.
- 2023 is partial through 2023-03-31.

## Reviewer Notes

The repository includes a small bundled sample for quick review. The full analysis can be regenerated when `US_Accidents_March23.csv` is available in `data/raw/` or `../dataset/`.
