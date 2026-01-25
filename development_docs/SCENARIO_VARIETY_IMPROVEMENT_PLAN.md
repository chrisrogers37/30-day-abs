# Scenario Variety Improvement Plan

**Date:** January 2025
**Status:** Mostly Complete
**Branch:** `claude/review-project-codebase-I80YU`

## Executive Summary

The 30 Day A/Bs application currently produces repetitive, "cookie cutter" scenarios despite using LLM generation. This document outlines a comprehensive plan to dramatically expand scenario variety while maintaining educational integrity.

## Implementation Status Overview

| Phase | Description | Status |
|-------|-------------|--------|
| **Phase 1** | Business Context Expansion | ✅ Complete |
| **Phase 2** | Parameter Space Expansion | ✅ Complete |
| **Phase 3** | Question & Analysis Variety | ✅ Complete |
| **Phase 4** | Scenario Complexity Dimensions | ✅ Complete |
| **Phase 5** | LLM Prompt Restructure | ✅ Complete |
| **UI Updates** | Streamlit Integration | ✅ Complete |

---

## Problem Statement

### Current Constraints Causing Repetition

| Dimension | Current State | Result |
|-----------|---------------|--------|
| **Business Context** | 7 company types, 6 segments, 4 KPIs, 30 scenario templates | Same stories, different numbers |
| **Parameter Space** | Traffic 500-5K, baseline 0.1-50%, MDE 0.1-10pp | ~50-100 distinct "shapes" |
| **Question Types** | Fixed 13 questions, always same formula sequence | Predictable learning path |
| **Metric Types** | Only conversion rates | Misses revenue, retention, engagement depth |
| **Test Designs** | Always 50/50 split, always two-proportion z-test | No design decisions |

### Root Causes Identified

1. **Narrow Traffic Range**: 500-5,000 (only 10x range)
2. **Limited Company Types**: Only 7 industries
3. **Limited User Segments**: Only 6 segment types
4. **Limited KPIs**: Only 4 metric types
5. **Template Archetypes**: 30 hardcoded scenario patterns in prompt
6. **Keyword Validation**: Forces template language in narratives
7. **Mathematical Constraints**: Removes independent parameter variance
8. **Contradictory Bounds**: Traffic minimum 500 vs 1000 in different files

---

## System Architecture Overview

```
┌──────────────────────────────────────────────────────────────────────┐
│                        LLM GENERATION                                 │
│  scenario_prompt.txt → LLM → JSON with:                              │
│    • scenario (title, narrative)                                     │
│    • design_params (baseline, MDE, alpha, power, traffic)            │
│    • llm_expected (simulation hints - largely unused)                │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                      DESIGN PHASE (6 Questions)                       │
│  Answers derived from LLM params + sample size formula:              │
│    Q1: MDE (pp) = baseline × target_lift × 100                       │
│    Q2: Target rate = baseline + MDE                                  │
│    Q3: Relative lift = MDE / baseline                                │
│    Q4: Sample size = z-test formula                                  │
│    Q5: Duration = sample_size / daily_traffic                        │
│    Q6: Additional conversions = traffic × MDE                        │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                        SIMULATION                                     │
│  simulate_trial() generates realistic data with:                     │
│    • ±10% baseline variation                                         │
│    • Treatment effect uncertainty (70/20/8/2% distribution)          │
│    • Returns: actual conversion counts per group                     │
└──────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌──────────────────────────────────────────────────────────────────────┐
│                    ANALYSIS PHASE (7 Questions)                       │
│  Answers derived from simulated data + z-test:                       │
│    Q1-2: Conversion rates (from sim counts)                          │
│    Q3-4: Lift metrics (from sim rates)                               │
│    Q5: P-value (two-proportion z-test)                               │
│    Q6: 95% CI (normal approximation)                                 │
│    Q7: Rollout decision (lift > MDE AND p < alpha)                   │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Plan

### Phase 1: Expand Business Context Variety ✅ COMPLETE

**Goal:** Make scenarios feel like different companies with different problems.

**Implementation Summary:**
- Expanded to 36 company types (from 7) across 5 industry categories
- Expanded to 29 user segments (from 6) across lifecycle, value, behavioral, and geographic dimensions
- Expanded to 27 KPI/metric types (from 4) including engagement, retention, and revenue metrics
- Removed keyword validation constraints from guardrails

#### 1.1 Expand Company Types & Industries
**Files:** `schemas/shared.py`, `llm/prompts/scenario_prompt.txt`

```python
class IndustryCategory(str, Enum):
    TECHNOLOGY = "Technology"
    CONSUMER = "Consumer"
    FINANCIAL = "Financial Services"
    HEALTHCARE = "Healthcare"
    INDUSTRIAL = "Industrial"

