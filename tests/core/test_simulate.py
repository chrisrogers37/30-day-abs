"""
Tests for core.simulate module - Data simulation functions.
"""

import pytest
from core.simulate import simulate_trial
from core.types import DesignParams, Allocation

from tests.helpers.assertions import (
    assert_simulation_result_valid,
    assert_within_tolerance,
    assert_probability_valid
)
from tests.helpers.factories import create_design_params


class TestSimulateTrial:
    """Test suite for simulate_trial function."""
    
    @pytest.mark.unit
    def test_simulate_trial_basic(self, standard_design_params):
        """Test basic trial simulation."""
        result = simulate_trial(standard_design_params, seed=42)
        
        assert result.control_n > 0
        assert result.treatment_n > 0
        assert result.control_conversions >= 0
        assert result.treatment_conversions >= 0
        assert_simulation_result_valid(
            result.control_n,
            result.control_conversions,
            result.treatment_n,
            result.treatment_conversions
        )
    
    @pytest.mark.unit
    def test_simulate_trial_deterministic(self, standard_design_params):
        """Test that simulation is deterministic with seed."""
        result1 = simulate_trial(standard_design_params, seed=42)
        result2 = simulate_trial(standard_design_params, seed=42)
        
        assert result1.control_n == result2.control_n
        assert result1.control_conversions == result2.control_conversions
        assert result1.treatment_n == result2.treatment_n
        assert result1.treatment_conversions == result2.treatment_conversions
    
    @pytest.mark.unit
    def test_simulate_trial_different_seeds(self, standard_design_params):
        """Test that different seeds produce different results."""
        result1 = simulate_trial(standard_design_params, seed=42)
        result2 = simulate_trial(standard_design_params, seed=43)
        
        # Results should differ (with high probability)
        assert (result1.control_conversions != result2.control_conversions or
                result1.treatment_conversions != result2.treatment_conversions)
    
    @pytest.mark.unit
    def test_simulate_trial_respects_allocation(self):
        """Test that simulation respects allocation ratio."""
        allocation = Allocation(control=0.7, treatment=0.3)
        params = create_design_params(
            allocation=allocation,
            expected_daily_traffic=10000
        )
        
        result = simulate_trial(params, seed=42)
        
        total_n = result.control_n + result.treatment_n
        control_ratio = result.control_n / total_n
        treatment_ratio = result.treatment_n / total_n
        
        assert_within_tolerance(0.7, control_ratio, tolerance_pct=0.05)
        assert_within_tolerance(0.3, treatment_ratio, tolerance_pct=0.05)
    
    @pytest.mark.unit
    def test_simulate_trial_conversion_rates(self, standard_design_params):
        """Test that conversion rates are reasonable."""
        result = simulate_trial(standard_design_params, seed=42)
        
        assert_probability_valid(result.control_rate)
        assert_probability_valid(result.treatment_rate)
    
    @pytest.mark.unit
    def test_simulate_trial_treatment_effect_variation(self):
        """Test that treatment effect shows realistic variation."""
        params = create_design_params(
            baseline_conversion_rate=0.05,
            target_lift_pct=0.20
        )
        
        # Run multiple simulations
        results = [simulate_trial(params, seed=i) for i in range(10)]
        
        # All should have valid rates
        for result in results:
            assert_probability_valid(result.control_rate)
            assert_probability_valid(result.treatment_rate)
        
        # There should be variation in results
        treatment_rates = [r.treatment_rate for r in results]
        assert len(set(treatment_rates)) > 1  # Not all the same
    
    @pytest.mark.unit
    def test_simulate_trial_sample_size(self):
        """Test that sample sizes are calculated correctly."""
        params = create_design_params(expected_daily_traffic=10000)
        result = simulate_trial(params, seed=42)
        
        # Total sample should be reasonable given traffic
        total_n = result.control_n + result.treatment_n
        assert total_n > 0


class TestEdgeCases:
    """Test edge cases for simulation."""
    
    @pytest.mark.unit
    def test_simulate_very_low_baseline(self):
        """Test simulation with very low baseline rate."""
        params = create_design_params(
            baseline_conversion_rate=0.001,
            target_lift_pct=0.50
        )
        
        result = simulate_trial(params, seed=42)
        
        assert_simulation_result_valid(
            result.control_n,
            result.control_conversions,
            result.treatment_n,
            result.treatment_conversions
        )
    
    @pytest.mark.unit
    def test_simulate_very_high_baseline(self):
        """Test simulation with very high baseline rate."""
        params = create_design_params(
            baseline_conversion_rate=0.50,
            target_lift_pct=0.10
        )
        
        result = simulate_trial(params, seed=42)
        
        assert_simulation_result_valid(
            result.control_n,
            result.control_conversions,
            result.treatment_n,
            result.treatment_conversions
        )
    
    @pytest.mark.unit
    def test_simulate_small_traffic(self):
        """Test simulation with small daily traffic."""
        params = create_design_params(expected_daily_traffic=1000)
        
        result = simulate_trial(params, seed=42)
        
        assert result.control_n + result.treatment_n > 0
    
    @pytest.mark.unit
    def test_simulate_large_traffic(self):
        """Test simulation with large daily traffic."""
        params = create_design_params(expected_daily_traffic=100000)
        
        result = simulate_trial(params, seed=42)
        
        assert result.control_n + result.treatment_n > 0

