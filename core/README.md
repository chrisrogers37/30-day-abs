# Core Module

The `core/` module contains the pure, deterministic mathematical foundation of the AB Test Simulator. This module follows the principle of **separation of concerns** - it contains only mathematical logic with no HTTP, no LLM calls, and no global state.

## Purpose

The core module provides:
- **Pure mathematical functions** for AB test calculations
- **Deterministic results** that are reproducible with fixed seeds
- **Domain types** for mathematical concepts only
- **Statistical analysis** with multiple test options
- **Business impact calculations** based on mathematical results
- **Realistic data simulation** with treatment effect uncertainty

## Architecture Principles

- **No External Dependencies**: No HTTP, file I/O, or LLM calls
- **Deterministic**: All functions produce consistent results with same inputs
- **Immutable Types**: All dataclasses are frozen for data integrity
- **Mathematical Focus**: Only mathematical domain logic, no business context
- **Testable**: Comprehensive test coverage across core mathematical modules (634+ tests)
- **Reproducible**: Fixed seeds ensure consistent simulation results

## Module Contents

### `__init__.py` - Module Exports
Public API exports for the core module:

- **`Allocation`**: Traffic allocation between control/treatment groups
- **`DesignParams`**: Core statistical parameters (baseline, lift, alpha, power, traffic)
- **`SampleSize`**: Sample size calculation results
- **`SimResult`**: Simulation results with conversion counts
- **`AnalysisResult`**: Statistical analysis results (p-value, CI, significance)
- **`BusinessImpact`**: Mathematical business impact calculations
- **`TestQuality`**: Mathematical test quality indicators
- **`ValidationResult`**: Answer validation results with feedback
- **`ScoringResult`**: Quiz scoring results with grades
- **`AnswerKey`**: Answer keys for quiz questions
- **`QuizResult`**: Complete quiz results with scoring and feedback

### `types.py` - Core Domain Types
Pure mathematical domain objects with validation:

- **`Allocation`**: Traffic allocation between control/treatment groups
  - Validates proportions sum to 1.0
  - Properties: `control`, `treatment`, `total`
- **`DesignParams`**: Core statistical parameters
  - Fields: `baseline_conversion_rate`, `target_lift_pct`, `alpha`, `power`, `allocation`, `expected_daily_traffic`
  - Validates parameter ranges and constraints
- **`SampleSize`**: Sample size calculation results
  - Fields: `per_arm`, `total`, `days_required`, `power_achieved`
  - Validates mathematical consistency
- **`SimResult`**: Simulation results with conversion counts
  - Fields: `control_n`, `control_conversions`, `treatment_n`, `treatment_conversions`, `user_data`
  - Properties: `control_rate`, `treatment_rate`, `absolute_lift`, `relative_lift_pct`
- **`AnalysisResult`**: Statistical analysis results
  - Fields: `test_statistic`, `p_value`, `confidence_interval`, `confidence_level`, `significant`, `effect_size`, `power_achieved`, `recommendation`
- **`BusinessImpact`**: Mathematical business impact calculations
  - Fields: `absolute_lift`, `relative_lift_pct`, `revenue_impact_monthly`, `confidence_in_revenue`, `rollout_recommendation`, `risk_level`, `implementation_complexity`
- **`TestQuality`**: Mathematical test quality indicators
  - Fields: `early_stopping_risk`, `novelty_effect_potential`, `seasonality_impact`, `traffic_consistency`, `allocation_balance`, `sample_size_adequacy`, `power_achieved`

### `design.py` - Sample Size Calculation
Statistical design functions for AB test planning:

- **`compute_sample_size()`**: Two-proportion z-test sample size calculation
  - Uses standard formula: `n = (z_alpha + z_beta)^2 * [p1(1-p1) + p2(1-p2)] / (p2-p1)^2`
  - Returns `SampleSize` with per-arm, total, days required, and achieved power
- **`_get_z_score`**: Re-exported from `utils.get_z_score` for backwards compatibility
- **`validate_test_duration()`**: Validate test duration against business constraints
- **`suggest_parameter_adjustments()`**: Suggest parameter changes if constraints not met

> **Note:** Power calculation (`calculate_achieved_power`), MDE calculation (`calculate_minimum_detectable_effect`), and `normal_cdf` live in `utils.py`, not `design.py`.

### `simulate.py` - Data Simulation
Realistic data generation with treatment effect variation:

