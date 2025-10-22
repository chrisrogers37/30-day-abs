"""
Custom assertions for testing.

This module provides custom assertion functions that make tests more readable
and provide better error messages.
"""

from typing import Any, Tuple, Optional
import math


def assert_within_tolerance(
    expected: float,
    actual: float,
    tolerance_pct: float = 0.05,
    tolerance_abs: float = 0.001,
    message: Optional[str] = None
) -> None:
    """
    Assert that actual value is within tolerance of expected value.
    
    Args:
        expected: Expected value
        actual: Actual value
        tolerance_pct: Percentage tolerance (0.05 = 5%)
        tolerance_abs: Absolute tolerance
        message: Optional custom error message
    
    Raises:
        AssertionError: If value is outside tolerance
    """
    if expected == 0:
        diff = abs(actual - expected)
        if diff > tolerance_abs:
            msg = message or (
                f"Expected {expected} ± {tolerance_abs} (absolute), "
                f"got {actual} (diff: {diff})"
            )
            raise AssertionError(msg)
        return
    
    pct_diff = abs((actual - expected) / expected)
    abs_diff = abs(actual - expected)
    
    if pct_diff > tolerance_pct and abs_diff > tolerance_abs:
        msg = message or (
            f"Expected {expected} ± {tolerance_pct*100}% or ± {tolerance_abs}, "
            f"got {actual} (pct_diff: {pct_diff*100:.2f}%, abs_diff: {abs_diff})"
        )
        raise AssertionError(msg)


def assert_confidence_interval_valid(
    ci: Tuple[float, float],
    point_estimate: Optional[float] = None,
    message: Optional[str] = None
) -> None:
    """
    Assert that confidence interval is valid.
    
    Args:
        ci: Confidence interval tuple (lower, upper)
        point_estimate: Optional point estimate that should be in interval
        message: Optional custom error message
    
    Raises:
        AssertionError: If CI is invalid
    """
    lower, upper = ci
    
    # Check that lower < upper
    if lower >= upper:
        msg = message or f"Invalid CI: lower ({lower}) >= upper ({upper})"
        raise AssertionError(msg)
    
    # Check that point estimate is in interval if provided
    if point_estimate is not None:
        if not (lower <= point_estimate <= upper):
            msg = message or (
                f"Point estimate {point_estimate} not in CI [{lower}, {upper}]"
            )
            raise AssertionError(msg)


def assert_probability_valid(
    probability: float,
    allow_zero: bool = True,
    allow_one: bool = True,
    message: Optional[str] = None
) -> None:
    """
    Assert that value is a valid probability.
    
    Args:
        probability: Value to check
        allow_zero: Whether 0.0 is valid
        allow_one: Whether 1.0 is valid
        message: Optional custom error message
    
    Raises:
        AssertionError: If not a valid probability
    """
    min_val = 0.0 if allow_zero else 0.0 + 1e-10
    max_val = 1.0 if allow_one else 1.0 - 1e-10
    
    if not (min_val <= probability <= max_val):
        msg = message or (
            f"Invalid probability: {probability} "
            f"(must be in [{min_val}, {max_val}])"
        )
        raise AssertionError(msg)


def assert_sample_size_valid(
    n: int,
    min_n: int = 1,
    message: Optional[str] = None
) -> None:
    """
    Assert that sample size is valid.
    
    Args:
        n: Sample size to check
        min_n: Minimum valid sample size
        message: Optional custom error message
    
    Raises:
        AssertionError: If sample size is invalid
    """
    if n < min_n:
        msg = message or f"Invalid sample size: {n} (must be >= {min_n})"
        raise AssertionError(msg)


def assert_conversion_data_valid(
    n: int,
    conversions: int,
    message: Optional[str] = None
) -> None:
    """
    Assert that conversion data is valid.
    
    Args:
        n: Sample size
        conversions: Number of conversions
        message: Optional custom error message
    
    Raises:
        AssertionError: If data is invalid
    """
    if conversions < 0:
        msg = message or f"Invalid conversions: {conversions} (must be >= 0)"
        raise AssertionError(msg)
    
    if conversions > n:
        msg = message or (
            f"Invalid conversions: {conversions} > sample size {n}"
        )
        raise AssertionError(msg)


def assert_p_value_valid(
    p_value: float,
    message: Optional[str] = None
) -> None:
    """
    Assert that p-value is valid.
    
    Args:
        p_value: P-value to check
        message: Optional custom error message
    
    Raises:
        AssertionError: If p-value is invalid
    """
    if not (0.0 <= p_value <= 1.0):
        msg = message or f"Invalid p-value: {p_value} (must be in [0, 1])"
        raise AssertionError(msg)


