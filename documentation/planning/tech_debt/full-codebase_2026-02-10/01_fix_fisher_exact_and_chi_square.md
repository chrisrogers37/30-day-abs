# Phase 01: Fix Fisher's Exact Test and Chi-Square CDF

**Status**: 🔧 IN PROGRESS
**Started**: 2026-02-10
**PR Title**: `fix(core): use scipy for Fisher's exact and chi-square tests`
**Risk Level**: Medium (changes statistical output values)
**Effort**: 3-5 hours
**Depends On**: None
**Blocks**: Phase 02

---

## Problem Statement

### Bug 1: Fisher's Exact Test Silently Falls Back to Chi-Square (CRITICAL)

**File**: `core/analyze.py:286-287`

The `_fisher_exact_test()` function was specifically selected by `select_statistical_test()` because expected cell counts are below 5 (violating chi-square assumptions). However, for any sample where `control_n + treatment_n > 100`, the function immediately falls back to chi-square — the exact test it was supposed to avoid.

```python
# core/analyze.py:286-287 — THE BUG
def _fisher_exact_test(sim_result: SimResult, alpha: float) -> AnalysisResult:
    # For large samples, approximate with chi-square
    if sim_result.control_n + sim_result.treatment_n > 100:
        return _chi_square_test(sim_result, alpha)  # <-- DEFEATS THE PURPOSE
```

**Impact**: In practice, nearly all simulated scenarios have n > 100 (typical daily traffic is 100-10M), so Fisher's exact test is *never actually used*. The test selection logic correctly identifies when Fisher's is needed, but the execution silently ignores it.

**Real-world example**: A scenario with 500 users per group and 2 conversions per group (baseline rate 0.4%) would have expected cell count of 2.0 — Fisher's exact is the only appropriate test. But n=1000 > 100, so it falls back to chi-square, which is invalid for this data.

### Bug 2: Crude Chi-Square CDF Approximation (HIGH)

**File**: `core/analyze.py:467-483`

The `_chi_square_cdf()` function uses `1 - math.exp(-chi_square / 2)` for df > 1. This is not a recognized statistical approximation and produces materially incorrect p-values.

```python
# core/analyze.py:478-483 — CRUDE APPROXIMATION
def _chi_square_cdf(chi_square: float, df: int) -> float:
    if df == 1:
        return _normal_cdf(math.sqrt(chi_square))  # This is fine for df=1
    # For df > 1, use approximation
    return 1 - math.exp(-chi_square / 2)  # <-- NOT A VALID STATISTICAL FORMULA
```

**Impact**: For df=1 (the 2x2 case used in this app), the code takes the correct `df == 1` branch, so this bug is currently **dormant**. However, if the codebase ever adds tests with df > 1 (e.g., multi-variant tests), p-values will be wrong. Additionally, the `_fisher_exact_p_value()` function at line 486-509 is also a rough approximation that should use scipy.

**Note**: The `_chi_square_p_value()` function at line 446-464 handles df=1 correctly by converting to a z-test. The bad path is only reached for df > 1 via `_chi_square_cdf()`.

---

## Root Cause

scipy is installed in the project venv (v1.16.1) and used in `core/design.py:98` inside `_get_z_score()`, but was **never declared in `requirements.txt`**. The design.py usage wraps the import in `try/except ImportError` with a fallback, treating it as optional. The statistical test functions were written with manual approximations instead of using scipy consistently. The Fisher's exact n>100 guard was likely added as a performance optimization that accidentally broke correctness.

---

## Implementation Plan

### Step 1: Add scipy to requirements.txt and verify

scipy is installed in the venv (v1.16.1) but missing from `requirements.txt`. Add it as a declared dependency.

```bash
# Add scipy to requirements.txt
echo "scipy" >> requirements.txt

# Confirm scipy is importable
python -c "from scipy.stats import fisher_exact, chi2; print('OK')"
```

### Step 2: Replace `_fisher_exact_test()` (core/analyze.py:274-323)

**Replace the entire function** with a scipy-based implementation. Remove the n>100 fallback completely.