- **`simulate_trial()`**: Generate realistic AB test data with seeded RNG and treatment effect uncertainty
  - **Control rate variation**: ±10% variation around baseline to reflect sampling variability
  - **Treatment effect variation**: 70% chance of achieving target lift, 20% partial success, 8% failure, 2% negative effect
  - **Reproducible**: Fixed seeds ensure consistent results
  - **Realistic outcomes**: Allows for both successful and unsuccessful experiments
- **`_generate_user_data()`**: Create user-level data with timestamps
  - Generates realistic user attributes: session duration, page views, device type, traffic source
  - Uses Bernoulli trials for conversion simulation
- **`_generate_realistic_timestamp()`**: Generate timestamps with business hour patterns
- **`_generate_session_duration()`**: Generate session duration based on conversion status
- **`_generate_page_views()`**: Generate page views based on conversion status
- **`_generate_device_type()`**: Generate realistic device type distribution
- **`_generate_traffic_source()`**: Generate realistic traffic source distribution
- **`validate_simulation_consistency()`**: Validate simulated data against expected rates
- **`add_seasonality_pattern()`**: Add seasonality effects (weekend, holiday)
- **`export_user_data_csv()`**: Export user-level data to CSV
- **`get_aggregate_summary()`**: Generate aggregate summary statistics

### `analyze.py` - Statistical Analysis
Comprehensive statistical testing and analysis:

- **`analyze_results()`**: Main analysis function with multiple test options
  - Supports: `two_proportion_z`, `chi_square`, `fisher_exact`
  - Returns `AnalysisResult` with test statistics, p-value, CI, and recommendation
- **`_two_proportion_z_test()`**: Two-proportion z-test implementation
  - Calculates z-statistic, p-value, confidence interval, effect size, achieved power
- **`_chi_square_test()`**: Chi-square test for categorical data
  - Creates 2x2 contingency table, calculates chi-square statistic
- **`select_statistical_test()`**: Automatic test selection based on sample size and expected cell counts
  - Returns `StatisticalTestSelection` with test type, reasoning, and alternatives
- **`_fisher_exact_test()`**: Fisher's exact test using `scipy.stats.fisher_exact`
- **`_calculate_p_value()`**: P-value calculation for z-statistic
- **`_generate_recommendation()`**: Business recommendation based on statistical results
- **`make_rollout_decision()`**: Rollout decision based on confidence interval vs business target
- **`calculate_business_impact()`**: Business impact calculations and projections
- **`assess_test_quality()`**: Test quality indicators and potential issues
- **`_chi_square_p_value()`**: Chi-square p-value via `scipy.stats.chi2.sf`

### `rng.py` - Random Number Generation
Centralized PRNG factory for reproducible simulations:

- **`RNGFactory`**: Factory class for creating reproducible random number generators
  - Component-based seeding for deterministic but varied results
  - Thread-safe generator management
- **`get_rng()`**: Get seeded numpy Generator for reproducibility
- **`set_global_seed()`**: Set global seed for all random number generation
- **`reset_rng()`**: Reset all random number generators
- **`get_rng_state()`**: Get current state of all generators
- **`set_rng_state()`**: Restore state of all generators
- **Distribution generators**:
  - `generate_bernoulli_samples()`: Bernoulli trials
  - `generate_uniform_samples()`: Uniform distribution
  - `generate_normal_samples()`: Normal distribution
  - `generate_choice_samples()`: Random choices
  - `generate_weighted_choice_samples()`: Weighted random choices
  - `generate_poisson_samples()`: Poisson distribution
  - `generate_exponential_samples()`: Exponential distribution
  - `generate_beta_samples()`: Beta distribution
  - `generate_gamma_samples()`: Gamma distribution
  - `generate_multinomial_samples()`: Multinomial distribution
  - `generate_correlated_samples()`: Multivariate normal
  - `generate_time_series_samples()`: Time series with trend/seasonality
  - `generate_mixture_samples()`: Mixture distributions

### `validation.py` - Answer Validation and Scoring
Validation and scoring logic for quiz answers:

- **`validate_design_answer()`**: Validate individual design question answers
  - Supports all 6 design questions (MDE, target rate, relative lift, sample size, duration, additional conversions)
  - Uses scenario's `mde_absolute` when provided, falls back to calculated value
  - Returns `ValidationResult` with correctness, feedback, and tolerance
