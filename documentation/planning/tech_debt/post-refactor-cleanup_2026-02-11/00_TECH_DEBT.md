# Tech Debt Report: Post-Refactor Cleanup

**Session:** `post-refactor-cleanup_2026-02-11`
**Date:** 2026-02-11
**Scope:** Full codebase scan after completion of 8-phase tech debt remediation (PRs #9-#16)

---

## Executive Summary

The codebase is in good health following the Phase 01-08 remediation. No critical issues remain. The findings below are **maintainability improvements** — structural duplication, excessive parameter counts, and deep nesting that increase cognitive load and bug surface area.

**Key metrics:**
- Test coverage: 25/25 source modules have test files
- Unused imports: 0 found
- Commented-out code: 0 found
- Broad except clauses: 0 remaining
- TODO/FIXME comments: 2 remaining (both low priority)
- Outdated dependencies: 93 packages (no action planned — major version bumps risk breaking changes)

---

## Inventory of Findings

### Finding 1: Duplicated Analysis Flow in `core/analyze.py`

| Attribute | Value |
|-----------|-------|
| **Severity** | High |
| **Blast Radius** | Medium — statistical correctness |
| **Complexity** | Low |
| **Risk** | Low |
| **Files** | `core/analyze.py` |

**Description:** The three statistical test functions (`_two_proportion_z_test`, `_chi_square_test`, `_fisher_exact_test`) duplicate the same post-test flow: extract proportions, compute CI, compute effect size, compute power, generate recommendation, build `AnalysisResult`. The shared steps should be extracted to a helper.

**Lines affected:** 173-344

---

### Finding 2: Excessive Parameter Counts in Scoring Functions

| Attribute | Value |
|-----------|-------|
| **Severity** | High |
| **Blast Radius** | Medium — scoring/validation API surface |
| **Complexity** | Medium |
| **Risk** | Low |
| **Files** | `core/validation.py`, `core/scoring.py` |

**Description:** Three functions accept 8-9 parameters each:
- `score_answers_by_id()` — 8 params (validation.py:808)
- `validate_answer_by_id()` — 8 params (validation.py:720)
- `create_variable_quiz_result()` — 8 params (scoring.py:481)

These share 6 common context parameters (`design_params`, `sample_size_result`, `sim_result`, `mde_absolute`, `business_target_absolute`, `alpha`) that should be bundled into a `ScoringContext` dataclass.

---

### Finding 3: Deeply Nested Retry Logic in `llm/client.py`

| Attribute | Value |
|-----------|-------|
| **Severity** | Medium |
| **Blast Radius** | Low — LLM module only |
| **Complexity** | Low |
| **Risk** | Low |
| **Files** | `llm/client.py` |

**Description:** `generate_completion()` (lines 261-404) mixes message preparation, retry logic with exponential backoff, provider-specific branching, and response construction in a single method at 4-5 levels of nesting. The retry loop should be extracted.

---

### Finding 4: Duplicated Similarity Calculation in `NoveltyScorer`

| Attribute | Value |
|-----------|-------|
| **Severity** | Medium |
| **Blast Radius** | Low — novelty scoring only |
| **Complexity** | Low |
| **Risk** | Low |
| **Files** | `llm/guardrails.py` |

**Description:** `score_novelty()` (lines 813-892) computes feature similarity twice — once for average similarity (lines 831-866) and again for recency-weighted similarity (lines 873-884). The similarity calculation should be extracted to a helper and computed once per scenario.

Additionally, `_extract_features()` (lines 762-811) has three nearly identical if-elif tier classification blocks that could use a shared helper.

---

### Finding 5: Redundant Power Calculation in `core/utils.py`

| Attribute | Value |
|-----------|-------|
| **Severity** | Low |
| **Blast Radius** | Low |
| **Complexity** | Low |
| **Risk** | Low |
| **Files** | `core/utils.py` |

**Description:** `calculate_power_for_proportions(p1, p2, n, alpha)` (line 300) duplicates the logic in `calculate_achieved_power(p1, p2, n1, n2, alpha, direction)` (line 385). The former is a special case (equal n, two-tailed) that should delegate to the latter.

---

### Finding 6: Duplicated Categorical Generators in `core/simulate.py`

| Attribute | Value |
|-----------|-------|
| **Severity** | Low |
| **Blast Radius** | Low |
| **Complexity** | Low |
| **Risk** | Low |
| **Files** | `core/simulate.py` |

**Description:** `_generate_device_type()` (line 251) and `_generate_traffic_source()` (line 264) are identical `random.choices()` calls differing only in the data arrays. Should be a single parameterized function.

---

### Finding 7: Duplicated Answer Key Generation Loop in `core/scoring.py`

| Attribute | Value |
|-----------|-------|
| **Severity** | Low |
| **Blast Radius** | Low |
| **Complexity** | Low |
| **Risk** | Low |
| **Files** | `core/scoring.py` |

**Description:** `generate_variable_design_answer_key()` (line 354) and `generate_variable_analysis_answer_key()` (line 398) share an identical loop pattern: iterate question IDs, look up question, calculate answer, catch errors. Should be extracted to a shared helper.

---

### Finding 8: TODO Comments (2 remaining)

| Attribute | Value |
|-----------|-------|
| **Severity** | Low |
| **Blast Radius** | Low |
| **Complexity** | Low |
| **Risk** | Low |
| **Files** | `llm/parser.py`, `llm/client.py` |

**Description:**
- `llm/parser.py:419` — Hardcoded timestamp `"2024-01-01T00:00:00Z"` should use `datetime.now().isoformat()`.
- `llm/client.py:254` — `# TODO: Implement Anthropic client`. This is a known limitation, not tech debt. Will be documented with a note rather than implemented.

---

### Deferred: `ui/streamlit_app.py` (1,812 lines)

This monolithic UI file is the largest in the codebase and handles multiple responsibilities. Splitting it requires understanding Streamlit session state patterns and is **high-risk, high-effort**. Recommend deferring to a dedicated UI refactoring initiative after feature development stabilizes.

---

## Prioritized Remediation Order

| Phase | Finding | Priority | Effort | Files Modified |
|-------|---------|----------|--------|----------------|
| 01 | Extract shared analysis result builder | High | Small | `core/analyze.py` | ✅ COMPLETE |
| 02 | Introduce `ScoringContext` dataclass | High | Medium | `core/validation.py`, `core/scoring.py` |
| 03 | Extract retry logic from LLM client | Medium | Small | `llm/client.py` |
| 04 | Deduplicate NoveltyScorer similarity calc | Medium | Small | `llm/guardrails.py` |
| 05 | Consolidate power calculation via delegation | Low | Small | `core/utils.py` |
| 06 | Consolidate categorical generators | Low | Small | `core/simulate.py` |
| 07 | Extract shared answer key generation loop | Low | Small | `core/scoring.py` |
| 08 | Fix hardcoded timestamp + document Anthropic TODO | Low | Small | `llm/parser.py`, `llm/client.py` |

---

## Dependency Matrix

```
Phase 01 ──── (independent, can run in parallel)
Phase 02 ──── (independent, can run in parallel)
Phase 03 ──── (independent, can run in parallel)
Phase 04 ──── (independent, can run in parallel)
Phase 05 ──── (independent, can run in parallel)
Phase 06 ──── (independent, can run in parallel)
Phase 07 ──── BLOCKED BY Phase 02 (both modify core/scoring.py)
Phase 08 ──── BLOCKED BY Phase 03 (both modify llm/client.py)
```

### Parallel Execution Groups

| Group | Phases | Can run simultaneously |
|-------|--------|----------------------|
| A | 01, 02, 03, 04, 05, 06 | Yes — all touch disjoint files |
| B | 07 | After Phase 02 merges |
| C | 08 | After Phase 03 merges |

---

## Out of Scope

- **Dependency upgrades** (93 outdated packages): Major version bumps (numpy 2.x, pandas 3.x, openai 2.x) require dedicated migration efforts. Not included in this remediation round.
- **UI refactoring** (`streamlit_app.py`): Deferred to dedicated initiative.
- **Anthropic client implementation**: Known feature gap, not tech debt.
