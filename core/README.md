# Core Module

The `core/` module contains the pure, deterministic mathematical foundation of the AB Test Simulator. This module follows the principle of **separation of concerns** - it contains only mathematical logic with no HTTP, no LLM calls, and no global state.

## Purpose

The core module provides:
- **Pure mathematical functions** for AB test calculations
- **Deterministic results** that are reproducible with fixed seeds
- **Domain types** for mathematical concepts only
- **Statistical analysis** with multiple test options
- **Business impact calculations** based on mathematical results

## Architecture Principles

- **No External Dependencies**: No HTTP, file I/O, or LLM calls
- **Deterministic**: All functions produce consistent results with same inputs
- **Immutable Types**: All dataclasses are frozen for data integrity
- **Mathematical Focus**: Only mathematical domain logic, no business context
- **Testable**: 100% branch coverage on mathematical functions

## Module Contents

### `types.py` - Core Domain Types
Pure mathematical domain objects:

- **`Allocation`**: Traffic allocation between control/treatment groups
- **`DesignParams`**: Core statistical parameters (baseline, lift, alpha, power, traffic)
- **`SampleSize`**: Sample size calculation results
- **`SimResult`**: Simulation results with conversion counts
- **`AnalysisResult`**: Statistical analysis results (p-value, CI, significance)
- **`BusinessImpact`**: Mathematical business impact calculations
- **`TestQuality`**: Mathematical test quality indicators

### `design.py` - Sample Size Calculation
Statistical design functions:

- **`compute_sample_size()`**: Two-proportion z-test sample size calculation
- **`_get_z_score()`**: Z-score calculation for given alpha and direction
- **`_calculate_achieved_power()`**: Power calculation for given sample size
- **`calculate_minimum_detectable_effect()`**: MDE calculation

### `simulate.py` - Data Simulation
Deterministic data generation:

- **`simulate_trial()`**: Generate realistic AB test data with seeded RNG
- **`_generate_user_data()`**: Create user-level data with timestamps
- **Traffic splitting**: Based on allocation with realistic variation
- **Reproducible**: Fixed seeds ensure consistent results

### `analyze.py` - Statistical Analysis
Comprehensive statistical testing:

- **`analyze_results()`**: Main analysis function with multiple test options
- **`_two_proportion_z_test()`**: Two-proportion z-test implementation
- **`_chi_square_test()`**: Chi-square test for categorical data
- **`_fisher_exact_test()`**: Fisher's exact test for small samples
- **Confidence intervals**: For effect sizes and relative lift
- **Power analysis**: Achieved power calculations

### `rng.py` - Random Number Generation
Centralized PRNG factory:

- **`get_rng()`**: Get seeded numpy Generator for reproducibility
- **Consistent seeding**: Same seed produces same results across modules
- **Thread-safe**: Each call gets independent generator

### `utils.py` - Mathematical Utilities
Helper functions for calculations:

- **`calculate_relative_lift()`**: Convert absolute to relative lift
- **`calculate_absolute_lift()`**: Convert relative to absolute lift
- **Business impact helpers**: Revenue calculations and projections

## Usage Examples

### Sample Size Calculation
```python
from core.types import DesignParams, Allocation
from core.design import compute_sample_size

allocation = Allocation(control=0.5, treatment=0.5)
params = DesignParams(
    baseline_conversion_rate=0.05,
    target_lift_pct=0.15,
    alpha=0.05,
    power=0.8,
    allocation=allocation,
    expected_daily_traffic=10000
)

sample_size = compute_sample_size(params)
print(f"Required: {sample_size.per_arm} per arm, {sample_size.days_required} days")
```

### Data Simulation
```python
from core.simulate import simulate_trial

true_rates = {"control": 0.05, "treatment": 0.0575}
sim_result = simulate_trial(params, true_rates, seed=42)
print(f"Control: {sim_result.control_conversions}/{sim_result.control_n}")
print(f"Treatment: {sim_result.treatment_conversions}/{sim_result.treatment_n}")
```

### Statistical Analysis
```python
from core.analyze import analyze_results

analysis = analyze_results(sim_result, alpha=0.05)
print(f"P-value: {analysis.p_value:.4f}")
print(f"Significant: {analysis.significant}")
print(f"Recommendation: {analysis.recommendation}")
```

## Testing

The core module has comprehensive test coverage:

- **Unit tests**: All mathematical functions tested with known scenarios
- **Property tests**: Mathematical properties (monotonicity, boundary conditions)
- **Edge cases**: Very small baselines, extreme lifts, boundary values
- **Reproducibility**: Fixed seeds ensure consistent test results

Run tests with:
```bash
python test_basic.py  # Basic functionality test
pytest tests/         # Full test suite
```

## Integration

The core module is designed to be used by:

- **`api/`**: FastAPI endpoints convert DTOs to core types
- **`llm/`**: LLM outputs are validated and converted to core types
- **`ui/`**: User interfaces display core calculation results

## Data Flow

```
API DTOs → Core Types → Mathematical Functions → Core Results → API DTOs
```

The core module never directly handles:
- HTTP requests/responses
- JSON serialization
- Business context (company type, user segments)
- LLM prompts or responses
- File I/O operations

## Future Extensions

The core module can be extended with:
- **Additional test types**: Mann-Whitney U, t-tests for continuous metrics
- **Sequential testing**: Group sequential boundaries
- **Multiple metrics**: CUPED, variance reduction techniques
- **Advanced power analysis**: Conditional power, futility analysis

All extensions maintain the core principles of determinism, purity, and mathematical focus.
