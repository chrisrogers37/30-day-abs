# CLAUDE.md - Project Instructions for Claude Code

This file provides project-specific guidance for Claude Code. Update this file whenever Claude does something incorrectly so it learns not to repeat mistakes.

## Project Overview

**30 Day A/Bs** is an A/B testing interview practice simulator built with AI-generated scenarios. It helps users practice experimental design, statistical analysis, and result interpretation through realistic business scenarios in a quiz format.

### Architecture

```
LLM Layer (GPT-4) → Core Engine (Pure Math) → UI Layer (Streamlit)
```

- **`core/`** - Pure mathematical functions, deterministic, no external dependencies
- **`llm/`** - LLM integration for scenario generation
- **`schemas/`** - Pydantic DTOs for type safety and validation
- **`ui/`** - Streamlit web application
- **`tests/`** - Comprehensive test suite (89% core coverage)

## Development Workflow

Give Claude verification loops for 2-3x quality improvement:

1. Make changes
2. Run type checking: `mypy core/ llm/ schemas/`
3. Run tests: `pytest`
4. Run linting: `ruff check .`
5. Format code: `black .`
6. Before creating PR: run full test suite with coverage

## Code Style & Conventions

### Python Style
- Use type hints for all function signatures
- Use Pydantic models for data validation (see `schemas/`)
- Prefer immutable data structures (frozen dataclasses, Pydantic models)
- Use `from __future__ import annotations` for forward references
- Follow PEP 8, enforced by Black and Ruff

### Testing Style
- Use pytest fixtures from `tests/conftest.py`
- Use `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.e2e` markers
- Use `@pytest.mark.requires_api` for tests that need OpenAI
- Mock LLM calls in unit tests, use real API only in E2E tests

### A/B Testing Domain
- Alpha (α) = significance level, typically 0.05
- Power = 1 - β, typically 0.80
- Effect size = minimum detectable effect (MDE)
- Always validate statistical assumptions before recommending tests

## Commands Reference

```sh
# Development
streamlit run ui/streamlit_app.py    # Run the app

# Verification loop
mypy core/ llm/ schemas/             # Type checking
pytest                                # Run all tests
pytest -m unit                        # Unit tests only
pytest -m integration                 # Integration tests only
pytest -m "not requires_api"          # Skip API-dependent tests
ruff check .                          # Lint
ruff check --fix .                    # Auto-fix lint issues
black .                               # Format code

# Coverage
pytest --cov=core --cov=llm --cov=schemas --cov-report=html

# Git workflow
git status                            # Check current state
git diff                              # Review changes before commit
```

## Things Claude Should NOT Do

- Don't modify `.env` files with API keys
- Don't skip writing tests for new functionality
- Don't add new dependencies without explicit approval
- Don't change core statistical functions without verifying mathematical correctness
- Don't use `any` or ignore type errors - fix them properly
- Don't break the pure mathematical core by adding I/O or side effects
- Don't skip the verification loop (typecheck → test → lint)
- Don't commit secrets or API keys

## Project-Specific Patterns

### Schema Validation
All data flowing between layers must use Pydantic schemas from `schemas/`. Never pass raw dicts.

### Deterministic Simulation
The `core/simulate.py` module uses seeded RNG for reproducibility. Always pass `random_seed` for deterministic tests.

### Statistical Test Selection
When analyzing A/B tests, use `core/analyze.py` which automatically selects appropriate statistical tests based on:
- Metric type (conversion rate vs continuous)
- Sample size
- Distribution characteristics

### Logging
Use the centralized logging from `core/logging.py`. Don't use print statements or create new loggers.

## Workflow Tips

Based on Boris Cherny's recommendations:

1. **Start in Plan Mode** (Shift+Tab twice) - Iterate on the plan before writing code
2. **Verification is key** - Always give Claude a way to verify its work (tests, type checks)
3. **Update this file** - When Claude makes a mistake, add it to "Things Claude Should NOT Do"
4. **Use slash commands** - `/verify`, `/test-and-fix`, `/quick-commit` for common workflows

### GitHub Integration

Consider installing the Claude GitHub action for automated PR reviews:
```sh
claude /install-github-action
```

This enables tagging @claude in PR reviews to suggest CLAUDE.md updates.

---

_Update this file continuously. Every mistake Claude makes is a learning opportunity._
