"""
Reusable test data for all test modules.

This module contains common test data, sample values, and constants
used across multiple test modules.
"""

from core.types import Allocation, DesignParams


# ============================================================================
# Standard Test Parameters
# ============================================================================

STANDARD_BASELINE = 0.05
STANDARD_LIFT = 0.15
STANDARD_ALPHA = 0.05
STANDARD_POWER = 0.80
STANDARD_TRAFFIC = 10000

# ============================================================================
# Sample Design Parameters
# ============================================================================

def get_standard_design_params() -> DesignParams:
    """Get standard design parameters for testing."""
    return DesignParams(
        baseline_conversion_rate=STANDARD_BASELINE,
        target_lift_pct=STANDARD_LIFT,
        alpha=STANDARD_ALPHA,
        power=STANDARD_POWER,
        allocation=Allocation(control=0.5, treatment=0.5),
        expected_daily_traffic=STANDARD_TRAFFIC
    )


# ============================================================================
# Edge Cases for Testing
# ============================================================================

EDGE_CASE_PARAMS = [
    # (baseline, lift, alpha, power, description)
    (0.001, 0.20, 0.05, 0.80, "very_low_baseline"),
    (0.50, 0.05, 0.05, 0.80, "very_high_baseline"),
    (0.05, 0.05, 0.05, 0.80, "very_small_lift"),
    (0.05, 0.50, 0.05, 0.80, "very_large_lift"),
    (0.05, 0.15, 0.01, 0.80, "very_low_alpha"),
    (0.05, 0.15, 0.10, 0.80, "very_high_alpha"),
    (0.05, 0.15, 0.05, 0.70, "low_power"),
    (0.05, 0.15, 0.05, 0.95, "very_high_power"),
]


# ============================================================================
# Company and Scenario Types
# ============================================================================

COMPANY_TYPES = [
    "SaaS",
    "E-commerce",
    "Media",
    "Fintech",
    "Marketplace",
    "Gaming"
]

USER_SEGMENTS = [
    "new_users",
    "returning_users",
    "premium_users",
    "all_users"
]

# ============================================================================
# Sample Simulation Results
# ============================================================================

SAMPLE_SIM_RESULTS = {
    "significant_positive": {
        "control_n": 5000,
        "control_conversions": 250,
        "treatment_n": 5000,
        "treatment_conversions": 325,
        "expected_significant": True,
        "expected_direction": "positive"
    },
    "significant_negative": {
        "control_n": 5000,
        "control_conversions": 300,
        "treatment_n": 5000,
        "treatment_conversions": 225,
        "expected_significant": True,
        "expected_direction": "negative"
    },
    "non_significant": {
        "control_n": 500,
        "control_conversions": 25,
        "treatment_n": 500,
        "treatment_conversions": 27,
        "expected_significant": False,
        "expected_direction": "unclear"
    },
    "borderline": {
        "control_n": 2000,
        "control_conversions": 100,
        "treatment_n": 2000,
        "treatment_conversions": 120,
        "expected_significant": "borderline",
        "expected_direction": "positive"
    }
}


# ============================================================================
# Expected Calculation Results
# ============================================================================

EXPECTED_SAMPLE_SIZES = {
    "standard": {
        "baseline": 0.05,
        "lift": 0.15,
        "alpha": 0.05,
        "power": 0.80,
        "expected_per_arm_min": 5000,
        "expected_per_arm_max": 7000,
    },
    "high_power": {
        "baseline": 0.05,
        "lift": 0.15,
        "alpha": 0.05,
        "power": 0.90,
        "expected_per_arm_min": 6500,
        "expected_per_arm_max": 8500,
    },
    "small_lift": {
        "baseline": 0.05,
        "lift": 0.10,
        "alpha": 0.05,
        "power": 0.80,
        "expected_per_arm_min": 9000,
        "expected_per_arm_max": 11000,
    },
}


# ============================================================================
# Rollout Decision Test Cases
# ============================================================================

ROLLOUT_DECISION_CASES = [
    {
        "name": "clear_proceed",
        "ci_lower": 0.02,
        "ci_upper": 0.04,
        "business_target": 0.01,
        "expected_decision": "proceed_with_confidence"
    },
    {
        "name": "proceed_with_caution",
        "ci_lower": 0.005,
        "ci_upper": 0.025,
        "business_target": 0.01,
        "expected_decision": "proceed_with_caution"
    },
    {
        "name": "do_not_proceed",
        "ci_lower": -0.01,
        "ci_upper": 0.015,
        "business_target": 0.02,
        "expected_decision": "do_not_proceed"
    },
]


