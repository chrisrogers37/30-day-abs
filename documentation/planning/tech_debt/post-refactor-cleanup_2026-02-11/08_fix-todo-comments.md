# Phase 08: Fix Hardcoded Timestamp and Document Anthropic TODO

**Status:** ✅ COMPLETE
**Started:** 2026-02-11
**Completed:** 2026-02-11
**PR Title:** `fix(llm): replace hardcoded timestamp with datetime.now()`
**Risk Level:** Low
**Estimated Effort:** Small (15 minutes)
**Files Modified:** `llm/parser.py`, `llm/client.py`
**Dependencies:** None
**Blocks:** None

---

## Problem

Two TODO comments remain in the codebase:

1. **`llm/parser.py` line 419** -- `created_at="2024-01-01T00:00:00Z"  # TODO: Use actual timestamp`
   This hardcodes a stale date instead of using the actual generation time. Every parsed scenario gets the same fake timestamp, which makes it impossible to tell when a scenario was actually generated.

2. **`llm/client.py` line 254** -- `# TODO: Implement Anthropic client`
   This is a known feature gap, not tech debt. The TODO should be replaced with a descriptive comment documenting the intentional limitation.

---

## Implementation

### Step 1: Fix the hardcoded timestamp in `llm/parser.py`

**File:** `/Users/chris/Projects/30-day-abs/llm/parser.py`

First, add the `datetime` and `timezone` imports. The file already imports `json`, `re`, `Dict`, `List`, `Optional`, and `dataclass` (lines 76-79). Add the new import after the existing standard library imports.

**Before** (lines 76-77):
```python
import json
import re
```

**After:**
```python
import json
import re
from datetime import datetime, timezone
```

Then change line 419 inside the `_validate_schema()` method:

**Before** (line 419):
```python
                created_at="2024-01-01T00:00:00Z"  # TODO: Use actual timestamp
```

**After:**
```python
                created_at=datetime.now(timezone.utc).isoformat()
```

**Context:** This line is inside `_validate_schema()` (line 379), within the `ScenarioResponseDTO` constructor call (lines 413-420). The full constructor call after the change looks like:

```python
            response_dto = ScenarioResponseDTO(
                scenario=scenario_dto,
                design_params=design_dto,
                llm_expected=llm_expected_dto,
                generation_metadata={"parser": "llm_parser", "version": "1.0"},
                scenario_id=f"scenario_{hash(str(data)) % 1000000:06d}",
                created_at=datetime.now(timezone.utc).isoformat()
            )
```

### Step 2: Replace the Anthropic TODO with a documented note in `llm/client.py`

**File:** `/Users/chris/Projects/30-day-abs/llm/client.py`

**Before** (lines 253-255 inside `_setup_client()`):
```python
        elif self.config.provider == LLMProvider.ANTHROPIC:
            # TODO: Implement Anthropic client
            raise NotImplementedError("Anthropic client not yet implemented")
```

**After:**
```python
        elif self.config.provider == LLMProvider.ANTHROPIC:
            # Anthropic provider is defined in LLMProvider enum for future use.
            # Implementation tracked separately from tech debt remediation.
            raise NotImplementedError("Anthropic client not yet implemented")
```

---

## Verification Checklist

1. Run parser tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/llm/test_parser.py -v
   ```

2. Run client tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/llm/test_client.py -v
   ```

3. Verify the timestamp is now a valid ISO 8601 string. Any test that creates a `ScenarioResponseDTO` via the parser should produce a `created_at` value starting with `"202"` (current year prefix), not the old `"2024-01-01T00:00:00Z"`. You can spot-check in a REPL:
   ```python
   from llm.parser import LLMOutputParser
   import json
   parser = LLMOutputParser()
   # Use the fallback scenario which internally calls _validate_schema
   result = parser.create_fallback_scenario()
   assert result.created_at.startswith("202"), f"Unexpected timestamp: {result.created_at}"
   ```

4. Verify no remaining TODO comments in the `llm/` directory:
   ```bash
   grep -rn "TODO" llm/ --include="*.py"
   ```
   This should return zero results.

5. Run broader tests:
   ```bash
   /Users/chris/Projects/30-day-abs/venv/bin/python3 -m pytest tests/ --ignore=tests/integration -x -q
   ```

---

## What NOT To Do

1. **Do NOT implement the Anthropic client.** That is a feature, not tech debt.
2. **Do NOT remove the `LLMProvider.ANTHROPIC` enum value** (line 84 in `llm/client.py`). It may be referenced in tests or configuration.
3. **Do NOT use `datetime.utcnow()`.** It is deprecated in Python 3.12+. Use `datetime.now(timezone.utc)` instead.
4. **Do NOT remove the `NotImplementedError` for Anthropic.** It correctly signals that the provider is not available.
5. **Do NOT change any test assertions** that check for the old hardcoded timestamp. Instead, update those assertions to accept a dynamic ISO 8601 string (e.g., assert `created_at.startswith("202")` or use `datetime.fromisoformat()` to validate the format).
