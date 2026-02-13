# Testing Suite - 30 Day A/Bs

Welcome to the comprehensive testing suite for 30 Day A/Bs!

## Quick Start

```bash
# Install test dependencies
pip install pytest pytest-cov pytest-asyncio pytest-mock

# Run all tests
pytest

# Run with coverage
pytest --cov=core --cov=llm --cov=schemas --cov-report=html

# Run specific test categories
pytest -m unit              # Unit tests only
pytest -m integration       # Integration tests only
pytest tests/core/          # Core module tests only
```

## Test Structure

```
tests/
├── __init__.py
├── conftest.py                      # Shared pytest fixtures (20+ fixtures)
│
├── core/                            # Core module tests (25 test files)
│   ├── test_analyze.py              # Statistical analysis tests
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
│   ├── test_simulate_utilities.py   # Simulation utility function tests
│   ├── test_types.py                # Domain type tests
│   ├── test_types_extended.py       # Extended type tests
│   ├── test_utils.py                # Utility function tests
│   ├── test_utils_extended.py       # Extended utility tests
│   ├── test_validation.py           # Answer validation tests
│   ├── test_validation_by_id.py     # Validation by question ID tests
│   └── test_validation_scoring.py   # Validation scoring integration tests
│
├── llm/                             # LLM integration tests (6 test files)
│   ├── test_client.py               # LLM client tests
│   ├── test_generator.py            # Scenario generation tests
│   ├── test_guardrails.py           # Parameter validation tests
│   ├── test_integration.py          # LLM pipeline tests
│   ├── test_novelty_scoring.py      # Novelty scoring tests
│   └── test_parser.py               # JSON parsing tests
│
├── schemas/                         # Schema validation tests (7 test files)
│   ├── test_analyze.py              # Analysis schema tests
│   ├── test_complications.py        # Complications schema tests
│   ├── test_design.py               # Design schema tests
│   ├── test_evaluation.py           # Evaluation schema tests
│   ├── test_scenario.py             # Scenario schema tests
│   ├── test_shared.py               # Shared schema tests
│   └── test_simulate.py             # Simulation schema tests
│
├── ui/                              # UI component tests
│   └── test_streamlit_app_enhanced.py  # Enhanced Streamlit tests
│
├── integration/                     # E2E integration tests
│   ├── test_complete_workflow.py    # Full quiz flow tests
│   ├── test_data_export.py          # Data export tests
│   ├── test_llm_pipeline.py         # LLM → Core pipeline tests
│   └── test_real_api.py             # Real API tests (skipped in CI)
│
├── fixtures/                        # Shared test data
│   ├── scenarios/                   # Sample scenario JSON files
│   │   ├── ecommerce_scenario.json
│   │   ├── saas_scenario.json
│   │   └── fintech_scenario.json
│   ├── expected_results.py          # Expected calculation results
│   ├── llm_responses.py             # Mock LLM responses
│   └── test_data.py                 # Reusable test data
│
├── helpers/                         # Test utilities
│   ├── assertions.py                # Custom assertions
│   ├── factories.py                 # Object factories
│   └── mocks.py                     # Mock objects
│
├── test_basic.py                    # Quick smoke tests
├── test_notebooks.py                # Notebook template tests
└── test_streamlit_app.py            # Basic Streamlit import/functionality tests
```

## Test Categories

### Unit Tests (`@pytest.mark.unit`)
Fast, isolated tests for individual functions:
- Core mathematical calculations
- Type validation
- Utility functions
- Schema validation

### Integration Tests (`@pytest.mark.integration`)
Module interaction tests:
- Complete workflow (design → simulate → analyze)
- LLM → Core pipeline
- Data export functionality

### E2E Tests (`@pytest.mark.e2e`)
End-to-end user workflow tests:
- Full quiz flow
- Complete analysis pipeline
- User interaction scenarios

## Coverage Targets

- **Core Module**: 90%+ (critical mathematical functions)
- **LLM Module**: 80%+ (integration logic)
- **Schemas Module**: 85%+ (validation logic)
- **UI Module**: 60%+ (component tests)

