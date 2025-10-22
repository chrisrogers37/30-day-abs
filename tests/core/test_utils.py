"""
Tests for core.utils module - Utility functions.
"""

import pytest
from core.utils import (
    relative_lift_to_absolute,
    absolute_lift_to_relative,
    format_percentage
)
from tests.helpers.assertions import assert_within_tolerance


class TestLiftConversions:
    """Test suite for lift conversion functions."""
    
    @pytest.mark.unit
    def test_relative_lift_to_absolute(self):
        """Test conversion from relative to absolute lift."""
        baseline = 0.05
        relative_lift_pct = 20.0  # 20% as percentage, not decimal
        
        absolute_lift = relative_lift_to_absolute(baseline, relative_lift_pct)
        
        expected = baseline * (relative_lift_pct / 100)  # Function divides by 100
        assert_within_tolerance(expected, absolute_lift)
    
    @pytest.mark.unit
    def test_absolute_lift_to_relative(self):
        """Test conversion from absolute to relative lift."""
        baseline = 0.05
        absolute_lift = 0.01
        
        relative_lift = absolute_lift_to_relative(baseline, absolute_lift)
        
        expected = (absolute_lift / baseline) * 100  # Function returns percentage
        assert_within_tolerance(expected, relative_lift)
    
    @pytest.mark.unit
    def test_lift_conversion_roundtrip(self):
        """Test that conversions are reversible."""
        baseline = 0.05
        original_relative_pct = 20.0  # Percentage
        
        # Convert to absolute and back
        absolute = relative_lift_to_absolute(baseline, original_relative_pct)
        back_to_relative = absolute_lift_to_relative(baseline, absolute)
        
        assert_within_tolerance(original_relative_pct, back_to_relative)


class TestFormatting:
    """Test suite for formatting functions."""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("value,expected", [
        (0.05, "5.00%"),  # format_percentage uses 2 decimals by default
        (0.15, "15.00%"),
        (0.005, "0.50%"),
        (1.0, "100.00%"),
    ])
    def test_format_percentage(self, value, expected):
        """Test percentage formatting."""
        result = format_percentage(value)
        assert result == expected
    
    @pytest.mark.unit
    def test_format_percentage_custom_decimals(self):
        """Test percentage formatting with custom decimals."""
        from core.utils import format_percentage
        result = format_percentage(0.12345, decimals=3)
        assert result == "12.345%"
    
    @pytest.mark.unit
    def test_format_currency(self):
        """Test currency formatting."""
        from core.utils import format_currency
        
        assert format_currency(1500) == "$1.5K"
        assert format_currency(1500000) == "$1.5M"
        assert format_currency(50) == "$50.00"
    
    @pytest.mark.unit
    def test_format_large_number(self):
        """Test large number formatting."""
        from core.utils import format_large_number
        
        assert format_large_number(1500) == "1.5K"
        assert format_large_number(1500000) == "1.5M"
        assert format_large_number(1500000000) == "1.5B"
        assert format_large_number(50) == "50"


class TestConfidenceIntervals:
    """Test suite for confidence interval functions."""
    
    @pytest.mark.unit
    def test_calculate_confidence_interval_for_proportion(self):
        """Test CI calculation for single proportion."""
        from core.utils import calculate_confidence_interval_for_proportion
        
        ci = calculate_confidence_interval_for_proportion(
            p=0.05,
            n=1000,
            confidence_level=0.95
        )
        
        assert len(ci) == 2
        assert ci[0] < 0.05 < ci[1]
        assert ci[0] >= 0  # Lower bound non-negative
        assert ci[1] <= 1  # Upper bound <= 1
    
    @pytest.mark.unit
    def test_calculate_confidence_interval_for_difference(self):
        """Test CI calculation for difference in proportions."""
        from core.utils import calculate_confidence_interval_for_difference
        
        ci = calculate_confidence_interval_for_difference(
            p1=0.05,
            p2=0.06,
            n1=1000,
            n2=1000,
            confidence_level=0.95
        )
        
        assert len(ci) == 2
        assert ci[0] < ci[1]
    
    @pytest.mark.unit
    def test_confidence_interval_zero_sample(self):
        """Test CI with zero sample size."""
        from core.utils import calculate_confidence_interval_for_proportion
        
        ci = calculate_confidence_interval_for_proportion(p=0.05, n=0)
        assert ci == (0.0, 0.0)


