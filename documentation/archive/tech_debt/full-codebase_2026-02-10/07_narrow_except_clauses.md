# Phase 07: Narrow Broad Except Clauses to Specific Exceptions

**Status**: ✅ COMPLETE
**Started**: 2026-02-10
**Completed**: 2026-02-10
**PR Title**: `fix(llm): narrow broad except clauses to specific exceptions`
**Risk Level**: Low (makes errors more visible, not less)
**Effort**: 3-4 hours
**Depends On**: None
**Blocks**: None

---

## Problem Statement

12 locations across the codebase use `except Exception` (or bare `except:`) which catches every possible error, including:
- `KeyboardInterrupt` (user trying to cancel)
- `SystemExit` (graceful shutdown)
- `MemoryError` (out of memory)
- Programming bugs (`TypeError`, `AttributeError`, `NameError`)

This makes debugging extremely difficult because real bugs are silently caught and either ignored or wrapped in generic error messages.

---

## Inventory

| # | File | Line | Context | Current Handling | Should Catch |
|---|------|------|---------|------------------|--------------|
| 1 | `llm/generator.py` | 369 | LLM API call retry | Logs and retries | `openai.APIError`, `openai.APITimeoutError`, `openai.RateLimitError` |
| 2 | `llm/generator.py` | 386 | JSON parse failure | Logs and retries | `json.JSONDecodeError`, `KeyError`, `ValueError` |
| 3 | `llm/generator.py` | 409 | Guardrail validation | Logs error | `ValueError`, `TypeError` |
| 4 | `llm/generator.py` | 413 | Outer generation wrapper | Returns error result | `openai.APIError`, `json.JSONDecodeError`, `ValueError` |
| 5 | `llm/parser.py` | 273 | JSON extraction | Returns None | `json.JSONDecodeError`, `KeyError` |
| 6 | `llm/parser.py` | 362 | Schema validation | Returns False | `pydantic.ValidationError`, `ValueError` |
| 7 | `llm/parser.py` | 376 | Field conversion | Returns original | `ValueError`, `TypeError` |
| 8 | `llm/parser.py` | 425 | Timestamp parsing | Returns fallback | `ValueError` |
| 9 | `llm/parser.py` | 474 | Nested JSON parse | Returns None | `json.JSONDecodeError`, `KeyError` |
| 10 | `llm/integration.py` | 316 | Pipeline orchestration | Returns error result | Combine specific exceptions from steps 1-9 |
| 11 | `llm/client.py` | 389 | API call wrapper | Logs and re-raises | `openai.APIError`, `httpx.HTTPError` |
| 12 | `llm/guardrails.py` | 348 | Parameter validation | Returns validation error | `ValueError`, `TypeError`, `KeyError` |
| 13 | `schemas/__init__.py` | 21 | Model rebuild | Silently passes | `pydantic.ConfigError`, `AttributeError` |
| 14 | `core/validation.py` | 931 | Answer calculation | Returns "N/A" | `ValueError`, `TypeError`, `KeyError` |
| 15 | `core/validation.py` | 964 | Answer validation | Returns error dict | `ValueError`, `TypeError` |

---

## Implementation Plan

### Principle

For each `except Exception`, determine:
1. **What operations** are in the try block?
2. **What exceptions** can those operations actually raise?
3. **Is the handling appropriate** for those specific exceptions?

Then narrow the catch to only those specific exceptions.

### Step 1: Fix `llm/generator.py` (4 locations)

Read the full function context around each line to understand the try block.

**Line 369** (LLM API call):
```python
# BEFORE:
except Exception as e:
    logger.warning(f"LLM call failed: {e}")

# AFTER:
except (openai.APIError, openai.APITimeoutError, openai.RateLimitError, ConnectionError) as e:
    logger.warning(f"LLM call failed: {e}")
```

**Line 386** (JSON parsing):
```python
# BEFORE:
except Exception as e:
    logger.warning(f"Parse failed: {e}")

# AFTER:
except (json.JSONDecodeError, KeyError, ValueError, TypeError) as e:
    logger.warning(f"Parse failed: {e}")
```

**Line 409** (Guardrail validation):
```python
# BEFORE:
except Exception as e:
    logger.error(f"Validation error: {e}")

# AFTER:
except (ValueError, TypeError, KeyError) as e:
    logger.error(f"Validation error: {e}")
```

