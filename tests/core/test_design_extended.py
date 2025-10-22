"""
Extended tests for core.design module - comprehensive design testing.
"""

import pytest
from core.design import compute_sample_size
from tests.helpers.factories import create_design_params
from tests.helpers.assertions import assert_within_tolerance


class TestDesignEdgeCasesExtended:
    """Extended edge case testing for design calculations."""
    
    @pytest.mark.unit
    def test_unbalanced_allocation_calculations(self):
        """Test calculations with various unbalanced allocations."""
        from core.types import Allocation
        
        for control_pct in [0.6, 0.7, 0.8, 0.9]:
            treatment_pct = 1.0 - control_pct
            allocation = Allocation(control=control_pct, treatment=treatment_pct)
            
            params = create_design_params(allocation=allocation)
            result = compute_sample_size(params)
            
            assert result.per_arm > 0
            assert result.total > 0
            assert result.days_required > 0
    
    @pytest.mark.unit
    def test_very_high_power_requirements(self):
        """Test with very high power requirements."""
        params = create_design_params(power=0.95)
        result = compute_sample_size(params)
        
        # Very high power should require more samples
        params_normal = create_design_params(power=0.80)
        result_normal = compute_sample_size(params_normal)
        
        assert result.per_arm > result_normal.per_arm
    
    @pytest.mark.unit
    def test_very_low_alpha(self):
        """Test with very stringent alpha."""
        params = create_design_params(alpha=0.01)
        result = compute_sample_size(params)
        
        # Lower alpha should require more samples
        params_normal = create_design_params(alpha=0.05)
        result_normal = compute_sample_size(params_normal)
        
        assert result.per_arm > result_normal.per_arm
    
    @pytest.mark.unit
    @pytest.mark.parametrize("baseline", [0.001, 0.01, 0.02, 0.05, 0.10, 0.20, 0.30, 0.40])
    def test_various_baseline_rates(self, baseline):
        """Test sample size calculation with various baseline rates."""
        params = create_design_params(baseline_conversion_rate=baseline, target_lift_pct=0.15)
        result = compute_sample_size(params)
        
        # All should produce valid results
        assert result.per_arm > 0
        assert 0 <= result.power_achieved <= 1