def assert_effect_size_reasonable(
    effect_size: float,
    max_absolute: float = 2.0,
    message: Optional[str] = None
) -> None:
    """
    Assert that effect size is reasonable.
    
    Args:
        effect_size: Effect size to check
        max_absolute: Maximum absolute value
        message: Optional custom error message
    
    Raises:
        AssertionError: If effect size is unreasonable
    """
    if abs(effect_size) > max_absolute:
        msg = message or (
            f"Unreasonable effect size: {effect_size} "
            f"(|effect| > {max_absolute})"
        )
        raise AssertionError(msg)


def assert_allocation_valid(
    control: float,
    treatment: float,
    tolerance: float = 1e-6,
    message: Optional[str] = None
) -> None:
    """
    Assert that allocation is valid.
    
    Args:
        control: Control group allocation
        treatment: Treatment group allocation
        tolerance: Tolerance for sum check
        message: Optional custom error message
    
    Raises:
        AssertionError: If allocation is invalid
    """
    # Check that allocations are valid probabilities
    assert_probability_valid(control, message=f"Invalid control allocation: {control}")
    assert_probability_valid(treatment, message=f"Invalid treatment allocation: {treatment}")
    
    # Check that allocations sum to 1
    total = control + treatment
    if abs(total - 1.0) > tolerance:
        msg = message or (
            f"Allocation doesn't sum to 1: control={control}, "
            f"treatment={treatment}, sum={total}"
        )
        raise AssertionError(msg)


def assert_simulation_result_valid(
    control_n: int,
    control_conversions: int,
    treatment_n: int,
    treatment_conversions: int,
    message: Optional[str] = None
) -> None:
    """
    Assert that simulation result is valid.
    
    Args:
        control_n: Control group sample size
        control_conversions: Control group conversions
        treatment_n: Treatment group sample size
        treatment_conversions: Treatment group conversions
        message: Optional custom error message
    
    Raises:
        AssertionError: If simulation result is invalid
    """
    assert_sample_size_valid(control_n, message=f"Invalid control_n: {control_n}")
    assert_sample_size_valid(treatment_n, message=f"Invalid treatment_n: {treatment_n}")
    assert_conversion_data_valid(
        control_n,
        control_conversions,
        message=f"Invalid control conversions: {control_conversions}/{control_n}"
    )
    assert_conversion_data_valid(
        treatment_n,
        treatment_conversions,
        message=f"Invalid treatment conversions: {treatment_conversions}/{treatment_n}"
    )


def assert_dict_contains_keys(
    d: dict,
    required_keys: list,
    message: Optional[str] = None
) -> None:
    """
    Assert that dictionary contains required keys.
    
    Args:
        d: Dictionary to check
        required_keys: List of required keys
        message: Optional custom error message
    
    Raises:
        AssertionError: If any required keys are missing
    """
    missing_keys = set(required_keys) - set(d.keys())
    if missing_keys:
        msg = message or f"Missing required keys: {missing_keys}"
        raise AssertionError(msg)


def assert_percentage_format(
    value: float,
    expected_range: Tuple[float, float] = (0.0, 100.0),
    message: Optional[str] = None
) -> None:
    """
    Assert that value is in percentage format.
    
    Args:
        value: Value to check
        expected_range: Expected range (min, max)
        message: Optional custom error message
    
    Raises:
        AssertionError: If value is outside range
    """
    min_val, max_val = expected_range
    if not (min_val <= value <= max_val):
        msg = message or (
            f"Value {value} outside percentage range [{min_val}, {max_val}]"
        )
        raise AssertionError(msg)


def assert_lists_almost_equal(
    list1: list,
    list2: list,
    tolerance: float = 1e-6,
    message: Optional[str] = None
) -> None:
    """
    Assert that two lists of numbers are almost equal.
    
    Args:
        list1: First list
        list2: Second list
        tolerance: Tolerance for element comparison
        message: Optional custom error message
    
    Raises:
        AssertionError: If lists differ
    """
    if len(list1) != len(list2):
        msg = message or (
            f"Lists have different lengths: {len(list1)} vs {len(list2)}"
        )
        raise AssertionError(msg)
    
    for i, (v1, v2) in enumerate(zip(list1, list2)):
        if abs(v1 - v2) > tolerance:
            msg = message or (
                f"Lists differ at index {i}: {v1} vs {v2} "
                f"(diff: {abs(v1 - v2)})"
            )
            raise AssertionError(msg)


def assert_is_deterministic(
    func: callable,
    *args,
    **kwargs
) -> None:
    """
    Assert that function produces deterministic results.
    
    Args:
        func: Function to test
        *args: Positional arguments for function
        **kwargs: Keyword arguments for function
    
    Raises:
        AssertionError: If function is not deterministic
    """
    result1 = func(*args, **kwargs)
    result2 = func(*args, **kwargs)
    
    if result1 != result2:
        raise AssertionError(
            f"Function {func.__name__} is not deterministic: "
            f"{result1} != {result2}"
        )

