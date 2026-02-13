# Phase 07: Extract Shared Answer Key Generation Loop

**Status:** ✅ COMPLETE
**Started:** 2026-02-11
**Completed:** 2026-02-11
**PR Title:** `refactor(scoring): extract shared answer key generation loop`
**Risk Level:** Low
**Estimated Effort:** Small (30 minutes)
**Files Modified:** `core/scoring.py`
**Dependencies:** None (but coordinate with any other phases that modify `core/scoring.py`)
**Blocks:** None

---

## Problem

`generate_variable_design_answer_key()` (line 354) and `generate_variable_analysis_answer_key()` (line 398) in `core/scoring.py` share an identical loop pattern:

```python
questions = []
correct_answers = {}

for qid in question_ids:
    question = get_question_by_id(qid)
    if question is None:
        raise ValueError(f"Unknown question ID: {qid}")
    questions.append(question)

    try:
        answer, _ = calculate_*_answer_by_id(qid, ...)
        correct_answers[qid] = answer
    except (ValueError, TypeError, KeyError, ZeroDivisionError) as e:
        correct_answers[qid] = f"Error: {str(e)}"
```

The only difference between the two loops is the `calculate_*_answer_by_id` call and its arguments. This shared logic should be extracted into a helper that accepts a callable.

---

## Implementation

### Step 1: Add `_build_answer_key_entries()` helper

**File:** `/Users/chris/Projects/30-day-abs/core/scoring.py`

Add this function **before** `generate_variable_design_answer_key()` (insert before line 354, after the `VariableQuizResult` dataclass):

```python
def _build_answer_key_entries(
    question_ids: List[str],
    calculate_fn,
) -> tuple:
    """
    Build answer key entries by iterating question IDs and computing answers.

    Args:
        question_ids: List of question IDs from question_bank
        calculate_fn: Callable that takes a question_id and returns (answer, tolerance).
                     Should be a lambda or partial wrapping calculate_*_answer_by_id.

    Returns:
        Tuple of (questions list, correct_answers dict)

    Raises:
        ValueError: If a question_id is not found in question_bank
    """
    questions = []
    correct_answers = {}

    for qid in question_ids:
        question = get_question_by_id(qid)
        if question is None:
            raise ValueError(f"Unknown question ID: {qid}")
        questions.append(question)

        try:
            answer, _ = calculate_fn(qid)
            correct_answers[qid] = answer
        except (ValueError, TypeError, KeyError, ZeroDivisionError) as e:
            correct_answers[qid] = f"Error: {str(e)}"

    return questions, correct_answers
```

### Step 2: Simplify `generate_variable_design_answer_key()`

**Before** (lines 354-395):
```python
def generate_variable_design_answer_key(
    question_ids: List[str],
    design_params: DesignParams,
    sample_size_result: Any,
    mde_absolute: Optional[float] = None
) -> VariableAnswerKey:
    """
    Generate answer key for a variable set of design questions.

    Args:
        question_ids: List of question IDs from question_bank
        design_params: Design parameters from scenario
        sample_size_result: Sample size calculation result
        mde_absolute: Pre-calculated MDE absolute value

    Returns:
        VariableAnswerKey with selected questions and correct answers
    """
    questions = []
    correct_answers = {}

    for qid in question_ids:
        question = get_question_by_id(qid)
        if question is None:
            raise ValueError(f"Unknown question ID: {qid}")
        questions.append(question)

        try:
            answer, _ = calculate_design_answer_by_id(
                qid, design_params, sample_size_result, mde_absolute
            )
            correct_answers[qid] = answer
        except (ValueError, TypeError, KeyError, ZeroDivisionError) as e:
            correct_answers[qid] = f"Error: {str(e)}"

    return VariableAnswerKey(
        question_type="design",
        question_ids=question_ids,
        questions=questions,
        correct_answers=correct_answers,
        max_score=len(question_ids)
    )
```

