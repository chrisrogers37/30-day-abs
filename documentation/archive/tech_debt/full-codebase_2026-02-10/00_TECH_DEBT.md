# Tech Debt Master Inventory

**Scan Date**: 2026-02-10
**Scanned By**: Claude Opus 4.6 automated analysis
**Codebase Version**: 1.5.1 (commit `53ee92d`)
**Test Baseline**: 452 passing, 4 skipped, 0 failures (456 total)

---

## Executive Summary

18 tech debt items identified across 3 severity levels. The codebase is structurally sound but has accumulated duplication in statistical functions, a critical bug in Fisher's exact test routing, and 4 modules with 0% test coverage. The recommended remediation is organized into 8 PRs, each independently mergeable (respecting the dependency chain below).

**Estimated total effort**: ~40-60 hours of engineering time
**Risk if unaddressed**: Incorrect statistical results shown to users (Fisher's exact bug), maintenance burden from duplicated code, and blind spots from untested modules.

---

## Severity Scoring

| Severity | Criteria | Count |
|----------|----------|-------|
| **HIGH** | Produces incorrect results, data loss risk, or blocks other work | 3 |
| **MEDIUM** | Increases maintenance burden, reduces code quality, or masks bugs | 9 |
| **LOW** | Cosmetic, style, or minor inefficiency issues | 6 |

---

## Prioritized Inventory

| # | Item | Severity | Phase | Files Affected | Effort |
|---|------|----------|-------|----------------|--------|
| 1 | Fisher's exact test silently falls back to chi-square for n>100 | **HIGH** | [01](./01_fix_fisher_exact_and_chi_square.md) | `core/analyze.py` | 2-3h |
| 2 | Chi-square CDF uses crude approximation for df>1 | **HIGH** | [01](./01_fix_fisher_exact_and_chi_square.md) | `core/analyze.py` | 1-2h |
| 3 | Broad `except Exception` in 12 locations across LLM module | **HIGH** | [07](./07_narrow_except_clauses.md) | `llm/*.py`, `schemas/__init__.py`, `core/validation.py` | 3-4h |
| 4 | `_normal_cdf()` duplicated in 3 files | **MEDIUM** | [02](./02_consolidate_duplicated_functions.md) | `core/analyze.py`, `core/design.py`, `core/utils.py` | 2-3h |
| 5 | `_calculate_achieved_power()` duplicated in 2 files | **MEDIUM** | [02](./02_consolidate_duplicated_functions.md) | `core/analyze.py`, `core/design.py` | 1-2h |
| 6 | `_calculate_effect_size()` duplicated in 2 files | **MEDIUM** | [02](./02_consolidate_duplicated_functions.md) | `core/analyze.py`, `core/utils.py` | 1h |
| 7 | `_calculate_confidence_interval()` duplicated in 2 files | **MEDIUM** | [02](./02_consolidate_duplicated_functions.md) | `core/analyze.py`, `core/utils.py` | 1h |
| 8 | `calculate_minimum_detectable_effect()` duplicated in 2 files | **MEDIUM** | [02](./02_consolidate_duplicated_functions.md) | `core/design.py`, `core/utils.py` | 1h |
| 9 | Magic numbers throughout core module | **MEDIUM** | [03](./03_extract_named_constants.md) | `core/analyze.py`, `core/simulate.py`, `core/design.py` | 2-3h |
| 10 | Scoring boilerplate repeated 12x in `validation.py` | **MEDIUM** | [05](./05_extract_scoring_helper.md) | `core/validation.py` | 3-4h |
| 11 | DTO-to-core conversion duplicated between LLM and UI | **MEDIUM** | [06](./06_extract_shared_helpers.md) | `llm/integration.py`, `ui/streamlit_app.py` | 2-3h |
| 12 | Question selection logic duplicated 4x in `question_bank.py` | **MEDIUM** | [06](./06_extract_shared_helpers.md) | `core/question_bank.py` | 1-2h |
| 13 | 4 modules with 0% test coverage (~2,050 lines) | **MEDIUM** | [08](./08_add_missing_test_coverage.md) | `tests/` (new files) | 12-16h |
| 14 | Unused imports in 7+ files | **LOW** | [04](./04_clean_unused_imports.md) | Multiple files | 1h |
| 15 | Redundant `import math` inside `_normal_cdf` in `design.py` | **LOW** | [04](./04_clean_unused_imports.md) | `core/design.py` | <5min |
| 16 | Global mutable state in 3 modules | **LOW** | Deferred | `core/rng.py`, `core/logging.py`, `llm/guardrails.py` | 4-6h |
| 17 | TODO comments (2 instances) | **LOW** | Deferred | `llm/client.py:255`, `llm/parser.py:420` | 1h |
| 18 | Complex function signatures (>7 params) | **LOW** | Deferred | `core/validation.py`, `core/scoring.py` | 2-3h |

---

## Dependency Matrix

```
Phase 01: Fix Fisher's exact + chi-square CDF
  └─ Phase 02: Consolidate duplicated functions (depends on 01)
       └─ Phase 03: Extract named constants (depends on 02)

Phase 04: Clean unused imports (independent)
Phase 05: Extract scoring helper (independent)
Phase 06: Extract shared helpers (independent)
Phase 07: Narrow except clauses (independent)

Phase 08: Add missing test coverage (should run LAST, after code stabilizes)
```

**Critical path**: 01 → 02 → 03 (must be done in order)
**Parallelizable**: 04, 05, 06, 07 can be done in any order, concurrently with 01-03

---

## Phase Plans

| Phase | PR Title | Risk | Effort | Depends On |
|-------|----------|------|--------|------------|
| [01](./01_fix_fisher_exact_and_chi_square.md) | fix(core): use scipy for Fisher's exact and chi-square tests | Medium | 3-5h | None | ✅ PR #9 |
| [02](./02_consolidate_duplicated_functions.md) | refactor(core): consolidate duplicated statistical functions | Low | 4-6h | Phase 01 | ✅ PR #10 |
| [03](./03_extract_named_constants.md) | refactor(core): extract magic numbers to named constants | Low | 2-3h | Phase 02 | ✅ PR #11 |
| [04](./04_clean_unused_imports.md) | chore: remove unused imports across codebase | Low | 1h | None | ✅ PR #12 |
| [05](./05_extract_scoring_helper.md) | refactor(core): extract scoring helper to reduce validation boilerplate | Low | 3-4h | None | ✅ PR #13 |
| [06](./06_extract_shared_helpers.md) | refactor: extract shared DTO conversion and question selection helpers | Low | 3-5h | None | ✅ PR #14 |
| [07](./07_narrow_except_clauses.md) | fix(llm): narrow broad except clauses to specific exceptions | Low | 3-4h | None | ✅ PR #15 |
| [08](./08_add_missing_test_coverage.md) | test: add coverage for 0% modules | Low | 12-16h | All above |

---

## Coverage Snapshot (Pre-Remediation)

| Module | Coverage | Notes |
|--------|----------|-------|
| `core/analyze.py` | 95% | |
| `core/design.py` | 63% | Low - needs attention |
| `core/logging.py` | 99% | |
| `core/question_bank.py` | 98% | |
| `core/rng.py` | 93% | |
| `core/scoring.py` | 92% | |
| `core/simulate.py` | 97% | |
| `core/types.py` | 82% | |
| `core/utils.py` | 91% | |
| `core/validation.py` | 89% | |
| `llm/client.py` | 53% | |
| `llm/generator.py` | **0%** | No test file |
| `llm/integration.py` | **0%** | No test file |
| `llm/guardrails.py` | 46% | |
| `llm/parser.py` | 17% | |
| `schemas/complications.py` | **0%** | No test file |
| `ui/streamlit_app.py` | **0%** | 1830 lines untested |
| **TOTAL** | **54%** | |

---

## How to Use These Plans

1. **Read this file first** to understand scope and dependencies
2. **Pick the next phase** according to the dependency matrix
3. **Read that phase's plan file** for exact implementation steps
4. **Follow the verification checklist** at the end of each plan
5. **Run the full test suite** before and after each PR: `pytest`
6. **Do NOT combine phases** into a single PR unless explicitly noted

---

**Last Updated**: 2026-02-10
