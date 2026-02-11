# Phase 02: Consolidate Duplicated Statistical Functions

**Status**: ✅ COMPLETE
**Started**: 2026-02-10
**Completed**: 2026-02-10
**PR Title**: `refactor(core): consolidate duplicated statistical functions`
**Risk Level**: Low (pure refactor — behavior unchanged)
**Effort**: 4-6 hours
**Depends On**: Phase 01 ✅
**Blocks**: Phase 03

---

## Problem Statement

Five statistical functions are duplicated across `core/analyze.py`, `core/design.py`, and `core/utils.py`. Each copy is byte-for-byte identical (or trivially different in signature). A bug fix in one copy has historically not been propagated to the others.

### Duplication Map

| Function | Location 1 | Location 2 | Location 3 | Difference |
|----------|-----------|-----------|-----------|------------|
| `_normal_cdf(z)` | `core/analyze.py:341` | `core/design.py:151` | `core/utils.py:320` | design.py has redundant `import math` at line 162 |
| `_calculate_achieved_power(...)` | `core/analyze.py:408` (6 params) | `core/design.py:119` (5 params) | — | analyze.py takes `n1, n2` separately; design.py takes single `n` |
| `_calculate_effect_size(p1, p2)` | `core/analyze.py:387` | `core/utils.py:136` (as `calculate_effect_size_cohens_h`) | — | Identical logic, different names |
| `_calculate_confidence_interval(...)` | `core/analyze.py:355` | `core/utils.py:251` (as `calculate_confidence_interval_for_difference`) | — | utils.py adds `n==0` guard and uses `confidence_level` instead of `alpha` |
| `calculate_minimum_detectable_effect(...)` | `core/design.py:166` (5 params) | `core/utils.py:333` (4 params) | — | design.py has extra `direction` param |

---

## Consolidation Strategy

**Canonical home**: `core/utils.py` for all shared statistical helper functions.

**Why utils.py**: It already serves as the utility module, is imported by both `analyze.py` and `design.py`, and has the most complete versions of most functions (with guards, docstrings, etc.).

---

## Implementation Plan

### Step 1: Consolidate `_normal_cdf()` into `core/utils.py`

**Keep**: `core/utils.py:320-330` (already the cleanest version)

**Delete**:
- `core/analyze.py:346-357`
- `core/design.py:151-163` (including the redundant `import math` at line 162)

