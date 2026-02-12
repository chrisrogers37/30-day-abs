"""
Statistical analysis and answer key generation.

This module performs comprehensive statistical analysis on simulated data
and generates detailed answer keys for user evaluation.
"""

import math
from typing import Optional

from scipy.stats import fisher_exact as scipy_fisher_exact
from scipy.stats import chi2

from .types import SimResult, AnalysisResult, BusinessImpact, TestQuality, DesignParams, StatisticalTestSelection
from .utils import (
    normal_cdf,
    calculate_achieved_power,
    calculate_effect_size_cohens_h,
    calculate_confidence_interval_for_difference,
)

# --- Statistical Thresholds ---
# Effect size thresholds for recommendation (Cohen's h scale)
EFFECT_SIZE_LARGE = 0.2
EFFECT_SIZE_MEDIUM = 0.1

# Power threshold below which test is considered underpowered
MIN_ADEQUATE_POWER = 0.8

# P-value threshold for marginal significance
MARGINAL_SIGNIFICANCE_THRESHOLD = 0.1

# Business impact thresholds (absolute lift)
LIFT_THRESHOLD_HIGH_CONFIDENCE = 0.01    # 1% absolute lift
LIFT_THRESHOLD_MODERATE_CONFIDENCE = 0.005  # 0.5% absolute lift

# Test quality thresholds
EARLY_STOPPING_HIGH_RISK_N = 1000
EARLY_STOPPING_MEDIUM_RISK_N = 5000
NOVELTY_EFFECT_HIGH_THRESHOLD = 0.2    # 20% target lift
NOVELTY_EFFECT_MEDIUM_THRESHOLD = 0.1  # 10% target lift


def select_statistical_test(sim_result: SimResult) -> StatisticalTestSelection:
    """
    Automatically select the most appropriate statistical test based on sample characteristics.

    Selection criteria:
    - Fisher's exact test: When any expected cell count < 5 (small sample rule)
    - Chi-square test: When sample size >= 5 per cell but < 30 per group
    - Two-proportion z-test: When sample size >= 30 per group (normal approximation valid)

    Args:
        sim_result: Simulation results with conversion counts

    Returns:
        StatisticalTestSelection with recommended test type and reasoning
    """
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions

    total_n = n1 + n2
    total_conversions = x1 + x2
    total_non_conversions = total_n - total_conversions

    # Calculate expected cell counts for the 2x2 contingency table
    # Expected = (row_total * column_total) / grand_total
    expected_cells = []
    if total_n > 0:
        expected_cells = [
            total_conversions * n1 / total_n,      # Control conversions
            total_non_conversions * n1 / total_n,  # Control non-conversions
            total_conversions * n2 / total_n,      # Treatment conversions
            total_non_conversions * n2 / total_n   # Treatment non-conversions
        ]

    min_expected = min(expected_cells) if expected_cells else 0
    min_sample = min(n1, n2)

    # Decision logic
    if min_expected < 5:
        return StatisticalTestSelection(
            test_type="fisher_exact",
            reasoning="Fisher's exact test selected: One or more expected cell counts are below 5, "
                     f"which violates chi-square assumptions (min expected: {min_expected:.1f}). "
                     "Fisher's exact test provides accurate p-values for small samples.",
            sample_size_adequate=min_sample >= 10,
            assumptions_met=True,  # Fisher's exact has no distributional assumptions
            alternative_tests=["chi_square", "two_proportion_z"],
            min_expected_cell_count=min_expected
        )
    elif min_sample < 30:
        return StatisticalTestSelection(
            test_type="chi_square",
            reasoning="Chi-square test selected: Sample sizes are adequate for chi-square "
                     f"(all expected cells >= 5, min: {min_expected:.1f}), but groups are too small "
                     f"for reliable normal approximation (min group size: {min_sample}). "
                     "Chi-square test is appropriate for this intermediate sample size.",
            sample_size_adequate=True,
            assumptions_met=min_expected >= 5,
            alternative_tests=["fisher_exact", "two_proportion_z"],
            min_expected_cell_count=min_expected
        )
    else:
        # Large sample - z-test is appropriate
        # Check additional z-test assumptions
        p1 = x1 / n1 if n1 > 0 else 0
        p2 = x2 / n2 if n2 > 0 else 0

        # Rule of thumb: np >= 5 and n(1-p) >= 5 for normal approximation
        np_checks = [
            n1 * p1 >= 5,
            n1 * (1 - p1) >= 5,
            n2 * p2 >= 5,
            n2 * (1 - p2) >= 5
        ]
        assumptions_met = all(np_checks)

        return StatisticalTestSelection(
            test_type="two_proportion_z",
            reasoning="Two-proportion z-test selected: Both groups have adequate sample sizes "
                     f"(control: {n1}, treatment: {n2}) and expected cell counts "
                     f"(min: {min_expected:.1f}) for reliable normal approximation. "
                     "This is the standard test for comparing proportions with large samples.",
            sample_size_adequate=True,
            assumptions_met=assumptions_met,
            alternative_tests=["chi_square"],
            min_expected_cell_count=min_expected
        )


