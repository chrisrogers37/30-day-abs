"""
Object factories for testing.

This module provides factory functions for creating test objects with
sensible defaults, reducing boilerplate in tests.
"""

from typing import Optional, Dict, Any
import numpy as np

from core.types import Allocation, DesignParams, SimResult
from schemas.shared import AllocationDTO, CompanyType, UserSegment
from schemas.scenario import ScenarioDTO


# ============================================================================
# Core Type Factories
# ============================================================================

def create_allocation(
    control: float = 0.5,
    treatment: float = 0.5
) -> Allocation:
    """
    Create an Allocation object.
    
    Args:
        control: Control group allocation (default: 0.5)
        treatment: Treatment group allocation (default: 0.5)
    
    Returns:
        Allocation object
    """
    return Allocation(control=control, treatment=treatment)


def create_design_params(
    baseline_conversion_rate: float = 0.05,
    target_lift_pct: float = 0.15,
    alpha: float = 0.05,
    power: float = 0.80,
    allocation: Optional[Allocation] = None,
    expected_daily_traffic: int = 10000
) -> DesignParams:
    """
    Create DesignParams object with sensible defaults.
    
    Args:
        baseline_conversion_rate: Baseline rate (default: 0.05)
        target_lift_pct: Target relative lift (default: 0.15)
        alpha: Significance level (default: 0.05)
        power: Statistical power (default: 0.80)
        allocation: Allocation object (default: 50/50)
        expected_daily_traffic: Daily traffic (default: 10000)
    
    Returns:
        DesignParams object
    """
    if allocation is None:
        allocation = create_allocation()
    
    return DesignParams(
        baseline_conversion_rate=baseline_conversion_rate,
        target_lift_pct=target_lift_pct,
        alpha=alpha,
        power=power,
        allocation=allocation,
        expected_daily_traffic=expected_daily_traffic
    )


def create_sim_result(
    control_n: int = 1000,
    control_conversions: int = 50,
    treatment_n: int = 1000,
    treatment_conversions: int = 60,
    user_data: Optional[list] = None
) -> SimResult:
    """
    Create SimResult object with sensible defaults.
    
    Args:
        control_n: Control sample size (default: 1000)
        control_conversions: Control conversions (default: 50)
        treatment_n: Treatment sample size (default: 1000)
        treatment_conversions: Treatment conversions (default: 60)
        user_data: Optional user-level data
    
    Returns:
        SimResult object
    """
    return SimResult(
        control_n=control_n,
        control_conversions=control_conversions,
        treatment_n=treatment_n,
        treatment_conversions=treatment_conversions,
        user_data=user_data
    )


# ============================================================================
# Schema/DTO Factories
# ============================================================================

def create_allocation_dto(
    control: float = 0.5,
    treatment: float = 0.5
) -> AllocationDTO:
    """
    Create AllocationDTO object.
    
    Args:
        control: Control group allocation (default: 0.5)
        treatment: Treatment group allocation (default: 0.5)
    
    Returns:
        AllocationDTO object
    """
    return AllocationDTO(control=control, treatment=treatment)


def create_scenario_dict(
    company_type: str = "E-commerce",
    user_segment: str = "all_users",
    baseline: float = 0.025,
    lift: float = 0.20,
    traffic: int = 5000
) -> Dict[str, Any]:
    """
    Create a scenario dictionary for testing.
    
    Args:
        company_type: Company type (default: "E-commerce")
        user_segment: User segment (default: "all_users")
        baseline: Baseline conversion rate (default: 0.025)
        lift: Target lift (default: 0.20)
        traffic: Daily traffic (default: 5000)
    
    Returns:
        Dictionary representing complete scenario
    """
    return {
        "scenario": {
            "title": f"{company_type} Test Scenario",
            "company_type": company_type,
            "user_segment": user_segment,
            "description": "Test scenario for unit testing",
            "intervention_description": "Test intervention",
            "primary_metric": "Conversion rate",
            "hypothesis": f"Will improve conversion by {lift*100}%"
        },
        "design_params": {
            "baseline_conversion_rate": baseline,
            "mde_absolute": baseline * lift * 0.5,
            "target_lift_pct": lift,
            "alpha": 0.05,
            "power": 0.80,
            "allocation": {"control": 0.5, "treatment": 0.5},
            "expected_daily_traffic": traffic
        },
        "business_context": {
            "business_target_absolute": baseline * lift * 0.8,
            "business_target_relative_pct": lift * 0.8,
            "revenue_per_conversion": 50.0,
            "implementation_cost": 10000.0,
            "risk_tolerance": "medium"
        }
    }