- **`validate_analysis_answer()`**: Validate individual analysis question answers
  - Supports all 7 analysis questions (control rate, treatment rate, absolute lift, relative lift, p-value, confidence interval, rollout decision)
  - Uses `SimResult` properties and `AnalysisResult` from statistical analysis
  - Returns `ValidationResult` with correctness, feedback, and tolerance
- **`calculate_correct_design_answers()`**: Calculate correct answers for all design questions
  - Uses scenario's `mde_absolute` when provided
  - Returns dictionary with all correct answers
- **`calculate_correct_analysis_answers()`**: Calculate correct answers for all analysis questions
  - Uses `SimResult` properties and runs statistical analysis
  - Includes rollout decision calculation using `make_rollout_decision`
  - Returns dictionary with all correct answers
- **`score_design_answers()`**: Score complete design quiz
  - Compares user answers against correct answers with tolerances
  - Returns `ScoringResult` with scores, percentage, and grade
- **`score_analysis_answers()`**: Score complete analysis quiz
  - Compares user answers against correct answers with tolerances
  - Supports 7 analysis questions including rollout decision
  - Returns `ScoringResult` with scores, percentage, and grade

### `scoring.py` - Answer Key Generation and Quiz Results
Answer key generation and comprehensive quiz result management:

- **`generate_design_answer_key()`**: Generate answer key for design questions
  - Creates `AnswerKey` with questions, hints, types, and correct answers
  - Includes all 6 design questions with proper formatting
- **`generate_analysis_answer_key()`**: Generate answer key for analysis questions
  - Creates `AnswerKey` with questions, hints, types, and correct answers
  - Includes all 7 analysis questions with proper formatting
- **`generate_quiz_feedback()`**: Generate detailed feedback for quiz results
  - Creates comprehensive feedback with question-by-question results
  - Includes overall score, grade, and individual question feedback
- **`create_complete_quiz_result()`**: Create complete quiz result
  - Combines answer key, scoring results, user answers, and feedback
  - Returns `QuizResult` with all quiz information
- **`export_answer_key_to_csv()`**: Export answer key to CSV file
- **`export_quiz_results_to_csv()`**: Export quiz results to CSV file
- **`_get_question_key()`**: Helper function to get question keys by number and type

### `logging.py` - Centralized Logging System
Unified logging configuration and quiz session tracking:

- **`setup_logging()`**: Configure centralized logging with file rotation and clean terminal output
- **`QuizSessionLogger`**: Structured logging for complete quiz session journeys
  - Session start/end with timing metrics
  - Scenario generation details
  - Question-by-question progress logging
  - Simulation and analysis result logging
  - Visual separators and organized output sections
- **Log file management**: Automatic log rotation and organized file structure (`logs/` directory)

### `question_bank.py` - Question Bank
Comprehensive question bank with 50+ questions across multiple categories:

- **Design Questions**: MDE, sample size, duration, power analysis
- **Analysis Questions**: Statistical test results, confidence intervals, p-values
- **Planning Questions**: Pre-registration, guardrail metrics, test prioritization
- **Interpretation Questions**: Practical vs. statistical significance, effect size interpretation
- **Question metadata**: Difficulty levels (EASY, MEDIUM, HARD), skills-tested tags, complication types
- **Variable scoring**: Different point values based on question difficulty and type

### `utils.py` - Mathematical Utilities
Helper functions for calculations and formatting:

- **Lift calculations**:
  - `relative_lift_to_absolute()`: Convert relative lift percentage to absolute difference
  - `absolute_lift_to_relative()`: Convert absolute difference to relative lift percentage
- **Revenue impact**:
  - `calculate_revenue_impact()`: Revenue impact from conversion rate improvement
  - `calculate_monthly_revenue_impact()`: Monthly revenue impact calculation
  - `calculate_confidence_interval_for_revenue()`: Revenue confidence intervals
  - `calculate_sample_size_for_revenue_detection()`: Sample size for revenue detection
- **Effect size calculations**:
  - `calculate_effect_size_cohens_h()`: Cohen's h for proportions
  - `interpret_effect_size_cohens_h()`: Interpret Cohen's h effect size
  - `calculate_effect_size_cohens_d()`: Cohen's d for means
  - `interpret_effect_size_cohens_d()`: Interpret Cohen's d effect size
- **Confidence intervals**:
  - `calculate_confidence_interval_for_proportion()`: CI for single proportion
  - `calculate_confidence_interval_for_difference()`: CI for difference in proportions
  - `calculate_conversion_rate_confidence_interval()`: CI for conversion rate
  - `calculate_relative_lift_confidence_interval()`: CI for relative lift
