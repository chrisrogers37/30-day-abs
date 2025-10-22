"""
Integration tests for complete quiz workflow.
"""

import pytest
from core.design import compute_sample_size
from core.simulate import simulate_trial
from core.analyze import analyze_results
from tests.helpers.factories import create_design_params


class TestCompleteWorkflow:
    """Test complete workflow from design to analysis."""
    
    @pytest.mark.integration
    def test_complete_quiz_flow(self):
        """Test complete quiz flow: design → simulate → analyze."""
        # Step 1: Design
        params = create_design_params()
        sample_size = compute_sample_size(params)
        
        assert sample_size.per_arm > 0
        
        # Step 2: Simulate
        sim_result = simulate_trial(params, seed=42)
        
        assert sim_result.control_n > 0
        assert sim_result.treatment_n > 0
        
        # Step 3: Analyze
        analysis = analyze_results(sim_result, alpha=params.alpha)
        
        assert 0 <= analysis.p_value <= 1
        assert len(analysis.confidence_interval) == 2

