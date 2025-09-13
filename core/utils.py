"""
Utility functions for AB test simulator.

This module contains common helper functions for conversions, business impact
calculations, and evaluation scoring.
"""

import math
from typing import Dict, List, Optional, Tuple, Union

from .design import _get_z_score


def relative_lift_to_absolute(control_rate: float, relative_lift_pct: float) -> float:
    """
    Convert relative lift percentage to absolute difference.
    
    Args:
        control_rate: Baseline conversion rate
        relative_lift_pct: Relative lift as percentage (e.g., 15 for 15%)
        
    Returns:
        Absolute difference in conversion rates
    """
    return control_rate * (relative_lift_pct / 100)


def absolute_lift_to_relative(control_rate: float, absolute_lift: float) -> float:
    """
    Convert absolute difference to relative lift percentage.
    
    Args:
        control_rate: Baseline conversion rate
        absolute_lift: Absolute difference in conversion rates
        
    Returns:
        Relative lift as percentage
    """
    if control_rate == 0:
        return 0.0
    return (absolute_lift / control_rate) * 100


def calculate_revenue_impact(conversion_rate: float, traffic_volume: int, 
                           revenue_per_conversion: float) -> float:
    """
    Calculate revenue impact from conversion rate improvement.
    
    Args:
        conversion_rate: Conversion rate
        traffic_volume: Traffic volume
        revenue_per_conversion: Revenue per conversion
        
    Returns:
        Total revenue impact
    """
    return conversion_rate * traffic_volume * revenue_per_conversion


def calculate_monthly_revenue_impact(conversion_rate: float, daily_traffic: int,
                                   revenue_per_conversion: float, 
                                   days_per_month: int = 30) -> float:
    """
    Calculate monthly revenue impact from conversion rate improvement.
    
    Args:
        conversion_rate: Conversion rate
        daily_traffic: Daily traffic volume
        revenue_per_conversion: Revenue per conversion
        days_per_month: Number of days per month
        
    Returns:
        Monthly revenue impact
    """
    monthly_traffic = daily_traffic * days_per_month
    return calculate_revenue_impact(conversion_rate, monthly_traffic, revenue_per_conversion)


