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

## Changelog Maintenance (CRITICAL)

**ALWAYS update CHANGELOG.md when creating PRs.** The changelog is the user-facing record of all changes.

**Format**: This project uses [Keep a Changelog](https://keepachangelog.com/) with [Semantic Versioning](https://semver.org/).

**When to update**:
- **Every PR** must include a CHANGELOG.md entry
- Add entries under `## [Unreleased]` section
- Move entries to a versioned section when releasing

**Version bump rules** (Semantic Versioning):
- **MAJOR** (X.0.0): Breaking changes, incompatible API changes
- **MINOR** (x.Y.0): New features, backward-compatible additions
- **PATCH** (x.y.Z): Bug fixes, performance improvements

**Entry categories** (use as applicable):
- `### Added` - New features or capabilities
- `### Changed` - Changes to existing functionality
- `### Fixed` - Bug fixes
- `### Improved` - Performance or UX improvements
- `### Technical Improvements` - Internal changes

**Entry format**:
```markdown
## [Unreleased]

### Added
- **Feature Name** - Brief description of what was added
  - Sub-bullet with implementation detail if needed

### Fixed
- **Bug Name** - What was broken and how it was fixed
```

**Best practices**:
- Write entries from the user's perspective (what changed for them)
- Include enough detail to understand the change without reading code
- Group related changes under descriptive subheadings
- Include Technical Improvements section for significant internal changes

## Test Template

When adding new tests, follow this structure:

```python
# tests/module/test_feature.py
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def my_fixture():
    """Fixture description."""
    return SomeClass()

class TestFeatureName:
    """Test suite for FeatureName."""

    @pytest.mark.unit
    def test_method_success_case(self, my_fixture):
        """Test description of what this validates."""
        # Arrange
        my_fixture.dependency = Mock(return_value="expected")

        # Act
        result = my_fixture.method_under_test()

        # Assert
        assert result == "expected"

    @pytest.mark.unit
    def test_method_error_case(self, my_fixture):
        """Test error handling."""
        # Arrange
        my_fixture.dependency = Mock(side_effect=ValueError("error"))

        # Act & Assert
        with pytest.raises(ValueError, match="error"):
            my_fixture.method_under_test()
```

## Documentation Organization

**Important**: All helpful markdown documentation should be placed in `development_docs/`.

```
development_docs/
├── README.md           # Index of all documentation
├── development.md      # Development setup and workflow
├── testing.md          # How to run and write tests
└── architecture.md     # Design decisions and patterns
```

**Root-level documentation exceptions** (only these in project root):
- `README.md` - Project overview and quick start
- `CHANGELOG.md` - Version history
- `CLAUDE.md` - This file (AI assistant guide)
- `LICENSE` - Project license

## Logging Standards

Use the centralized logging from `core/logging.py`:

```python
from core.logging import get_logger

logger = get_logger(__name__)

# Use appropriate levels
logger.debug("Detailed diagnostic info")      # DEBUG: Development debugging
logger.info("General informational messages") # INFO: Normal operations
logger.warning("Something unexpected")        # WARNING: Handled issues
logger.error("Error occurred", exc_info=True) # ERROR: Failures with traceback
```

---

_Update this file continuously. Every mistake Claude makes is a learning opportunity._
