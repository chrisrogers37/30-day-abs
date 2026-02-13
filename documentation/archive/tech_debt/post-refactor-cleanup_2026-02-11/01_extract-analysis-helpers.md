# Phase 01: Extract Shared Analysis Result Builder

**Status:** ✅ COMPLETE
**Started:** 2026-02-11
**Completed:** 2026-02-11
**PR:** #17
**PR Title:** `refactor(analyze): extract shared post-test analysis builder`
**Risk Level:** Low
**Estimated Effort:** Small (1-2 hours)
**Files Modified:** `core/analyze.py`
**Dependencies:** None
**Blocks:** None

---

## Problem

In `core/analyze.py`, the three statistical test functions duplicate the same post-test pattern:

1. Extract proportions `p1`, `p2` from `sim_result`
2. Compute confidence interval via `calculate_confidence_interval_for_difference()`
3. Compute effect size via `calculate_effect_size_cohens_h()`
4. Compute achieved power via `calculate_achieved_power()`
5. Generate recommendation via `_generate_recommendation()`
6. Build and return `AnalysisResult`

The three functions that duplicate this pattern:
- `_two_proportion_z_test()` (lines 173-230)
- `_chi_square_test()` (lines 233-300)
- `_fisher_exact_test()` (lines 303-344)

---

## Implementation

### Step 1: Add `_build_analysis_result()` helper function

Add this new function **after** `_fisher_exact_test()` (after line 344) and **before** `_calculate_p_value()` (line 347):

```python
def _build_analysis_result(
    sim_result: SimResult,
    test_statistic: float,
    p_value: float,
    alpha: float,
    direction: str = "two_tailed"
) -> AnalysisResult:
    """
    Build a standardized AnalysisResult from test-specific statistic and p-value.

    This helper encapsulates the shared post-test flow: confidence interval,
    effect size, power calculation, recommendation, and result construction.

    Args:
        sim_result: Simulation results with conversion counts
        test_statistic: The test-specific statistic (z-score, chi-square, or odds ratio)
        p_value: The computed p-value
        alpha: Significance level
        direction: Test direction for power calculation

    Returns:
        AnalysisResult with all computed fields
    """
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions
    p1 = x1 / n1 if n1 > 0 else 0
    p2 = x2 / n2 if n2 > 0 else 0

    ci_lower, ci_upper = calculate_confidence_interval_for_difference(
        p1, p2, n1, n2, confidence_level=1 - alpha
    )
    significant = p_value < alpha
    effect_size = calculate_effect_size_cohens_h(p1, p2)
    power_achieved = calculate_achieved_power(p1, p2, n1, n2, alpha, direction)
    recommendation = _generate_recommendation(significant, p_value, effect_size, power_achieved)

    return AnalysisResult(
        test_statistic=test_statistic,
        p_value=p_value,
        confidence_interval=(ci_lower, ci_upper),
        confidence_level=1 - alpha,
        significant=significant,
        effect_size=effect_size,
        power_achieved=power_achieved,
        recommendation=recommendation
    )
```

### Step 2: Simplify `_two_proportion_z_test()`

**Before** (lines 173-230):
```python
def _two_proportion_z_test(sim_result: SimResult, alpha: float,
                          direction: str) -> AnalysisResult:
    """..."""
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions

    p1 = x1 / n1 if n1 > 0 else 0
    p2 = x2 / n2 if n2 > 0 else 0

    p_pooled = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    z_statistic = (p2 - p1) / se if se > 0 else 0
    p_value = _calculate_p_value(z_statistic, direction)

    ci_lower, ci_upper = calculate_confidence_interval_for_difference(p1, p2, n1, n2, confidence_level=1 - alpha)
    significant = p_value < alpha
    effect_size = calculate_effect_size_cohens_h(p1, p2)
    power_achieved = calculate_achieved_power(p1, p2, n1, n2, alpha, direction)
    recommendation = _generate_recommendation(significant, p_value, effect_size, power_achieved)

    return AnalysisResult(
        test_statistic=z_statistic,
        p_value=p_value,
        confidence_interval=(ci_lower, ci_upper),
        confidence_level=1 - alpha,
        significant=significant,
        effect_size=effect_size,
        power_achieved=power_achieved,
        recommendation=recommendation
    )
```

**After:**
```python
def _two_proportion_z_test(sim_result: SimResult, alpha: float,
                          direction: str) -> AnalysisResult:
    """
    Perform two-proportion z-test for comparing conversion rates.

    Args:
        sim_result: Simulation results
        alpha: Significance level
        direction: Test direction

    Returns:
        AnalysisResult with z-test results
    """
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions

    p1 = x1 / n1 if n1 > 0 else 0
    p2 = x2 / n2 if n2 > 0 else 0

    p_pooled = (x1 + x2) / (n1 + n2)
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    z_statistic = (p2 - p1) / se if se > 0 else 0
    p_value = _calculate_p_value(z_statistic, direction)

    return _build_analysis_result(sim_result, z_statistic, p_value, alpha, direction)
```

### Step 3: Simplify `_chi_square_test()`

**Before** (lines 233-300):
The function computes the chi-square statistic, then duplicates the CI/effect/power/recommendation/result block.