## Running Tests

### Basic Commands

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=core --cov=llm --cov=schemas

# Generate HTML coverage report
pytest --cov=core --cov=llm --cov=schemas --cov-report=html
open htmlcov/index.html
```

### Test Selection

```bash
# By marker
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests only
pytest -m "not slow"              # Exclude slow tests
pytest -m "not requires_api"      # Exclude tests needing API keys

# By module
pytest tests/core/                # Core module tests
pytest tests/llm/                 # LLM module tests
pytest tests/integration/         # Integration tests

# By file
pytest tests/core/test_design.py  # Specific file

# By function
pytest tests/core/test_design.py::TestComputeSampleSize::test_compute_sample_size_basic
```

### Output Options

```bash
# Show print statements
pytest -s

# Stop on first failure
pytest -x

# Show local variables on failure
pytest -l

# Quiet output
pytest -q

# Show test durations
pytest --durations=10
```

## Test Fixtures

Shared fixtures are defined in `conftest.py`:

- **Design Parameters**: `standard_design_params`, `high_baseline_design_params`, `low_baseline_design_params`
- **Allocations**: `standard_allocation`, `unbalanced_allocation`
- **Simulation Results**: `simple_sim_result`, `significant_sim_result`, `non_significant_sim_result`
- **Tolerances**: `tolerance_percentage`, `tolerance_absolute`
- **Mock Data**: `sample_scenario_dict`, `mock_llm_response_json`

## Writing Tests

### Example Unit Test

```python
import pytest
from core.design import compute_sample_size
from tests.helpers.factories import create_design_params

class TestSampleSize:
    @pytest.mark.unit
    def test_compute_sample_size(self):
        params = create_design_params()
        result = compute_sample_size(params)
        
        assert result.per_arm > 0
        assert result.total == 2 * result.per_arm
```

### Example Integration Test

```python
import pytest
from tests.helpers.factories import create_design_params
from core.design import compute_sample_size
from core.simulate import simulate_trial
from core.analyze import analyze_results

class TestWorkflow:
    @pytest.mark.integration
    def test_complete_flow(self):
        # Design
        params = create_design_params()
        sample_size = compute_sample_size(params)
        
        # Simulate
        sim_result = simulate_trial(params, seed=42)
        
        # Analyze
        analysis = analyze_results(sim_result, alpha=0.05)
        
        assert analysis.p_value >= 0.0
        assert analysis.p_value <= 1.0
```

## Documentation

For detailed testing documentation, see:

- **[Testing Guide](../development_docs/TESTING_GUIDE.md)**: Comprehensive testing documentation
- **[Development Guide](../development_docs/DEVELOPMENT_GUIDE.md)**: Development workflow and standards
- **[Development Docs README](../development_docs/README.md)**: Navigation guide

## Contributing

When contributing tests:

1. Follow the existing test structure
2. Use appropriate markers (`@pytest.mark.unit`, etc.)
3. Use fixtures from `conftest.py`
4. Use helpers from `tests/helpers/`
5. Maintain test coverage above thresholds
6. Ensure all tests pass before submitting PR

## Troubleshooting

### Common Issues

**Issue**: Tests not found
**Solution**: Ensure you're running pytest from project root

**Issue**: Import errors
**Solution**: Add project root to PYTHONPATH:
```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

**Issue**: Fixture not found
**Solution**: Check `conftest.py` for available fixtures

**Issue**: Coverage not working
**Solution**: Install pytest-cov:
```bash
pip install pytest-cov
```

## CI/CD

Tests are configured to run in CI/CD pipelines:

- **Unit tests**: Run on every commit
- **Integration tests**: Run on pull requests
- **Real API tests**: Run manually or nightly (requires API keys)

See `.github/workflows/test.yml` for CI configuration (when set up).

---

**Happy Testing!** 🧪

For questions or issues, see the [Development Guide](../development_docs/DEVELOPMENT_GUIDE.md) or create an issue on GitHub.

