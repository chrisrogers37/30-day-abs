# Phase 06: Consolidate Categorical Generators

**Status:** ✅ COMPLETE
**Started:** 2026-02-11
**Completed:** 2026-02-11
**PR Title:** `refactor(simulate): consolidate categorical feature generators`
**Risk Level:** Low
**Estimated Effort:** Small (30 minutes)
**Files Modified:** `core/simulate.py`
**Dependencies:** None
**Blocks:** None

---

## Problem

`_generate_device_type()` (line 251) and `_generate_traffic_source()` (line 264) in `core/simulate.py` are identical `random.choices()` calls that differ only in the data arrays passed in. Both follow this exact pattern:

```python
return random.choices(CATEGORIES, weights=WEIGHTS)[0]
```

This should be extracted into a shared helper to eliminate the duplication.

---

## Implementation

### Step 1: Add `_generate_categorical()` helper

**File:** `/Users/chris/Projects/30-day-abs/core/simulate.py`

Add this function **before** `_generate_device_type()` (insert before line 251):

```python
def _generate_categorical(categories: list, weights: list) -> str:
    """
    Generate a random categorical value from weighted categories.

    Args:
        categories: List of category strings
        weights: List of corresponding weights

    Returns:
        Selected category string
    """
    return random.choices(categories, weights=weights)[0]
```

### Step 2: Replace `_generate_device_type()` body

**Before** (lines 251-261):
```python
def _generate_device_type() -> str:
    """
    Generate realistic device type distribution.

    Returns:
        Device type string
    """
    return random.choices(
        DEVICE_TYPES,
        weights=DEVICE_WEIGHTS
    )[0]
```

**After:**
```python
def _generate_device_type() -> str:
    """
    Generate realistic device type distribution.

    Returns:
        Device type string
    """
    return _generate_categorical(DEVICE_TYPES, DEVICE_WEIGHTS)
```

### Step 3: Replace `_generate_traffic_source()` body

**Before** (lines 264-274):
```python
def _generate_traffic_source() -> str:
    """
    Generate realistic traffic source distribution.

    Returns:
        Traffic source string
    """
    return random.choices(
        TRAFFIC_SOURCES,
        weights=TRAFFIC_WEIGHTS
    )[0]
```

**After:**
```python
def _generate_traffic_source() -> str:
    """
    Generate realistic traffic source distribution.

    Returns:
        Traffic source string
    """
    return _generate_categorical(TRAFFIC_SOURCES, TRAFFIC_WEIGHTS)
```

---

## Context: Where the constants are defined

The module-level constants used by these functions are defined at lines 36-41 of `core/simulate.py`:

```python
# Device type distribution
DEVICE_TYPES = ['desktop', 'mobile', 'tablet']
DEVICE_WEIGHTS = [0.4, 0.5, 0.1]

# Traffic source distribution
TRAFFIC_SOURCES = ['organic', 'direct', 'social', 'paid', 'email', 'referral']
TRAFFIC_WEIGHTS = [0.35, 0.25, 0.15, 0.15, 0.05, 0.05]
```

Do NOT move or rename these constants.

---

## Verification Checklist

1. Run simulation tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/core/test_simulate.py -v
   ```

2. Verify that both `_generate_device_type()` and `_generate_traffic_source()` are still called from `_generate_user_data()` (lines 153-154). Those call sites should not change.

3. Run broader tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/ --ignore=tests/integration -x -q
   ```

---

## What NOT To Do

1. **Do NOT remove `_generate_device_type()` or `_generate_traffic_source()`.** They are called from `_generate_user_data()` at lines 153 and 154. Keep them as thin wrappers.
2. **Do NOT change the module-level constant names** (`DEVICE_TYPES`, `DEVICE_WEIGHTS`, `TRAFFIC_SOURCES`, `TRAFFIC_WEIGHTS`).
3. **Do NOT make `_generate_categorical()` a method on any class.** It is a module-level private function, consistent with all other helpers in this file (e.g., `_generate_session_duration`, `_generate_page_views`).
4. **Do NOT add any new imports.** `random` is already imported at line 8.
