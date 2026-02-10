# Development Guide - 30 Day A/Bs

Welcome to the 30 Day A/Bs development guide. This document provides comprehensive guidance for developers contributing to the project.

## Table of Contents

1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Setup & Installation](#setup--installation)
4. [Development Workflow](#development-workflow)
5. [Code Standards](#code-standards)
6. [Module Documentation](#module-documentation)
7. [Git Workflow](#git-workflow)
8. [Release Process](#release-process)

---

## Project Overview

### Mission

30 Day A/Bs is an A/B test simulator that generates realistic business scenarios for experimentation and walks through design calculations and result interpretation in a quiz format.

### Key Features

- AI-generated realistic business scenarios using LLMs
- Deterministic mathematical engine for statistical calculations
- Interactive Streamlit web application
- Comprehensive statistical analysis and validation
- Educational quiz format with automated scoring
- Data export and analysis templates

### Technology Stack

- **Language**: Python 3.11+
- **Framework**: Streamlit (UI)
- **LLM Integration**: OpenAI GPT-4
- **Data Validation**: Pydantic
- **Statistical Computing**: NumPy, SciPy
- **Testing**: Pytest
- **Deployment**: Streamlit Cloud

---

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   LLM Layer     │    │   Core Engine   │    │   UI Layer      │
│                 │    │                 │    │                 │
│ • Scenario Gen  │───▶│ • Math Engine   │◀───│ • Streamlit     │
│ • JSON Parsing  │    │ • Simulation    │    │ • Data Viz      │
│ • Guardrails    │    │ • Analysis      │    │ • User Interface│
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Schemas       │    │   Validation    │    │   Scoring       │
│                 │    │                 │    │                 │
│ • DTOs          │    │ • Answer Check  │    │ • Grading       │
│ • Validation    │    │ • Feedback      │    │ • Answer Keys   │
│ • Serialization │    │ • Tolerances    │    │ • Quiz Results  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Module Organization

#### Core Module (`core/`)
Pure mathematical functions with no external dependencies:
- **Purpose**: Deterministic statistical calculations
- **Key Principle**: No HTTP, no LLM calls, no global state
- **Focus**: Sample size, power analysis, simulation, validation

#### LLM Module (`llm/`)
LLM integration and scenario generation:
- **Purpose**: Generate realistic business scenarios
- **Key Components**: Client, generator, parser, guardrails
- **Integration**: OpenAI API with retry logic and validation

#### Schemas Module (`schemas/`)
Pydantic-based data transfer objects:
- **Purpose**: API boundaries and validation
- **Key Components**: DTOs for scenarios, design, simulation, analysis
- **Benefits**: Type safety, validation, serialization

#### UI Module (`ui/`)
Streamlit web application:
- **Purpose**: Interactive user interface
- **Key Components**: Quiz flow, data visualization, feedback
- **State Management**: Streamlit session state

### Data Flow

```
User Request → LLM Generation → Schema Validation → Core Calculation → UI Display
                     ↓                    ↓                 ↓              ↓
              JSON Parsing         DTO Validation    Math Engine    Streamlit
              Guardrails           Type Safety       Simulation     Visualization
              Error Handling       Field Validation  Analysis       User Feedback
```

---

## Setup & Installation

### Prerequisites

- **Python**: 3.11 or higher
- **Git**: For version control
- **OpenAI API Key**: For LLM integration (development)

### Initial Setup

```bash
# Clone the repository
git clone https://github.com/chrisrogers37/30-day-abs.git
cd 30-day-abs

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install production dependencies
pip install -r requirements.txt

# Install development dependencies (testing, linting, etc.)
pip install -r requirements-dev.txt

# Create .env file
cp .env.example .env
# Edit .env and add your OpenAI API key
```

### Environment Variables

Create a `.env` file in the project root:

```bash
# OpenAI Configuration
OPENAI_API_KEY=your-openai-api-key-here

# LLM Configuration
LLM_PROVIDER=openai  # openai, mock
LLM_MODEL=gpt-4
LLM_MAX_RETRIES=3
LLM_TIMEOUT=30

# Application Configuration
ENVIRONMENT=development  # development, production, test
DEBUG=true
```

### Verify Installation

```bash
# Run basic tests
python tests/test_basic.py

# Run Streamlit app tests
python tests/test_streamlit_app.py

# Start the application
streamlit run ui/streamlit_app.py
```

---

## Development Workflow

### Branch Strategy

We use a simplified branching strategy based off `main`:

- **`main`**: Production-ready code (primary branch)
- **`feature/*`**: New features (branch from main)
- **`bugfix/*`**: Bug fixes
- **`hotfix/*`**: Production hotfixes

> **Note:** There is no `develop` branch. All feature branches are created from and merged back into `main`.

### Creating a New Feature

```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# Make changes and commit
git add .
git commit -m "Add feature: description"

# Push to remote
git push -u origin feature/your-feature-name

# Create Pull Request on GitHub
```

### Development Cycle

1. **Plan**: Review issue or feature requirements
2. **Branch**: Create feature branch from `main`
3. **Code**: Implement feature following code standards
4. **Test**: Write and run tests (aim for 80%+ coverage)
5. **Document**: Update documentation and CHANGELOG
6. **Review**: Create PR and request code review
7. **Merge**: Merge to `main` after approval

### Local Development Commands

```bash
# Run the application
streamlit run ui/streamlit_app.py

# Run tests
pytest                          # All tests
pytest -m unit                  # Unit tests only
pytest tests/core/              # Specific module
pytest --cov=core               # With coverage

# Code formatting
black .                         # Format all files
black core/ llm/ schemas/       # Format specific modules
ruff check .                    # Lint code
ruff check --fix .              # Auto-fix issues

# Type checking
mypy core/                      # Type check core module
mypy llm/ schemas/              # Type check multiple modules

# Pre-commit checks (recommended)
black . && ruff check --fix . && pytest -m unit
```

---

## Code Standards

### Python Style Guide

We follow [PEP 8](https://peps.python.org/pep-0008/) with some modifications:

- **Line Length**: 100 characters (Black default)
- **Indentation**: 4 spaces
- **Quotes**: Double quotes for strings
- **Imports**: Organized alphabetically, grouped by type

### Code Formatting

Use [Black](https://black.readthedocs.io/) for automatic formatting:

```bash
# Format all Python files
black .

# Format specific directory
black core/

# Check without modifying
black --check .
```

### Linting

Use [Ruff](https://docs.astral.sh/ruff/) for fast linting:

```bash
# Lint all files
ruff check .

# Auto-fix issues
ruff check --fix .

# Check specific rules
ruff check --select E,F .
```

### Type Hints

Use type hints for all function signatures:

```python
from typing import Optional, List, Tuple
from core.types import DesignParams, SampleSize


def compute_sample_size(
    params: DesignParams,
    custom_effect_size: Optional[float] = None
) -> SampleSize:
    """
    Compute required sample size for AB test.
    
    Args:
        params: Design parameters for the test
        custom_effect_size: Override effect size calculation
    
    Returns:
        Sample size calculation results
    
    Raises:
        ValueError: If parameters are invalid
    """
    # Implementation
    pass
```

### Docstrings

Use Google-style docstrings:

```python
def analyze_results(
    sim_result: SimResult,
    alpha: float = 0.05,
    test_type: str = "two_proportion_z"
) -> AnalysisResult:
    """
    Perform statistical analysis on AB test results.
    
    This function runs the specified statistical test and calculates
    p-value, confidence intervals, and effect size.
    
    Args:
        sim_result: Simulation results with conversion data
        alpha: Significance level (default: 0.05)
        test_type: Type of statistical test to perform
            Options: "two_proportion_z", "chi_square", "fisher_exact"
    
    Returns:
        AnalysisResult containing statistical test results
    
    Raises:
        ValueError: If test_type is not supported
        
    Example:
        >>> from core.simulate import simulate_trial
        >>> from core.analyze import analyze_results
        >>> 
        >>> sim_result = simulate_trial(params, seed=42)
        >>> analysis = analyze_results(sim_result, alpha=0.05)
        >>> print(f"P-value: {analysis.p_value:.4f}")
    
    Note:
        Uses two-tailed test for p-value calculation.
        Confidence intervals are calculated using normal approximation.
    """
    # Implementation
    pass
```

### Naming Conventions

- **Variables**: `snake_case`
- **Functions**: `snake_case`
- **Classes**: `PascalCase`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`
- **DTOs**: `PascalCaseDTO`

Examples:

```python
# Good
baseline_conversion_rate = 0.05
MAX_RETRIES = 3

class DesignParams:
    pass

def compute_sample_size():
    pass

def _calculate_z_score():  # Private function
    pass

# Bad
BaselineConversionRate = 0.05  # Should be snake_case
max_retries = 3  # Should be UPPER_SNAKE_CASE
class design_params:  # Should be PascalCase
    pass
```

### Code Organization

#### Import Order

```python
# Standard library imports
import os
import sys
from typing import Optional, List

# Third-party imports
import numpy as np
import pandas as pd
from pydantic import BaseModel

# Local application imports
from core.types import DesignParams, SampleSize
from core.design import compute_sample_size
```

#### Function Organization

```python
# Public API functions at top
def public_function():
    """Public function used by other modules."""
    pass

# Private helper functions below
def _private_helper():
    """Private helper function."""
    pass

# Constants at module level
DEFAULT_ALPHA = 0.05
DEFAULT_POWER = 0.80
```

---

## Module Documentation

### Core Module

**Location**: `core/`
**Documentation**: `core/README.md`

Key modules:
- `design.py`: Sample size calculations
- `simulate.py`: Data simulation
- `analyze.py`: Statistical analysis
- `validation.py`: Answer validation
- `scoring.py`: Quiz scoring
- `types.py`: Domain types
- `utils.py`: Utility functions
- `rng.py`: Random number generation

### LLM Module

**Location**: `llm/`
**Documentation**: `llm/README.md`

Key modules:
- `client.py`: LLM client with retry logic
- `generator.py`: Scenario generation orchestration
- `parser.py`: JSON parsing and validation
- `guardrails.py`: Parameter validation
- `integration.py`: End-to-end pipeline

### Schemas Module

**Location**: `schemas/`
**Documentation**: `schemas/README.md`

Key modules:
- `shared.py`: Common types and enums
- `scenario.py`: Scenario DTOs
- `design.py`: Design parameter DTOs
- `simulate.py`: Simulation DTOs
- `analyze.py`: Analysis DTOs
- `evaluation.py`: Evaluation DTOs

### UI Module

**Location**: `ui/`
**Documentation**: `ui/README.md`

Main file:
- `streamlit_app.py`: Streamlit web application

---

## Git Workflow

### Commit Message Format

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types**:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Formatting changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples**:

```bash
# Feature commit
git commit -m "feat(core): add MDE calculation function"

# Bug fix commit
git commit -m "fix(llm): handle JSON parsing errors gracefully"

# Documentation commit
git commit -m "docs(readme): update installation instructions"

# Test commit
git commit -m "test(core): add unit tests for sample size calculation"
```

### Pull Request Process

1. **Create Branch**: Create feature branch from `main`
2. **Make Changes**: Implement feature with tests
3. **Update Documentation**: Update relevant docs and CHANGELOG
4. **Run Tests**: Ensure all tests pass locally
5. **Push Branch**: Push to remote repository
6. **Create PR**: Create pull request on GitHub
7. **Code Review**: Address review comments
8. **Merge**: Merge after approval

### Pull Request Template

```markdown
## Description
Brief description of changes

## Type of Change
- [ ] Bug fix
- [ ] New feature
- [ ] Breaking change
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] All tests passing locally
- [ ] Coverage maintained/improved

## Checklist
- [ ] Code follows style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] CHANGELOG updated
- [ ] No breaking changes (or documented)

## Related Issues
Closes #123
```

---

## Release Process

### Version Numbering

We follow [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

Examples:
- `1.0.0` → `2.0.0`: Breaking change
- `1.0.0` → `1.1.0`: New feature
- `1.0.0` → `1.0.1`: Bug fix

### Release Checklist

1. **Update Version**: Update version in relevant files
2. **Update CHANGELOG**: Document all changes
3. **Run Tests**: Ensure all tests pass
4. **Create Release Branch**: `git checkout -b release/1.2.0` (from `main`)
5. **Final Testing**: Run full test suite
6. **Merge to Main**: Merge release branch to `main`
7. **Tag Release**: Create Git tag `git tag v1.2.0`
8. **Deploy**: Deploy to Streamlit Cloud
9. **Announce**: Update README and announce release

### CHANGELOG Format

Follow [Keep a Changelog](https://keepachangelog.com/):

```markdown
## [1.2.0] - 2025-01-21

### Added
- New feature X
- New feature Y

### Changed
- Modified behavior of Z

### Fixed
- Bug fix for issue #123

### Deprecated
- Feature X is deprecated

### Removed
- Removed deprecated feature Y

### Security
- Security fix for vulnerability Z
```

---

## Best Practices

### Design Principles

1. **Separation of Concerns**: Each module has a single responsibility
2. **Pure Functions**: Core module functions are deterministic
3. **Immutability**: Use frozen dataclasses for data integrity
4. **Type Safety**: Use type hints and Pydantic validation
5. **Testability**: Write testable code with dependency injection

### Performance Considerations

1. **Avoid Premature Optimization**: Profile before optimizing
2. **Use NumPy**: Vectorized operations for numerical calculations
3. **Cache When Appropriate**: Cache expensive calculations
4. **Async Operations**: Use async/await for I/O operations
5. **Lazy Loading**: Load resources only when needed

### Security Best Practices

1. **Environment Variables**: Never commit API keys or secrets
2. **Input Validation**: Validate all user inputs
3. **Error Messages**: Don't expose sensitive information in errors
4. **Dependencies**: Keep dependencies updated
5. **Code Review**: Require review for all changes

### Documentation Standards

1. **Code Comments**: Explain why, not what
2. **Docstrings**: Document all public functions
3. **README Files**: Each module should have a README
4. **Examples**: Provide usage examples
5. **Keep Updated**: Update docs with code changes

---

## Troubleshooting

### Common Issues

**Issue**: Import errors when running tests
**Solution**: Ensure PYTHONPATH includes project root
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Issue**: Streamlit app won't start
**Solution**: Check virtual environment and dependencies
```bash
source venv/bin/activate
pip install -r requirements.txt
```

**Issue**: Tests fail with API errors
**Solution**: Use mock provider for development
```python
client = create_llm_client(provider="mock")
```

**Issue**: Type checking errors with mypy
**Solution**: Add type: ignore for third-party libraries
```python
import third_party_library  # type: ignore
```

### Getting Help

1. Check existing documentation
2. Search closed issues on GitHub
3. Ask in team discussions
4. Create a new issue with detailed information

---

## Resources

### Internal Documentation
- [Testing Guide](./TESTING_GUIDE.md)
- [Core Module README](../core/README.md)
- [LLM Module README](../llm/README.md)
- [Schemas Module README](../schemas/README.md)
- [CHANGELOG](../CHANGELOG.md)

### External Resources
- [Python Official Docs](https://docs.python.org/3/)
- [Streamlit Documentation](https://docs.streamlit.io/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [Pytest Documentation](https://docs.pytest.org/)
- [NumPy Documentation](https://numpy.org/doc/)

### Learning Resources
- [A/B Testing Theory](https://www.evanmiller.org/ab-testing/)
- [Statistical Power Analysis](https://statpower.net/)
- [Python Type Hints](https://realpython.com/python-type-checking/)
- [Clean Code Principles](https://www.oreilly.com/library/view/clean-code-a/9780136083238/)

---

**Version**: 1.1
**Last Updated**: 2026-02-10
**Maintained By**: Development Team

