"""
Extended tests for core.simulate module - comprehensive simulation testing.
"""

import pytest
from core.simulate import simulate_trial
from tests.helpers.factories import create_design_params
from tests.helpers.assertions import assert_simulation_result_valid


class TestSimulateVariousScenarios:
    """Test simulation with various realistic scenarios."""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("baseline,lift", [
        (0.01, 0.20),
        (0.05, 0.15),
        (0.10, 0.25),
        (0.20, 0.10),
        (0.30, 0.15),
    ])
    def test_simulate_various_params(self, baseline, lift):
        """Test simulation with various parameter combinations."""
        params = create_design_params(
            baseline_conversion_rate=baseline,
            target_lift_pct=lift
        )
        
        result = simulate_trial(params, seed=42)
        
        assert_simulation_result_valid(
            result.control_n,
            result.control_conversions,
            result.treatment_n,
            result.treatment_conversions
        )
    
    @pytest.mark.unit
    def test_simulate_reproducibility_multiple_runs(self):
        """Test that multiple simulations with same seed are identical."""
        params = create_design_params()
        
        results = [simulate_trial(params, seed=42) for _ in range(5)]
        
        # All should be identical
        for result in results[1:]:
            assert result.control_n == results[0].control_n
            assert result.control_conversions == results[0].control_conversions
            assert result.treatment_n == results[0].treatment_n
            assert result.treatment_conversions == results[0].treatment_conversions
    
    @pytest.mark.unit
    def test_simulate_variability_different_seeds(self):
        """Test that different seeds produce different but valid results."""
        params = create_design_params()
        
        results = [simulate_trial(params, seed=i) for i in range(10)]
        
        # Should have some variability in results
        control_rates = [r.control_rate for r in results]
        assert len(set(control_rates)) > 1  # Not all identical
        
        # But all should be valid
        for result in results:
            assert 0 <= result.control_rate <= 1
            assert 0 <= result.treatment_rate <= 1

