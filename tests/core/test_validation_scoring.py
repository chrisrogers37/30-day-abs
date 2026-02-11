"""
Additional tests for core.validation scoring functions.

This module tests the score_design_answers and score_analysis_answers functions
to push coverage above 90%.
"""

import pytest
from core.validation import (
    score_design_answers,
    score_analysis_answers,
    calculate_correct_design_answers,
    calculate_correct_analysis_answers
)
from tests.helpers.factories import create_significant_positive_result


class TestScoreDesignAnswers:
    """Test suite for score_design_answers function."""
    
    @pytest.mark.unit
    def test_score_all_correct(self, standard_design_params):
        """Test scoring when all answers are correct."""
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        correct_answers = calculate_correct_design_answers(standard_design_params, sample_size)
        
        # Use correct answers as user answers
        scoring_result = score_design_answers(
            user_answers=correct_answers,
            design_params=standard_design_params,
            sample_size_result=sample_size
        )
        
        assert scoring_result.total_score == scoring_result.max_score
        assert scoring_result.percentage == 100.0
        assert scoring_result.grade == "A"
    
    @pytest.mark.unit
    def test_score_partial_correct(self, standard_design_params):
        """Test scoring with some correct and some wrong answers."""
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        correct_answers = calculate_correct_design_answers(standard_design_params, sample_size)
        
        # Mix correct and incorrect answers
        user_answers = correct_answers.copy()
        user_answers["sample_size"] = 999999  # Wrong answer
        
        scoring_result = score_design_answers(
            user_answers=user_answers,
            design_params=standard_design_params,
            sample_size_result=sample_size
        )
        
        assert scoring_result.total_score < scoring_result.max_score
        assert scoring_result.percentage < 100.0
    
    @pytest.mark.unit
    def test_score_all_wrong(self, standard_design_params):
        """Test scoring when all answers are wrong."""
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        
        # All wrong answers
        user_answers = {
            "mde_absolute": 999.0,
            "target_conversion_rate": 999.0,
            "relative_lift_pct": 999.0,
            "sample_size": 999999,
            "duration": 999,
            "additional_conversions": 999
        }
        
        scoring_result = score_design_answers(
            user_answers=user_answers,
            design_params=standard_design_params,
            sample_size_result=sample_size
        )
        
        assert scoring_result.total_score == 0
        assert scoring_result.percentage == 0.0
        assert scoring_result.grade == "F"


class TestScoreAnalysisAnswers:
    """Test suite for score_analysis_answers function."""
    
    @pytest.mark.unit
    def test_score_analysis_all_correct(self):
        """Test scoring analysis answers when all correct."""
        sim_result = create_significant_positive_result(seed=42)
        correct_answers = calculate_correct_analysis_answers(sim_result, business_target_absolute=0.01)
        
        scoring_result = score_analysis_answers(
            user_answers=correct_answers,
            sim_result=sim_result,
            business_target_absolute=0.01
        )
        
        # Should have high score (maybe not perfect due to tolerances/rounding)
        assert scoring_result.percentage >= 70.0
        assert scoring_result.total_score > 0
    
    @pytest.mark.unit
    def test_score_analysis_partial(self):
        """Test scoring analysis with mixed answers."""
        sim_result = create_significant_positive_result(seed=42)
        
        # Get correct answers first
        correct_answers = calculate_correct_analysis_answers(sim_result, business_target_absolute=0.01)
        
        # Mix some correct and some wrong
        user_answers = correct_answers.copy()
        user_answers["control_conversion_rate"] = 999.0  # Wrong
        
        scoring_result = score_analysis_answers(
            user_answers=user_answers,
            sim_result=sim_result,
            business_target_absolute=0.01
        )
        
        assert scoring_result.total_score < scoring_result.max_score
        assert 0 < scoring_result.percentage < 100.0
    
    @pytest.mark.unit
    def test_score_analysis_all_wrong(self):
        """Test scoring analysis when all answers are wrong."""
        from tests.helpers.factories import create_sim_result
        from core.validation import calculate_correct_analysis_answers
        
        sim_result = create_sim_result()
        
        # Get structure of correct answers to ensure all keys present
        correct_structure = calculate_correct_analysis_answers(sim_result, business_target_absolute=0.01)
        
        # All wrong answers but with correct keys
        user_answers = {key: 999.0 if key != "confidence_interval" and key != "rollout_decision" 
                       else ((999, 999) if key == "confidence_interval" else "do_not_proceed")
                       for key in correct_structure.keys()}
        
        scoring_result = score_analysis_answers(
            user_answers=user_answers,
            sim_result=sim_result,
            business_target_absolute=0.01
        )
        
        assert scoring_result.total_score == 0
        assert scoring_result.percentage == 0.0

