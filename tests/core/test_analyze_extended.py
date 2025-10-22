"""
Extended tests for core.analyze module - comprehensive analysis testing.
"""

import pytest
from core.analyze import analyze_results
from tests.helpers.factories import (
    create_sim_result,
    create_significant_positive_result,
    create_non_significant_result
)
from tests.helpers.assertions import assert_p_value_valid, assert_confidence_interval_valid


class TestAnalysisComprehensive:
    """Comprehensive analysis tests."""
    
    @pytest.mark.unit
    @pytest.mark.parametrize("alpha", [0.01, 0.05, 0.10])
    def test_analysis_various_alphas(self, alpha):
        """Test analysis with various alpha levels."""
        result = create_significant_positive_result(seed=42)
        analysis = analyze_results(result, alpha=alpha)
        
        assert_p_value_valid(analysis.p_value)
        assert_confidence_interval_valid(analysis.confidence_interval)
        assert 0 <= analysis.power_achieved <= 1
    
    @pytest.mark.unit
    def test_analysis_different_sample_sizes(self):
        """Test analysis with different sample sizes."""
        sizes = [100, 500, 1000, 5000, 10000]
        
        for n in sizes:
            result = create_sim_result(
                control_n=n,
                control_conversions=int(n * 0.05),
                treatment_n=n,
                treatment_conversions=int(n * 0.06)
            )
            
            analysis = analyze_results(result, alpha=0.05)
            assert_p_value_valid(analysis.p_value)
    
    @pytest.mark.unit
    def test_confidence_level_consistency(self):
        """Test that confidence level matches 1-alpha."""
        result = create_significant_positive_result(seed=42)
        
        for alpha in [0.01, 0.05, 0.10]:
            analysis = analyze_results(result, alpha=alpha)
            expected_confidence = 1 - alpha
            assert analysis.confidence_level == expected_confidence
    
    @pytest.mark.unit
    def test_significance_determination(self):
        """Test that significance is properly determined."""
        # Significant result
        sig_result = create_significant_positive_result(n_per_arm=10000)
        sig_analysis = analyze_results(sig_result, alpha=0.05)
        
        if sig_analysis.p_value < 0.05:
            assert sig_analysis.significant == True
        
        # Non-significant result  
        non_sig_result = create_non_significant_result()
        non_sig_analysis = analyze_results(non_sig_result, alpha=0.05)
        
        if non_sig_analysis.p_value >= 0.05:
            assert non_sig_analysis.significant == False