**After:**
```python
def generate_variable_design_answer_key(
    question_ids: List[str],
    design_params: DesignParams,
    sample_size_result: Any,
    mde_absolute: Optional[float] = None
) -> VariableAnswerKey:
    """
    Generate answer key for a variable set of design questions.

    Args:
        question_ids: List of question IDs from question_bank
        design_params: Design parameters from scenario
        sample_size_result: Sample size calculation result
        mde_absolute: Pre-calculated MDE absolute value

    Returns:
        VariableAnswerKey with selected questions and correct answers
    """
    questions, correct_answers = _build_answer_key_entries(
        question_ids,
        lambda qid: calculate_design_answer_by_id(qid, design_params, sample_size_result, mde_absolute),
    )

    return VariableAnswerKey(
        question_type="design",
        question_ids=question_ids,
        questions=questions,
        correct_answers=correct_answers,
        max_score=len(question_ids)
    )
```

### Step 3: Simplify `generate_variable_analysis_answer_key()`

**Before** (lines 398-439):
```python
def generate_variable_analysis_answer_key(
    question_ids: List[str],
    sim_result: SimResult,
    business_target_absolute: Optional[float] = None,
    alpha: float = 0.05
) -> VariableAnswerKey:
    """
    Generate answer key for a variable set of analysis questions.

    Args:
        question_ids: List of question IDs from question_bank
        sim_result: Simulation results
        business_target_absolute: Business target for rollout decision
        alpha: Significance level

    Returns:
        VariableAnswerKey with selected questions and correct answers
    """
    questions = []
    correct_answers = {}

    for qid in question_ids:
        question = get_question_by_id(qid)
        if question is None:
            raise ValueError(f"Unknown question ID: {qid}")
        questions.append(question)

        try:
            answer, _ = calculate_analysis_answer_by_id(
                qid, sim_result, business_target_absolute, alpha
            )
            correct_answers[qid] = answer
        except (ValueError, TypeError, KeyError, ZeroDivisionError) as e:
            correct_answers[qid] = f"Error: {str(e)}"

    return VariableAnswerKey(
        question_type="analysis",
        question_ids=question_ids,
        questions=questions,
        correct_answers=correct_answers,
        max_score=len(question_ids)
    )
```

**After:**
```python
def generate_variable_analysis_answer_key(
    question_ids: List[str],
    sim_result: SimResult,
    business_target_absolute: Optional[float] = None,
    alpha: float = 0.05
) -> VariableAnswerKey:
    """
    Generate answer key for a variable set of analysis questions.

    Args:
        question_ids: List of question IDs from question_bank
        sim_result: Simulation results
        business_target_absolute: Business target for rollout decision
        alpha: Significance level

    Returns:
        VariableAnswerKey with selected questions and correct answers
    """
    questions, correct_answers = _build_answer_key_entries(
        question_ids,
        lambda qid: calculate_analysis_answer_by_id(qid, sim_result, business_target_absolute, alpha),
    )

    return VariableAnswerKey(
        question_type="analysis",
        question_ids=question_ids,
        questions=questions,
        correct_answers=correct_answers,
        max_score=len(question_ids)
    )
```

---

## Verification Checklist

1. Run scoring tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/core/test_scoring.py -v
   ```

2. Verify that answer keys are generated correctly for both design and analysis question types. The `VariableAnswerKey` returned by both functions should have identical structure to before.

3. Verify error handling: if `calculate_design_answer_by_id` raises a `ValueError`, the error message should still appear as `f"Error: {str(e)}"` in `correct_answers`. The lambda captures the outer arguments by closure, so the `calculate_fn(qid)` call signature works correctly.

4. Run broader tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/ --ignore=tests/integration -x -q
   ```

---

## What NOT To Do

1. **Do NOT change the function signatures** of `generate_variable_design_answer_key()` or `generate_variable_analysis_answer_key()`. They are called from `select_and_create_design_quiz()` (line 570), `select_and_create_analysis_quiz()` (line 598), and `create_variable_quiz_result()` (line 514/520).
2. **Do NOT change the exception types caught** in the try/except block. The tuple `(ValueError, TypeError, KeyError, ZeroDivisionError)` is intentional and matches the existing behavior exactly.
3. **Do NOT make `_build_answer_key_entries()` a method on any class.** It is a module-level private function, consistent with `_get_question_key()` at line 199.
4. **Do NOT add new imports.** `get_question_by_id`, `calculate_design_answer_by_id`, and `calculate_analysis_answer_by_id` are already imported at lines 19-22.