**Line 413** (Outer wrapper):
```python
# BEFORE:
except Exception as e:
    return GenerationResult(success=False, error=str(e))

# AFTER:
except (openai.APIError, json.JSONDecodeError, ValueError, TypeError, KeyError, ConnectionError) as e:
    return GenerationResult(success=False, error=str(e))
```

### Step 2: Fix `llm/parser.py` (5 locations)

**Line 273** (JSON extraction):
```python
# AFTER:
except (json.JSONDecodeError, KeyError, IndexError) as e:
```

**Line 362** (Schema validation):
```python
# AFTER:
from pydantic import ValidationError
except (ValidationError, ValueError, TypeError) as e:
```

**Line 376** (Field conversion):
```python
# AFTER:
except (ValueError, TypeError) as e:
```

**Line 425** (Timestamp parsing):
```python
# AFTER:
except ValueError as e:
```

**Line 474** (Nested JSON):
```python
# AFTER:
except (json.JSONDecodeError, KeyError, TypeError) as e:
```

### Step 3: Fix `llm/client.py` (1 location)

**Line 389**:
```python
# AFTER:
except (openai.APIError, openai.APITimeoutError, openai.RateLimitError,
        openai.AuthenticationError, ConnectionError) as e:
```

### Step 4: Fix `llm/guardrails.py` (1 location)

**Line 348**:
```python
# AFTER:
except (ValueError, TypeError, KeyError) as e:
```

### Step 5: Fix `llm/integration.py` (1 location)

**Line 316**:
```python
# AFTER:
except (openai.APIError, json.JSONDecodeError, ValueError, TypeError,
        KeyError, ConnectionError) as e:
```

### Step 6: Fix `schemas/__init__.py` (1 location)

**Line 21**:
```python
# BEFORE:
except Exception:
    pass

# AFTER:
except (AttributeError, TypeError) as e:
    # model_rebuild() can fail if forward references are unresolvable
    # This is non-critical — models still work for basic functionality
    pass
```

### Step 7: Fix `core/validation.py` (2 locations)

**Line 931**:
```python
# BEFORE:
except Exception:
    correct, tolerance = "N/A", 0

# AFTER:
except (ValueError, TypeError, KeyError) as e:
    correct, tolerance = "N/A", 0
```

**Line 964**:
```python
# BEFORE:
except Exception as e:
    scores[question_id] = {
        "correct": False,
        "user": user_answer,
        "correct_answer": f"Error: {str(e)}",
        "tolerance": 0
    }

# AFTER:
except (ValueError, TypeError, KeyError) as e:
    scores[question_id] = {
        "correct": False,
        "user": user_answer,
        "correct_answer": f"Error: {str(e)}",
        "tolerance": 0
    }
```

### Step 8: Add necessary imports

For each file, ensure the specific exception types are imported:

```python
# llm/generator.py - add near top:
import json
import openai

# llm/parser.py - add near top:
import json
from pydantic import ValidationError

# llm/client.py - verify openai is imported

# llm/integration.py - add:
import json
import openai
```

### Step 9: Run tests

```bash
pytest tests/ -v
pytest  # Full suite
```

---

## Verification Checklist

- [ ] `grep -rn "except Exception" core/ llm/ schemas/` returns 0 results
- [ ] `grep -rn "except:" core/ llm/ schemas/` returns 0 results (no bare excepts)
- [ ] Each narrowed except clause includes only exceptions that can actually be raised by the try block
- [ ] All necessary exception types are imported at the top of each file
- [ ] `pytest` passes — 452+ tests, 0 failures
- [ ] Error handling behavior is preserved (same log messages, same return values)
- [ ] `openai` exception types match the installed openai SDK version

---

## What NOT To Do

- **Do NOT add new try/except blocks** — only narrow existing ones.
- **Do NOT change what happens in the except body** (logging, return values, etc.) — only change what is caught.
- **Do NOT catch `BaseException`** — that's even broader than `Exception`.
- **Do NOT remove try/except blocks entirely** — the error handling is intentional, it's just too broad.
- **Do NOT add `except Exception as e: raise` fallbacks** — if an unexpected exception occurs, it should propagate naturally with its full traceback.
- **Do NOT change the openai import style** if the project uses `from openai import OpenAI` — check the existing pattern first.

---

## Rollback Plan

If tests fail after narrowing, it means an exception type was missed. The test failure will show the actual exception type that was raised but not caught. Add that type to the except clause.

Common misses:
- `AttributeError` when accessing a field that might not exist on a response object
- `IndexError` when parsing JSON arrays that might be empty
- `UnicodeDecodeError` for malformed API responses
