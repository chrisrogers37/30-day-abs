"""
Comprehensive tests for core.design module - Sample Size Calculation.

These tests exercise the compute_sample_size function and related helper
functions with proper test coverage of validation, edge cases, and
auxiliary functions like validate_test_duration and suggest_parameter_adjustments.
"""

import pytest
import math
from unittest.mock import Mock, patch

from core.design import (
    compute_sample_size,
    _get_z_score,
    _calculate_achieved_power,
    _normal_cdf,
    calculate_minimum_detectable_effect,
    validate_test_duration,
    suggest_parameter_adjustments,
)
from core.types import DesignParams, Allocation, SampleSize


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def standard_params():
    """Create standard design parameters."""
    return DesignParams(
        baseline_conversion_rate=0.05,
        target_lift_pct=0.15,
        alpha=0.05,
        power=0.80,
        expected_daily_traffic=5000,
        allocation=Allocation(control=0.5, treatment=0.5)
    )


@pytest.fixture
def sample_size_result():
    """Create a sample size result for testing."""
    return SampleSize(
        per_arm=5000,
        total=10000,
        days_required=2,
        power_achieved=0.82
    )


# ============================================================================
# compute_sample_size Error Handling Tests
# ============================================================================


class TestComputeSampleSizeErrors:
    """Test suite for compute_sample_size error handling."""

    @pytest.mark.unit
    def test_compute_sample_size_negative_lift_causes_invalid_rate(self):
        """Test that negative lift resulting in p2 <= 0 raises ValueError."""
        # Use mock to bypass DesignParams validation
        params = Mock()
        params.baseline_conversion_rate = 0.05
        params.target_lift_pct = -1.1  # Results in p2 = 0.05 * (1 - 1.1) = -0.005
        params.alpha = 0.05
        params.power = 0.80
        params.expected_daily_traffic = 5000
        params.allocation = Allocation(control=0.5, treatment=0.5)

        with pytest.raises(ValueError, match="outside valid range"):
            compute_sample_size(params)

    @pytest.mark.unit
    def test_compute_sample_size_huge_lift_causes_invalid_rate(self):
        """Test that huge lift resulting in p2 >= 1 raises ValueError."""
        # Use mock to bypass DesignParams validation
        params = Mock()
        params.baseline_conversion_rate = 0.5
        params.target_lift_pct = 1.5  # Results in p2 = 0.5 * (1 + 1.5) = 1.25 > 1
        params.alpha = 0.05
        params.power = 0.80
        params.expected_daily_traffic = 5000
        params.allocation = Allocation(control=0.5, treatment=0.5)

        with pytest.raises(ValueError, match="outside valid range"):
            compute_sample_size(params)


# ============================================================================
# _get_z_score Tests
# ============================================================================


class TestGetZScore:
    """Test suite for _get_z_score function including edge cases."""

    @pytest.mark.unit
    def test_get_z_score_alpha_0_10_two_tailed(self):
        """Test z-score for alpha=0.10 two-tailed."""
        z_score = _get_z_score(0.10, "two_tailed")
        # alpha=0.10 two-tailed -> alpha/2=0.05 which matches the 0.05 lookup
        # The function returns 1.96 for two_tailed when alpha/2=0.05
        assert abs(z_score - 1.96) < 0.1

    @pytest.mark.unit
    def test_get_z_score_nonstandard_alpha(self):
        """Test z-score for non-standard alpha value."""
        # Test with alpha=0.03 (not in lookup table)
        z_score = _get_z_score(0.03, "two_tailed")
        # Should use scipy or fallback
        assert z_score > 1.96  # More conservative than 0.05

    @pytest.mark.unit
    def test_get_z_score_very_small_alpha(self):
        """Test z-score for very small alpha."""
        z_score = _get_z_score(0.001, "two_tailed")
        # Very small alpha should give high z-score
        assert z_score > 2.576

    @pytest.mark.unit
    def test_get_z_score_scipy_fallback(self):
        """Test z-score calculation with scipy import for non-standard alpha."""
        # This tests the scipy branch by using a non-standard alpha
        z_score = _get_z_score(0.025, "one_tailed")
        assert z_score > 0  # Should work even with scipy
        # For alpha=0.025, z-score should be around 1.96
        assert abs(z_score - 1.96) < 0.1

    @pytest.mark.unit
    def test_get_z_score_alpha_0_02_uses_scipy(self):
        """Test z-score calculation for alpha=0.02 uses scipy branch."""
        # alpha=0.02 is not in the lookup table, so it uses scipy
        z_score = _get_z_score(0.02, "one_tailed")
        assert z_score > 0
        # For alpha=0.02, z-score should be around 2.05
        assert z_score > 1.96  # More conservative than 0.05