class CompanyType(str, Enum):
    # Technology
    SAAS_B2B = "B2B SaaS"
    SAAS_B2C = "B2C SaaS"
    DEVELOPER_TOOLS = "Developer Tools"
    CYBERSECURITY = "Cybersecurity"

    # Consumer
    ECOMMERCE_DTC = "DTC E-commerce"
    MARKETPLACE = "Marketplace"
    SUBSCRIPTION_BOX = "Subscription Box"
    FOOD_DELIVERY = "Food Delivery"
    TRAVEL = "Travel & Hospitality"
    GAMING = "Gaming"
    STREAMING = "Streaming Media"
    SOCIAL_NETWORK = "Social Network"
    FITNESS_APP = "Fitness/Wellness App"

    # Financial
    NEOBANK = "Neobank"
    INVESTING_APP = "Investing Platform"
    INSURANCE = "Insurtech"
    PAYMENTS = "Payments"
    LENDING = "Lending Platform"

    # Healthcare
    TELEHEALTH = "Telehealth"
    HEALTH_TRACKING = "Health Tracking"
    PHARMACY = "Digital Pharmacy"

    # Industrial
    LOGISTICS = "Logistics"
    HR_TECH = "HR Tech"
    EDTECH = "EdTech"
    REAL_ESTATE = "PropTech"
```

#### 1.2 Expand User Segments
**Files:** `schemas/shared.py`

```python
class UserSegment(str, Enum):
    # Lifecycle
    NEW_VISITORS = "first-time visitors"
    NEW_SIGNUPS = "new signups (< 7 days)"
    ACTIVATED_USERS = "activated users"
    ENGAGED_USERS = "weekly active users"
    POWER_USERS = "power users (top 10%)"
    AT_RISK_USERS = "at-risk users (no activity 14+ days)"
    CHURNED_REACTIVATION = "churned users (win-back)"

    # Value
    FREE_TIER = "free tier users"
    TRIAL_USERS = "trial users"
    PAID_USERS = "paid subscribers"
    ENTERPRISE = "enterprise accounts"
    HIGH_LTV = "high-LTV customers"

    # Behavioral
    MOBILE_USERS = "mobile app users"
    DESKTOP_USERS = "desktop users"
    HIGH_INTENT = "high-intent searchers"
    CART_ABANDONERS = "cart abandoners"
    REPEAT_PURCHASERS = "repeat purchasers"

    # Geographic
    US_USERS = "US users"
    INTERNATIONAL = "international users"
    EMERGING_MARKETS = "emerging market users"
```

#### 1.3 Expand KPIs & Metric Types
**Files:** `schemas/shared.py`, `llm/prompts/scenario_prompt.txt`

```python
class MetricType(str, Enum):
    # Conversion (current support)
    CONVERSION_RATE = "conversion_rate"
    SIGNUP_RATE = "signup_rate"
    ACTIVATION_RATE = "activation_rate"
    PURCHASE_RATE = "purchase_rate"

    # Engagement
    CLICK_THROUGH_RATE = "click_through_rate"
    ENGAGEMENT_RATE = "engagement_rate"
    FEATURE_ADOPTION = "feature_adoption_rate"
    CONTENT_COMPLETION = "content_completion_rate"

    # Retention
    DAY_7_RETENTION = "day_7_retention"
    DAY_30_RETENTION = "day_30_retention"
    CHURN_RATE = "churn_rate"

    # Revenue (requires different analysis approach)
    REVENUE_PER_USER = "revenue_per_user"
    AVERAGE_ORDER_VALUE = "average_order_value"
    ARPU = "average_revenue_per_user"
