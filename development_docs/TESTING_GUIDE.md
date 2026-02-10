# Testing Guide - 30 Day A/Bs

This document provides comprehensive guidance for testing the 30 Day A/Bs project. It covers testing philosophy, structure, conventions, and best practices.

## Table of Contents

1. [Testing Philosophy](#testing-philosophy)
2. [Testing Structure](#testing-structure)
3. [Setup & Installation](#setup--installation)
4. [Running Tests](#running-tests)
5. [Writing Tests](#writing-tests)
6. [Test Coverage](#test-coverage)
7. [Mock Strategy](#mock-strategy)
8. [CI/CD Integration](#cicd-integration)
9. [Contributing Guidelines](#contributing-guidelines)

---

## Testing Philosophy

### Core Principles

**Comprehensive Coverage**: Aim for 90%+ coverage on core mathematical functions, 80%+ on integration modules.

**Test Pyramid**: Follow the testing pyramid approach:
- **70% Unit Tests**: Fast, isolated tests for individual functions
- **20% Integration Tests**: Tests for module interactions
- **10% E2E Tests**: Complete workflow tests

**Deterministic Testing**: All tests should be reproducible with fixed random seeds.

**Mock by Default**: Use mock LLM clients for all tests except explicitly marked real API tests.

**Fast Feedback**: Unit tests should complete in seconds, full suite in minutes.

### Testing Types

1. **Unit Tests**: Test individual functions in isolation
2. **Integration Tests**: Test module interactions and pipelines
3. **Schema Tests**: Test Pydantic validation and serialization
4. **E2E Tests**: Test complete user workflows
5. **Performance Tests**: Benchmark critical operations (optional)

---

## Testing Structure

```
tests/
├── __init__.py
├── conftest.py                      # Pytest configuration & shared fixtures
│
├── core/                            # Unit tests for core/ (27 test files)
│   ├── __init__.py
│   ├── test_analyze.py              # Tests for core.analyze
│   ├── test_analyze_business.py     # Business impact analysis tests
│   ├── test_analyze_extended.py     # Extended analysis edge cases
│   ├── test_analyze_statistical_tests.py  # Chi-square, Fisher's exact tests
│   ├── test_design.py               # Sample size calculation tests
│   ├── test_design_extended.py      # Extended design edge cases
│   ├── test_design_helpers.py       # Design helper function tests
│   ├── test_logging.py              # Centralized logging tests
│   ├── test_logging_quiz.py         # Quiz session logging tests
│   ├── test_question_bank.py        # Question bank tests (50+ questions)
│   ├── test_rng.py                  # RNG determinism tests
│   ├── test_rng_advanced.py         # Advanced RNG distribution tests
│   ├── test_rng_extended.py         # Extended RNG edge cases
│   ├── test_scoring.py              # Answer key & scoring tests
│   ├── test_scoring_variable.py     # Variable scoring tests
│   ├── test_simulate.py             # Data simulation tests
│   ├── test_simulate_extended.py    # Extended simulation tests
│   ├── test_simulate_utilities.py   # Simulation utility tests
│   ├── test_types.py                # Domain type tests
│   ├── test_types_extended.py       # Extended type tests
│   ├── test_utils.py                # Utility function tests
│   ├── test_utils_extended.py       # Extended utility tests
│   ├── test_validation.py           # Answer validation tests
│   ├── test_validation_by_id.py     # Validation by question ID tests
│   └── test_validation_scoring.py   # Validation scoring integration tests
│
├── llm/                             # LLM integration tests (6 test files)
│   ├── __init__.py
│   ├── test_client.py               # LLM client tests
│   ├── test_generator.py            # Scenario generation tests
│   ├── test_guardrails.py           # Parameter validation tests
│   ├── test_integration.py          # LLM pipeline tests
│   ├── test_novelty_scoring.py      # Novelty scoring tests
│   └── test_parser.py               # JSON parsing tests
│
├── schemas/                         # Schema validation tests (6 test files)
│   ├── __init__.py
│   ├── test_analyze.py              # Analysis schema tests
│   ├── test_design.py               # Design schema tests
│   ├── test_evaluation.py           # Evaluation schema tests
│   ├── test_scenario.py             # Scenario schema tests
│   ├── test_shared.py               # Shared schema tests
│   └── test_simulate.py             # Simulation schema tests
│
├── ui/                              # UI component tests
│   ├── __init__.py
│   └── test_streamlit_app_enhanced.py  # Enhanced Streamlit tests
│
├── integration/                     # E2E integration tests
│   ├── __init__.py
│   ├── test_complete_workflow.py    # Full quiz flow
│   ├── test_data_export.py          # Data generation & export
│   ├── test_llm_pipeline.py         # LLM → Core → Analysis
│   └── test_real_api.py             # Real API tests (CI skip)
│
├── fixtures/                        # Shared test data
│   ├── __init__.py
│   ├── scenarios/                   # Sample scenario JSON files
│   │   ├── ecommerce_scenario.json
│   │   ├── saas_scenario.json
│   │   └── fintech_scenario.json
│   ├── expected_results.py          # Expected calculation results
│   ├── llm_responses.py             # Mock LLM responses
│   └── test_data.py                 # Reusable test data
│
├── helpers/                         # Test utilities
│   ├── __init__.py
│   ├── assertions.py                # Custom assertions
│   ├── factories.py                 # Object factories
│   └── mocks.py                     # Mock helpers
│
├── test_basic.py                    # Quick smoke tests
├── test_notebooks.py                # Notebook template validation
└── test_streamlit_app.py            # Basic Streamlit import/functionality tests
```

### Module-to-Test Mapping

Each source module has a corresponding test module:

| Source Module | Test Module | Focus |
|--------------|-------------|-------|
| `core/analyze.py` | `tests/core/test_analyze.py` + 3 extended files | Statistical analysis, business impact, test selection |
| `core/design.py` | `tests/core/test_design.py` + 2 extended files | Sample size calculations, helpers |
| `core/logging.py` | `tests/core/test_logging.py`, `test_logging_quiz.py` | Centralized and quiz session logging |
| `core/question_bank.py` | `tests/core/test_question_bank.py` | Question bank (50+ questions) |
| `core/rng.py` | `tests/core/test_rng.py` + 2 extended files | RNG determinism, distributions |
| `core/scoring.py` | `tests/core/test_scoring.py`, `test_scoring_variable.py` | Answer key generation, variable scoring |
| `core/simulate.py` | `tests/core/test_simulate.py` + 2 extended files | Data simulation, utilities |
| `core/types.py` | `tests/core/test_types.py`, `test_types_extended.py` | Type validation |
| `core/utils.py` | `tests/core/test_utils.py`, `test_utils_extended.py` | Utility functions |
| `core/validation.py` | `tests/core/test_validation.py` + 2 extended files | Answer validation, by-ID, scoring |
| `llm/client.py` | `tests/llm/test_client.py` | LLM client & retry logic |
| `llm/generator.py` | `tests/llm/test_generator.py` | Scenario generation |
| `llm/guardrails.py` | `tests/llm/test_guardrails.py`, `test_novelty_scoring.py` | Parameter validation, novelty scoring |
| `llm/integration.py` | `tests/llm/test_integration.py` | LLM pipeline |
| `llm/parser.py` | `tests/llm/test_parser.py` | JSON parsing |
| `schemas/*.py` | `tests/schemas/test_*.py` | Pydantic validation |
| `ui/streamlit_app.py` | `tests/ui/test_streamlit_app_enhanced.py` | Enhanced UI component tests |

---

## Setup & Installation

### Prerequisites

```bash
# Python 3.11+
python --version

# Virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Install development dependencies (includes all testing tools)
pip install -r requirements-dev.txt
```

### Environment Configuration

Create a `.env.test` file for test environment variables:

```bash
# .env.test
OPENAI_API_KEY=mock-key-for-testing
LLM_PROVIDER=mock
ENVIRONMENT=test
```

### Pytest Configuration

The `pytest.ini` file configures pytest behavior:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts =
    --verbose
    --strict-markers
    --tb=short
    --cov=core
    --cov=llm
    --cov=schemas
    --cov=ui
    --cov-report=term-missing
    --cov-report=html
    --cov-report=xml
    -ra
markers =
    unit: Unit tests (fast, isolated function tests)
    integration: Integration tests (module interaction tests)
    e2e: End-to-end tests (complete workflow tests)
    slow: Slow tests (may take several seconds or more)
    requires_api: Tests requiring real API calls (OpenAI, etc.)
    requires_env_var: Tests requiring specific environment variables
    parametrize: Parametrized tests with multiple inputs
    asyncio: Asynchronous tests requiring asyncio support
```

---

## Running Tests

### Run All Tests

```bash
# Run entire test suite
pytest

# Run with coverage report
pytest --cov=core --cov=llm --cov=schemas --cov-report=html
```

### Run Specific Test Categories

```bash
# Unit tests only (fast)
pytest -m unit

# Integration tests only
pytest -m integration

# E2E tests only
pytest -m e2e

# Skip slow tests
pytest -m "not slow"

# Skip tests requiring API
pytest -m "not requires_api"
```

### Run Specific Modules

```bash
# Test specific module
pytest tests/core/test_design.py

# Test specific class
pytest tests/core/test_design.py::TestSampleSizeCalculation

# Test specific function
pytest tests/core/test_design.py::test_compute_sample_size_basic
```

### Run with Different Output Formats

```bash
# Verbose output
pytest -v

# Quiet output
pytest -q

# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l
```

### Coverage Reports

```bash
# Generate HTML coverage report
pytest --cov=core --cov-report=html
open htmlcov/index.html

# Generate terminal coverage report
pytest --cov=core --cov-report=term-missing

# Set minimum coverage threshold
pytest --cov=core --cov-fail-under=90
```

### Performance Benchmarks

```bash
# Run benchmark tests
pytest tests/performance/ --benchmark-only

# Compare benchmark results
pytest tests/performance/ --benchmark-compare
```

---

## Writing Tests

### Unit Test Template

```python
"""
Tests for core.design module.

This module tests sample size calculation functions.
"""

import pytest
from core.design import compute_sample_size
from core.types import DesignParams, Allocation


class TestComputeSampleSize:
    """Test suite for compute_sample_size function."""
    
    @pytest.fixture
    def basic_params(self):
        """Standard design parameters for testing."""
        allocation = Allocation(control=0.5, treatment=0.5)
        return DesignParams(
            baseline_conversion_rate=0.05,
            target_lift_pct=0.15,
            alpha=0.05,
            power=0.8,
            allocation=allocation,
            expected_daily_traffic=10000
        )
    
    @pytest.mark.unit
    def test_compute_sample_size_basic(self, basic_params):
        """Test basic sample size calculation."""
        result = compute_sample_size(basic_params)
        
        assert result.per_arm > 0
        assert result.total == 2 * result.per_arm
        assert result.days_required > 0
        assert 0 <= result.power_achieved <= 1
    
    @pytest.mark.unit
    def test_compute_sample_size_deterministic(self, basic_params):
        """Test that results are deterministic."""
        result1 = compute_sample_size(basic_params)
        result2 = compute_sample_size(basic_params)
        
        assert result1.per_arm == result2.per_arm
        assert result1.total == result2.total
    
    @pytest.mark.unit
    @pytest.mark.parametrize("baseline,lift,expected_range", [
        (0.05, 0.10, (8000, 12000)),
        (0.05, 0.20, (1500, 2500)),
        (0.10, 0.15, (3000, 5000)),
    ])
    def test_compute_sample_size_ranges(self, baseline, lift, expected_range):
        """Test sample size ranges for different parameters."""
        allocation = Allocation(control=0.5, treatment=0.5)
        params = DesignParams(
            baseline_conversion_rate=baseline,
            target_lift_pct=lift,
            alpha=0.05,
            power=0.8,
            allocation=allocation,
            expected_daily_traffic=10000
        )
        
        result = compute_sample_size(params)
        min_expected, max_expected = expected_range
        assert min_expected <= result.per_arm <= max_expected
    
    @pytest.mark.unit
    def test_compute_sample_size_edge_cases(self):
        """Test edge cases for sample size calculation."""
        # Very small baseline
        allocation = Allocation(control=0.5, treatment=0.5)
        params = DesignParams(
            baseline_conversion_rate=0.001,
            target_lift_pct=0.20,
            alpha=0.05,
            power=0.8,
            allocation=allocation,
            expected_daily_traffic=10000
        )
        
        result = compute_sample_size(params)
        assert result.per_arm > 0
```

### Integration Test Template

```python
"""
Integration tests for LLM → Core → Analysis pipeline.
"""

import pytest
from llm.integration import create_llm_integration


class TestLLMPipeline:
    """Test complete LLM to analysis pipeline."""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_pipeline_success(self):
        """Test successful pipeline execution."""
        integration = create_llm_integration(provider="mock")
        
        result = await integration.run_complete_pipeline(
            max_attempts=3,
            min_quality_score=0.7
        )
        
        assert result.success
        assert result.scenario_dto is not None
        assert result.design_params is not None
        assert result.simulation_result is not None
        assert result.analysis_result is not None
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_pipeline_statistical_validity(self):
        """Test that pipeline produces statistically valid results."""
        integration = create_llm_integration(provider="mock")
        
        result = await integration.run_complete_pipeline()
        
        assert result.success
        
        # Validate design parameters
        design = result.design_params
        assert 0 < design.baseline_conversion_rate < 1
        assert 0 < design.alpha < 0.1
        assert 0.7 <= design.power <= 0.95
        
        # Validate simulation results
        sim = result.simulation_result
        assert sim.control_n > 0
        assert sim.treatment_n > 0
        assert 0 <= sim.control_conversions <= sim.control_n
        assert 0 <= sim.treatment_conversions <= sim.treatment_n
        
        # Validate analysis results
        analysis = result.analysis_result
        assert 0 <= analysis.p_value <= 1
        assert len(analysis.confidence_interval) == 2
        assert analysis.confidence_interval[0] < analysis.confidence_interval[1]
```

### Schema Test Template

```python
"""
Tests for schemas.design module.
"""

import pytest
from pydantic import ValidationError
from schemas.design import DesignParamsDTO
from schemas.shared import AllocationDTO


class TestDesignParamsDTO:
    """Test suite for DesignParamsDTO validation."""
    
    @pytest.mark.unit
    def test_valid_design_params(self):
        """Test creation of valid design parameters."""
        allocation = AllocationDTO(control=0.5, treatment=0.5)
        params = DesignParamsDTO(
            baseline_conversion_rate=0.025,
            mde_absolute=0.005,
            target_lift_pct=0.20,
            alpha=0.05,
            power=0.80,
            allocation=allocation,
            expected_daily_traffic=5000
        )
        
        assert params.baseline_conversion_rate == 0.025
        assert params.mde_absolute == 0.005
        assert params.alpha == 0.05
    
    @pytest.mark.unit
    def test_invalid_baseline_rate(self):
        """Test that invalid baseline rate raises ValidationError."""
        allocation = AllocationDTO(control=0.5, treatment=0.5)
        
        with pytest.raises(ValidationError) as exc_info:
            DesignParamsDTO(
                baseline_conversion_rate=1.5,  # Invalid: > 1.0
                mde_absolute=0.005,
                target_lift_pct=0.20,
                alpha=0.05,
                power=0.80,
                allocation=allocation,
                expected_daily_traffic=5000
            )
        
        assert "baseline_conversion_rate" in str(exc_info.value)
    
    @pytest.mark.unit
    def test_serialization_roundtrip(self):
        """Test JSON serialization and deserialization."""
        allocation = AllocationDTO(control=0.5, treatment=0.5)
        original = DesignParamsDTO(
            baseline_conversion_rate=0.025,
            mde_absolute=0.005,
            target_lift_pct=0.20,
            alpha=0.05,
            power=0.80,
            allocation=allocation,
            expected_daily_traffic=5000
        )
        
        # Serialize to JSON
        json_str = original.model_dump_json()
        
        # Deserialize from JSON
        parsed = DesignParamsDTO.model_validate_json(json_str)
        
        assert parsed.baseline_conversion_rate == original.baseline_conversion_rate
        assert parsed.mde_absolute == original.mde_absolute
```

### Test Fixtures

Use `conftest.py` for shared fixtures:

```python
"""
Shared pytest fixtures for all tests.
"""

import pytest
from core.types import Allocation, DesignParams
from schemas.shared import AllocationDTO


@pytest.fixture
def standard_allocation():
    """Standard 50/50 allocation."""
    return Allocation(control=0.5, treatment=0.5)


@pytest.fixture
def standard_design_params(standard_allocation):
    """Standard design parameters for testing."""
    return DesignParams(
        baseline_conversion_rate=0.05,
        target_lift_pct=0.15,
        alpha=0.05,
        power=0.8,
        allocation=standard_allocation,
        expected_daily_traffic=10000
    )


@pytest.fixture
def mock_llm_response():
    """Mock LLM response for testing."""
    return {
        "scenario": {
            "title": "Test Scenario",
            "company_type": "E-commerce",
            "user_segment": "all_users",
            # ... more fields
        },
        # ... more data
    }
```

### Parametrized Tests

Use `@pytest.mark.parametrize` for testing multiple cases:

```python
@pytest.mark.unit
@pytest.mark.parametrize("baseline,lift,alpha,power,expected_min,expected_max", [
    (0.05, 0.10, 0.05, 0.80, 8000, 12000),
    (0.05, 0.20, 0.05, 0.80, 1500, 2500),
    (0.10, 0.15, 0.05, 0.80, 3000, 5000),
    (0.05, 0.15, 0.01, 0.90, 5000, 8000),
])
def test_sample_size_ranges(baseline, lift, alpha, power, expected_min, expected_max):
    """Test sample size calculation ranges."""
    allocation = Allocation(control=0.5, treatment=0.5)
    params = DesignParams(
        baseline_conversion_rate=baseline,
        target_lift_pct=lift,
        alpha=alpha,
        power=power,
        allocation=allocation,
        expected_daily_traffic=10000
    )
    
    result = compute_sample_size(params)
    assert expected_min <= result.per_arm <= expected_max
```

---

## Test Coverage

### Coverage Targets

| Module | Target Coverage | Priority |
|--------|----------------|----------|
| `core/` | 90%+ | Critical |
| `llm/` | 80%+ | High |
| `schemas/` | 85%+ | High |
| `ui/` | 60%+ | Medium |

### Measuring Coverage

```bash
# Generate coverage report
pytest --cov=core --cov=llm --cov=schemas --cov-report=html

# View in browser
open htmlcov/index.html

# Check coverage threshold
pytest --cov=core --cov-fail-under=90
```

### Coverage Best Practices

1. **Test All Code Paths**: Ensure all conditional branches are tested
2. **Edge Cases**: Test boundary conditions and edge cases
3. **Error Paths**: Test error handling and exception cases
4. **Integration Points**: Test module interfaces and integration points
5. **Happy Path**: Test expected successful execution
6. **Sad Path**: Test failure scenarios and error recovery

### Excluded from Coverage

Some code can be excluded from coverage requirements:

```python
# Exclude debugging code
if __name__ == "__main__":  # pragma: no cover
    main()

# Exclude platform-specific code
if sys.platform == "win32":  # pragma: no cover
    windows_specific_function()
```

---

## Mock Strategy

### Mock LLM Client by Default

All tests should use mock LLM clients unless explicitly testing real API integration:

```python
from llm.client import create_llm_client

# Use mock provider for tests
client = create_llm_client(provider="mock")
```

### Mock Fixtures

Create reusable mock fixtures:

```python
@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing."""
    return create_llm_client(provider="mock")


@pytest.fixture
def mock_scenario_generator(mock_llm_client):
    """Mock scenario generator."""
    from llm.generator import LLMScenarioGenerator
    return LLMScenarioGenerator(mock_llm_client)
```

### Mocking External Dependencies

Use `pytest-mock` for mocking:

```python
@pytest.mark.unit
def test_with_mock(mocker):
    """Test using mocker fixture."""
    # Mock external API call
    mock_api = mocker.patch('llm.client.openai.ChatCompletion.create')
    mock_api.return_value = {"choices": [{"message": {"content": "test"}}]}
    
    # Run test
    result = function_that_calls_api()
    
    # Assert mock was called
    mock_api.assert_called_once()
```

### Real API Tests

Mark tests that require real API calls:

```python
@pytest.mark.requires_api
@pytest.mark.skipif(
    os.getenv("OPENAI_API_KEY") is None,
    reason="Requires OPENAI_API_KEY environment variable"
)
async def test_real_openai_api():
    """Test real OpenAI API integration."""
    client = create_llm_client(
        provider="openai",
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    response = await client.generate_completion(
        messages=[{"role": "user", "content": "Test"}]
    )
    
    assert response.content is not None
```

---

## CI/CD Integration

### GitHub Actions Workflow

Create `.github/workflows/test.yml`:

```yaml
name: Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.11", "3.12"]
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python ${{ matrix.python-version }}
      uses: actions/setup-python@v4
      with:
        python-version: ${{ matrix.python-version }}
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest pytest-cov pytest-asyncio pytest-mock
    
    - name: Run unit tests
      run: |
        pytest -m "unit" --cov=core --cov=llm --cov=schemas
    
    - name: Run integration tests
      run: |
        pytest -m "integration and not requires_api"
    
    - name: Generate coverage report
      run: |
        pytest --cov=core --cov=llm --cov=schemas --cov-report=xml
    
    - name: Upload coverage to Codecov
      uses: codecov/codecov-action@v3
      with:
        files: ./coverage.xml
```

### Pre-commit Hooks

Use pre-commit hooks to run tests before commits:

```yaml
# .pre-commit-config.yaml
repos:
  - repo: local
    hooks:
      - id: pytest-unit
        name: pytest unit tests
        entry: pytest -m unit
        language: system
        pass_filenames: false
        always_run: true
```

### Test on Pull Requests

Configure GitHub to require passing tests on PRs:

1. Go to repository Settings → Branches
2. Add branch protection rule for `main`
3. Require status checks to pass: `test`

---

## Contributing Guidelines

### Before Submitting Code

1. **Write Tests First**: Follow TDD when possible
2. **Run Tests Locally**: Ensure all tests pass
3. **Check Coverage**: Maintain or improve coverage
4. **Format Code**: Run `black` and `ruff` formatters
5. **Type Checking**: Run `mypy` for type checking

### Test Checklist

- [ ] All new functions have corresponding unit tests
- [ ] Edge cases are tested
- [ ] Integration tests added for new workflows
- [ ] Tests are properly marked (`@pytest.mark.unit`, etc.)
- [ ] Fixtures are used for shared test data
- [ ] Coverage meets minimum thresholds
- [ ] Tests pass locally
- [ ] No real API calls in unmarked tests
- [ ] Documentation updated if needed

### Code Review Focus

When reviewing tests, focus on:

1. **Test Coverage**: Are all code paths tested?
2. **Test Quality**: Are tests clear and maintainable?
3. **Assertions**: Are assertions specific and meaningful?
4. **Independence**: Are tests independent and isolated?
5. **Determinism**: Are tests reproducible?
6. **Performance**: Do tests run quickly?

---

## Additional Resources

### Pytest Documentation
- [Pytest Official Docs](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Parametrize](https://docs.pytest.org/en/stable/parametrize.html)

### Best Practices
- [Testing Best Practices](https://testdriven.io/blog/testing-best-practices/)
- [Python Testing with Pytest](https://realpython.com/pytest-python-testing/)
- [Test-Driven Development](https://www.obeythetestinggoat.com/)

### Tools
- [pytest](https://pytest.org/) - Testing framework
- [pytest-cov](https://pytest-cov.readthedocs.io/) - Coverage plugin
- [pytest-asyncio](https://pytest-asyncio.readthedocs.io/) - Async test support
- [pytest-mock](https://pytest-mock.readthedocs.io/) - Mocking utilities
- [pytest-benchmark](https://pytest-benchmark.readthedocs.io/) - Performance benchmarks

---

## Troubleshooting

### Common Issues

**Issue**: Tests fail with `ModuleNotFoundError`
**Solution**: Ensure project root is in PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Issue**: Tests pass locally but fail in CI
**Solution**: Check environment variables and dependencies

**Issue**: Slow test execution
**Solution**: Use markers to skip slow tests during development:
```bash
pytest -m "not slow"
```

**Issue**: Coverage not measuring correctly
**Solution**: Ensure source code is importable and coverage config is correct

### Getting Help

1. Check this guide
2. Review existing tests for examples
3. Check pytest documentation
4. Ask in team discussions
5. Open an issue for bugs

---

**Version**: 1.1
**Last Updated**: 2026-02-10
**Maintained By**: Development Team