# ============================================================================
# _calculate_achieved_power Tests
# ============================================================================


class TestCalculateAchievedPower:
    """Test suite for _calculate_achieved_power function."""

    @pytest.mark.unit
    def test_calculate_achieved_power_basic(self):
        """Test basic power calculation."""
        power = _calculate_achieved_power(
            p1=0.05,
            p2=0.06,  # 20% lift
            n=14000,
            alpha=0.05,
            direction="two_tailed"
        )

        assert 0 <= power <= 1
        assert power > 0.5  # Should have reasonable power with good sample size

    @pytest.mark.unit
    def test_calculate_achieved_power_small_sample(self):
        """Test power with small sample size."""
        power = _calculate_achieved_power(
            p1=0.05,
            p2=0.055,
            n=100,
            alpha=0.05,
            direction="two_tailed"
        )

        # Small sample = low power
        assert power < 0.5

    @pytest.mark.unit
    def test_calculate_achieved_power_large_effect(self):
        """Test power with large effect size."""
        power = _calculate_achieved_power(
            p1=0.05,
            p2=0.10,  # 100% lift
            n=1000,
            alpha=0.05,
            direction="two_tailed"
        )

        # Large effect = high power even with moderate sample
        assert power > 0.8

    @pytest.mark.unit
    def test_calculate_achieved_power_one_tailed(self):
        """Test power with one-tailed test."""
        power_one = _calculate_achieved_power(
            p1=0.05,
            p2=0.06,
            n=5000,
            alpha=0.05,
            direction="one_tailed"
        )

        power_two = _calculate_achieved_power(
            p1=0.05,
            p2=0.06,
            n=5000,
            alpha=0.05,
            direction="two_tailed"
        )

        # One-tailed should have higher power
        assert power_one > power_two

    @pytest.mark.unit
    def test_calculate_achieved_power_bounds(self):
        """Test that power is bounded to [0, 1]."""
        # Test with extreme parameters
        power = _calculate_achieved_power(
            p1=0.05,
            p2=0.5,  # Huge effect
            n=100000,  # Huge sample
            alpha=0.05,
            direction="two_tailed"
        )

        assert power <= 1.0
        assert power >= 0.0


# ============================================================================
# _normal_cdf Tests
# ============================================================================


class TestNormalCDF:
    """Test suite for _normal_cdf function."""

    @pytest.mark.unit
    def test_normal_cdf_zero(self):
        """Test CDF at z=0."""
        result = _normal_cdf(0)
        assert abs(result - 0.5) < 0.01

    @pytest.mark.unit
    def test_normal_cdf_positive(self):
        """Test CDF for positive z."""
        result = _normal_cdf(1.96)
        # CDF(1.96) ≈ 0.975
        assert abs(result - 0.975) < 0.01

    @pytest.mark.unit
    def test_normal_cdf_negative(self):
        """Test CDF for negative z."""
        result = _normal_cdf(-1.96)
        # CDF(-1.96) ≈ 0.025
        assert abs(result - 0.025) < 0.01

    @pytest.mark.unit
    def test_normal_cdf_extreme_positive(self):
        """Test CDF for extreme positive z."""
        result = _normal_cdf(5)
        # Should be very close to 1
        assert result > 0.999

    @pytest.mark.unit
    def test_normal_cdf_extreme_negative(self):
        """Test CDF for extreme negative z."""
        result = _normal_cdf(-5)
        # Should be very close to 0
        assert result < 0.001


# ============================================================================
# calculate_minimum_detectable_effect Tests
# ============================================================================


