# Phase 02: Introduce `ScoringContext` Dataclass

**Status:** ✅ COMPLETE
**Started:** 2026-02-11
**Completed:** 2026-02-11
**PR:** #18
**PR Title:** `refactor(scoring): introduce ScoringContext to reduce parameter counts`
**Risk Level:** Low
**Estimated Effort:** Medium (2-3 hours)
**Files Modified:** `core/validation.py`, `core/scoring.py`, `core/__init__.py`, tests, `ui/streamlit_app.py` (if applicable)
**Dependencies:** None
**Blocks:** Phase 07

---

## Problem

Three functions accept 8-9 parameters that share 6 common context parameters:

| Function | File | Line | Param Count |
|----------|------|------|-------------|
| `validate_answer_by_id()` | `core/validation.py` | 720 | 8 |
| `score_answers_by_id()` | `core/validation.py` | 808 | 8 |
| `create_variable_quiz_result()` | `core/scoring.py` | 481 | 8 |

The shared parameters are: `design_params`, `sample_size_result`, `sim_result`, `mde_absolute`, `business_target_absolute`, `alpha`.

---

## Implementation

### Step 1: Define `ScoringContext` in `core/validation.py`

Add this dataclass **after** the `ScoringResult` dataclass (after line 38) and **before** the `_calculate_grade` function (line 43):

```python
@dataclass(frozen=True)
class ScoringContext:
    """Shared context for scoring and validation operations.

    Bundles the common parameters needed by validate_answer_by_id,
    score_answers_by_id, and create_variable_quiz_result to reduce
    parameter counts from 8 to 3.
    """
    design_params: Optional['DesignParams'] = None
    sample_size_result: Optional[Any] = None
    sim_result: Optional['SimResult'] = None
    mde_absolute: Optional[float] = None
    business_target_absolute: Optional[float] = None
    alpha: float = 0.05
```

You need to add `Optional` to the existing typing import (it's already there). The `DesignParams` and `SimResult` forward references are already imported at the top of the file.

### Step 2: Clean break — replace individual params with `ctx`

**Approach:** Remove the 6 individual context kwargs entirely. Replace with a single `ctx: Optional[ScoringContext] = None` parameter. No dual interface, no resolution logic. Update all callers to construct `ScoringContext`.

**`validate_answer_by_id()`** (line 720) becomes:
```python
def validate_answer_by_id(
    question_id: str,
    user_answer: Any,
    ctx: Optional[ScoringContext] = None,
) -> ValidationResult:
```

Add normalization as first line inside body:
```python
    if ctx is None:
        ctx = ScoringContext()
```

Replace all internal references: `design_params` → `ctx.design_params`, `alpha` → `ctx.alpha`, etc.

### Step 3: Same pattern for `score_answers_by_id()`

**`score_answers_by_id()`** (line 808) becomes:
```python
def score_answers_by_id(
    user_answers: Dict[str, Any],
    question_ids: List[str],
    ctx: Optional[ScoringContext] = None,
) -> ScoringResult:
```

Same normalization. Pass `ctx` through to `validate_answer_by_id()` directly (no double-resolution concern with clean break).

### Step 4: Same pattern for `create_variable_quiz_result()` in `core/scoring.py`

Add `ScoringContext` to the import from `.validation`. Update signature to `(user_answers, question_ids, ctx=None)`. Pass `ctx` through to `score_answers_by_id()`.

### Step 5: Update all callers

Update all test files and internal callers to construct `ScoringContext(...)` instead of passing individual kwargs. All callers already use keyword args, so the migration is mechanical.

### Step 6: Export `ScoringContext` from the package

Add `ScoringContext` to `core/__init__.py`'s `__all__` list and import, alongside the existing `ScoringResult` export.

---

## Verification Checklist

1. Run validation tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/core/test_validation*.py -v
   ```

2. Run scoring tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/core/test_scoring*.py -v
   ```

3. All callers updated to use `ScoringContext` — no individual kwargs remain.

4. Verify `ScoringContext` can be imported:
   ```python
   from core.validation import ScoringContext
   ctx = ScoringContext(alpha=0.01)
   ```

5. Run broader tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/ --ignore=tests/integration -x -q
   ```

---

## What NOT To Do

1. **Do NOT change the default value of `alpha` (0.05) on `ScoringContext`.** This is the standard significance level and callers depend on it.

2. **Do NOT modify `calculate_design_answer_by_id()` or `calculate_analysis_answer_by_id()`.** These are called internally with individual params from ctx fields and don't need `ctx` in their signatures.

3. **Do NOT add `ScoringContext` to `core/types.py`.** It belongs in `core/validation.py` alongside the scoring functions that use it.

4. **Do NOT use mutable default arguments.** `ScoringContext` is a frozen dataclass — this is correct and intentional.
