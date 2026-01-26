# CLAUDE.md - Project Instructions for Claude

This file provides project-specific guidance for Claude (Code CLI, web app, or phone app). Update this file whenever Claude does something incorrectly so it learns not to repeat mistakes.

## Quick Context (Paste into Claude Web/Phone)

**30 Day A/Bs** is an A/B testing interview practice simulator. Users get AI-generated business scenarios and practice experimental design + statistical analysis in a quiz format.

**Tech Stack**: Python 3.11+, Streamlit (UI), OpenAI GPT-4 (scenarios), Pydantic (schemas), pytest (testing)

**Architecture**: `LLM Layer → Core Engine (pure math) → UI Layer`

---

## Current State

**Version**: 1.5.1 (see CHANGELOG.md for details)

**Recent Changes**:
- Fixed simulation performance (27s → 0.01s by using calculated sample size)
- Added comprehensive test suites (89% core coverage, 283 tests)
- Fixed AttributeError in logging when simulation fails

**Known Issues**:
- Streamlit Cloud deployment badge links to placeholder
- Some E2E tests require OpenAI API key

**In Progress / TODO**:
- [ ] Streamlit Cloud deployment
- [ ] Additional question types and difficulty levels
- [ ] More statistical test options (chi-square, Fisher's exact)
- [ ] Export functionality for results and reports

---

## File Map

```
30-day-abs/
├── CLAUDE.md              # THIS FILE - AI assistant guide
├── README.md              # Project overview, quick start
├── CHANGELOG.md           # Version history (Keep a Changelog format)
├── requirements.txt       # Production dependencies
├── requirements-dev.txt   # Dev dependencies (pytest, black, ruff, mypy)
├── pytest.ini             # Test configuration and markers
│
├── core/                  # PURE MATH - No I/O, no side effects
│   ├── types.py           # Domain types: Allocation, DesignParams, SampleSize, SimResult, AnalysisResult
│   ├── design.py          # Sample size calculations (two-proportion z-test)
│   ├── simulate.py        # Data simulation with treatment effect variation
│   ├── analyze.py         # Statistical analysis: z-test, CI, p-value, business impact
│   ├── validation.py      # Answer validation for quiz questions
│   ├── scoring.py         # Answer key generation and quiz results
│   ├── rng.py             # Reproducible random number generation
│   ├── utils.py           # Helpers: lift conversion, formatting
│   ├── logging.py         # Centralized logging system
│   └── question_bank.py   # Quiz question definitions
│
├── llm/                   # LLM integration (OpenAI)
│   ├── client.py          # OpenAI API client with rate limiting
│   ├── generator.py       # Scenario generation prompts
│   ├── parser.py          # JSON response parsing
│   ├── guardrails.py      # Response validation
│   └── integration.py     # Orchestration layer
│
├── schemas/               # Pydantic DTOs for type safety
│   ├── scenario.py        # ScenarioDTO, CompanyType, UserSegment
│   ├── design.py          # DesignParamsDTO, AllocationDTO
│   ├── analyze.py         # AnalysisResultDTO
│   └── ...                # Other schema files
│
├── ui/
│   └── streamlit_app.py   # Main Streamlit web application
│
├── tests/                 # 283 tests, 89% core coverage
│   ├── conftest.py        # 20+ shared fixtures
│   ├── core/              # Core module tests (18 files)
│   ├── llm/               # LLM module tests (5 files)
│   └── ui/                # UI tests
│
├── development_docs/      # Comprehensive dev documentation
│   ├── DEVELOPMENT_GUIDE.md
│   ├── TESTING_GUIDE.md
│   └── ...
│
├── .claude/               # Claude Code configuration
│   ├── settings.json      # Permissions
│   └── commands/          # Slash commands (/verify, /quick-commit, etc.)
│
└── logs/                  # Application and quiz session logs
```

---

## Key Code Patterns

### 1. Core Types (Immutable Dataclasses)

```python
# core/types.py - All types are frozen for data integrity
@dataclass(frozen=True)
class DesignParams:
    baseline_conversion_rate: float  # e.g., 0.05 for 5%
    target_lift_pct: float           # e.g., 0.20 for 20% lift
    alpha: float                     # e.g., 0.05
    power: float                     # e.g., 0.80
    allocation: Allocation           # e.g., Allocation(0.5, 0.5)
    expected_daily_traffic: int      # e.g., 10000
```

### 2. Sample Size Calculation

```python
from core.design import compute_sample_size
from core.types import DesignParams, Allocation

params = DesignParams(
    baseline_conversion_rate=0.05,
    target_lift_pct=0.20,
    alpha=0.05,
    power=0.80,
    allocation=Allocation(0.5, 0.5),
    expected_daily_traffic=10000
)
result = compute_sample_size(params)  # Returns SampleSize
print(f"Need {result.per_arm} users per arm, {result.days_required} days")
```

### 3. Simulation

```python
from core.simulate import simulate_trial

# Fast mode (recommended) - uses calculated sample size
sim_result = simulate_trial(
    params,
    seed=42,
    sample_size_per_arm=result.per_arm,
    generate_user_data=False  # Fast: only aggregate counts
)

# Slow mode - generates full user-level data
sim_result = simulate_trial(params, seed=42, generate_user_data=True)
```

### 4. Statistical Analysis

```python
from core.analyze import analyze_results

analysis = analyze_results(sim_result, alpha=0.05)
print(f"P-value: {analysis.p_value}")
print(f"Significant: {analysis.significant}")
print(f"CI: {analysis.confidence_interval}")
```

### 5. Schema Validation (Pydantic)

```python
from schemas.design import DesignParamsDTO

# All data between layers MUST use Pydantic schemas
dto = DesignParamsDTO(
    baseline_conversion_rate=0.05,
    target_lift_pct=0.20,
    alpha=0.05,
    power=0.80,
    allocation=AllocationDTO(control=0.5, treatment=0.5),
    expected_daily_traffic=10000
)
```

### 6. Logging

```python
from core.logging import get_logger

logger = get_logger(__name__)
logger.info("Starting simulation...")
logger.error("Error occurred", exc_info=True)
```

---

## Development Workflow

### Verification Loop (Run Before Every Commit)

```bash
mypy core/ llm/ schemas/      # Type checking
pytest                        # Run all tests
ruff check .                  # Lint
black .                       # Format
```

### Common Commands

```bash
# Run the app
streamlit run ui/streamlit_app.py

# Testing
pytest                              # All tests
pytest -m unit                      # Unit tests only
pytest -m "not requires_api"        # Skip API tests
pytest --cov=core --cov-report=html # With coverage

# Code quality
mypy core/ llm/ schemas/
ruff check --fix .
black .
```

### Test Markers

```python
@pytest.mark.unit         # Fast unit tests
@pytest.mark.integration  # Integration tests
@pytest.mark.e2e          # End-to-end tests
@pytest.mark.slow         # Slow tests
@pytest.mark.requires_api # Needs OpenAI API key
```

---

## Things Claude Should NOT Do

- Don't modify `.env` files with API keys
- Don't skip writing tests for new functionality
- Don't add new dependencies without explicit approval
- Don't change core statistical functions without verifying mathematical correctness
- Don't use `any` or ignore type errors - fix them properly
- Don't break the pure mathematical core by adding I/O or side effects
- Don't skip the verification loop (typecheck → test → lint)
- Don't commit secrets or API keys
- Don't create new files unless absolutely necessary - prefer editing existing files

---

## Troubleshooting

### "ModuleNotFoundError: No module named 'streamlit'"
```bash
pip install -r requirements.txt
```

### "OPENAI_API_KEY not set"
```bash
echo "OPENAI_API_KEY=your_key_here" > .env
```

### Tests taking too long (30+ minutes)
The simulation tests were optimized. If slow, check that `simulate_trial()` is using `sample_size_per_arm` parameter instead of generating 30 days of traffic.

### AttributeError accessing simulation results
Always check for None before accessing attributes:
```python
if sim_result is not None:
    print(sim_result.control_n)
```

### Coverage report not generating
```bash
pytest --cov=core --cov=llm --cov=schemas --cov-report=html
open htmlcov/index.html
```

---

## Session Handoff (For Claude Web/Phone)

When starting a new Claude session on this project:

1. **Share this file** - Copy/paste CLAUDE.md or upload it
2. **Share the specific file** - Upload the file you want to work on
3. **Describe the task** - What you want to accomplish
4. **Share error messages** - Full tracebacks if debugging

Example prompt:
```
I'm working on the 30-day-abs project (A/B testing interview practice app).
Here's the CLAUDE.md context: [paste]
Here's the file I'm working on: [paste/upload]
I want to [describe task].
```

---

## Changelog Maintenance (CRITICAL)

**ALWAYS update CHANGELOG.md when creating PRs.**

**Format**: [Keep a Changelog](https://keepachangelog.com/) with [Semantic Versioning](https://semver.org/)

**Version bump rules**:
- **MAJOR** (X.0.0): Breaking changes
- **MINOR** (x.Y.0): New features
- **PATCH** (x.y.Z): Bug fixes

**Entry categories**: Added, Changed, Fixed, Improved, Technical Improvements

```markdown
## [Unreleased]

### Added
- **Feature Name** - Brief description
  - Implementation detail if needed

### Fixed
- **Bug Name** - What was broken and how it was fixed
```

---

## Test Template

```python
import pytest
from unittest.mock import Mock, patch

class TestFeatureName:
    """Test suite for FeatureName."""

    @pytest.mark.unit
    def test_success_case(self):
        """Test description."""
        # Arrange
        input_data = create_test_data()

        # Act
        result = function_under_test(input_data)

        # Assert
        assert result == expected_value

    @pytest.mark.unit
    def test_error_case(self):
        """Test error handling."""
        with pytest.raises(ValueError, match="expected error"):
            function_under_test(invalid_input)
```

---

## A/B Testing Domain Quick Reference

- **Alpha (α)**: Significance level, typically 0.05 (5% false positive rate)
- **Power (1-β)**: Typically 0.80 (80% chance of detecting true effect)
- **MDE**: Minimum Detectable Effect (smallest lift worth detecting)
- **Relative Lift**: `(treatment_rate - control_rate) / control_rate`
- **Absolute Lift**: `treatment_rate - control_rate`
- **Sample Size Formula**: Two-proportion z-test (see `core/design.py`)

---

_Update this file continuously. Every mistake Claude makes is a learning opportunity._