**Update callers**:
- `core/analyze.py`: Add `from .utils import _normal_cdf` at top (or rename to `normal_cdf` since it's now shared)
- `core/design.py`: Add `from .utils import _normal_cdf` at top

**Rename consideration**: Since this function is now shared between modules, consider renaming from `_normal_cdf` (private) to `normal_cdf` (internal but shared). The leading underscore convention means "don't call from outside the module," but it's now called from 3 modules. Either name works — just be consistent.

**Recommended approach**: Rename to `normal_cdf` (no underscore) in `core/utils.py` and update all callers.

### Step 2: Consolidate `_calculate_achieved_power()` into `core/utils.py`

The two versions have different signatures:
- `core/design.py:119`: `(p1, p2, n, alpha, direction)` — takes single `n` per arm
- `core/analyze.py:413`: `(p1, p2, n1, n2, alpha, direction)` — takes separate `n1, n2`

**Canonical version** (in `core/utils.py`):
```python
def calculate_achieved_power(p1: float, p2: float, n1: int, n2: int,
                            alpha: float, direction: str) -> float:
    """
    Calculate achieved power for comparing two proportions.

    Args:
        p1: Control group proportion
        p2: Treatment group proportion
        n1: Control group sample size
        n2: Treatment group sample size
        alpha: Significance level
        direction: Test direction ("two_tailed" or "one_tailed")

    Returns:
        Achieved power (probability of detecting the effect)
    """
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    z_alpha = _get_z_score(alpha, direction)
    effect_size = abs(p2 - p1)
    z_effect = effect_size / se if se > 0 else 0
    power = 1 - normal_cdf(z_alpha - z_effect)
    return min(max(power, 0.0), 1.0)
```

**Update caller in design.py** (`core/design.py:63`):
```python
# BEFORE:
achieved_power = _calculate_achieved_power(p1, p2, n_per_arm, alpha, "two_tailed")

# AFTER (pass n_per_arm for both n1 and n2 since allocation is equal):
from .utils import calculate_achieved_power
achieved_power = calculate_achieved_power(p1, p2, n_per_arm, n_per_arm, alpha, "two_tailed")
```

**Delete**:
- `core/analyze.py:413-443`
- `core/design.py:119-148`

### Step 3: Consolidate `_calculate_effect_size()` → use existing `calculate_effect_size_cohens_h()`

**Keep**: `core/utils.py:136-154` (`calculate_effect_size_cohens_h`)

**Delete**: `core/analyze.py:392-410` (`_calculate_effect_size`)

**Update callers in analyze.py**:
```python
# BEFORE (3 locations in analyze.py):
effect_size = _calculate_effect_size(p1, p2)

# AFTER:
from .utils import calculate_effect_size_cohens_h
effect_size = calculate_effect_size_cohens_h(p1, p2)
```

Locations to update in `core/analyze.py`:
- Line 184: inside `_two_proportion_z_test()`
- Line 306: inside `_fisher_exact_test()`

(The chi-square test at line 254 uses Cramer's V, not Cohen's h — leave it alone.)

### Step 4: Consolidate `_calculate_confidence_interval()` → use existing `calculate_confidence_interval_for_difference()`

The two versions differ slightly:
- `core/analyze.py:360`: Takes `alpha`, no n==0 guard
- `core/utils.py:251`: Takes `confidence_level`, has n==0 guard

**Keep**: `core/utils.py:251-287` (more robust)

**Delete**: `core/analyze.py:360-389`

**Update callers in analyze.py** (3 locations):
```python
# BEFORE:
ci_lower, ci_upper = _calculate_confidence_interval(p1, p2, n1, n2, alpha)

# AFTER:
from .utils import calculate_confidence_interval_for_difference
ci_lower, ci_upper = calculate_confidence_interval_for_difference(
    p1, p2, n1, n2, confidence_level=1 - alpha
)
```

Locations to update in `core/analyze.py`:
- Line 178: inside `_two_proportion_z_test()`
- Line 248: inside `_chi_square_test()`
- Line 300: inside `_fisher_exact_test()`

### Step 5: Consolidate `calculate_minimum_detectable_effect()`

The two versions differ:
- `core/design.py:166`: Takes `direction` param (5 params)
- `core/utils.py:333`: No `direction` param, hardcodes "two_tailed" (4 params)

**Keep**: `core/design.py:166-190` (more complete with `direction` param)

**Move to**: `core/utils.py` (replacing the existing version at line 333-356)

**Update the utils.py version** to match the design.py signature:
```python
def calculate_minimum_detectable_effect(p1: float, n: int, alpha: float = 0.05,
                                       power: float = 0.8,
                                       direction: str = "two_tailed") -> float:
```

**Delete**: `core/design.py:166-190` (after moving to utils.py)

**Update callers**:
- Any code importing from `core.design` should now import from `core.utils`
- `core.design` can re-export if needed: `from .utils import calculate_minimum_detectable_effect`

### Step 6: Update all imports

After consolidation, the import section of `core/analyze.py` should include:
```python
from .utils import (
    normal_cdf,
    calculate_achieved_power,
    calculate_effect_size_cohens_h,
    calculate_confidence_interval_for_difference,
)
```

And `core/design.py`:
```python
from .utils import normal_cdf, calculate_achieved_power
```

### Step 7: Run tests and fix any import issues

```bash
pytest tests/core/ -v
pytest  # Full suite
```

---

## Verification Checklist

- [ ] `_normal_cdf` exists only in `core/utils.py` (grep confirms no other copies)
- [ ] `_calculate_achieved_power` exists only in `core/utils.py`
- [ ] `_calculate_effect_size` exists only in `core/utils.py` (as `calculate_effect_size_cohens_h`)
- [ ] `_calculate_confidence_interval` exists only in `core/utils.py` (as `calculate_confidence_interval_for_difference`)
- [ ] `calculate_minimum_detectable_effect` exists only in `core/utils.py`
- [ ] No redundant `import math` inside functions (the one at `design.py:162` is gone)
- [ ] `pytest` passes — 452+ tests, 0 failures
- [ ] No circular imports (utils.py should not import from analyze.py or vice versa)
- [ ] `grep -rn "_normal_cdf\|_calculate_achieved_power\|_calculate_effect_size\|_calculate_confidence_interval\|_fisher_exact_p_value" core/` shows only utils.py definitions and legitimate callers

---

## What NOT To Do

- **Do NOT change any function's behavior** — this is a pure refactor. The output for any given input must be identical before and after.
- **DO move `_get_z_score()` to `core/utils.py`** — originally the plan said not to, but moving `calculate_achieved_power` and `calculate_minimum_detectable_effect` to utils.py while they depend on `_get_z_score` in design.py creates a circular import (design→utils→design). Moving `_get_z_score` to utils.py eliminates the circular dependency entirely and creates a clean hierarchy: `types → utils → design → analyze`.
- **Do NOT touch `core/scoring.py` or `core/validation.py`** — their duplication issues are handled separately in Phase 05.
- **Do NOT consolidate `calculate_power_for_proportions()` in utils.py with `calculate_achieved_power()`** — they have the same logic but different signatures. After this refactor, `calculate_power_for_proportions` can be updated to delegate to `calculate_achieved_power`, but do that in a follow-up if desired.
- **Do NOT remove the `calculate_effect_size_cohens_h` name** — external code may reference it. Only remove the private `_calculate_effect_size` alias.

---

## Rollback Plan

This is a pure refactor. If tests fail, the cause is an import error or a missed caller update. Search for the old function name in the failing test to find what needs updating.
