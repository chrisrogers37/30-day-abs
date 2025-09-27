"""
Statistical analysis and answer key generation.

This module performs comprehensive statistical analysis on simulated data
and generates detailed answer keys for user evaluation.
"""

import math
from typing import Dict, Tuple, Optional

from .types import SimResult, AnalysisResult, BusinessImpact, TestQuality, DesignParams
from .design import _get_z_score


def analyze_results(sim_result: SimResult, alpha: float = 0.05, 
                   test_type: str = "two_proportion_z",
                   test_direction: str = "two_tailed") -> AnalysisResult:
    """
    Perform comprehensive statistical analysis on simulation results.
    
    Args:
        sim_result: Simulation results with conversion counts
        alpha: Significance level
        test_type: Type of statistical test to perform
        test_direction: One-tailed or two-tailed test
        
    Returns:
        AnalysisResult with test statistics, p-value, CI, and recommendation
    """
    if test_type == "two_proportion_z":
        return _two_proportion_z_test(sim_result, alpha, test_direction)
    elif test_type == "chi_square":
        return _chi_square_test(sim_result, alpha)
    elif test_type == "fisher_exact":
        return _fisher_exact_test(sim_result, alpha)
    else:
        raise ValueError(f"Unsupported test type: {test_type}")


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
    
    # Calculate confidence interval for difference
    ci_lower, ci_upper = _calculate_confidence_interval(p1, p2, n1, n2, alpha)
    
    # Determine significance
    significant = p_value < alpha
    
    # Calculate effect size (Cohen's h)
    effect_size = _calculate_effect_size(p1, p2)
    
    # Calculate achieved power
    power_achieved = _calculate_achieved_power(p1, p2, n1, n2, alpha, direction)
    
    # Generate recommendation
    recommendation = _generate_recommendation(significant, p_value, effect_size, power_achieved)
    
    return AnalysisResult(
        test_statistic=z_statistic,
        p_value=p_value,
        confidence_interval=(ci_lower, ci_upper),
        confidence_level=1 - alpha,
        significant=significant,
        effect_size=effect_size,
        power_achieved=power_achieved,
        recommendation=recommendation
    )


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
    
    # Calculate confidence interval for difference
    p1 = x1 / n1 if n1 > 0 else 0
    p2 = x2 / n2 if n2 > 0 else 0
    ci_lower, ci_upper = _calculate_confidence_interval(p1, p2, n1, n2, alpha)
    
    # Determine significance
    significant = p_value < alpha
    
    # Calculate effect size (Cramér's V)
    effect_size = math.sqrt(chi_square / total_users)
    
    # Calculate achieved power
    power_achieved = _calculate_achieved_power(p1, p2, n1, n2, alpha, "two_tailed")
    
    # Generate recommendation
    recommendation = _generate_recommendation(significant, p_value, effect_size, power_achieved)
    
    return AnalysisResult(
        test_statistic=chi_square,
        p_value=p_value,
        confidence_interval=(ci_lower, ci_upper),
        confidence_level=1 - alpha,
        significant=significant,
        effect_size=effect_size,
        power_achieved=power_achieved,
        recommendation=recommendation
    )