# ============================================================================
# Statistical Test Case Factories
# ============================================================================

def create_significant_positive_result(
    n_per_arm: int = 5000,
    baseline: float = 0.05,
    lift: float = 0.30,
    seed: Optional[int] = None
) -> SimResult:
    """
    Create simulation result with significant positive effect.
    
    Args:
        n_per_arm: Sample size per arm (default: 5000)
        baseline: Baseline rate (default: 0.05)
        lift: Relative lift (default: 0.30)
        seed: Random seed for reproducibility
    
    Returns:
        SimResult with significant positive effect
    """
    if seed is not None:
        np.random.seed(seed)
    
    control_conversions = int(n_per_arm * baseline)
    treatment_rate = baseline * (1 + lift)
    treatment_conversions = int(n_per_arm * treatment_rate)
    
    return create_sim_result(
        control_n=n_per_arm,
        control_conversions=control_conversions,
        treatment_n=n_per_arm,
        treatment_conversions=treatment_conversions
    )


def create_non_significant_result(
    n_per_arm: int = 500,
    baseline: float = 0.05,
    lift: float = 0.08,
    seed: Optional[int] = None
) -> SimResult:
    """
    Create simulation result with non-significant effect.
    
    Args:
        n_per_arm: Sample size per arm (default: 500)
        baseline: Baseline rate (default: 0.05)
        lift: Small relative lift (default: 0.08)
        seed: Random seed for reproducibility
    
    Returns:
        SimResult with non-significant effect
    """
    if seed is not None:
        np.random.seed(seed)
    
    control_conversions = int(n_per_arm * baseline)
    treatment_rate = baseline * (1 + lift)
    treatment_conversions = int(n_per_arm * treatment_rate)
    
    return create_sim_result(
        control_n=n_per_arm,
        control_conversions=control_conversions,
        treatment_n=n_per_arm,
        treatment_conversions=treatment_conversions
    )


def create_significant_negative_result(
    n_per_arm: int = 3000,
    baseline: float = 0.06,
    negative_lift: float = -0.25,
    seed: Optional[int] = None
) -> SimResult:
    """
    Create simulation result with significant negative effect.
    
    Args:
        n_per_arm: Sample size per arm (default: 3000)
        baseline: Baseline rate (default: 0.06)
        negative_lift: Negative relative lift (default: -0.25)
        seed: Random seed for reproducibility
    
    Returns:
        SimResult with significant negative effect
    """
    if seed is not None:
        np.random.seed(seed)
    
    control_conversions = int(n_per_arm * baseline)
    treatment_rate = baseline * (1 + negative_lift)
    treatment_conversions = int(n_per_arm * treatment_rate)
    
    return create_sim_result(
        control_n=n_per_arm,
        control_conversions=control_conversions,
        treatment_n=n_per_arm,
        treatment_conversions=treatment_conversions
    )


# ============================================================================
# Edge Case Factories
# ============================================================================

def create_zero_conversion_result(n_per_arm: int = 1000) -> SimResult:
    """
    Create result with zero conversions (edge case).
    
    Args:
        n_per_arm: Sample size per arm
    
    Returns:
        SimResult with zero conversions
    """
    return create_sim_result(
        control_n=n_per_arm,
        control_conversions=0,
        treatment_n=n_per_arm,
        treatment_conversions=0
    )


def create_perfect_conversion_result(n_per_arm: int = 100) -> SimResult:
    """
    Create result with 100% conversion (edge case).
    
    Args:
        n_per_arm: Sample size per arm
    
    Returns:
        SimResult with 100% conversions
    """
    return create_sim_result(
        control_n=n_per_arm,
        control_conversions=n_per_arm,
        treatment_n=n_per_arm,
        treatment_conversions=n_per_arm
    )


