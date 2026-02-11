"""
Tests for core.types module.

This module tests the core domain types and their validation logic.
"""

import pytest
from core.types import Allocation, DesignParams, SimResult

from tests.helpers.assertions import assert_allocation_valid


class TestAllocation:
    """Test suite for Allocation class."""
    
    @pytest.mark.unit
    def test_allocation_creation_valid(self):
        """Test creating valid allocation."""
        allocation = Allocation(control=0.5, treatment=0.5)
        
        assert allocation.control == 0.5
        assert allocation.treatment == 0.5
        assert allocation.total == 1.0
    
    @pytest.mark.unit
    def test_allocation_total_property(self):
        """Test total property calculation."""
        allocation = Allocation(control=0.7, treatment=0.3)
        
        assert allocation.total == pytest.approx(1.0)
    
    @pytest.mark.unit
    @pytest.mark.parametrize("control,treatment", [
        (0.5, 0.5),
        (0.6, 0.4),
        (0.7, 0.3),
        (0.8, 0.2),
        (0.9, 0.1),
    ])
    def test_allocation_various_splits(self, control, treatment):
        """Test various allocation splits."""
        allocation = Allocation(control=control, treatment=treatment)
        
        assert allocation.control == control
        assert allocation.treatment == treatment
        assert_allocation_valid(control, treatment)
    
    @pytest.mark.unit
    def test_allocation_validation_sum(self):
        """Test allocation validation requires sum to 1."""
        # This should work
        allocation = Allocation(control=0.5, treatment=0.5)
        assert abs(allocation.total - 1.0) < 1e-6
    
    @pytest.mark.unit
    def test_allocation_immutable(self):
        """Test that allocation is immutable (frozen dataclass)."""
        allocation = Allocation(control=0.5, treatment=0.5)
        
        with pytest.raises(AttributeError):
            allocation.control = 0.6


class TestDesignParams:
    """Test suite for DesignParams class."""
    
    @pytest.mark.unit
    def test_design_params_creation_valid(self, standard_allocation):
        """Test creating valid design parameters."""
        params = DesignParams(
            baseline_conversion_rate=0.05,
            target_lift_pct=0.15,
            alpha=0.05,
            power=0.8,
            allocation=standard_allocation,
            expected_daily_traffic=10000
        )
        
        assert params.baseline_conversion_rate == 0.05
        assert params.target_lift_pct == 0.15
        assert params.alpha == 0.05
        assert params.power == 0.8
        assert params.expected_daily_traffic == 10000
    
    @pytest.mark.unit
    def test_design_params_all_fields_required(self, standard_allocation):
        """Test that all fields are required."""
        # Missing fields should raise TypeError
        with pytest.raises(TypeError):
            DesignParams(
                baseline_conversion_rate=0.05,
                target_lift_pct=0.15
                # Missing other required fields
            )
    
    @pytest.mark.unit
    def test_design_params_immutable(self, standard_allocation):
        """Test that design params are immutable."""
        params = DesignParams(
            baseline_conversion_rate=0.05,
            target_lift_pct=0.15,
            alpha=0.05,
            power=0.8,
            allocation=standard_allocation,
            expected_daily_traffic=10000
        )
        
        with pytest.raises(AttributeError):
            params.baseline_conversion_rate = 0.10
    
    @pytest.mark.unit
    def test_design_params_nested_allocation(self):
        """Test nested allocation object."""
        allocation = Allocation(control=0.6, treatment=0.4)
        params = DesignParams(
            baseline_conversion_rate=0.05,
            target_lift_pct=0.15,
            alpha=0.05,
            power=0.8,
            allocation=allocation,
            expected_daily_traffic=10000
        )
        
        assert params.allocation.control == 0.6
        assert params.allocation.treatment == 0.4


