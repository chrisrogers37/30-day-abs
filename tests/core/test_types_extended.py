"""
Extended tests for core.types edge cases and validation.

Tests for property validation, immutability, and edge case handling.
"""

import pytest
from core.types import Allocation
from tests.helpers.factories import create_design_params


class TestAllocationEdgeCases:
    """Extended edge case tests for Allocation."""
    
    @pytest.mark.unit
    def test_allocation_precision(self):
        """Test allocation with floating point precision issues."""
        # Test that allocations handle floating point precision
        allocation = Allocation(control=0.33333333, treatment=0.66666667)
        
        # Total should be very close to 1.0
        assert abs(allocation.total - 1.0) < 0.0001
    
    @pytest.mark.unit
    def test_allocation_minimal_split(self):
        """Test allocation with minimal treatment group."""
        allocation = Allocation(control=0.99, treatment=0.01)
        
        assert allocation.control == 0.99
        assert allocation.treatment == 0.01
        assert abs(allocation.total - 1.0) < 1e-10


class TestDesignParamsValidation:
    """Extended validation tests for DesignParams."""
    
    @pytest.mark.unit
    def test_design_params_boundary_values(self):
        """Test design params with boundary values."""
        # Test with minimum valid values
        params = create_design_params(
            baseline_conversion_rate=0.001,  # Very low
            target_lift_pct=0.05,  # Small
            alpha=0.01,  # Stringent
            power=0.70,  # Lower bound
            expected_daily_traffic=1000  # Minimum
        )
        
        assert params.baseline_conversion_rate == 0.001
        assert params.power == 0.70
    
    @pytest.mark.unit
    def test_design_params_maximum_values(self):
        """Test design params with maximum valid values."""
        params = create_design_params(
            baseline_conversion_rate=0.50,  # Very high
            target_lift_pct=0.50,  # Large
            alpha=0.10,  # Lenient
            power=0.95,  # High
            expected_daily_traffic=1000000  # Very large
        )
        
        assert params.baseline_conversion_rate == 0.50
        assert params.power == 0.95


class TestSampleSizeType:
    """Extended tests for SampleSize type."""
    
    @pytest.mark.unit
    def test_sample_size_consistency(self):
        """Test that SampleSize maintains consistency."""
        from core.design import compute_sample_size
        
        params = create_design_params()
        result = compute_sample_size(params)
        
        # Total should always be 2x per_arm
        assert result.total == 2 * result.per_arm
        
        # Days required should be consistent with per_arm and traffic
        expected_days = (result.per_arm * 2) / params.expected_daily_traffic
        assert result.days_required >= expected_days - 1  # Allow rounding
    
    @pytest.mark.unit
    def test_sample_size_power_achieved(self):
        """Test that power_achieved is reasonable."""
        from core.design import compute_sample_size
        
        params = create_design_params(power=0.80)
        result = compute_sample_size(params)
        
        # Achieved power should be at least target power (may be higher due to rounding)
        assert result.power_achieved >= params.power - 0.05  # Small tolerance
        assert result.power_achieved <= 1.0


class TestSimResultProperties:
    """Extended tests for SimResult calculated properties."""
    
    @pytest.mark.unit
    def test_sim_result_rate_calculations(self):
        """Test that rate calculations are accurate."""
        from tests.helpers.factories import create_sim_result
        
        result = create_sim_result(
            control_n=1000,
            control_conversions=123,
            treatment_n=2000,
            treatment_conversions=456
        )
        
        # Verify exact calculations
        assert result.control_rate == 123 / 1000
        assert result.treatment_rate == 456 / 2000
    
    @pytest.mark.unit
    def test_sim_result_lift_calculations(self):
        """Test lift calculations are accurate."""
        from tests.helpers.factories import create_sim_result
        
        result = create_sim_result(
            control_n=1000,
            control_conversions=50,  # 5%
            treatment_n=1000,
            treatment_conversions=60  # 6%
        )
        
        # Verify lift calculations
        expected_absolute = 0.06 - 0.05
        expected_relative = (0.06 - 0.05) / 0.05
        
        assert abs(result.absolute_lift - expected_absolute) < 0.0001
        assert abs(result.relative_lift_pct - expected_relative) < 0.0001


class TestAnalysisResultStructure:
    """Extended tests for AnalysisResult structure."""
    
    @pytest.mark.unit
    def test_analysis_result_has_all_fields(self):
        """Test that AnalysisResult has all expected fields."""
        from core.analyze import analyze_results
        from tests.helpers.factories import create_significant_positive_result
        
        sim_result = create_significant_positive_result(seed=42)
        analysis = analyze_results(sim_result, alpha=0.05)
        
        # Check all expected attributes exist
        required_attrs = [
            'test_statistic',
            'p_value',
            'confidence_interval',
            'confidence_level',
            'significant',
            'effect_size',
            'power_achieved',
            'recommendation'
        ]
        
        for attr in required_attrs:
            assert hasattr(analysis, attr), f"Missing attribute: {attr}"

