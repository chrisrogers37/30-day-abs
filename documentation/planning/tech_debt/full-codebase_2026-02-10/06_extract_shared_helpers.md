# Phase 06: Extract Shared DTO Conversion and Question Selection Helpers

**PR Title**: `refactor: extract shared DTO conversion and question selection helpers`
**Risk Level**: Low (pure refactor)
**Effort**: 3-5 hours
**Depends On**: None
**Blocks**: None

---

## Problem Statement

Two patterns are duplicated across module boundaries:

### Issue 1: DTO-to-Core Conversion Duplicated Between LLM and UI

The conversion from Pydantic DTOs (schemas) to core domain types (`DesignParams`, `Allocation`, etc.) is performed in two places:

- `llm/integration.py:321-341`
- `ui/streamlit_app.py:262-276` (approximate — line numbers may vary in the 1830-line file)

Both locations construct the same `DesignParams` and `Allocation` objects from the same DTO fields. If a field is added to the DTO, both locations must be updated.

### Issue 2: Question Selection Logic Duplicated 4x in `question_bank.py`

`core/question_bank.py` has four nearly identical functions for selecting questions:

- `get_default_design_questions()` (~line 833)
- `get_default_analysis_questions()` (~line 868)
- `get_planning_questions()` (~line 925)
- `get_interpretation_questions()` (~line 953)

Each follows the same pattern:
1. Filter questions by category
2. Filter by difficulty
3. Apply random selection with seed
4. Return list

The only differences are: which category to filter, which difficulty levels to include, and how many questions to return.

---

## Implementation Plan

### Part A: Extract DTO Conversion Helper

#### Step 1: Create conversion functions in `schemas/` or a shared location

The natural home is in the schemas module, since it owns the DTO definitions. Create helper methods or a standalone function.

**Option A (Recommended)**: Add a `to_core_types()` classmethod on the relevant DTO:

In `schemas/scenario.py` (or wherever `ScenarioResponseDTO` is defined):

```python
def to_design_params(self) -> "DesignParams":
    """Convert this DTO to core DesignParams for calculations."""
    from core.types import DesignParams, Allocation

    return DesignParams(
        baseline_conversion_rate=self.baseline_conversion_rate,
        target_lift_pct=self.target_lift_pct,
        alpha=self.alpha,
        power=self.power,
        expected_daily_traffic=self.expected_daily_traffic,
        allocation=Allocation(
            control=self.allocation_control,
            treatment=self.allocation_treatment,
        ),
        # ... map remaining fields
    )
```

**Option B**: Create a standalone converter function in a new file `core/converters.py`:

```python
def scenario_dto_to_design_params(dto) -> DesignParams:
    """Convert ScenarioResponseDTO to DesignParams."""
    return DesignParams(
        baseline_conversion_rate=dto.baseline_conversion_rate,
        # ... etc
    )
```

#### Step 2: Identify exact field mapping