def create_very_small_sample_result() -> SimResult:
    """
    Create result with very small sample size (edge case).
    
    Returns:
        SimResult with small sample
    """
    return create_sim_result(
        control_n=10,
        control_conversions=1,
        treatment_n=10,
        treatment_conversions=2
    )


def create_unbalanced_allocation_params(
    control_pct: float = 0.7,
    treatment_pct: float = 0.3
) -> DesignParams:
    """
    Create design params with unbalanced allocation.
    
    Args:
        control_pct: Control allocation percentage
        treatment_pct: Treatment allocation percentage
    
    Returns:
        DesignParams with unbalanced allocation
    """
    allocation = create_allocation(
        control=control_pct,
        treatment=treatment_pct
    )
    return create_design_params(allocation=allocation)


# ============================================================================
# Batch Factories
# ============================================================================

def create_multiple_design_params(
    baseline_rates: list = None,
    lifts: list = None
) -> list:
    """
    Create multiple design params for parametrized tests.
    
    Args:
        baseline_rates: List of baseline rates
        lifts: List of lift percentages
    
    Returns:
        List of DesignParams objects
    """
    if baseline_rates is None:
        baseline_rates = [0.05, 0.10, 0.15]
    
    if lifts is None:
        lifts = [0.10, 0.15, 0.20]
    
    params_list = []
    for baseline in baseline_rates:
        for lift in lifts:
            params = create_design_params(
                baseline_conversion_rate=baseline,
                target_lift_pct=lift
            )
            params_list.append(params)
    
    return params_list


def create_test_case_matrix(
    baselines: list = None,
    lifts: list = None,
    alphas: list = None,
    powers: list = None
) -> list:
    """
    Create matrix of test cases for comprehensive testing.
    
    Args:
        baselines: List of baseline rates
        lifts: List of lift percentages
        alphas: List of alpha values
        powers: List of power values
    
    Returns:
        List of tuples (baseline, lift, alpha, power)
    """
    if baselines is None:
        baselines = [0.05, 0.10]
    if lifts is None:
        lifts = [0.10, 0.15, 0.20]
    if alphas is None:
        alphas = [0.05]
    if powers is None:
        powers = [0.80]
    
    test_cases = []
    for baseline in baselines:
        for lift in lifts:
            for alpha in alphas:
                for power in powers:
                    test_cases.append((baseline, lift, alpha, power))
    
    return test_cases


# ============================================================================
# User Data Factories
# ============================================================================

def create_user_data_record(
    user_id: str = "user_001",
    group: str = "control",
    converted: bool = False,
    timestamp: str = "2024-01-15T10:00:00",
    **kwargs
) -> Dict[str, Any]:
    """
    Create a single user data record.
    
    Args:
        user_id: User ID
        group: Group assignment (control/treatment)
        converted: Conversion status
        timestamp: Timestamp string
        **kwargs: Additional attributes
    
    Returns:
        Dictionary representing user data
    """
    record = {
        "user_id": user_id,
        "group": group,
        "converted": converted,
        "timestamp": timestamp,
        "session_duration": kwargs.get("session_duration", 60),
        "page_views": kwargs.get("page_views", 3),
        "device_type": kwargs.get("device_type", "mobile"),
        "traffic_source": kwargs.get("traffic_source", "organic")
    }
    
    return record


def create_user_data_batch(
    n_users: int = 100,
    conversion_rate: float = 0.05,
    group: str = "control",
    seed: Optional[int] = None
) -> list:
    """
    Create batch of user data records.
    
    Args:
        n_users: Number of user records to create
        conversion_rate: Conversion rate for the batch
        group: Group assignment
        seed: Random seed
    
    Returns:
        List of user data dictionaries
    """
    if seed is not None:
        np.random.seed(seed)
    
    user_data = []
    conversions = np.random.binomial(1, conversion_rate, n_users)
    
    for i in range(n_users):
        record = create_user_data_record(
            user_id=f"user_{i:06d}",
            group=group,
            converted=bool(conversions[i]),
            timestamp=f"2024-01-15T{10 + i//100:02d}:{(i%100)//2:02d}:00"
        )
        user_data.append(record)
    
    return user_data

