---
description: "Run tests and fix any failures"
---

1. Run the test suite: `pytest -v`
2. If all tests pass, report success
3. If tests fail:
   - Analyze each failure carefully
   - Identify the root cause (is it the test or the implementation?)
   - Fix the issue
   - Re-run tests to verify the fix
   - Repeat until all tests pass

For faster iteration on specific modules:
- `pytest tests/core/ -v` - Core logic tests
- `pytest tests/llm/ -v` - LLM integration tests
- `pytest tests/schemas/ -v` - Schema validation tests
- `pytest -m unit -v` - All unit tests only
- `pytest -k "test_name"` - Run specific test by name

Be methodical: fix one test at a time and verify before moving to the next.
