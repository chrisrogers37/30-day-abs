---
description: "Review uncommitted changes and suggest improvements"
---

Here is the current git status:
```
${{ git status --short }}
```

Here are the changes:
```
${{ git diff }}
```

For each modified file, analyze:
   - Is the change correct and complete?
   - Are there any potential bugs?
   - Does it follow project conventions (type hints, Pydantic schemas)?
   - Are there any security concerns?
   - Is error handling adequate?
   - For statistical code: is the math correct?
4. Run the verification loop:
   - `mypy core/ llm/ schemas/` for type checking
   - `pytest -m unit` for quick test validation
   - `ruff check .` for linting
5. Provide a summary with:
   - What looks good
   - Any concerns or suggestions
   - Recommended next steps (test more, commit, or make changes)