**BEFORE** (`core/analyze.py:274-323`):
```python
def _fisher_exact_test(sim_result: SimResult, alpha: float) -> AnalysisResult:
    # For large samples, approximate with chi-square
    if sim_result.control_n + sim_result.treatment_n > 100:
        return _chi_square_test(sim_result, alpha)

    # Simplified Fisher's exact test implementation
    # In production, use scipy.stats.fisher_exact
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions

    # Calculate p-value using hypergeometric distribution approximation
    p_value = _fisher_exact_p_value(x1, n1, x2, n2)
    # ... rest of function
```

**AFTER** (scipy imported at module level):
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

    # Build 2x2 contingency table
    table = [[x1, n1 - x1],
             [x2, n2 - x2]]

    # scipy handles any sample size correctly
    odds_ratio, p_value = scipy_fisher_exact(table, alternative='two-sided')

    # Calculate confidence interval for difference
    p1 = x1 / n1 if n1 > 0 else 0
    p2 = x2 / n2 if n2 > 0 else 0
    ci_lower, ci_upper = _calculate_confidence_interval(p1, p2, n1, n2, alpha)

    # Determine significance
    significant = p_value < alpha

    # Calculate effect size
    effect_size = _calculate_effect_size(p1, p2)

    # Calculate achieved power
    power_achieved = _calculate_achieved_power(p1, p2, n1, n2, alpha, "two_tailed")

    # Generate recommendation
    recommendation = _generate_recommendation(significant, p_value, effect_size, power_achieved)

    return AnalysisResult(
        test_statistic=odds_ratio,  # Odds ratio is the natural test statistic for Fisher's
        p_value=p_value,
        confidence_interval=(ci_lower, ci_upper),
        confidence_level=1 - alpha,
        significant=significant,
        effect_size=effect_size,
        power_achieved=power_achieved,
        recommendation=recommendation
    )
```

### Step 3: Replace `_chi_square_p_value()` and `_chi_square_cdf()` (core/analyze.py:446-483)

Replace both functions with a single scipy-based implementation.

**BEFORE** (`core/analyze.py:446-483`):
```python
def _chi_square_p_value(chi_square: float, df: int) -> float:
    if df == 1:
        z = math.sqrt(chi_square)
        return 2 * (1 - _normal_cdf(z))
    return 1 - _chi_square_cdf(chi_square, df)

def _chi_square_cdf(chi_square: float, df: int) -> float:
    if df == 1:
        return _normal_cdf(math.sqrt(chi_square))
    return 1 - math.exp(-chi_square / 2)  # BAD APPROXIMATION
```

**AFTER** (replace both with a single function, scipy imported at module level):
```python
def _chi_square_p_value(chi_square: float, df: int) -> float:
    """
    Calculate p-value for chi-square statistic using scipy.

    Args:
        chi_square: Chi-square statistic
        df: Degrees of freedom

    Returns:
        P-value (survival function)
    """
    return float(chi2.sf(chi_square, df))
```

### Step 4: Remove `_fisher_exact_p_value()` (core/analyze.py:486-509)

This function is no longer needed since Fisher's exact test now uses scipy directly. **Delete the entire function.**

### Step 5: Remove `_chi_square_cdf()` (core/analyze.py:467-483)

This function is no longer called after Step 3. **Delete the entire function.**

### Step 6: Add scipy imports at top of file

Add to the imports section of `core/analyze.py`:
```python
from scipy.stats import fisher_exact as scipy_fisher_exact
from scipy.stats import chi2
```

### Step 7: Update tests

**File**: `tests/core/test_analyze.py`

Add or update test cases to verify:

```python
def test_fisher_exact_works_for_large_samples():
    """Fisher's exact should NOT fall back to chi-square for n > 100."""
    # Create scenario where Fisher's is selected (small expected cells)
    # but total n > 100
    sim_result = SimResult(
        control_n=500,
        control_conversions=2,  # Very low rate -> small expected cells
        treatment_n=500,
        treatment_conversions=8,
        user_data=[]
    )
    result = analyze_results(sim_result, alpha=0.05, test_type="fisher_exact")
    # Should complete without falling back to chi-square
    assert result.test_type_used == "fisher_exact"
    assert 0 <= result.p_value <= 1


