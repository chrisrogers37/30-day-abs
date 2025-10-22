"""
Expected calculation results for testing.

This module contains expected results for various statistical calculations
to validate the correctness of the core mathematical functions.
"""

from typing import Dict, Any, Tuple
import math


# ============================================================================
# Sample Size Calculation Expected Results
# ============================================================================

EXPECTED_SAMPLE_SIZES: Dict[str, Dict[str, Any]] = {
    "standard_case": {
        "params": {
            "baseline": 0.05,
            "lift": 0.15,
            "alpha": 0.05,
            "power": 0.80,
        },
        "expected_per_arm": 6140,  # Approximate
        "expected_total": 12280,
        "tolerance_per_arm": 200,
        "days_with_10k_traffic": 2,
    },
    
    "high_power": {
        "params": {
            "baseline": 0.05,
            "lift": 0.15,
            "alpha": 0.05,
            "power": 0.90,
        },
        "expected_per_arm": 8200,  # Approximate
        "expected_total": 16400,
        "tolerance_per_arm": 250,
        "days_with_10k_traffic": 2,
    },
    
    "small_lift": {
        "params": {
            "baseline": 0.05,
            "lift": 0.10,
            "alpha": 0.05,
            "power": 0.80,
        },
        "expected_per_arm": 13800,  # Approximate
        "expected_total": 27600,
        "tolerance_per_arm": 400,
        "days_with_10k_traffic": 3,
    },
    
    "high_baseline": {
        "params": {
            "baseline": 0.25,
            "lift": 0.15,
            "alpha": 0.05,
            "power": 0.80,
        },
        "expected_per_arm": 2850,  # Approximate
        "expected_total": 5700,
        "tolerance_per_arm": 150,
        "days_with_10k_traffic": 2,
    },
    
    "low_alpha": {
        "params": {
            "baseline": 0.05,
            "lift": 0.15,
            "alpha": 0.01,
            "power": 0.80,
        },
        "expected_per_arm": 9500,  # Approximate
        "expected_total": 19000,
        "tolerance_per_arm": 300,
        "days_with_10k_traffic": 2,
    },
}


# ============================================================================
# Statistical Analysis Expected Results
# ============================================================================

EXPECTED_ANALYSIS_RESULTS: Dict[str, Dict[str, Any]] = {
    "significant_positive": {
        "sim_data": {
            "control_n": 5000,
            "control_conversions": 250,
            "treatment_n": 5000,
            "treatment_conversions": 325,
        },
        "expected": {
            "control_rate": 0.05,
            "treatment_rate": 0.065,
            "absolute_lift": 0.015,
            "relative_lift_pct": 0.30,
            "p_value_max": 0.01,  # Should be < 0.01
            "significant": True,
            "ci_excludes_zero": True,
        }
    },
    
    "non_significant": {
        "sim_data": {
            "control_n": 500,
            "control_conversions": 25,
            "treatment_n": 500,
            "treatment_conversions": 27,
        },
        "expected": {
            "control_rate": 0.05,
            "treatment_rate": 0.054,
            "absolute_lift": 0.004,
            "relative_lift_pct": 0.08,
            "p_value_min": 0.05,  # Should be > 0.05
            "significant": False,
            "ci_includes_zero": True,
        }
    },
    
    "significant_negative": {
        "sim_data": {
            "control_n": 3000,
            "control_conversions": 180,
            "treatment_n": 3000,
            "treatment_conversions": 135,
        },
        "expected": {
            "control_rate": 0.06,
            "treatment_rate": 0.045,
            "absolute_lift": -0.015,
            "relative_lift_pct": -0.25,
            "p_value_max": 0.01,
            "significant": True,
            "ci_excludes_zero": True,
        }
    },
}


# ============================================================================
# Confidence Interval Expected Results
# ============================================================================

EXPECTED_CONFIDENCE_INTERVALS: Dict[str, Dict[str, Any]] = {
    "95_percent": {
        "alpha": 0.05,
        "z_score": 1.96,
        "example": {
            "control_n": 1000,
            "control_conversions": 50,
            "treatment_n": 1000,
            "treatment_conversions": 70,
            "expected_ci_width_approx": 0.03,
        }
    },
    
    "99_percent": {
        "alpha": 0.01,
        "z_score": 2.576,
        "example": {
            "control_n": 1000,
            "control_conversions": 50,
            "treatment_n": 1000,
            "treatment_conversions": 70,
            "expected_ci_width_approx": 0.04,
        }
    },
}


# ============================================================================
# Effect Size Expected Results
# ============================================================================

EXPECTED_EFFECT_SIZES: Dict[str, Dict[str, Any]] = {
    "small_effect": {
        "control_rate": 0.10,
        "treatment_rate": 0.105,
        "cohens_h": 0.017,  # Small effect
        "interpretation": "small",
    },
    
    "medium_effect": {
        "control_rate": 0.10,
        "treatment_rate": 0.125,
        "cohens_h": 0.082,  # Medium effect
        "interpretation": "medium",
    },
    
    "large_effect": {
        "control_rate": 0.10,
        "treatment_rate": 0.15,
        "cohens_h": 0.164,  # Large effect
        "interpretation": "large",
    },
}


