# Phase 05: Consolidate Power Calculation via Delegation

**Status:** ✅ COMPLETE
**Started:** 2026-02-11
**Completed:** 2026-02-11
**PR Title:** `refactor(utils): delegate calculate_power_for_proportions to calculate_achieved_power`
**Risk Level:** Low
**Estimated Effort:** Small (30 minutes)
**Files Modified:** `core/utils.py`
**Dependencies:** None
**Blocks:** None

---

## Problem

`calculate_power_for_proportions(p1, p2, n, alpha)` (line 300 in `core/utils.py`) duplicates the logic in `calculate_achieved_power(p1, p2, n1, n2, alpha, direction)` (line 385). The former is a special case (equal sample sizes, two-tailed test) that should delegate to the latter instead of reimplementing the same math.

Both functions compute power identically:
1. Calculate standard error from proportions and sample sizes
2. Get the z-score for the given alpha and direction
3. Compute the effect z-score
4. Return `1 - normal_cdf(z_alpha - z_effect)` clamped to `[0.0, 1.0]`

The only difference is that `calculate_power_for_proportions` assumes `n1 == n2 == n` and `direction == "two_tailed"`.

---

## Implementation

### Step 1: Replace `calculate_power_for_proportions()` body with delegation

**File:** `/Users/chris/Projects/30-day-abs/core/utils.py`

**Before** (lines 300-327):
```python
def calculate_power_for_proportions(p1: float, p2: float, n: int,
                                  alpha: float = 0.05) -> float:
    """
    Calculate statistical power for comparing two proportions.

    Args:
        p1: First proportion
        p2: Second proportion
        n: Sample size per group
        alpha: Significance level

    Returns:
        Statistical power
    """
    # Calculate standard error
    se = math.sqrt(p1 * (1 - p1) / n + p2 * (1 - p2) / n)

    # Calculate critical value
    z_alpha = get_z_score(alpha, "two_tailed")

    # Calculate z-score for the effect
    effect_size = abs(p2 - p1)
    z_effect = effect_size / se if se > 0 else 0

    # Calculate power
    power = 1 - normal_cdf(z_alpha - z_effect)

    return min(max(power, 0.0), 1.0)
```

**After:**
```python
def calculate_power_for_proportions(p1: float, p2: float, n: int,
                                  alpha: float = 0.05) -> float:
    """
    Calculate statistical power for comparing two proportions.

    Convenience wrapper for equal sample sizes (two-tailed test).
    Delegates to calculate_achieved_power().

    Args:
        p1: First proportion
        p2: Second proportion
        n: Sample size per group
        alpha: Significance level

    Returns:
        Statistical power
    """
    return calculate_achieved_power(p1, p2, n, n, alpha, "two_tailed")
```

**IMPORTANT:** `calculate_achieved_power` is defined AFTER `calculate_power_for_proportions` in the file (line 385 vs line 300). In Python, this is fine because `calculate_power_for_proportions` is only called at runtime (not at module import time), so the forward reference is resolved by the time any caller invokes it. Do NOT rearrange function order.

---

## Verification Checklist

1. Run utils tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/core/test_utils.py -v
   ```

2. Verify that `calculate_power_for_proportions(0.05, 0.07, 1000)` and `calculate_achieved_power(0.05, 0.07, 1000, 1000, 0.05, "two_tailed")` return identical values. You can check this in a Python REPL:
   ```python
   from core.utils import calculate_power_for_proportions, calculate_achieved_power
   a = calculate_power_for_proportions(0.05, 0.07, 1000)
   b = calculate_achieved_power(0.05, 0.07, 1000, 1000, 0.05, "two_tailed")
   assert a == b, f"{a} != {b}"
   ```

3. Run broader tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/ --ignore=tests/integration -x -q
   ```

---

## What NOT To Do

1. **Do NOT remove `calculate_power_for_proportions()`.** It is a convenience API that callers may use. Only change its *body*.
2. **Do NOT change the function signature.** The `n: int` (single value) parameter is the API contract.
3. **Do NOT move `calculate_achieved_power()` above `calculate_power_for_proportions()`.** The file order is established and tests may depend on it.
4. **Do NOT add new imports.** Both functions are already in `core/utils.py`, so no import is needed.
