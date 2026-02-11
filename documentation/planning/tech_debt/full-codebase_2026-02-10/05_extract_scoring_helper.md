# Phase 05: Extract Scoring Helper to Reduce Validation Boilerplate

**Status**: ✅ COMPLETE
**Started**: 2026-02-10
**Completed**: 2026-02-10
**PR Title**: `refactor(core): extract scoring helper to reduce validation boilerplate`
**Risk Level**: Low (pure refactor — behavior unchanged)
**Effort**: 3-4 hours
**Depends On**: None
**Blocks**: None

---

## Problem Statement

`core/validation.py` contains two large scoring functions that repeat an identical pattern 12 times total:

- `score_design_answers()` (lines 301-418): 6 questions, ~117 lines
- `score_analysis_answers()` (lines 421-612): 6+ questions, ~191 lines

Each question block follows the exact same pattern:

```python
# Get user answer
user_X = user_answers.get("key_name", 0)
correct_X = correct_answers["key_name"]
tolerance = N
is_correct = abs(user_X - correct_X) <= tolerance
scores["key_name"] = {
    "correct": is_correct,
    "user": user_X,
    "correct_answer": correct_X,
    "tolerance": tolerance
}
if is_correct:
    total_score += 1
```

This pattern is repeated for every question, varying only in:
1. The dictionary key name
2. The tolerance value
3. The default value for missing answers

The total is ~308 lines of scoring boilerplate that could be ~50 lines with a helper.

---

## Implementation Plan

### Step 1: Define the scoring helper function

Add this function near the top of `core/validation.py`, after the dataclass definitions (around line 40):

```python
def _score_numeric_answer(
    user_answers: Dict[str, Any],
    correct_answers: Dict[str, Any],
    key: str,
    tolerance: float,
    default: Any = 0
) -> Tuple[bool, Dict[str, Any]]:
    """
    Score a single numeric answer against the correct value.

    Args:
        user_answers: Dict of user's answers
        correct_answers: Dict of correct answers
        key: Answer key to look up in both dicts
        tolerance: Acceptable absolute deviation
        default: Default value if user didn't answer

    Returns:
        Tuple of (is_correct, score_dict) where score_dict contains
        'correct', 'user', 'correct_answer', and 'tolerance' keys.
    """
    user_value = user_answers.get(key, default)
    correct_value = correct_answers[key]
    is_correct = abs(user_value - correct_value) <= tolerance
    score_dict = {
        "correct": is_correct,
        "user": user_value,
        "correct_answer": correct_value,
        "tolerance": tolerance
    }
    return is_correct, score_dict
```

### Step 2: Define a question specification list for design questions

Add a configuration list that captures the per-question differences:

```python
# Design question scoring specifications: (key, tolerance, default)
_DESIGN_SCORING_SPECS = [
    ("mde_absolute", 0.5, 0),
    ("target_conversion_rate", 0.5, 0),
    ("relative_lift_pct", 2.0, 0),
    ("sample_size", 50, 0),
    ("duration", 1, 0),
    ("additional_conversions", 5, 0),
]
```

### Step 3: Rewrite `score_design_answers()` using the helper

**BEFORE** (`core/validation.py:301-418`, ~117 lines):
```python
def score_design_answers(user_answers, design_params, sample_size_result, mde_absolute=None):
    correct_answers = calculate_correct_design_answers(design_params, sample_size_result, mde_absolute)
    scores = {}
    total_score = 0
    max_score = 6

    # Question 1: MDE (absolute)
    user_mde = user_answers.get("mde_absolute", 0)
    correct_mde = correct_answers["mde_absolute"]
    tolerance = 0.5
    is_correct = abs(user_mde - correct_mde) <= tolerance
    scores["mde_absolute"] = { ... }
    if is_correct: total_score += 1

    # Question 2: Target conversion rate
    # ... (same pattern repeated 5 more times)

    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    grade = ...
    return ScoringResult(scores=scores, total_score=total_score, ...)
```

