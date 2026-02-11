# Phase 03: Extract Magic Numbers to Named Constants

**Status**: ✅ COMPLETE
**Started**: 2026-02-10
**Completed**: 2026-02-10
**PR Title**: `refactor(core): extract magic numbers to named constants`
**Risk Level**: Low (pure refactor — behavior unchanged)
**Effort**: 2-3 hours
**Depends On**: Phase 02 ✅
**Blocks**: None

### Corrections Applied During Implementation

1. **Step 3 targets wrong file**: After Phase 02, `get_z_score` lives in `core/utils.py` (not `core/design.py`). Constants and replacements go in `utils.py`.
2. **analyze.py line numbers drifted ~155 lines** from Phases 01+02 removals. Actual locations verified against current code.
3. **Z_SCORES dict approach replaced**: Keeping the existing if/elif structure in `get_z_score()` and extracting numeric values to named constants at module level. Same benefit (no magic numbers) without structural refactor. This aligns with the plan's own "What NOT To Do" rule: "Do NOT refactor the `_get_z_score()` fallback chain beyond replacing magic numbers."

---

## Problem Statement

Magic numbers are scattered throughout the core module, making the code harder to understand, maintain, and modify. These fall into three categories:

1. **Statistical thresholds** (effect size interpretation, recommendation cutoffs)
2. **Simulation parameters** (effect weights, duration, session ranges)
3. **Z-score lookup values** (hardcoded for common alpha levels)

---

## Inventory of Magic Numbers

### In `core/analyze.py`

| Line(s) | Value(s) | Meaning |
|---------|----------|---------|
| 527 | `0.2` | Effect size threshold for "large" recommendation |
| 529 | `0.1` | Effect size threshold for "medium" recommendation |
| 534 | `0.8` | Power threshold for "insufficient power" warning |
| 536 | `0.1` | P-value threshold for "marginal significance" |
| 605 | `0.01` | Absolute lift threshold for "proceed with confidence" |
| 608 | `0.005` | Absolute lift threshold for "proceed with caution" |
| 645 | `1000` | Sample size threshold for "high early stopping risk" |
| 647 | `5000` | Sample size threshold for "medium early stopping risk" |
| 653 | `0.2` | Target lift threshold for "high novelty effect" |
| 655 | `0.1` | Target lift threshold for "medium novelty effect" |

### In `core/simulate.py`

| Line(s) | Value(s) | Meaning |
|---------|----------|---------|
| 41 | `-0.1, 0.1` | Control rate variation bounds (±10%) |
| 52 | `[1.0, 0.5, 0.0, -0.3]` | Effect multipliers (full, partial, none, negative) |
| 53 | `[0.7, 0.2, 0.08, 0.02]` | Effect probability weights |
| 69 | `30` | Hardcoded simulation duration in days |
| 199 | `300, 1800` | Converter session duration range (seconds) |
| 202 | `30, 600` | Non-converter session duration range (seconds) |
| 217 | `3, 15` | Converter page view range |
| 220 | `1, 5` | Non-converter page view range |
| 231 | `[0.4, 0.5, 0.1]` | Device type distribution weights |
| 244-245 | `[0.35, 0.25, ...]` | Traffic source distribution weights |

### In `core/design.py`

| Line(s) | Value(s) | Meaning |
|---------|----------|---------|
| 89-111 | `1.96, 2.576, 1.645, 2.326, 1.282` | Z-scores for common alpha levels |

---

## Implementation Plan

### Step 1: Create constants section at top of `core/analyze.py`

Add after the imports (around line 12), before the first function:

```python
# --- Statistical Thresholds ---
# Effect size thresholds for recommendation (Cohen's h scale)
EFFECT_SIZE_LARGE = 0.2
EFFECT_SIZE_MEDIUM = 0.1

# Power threshold below which test is considered underpowered
MIN_ADEQUATE_POWER = 0.8

# P-value threshold for marginal significance
MARGINAL_SIGNIFICANCE_THRESHOLD = 0.1

# Business impact thresholds (absolute lift)
LIFT_THRESHOLD_HIGH_CONFIDENCE = 0.01   # 1% absolute lift
LIFT_THRESHOLD_MODERATE_CONFIDENCE = 0.005  # 0.5% absolute lift

# Test quality thresholds
EARLY_STOPPING_HIGH_RISK_N = 1000
EARLY_STOPPING_MEDIUM_RISK_N = 5000
NOVELTY_EFFECT_HIGH_THRESHOLD = 0.2   # 20% target lift
NOVELTY_EFFECT_MEDIUM_THRESHOLD = 0.1  # 10% target lift
```

Then replace all hardcoded values in the functions with these constants.

### Step 2: Create constants section at top of `core/simulate.py`

Add after the imports (around line 12):