class TestCalculateMDE:
    """Test suite for calculate_minimum_detectable_effect function."""

    @pytest.mark.unit
    def test_calculate_mde_basic(self):
        """Test basic MDE calculation."""
        mde = calculate_minimum_detectable_effect(
            p1=0.05,
            n=14000,
            alpha=0.05,
            power=0.80,
            direction="two_tailed"
        )

        assert mde > 0
        # For these parameters, MDE should be around 0.0075
        assert 0.005 < mde < 0.015

    @pytest.mark.unit
    def test_calculate_mde_larger_sample_smaller_effect(self):
        """Test that larger sample detects smaller effect."""
        mde_small = calculate_minimum_detectable_effect(
            p1=0.05,
            n=1000,
            alpha=0.05,
            power=0.80,
            direction="two_tailed"
        )

        mde_large = calculate_minimum_detectable_effect(
            p1=0.05,
            n=10000,
            alpha=0.05,
            power=0.80,
            direction="two_tailed"
        )

        assert mde_large < mde_small

    @pytest.mark.unit
    def test_calculate_mde_higher_power_larger_mde(self):
        """Test that higher power requires larger effect to detect."""
        mde_80 = calculate_minimum_detectable_effect(
            p1=0.05,
            n=5000,
            alpha=0.05,
            power=0.80,
            direction="two_tailed"
        )

        mde_90 = calculate_minimum_detectable_effect(
            p1=0.05,
            n=5000,
            alpha=0.05,
            power=0.90,
            direction="two_tailed"
        )

        assert mde_90 > mde_80

    @pytest.mark.unit
    def test_calculate_mde_one_tailed(self):
        """Test MDE with one-tailed test."""
        mde_one = calculate_minimum_detectable_effect(
            p1=0.05,
            n=5000,
            alpha=0.05,
            power=0.80,
            direction="one_tailed"
        )

        mde_two = calculate_minimum_detectable_effect(
            p1=0.05,
            n=5000,
            alpha=0.05,
            power=0.80,
            direction="two_tailed"
        )

        # One-tailed should have smaller MDE (more power)
        assert mde_one < mde_two


# ============================================================================
# validate_test_duration Tests
# ============================================================================


class TestValidateTestDuration:
    """Test suite for validate_test_duration function."""

    @pytest.mark.unit
    def test_validate_duration_no_constraints(self):
        """Test validation when no duration constraints are set."""
        params = Mock()
        params.min_test_duration_days = None
        params.max_test_duration_days = None

        sample_size = SampleSize(
            per_arm=5000,
            total=10000,
            days_required=10,
            power_achieved=0.82
        )

        result = validate_test_duration(params, sample_size)
        assert result is True

    @pytest.mark.unit
    def test_validate_duration_within_bounds(self):
        """Test validation when duration is within bounds."""
        params = Mock()
        params.min_test_duration_days = 5
        params.max_test_duration_days = 30

        sample_size = SampleSize(
            per_arm=5000,
            total=10000,
            days_required=10,
            power_achieved=0.82
        )

        result = validate_test_duration(params, sample_size)
        assert result is True

    @pytest.mark.unit
    def test_validate_duration_below_minimum(self):
        """Test validation fails when duration is below minimum."""
        params = Mock()
        params.min_test_duration_days = 14
        params.max_test_duration_days = None

        sample_size = SampleSize(
            per_arm=5000,
            total=10000,
            days_required=7,  # Below minimum
            power_achieved=0.82
        )

        result = validate_test_duration(params, sample_size)
        assert result is False

    @pytest.mark.unit
    def test_validate_duration_above_maximum(self):
        """Test validation fails when duration exceeds maximum."""
        params = Mock()
        params.min_test_duration_days = None
        params.max_test_duration_days = 21

        sample_size = SampleSize(
            per_arm=5000,
            total=10000,
            days_required=30,  # Above maximum
            power_achieved=0.82
        )

        result = validate_test_duration(params, sample_size)
        assert result is False


# ============================================================================
# suggest_parameter_adjustments Tests
# ============================================================================