**AFTER** (~25 lines):
```python
def score_design_answers(user_answers: Dict[str, Any],
                        design_params: DesignParams,
                        sample_size_result: Any,
                        mde_absolute: Optional[float] = None) -> ScoringResult:
    """Score design question answers."""
    correct_answers = calculate_correct_design_answers(
        design_params, sample_size_result, mde_absolute
    )

    scores = {}
    total_score = 0

    for key, tolerance, default in _DESIGN_SCORING_SPECS:
        is_correct, score_dict = _score_numeric_answer(
            user_answers, correct_answers, key, tolerance, default
        )
        scores[key] = score_dict
        if is_correct:
            total_score += 1

    max_score = len(_DESIGN_SCORING_SPECS)
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    grade = _calculate_grade(percentage)

    return ScoringResult(
        scores=scores,
        total_score=total_score,
        max_score=max_score,
        percentage=percentage,
        grade=grade
    )
```

### Step 4: Define a question specification list for analysis questions

You'll need to read the full `score_analysis_answers()` function (lines 421-612) to extract each question's key, tolerance, and default. The pattern is the same — just different keys and tolerances.

```python
# Analysis question scoring specifications: (key, tolerance, default)
_ANALYSIS_SCORING_SPECS = [
    # Extract these from the existing function body
    # Example: ("control_conversion_rate", 0.5, 0),
    # ...
]
```

**Important**: Some analysis questions may have special scoring logic (e.g., string comparison for rollout decisions, tuple comparison for confidence intervals). For these, add a `score_type` field to the spec:

```python
_ANALYSIS_SCORING_SPECS = [
    ("control_conversion_rate", 0.5, 0, "numeric"),
    ("treatment_conversion_rate", 0.5, 0, "numeric"),
    ("absolute_lift", 0.1, 0, "numeric"),
    ("relative_lift", 2.0, 0, "numeric"),
    ("p_value", 0.01, 0, "numeric"),
    ("confidence_interval", 0.5, (0, 0), "range"),
    ("rollout_decision", 0, "", "string"),
]
```

And extend the helper to handle different types, or add a second helper for non-numeric comparisons.

### Step 5: Extract the grade calculation

The grade calculation is repeated in both functions. Extract it:

```python
def _calculate_grade(percentage: float) -> str:
    """Calculate letter grade from percentage score."""
    if percentage >= 90:
        return "A"
    elif percentage >= 80:
        return "B"
    elif percentage >= 70:
        return "C"
    elif percentage >= 60:
        return "D"
    return "F"
```

This is also duplicated at `core/validation.py:973` in `score_answers_by_id()`.

### Step 6: Rewrite `score_analysis_answers()` using the same pattern

Follow the same approach as Step 3.

### Step 7: Run tests

```bash
pytest tests/core/test_validation.py -v
pytest  # Full suite
```

---

## Verification Checklist

- [ ] `score_design_answers()` produces identical output for all test inputs
- [ ] `score_analysis_answers()` produces identical output for all test inputs
- [ ] `_score_numeric_answer()` helper is tested directly with edge cases
- [ ] Grade calculation uses `_calculate_grade()` in all 3 locations
- [ ] `pytest` passes — 452+ tests, 0 failures
- [ ] Total line count of `core/validation.py` is reduced by ~200 lines
- [ ] No changes to `ScoringResult` or `ValidationResult` dataclasses

---

## What NOT To Do

- **Do NOT change the scoring logic** — tolerances, defaults, and grading thresholds must remain identical.
- **Do NOT change `validate_design_answer()`** (lines 42-130) — this is the per-question validation function, not the batch scorer. It has a different structure and purpose.
- **Do NOT change `validate_answer_by_id()` or `score_answers_by_id()`** — these are the newer ID-based API and have their own pattern.
- **Do NOT introduce a class** for scoring — a helper function + data list is the right level of abstraction here.
- **Do NOT change function signatures** — `score_design_answers()` and `score_analysis_answers()` must keep their current signatures for backward compatibility.
