"""
Extended tests for core.utils module - comprehensive utility testing.
"""

import pytest
from core.utils import (
    calculate_confidence_interval_for_revenue,
    calculate_conversion_rate_confidence_interval,
    calculate_relative_lift_confidence_interval,
    calculate_conversion_rate_standard_error,
    calculate_required_sample_size_for_power
)
from tests.helpers.assertions import assert_confidence_interval_valid, assert_within_tolerance


class TestAdditionalConfidenceIntervals:
    """Test additional CI calculation functions."""
    
    @pytest.mark.unit
    def test_calculate_conversion_rate_confidence_interval(self):
        """Test conversion rate CI calculation."""
        ci = calculate_conversion_rate_confidence_interval(
            p=0.05,
            n=1000,
            confidence_level=0.95
        )
        
        assert_confidence_interval_valid(ci, point_estimate=0.05)
    
    @pytest.mark.unit
    def test_calculate_relative_lift_confidence_interval(self):
        """Test relative lift CI calculation."""
        ci = calculate_relative_lift_confidence_interval(
            control_rate=0.05,
            treatment_rate=0.06,
            control_n=1000,
            treatment_n=1000,
            confidence_level=0.95
        )
        
        assert len(ci) == 2
        assert ci[0] < ci[1]
    
    @pytest.mark.unit
    def test_calculate_confidence_interval_for_revenue(self):
        """Test revenue CI calculation."""
        ci = calculate_confidence_interval_for_revenue(
            revenue_impact=10000.0,
            confidence_level=0.95
        )
        
        assert len(ci) == 2
        assert ci[0] < 10000.0 < ci[1]
    
    @pytest.mark.unit
    def test_conversion_rate_standard_error(self):
        """Test standard error calculation."""
        se = calculate_conversion_rate_standard_error(p=0.05, n=1000)
        
        expected = (0.05 * 0.95 / 1000) ** 0.5
        assert_within_tolerance(expected, se, tolerance_pct=0.01)
    
    @pytest.mark.unit
    def test_standard_error_zero_sample(self):
        """Test SE with zero sample size."""
        se = calculate_conversion_rate_standard_error(p=0.05, n=0)
        assert se == 0.0


class TestSampleSizeForPower:
    """Test required sample size for power calculations."""
    
    @pytest.mark.unit
    def test_calculate_required_sample_size(self):
        """Test sample size calculation for given power."""
        n = calculate_required_sample_size_for_power(
            p1=0.05,
            p2=0.06,
            alpha=0.05,
            power=0.80
        )
        
        assert n > 0
        assert isinstance(n, int)
    
    @pytest.mark.unit
    def test_larger_effect_smaller_sample(self):
        """Test that larger effect sizes need smaller samples."""
        n_small_effect = calculate_required_sample_size_for_power(
            p1=0.05,
            p2=0.055,  # Small effect
            alpha=0.05,
            power=0.80
        )
        
        n_large_effect = calculate_required_sample_size_for_power(
            p1=0.05,
            p2=0.075,  # Larger effect
            alpha=0.05,
            power=0.80
        )
        
        assert n_large_effect < n_small_effect

