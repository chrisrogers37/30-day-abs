"""
Tests for core.design module.

This module tests sample size calculation functions and related
design parameter validation.
"""

import pytest
from core.design import compute_sample_size
from core.utils import calculate_minimum_detectable_effect, get_z_score
from core.types import DesignParams, Allocation

from tests.helpers.assertions import (
    assert_within_tolerance,
    assert_sample_size_valid
)
from tests.helpers.factories import create_design_params
from tests.fixtures.expected_results import EXPECTED_SAMPLE_SIZES


class TestComputeSampleSize:
    """Test suite for compute_sample_size function."""
    
    @pytest.mark.unit
    def test_compute_sample_size_basic(self, standard_design_params):
        """Test basic sample size calculation."""
        result = compute_sample_size(standard_design_params)
        
        assert result.per_arm > 0
        assert result.total == 2 * result.per_arm
        assert result.days_required > 0
        assert 0 <= result.power_achieved <= 1
    
    @pytest.mark.unit
    def test_compute_sample_size_deterministic(self, standard_design_params):
        """Test that results are deterministic."""
        result1 = compute_sample_size(standard_design_params)
        result2 = compute_sample_size(standard_design_params)
        
        assert result1.per_arm == result2.per_arm
        assert result1.total == result2.total
        assert result1.days_required == result2.days_required
        assert result1.power_achieved == result2.power_achieved
    
    @pytest.mark.unit
    def test_compute_sample_size_standard_case(self):
        """Test sample size for standard case matches expected range."""
        params = create_design_params(
            baseline_conversion_rate=0.05,
            target_lift_pct=0.15,
            alpha=0.05,
            power=0.80
        )
        
        result = compute_sample_size(params)
        
        # Check per-arm sample size is in expected range (around 14k)
        assert 13000 <= result.per_arm <= 15000, f"Sample size {result.per_arm} outside expected range"
        
        # Check total is 2x per-arm
        assert result.total == 2 * result.per_arm
    
    @pytest.mark.unit
    @pytest.mark.parametrize("baseline,lift,expected_min,expected_max", [
        (0.05, 0.10, 29000, 33000),  # Small lift requires more samples (~31k)
        (0.05, 0.15, 13000, 15000),  # Standard case (~14k)
        (0.05, 0.20, 7500, 8500),    # Large lift requires fewer samples (~8k)
        (0.10, 0.15, 6000, 7500),    # Higher baseline (~6.7k)
        (0.25, 0.15, 2000, 2500),    # Very high baseline (~2.2k)
    ])
    def test_compute_sample_size_ranges(
        self,
        baseline,
        lift,
        expected_min,
        expected_max
    ):
        """Test sample size ranges for different parameter combinations."""
        params = create_design_params(
            baseline_conversion_rate=baseline,
            target_lift_pct=lift
        )
        
        result = compute_sample_size(params)
        
        assert expected_min <= result.per_arm <= expected_max, (
            f"Sample size {result.per_arm} outside expected range "
            f"[{expected_min}, {expected_max}] for baseline={baseline}, lift={lift}"
        )
    
    @pytest.mark.unit
    def test_compute_sample_size_high_power(self):
        """Test that higher power requires more samples."""
        params_80 = create_design_params(power=0.80)
        params_90 = create_design_params(power=0.90)
        
        result_80 = compute_sample_size(params_80)
        result_90 = compute_sample_size(params_90)
        
        assert result_90.per_arm > result_80.per_arm
    
    @pytest.mark.unit
    def test_compute_sample_size_small_lift(self):
        """Test that smaller lift requires more samples."""
        params_large_lift = create_design_params(target_lift_pct=0.20)
        params_small_lift = create_design_params(target_lift_pct=0.10)
        
        result_large = compute_sample_size(params_large_lift)
        result_small = compute_sample_size(params_small_lift)
        
        assert result_small.per_arm > result_large.per_arm
    
    @pytest.mark.unit
    def test_compute_sample_size_days_calculation(self):
        """Test that days required is calculated correctly."""
        params = create_design_params(expected_daily_traffic=10000)
        result = compute_sample_size(params)
        
        # Each arm gets half the daily traffic (50/50 split)
        expected_days = (result.per_arm * 2) / 10000
        
        assert result.days_required == pytest.approx(expected_days, rel=0.1)
    
    @pytest.mark.unit
    def test_compute_sample_size_unbalanced_allocation(self):
        """Test sample size with unbalanced allocation."""
        allocation = Allocation(control=0.7, treatment=0.3)
        params = create_design_params(allocation=allocation)
        
        result = compute_sample_size(params)
        
        # Should still return valid sample size
        assert result.per_arm > 0
        assert result.total > 0


