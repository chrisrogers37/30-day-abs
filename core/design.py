"""
Sample size calculation and test design utilities.

This module contains deterministic mathematical functions for calculating
sample sizes, test durations, and other design parameters.
"""

import math

from .types import DesignParams, SampleSize
from .logging import get_logger

logger = get_logger(__name__)


def compute_sample_size(params: DesignParams) -> SampleSize:
    """
    Calculate required sample size for two-proportion z-test.
    
    Uses the standard formula for comparing two proportions with specified
    power and significance level.
    
    Args:
        params: Design parameters including baseline rate, target lift, alpha, power
        
    Returns:
        SampleSize object with per-arm sample size, total, and days required
        
    Raises:
        ValueError: If parameters are invalid for sample size calculation
    """
    # Extract parameters
    p1 = params.baseline_conversion_rate
    p2 = p1 * (1 + params.target_lift_pct)
    alpha = params.alpha
    power = params.power
    allocation = params.allocation
    
    # Validate that treatment rate is reasonable
    if p2 <= 0 or p2 >= 1:
        raise ValueError(f"Calculated treatment rate {p2:.4f} is outside valid range [0, 1]")
    
    # Calculate z-scores
    z_alpha = _get_z_score(alpha, "two_tailed")
    z_beta = _get_z_score(1 - power, "one_tailed")
    
    # Calculate required sample size per arm using standard formula
    # Standard formula: n = (z_alpha + z_beta)^2 * [p1(1-p1) + p2(1-p2)] / (p2-p1)^2
    numerator = (z_alpha + z_beta) ** 2 * (p1 * (1 - p1) + p2 * (1 - p2))
    denominator = (p2 - p1) ** 2
    
    n_per_arm = math.ceil(numerator / denominator)
    
    # Calculate total sample size
    total_n = 2 * n_per_arm
    
    # Calculate days required based on daily traffic and allocation
    daily_traffic_per_arm = params.expected_daily_traffic * allocation.control
    days_required = math.ceil(n_per_arm / daily_traffic_per_arm)
    
    # Calculate achieved power (may be slightly higher than target due to rounding)
    achieved_power = _calculate_achieved_power(p1, p2, n_per_arm, alpha, "two_tailed")
    
    return SampleSize(
        per_arm=n_per_arm,
        total=total_n,
        days_required=days_required,
        power_achieved=achieved_power
    )


def _get_z_score(alpha: float, direction: str) -> float:
    """
    Get z-score for given alpha level and test direction.
    
    Args:
        alpha: Significance level
        direction: One-tailed or two-tailed test
        
    Returns:
        Z-score corresponding to the alpha level
    """
    if direction == "two_tailed":
        alpha = alpha / 2
    
    # Use inverse normal approximation
    # For common alpha values, use exact values
    if abs(alpha - 0.05) < 1e-6:
        z_score = 1.96 if direction == "two_tailed" else 1.645
    elif abs(alpha - 0.01) < 1e-6:
        z_score = 2.576 if direction == "two_tailed" else 2.326
    elif abs(alpha - 0.1) < 1e-6:
        z_score = 1.645 if direction == "two_tailed" else 1.282
    else:
        # For other values, use scipy.stats.norm.ppf
        try:
            from scipy.stats import norm
            z_score = norm.ppf(1 - alpha)
        except ImportError:
            # Fallback approximation if scipy not available
            # Simple approximation for common values
            if alpha < 0.01:
                z_score = 2.576
            elif alpha < 0.05:
                z_score = 1.96
            elif alpha < 0.1:
                z_score = 1.645
            else:
                z_score = 1.282
    
    # Log z-score calculation for debugging
    logger.debug(f"Z-score calculation: alpha={alpha:.6f}, direction={direction}, z_score={z_score:.6f}")
    
    return z_score


def _calculate_achieved_power(p1: float, p2: float, n: int, alpha: float, 
                            direction: str) -> float:
    """
    Calculate the achieved power for given sample size.
    
    Args:
        p1: Control group proportion
        p2: Treatment group proportion
        n: Sample size per group
        alpha: Significance level
        direction: Test direction
        
    Returns:
        Achieved power (probability of detecting the effect)
    """
    # Calculate standard error
    se = math.sqrt(p1 * (1 - p1) / n + p2 * (1 - p2) / n)

    # Calculate critical z-score
    z_alpha = _get_z_score(alpha, direction)

    # Calculate z-score for the effect
    effect_size = abs(p2 - p1)
    z_effect = effect_size / se
    
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
    # Simple approximation using error function
    import math
    return 0.5 * (1 + math.erf(z / math.sqrt(2)))


def calculate_minimum_detectable_effect(p1: float, n: int, alpha: float, 
                                     power: float, direction: str) -> float:
    """
    Calculate the minimum detectable effect for given sample size and power.
    
    Args:
        p1: Baseline proportion
        n: Sample size per group
        alpha: Significance level
        power: Desired power
        direction: Test direction
        
    Returns:
        Minimum detectable effect as absolute difference
    """
    z_alpha = _get_z_score(alpha, direction)
    z_beta = _get_z_score(1 - power, "one_tailed")
    
    # Standard error for equal sample sizes
    se = math.sqrt(2 * p1 * (1 - p1) / n)
    
    # Minimum detectable effect
    mde = (z_alpha + z_beta) * se
    
    return mde


def validate_test_duration(params: DesignParams, sample_size: SampleSize) -> bool:
    """
    Validate that the test duration meets business constraints.
    
    Args:
        params: Design parameters with duration constraints
        sample_size: Calculated sample size
        
    Returns:
        True if duration constraints are met, False otherwise
    """
    days_required = sample_size.days_required
    
    # Check minimum duration constraint
    if params.min_test_duration_days and days_required < params.min_test_duration_days:
        return False
    
    # Check maximum duration constraint
    if params.max_test_duration_days and days_required > params.max_test_duration_days:
        return False
    
    return True


def suggest_parameter_adjustments(params: DesignParams, sample_size: SampleSize) -> dict:
    """
    Suggest parameter adjustments if constraints are not met.
    
    Args:
        params: Original design parameters
        sample_size: Calculated sample size
        
    Returns:
        Dictionary with suggested adjustments
    """
    suggestions = {}
    
    # Check duration constraints
    if params.max_test_duration_days and sample_size.days_required > params.max_test_duration_days:
        # Suggest increasing traffic or reducing power
        required_traffic = sample_size.per_arm / params.max_test_duration_days / params.allocation.control
        suggestions["increase_traffic"] = {
            "current": params.expected_daily_traffic,
            "required": math.ceil(required_traffic),
            "reason": "To meet maximum duration constraint"
        }
        
        # Alternative: reduce power
        suggestions["reduce_power"] = {
            "current": params.power,
            "suggested": max(0.7, params.power - 0.1),
            "reason": "To reduce sample size requirements"
        }
    
    # Check if power is too low
    if sample_size.power_achieved < 0.8:
        suggestions["increase_power"] = {
            "current": sample_size.power_achieved,
            "suggested": 0.8,
            "reason": "To achieve adequate statistical power"
        }
    
    return suggestions
