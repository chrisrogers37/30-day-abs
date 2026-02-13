# Notebook Templates

Downloadable Jupyter notebook templates for working through A/B test calculations offline. These are offered as downloads within the Streamlit app at each phase of the quiz.

## Templates

### `ab_test_design_template.ipynb` — Experiment Design

Walks through the 6 design questions:
1. MDE (minimum detectable effect) in percentage points
2. Target conversion rate calculation
3. Relative lift calculation
4. Sample size calculation (two-proportion z-test formula)
5. Experiment duration based on daily traffic
6. Business impact (additional conversions per day)

Each cell has placeholder variables and commented-out formulas for the user to complete.

### `ab_experimental_analysis_template.ipynb` — Data Analysis

Walks through the 7 analysis questions using the downloaded CSV data:
1. Control group conversion rate
2. Treatment group conversion rate
3. Absolute lift (percentage points)
4. Relative lift (%)
5. P-value via two-proportion z-test (uses `statsmodels`)
6. 95% confidence interval for the difference
7. Rollout decision based on CI vs. business target

Imports pandas, numpy, and statsmodels. Users load their `experiment_data.csv` and work through each calculation.

## Usage

These notebooks are downloaded from within the Streamlit app during the "Data Download" phase. They can also be opened directly:

```bash
cd notebooks/
jupyter notebook ab_test_design_template.ipynb
```

## Dependencies

The analysis notebook requires `statsmodels` for the z-test:
```bash
pip install statsmodels
```
All other dependencies (pandas, numpy) are included in `requirements.txt`.