class TestSimResult:
    """Test suite for SimResult class."""
    
    @pytest.mark.unit
    def test_sim_result_creation_valid(self):
        """Test creating valid simulation result."""
        result = SimResult(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )
        
        assert result.control_n == 1000
        assert result.control_conversions == 50
        assert result.treatment_n == 1000
        assert result.treatment_conversions == 60
    
    @pytest.mark.unit
    def test_sim_result_control_rate_property(self):
        """Test control_rate calculated property."""
        result = SimResult(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )
        
        expected_rate = 50 / 1000
        assert result.control_rate == expected_rate
    
    @pytest.mark.unit
    def test_sim_result_treatment_rate_property(self):
        """Test treatment_rate calculated property."""
        result = SimResult(
            control_n=1000,
            control_conversions=60,
            treatment_n=1000,
            treatment_conversions=75
        )
        
        expected_rate = 75 / 1000
        assert result.treatment_rate == expected_rate
    
    @pytest.mark.unit
    def test_sim_result_absolute_lift_property(self):
        """Test absolute_lift calculated property."""
        result = SimResult(
            control_n=1000,
            control_conversions=50,  # 5%
            treatment_n=1000,
            treatment_conversions=60  # 6%
        )
        
        expected_lift = 0.06 - 0.05
        assert result.absolute_lift == pytest.approx(expected_lift)
    
    @pytest.mark.unit
    def test_sim_result_relative_lift_pct_property(self):
        """Test relative_lift_pct calculated property."""
        result = SimResult(
            control_n=1000,
            control_conversions=50,  # 5%
            treatment_n=1000,
            treatment_conversions=60  # 6%
        )
        
        # Relative lift = (6% - 5%) / 5% = 20%
        expected_relative_lift = (0.06 - 0.05) / 0.05
        assert result.relative_lift_pct == pytest.approx(expected_relative_lift)
    
    @pytest.mark.unit
    def test_sim_result_zero_control_rate(self):
        """Test behavior with zero control conversions."""
        result = SimResult(
            control_n=1000,
            control_conversions=0,
            treatment_n=1000,
            treatment_conversions=10
        )
        
        assert result.control_rate == 0.0
        assert result.absolute_lift == 0.01
    
    @pytest.mark.unit
    def test_sim_result_perfect_conversion(self):
        """Test behavior with 100% conversion."""
        result = SimResult(
            control_n=100,
            control_conversions=100,
            treatment_n=100,
            treatment_conversions=100
        )
        
        assert result.control_rate == 1.0
        assert result.treatment_rate == 1.0
        assert result.absolute_lift == 0.0
    
    @pytest.mark.unit
    def test_sim_result_negative_lift(self):
        """Test behavior with negative lift."""
        result = SimResult(
            control_n=1000,
            control_conversions=60,  # 6%
            treatment_n=1000,
            treatment_conversions=50  # 5%
        )
        
        assert result.absolute_lift < 0
        assert result.relative_lift_pct < 0
    
    @pytest.mark.unit
    def test_sim_result_with_user_data(self):
        """Test simulation result with user data."""
        user_data = [
            {"user_id": "1", "group": "control", "converted": True},
            {"user_id": "2", "group": "treatment", "converted": False}
        ]
        
        result = SimResult(
            control_n=100,
            control_conversions=10,
            treatment_n=100,
            treatment_conversions=15,
            user_data=user_data
        )
        
        assert result.user_data is not None
        assert len(result.user_data) == 2
    
    @pytest.mark.unit
    def test_sim_result_immutable(self):
        """Test that SimResult is immutable."""
        result = SimResult(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )
        
        with pytest.raises(AttributeError):
            result.control_n = 2000


class TestEdgeCases:
    """Test edge cases for types."""
    
    @pytest.mark.unit
    def test_allocation_extreme_split(self):
        """Test allocation with extreme splits."""
        # 95/5 split
        allocation = Allocation(control=0.95, treatment=0.05)
        assert allocation.total == pytest.approx(1.0)
        
        # 5/95 split
        allocation = Allocation(control=0.05, treatment=0.95)
        assert allocation.total == pytest.approx(1.0)
    
    @pytest.mark.unit
    def test_sim_result_tiny_sample(self):
        """Test simulation result with tiny sample size."""
        result = SimResult(
            control_n=10,
            control_conversions=1,
            treatment_n=10,
            treatment_conversions=2
        )
        
        assert result.control_rate == 0.1
        assert result.treatment_rate == 0.2
    
    @pytest.mark.unit
    def test_sim_result_large_sample(self):
        """Test simulation result with large sample size."""
        result = SimResult(
            control_n=1000000,
            control_conversions=50000,
            treatment_n=1000000,
            treatment_conversions=52500
        )
        
        assert result.control_rate == 0.05
        assert result.treatment_rate == 0.0525
        assert result.absolute_lift == pytest.approx(0.0025)