def analyze_results(sim_result: SimResult, alpha: float = 0.05,
                   test_type: str = "auto",
                   test_direction: str = "two_tailed") -> AnalysisResult:
    """
    Perform comprehensive statistical analysis on simulation results.

    Args:
        sim_result: Simulation results with conversion counts
        alpha: Significance level
        test_type: Type of statistical test to perform ("auto" for automatic selection,
                  or "two_proportion_z", "chi_square", "fisher_exact")
        test_direction: One-tailed or two-tailed test

    Returns:
        AnalysisResult with test statistics, p-value, CI, recommendation, and test selection info
    """
    # Automatic test selection
    test_selection = None
    if test_type == "auto":
        test_selection = select_statistical_test(sim_result)
        actual_test_type = test_selection.test_type
    else:
        actual_test_type = test_type

    # Perform the selected test
    if actual_test_type == "two_proportion_z":
        result = _two_proportion_z_test(sim_result, alpha, test_direction)
    elif actual_test_type == "chi_square":
        result = _chi_square_test(sim_result, alpha)
    elif actual_test_type == "fisher_exact":
        result = _fisher_exact_test(sim_result, alpha)
    else:
        raise ValueError(f"Unsupported test type: {actual_test_type}")

    # Add test selection info to result
    result.test_type_used = actual_test_type
    result.test_selection = test_selection

    return result


def _two_proportion_z_test(sim_result: SimResult, alpha: float, 
                          direction: str) -> AnalysisResult:
    """
    Perform two-proportion z-test for comparing conversion rates.
    
    Args:
        sim_result: Simulation results
        alpha: Significance level
        direction: Test direction
        
    Returns:
        AnalysisResult with z-test results
    """
    # Extract data
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions
    
    # Calculate proportions
    p1 = x1 / n1 if n1 > 0 else 0
    p2 = x2 / n2 if n2 > 0 else 0
    
    # Calculate pooled proportion
    p_pooled = (x1 + x2) / (n1 + n2)
    
    # Calculate standard error
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    
    # Calculate z-statistic
    z_statistic = (p2 - p1) / se if se > 0 else 0
    
    # Calculate p-value
    p_value = _calculate_p_value(z_statistic, direction)

    return _build_analysis_result(sim_result, z_statistic, p_value, alpha, direction)


def _chi_square_test(sim_result: SimResult, alpha: float) -> AnalysisResult:
    """
    Perform chi-square test for independence.
    
    Args:
        sim_result: Simulation results
        alpha: Significance level
        
    Returns:
        AnalysisResult with chi-square test results
    """
    # Create 2x2 contingency table
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions
    
    # Observed frequencies
    observed = [
        [x1, n1 - x1],  # Control: conversions, non-conversions
        [x2, n2 - x2]   # Treatment: conversions, non-conversions
    ]
    
    # Calculate expected frequencies
    total_conversions = x1 + x2
    total_users = n1 + n2
    total_non_conversions = total_users - total_conversions
    
    expected = [
        [total_conversions * n1 / total_users, total_non_conversions * n1 / total_users],
        [total_conversions * n2 / total_users, total_non_conversions * n2 / total_users]
    ]
    
    # Calculate chi-square statistic
    chi_square = 0
    for i in range(2):
        for j in range(2):
            if expected[i][j] > 0:
                chi_square += (observed[i][j] - expected[i][j]) ** 2 / expected[i][j]
    
    # Calculate p-value (approximate)
    p_value = _chi_square_p_value(chi_square, df=1)

    return _build_analysis_result(sim_result, chi_square, p_value, alpha)


def _fisher_exact_test(sim_result: SimResult, alpha: float) -> AnalysisResult:
    """
    Perform Fisher's exact test using scipy.

    Args:
        sim_result: Simulation results
        alpha: Significance level

    Returns:
        AnalysisResult with Fisher's exact test results
    """
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions

    # Build 2x2 contingency table
    table = [[x1, n1 - x1],
             [x2, n2 - x2]]

    odds_ratio, p_value = scipy_fisher_exact(table, alternative='two-sided')
    odds_ratio = float(odds_ratio)
    p_value = float(p_value)

    return _build_analysis_result(sim_result, odds_ratio, p_value, alpha)