```python
# --- Simulation Parameters ---
# Control rate variation (±10% of baseline to simulate sampling variability)
CONTROL_RATE_VARIATION_MIN = -0.1
CONTROL_RATE_VARIATION_MAX = 0.1

# Effect realization distribution
# [full_effect, partial_effect, no_effect, negative_effect]
EFFECT_MULTIPLIERS = [1.0, 0.5, 0.0, -0.3]
EFFECT_WEIGHTS = [0.70, 0.20, 0.08, 0.02]

# Default simulation duration (days)
DEFAULT_SIMULATION_DAYS = 30

# Session duration ranges (seconds)
CONVERTER_SESSION_DURATION_RANGE = (300, 1800)    # 5-30 minutes
NON_CONVERTER_SESSION_DURATION_RANGE = (30, 600)  # 30s-10 minutes

# Page view ranges
CONVERTER_PAGE_VIEW_RANGE = (3, 15)
NON_CONVERTER_PAGE_VIEW_RANGE = (1, 5)

# Device type distribution
DEVICE_TYPES = ['desktop', 'mobile', 'tablet']
DEVICE_WEIGHTS = [0.4, 0.5, 0.1]

# Traffic source distribution
TRAFFIC_SOURCES = ['organic', 'direct', 'social', 'paid', 'email', 'referral']
TRAFFIC_WEIGHTS = [0.35, 0.25, 0.15, 0.15, 0.05, 0.05]
```

Then replace all inline values with these constants.

### Step 3: Create constants section at top of `core/design.py`

Add after the imports (around line 14):

```python
# --- Z-Score Lookup Table ---
# Common z-scores for standard alpha values (two-tailed and one-tailed)
Z_SCORES = {
    (0.05, "two_tailed"): 1.96,
    (0.05, "one_tailed"): 1.645,
    (0.01, "two_tailed"): 2.576,
    (0.01, "one_tailed"): 2.326,
    (0.1, "two_tailed"): 1.645,
    (0.1, "one_tailed"): 1.282,
}
```

Then update `_get_z_score()` to use the lookup table:
```python
def _get_z_score(alpha: float, direction: str) -> float:
    lookup_alpha = alpha / 2 if direction == "two_tailed" else alpha
    key = (round(lookup_alpha, 6), direction)

    # Check lookup table first
    if key in Z_SCORES:
        z_score = Z_SCORES[key]
    else:
        # Fall back to scipy
        try:
            from scipy.stats import norm
            z_score = norm.ppf(1 - lookup_alpha)
        except ImportError:
            # Last resort: closest known value
            z_score = Z_SCORES.get(
                min(Z_SCORES.keys(), key=lambda k: abs(k[0] - lookup_alpha)),
                1.96
            )

    logger.debug(f"Z-score: alpha={alpha:.6f}, direction={direction}, z={z_score:.6f}")
    return z_score
```

### Step 4: Update function bodies to use constants

This is mechanical replacement. For each magic number in the inventory above, replace it with the corresponding constant name. Example:

```python
# BEFORE (core/analyze.py:527-529):
if effect_size > 0.2:
    return "Strong evidence..."
elif effect_size > 0.1:
    return "Moderate improvement..."

# AFTER:
if effect_size > EFFECT_SIZE_LARGE:
    return "Strong evidence..."
elif effect_size > EFFECT_SIZE_MEDIUM:
    return "Moderate improvement..."
```

### Step 5: Run tests

```bash
pytest tests/core/ -v
pytest  # Full suite
```

---

## Verification Checklist

- [ ] No magic numbers remain in `_generate_recommendation()` — uses named constants
- [ ] No magic numbers remain in `calculate_business_impact()` — uses named constants
- [ ] No magic numbers remain in `assess_test_quality()` — uses named constants
- [ ] No magic numbers remain in `simulate_trial()` — uses named constants
- [ ] No magic numbers remain in `_generate_session_duration()`, `_generate_page_views()`, `_generate_device_type()`, `_generate_traffic_source()` — uses named constants
- [ ] Z-score lookup in `_get_z_score()` uses dictionary instead of if/elif chain
- [ ] `pytest` passes — 452+ tests, 0 failures
- [ ] Constants are defined at module level with UPPER_SNAKE_CASE names
- [ ] Each constant has a comment explaining what it represents

---

## What NOT To Do

- **Do NOT change any constant's value** — this is a pure naming refactor. Output must be identical.
- **Do NOT move constants to a separate `constants.py` file** — keep them in the module that uses them. Cross-module constants can be consolidated later if needed.
- **Do NOT extract tolerances from `core/validation.py`** — those are per-question and context-dependent, not general constants. That's Phase 05's concern.
- **Do NOT refactor the `_get_z_score()` fallback chain** beyond replacing magic numbers — it works correctly and the fallback behavior is intentional.
