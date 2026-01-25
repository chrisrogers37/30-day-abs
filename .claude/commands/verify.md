---
description: "Run full verification loop: typecheck, test, lint"
---

Run the complete verification loop in order:

1. **Type Checking**
   ```sh
   mypy core/ llm/ schemas/
   ```
   - Fix any type errors before proceeding
   - Don't use `# type: ignore` without good reason

2. **Tests**
   ```sh
   pytest -v
   ```
   - All tests must pass
   - For quick verification: `pytest -m unit -v`
   - For coverage: `pytest --cov=core --cov=llm --cov=schemas`

3. **Linting**
   ```sh
   ruff check .
   ```
   - Auto-fix simple issues: `ruff check --fix .`

4. **Formatting**
   ```sh
   black --check .
   ```
   - Auto-format if needed: `black .`

Report the results of each step. If any step fails, stop and fix before continuing.