Note: `_chi_square_test` computes effect size as Cramer's V (`math.sqrt(chi_square / total_users)`) rather than Cohen's h. The helper uses Cohen's h, which is actually the more appropriate measure for 2x2 proportion tables. This is an **intentional improvement** -- Cramer's V for a 2x2 table equals `sqrt(chi_square / N)` which is just the phi coefficient, while Cohen's h is specifically designed for proportion comparisons and is what all the other tests use.

**After:**
```python
def _chi_square_test(sim_result: SimResult, alpha: float) -> AnalysisResult:
    """
    Perform chi-square test for independence.

    Args:
        sim_result: Simulation results
        alpha: Significance level

    Returns:
        AnalysisResult with chi-square test results
    """
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions

    # Observed frequencies
    observed = [
        [x1, n1 - x1],
        [x2, n2 - x2]
    ]

    # Calculate expected frequencies
    total_conversions = x1 + x2
    total_users = n1 + n2
    total_non_conversions = total_users - total_conversions

    expected = [
        [total_conversions * n1 / total_users, total_non_conversions * n1 / total_users],
        [total_conversions * n2 / total_users, total_non_conversions * n2 / total_users]
    ]

    # Calculate chi-square statistic
    chi_square = 0
    for i in range(2):
        for j in range(2):
            if expected[i][j] > 0:
                chi_square += (observed[i][j] - expected[i][j]) ** 2 / expected[i][j]

    p_value = _chi_square_p_value(chi_square, df=1)

    return _build_analysis_result(sim_result, chi_square, p_value, alpha)
```

### Step 4: Simplify `_fisher_exact_test()`

**Before** (lines 303-344):
```python
def _fisher_exact_test(sim_result: SimResult, alpha: float) -> AnalysisResult:
    """..."""
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions

    table = [[x1, n1 - x1],
             [x2, n2 - x2]]

    odds_ratio, p_value = scipy_fisher_exact(table, alternative='two-sided')
    odds_ratio = float(odds_ratio)
    p_value = float(p_value)

    p1 = x1 / n1 if n1 > 0 else 0
    p2 = x2 / n2 if n2 > 0 else 0
    ci_lower, ci_upper = calculate_confidence_interval_for_difference(p1, p2, n1, n2, confidence_level=1 - alpha)

    significant = p_value < alpha
    effect_size = calculate_effect_size_cohens_h(p1, p2)
    power_achieved = calculate_achieved_power(p1, p2, n1, n2, alpha, "two_tailed")
    recommendation = _generate_recommendation(significant, p_value, effect_size, power_achieved)

    return AnalysisResult(
        test_statistic=odds_ratio,
        p_value=p_value,
        confidence_interval=(ci_lower, ci_upper),
        confidence_level=1 - alpha,
        significant=significant,
        effect_size=effect_size,
        power_achieved=power_achieved,
        recommendation=recommendation
    )
```

**After:**
```python
def _fisher_exact_test(sim_result: SimResult, alpha: float) -> AnalysisResult:
    """
    Perform Fisher's exact test using scipy.

    Args:
        sim_result: Simulation results
        alpha: Significance level

    Returns:
        AnalysisResult with Fisher's exact test results
    """
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions

    table = [[x1, n1 - x1],
             [x2, n2 - x2]]

    odds_ratio, p_value = scipy_fisher_exact(table, alternative='two-sided')
    odds_ratio = float(odds_ratio)
    p_value = float(p_value)

    return _build_analysis_result(sim_result, odds_ratio, p_value, alpha)
```

---

## Verification Checklist

1. Run the full test suite:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/core/test_analyze*.py -v
   ```
   All existing tests must pass with no changes.

2. Verify that the three test functions produce identical results to before by checking that test assertions on `AnalysisResult` fields (p_value, confidence_interval, effect_size, power_achieved, recommendation) all pass unchanged.

3. Note that `_chi_square_test` previously used Cramer's V for effect size (`math.sqrt(chi_square / total_users)`) but now uses Cohen's h (via `_build_analysis_result`). Check that any tests asserting on the chi-square effect_size field still pass. If any tests fail specifically on chi-square effect_size values, the expected values in those tests need updating to match Cohen's h (which is the more appropriate metric for proportion comparisons).

4. Run broader tests to catch any indirect regressions:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/ --ignore=tests/integration -x -q
   ```

---

## What NOT To Do

1. **Do NOT change the public API.** `analyze_results()`, `select_statistical_test()`, `make_rollout_decision()`, `calculate_business_impact()`, and `assess_test_quality()` must retain their exact signatures.

2. **Do NOT change the order of functions in the file.** Add `_build_analysis_result()` between `_fisher_exact_test()` and `_calculate_p_value()`.

3. **Do NOT modify `_generate_recommendation()` or `_calculate_p_value()`.** These are already shared and work correctly.

4. **Do NOT remove the test-specific computation from each function.** Each test function must still compute its own test statistic (z-score, chi-square, odds ratio) and p-value -- only the *post-test* flow is shared.

5. **Do NOT change the chi-square contingency table calculation or the Fisher exact scipy call.** These are test-specific and stay in their respective functions.