def test_fisher_exact_matches_scipy():
    """Fisher's exact p-value should match scipy.stats.fisher_exact."""
    from scipy.stats import fisher_exact
    sim_result = SimResult(
        control_n=50,
        control_conversions=3,
        treatment_n=50,
        treatment_conversions=10,
        user_data=[]
    )
    result = analyze_results(sim_result, alpha=0.05, test_type="fisher_exact")

    # Compare with direct scipy call
    table = [[3, 47], [10, 40]]
    _, expected_p = fisher_exact(table, alternative='two-sided')
    assert abs(result.p_value - expected_p) < 1e-10


def test_chi_square_p_value_uses_scipy():
    """Chi-square p-value should use scipy for all df values."""
    from scipy.stats import chi2
    # Test df=1
    p1 = _chi_square_p_value(3.84, df=1)
    expected_p1 = chi2.sf(3.84, 1)
    assert abs(p1 - expected_p1) < 1e-10

    # Test df=2 (previously broken)
    p2 = _chi_square_p_value(5.99, df=2)
    expected_p2 = chi2.sf(5.99, 2)
    assert abs(p2 - expected_p2) < 1e-10
```

### Step 8: Remove try/except pytest.skip guards from existing tests

Now that Fisher's exact and chi-square are properly implemented with scipy, remove the defensive `try/except` + `pytest.skip()` wrappers from:

- `tests/core/test_analyze.py`: 2 guards (lines 186-191, 199-204)
- `tests/core/test_analyze_statistical_tests.py`: 9 guards across `TestChiSquareTest` and `TestFisherExactTest`

These tests should now run and assert directly. This ensures regressions are caught rather than silently skipped.

---

## Verification Checklist

- [ ] `pytest tests/core/test_analyze.py` passes
- [ ] `pytest` (full suite) passes — 452+ tests passing, 0 failures
- [ ] Fisher's exact test produces correct p-values for n > 100
- [ ] Fisher's exact test produces correct p-values for n <= 100
- [ ] Chi-square p-value matches `scipy.stats.chi2.sf()` for df=1
- [ ] Chi-square p-value matches `scipy.stats.chi2.sf()` for df=2
- [ ] `_fisher_exact_p_value()` function is deleted
- [ ] `_chi_square_cdf()` function is deleted
- [ ] No references to deleted functions remain (grep for them)
- [ ] `result.test_type_used` correctly reports "fisher_exact" (not "chi_square") when Fisher's is selected
- [ ] scipy is listed in `requirements.txt`
- [ ] scipy imported at module level in `core/analyze.py`
- [ ] All try/except pytest.skip guards removed from Fisher/chi-square tests (11 guards across 2 files)
- [ ] Previously-skipped tests now run and pass

---

## What NOT To Do

- **Do NOT remove the `select_statistical_test()` function** — it correctly determines *when* to use Fisher's exact. The bug is only in `_fisher_exact_test()` execution.
- **Do NOT change the test selection thresholds** (min_expected < 5 for Fisher's, min_sample < 30 for chi-square). Those are separate concerns (see CODE_REVIEW_EXPERIMENTAL_RIGOR.md item 1).
- **DO add scipy to requirements.txt** — it was missing despite being used. It is now a hard dependency.
- **DO import scipy at the module level** — local imports were only justified when scipy was optional.
- **Do NOT change `_two_proportion_z_test()`** — it is not affected by these bugs.
- **Do NOT change the `AnalysisResult` dataclass** — the existing fields accommodate all three test types.

---

## Rollback Plan

If tests fail after this change, the most likely cause is that existing tests assert exact p-values that were computed with the old approximation. Update the expected values in those tests to match scipy's output, which is more accurate. Do NOT revert to the broken approximation to make old tests pass.
