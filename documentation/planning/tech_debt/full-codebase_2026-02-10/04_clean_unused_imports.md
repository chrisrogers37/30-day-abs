# Phase 04: Clean Unused Imports

**Status**: ✅ COMPLETE
**Started**: 2026-02-10
**Completed**: 2026-02-10
**PR Title**: `chore: remove unused imports across codebase`
**Risk Level**: Low (no behavior change)
**Effort**: 1 hour
**Depends On**: None
**Blocks**: None

### Notes
- Plan estimated 8 unused imports. After Phases 01-03, ruff found **137 unused imports** across 47 files.
- 133 auto-fixed by ruff, 4 remaining are intentional (test_basic.py import-verification pattern).
- Major cleanup in `ui/streamlit_app.py`, `llm/` modules, and test files.

---

## Problem Statement

7+ files contain unused imports that clutter the code, slow down IDE navigation, and may confuse contributors into thinking removed features are still used.

---

## Inventory

| File | Line | Unused Import | How to Verify |
|------|------|---------------|---------------|
| `core/design.py` | 162 (inside `_normal_cdf`) | `import math` | `math` is already imported at module level (line 8). This inner import is redundant. |
| `core/simulate.py` | 10 | `Tuple` from typing | Grep for `Tuple` in file — not used in any type annotation. |
| `core/simulate.py` | 10 | `Optional` from typing | Grep for `Optional` in file — not used in any type annotation. |
| `core/utils.py` | 9 | `Union` from typing | Grep for `Union` in file — not used in any type annotation. |
| `core/rng.py` | 8 | `import random` | Module uses numpy's RNG exclusively. Grep for `random.` calls — none exist. |
| `core/question_bank.py` | (near top) | `Callable` from typing | Grep for `Callable` in file — not used in any type annotation. |
| `llm/client.py` | (near top) | `import httpx` | Grep for `httpx.` calls — none exist (client uses `openai` SDK). |
| `llm/client.py` | 560 | `import os` | `os` is already imported at module level. This inner import is redundant. |

**Note**: Run `ruff check --select F401 .` to automatically detect all unused imports. The list above is from manual inspection and may not be exhaustive.

---

## Implementation Plan

### Step 1: Use ruff to find all unused imports

```bash
cd /Users/chris/Projects/30-day-abs
source venv/bin/activate
ruff check --select F401 .
```

This will give an authoritative list. The manual inventory above may miss some or include false positives.

### Step 2: Auto-fix with ruff

```bash
ruff check --select F401 --fix .
```

This automatically removes unused imports. Review the changes with `git diff` to ensure nothing important was removed.

### Step 3: Manual fixes ruff can't handle

Ruff may not catch:
- **Redundant inner imports** (like `import math` inside a function when `math` is already imported at module level). These need manual removal.
- **`from .module import *`** — star imports can't be checked by ruff without type stubs.

Manually fix:
- `core/design.py:162`: Remove `import math` from inside `_normal_cdf()` function body (if Phase 02 hasn't already removed this function from design.py)

### Step 4: Run tests

```bash
pytest tests/ -v
pytest  # Full suite
```

---

## Verification Checklist

- [ ] `ruff check --select F401 .` returns no errors
- [ ] `git diff` shows only import line removals (no logic changes)
- [ ] `pytest` passes — 452+ tests, 0 failures
- [ ] No inner `import` statements that duplicate module-level imports

---

## What NOT To Do

- **Do NOT remove imports that are re-exported** for use by other modules (e.g., `schemas/__init__.py` uses `from .shared import *` intentionally).
- **Do NOT remove imports used only in type annotations** — `from __future__ import annotations` can make imports appear unused to linters when they're needed at runtime.
- **Do NOT add `# noqa: F401` comments** unless the import is intentionally re-exported.
- **Do NOT combine this with any logic changes** — this PR should be exclusively import cleanup.