def _fisher_exact_test(sim_result: SimResult, alpha: float) -> AnalysisResult:
    """
    Perform Fisher's exact test (simplified implementation).
    
    Args:
        sim_result: Simulation results
        alpha: Significance level
        
    Returns:
        AnalysisResult with Fisher's exact test results
    """
    # For large samples, approximate with chi-square
    if sim_result.control_n + sim_result.treatment_n > 100:
        return _chi_square_test(sim_result, alpha)
    
    # Simplified Fisher's exact test implementation
    # In production, use scipy.stats.fisher_exact
    n1, x1 = sim_result.control_n, sim_result.control_conversions
    n2, x2 = sim_result.treatment_n, sim_result.treatment_conversions
    
    # Calculate p-value using hypergeometric distribution approximation
    p_value = _fisher_exact_p_value(x1, n1, x2, n2)
    
    # Calculate confidence interval
    p1 = x1 / n1 if n1 > 0 else 0
    p2 = x2 / n2 if n2 > 0 else 0
    ci_lower, ci_upper = _calculate_confidence_interval(p1, p2, n1, n2, alpha)
    
    # Determine significance
    significant = p_value < alpha
    
    # Calculate effect size
    effect_size = _calculate_effect_size(p1, p2)
    
    # Calculate achieved power
    power_achieved = _calculate_achieved_power(p1, p2, n1, n2, alpha, "two_tailed")
    
    # Generate recommendation
    recommendation = _generate_recommendation(significant, p_value, effect_size, power_achieved)
    
    return AnalysisResult(
        test_statistic=0.0,  # Fisher's exact doesn't have a traditional test statistic
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
    p_value = 2 * (1 - _normal_cdf(abs(z_statistic)))
    
    if direction == "one_tailed":
        p_value = p_value / 2
    
    return min(max(p_value, 0.0), 1.0)


def _normal_cdf(z: float) -> float:
    """
    Approximate cumulative distribution function for standard normal distribution.
    
    Args:
        z: Z-score
        
    Returns:
        Cumulative probability
    """
    # Simple approximation using error function
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def _calculate_confidence_interval(p1: float, p2: float, n1: int, n2: int, 
                                 alpha: float) -> Tuple[float, float]:
    """
    Calculate confidence interval for difference in proportions.
    
    Args:
        p1: Control group proportion
        p2: Treatment group proportion
        n1: Control group sample size
        n2: Treatment group sample size
        alpha: Significance level
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    # Calculate standard error for difference
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    
    # Calculate margin of error
    z_alpha_2 = _get_z_score(alpha, "two_tailed")
    margin_of_error = z_alpha_2 * se
    
    # Calculate difference
    diff = p2 - p1
    
    # Calculate bounds
    lower_bound = diff - margin_of_error
    upper_bound = diff + margin_of_error
    
    return (lower_bound, upper_bound)


def _calculate_effect_size(p1: float, p2: float) -> float:
    """
    Calculate Cohen's h effect size for proportions.
    
    Args:
        p1: Control group proportion
        p2: Treatment group proportion
        
    Returns:
        Effect size (Cohen's h)
    """
    # Convert proportions to angles
    theta1 = 2 * math.asin(math.sqrt(p1))
    theta2 = 2 * math.asin(math.sqrt(p2))
    
    # Calculate Cohen's h
    h = theta2 - theta1
    
    return h


def _calculate_achieved_power(p1: float, p2: float, n1: int, n2: int,
                            alpha: float, direction: str) -> float:
    """
    Calculate achieved power for the test.
    
    Args:
        p1: Control group proportion
        p2: Treatment group proportion
        n1: Control group sample size
        n2: Treatment group sample size
        alpha: Significance level
        direction: Test direction
        
    Returns:
        Achieved power
    """
    # Calculate standard error
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    
    # Calculate critical value
    z_alpha = _get_z_score(alpha, direction)
    critical_value = z_alpha * se
    
    # Calculate z-score for the effect
    effect_size = abs(p2 - p1)
    z_effect = effect_size / se if se > 0 else 0
    
    # Calculate power
    power = 1 - _normal_cdf(z_alpha - z_effect)
    
    return min(max(power, 0.0), 1.0)


def _chi_square_p_value(chi_square: float, df: int) -> float:
    """
    Approximate p-value for chi-square statistic.
    
    Args:
        chi_square: Chi-square statistic
        df: Degrees of freedom
        
    Returns:
        P-value
    """
    # Simplified approximation for df=1
    if df == 1:
        # For df=1, chi-square is approximately z^2
        z = math.sqrt(chi_square)
        return 2 * (1 - _normal_cdf(z))
    
    # For other df, use approximation
    return 1 - _chi_square_cdf(chi_square, df)


def _chi_square_cdf(chi_square: float, df: int) -> float:
    """
    Approximate CDF for chi-square distribution.
    
    Args:
        chi_square: Chi-square statistic
        df: Degrees of freedom
        
    Returns:
        Cumulative probability
    """
    # Simplified approximation
    if df == 1:
        return _normal_cdf(math.sqrt(chi_square))
    
    # For df > 1, use approximation
    return 1 - math.exp(-chi_square / 2)


def _fisher_exact_p_value(x1: int, n1: int, x2: int, n2: int) -> float:
    """
    Approximate p-value for Fisher's exact test.
    
    Args:
        x1: Control group conversions
        n1: Control group sample size
        x2: Treatment group conversions
        n2: Treatment group sample size
        
    Returns:
        P-value
    """
    # Simplified implementation - in production use scipy.stats.fisher_exact
    # This is a rough approximation
    p1 = x1 / n1 if n1 > 0 else 0
    p2 = x2 / n2 if n2 > 0 else 0
    
    # Use chi-square approximation for simplicity
    return _chi_square_p_value(
        (x1 - n1 * p1) ** 2 / (n1 * p1 * (1 - p1)) + 
        (x2 - n2 * p2) ** 2 / (n2 * p2 * (1 - p2)), 
        df=1
    )


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
        if effect_size > 0.2:  # Large effect
            return "Strong evidence of improvement. Recommend immediate rollout with monitoring."
        elif effect_size > 0.1:  # Medium effect
            return "Moderate improvement detected. Recommend gradual rollout with careful monitoring."
        else:  # Small effect
            return "Small but significant improvement. Consider rollout if business impact is meaningful."
    else:
        if power_achieved < 0.8:
            return "Insufficient power to detect effect. Consider increasing sample size or extending test duration."
        elif p_value < 0.1:
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
    if absolute_lift > 0.01:  # 1% absolute lift
        rollout_recommendation = "proceed_with_confidence"
        risk_level = "low"
    elif absolute_lift > 0.005:  # 0.5% absolute lift
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
    if sim_result.control_n < 1000 or sim_result.treatment_n < 1000:
        early_stopping_risk = "high"
    elif sim_result.control_n < 5000 or sim_result.treatment_n < 5000:
        early_stopping_risk = "medium"
    else:
        early_stopping_risk = "low"
    
    # Assess novelty effect potential (simplified)
    if design_params.target_lift_pct > 0.2:  # 20% lift
        novelty_effect_potential = "high"
    elif design_params.target_lift_pct > 0.1:  # 10% lift
        novelty_effect_potential = "medium"
    else:
        novelty_effect_potential = "low"
    
    # Assess seasonality impact (simplified)
    seasonality_impact = "none"  # Could be enhanced with date analysis
    
    # Calculate traffic consistency (simplified)
    traffic_consistency = 0.95  # Could be enhanced with actual traffic analysis
    
    # Assess sample size adequacy
    sample_size_adequacy = sim_result.control_n >= 1000 and sim_result.treatment_n >= 1000
    
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