```

#### 1.4 Remove Keyword Validation
**File:** `llm/guardrails.py`

Remove lines that warn when scenarios don't include expected keywords. Let LLM generate natural narratives without template constraints.

---

### Phase 2: Expand Parameter Space ✅ COMPLETE

**Goal:** Create mathematically distinct scenarios, not just narrative variations.

**Implementation Summary:**
- Widened traffic range from 100 to 10,000,000 (100,000x range vs original 10x)
- Implemented metric-specific baseline ranges in guardrails
- Added effect size profiles (incremental, significant, transformational, defensive)
- Alpha now ranges 0.01-0.10, Power now ranges 0.80-0.95 with business justification

#### 2.1 Widen Traffic Range
**Files:** `llm/guardrails.py`, `core/types.py`, `llm/prompts/scenario_prompt.txt`

```python
# Current: 500 - 5,000 (10x range)
# Proposed: 100 - 1,000,000 (10,000x range)

TRAFFIC_TIERS = {
    "early_stage": (100, 1_000),       # MVP, beta testing
    "growth": (1_000, 10_000),          # Product-market fit
    "scale": (10_000, 100_000),         # Growth stage
    "enterprise": (100_000, 1_000_000)  # Large scale
}
```

#### 2.2 Support Different Baseline Ranges by Metric Type
**File:** `llm/guardrails.py`

```python
BASELINE_RANGES = {
    "conversion_rate": (0.001, 0.15),    # 0.1% - 15%
    "click_through_rate": (0.005, 0.30), # 0.5% - 30%
    "signup_rate": (0.01, 0.40),         # 1% - 40%
    "activation_rate": (0.10, 0.80),     # 10% - 80%
    "retention_rate": (0.05, 0.70),      # 5% - 70%
    "churn_rate": (0.01, 0.20),          # 1% - 20%
    "feature_adoption": (0.01, 0.50),    # 1% - 50%
}
```

#### 2.3 Expand Effect Size Profiles
**File:** `llm/prompts/scenario_prompt.txt`

```python
EFFECT_SIZE_PROFILES = {
    "incremental_optimization": {
        "relative_lift": (0.02, 0.10),  # 2-10% relative
        "description": "Mature product, optimizing existing flow"
    },
    "significant_change": {
        "relative_lift": (0.10, 0.30),  # 10-30% relative
        "description": "Major UX overhaul, new feature launch"
    },
    "transformational": {
        "relative_lift": (0.30, 1.00),  # 30-100% relative
        "description": "Completely new approach, high-risk test"
    },
    "defensive": {
        "relative_lift": (-0.10, 0.05), # Proving no harm
        "description": "Cost reduction, infrastructure change"
    }
}
```

#### 2.4 Vary Alpha/Power with Business Justification
**File:** `llm/prompts/scenario_prompt.txt`

Require LLM to justify alpha/power choices based on business context rather than defaulting to 0.05/0.80.

---

### Phase 3: Expand Question & Analysis Variety ✅ COMPLETE

**Goal:** Users face different analytical challenges, not the same 13 questions every time.

**Implementation Summary:**
- Created `core/question_bank.py` with 50 questions across 4 categories
- Implemented question ID-based validation in `core/validation.py`
- Added variable question set support in `core/scoring.py`
- Added selection functions with difficulty filtering and reproducible seeding
- Chi-square and Fisher's exact test implementations in `core/analyze.py` (tests pending full integration)
- Unequal allocation supported via `allocation` parameter in DesignParams

#### 3.1 Question Pool System
**Files:** New `core/question_bank.py`, modify `core/validation.py`

```python
DESIGN_QUESTION_POOL = {
    # MDE Understanding (pick 1-2)
    "mde_absolute": "What is the MDE in percentage points?",
    "mde_relative": "What is the MDE as a relative lift?",
    "mde_users": "How many additional conversions per day does this represent?",

    # Sample Size (pick 1-2)
    "sample_per_arm": "What sample size is needed per group?",
    "sample_total": "What is the total sample size needed?",
    "sample_with_imbalance": "With 70/30 allocation, what's the control group size?",

    # Duration (pick 1)
    "duration_days": "How many days will the experiment run?",
    "duration_weeks": "Approximately how many weeks?",

    # Power Analysis (new)
    "power_tradeoff": "If you only have 2 weeks, what MDE could you detect?",
    "sample_for_power": "What sample size for 95% power instead of 80%?",
}