class TestEffectSize:
    """Test suite for effect size calculations."""
    
    @pytest.mark.unit
    def test_cohens_h_calculation(self):
        """Test Cohen's h effect size calculation."""
        from core.utils import calculate_effect_size_cohens_h
        
        h = calculate_effect_size_cohens_h(p1=0.10, p2=0.15)
        
        # Cohen's h should be reasonable
        assert -2.0 < h < 2.0
    
    @pytest.mark.unit
    def test_cohens_h_interpretation(self):
        """Test Cohen's h interpretation."""
        from core.utils import interpret_effect_size_cohens_h
        
        assert interpret_effect_size_cohens_h(0.1) == "small"
        assert interpret_effect_size_cohens_h(0.4) == "medium"
        assert interpret_effect_size_cohens_h(0.8) == "large"
    
    @pytest.mark.unit
    def test_cohens_d_calculation(self):
        """Test Cohen's d effect size calculation."""
        from core.utils import calculate_effect_size_cohens_d
        
        d = calculate_effect_size_cohens_d(mean1=10.0, mean2=12.0, pooled_std=5.0)
        
        expected = (12.0 - 10.0) / 5.0
        assert_within_tolerance(expected, d)
    
    @pytest.mark.unit
    def test_cohens_d_interpretation(self):
        """Test Cohen's d interpretation."""
        from core.utils import interpret_effect_size_cohens_d
        
        assert interpret_effect_size_cohens_d(0.1) == "small"
        assert interpret_effect_size_cohens_d(0.4) == "medium"
        assert interpret_effect_size_cohens_d(0.6) == "large"
        assert interpret_effect_size_cohens_d(1.0) == "very large"


class TestPowerCalculations:
    """Test suite for power calculations."""
    
    @pytest.mark.unit
    def test_calculate_power_for_proportions(self):
        """Test power calculation for proportions."""
        from core.utils import calculate_power_for_proportions
        
        power = calculate_power_for_proportions(
            p1=0.05,
            p2=0.06,
            n=10000,
            alpha=0.05
        )
        
        assert 0 <= power <= 1
        assert power > 0.5  # Should have decent power with large n


class TestValidationFunctions:
    """Test suite for validation helper functions."""
    
    @pytest.mark.unit
    def test_validate_conversion_rate(self):
        """Test conversion rate validation."""
        from core.utils import validate_conversion_rate
        
        assert validate_conversion_rate(0.05) == True
        assert validate_conversion_rate(0.0) == True
        assert validate_conversion_rate(1.0) == True
        assert validate_conversion_rate(-0.1) == False
        assert validate_conversion_rate(1.5) == False
    
    @pytest.mark.unit
    def test_validate_sample_size(self):
        """Test sample size validation."""
        from core.utils import validate_sample_size
        
        assert validate_sample_size(100) == True
        assert validate_sample_size(1) == True
        assert validate_sample_size(0) == False
        assert validate_sample_size(-10) == False
    
    @pytest.mark.unit
    def test_validate_confidence_level(self):
        """Test confidence level validation."""
        from core.utils import validate_confidence_level
        
        assert validate_confidence_level(0.95) == True
        assert validate_confidence_level(0.99) == True
        assert validate_confidence_level(0.0) == False
        assert validate_confidence_level(1.0) == False
        assert validate_confidence_level(1.5) == False
    
    @pytest.mark.unit
    def test_validate_significance_level(self):
        """Test significance level validation."""
        from core.utils import validate_significance_level
        
        assert validate_significance_level(0.05) == True
        assert validate_significance_level(0.01) == True
        assert validate_significance_level(0.0) == False
        assert validate_significance_level(1.0) == False
    
    @pytest.mark.unit
    def test_validate_power(self):
        """Test power validation."""
        from core.utils import validate_power
        
        assert validate_power(0.80) == True
        assert validate_power(0.90) == True
        assert validate_power(0.0) == False
        assert validate_power(1.0) == False


class TestRevenueCalculations:
    """Test suite for revenue calculation functions."""
    
    @pytest.mark.unit
    def test_calculate_revenue_impact(self):
        """Test revenue impact calculation."""
        from core.utils import calculate_revenue_impact
        
        revenue = calculate_revenue_impact(
            conversion_rate=0.05,
            traffic_volume=10000,
            revenue_per_conversion=50.0
        )
        
        expected = 0.05 * 10000 * 50.0
        assert_within_tolerance(expected, revenue)
    
    @pytest.mark.unit
    def test_calculate_monthly_revenue_impact(self):
        """Test monthly revenue impact calculation."""
        from core.utils import calculate_monthly_revenue_impact
        
        monthly_revenue = calculate_monthly_revenue_impact(
            conversion_rate=0.05,
            daily_traffic=1000,
            revenue_per_conversion=100.0,
            days_per_month=30
        )
        
        expected = 0.05 * 1000 * 30 * 100.0
        assert_within_tolerance(expected, monthly_revenue)