def _build_analysis_result(
    sim_result: SimResult,
    test_statistic: float,
    p_value: float,
    alpha: float,
    direction: str = "two_tailed"
) -> AnalysisResult:
    """
    Build a standardized AnalysisResult from test-specific statistic and p-value.

    This helper encapsulates the shared post-test flow: confidence interval,
    effect size, power calculation, recommendation, and result construction.

    Args:
        sim_result: Simulation results with conversion counts
        test_statistic: The test-specific statistic (z-score, chi-square, or odds ratio)
        p_value: The computed p-value
        alpha: Significance level
        direction: Test direction for power calculation

    Returns:
        AnalysisResult with all computed fields
    """
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions
    p1 = x1 / n1 if n1 > 0 else 0
    p2 = x2 / n2 if n2 > 0 else 0

    ci_lower, ci_upper = calculate_confidence_interval_for_difference(
        p1, p2, n1, n2, confidence_level=1 - alpha
    )
    significant = p_value < alpha
    effect_size = calculate_effect_size_cohens_h(p1, p2)
    power_achieved = calculate_achieved_power(p1, p2, n1, n2, alpha, direction)
    recommendation = _generate_recommendation(significant, p_value, effect_size, power_achieved)

    return AnalysisResult(
        test_statistic=test_statistic,
        p_value=p_value,
        confidence_interval=(ci_lower, ci_upper),
        confidence_level=1 - alpha,
        significant=significant,
        effect_size=effect_size,
        power_achieved=power_achieved,
        recommendation=recommendation
    )


def _calculate_p_value(z_statistic: float, direction: str) -> float:
    """
    Calculate p-value for z-statistic.
    
    Args:
        z_statistic: Z-test statistic
        direction: Test direction
        
    Returns:
        P-value
    """
    # Use normal CDF approximation
    p_value = 2 * (1 - normal_cdf(abs(z_statistic)))
    
    if direction == "one_tailed":
        p_value = p_value / 2
    
    return min(max(p_value, 0.0), 1.0)


def _chi_square_p_value(chi_square: float, df: int) -> float:
    """
    Calculate p-value for chi-square statistic using scipy.

    Args:
        chi_square: Chi-square statistic
        df: Degrees of freedom

    Returns:
        P-value (survival function)
    """
    return float(chi2.sf(chi_square, df))


def _generate_recommendation(significant: bool, p_value: float, 
                           effect_size: float, power_achieved: float) -> str:
    """
    Generate business recommendation based on statistical results.
    
    Args:
        significant: Whether the result is statistically significant
        p_value: P-value of the test
        effect_size: Effect size (Cohen's h)
        power_achieved: Achieved power
        
    Returns:
        Recommendation string
    """
    if significant:
        if effect_size > EFFECT_SIZE_LARGE:
            return "Strong evidence of improvement. Recommend immediate rollout with monitoring."
        elif effect_size > EFFECT_SIZE_MEDIUM:
            return "Moderate improvement detected. Recommend gradual rollout with careful monitoring."
        else:
            return "Small but significant improvement. Consider rollout if business impact is meaningful."
    else:
        if power_achieved < MIN_ADEQUATE_POWER:
            return "Insufficient power to detect effect. Consider increasing sample size or extending test duration."
        elif p_value < MARGINAL_SIGNIFICANCE_THRESHOLD:
            return "Marginal significance. Consider extending test or investigating further."
        else:
            return "No significant difference detected. Consider alternative approaches or hypothesis refinement."


def make_rollout_decision(
    sim_result: SimResult, 
    analysis_result: AnalysisResult,
    business_target_absolute: float
) -> str:
    """
    Make rollout decision based on confidence interval vs business target.
    
    Args:
        sim_result: Simulation results with observed lift
        analysis_result: Statistical analysis with CI bounds
        business_target_absolute: Business's target absolute lift (e.g., 0.03 for 3%)
        
    Returns:
        Decision: "proceed_with_confidence", "proceed_with_caution", "do_not_proceed"
    """
    ci_lower, ci_upper = analysis_result.confidence_interval
    
    # Check if business target is achievable within CI
    if ci_upper < business_target_absolute:
        # Upper bound is below target - target not achievable
        return "do_not_proceed"
    elif ci_lower >= business_target_absolute:
        # Lower bound is above target - target is very likely achievable
        return "proceed_with_confidence"
    else:
        # Target is within CI bounds - proceed with caution
        return "proceed_with_caution"