ANALYSIS_QUESTION_POOL = {
    # Rate Calculations (pick 2)
    "control_rate": "What is the control conversion rate?",
    "treatment_rate": "What is the treatment conversion rate?",
    "pooled_rate": "What is the pooled conversion rate?",

    # Lift Calculations (pick 1-2)
    "absolute_lift": "What is the absolute lift in percentage points?",
    "relative_lift": "What is the relative lift percentage?",

    # Statistical Testing (pick 2)
    "p_value": "What is the p-value?",
    "significant_yn": "Is this result statistically significant at α=0.05?",
    "confidence_interval": "What is the 95% CI for the difference?",

    # Decision Making (pick 1-2)
    "rollout_decision": "Should you roll out this treatment?",
    "practical_significance": "Is this result practically significant?",
    "business_impact": "What's the projected annual impact?",
}
```

#### 3.2 Support Multiple Statistical Tests
**Files:** `core/analyze.py`, `core/validation.py`

```python
class TestType(str, Enum):
    TWO_PROPORTION_Z = "two_proportion_z"      # Current
    CHI_SQUARE = "chi_square"                   # Add
    FISHER_EXACT = "fisher_exact"              # Add (small samples)
    T_TEST = "t_test"                          # Add (continuous metrics)
    MANN_WHITNEY = "mann_whitney"              # Add (non-parametric)
```

#### 3.3 Support Unequal Allocation
**Files:** `core/design.py`, `llm/prompts/scenario_prompt.txt`

```python
ALLOCATION_PROFILES = {
    "standard": {"control": 0.50, "treatment": 0.50},
    "conservative": {"control": 0.80, "treatment": 0.20},
    "aggressive": {"control": 0.20, "treatment": 0.80},
}
```

---

### Phase 4: Add Scenario Complexity Dimensions ✅ COMPLETE

**Goal:** Introduce realistic complications that require deeper thinking.

**Implementation Summary:**
- Created `schemas/complications.py` with 17 complication types across 4 categories
- Added 12 planning questions (hypothesis formulation, test selection, experimental design)
- Added 13 interpretation questions (business recommendations, limitations, follow-up)
- Complication templates with severity levels, mitigation hints, and additional questions

#### 4.1 Add Contextual Complications
**File:** `llm/prompts/scenario_prompt.txt`, new `schemas/complications.py`

```python
class ScenarioComplication(str, Enum):
    NONE = "none"
    SEASONALITY = "seasonality"
    TIME_PRESSURE = "time_pressure"
    OPPORTUNITY_COST = "opportunity_cost"
    SEGMENT_EFFECTS = "segment_effects"
    NOVELTY_EFFECT = "novelty_effect"
    MULTIPLE_TESTING = "multiple_testing"
```

#### 4.2 Add Planning Questions (Pre-Analysis)

```python
PLANNING_QUESTIONS = {
    "hypothesis": "State your null and alternative hypotheses",
    "test_selection": "Which statistical test is most appropriate?",
    "assumptions": "What assumptions must hold for this test?",
    "guardrail_metrics": "What guardrail metrics should you monitor?",
}
```

#### 4.3 Add Interpretation Questions (Post-Analysis)

```python
INTERPRETATION_QUESTIONS = {
    "practical_vs_statistical": "Is this practically significant?",
    "business_recommendation": "What's your recommendation to stakeholders?",
    "follow_up": "What follow-up experiments would you suggest?",
    "limitations": "What are the limitations of this experiment?",
}
```

---

### Phase 5: Restructure LLM Prompt ✅ COMPLETE

**Goal:** Remove template archetypes, encourage creative scenario generation.

**Implementation Summary:**
- Completely rewrote `llm/prompts/scenario_prompt.txt` - removed 30 hardcoded templates
- Prompt trimmed to fit GPT-4 context window while maintaining rich variety guidance
- Implemented `NoveltyScorer` class in `llm/guardrails.py` with feature extraction
- Integrated novelty scoring into `llm/generator.py` - scores and records all scenarios
- Generator now returns novelty_score and diversity_suggestions in results

#### 5.1 New Prompt Philosophy

- Remove the 30 hardcoded scenario archetypes
- Provide parameter ranges without forcing specific patterns
- Add diversity scoring to avoid repetition
- Include example scenarios that demonstrate variety

#### 5.2 Add Scenario Novelty Scoring
**File:** `llm/guardrails.py`

```python
def score_scenario_novelty(scenario, recent_scenarios):
    """Score how different this scenario is from recent ones."""
    novelty_score = 1.0

    for recent in recent_scenarios:
        if scenario.company_type == recent.company_type:
            novelty_score -= 0.2
        if abs(scenario.baseline - recent.baseline) < 0.02:
            novelty_score -= 0.1
        if similar_traffic_range(scenario, recent):
            novelty_score -= 0.1

    return max(0, novelty_score)