Read both duplicate locations carefully to determine the exact field mapping. The two locations may have slight differences (e.g., one may have a default fallback the other doesn't). The canonical version should include all guards from both.

Fields to map (expected — verify against actual code):
- `baseline_conversion_rate`
- `target_lift_pct`
- `alpha` (default 0.05)
- `power` (default 0.80)
- `expected_daily_traffic`
- `allocation.control` / `allocation.treatment` (default 0.5/0.5)
- `mde_absolute` (may be computed)
- `min_test_duration_days` / `max_test_duration_days` (optional)

#### Step 3: Update callers

In `llm/integration.py`, replace the inline conversion (lines ~321-341) with a call to the new helper.

In `ui/streamlit_app.py`, replace the inline conversion (lines ~262-276) with a call to the same helper.

#### Step 4: Test

Both callers should produce identical `DesignParams` objects for the same DTO input. Add a test that verifies this.

---

### Part B: Extract Question Selection Helper

#### Step 1: Identify the common pattern

All four selection functions follow this pattern:
```python
def get_X_questions(difficulty=None, count=None, seed=None):
    questions = [q for q in ALL_QUESTIONS if q.category == "X"]
    if difficulty:
        questions = [q for q in questions if q.difficulty == difficulty]
    if seed is not None:
        random.seed(seed)
        random.shuffle(questions)
    if count:
        questions = questions[:count]
    return questions
```

#### Step 2: Create a generic selection function

```python
def select_questions(
    category: str,
    difficulty: Optional[str] = None,
    count: Optional[int] = None,
    seed: Optional[int] = None
) -> List[Question]:
    """
    Select questions from the bank by category and optional filters.

    Args:
        category: Question category to filter by
        difficulty: Optional difficulty filter ("easy", "medium", "hard")
        count: Optional max number of questions to return
        seed: Optional random seed for reproducible selection

    Returns:
        List of matching Question objects
    """
    # Start with all questions in the category
    questions = [q for q in ALL_QUESTIONS if q.category == category]

    # Filter by difficulty if specified
    if difficulty:
        questions = [q for q in questions if q.difficulty == difficulty]

    # Shuffle with seed for reproducible random selection
    if seed is not None:
        rng = random.Random(seed)
        rng.shuffle(questions)

    # Limit count
    if count is not None:
        questions = questions[:count]

    return questions
```

**Important**: Use `random.Random(seed)` instead of `random.seed(seed)` to avoid mutating global state (this is also a minor improvement over the current code).

#### Step 3: Rewrite the four functions as thin wrappers

```python
def get_default_design_questions(difficulty=None, count=6, seed=None):
    """Get default design questions."""
    return select_questions("design", difficulty=difficulty, count=count, seed=seed)

def get_default_analysis_questions(difficulty=None, count=6, seed=None):
    """Get default analysis questions."""
    return select_questions("analysis", difficulty=difficulty, count=count, seed=seed)

def get_planning_questions(difficulty=None, count=4, seed=None):
    """Get planning questions."""
    return select_questions("planning", difficulty=difficulty, count=count, seed=seed)

def get_interpretation_questions(difficulty=None, count=4, seed=None):
    """Get interpretation questions."""
    return select_questions("interpretation", difficulty=difficulty, count=count, seed=seed)
```

**Note**: Keep the wrapper functions for backward compatibility — existing callers use `get_default_design_questions()`, not `select_questions("design")`.

#### Step 4: Verify wrapper defaults match current behavior

Read each original function carefully to confirm:
- Default `count` values match
- Default `difficulty` filtering matches
- Selection behavior (shuffle vs. sorted) matches

The wrappers must produce identical results for identical inputs.

#### Step 5: Run tests

```bash
pytest tests/core/test_question_bank.py -v
pytest  # Full suite
```

---

## Verification Checklist

### Part A: DTO Conversion
- [ ] Single source of truth for DTO → DesignParams conversion
- [ ] `llm/integration.py` uses the shared converter
- [ ] `ui/streamlit_app.py` uses the shared converter
- [ ] Both callers produce identical DesignParams for same input
- [ ] No inline DesignParams/Allocation construction remains in integration.py or streamlit_app.py

### Part B: Question Selection
- [ ] `select_questions()` generic function exists in `core/question_bank.py`
- [ ] All 4 wrapper functions delegate to `select_questions()`
- [ ] Wrapper functions keep their original signatures and defaults
- [ ] `random.Random(seed)` used instead of `random.seed(seed)` (no global state mutation)
- [ ] `pytest` passes — 452+ tests, 0 failures

---

## What NOT To Do

- **Do NOT change the public API** of `get_default_design_questions()` etc. — existing callers depend on the signature.
- **Do NOT move the question bank data** (the actual question definitions) — only the selection logic.
- **Do NOT create a new module** for the DTO converter unless it would cause circular imports. Prefer adding a method to the existing DTO class.
- **Do NOT change `ui/streamlit_app.py` layout or UI logic** — only replace the DTO conversion code.
- **Do NOT change how `ALL_QUESTIONS` is populated** — only how questions are selected from it.