# ============================================================================
# Rollout Decision Expected Results
# ============================================================================

EXPECTED_ROLLOUT_DECISIONS: Dict[str, Dict[str, Any]] = {
    "proceed_with_confidence": {
        "ci_lower": 0.02,
        "ci_upper": 0.04,
        "business_target": 0.01,
        "expected_decision": "proceed_with_confidence",
        "rationale": "Lower bound exceeds business target"
    },
    
    "proceed_with_caution": {
        "ci_lower": 0.005,
        "ci_upper": 0.025,
        "business_target": 0.01,
        "expected_decision": "proceed_with_caution",
        "rationale": "CI includes business target but upper bound exceeds it"
    },
    
    "do_not_proceed": {
        "ci_lower": -0.01,
        "ci_upper": 0.015,
        "business_target": 0.02,
        "expected_decision": "do_not_proceed",
        "rationale": "Upper bound below business target"
    },
}


# ============================================================================
# Validation Tolerance Expected Results
# ============================================================================

EXPECTED_VALIDATION_RESULTS: Dict[str, Dict[str, Any]] = {
    "within_tolerance": {
        "correct_answer": 100,
        "user_answer": 102,
        "tolerance_percentage": 0.05,  # 5%
        "should_pass": True,
    },
    
    "outside_tolerance": {
        "correct_answer": 100,
        "user_answer": 110,
        "tolerance_percentage": 0.05,  # 5%
        "should_pass": False,
    },
    
    "exact_match": {
        "correct_answer": 100,
        "user_answer": 100,
        "tolerance_percentage": 0.0,
        "should_pass": True,
    },
}


# ============================================================================
# Helper Functions
# ============================================================================

def calculate_expected_z_score(alpha: float, two_tailed: bool = True) -> float:
    """
    Calculate expected z-score for given alpha.
    
    Args:
        alpha: Significance level
        two_tailed: Whether test is two-tailed
    
    Returns:
        Expected z-score
    """
    if two_tailed:
        alpha = alpha / 2
    
    z_scores = {
        0.005: 2.576,  # 99% CI (two-tailed)
        0.01: 2.326,   # 98% CI (two-tailed)
        0.025: 1.96,   # 95% CI (two-tailed)
        0.05: 1.645,   # 90% CI (two-tailed)
    }
    
    return z_scores.get(alpha, 1.96)


def is_within_tolerance(
    expected: float,
    actual: float,
    tolerance_pct: float = 0.05,
    tolerance_abs: float = 0.001
) -> bool:
    """
    Check if actual value is within tolerance of expected value.
    
    Args:
        expected: Expected value
        actual: Actual value
        tolerance_pct: Percentage tolerance (0.05 = 5%)
        tolerance_abs: Absolute tolerance
    
    Returns:
        True if within tolerance
    """
    if expected == 0:
        return abs(actual - expected) <= tolerance_abs
    
    pct_diff = abs((actual - expected) / expected)
    abs_diff = abs(actual - expected)
    
    return pct_diff <= tolerance_pct or abs_diff <= tolerance_abs


def calculate_pooled_std_error(
    n1: int,
    p1: float,
    n2: int,
    p2: float
) -> float:
    """
    Calculate pooled standard error for two proportions.
    
    Args:
        n1: Sample size group 1
        p1: Proportion group 1
        n2: Sample size group 2
        p2: Proportion group 2
    
    Returns:
        Pooled standard error
    """
    p_pooled = (n1 * p1 + n2 * p2) / (n1 + n2)
    se = math.sqrt(p_pooled * (1 - p_pooled) * (1/n1 + 1/n2))
    return se


# ============================================================================
# Z-Score Lookup Table
# ============================================================================

Z_SCORES: Dict[Tuple[float, str], float] = {
    # (alpha, direction): z_score
    (0.01, "two_tailed"): 2.576,
    (0.05, "two_tailed"): 1.96,
    (0.10, "two_tailed"): 1.645,
    (0.01, "one_tailed"): 2.326,
    (0.05, "one_tailed"): 1.645,
    (0.10, "one_tailed"): 1.282,
    (0.20, "one_tailed"): 0.842,  # For power = 0.80
}


# ============================================================================
# Power Calculation Expected Results
# ============================================================================

EXPECTED_POWER_VALUES: Dict[str, Dict[str, Any]] = {
    "standard_power": {
        "params": {
            "n_per_arm": 6000,
            "baseline": 0.05,
            "lift": 0.15,
            "alpha": 0.05,
        },
        "expected_power_min": 0.78,
        "expected_power_max": 0.82,
    },
    
    "high_power": {
        "params": {
            "n_per_arm": 10000,
            "baseline": 0.05,
            "lift": 0.15,
            "alpha": 0.05,
        },
        "expected_power_min": 0.88,
        "expected_power_max": 0.92,
    },
}