```

---

## Files to Modify

| File | Changes |
|------|---------|
| `schemas/shared.py` | Expand enums (CompanyType, UserSegment, MetricType) |
| `llm/prompts/scenario_prompt.txt` | Complete rewrite, remove templates |
| `llm/guardrails.py` | Widen bounds, remove keyword validation, add novelty scoring |
| `core/types.py` | Fix traffic minimum contradiction |
| `core/validation.py` | Support dynamic tolerances, new question types |
| `core/scoring.py` | Support variable question sets |
| `core/question_bank.py` | New file for question pool system |
| `schemas/complications.py` | New file for scenario complications |
| `ui/streamlit_app.py` | Display new question types, handle variable flows |

---

## Implementation Priority

| Phase | Effort | Impact | Priority |
|-------|--------|--------|----------|
| **Phase 1**: Business Context | Medium | High | 🥇 First |
| **Phase 2**: Parameter Space | Low | High | 🥇 First |
| **Phase 5**: Prompt Restructure | Medium | High | 🥈 Second |
| **Phase 3**: Question Variety | High | Medium | 🥉 Third |
| **Phase 4**: Complications | High | Medium | 🥉 Third |

---

## Success Metrics

After implementation, we should see:

1. **Company Type Distribution**: Even spread across 20+ types (vs clustering in 7)
2. **Traffic Range Usage**: Full spectrum from 100 to 1M (vs 500-5K)
3. **Baseline Variety**: Different ranges based on metric type
4. **Question Variety**: Users see different question combinations
5. **Narrative Uniqueness**: Less template language, more creative scenarios

---

## Testing Strategy

1. **Unit Tests**: Update existing tests for new enums and bounds
2. **Integration Tests**: Verify LLM → quiz flow with new parameters
3. **Scenario Diversity Tests**: Generate 100 scenarios, measure distribution
4. **Regression Tests**: Ensure existing functionality still works

---

---

## Remaining Work

### UI Integration (streamlit_app.py) ✅ COMPLETE
The Streamlit UI has been updated with:

1. **Variable Question Selection**: Questions selected based on difficulty setting
2. **Planning Phase UI**: Optional section for planning questions before design phase
3. **Interpretation Phase UI**: Optional section for interpretation questions after analysis
4. **Difficulty Selector**: Users can choose EASY, MEDIUM, HARD, or MIXED difficulty
5. **Question Pool Summary**: Shows total questions available in each category

### Statistical Test Full Integration (Lower Priority)
While chi-square and Fisher's exact tests are implemented in `core/analyze.py`, their integration needs:

1. **Test Selection Logic**: Automatic selection based on sample size and metric type
2. **UI Display**: Show which test was used and why
3. **Question Pool Integration**: Add questions about test selection and assumptions

---

## Test Coverage Summary

| Test File | Tests | Status |
|-----------|-------|--------|
| `tests/core/test_question_bank.py` | 47 | ✅ Pass |
| `tests/core/test_validation_by_id.py` | 37 | ✅ Pass |
| `tests/core/test_scoring_variable.py` | 14 | ✅ Pass |
| `tests/llm/test_novelty_scoring.py` | 23 | ✅ Pass |
| **Full Suite** | 445 | ✅ Pass (5 skipped) |

---

## Changelog

- **2025-01-25**: UI Integration complete - Added planning/interpretation phases, difficulty selector, question pool summary
- **2025-01-25**: Phase 4.2-4.3 complete - Added 25 planning/interpretation questions, integrated novelty scorer into generator
- **2025-01-24**: Phases 1-5 core implementation complete - Question bank, novelty scoring, variable scoring
- **2025-01-24**: Initial plan created based on codebase review
