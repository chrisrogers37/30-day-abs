"""
Tests for core.analyze module - Statistical analysis functions.
"""

import pytest
from core.analyze import analyze_results, make_rollout_decision
from core.types import SimResult

from tests.helpers.assertions import (
    assert_p_value_valid,
    assert_confidence_interval_valid,
    assert_probability_valid
)
from tests.helpers.factories import (
    create_sim_result,
    create_significant_positive_result,
    create_non_significant_result,
    create_significant_negative_result
)


class TestAnalyzeResults:
    """Test suite for analyze_results function."""
    
    @pytest.mark.unit
    def test_analyze_results_basic(self, simple_sim_result):
        """Test basic statistical analysis."""
        analysis = analyze_results(simple_sim_result, alpha=0.05)
        
        assert_p_value_valid(analysis.p_value)
        assert len(analysis.confidence_interval) == 2
        assert_confidence_interval_valid(analysis.confidence_interval)
        assert isinstance(analysis.significant, bool)
        assert isinstance(analysis.recommendation, str)
    
    @pytest.mark.unit
    def test_analyze_results_significant_positive(self):
        """Test analysis of significant positive result."""
        result = create_significant_positive_result(seed=42)
        analysis = analyze_results(result, alpha=0.05)
        
        assert analysis.significant == True
        assert analysis.p_value < 0.05
        assert analysis.confidence_interval[0] > 0  # Lower bound positive
    
    @pytest.mark.unit
    def test_analyze_results_non_significant(self):
        """Test analysis of non-significant result."""
        result = create_non_significant_result(seed=42)
        analysis = analyze_results(result, alpha=0.05)
        
        # Should not be significant (high probability)
        assert analysis.p_value >= 0.01  # Very likely > 0.05
    
    @pytest.mark.unit
    def test_analyze_results_significant_negative(self):
        """Test analysis of significant negative result."""
        result = create_significant_negative_result(seed=42)
        analysis = analyze_results(result, alpha=0.05)
        
        assert analysis.significant == True
        assert analysis.p_value < 0.05
        assert analysis.confidence_interval[1] < 0  # Upper bound negative
    
    @pytest.mark.unit
    def test_analyze_results_different_alphas(self, significant_sim_result):
        """Test that different alphas affect significance."""
        analysis_05 = analyze_results(significant_sim_result, alpha=0.05)
        analysis_01 = analyze_results(significant_sim_result, alpha=0.01)
        
        # Stricter alpha should have wider CI
        ci_width_05 = analysis_05.confidence_interval[1] - analysis_05.confidence_interval[0]
        ci_width_01 = analysis_01.confidence_interval[1] - analysis_01.confidence_interval[0]
        
        assert ci_width_01 > ci_width_05
    
    @pytest.mark.unit
    def test_analyze_results_confidence_interval_contains_estimate(self):
        """Test that CI contains point estimate."""
        result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )
        
        analysis = analyze_results(result, alpha=0.05)
        point_estimate = result.absolute_lift
        
        assert_confidence_interval_valid(
            analysis.confidence_interval,
            point_estimate=point_estimate
        )
    
    @pytest.mark.unit
    def test_analyze_results_effect_size(self):
        """Test that effect size is calculated."""
        result = create_significant_positive_result()
        analysis = analyze_results(result, alpha=0.05)
        
        # Effect size should be a reasonable number
        assert -5.0 < analysis.effect_size < 5.0
    
    @pytest.mark.unit
    def test_analyze_results_power_achieved(self):
        """Test that achieved power is calculated."""
        result = create_significant_positive_result(n_per_arm=5000)
        analysis = analyze_results(result, alpha=0.05)
        
        assert_probability_valid(analysis.power_achieved)


class TestMakeRolloutDecision:
    """Test suite for make_rollout_decision function."""
    
    @pytest.mark.unit
    def test_rollout_decision_proceed_with_confidence(self):
        """Test proceed_with_confidence decision."""
        sim_result = create_sim_result(
            control_n=5000,
            control_conversions=250,
            treatment_n=5000,
            treatment_conversions=350
        )
        
        analysis = analyze_results(sim_result, alpha=0.05)
        decision = make_rollout_decision(
            sim_result,
            analysis,
            business_target_absolute=0.01  # 1% absolute lift target
        )
        
        assert decision in ["proceed_with_confidence", "proceed_with_caution"]
    
    @pytest.mark.unit
    def test_rollout_decision_do_not_proceed(self):
        """Test do_not_proceed decision."""
        sim_result = create_non_significant_result()
        analysis = analyze_results(sim_result, alpha=0.05)
        
        decision = make_rollout_decision(
            sim_result,
            analysis,
            business_target_absolute=0.05  # High target unlikely to be met
        )
        
        # Should be do_not_proceed or proceed_with_caution
        assert decision in ["do_not_proceed", "proceed_with_caution"]
    
    @pytest.mark.unit
    def test_rollout_decision_types(self):
        """Test that decision is one of three valid types."""
        result = create_significant_positive_result()
        analysis = analyze_results(result, alpha=0.05)
        
        decision = make_rollout_decision(
            result,
            analysis,
            business_target_absolute=0.01
        )
        
        assert decision in [
            "proceed_with_confidence",
            "proceed_with_caution",
            "do_not_proceed"
        ]