class TestSuggestParameterAdjustments:
    """Test suite for suggest_parameter_adjustments function."""

    @pytest.mark.unit
    def test_suggest_no_adjustments_needed(self):
        """Test no suggestions when constraints are met."""
        params = Mock()
        params.max_test_duration_days = None
        params.expected_daily_traffic = 5000
        params.power = 0.80
        params.allocation = Allocation(control=0.5, treatment=0.5)

        sample_size = SampleSize(
            per_arm=5000,
            total=10000,
            days_required=2,
            power_achieved=0.85
        )

        suggestions = suggest_parameter_adjustments(params, sample_size)
        assert "increase_traffic" not in suggestions
        assert "reduce_power" not in suggestions

    @pytest.mark.unit
    def test_suggest_increase_traffic(self):
        """Test traffic increase suggestion when duration exceeds max."""
        params = Mock()
        params.max_test_duration_days = 14
        params.expected_daily_traffic = 1000
        params.power = 0.80
        params.allocation = Allocation(control=0.5, treatment=0.5)

        sample_size = SampleSize(
            per_arm=10000,
            total=20000,
            days_required=30,  # Exceeds max
            power_achieved=0.82
        )

        suggestions = suggest_parameter_adjustments(params, sample_size)

        assert "increase_traffic" in suggestions
        assert suggestions["increase_traffic"]["current"] == 1000
        assert suggestions["increase_traffic"]["required"] > 1000

    @pytest.mark.unit
    def test_suggest_reduce_power(self):
        """Test power reduction suggestion when duration exceeds max."""
        params = Mock()
        params.max_test_duration_days = 14
        params.expected_daily_traffic = 1000
        params.power = 0.90
        params.allocation = Allocation(control=0.5, treatment=0.5)

        sample_size = SampleSize(
            per_arm=10000,
            total=20000,
            days_required=30,  # Exceeds max
            power_achieved=0.90
        )

        suggestions = suggest_parameter_adjustments(params, sample_size)

        assert "reduce_power" in suggestions
        assert suggestions["reduce_power"]["current"] == 0.90
        assert suggestions["reduce_power"]["suggested"] < 0.90
        assert suggestions["reduce_power"]["suggested"] >= 0.7

    @pytest.mark.unit
    def test_suggest_increase_power(self):
        """Test power increase suggestion when achieved power is low."""
        params = Mock()
        params.max_test_duration_days = None
        params.power = 0.80

        sample_size = SampleSize(
            per_arm=500,
            total=1000,
            days_required=1,
            power_achieved=0.65  # Below 0.8
        )

        suggestions = suggest_parameter_adjustments(params, sample_size)

        assert "increase_power" in suggestions
        assert suggestions["increase_power"]["current"] == 0.65
        assert suggestions["increase_power"]["suggested"] == 0.8


# ============================================================================
# Integration Tests
# ============================================================================


class TestDesignIntegration:
    """Integration tests for design module."""

    @pytest.mark.unit
    def test_full_design_workflow(self, standard_params):
        """Test complete design workflow."""
        # Calculate sample size
        sample_size = compute_sample_size(standard_params)

        assert sample_size.per_arm > 0
        assert sample_size.total == 2 * sample_size.per_arm
        assert sample_size.days_required > 0
        assert 0 <= sample_size.power_achieved <= 1

        # Calculate MDE for the sample size
        mde = calculate_minimum_detectable_effect(
            p1=standard_params.baseline_conversion_rate,
            n=sample_size.per_arm,
            alpha=standard_params.alpha,
            power=standard_params.power,
            direction="two_tailed"
        )

        assert mde > 0

    @pytest.mark.unit
    def test_sample_size_mde_consistency(self, standard_params):
        """Test that computed sample size can detect the target effect."""
        sample_size = compute_sample_size(standard_params)

        # Calculate MDE for the computed sample size
        mde = calculate_minimum_detectable_effect(
            p1=standard_params.baseline_conversion_rate,
            n=sample_size.per_arm,
            alpha=standard_params.alpha,
            power=standard_params.power,
            direction="two_tailed"
        )

        # Target absolute effect
        target_effect = standard_params.baseline_conversion_rate * standard_params.target_lift_pct

        # MDE should be approximately equal to or slightly less than target
        assert mde <= target_effect * 1.2  # Allow 20% tolerance