def calculate_confidence_interval_for_revenue(revenue_impact: float, 
                                            confidence_level: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for revenue impact (simplified).
    
    Args:
        revenue_impact: Point estimate of revenue impact
        confidence_level: Confidence level (e.g., 0.95 for 95%)
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    # Simplified calculation - in practice, this would use the CI for the conversion rate
    margin_of_error = revenue_impact * (1 - confidence_level)
    return (revenue_impact - margin_of_error, revenue_impact + margin_of_error)


def calculate_sample_size_for_revenue_detection(min_revenue_impact: float,
                                              daily_traffic: int,
                                              revenue_per_conversion: float,
                                              baseline_conversion_rate: float,
                                              alpha: float = 0.05,
                                              power: float = 0.8) -> int:
    """
    Calculate sample size needed to detect minimum revenue impact.
    
    Args:
        min_revenue_impact: Minimum revenue impact to detect
        daily_traffic: Daily traffic volume
        revenue_per_conversion: Revenue per conversion
        baseline_conversion_rate: Baseline conversion rate
        
    Returns:
        Required sample size per group
    """
    # Convert revenue impact to conversion rate difference
    min_conversion_impact = min_revenue_impact / (daily_traffic * revenue_per_conversion)
    
    # Use standard sample size formula for proportions
    p1 = baseline_conversion_rate
    p2 = p1 + min_conversion_impact
    
    # Calculate z-scores
    z_alpha = _get_z_score(alpha, "two_tailed")
    z_beta = _get_z_score(1 - power, "two_tailed")
    
    # Calculate pooled proportion
    p_pooled = (p1 + p2) / 2
    
    # Calculate sample size
    numerator = (z_alpha * math.sqrt(2 * p_pooled * (1 - p_pooled)) + 
                z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denominator = (p2 - p1) ** 2
    
    return math.ceil(numerator / denominator)


def calculate_effect_size_cohens_h(p1: float, p2: float) -> float:
    """
    Calculate Cohen's h effect size for proportions.
    
    Args:
        p1: First proportion
        p2: Second proportion
        
    Returns:
        Cohen's h effect size
    """
    # Convert proportions to angles
    theta1 = 2 * math.asin(math.sqrt(p1))
    theta2 = 2 * math.asin(math.sqrt(p2))
    
    # Calculate Cohen's h
    h = theta2 - theta1
    
    return h


def interpret_effect_size_cohens_h(h: float) -> str:
    """
    Interpret Cohen's h effect size.
    
    Args:
        h: Cohen's h value
        
    Returns:
        Interpretation string
    """
    abs_h = abs(h)
    
    if abs_h < 0.2:
        return "small"
    elif abs_h < 0.5:
        return "medium"
    else:
        return "large"


def calculate_effect_size_cohens_d(mean1: float, mean2: float, 
                                  pooled_std: float) -> float:
    """
    Calculate Cohen's d effect size for means.
    
    Args:
        mean1: First mean
        mean2: Second mean
        pooled_std: Pooled standard deviation
        
    Returns:
        Cohen's d effect size
    """
    if pooled_std == 0:
        return 0.0
    
    return (mean2 - mean1) / pooled_std


def interpret_effect_size_cohens_d(d: float) -> str:
    """
    Interpret Cohen's d effect size.
    
    Args:
        d: Cohen's d value
        
    Returns:
        Interpretation string
    """
    abs_d = abs(d)
    
    if abs_d < 0.2:
        return "small"
    elif abs_d < 0.5:
        return "medium"
    elif abs_d < 0.8:
        return "large"
    else:
        return "very large"


def calculate_confidence_interval_for_proportion(p: float, n: int, 
                                               confidence_level: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for a proportion.
    
    Args:
        p: Sample proportion
        n: Sample size
        confidence_level: Confidence level
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n == 0:
        return (0.0, 0.0)
    
    # Calculate standard error
    se = math.sqrt(p * (1 - p) / n)
    
    # Calculate z-score for confidence level
    alpha = 1 - confidence_level
    z_score = _get_z_score(alpha, "two_tailed")
    
    # Calculate margin of error
    margin_of_error = z_score * se
    
    # Calculate bounds
    lower_bound = max(0, p - margin_of_error)
    upper_bound = min(1, p + margin_of_error)
    
    return (lower_bound, upper_bound)


def calculate_confidence_interval_for_difference(p1: float, p2: float, 
                                               n1: int, n2: int,
                                               confidence_level: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for difference in proportions.
    
    Args:
        p1: First proportion
        p2: Second proportion
        n1: First sample size
        n2: Second sample size
        confidence_level: Confidence level
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    if n1 == 0 or n2 == 0:
        return (0.0, 0.0)
    
    # Calculate standard error for difference
    se = math.sqrt(p1 * (1 - p1) / n1 + p2 * (1 - p2) / n2)
    
    # Calculate z-score for confidence level
    alpha = 1 - confidence_level
    z_score = _get_z_score(alpha, "two_tailed")
    
    # Calculate margin of error
    margin_of_error = z_score * se
    
    # Calculate difference
    diff = p2 - p1
    
    # Calculate bounds
    lower_bound = diff - margin_of_error
    upper_bound = diff + margin_of_error
    
    return (lower_bound, upper_bound)


def calculate_power_for_proportions(p1: float, p2: float, n: int, 
                                  alpha: float = 0.05) -> float:
    """
    Calculate statistical power for comparing two proportions.
    
    Args:
        p1: First proportion
        p2: Second proportion
        n: Sample size per group
        alpha: Significance level
        
    Returns:
        Statistical power
    """
    # Calculate standard error
    se = math.sqrt(p1 * (1 - p1) / n + p2 * (1 - p2) / n)
    
    # Calculate critical value
    z_alpha = _get_z_score(alpha, "two_tailed")
    
    # Calculate z-score for the effect
    effect_size = abs(p2 - p1)
    z_effect = effect_size / se if se > 0 else 0
    
    # Calculate power
    power = 1 - _normal_cdf(z_alpha - z_effect)
    
    return min(max(power, 0.0), 1.0)


def _normal_cdf(z: float) -> float:
    """
    Approximate cumulative distribution function for standard normal distribution.
    
    Args:
        z: Z-score
        
    Returns:
        Cumulative probability
    """
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def calculate_minimum_detectable_effect(p1: float, n: int, alpha: float = 0.05, 
                                      power: float = 0.8) -> float:
    """
    Calculate minimum detectable effect for given sample size and power.
    
    Args:
        p1: Baseline proportion
        n: Sample size per group
        alpha: Significance level
        power: Desired power
        
    Returns:
        Minimum detectable effect as absolute difference
    """
    z_alpha = _get_z_score(alpha, "two_tailed")
    z_beta = _get_z_score(1 - power, "two_tailed")
    
    # Standard error for equal sample sizes
    se = math.sqrt(2 * p1 * (1 - p1) / n)
    
    # Minimum detectable effect
    mde = (z_alpha + z_beta) * se
    
    return mde


def calculate_required_sample_size_for_power(p1: float, p2: float, 
                                           alpha: float = 0.05, 
                                           power: float = 0.8) -> int:
    """
    Calculate required sample size for given power.
    
    Args:
        p1: First proportion
        p2: Second proportion
        alpha: Significance level
        power: Desired power
        
    Returns:
        Required sample size per group
    """
    z_alpha = _get_z_score(alpha, "two_tailed")
    z_beta = _get_z_score(1 - power, "two_tailed")
    
    # Calculate pooled proportion
    p_pooled = (p1 + p2) / 2
    
    # Calculate sample size
    numerator = (z_alpha * math.sqrt(2 * p_pooled * (1 - p_pooled)) + 
                z_beta * math.sqrt(p1 * (1 - p1) + p2 * (1 - p2))) ** 2
    denominator = (p2 - p1) ** 2
    
    return math.ceil(numerator / denominator)


def format_percentage(value: float, decimals: int = 2) -> str:
    """
    Format a decimal as a percentage string.
    
    Args:
        value: Decimal value (e.g., 0.15 for 15%)
        decimals: Number of decimal places
        
    Returns:
        Formatted percentage string
    """
    return f"{value * 100:.{decimals}f}%"


def format_currency(value: float, currency: str = "$") -> str:
    """
    Format a number as currency.
    
    Args:
        value: Numeric value
        currency: Currency symbol
        
    Returns:
        Formatted currency string
    """
    if abs(value) >= 1e6:
        return f"{currency}{value/1e6:.1f}M"
    elif abs(value) >= 1e3:
        return f"{currency}{value/1e3:.1f}K"
    else:
        return f"{currency}{value:.2f}"


def format_large_number(value: int) -> str:
    """
    Format a large number with appropriate suffixes.
    
    Args:
        value: Numeric value
        
    Returns:
        Formatted number string
    """
    if value >= 1e9:
        return f"{value/1e9:.1f}B"
    elif value >= 1e6:
        return f"{value/1e6:.1f}M"
    elif value >= 1e3:
        return f"{value/1e3:.1f}K"
    else:
        return str(value)


def calculate_conversion_rate_standard_error(p: float, n: int) -> float:
    """
    Calculate standard error for a conversion rate.
    
    Args:
        p: Sample proportion
        n: Sample size
        
    Returns:
        Standard error
    """
    if n == 0:
        return 0.0
    
    return math.sqrt(p * (1 - p) / n)


def calculate_conversion_rate_confidence_interval(p: float, n: int, 
                                                confidence_level: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for a conversion rate.
    
    Args:
        p: Sample proportion
        n: Sample size
        confidence_level: Confidence level
        
    Returns:
        Tuple of (lower_bound, upper_bound)
    """
    se = calculate_conversion_rate_standard_error(p, n)
    
    # Calculate z-score for confidence level
    alpha = 1 - confidence_level
    z_score = _get_z_score(alpha, "two_tailed")
    
    # Calculate margin of error
    margin_of_error = z_score * se
    
    # Calculate bounds
    lower_bound = max(0, p - margin_of_error)
    upper_bound = min(1, p + margin_of_error)
    
    return (lower_bound, upper_bound)


def calculate_relative_lift_confidence_interval(control_rate: float, treatment_rate: float,
                                              control_n: int, treatment_n: int,
                                              confidence_level: float = 0.95) -> Tuple[float, float]:
    """
    Calculate confidence interval for relative lift.
    
    Args:
        control_rate: Control group conversion rate
        treatment_rate: Treatment group conversion rate
        control_n: Control group sample size
        treatment_n: Treatment group sample size
        confidence_level: Confidence level
        
    Returns:
        Tuple of (lower_bound, upper_bound) for relative lift
    """
    if control_rate == 0:
        return (0.0, 0.0)
    
    # Calculate confidence interval for difference
    diff_lower, diff_upper = calculate_confidence_interval_for_difference(
        control_rate, treatment_rate, control_n, treatment_n, confidence_level
    )
    
    # Convert to relative lift
    relative_lift_lower = (diff_lower / control_rate) * 100
    relative_lift_upper = (diff_upper / control_rate) * 100
    
    return (relative_lift_lower, relative_lift_upper)


def validate_conversion_rate(rate: float) -> bool:
    """
    Validate that a conversion rate is within valid bounds.
    
    Args:
        rate: Conversion rate to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 0 <= rate <= 1


def validate_sample_size(n: int) -> bool:
    """
    Validate that a sample size is positive.
    
    Args:
        n: Sample size to validate
        
    Returns:
        True if valid, False otherwise
    """
    return n > 0


def validate_confidence_level(level: float) -> bool:
    """
    Validate that a confidence level is within valid bounds.
    
    Args:
        level: Confidence level to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 0 < level < 1


def validate_significance_level(alpha: float) -> bool:
    """
    Validate that a significance level is within valid bounds.
    
    Args:
        alpha: Significance level to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 0 < alpha < 1


def validate_power(power: float) -> bool:
    """
    Validate that a power level is within valid bounds.
    
    Args:
        power: Power level to validate
        
    Returns:
        True if valid, False otherwise
    """
    return 0 < power < 1