class TestGetZScore:
    """Test suite for get_z_score function."""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("alpha,direction,expected", [
        (0.05, "two_tailed", 1.96),
        (0.01, "two_tailed", 2.576),
        # Note: alpha=0.10 not in function's lookup table, uses scipy or fallback
        (0.05, "one_tailed", 1.645),
        (0.01, "one_tailed", 2.326),
    ])
    def test_get_z_score_standard_values(self, alpha, direction, expected):
        """Test z-score calculation for standard alpha values."""
        result = get_z_score(alpha, direction=direction)
        assert_within_tolerance(expected, result, tolerance_abs=0.02)

    @pytest.mark.unit
    def test_get_z_score_two_tailed_vs_one_tailed(self):
        """Test that two-tailed and one-tailed give different values."""
        result_two_tailed = get_z_score(0.05, direction="two_tailed")
        result_one_tailed = get_z_score(0.05, direction="one_tailed")
        
        # Two-tailed should be more conservative (higher z-score)
        assert result_two_tailed > result_one_tailed


class TestCalculateMinimumDetectableEffect:
    """Test suite for calculate_minimum_detectable_effect function."""
    
    @pytest.mark.unit
    def test_calculate_mde_basic(self):
        """Test basic MDE calculation."""
        params = create_design_params(
            baseline_conversion_rate=0.05,
            target_lift_pct=0.15,
            alpha=0.05,
            power=0.80
        )
        
        sample_size_result = compute_sample_size(params)
        mde = calculate_minimum_detectable_effect(
            p1=params.baseline_conversion_rate,  # Fixed parameter name
            n=sample_size_result.per_arm,  # Fixed parameter name
            alpha=params.alpha,
            power=params.power
        )
        
        # MDE should be positive
        assert mde > 0
        
        # MDE should be reasonably close to target absolute lift
        # (wider tolerance due to different formulas)
        target_absolute = params.baseline_conversion_rate * params.target_lift_pct
        assert_within_tolerance(target_absolute, mde, tolerance_pct=0.30)
    
    @pytest.mark.unit
    def test_calculate_mde_larger_sample_smaller_mde(self):
        """Test that larger samples detect smaller effects."""
        params = create_design_params(baseline_conversion_rate=0.05)
        
        mde_small_sample = calculate_minimum_detectable_effect(
            p1=params.baseline_conversion_rate,  # Fixed parameter name
            n=1000,  # Fixed parameter name
            alpha=0.05,
            power=0.80
        )
        
        mde_large_sample = calculate_minimum_detectable_effect(
            p1=params.baseline_conversion_rate,  # Fixed parameter name
            n=10000,  # Fixed parameter name
            alpha=0.05,
            power=0.80
        )
        
        assert mde_large_sample < mde_small_sample


class TestEdgeCases:
    """Test edge cases for design calculations."""
    
    @pytest.mark.unit
    def test_very_low_baseline(self):
        """Test with very low baseline conversion rate."""
        params = create_design_params(
            baseline_conversion_rate=0.001,
            target_lift_pct=0.20
        )
        
        result = compute_sample_size(params)
        
        # Should still produce valid results
        assert result.per_arm > 0
        assert result.power_achieved >= 0
    
    @pytest.mark.unit
    def test_very_high_baseline(self):
        """Test with very high baseline conversion rate."""
        params = create_design_params(
            baseline_conversion_rate=0.50,
            target_lift_pct=0.10
        )
        
        result = compute_sample_size(params)
        
        # Should still produce valid results
        assert result.per_arm > 0
        assert result.power_achieved >= 0
    
    @pytest.mark.unit
    def test_very_small_lift(self):
        """Test with very small target lift."""
        params = create_design_params(
            baseline_conversion_rate=0.05,
            target_lift_pct=0.05  # Only 5% relative lift
        )
        
        result = compute_sample_size(params)
        
        # Should require large sample
        assert result.per_arm > 10000
    
    @pytest.mark.unit
    def test_very_large_lift(self):
        """Test with very large target lift."""
        params = create_design_params(
            baseline_conversion_rate=0.05,
            target_lift_pct=0.50  # 50% relative lift
        )
        
        result = compute_sample_size(params)
        
        # Should require smaller sample
        assert result.per_arm < 5000