- **Power and sample size**:
  - `calculate_power_for_proportions()`: Statistical power for proportions
  - `calculate_minimum_detectable_effect()`: MDE calculation
  - `calculate_required_sample_size_for_power()`: Sample size for given power
- **Formatting utilities**:
  - `format_percentage()`: Format decimal as percentage string
  - `format_currency()`: Format number as currency
  - `format_large_number()`: Format large numbers with suffixes
- **Validation utilities**:
  - `validate_conversion_rate()`: Validate conversion rate bounds
  - `validate_sample_size()`: Validate sample size is positive
  - `validate_confidence_level()`: Validate confidence level bounds
  - `validate_significance_level()`: Validate significance level bounds
  - `validate_power()`: Validate power level bounds
- **Standard error calculations**:
  - `calculate_conversion_rate_standard_error()`: Standard error for conversion rate
- **`_normal_cdf()`**: Normal cumulative distribution function

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

# Core calculates true rates internally with realistic variation
sim_result = simulate_trial(params, seed=42)
print(f"Control: {sim_result.control_conversions}/{sim_result.control_n}")
print(f"Treatment: {sim_result.treatment_conversions}/{sim_result.treatment_n}")
print(f"Actual lift: {sim_result.relative_lift_pct:.1%}")
```

### Statistical Analysis
```python
from core.analyze import analyze_results

analysis = analyze_results(sim_result, alpha=0.05)
print(f"P-value: {analysis.p_value:.4f}")
print(f"Significant: {analysis.significant}")
print(f"Recommendation: {analysis.recommendation}")
```

### Business Impact Analysis
```python
from core.analyze import calculate_business_impact, make_rollout_decision

# Comprehensive business impact analysis
business_impact = calculate_business_impact(
    sim_result, 
    revenue_per_conversion=50.0,
    monthly_traffic=30000
)
print(f"Monthly revenue impact: ${business_impact.revenue_impact_monthly:,.2f}")
print(f"Rollout recommendation: {business_impact.rollout_recommendation}")

# Focused rollout decision based on CI vs business target
rollout_decision = make_rollout_decision(
    sim_result, 
    analysis, 
    business_target_absolute=0.03  # 3% absolute lift
)
print(f"Rollout decision: {rollout_decision}")
```

### Random Number Generation
```python
from core.rng import get_rng, generate_bernoulli_samples

# Get component-specific RNG
rng = get_rng("simulation")
samples = generate_bernoulli_samples(rate=0.05, n=1000, rng_name="simulation")
print(f"Generated {len(samples)} Bernoulli samples")
```

### Answer Validation and Scoring
```python
from core.validation import validate_design_answer, validate_analysis_answer, score_design_answers, score_analysis_answers
from core.scoring import generate_design_answer_key, create_complete_quiz_result

# Validate individual design question
validation_result = validate_design_answer(
    question_num=1, 
    user_answer=1.0, 
    design_params=params, 
    sample_size_result=sample_size,
    mde_absolute=0.01  # From LLM scenario
)
print(f"Correct: {validation_result.is_correct}, Feedback: {validation_result.feedback}")

# Validate individual analysis question (including rollout decision)
validation_result = validate_analysis_answer(
    question_num=7, 
    user_answer="proceed_with_confidence", 
    sim_result=sim_result,
    business_target_absolute=0.03
)
print(f"Correct: {validation_result.is_correct}, Feedback: {validation_result.feedback}")

# Score complete design quiz
user_answers = {"mde_absolute": 1.0, "target_conversion_rate": 6.0, ...}
scoring_result = score_design_answers(user_answers, params, sample_size, mde_absolute=0.01)
print(f"Score: {scoring_result.total_score}/{scoring_result.max_score} ({scoring_result.percentage:.1f}%)")

# Score complete analysis quiz (7 questions including rollout decision)
analysis_answers = {"control_conversion_rate": 25.0, "rollout_decision": "proceed_with_confidence", ...}
scoring_result = score_analysis_answers(analysis_answers, sim_result, business_target_absolute=0.03)
print(f"Score: {scoring_result.total_score}/{scoring_result.max_score} ({scoring_result.percentage:.1f}%)")

# Generate answer key and complete quiz result
answer_key = generate_design_answer_key(params, sample_size)
quiz_result = create_complete_quiz_result(user_answers, design_params=params, sample_size_result=sample_size)
```

### Utility Functions
```python
from core.utils import relative_lift_to_absolute, format_percentage