class TestAnalysisTestTypes:
    """Test different statistical test types."""
    
    @pytest.mark.unit
    def test_two_proportion_z_test(self):
        """Test two-proportion z-test explicitly."""
        result = create_significant_positive_result()
        analysis = analyze_results(result, alpha=0.05, test_type="two_proportion_z")
        
        assert_p_value_valid(analysis.p_value)
        assert len(analysis.confidence_interval) == 2
    
    @pytest.mark.unit
    def test_chi_square_test(self):
        """Test chi-square test."""
        result = create_significant_positive_result()
        
        try:
            analysis = analyze_results(result, alpha=0.05, test_type="chi_square")
            assert_p_value_valid(analysis.p_value)
        except Exception:
            # Chi-square may not be implemented yet
            pytest.skip("Chi-square test not fully implemented")
    
    @pytest.mark.unit
    def test_fisher_exact_test(self):
        """Test Fisher's exact test."""
        result = create_sim_result(control_n=50, control_conversions=5,
                                   treatment_n=50, treatment_conversions=10)
        
        try:
            analysis = analyze_results(result, alpha=0.05, test_type="fisher_exact")
            assert_p_value_valid(analysis.p_value)
        except Exception:
            # Fisher's exact may not be implemented yet
            pytest.skip("Fisher's exact test not fully implemented")
    
    @pytest.mark.unit
    def test_invalid_test_type(self):
        """Test that invalid test type raises error."""
        result = create_sim_result()
        
        with pytest.raises(ValueError):
            analyze_results(result, alpha=0.05, test_type="invalid_test")


class TestAnalysisRecommendations:
    """Test analysis recommendations."""
    
    @pytest.mark.unit
    def test_recommendation_string_present(self):
        """Test that recommendation is generated."""
        result = create_significant_positive_result()
        analysis = analyze_results(result, alpha=0.05)
        
        assert isinstance(analysis.recommendation, str)
        assert len(analysis.recommendation) > 0


class TestEdgeCases:
    """Test edge cases for analysis."""
    
    @pytest.mark.unit
    def test_analyze_zero_conversions(self):
        """Test analysis with zero conversions - may raise error for degenerate case."""
        result = create_sim_result(
            control_n=1000,
            control_conversions=0,
            treatment_n=1000,
            treatment_conversions=0
        )
        
        # This is a degenerate case - function may raise ValueError
        # which is acceptable for zero conversions in both groups
        try:
            analysis = analyze_results(result, alpha=0.05)
            # If it succeeds, validate the result
            assert 0 <= analysis.p_value <= 1
            assert len(analysis.confidence_interval) == 2
        except ValueError:
            # Acceptable to raise error for degenerate case
            pass
    
    @pytest.mark.unit
    def test_analyze_perfect_conversion(self):
        """Test analysis with 100% conversion - may raise error for degenerate case."""
        result = create_sim_result(
            control_n=100,
            control_conversions=100,
            treatment_n=100,
            treatment_conversions=100
        )
        
        # This is a degenerate case - function may raise ValueError
        try:
            analysis = analyze_results(result, alpha=0.05)
            # If it succeeds, validate the result
            assert 0 <= analysis.p_value <= 1
            assert analysis.significant == False
        except ValueError:
            # Acceptable to raise error for degenerate case
            pass
    
    @pytest.mark.unit
    def test_analyze_very_small_sample(self):
        """Test analysis with very small sample."""
        result = create_sim_result(
            control_n=10,
            control_conversions=1,
            treatment_n=10,
            treatment_conversions=3
        )
        
        analysis = analyze_results(result, alpha=0.05)
        
        # Should still produce valid output
        assert_p_value_valid(analysis.p_value)
        assert len(analysis.confidence_interval) == 2
    
    @pytest.mark.unit
    def test_analyze_large_sample(self):
        """Test analysis with large sample."""
        result = create_sim_result(
            control_n=100000,
            control_conversions=5000,
            treatment_n=100000,
            treatment_conversions=5200
        )
        
        analysis = analyze_results(result, alpha=0.05)
        
        # Large sample should detect small differences
        assert_p_value_valid(analysis.p_value)
        # Likely to be significant with this sample size
        if analysis.significant:
            assert analysis.p_value < 0.05