def calculate_business_impact(sim_result: SimResult, 
                            revenue_per_conversion: Optional[float] = None,
                            monthly_traffic: Optional[int] = None) -> BusinessImpact:
    """
    Calculate business impact metrics from simulation results.
    
    Args:
        sim_result: Simulation results
        revenue_per_conversion: Revenue per conversion (optional)
        monthly_traffic: Monthly traffic volume (optional)
        
    Returns:
        BusinessImpact with revenue projections and recommendations
    """
    # Calculate lift metrics
    absolute_lift = sim_result.absolute_lift
    relative_lift_pct = sim_result.relative_lift_pct * 100
    
    # Calculate revenue impact if revenue data provided
    revenue_impact_monthly = None
    confidence_in_revenue = None
    
    if revenue_per_conversion and monthly_traffic:
        # Estimate monthly revenue impact
        baseline_conversions = monthly_traffic * sim_result.control_rate
        additional_conversions = monthly_traffic * absolute_lift
        revenue_impact_monthly = additional_conversions * revenue_per_conversion
        
        # Estimate confidence in revenue (based on statistical significance)
        # This is a simplified heuristic
        confidence_in_revenue = min(0.95, max(0.5, 1 - sim_result.p_value if hasattr(sim_result, 'p_value') else 0.7))
    
    # Determine rollout recommendation
    if absolute_lift > LIFT_THRESHOLD_HIGH_CONFIDENCE:
        rollout_recommendation = "proceed_with_confidence"
        risk_level = "low"
    elif absolute_lift > LIFT_THRESHOLD_MODERATE_CONFIDENCE:
        rollout_recommendation = "proceed_with_caution"
        risk_level = "medium"
    else:
        rollout_recommendation = "do_not_proceed"
        risk_level = "high"
    
    # Determine implementation complexity (simplified)
    implementation_complexity = "low"  # Could be enhanced with more context
    
    return BusinessImpact(
        absolute_lift=absolute_lift,
        relative_lift_pct=relative_lift_pct,
        revenue_impact_monthly=revenue_impact_monthly,
        confidence_in_revenue=confidence_in_revenue,
        rollout_recommendation=rollout_recommendation,
        risk_level=risk_level,
        implementation_complexity=implementation_complexity
    )


def assess_test_quality(sim_result: SimResult, design_params: DesignParams) -> TestQuality:
    """
    Assess the quality of the test design and execution.
    
    Args:
        sim_result: Simulation results
        design_params: Original design parameters
        
    Returns:
        TestQuality with quality indicators
    """
    # Calculate allocation balance
    total_n = sim_result.control_n + sim_result.treatment_n
    allocation_balance = sim_result.control_n / total_n if total_n > 0 else 0.5
    
    # Assess early stopping risk (simplified)
    if sim_result.control_n < EARLY_STOPPING_HIGH_RISK_N or sim_result.treatment_n < EARLY_STOPPING_HIGH_RISK_N:
        early_stopping_risk = "high"
    elif sim_result.control_n < EARLY_STOPPING_MEDIUM_RISK_N or sim_result.treatment_n < EARLY_STOPPING_MEDIUM_RISK_N:
        early_stopping_risk = "medium"
    else:
        early_stopping_risk = "low"

    # Assess novelty effect potential (simplified)
    if design_params.target_lift_pct > NOVELTY_EFFECT_HIGH_THRESHOLD:
        novelty_effect_potential = "high"
    elif design_params.target_lift_pct > NOVELTY_EFFECT_MEDIUM_THRESHOLD:
        novelty_effect_potential = "medium"
    else:
        novelty_effect_potential = "low"
    
    # Assess seasonality impact (simplified)
    seasonality_impact = "none"  # Could be enhanced with date analysis
    
    # Calculate traffic consistency (simplified)
    traffic_consistency = 0.95  # Could be enhanced with actual traffic analysis
    
    # Assess sample size adequacy
    sample_size_adequacy = sim_result.control_n >= EARLY_STOPPING_HIGH_RISK_N and sim_result.treatment_n >= EARLY_STOPPING_HIGH_RISK_N
    
    # Calculate achieved power (simplified)
    power_achieved = 0.8  # Could be calculated more precisely
    
    return TestQuality(
        early_stopping_risk=early_stopping_risk,
        novelty_effect_potential=novelty_effect_potential,
        seasonality_impact=seasonality_impact,
        traffic_consistency=traffic_consistency,
        allocation_balance=allocation_balance,
        sample_size_adequacy=sample_size_adequacy,
        power_achieved=power_achieved
    )