# Convert relative lift to absolute
absolute_lift = relative_lift_to_absolute(control_rate=0.05, relative_lift_pct=20.0)
print(f"Absolute lift: {format_percentage(absolute_lift)}")
```

## Testing

The core module has comprehensive test coverage:

- **Unit tests**: All mathematical functions tested with known scenarios
- **Property tests**: Mathematical properties (monotonicity, boundary conditions)
- **Edge cases**: Very small baselines, extreme lifts, boundary values
- **Reproducibility**: Fixed seeds ensure consistent test results
- **Validation tests**: Parameter validation and error handling

Run tests with:
```bash
pytest tests/         # Full test suite
```

## Integration

The core module is designed to be used by:

- **`llm/`**: LLM outputs are validated and converted to core types
- **`schemas/`**: DTOs bridge between external interfaces and core types (via `DesignParamsDTO.to_design_params()`)
- **`ui/`**: Streamlit app displays core calculation results and uses core validation/scoring

## Data Flow

```
LLM Scenarios → Schema DTOs → Core Types → Mathematical Functions → Core Results → UI Display
```

The core module never directly handles:
- HTTP requests/responses
- JSON serialization
- Business context (company type, user segments)
- LLM prompts or responses
- File I/O operations
- UI state management

## Key Features

### Realistic Simulation
- **Control rate variation**: ±10% around baseline to reflect sampling variability
- **Treatment effect uncertainty**: 70% success, 20% partial, 8% failure, 2% negative
- **User-level data**: Realistic timestamps, session duration, device types, traffic sources
- **Seasonality effects**: Weekend and holiday patterns

### Statistical Rigor
- **Multiple test types**: Two-proportion z-test, chi-square, Fisher's exact
- **Effect size calculations**: Cohen's h and d
- **Power analysis**: Achieved power calculations
- **Confidence intervals**: For proportions, differences, and relative lift

### Business Impact
- **Revenue projections**: Monthly revenue impact calculations
- **Risk assessment**: Rollout recommendations and risk levels
- **Quality indicators**: Test quality assessment and potential issues
- **Rollout decisions**: CI-based go/no-go decisions vs business targets

### Answer Validation and Scoring
- **Individual question validation**: Real-time feedback with tolerances
- **Complete quiz scoring**: Comprehensive scoring with grades and feedback
- **Answer key generation**: Automatic generation of correct answers
- **Export capabilities**: CSV export for answer keys and quiz results
- **MDE handling**: Uses LLM scenario's `mde_absolute` when available
- **Rollout decision validation**: CI-based decision validation for Question 7

### Reproducibility
- **Fixed seeds**: Consistent results across runs
- **Component-based RNG**: Deterministic but varied random number generation
- **State management**: RNG state saving and restoration

## Future Extensions

The core module can be extended with:
- **Additional test types**: Mann-Whitney U, t-tests for continuous metrics
- **Sequential testing**: Group sequential boundaries
- **Multiple metrics**: CUPED, variance reduction techniques
- **Advanced power analysis**: Conditional power, futility analysis
- **Bayesian methods**: Bayesian AB testing and credible intervals
- **Multi-armed bandits**: Thompson sampling, UCB algorithms
- **Advanced validation**: Custom validation rules, adaptive tolerances
- **Enhanced scoring**: Weighted scoring, partial credit, learning analytics
- **Advanced business impact**: ROI calculations, risk-adjusted revenue projections
- **Multi-metric analysis**: CUPED, variance reduction, multiple outcome variables

All extensions maintain the core principles of determinism, purity, and mathematical focus.

## Recent Updates

### Question 7 Implementation
- **Added rollout decision question**: New Question 7 in analysis section
- **`make_rollout_decision()` function**: CI-based go/no-go decision logic
- **Updated validation**: Support for 7 analysis questions
- **Enhanced scoring**: Rollout decision validation with exact match tolerance

### Architecture Improvements
- **Core validation module**: Centralized answer validation and scoring
- **Core scoring module**: Answer key generation and quiz result management
- **UI simplification**: Removed duplicated statistical calculations from UI layer
- **Separation of concerns**: UI focuses on flow, core handles calculations

### Function Status
- **`calculate_business_impact()`**: Still functional, provides comprehensive business analysis
- **`make_rollout_decision()`**: New focused function for CI-based decisions
- **`_generate_recommendation()`**: Used internally by `analyze_results()`
- **`assess_test_quality()`**: Available but not currently used in UI