# ============================================================================
# Validation Tolerances
# ============================================================================

VALIDATION_TOLERANCES = {
    "mde_absolute": 0.001,
    "target_conversion_rate": 0.005,
    "relative_lift_pct": 0.05,
    "sample_size_per_arm": 100,
    "test_duration_days": 1,
    "additional_conversions_per_day": 5,
    "control_conversion_rate": 0.005,
    "treatment_conversion_rate": 0.005,
    "absolute_lift": 0.005,
    "relative_lift": 0.05,
    "p_value": 0.01,
    "confidence_interval_bound": 0.005,
}


# ============================================================================
# Mock LLM Prompts and Responses
# ============================================================================

SAMPLE_LLM_PROMPTS = {
    "scenario_generation": """Generate a realistic A/B test scenario for {company_type} 
    targeting {user_segment}. Include statistical parameters and business context.""",
    
    "parameter_validation": """Validate these A/B test parameters and suggest improvements: 
    Baseline: {baseline}, Target Lift: {lift}, Alpha: {alpha}, Power: {power}""",
}


SAMPLE_LLM_RESPONSES = {
    "valid_scenario": {
        "title": "Checkout Flow Simplification",
        "company_type": "E-commerce",
        "baseline_conversion_rate": 0.035,
        "target_lift_pct": 0.20,
    },
    
    "invalid_scenario": {
        "title": "Invalid Test Scenario",
        "company_type": "Unknown",
        "baseline_conversion_rate": 1.5,  # Invalid: > 1.0
        "target_lift_pct": 2.0,  # Invalid: > 1.0
    }
}


# ============================================================================
# User Data Samples
# ============================================================================

SAMPLE_USER_DATA = [
    {
        "user_id": "user_001",
        "group": "control",
        "converted": True,
        "timestamp": "2024-01-15T10:00:00",
        "session_duration": 120,
        "page_views": 5,
        "device_type": "mobile",
        "traffic_source": "organic"
    },
    {
        "user_id": "user_002",
        "group": "control",
        "converted": False,
        "timestamp": "2024-01-15T10:05:00",
        "session_duration": 45,
        "page_views": 2,
        "device_type": "desktop",
        "traffic_source": "paid"
    },
    {
        "user_id": "user_003",
        "group": "treatment",
        "converted": True,
        "timestamp": "2024-01-15T10:10:00",
        "session_duration": 150,
        "page_views": 7,
        "device_type": "mobile",
        "traffic_source": "organic"
    },
    {
        "user_id": "user_004",
        "group": "treatment",
        "converted": False,
        "timestamp": "2024-01-15T10:15:00",
        "session_duration": 30,
        "page_views": 1,
        "device_type": "tablet",
        "traffic_source": "direct"
    },
]


# ============================================================================
# Statistical Test Cases
# ============================================================================

STATISTICAL_TEST_CASES = {
    "two_proportion_z": {
        "name": "Two-Proportion Z-Test",
        "suitable_for": "large_samples",
        "min_sample_size": 30,
    },
    "chi_square": {
        "name": "Chi-Square Test",
        "suitable_for": "categorical_data",
        "min_expected_count": 5,
    },
    "fisher_exact": {
        "name": "Fisher's Exact Test",
        "suitable_for": "small_samples",
        "max_sample_size": 1000,
    },
}


# ============================================================================
# Answer Key Examples
# ============================================================================

SAMPLE_DESIGN_ANSWERS = {
    "mde_absolute": 0.0075,
    "target_conversion_rate": 5.75,
    "relative_lift_pct": 15.0,
    "sample_size_per_arm": 5500,
    "test_duration_days": 2,
    "additional_conversions_per_day": 75,
}

SAMPLE_ANALYSIS_ANSWERS = {
    "control_conversion_rate": 5.0,
    "treatment_conversion_rate": 6.0,
    "absolute_lift": 1.0,
    "relative_lift_pct": 20.0,
    "p_value": 0.023,
    "confidence_interval": (0.2, 1.8),
    "rollout_decision": "proceed_with_confidence",
}

