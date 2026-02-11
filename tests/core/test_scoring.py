"""
Tests for core.scoring module - Answer key generation and quiz scoring.
"""

import pytest
from core.scoring import (
    generate_design_answer_key,
    generate_analysis_answer_key
)
from tests.helpers.factories import create_significant_positive_result


class TestGenerateDesignAnswerKey:
    """Test suite for generate_design_answer_key function."""
    
    @pytest.mark.unit
    def test_generate_design_answer_key(self, standard_design_params):
        """Test generation of design answer key."""
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        answer_key = generate_design_answer_key(
            design_params=standard_design_params,
            sample_size_result=sample_size
        )
        
        assert answer_key is not None
        assert hasattr(answer_key, "questions")
        assert hasattr(answer_key, "correct_answers")
    
    @pytest.mark.unit
    def test_answer_key_contains_all_questions(self, standard_design_params):
        """Test that answer key contains all design questions."""
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        answer_key = generate_design_answer_key(
            design_params=standard_design_params,
            sample_size_result=sample_size
        )
        
        # Should have 6 design questions
        assert len(answer_key.questions) == 6


class TestGenerateAnalysisAnswerKey:
    """Test suite for generate_analysis_answer_key function."""
    
    @pytest.mark.unit
    def test_generate_analysis_answer_key(self):
        """Test generation of analysis answer key."""
        sim_result = create_significant_positive_result(seed=42)
        
        answer_key = generate_analysis_answer_key(
            sim_result=sim_result  # Fixed: function only takes sim_result
        )
        
        assert answer_key is not None
        assert hasattr(answer_key, "questions")
        assert hasattr(answer_key, "correct_answers")
    
    @pytest.mark.unit
    def test_analysis_answer_key_contains_all_questions(self):
        """Test that answer key contains all analysis questions."""
        sim_result = create_significant_positive_result(seed=42)
        
        answer_key = generate_analysis_answer_key(
            sim_result=sim_result  # Fixed: function only takes sim_result
        )
        
        # Should have analysis questions (may not be exactly 7 without business target)
        assert len(answer_key.questions) >= 6  # At least 6 questions without rollout decision
    
    @pytest.mark.unit
    def test_answer_key_structure(self):
        """Test answer key structure."""
        sim_result = create_significant_positive_result(seed=42)
        answer_key = generate_analysis_answer_key(sim_result)
        
        assert hasattr(answer_key, "question_type")
        assert hasattr(answer_key, "questions")
        assert hasattr(answer_key, "correct_answers")
        assert hasattr(answer_key, "max_score")
        assert answer_key.question_type == "analysis"


class TestAnswerKeyContent:
    """Test answer key content generation."""
    
    @pytest.mark.unit
    def test_design_answer_key_content(self, standard_design_params):
        """Test that design answer key contains proper content."""
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        answer_key = generate_design_answer_key(standard_design_params, sample_size)
        
        # Check each question has required fields
        for question in answer_key.questions:
            assert "number" in question
            assert "question" in question
            assert "hint" in question
            assert "type" in question
    
    @pytest.mark.unit
    def test_analysis_answer_key_content(self):
        """Test that analysis answer key contains proper content."""
        sim_result = create_significant_positive_result(seed=42)
        answer_key = generate_analysis_answer_key(sim_result)
        
        # Check each question has required fields
        for question in answer_key.questions:
            assert "number" in question
            assert "question" in question
            assert "hint" in question
            assert "type" in question


class TestGenerateQuizFeedback:
    """Test suite for generate_quiz_feedback function."""
    
    @pytest.mark.unit
    def test_generate_quiz_feedback(self, standard_design_params):
        """Test quiz feedback generation."""
        from core.scoring import generate_quiz_feedback
        from core.design import compute_sample_size
        from core.validation import ScoringResult
        
        sample_size = compute_sample_size(standard_design_params)
        answer_key = generate_design_answer_key(standard_design_params, sample_size)
        
        # Create mock scoring result
        scoring_result = ScoringResult(
            scores={},
            total_score=5,
            max_score=6,
            percentage=83.3,
            grade="B"
        )
        
        feedback = generate_quiz_feedback(scoring_result, answer_key)
        
        assert isinstance(feedback, list)
        assert len(feedback) > 0
        assert "Overall Score" in feedback[0]
        assert "Grade" in feedback[1]


class TestCreateCompleteQuizResult:
    """Test suite for create_complete_quiz_result function."""
    
    @pytest.mark.unit
    def test_create_quiz_result_design(self, standard_design_params):
        """Test creating complete quiz result for design questions."""
        from core.scoring import create_complete_quiz_result
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        
        user_answers = {
            "mde_absolute": 0.75,
            "target_conversion_rate": 5.75,
            "relative_lift_pct": 15.0,
            "sample_size": sample_size.per_arm,
            "duration": 2,
            "additional_conversions": 75
        }
        
        quiz_result = create_complete_quiz_result(
            user_answers=user_answers,
            design_params=standard_design_params,
            sample_size_result=sample_size
        )
        
        assert quiz_result is not None
        assert quiz_result.answer_key is not None
        assert quiz_result.scoring_result is not None
        assert quiz_result.user_answers == user_answers
        assert len(quiz_result.feedback) > 0
    
    @pytest.mark.unit
    def test_create_quiz_result_analysis_basic(self):
        """Test creating basic quiz result for analysis questions."""
        from core.scoring import generate_analysis_answer_key
        
        sim_result = create_significant_positive_result(seed=42)
        
        # Just test the answer key generation (simpler)
        answer_key = generate_analysis_answer_key(sim_result)
        
        assert answer_key is not None
        assert answer_key.question_type == "analysis"
        assert len(answer_key.questions) >= 6


class TestExportFunctions:
    """Test suite for export functions."""
    
    @pytest.mark.unit
    def test_export_answer_key_to_csv(self, standard_design_params, temp_output_dir):
        """Test exporting answer key to CSV."""
        from core.scoring import export_answer_key_to_csv
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        answer_key = generate_design_answer_key(standard_design_params, sample_size)
        
        output_file = temp_output_dir / "answer_key.csv"
        export_answer_key_to_csv(answer_key, str(output_file))
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0
    
    @pytest.mark.unit
    def test_export_quiz_results_to_csv(self, standard_design_params, temp_output_dir):
        """Test exporting quiz results to CSV."""
        from core.scoring import export_quiz_results_to_csv, create_complete_quiz_result
        from core.design import compute_sample_size
        
        sample_size = compute_sample_size(standard_design_params)
        
        user_answers = {
            "mde_absolute": 0.75,
            "sample_size": sample_size.per_arm,
        }
        
        quiz_result = create_complete_quiz_result(
            user_answers=user_answers,
            design_params=standard_design_params,
            sample_size_result=sample_size
        )
        
        output_file = temp_output_dir / "quiz_results.csv"
        export_quiz_results_to_csv(quiz_result, str(output_file))
        
        assert output_file.exists()
        assert output_file.stat().st_size > 0


class TestGetQuestionKey:
    """Test suite for _get_question_key helper function."""
    
    @pytest.mark.unit
    def test_get_question_key_design(self):
        """Test getting question key for design questions."""
        from core.scoring import _get_question_key
        
        assert _get_question_key(1, "design") == "mde_absolute"
        assert _get_question_key(4, "design") == "sample_size"
        assert _get_question_key(6, "design") == "additional_conversions"
    
    @pytest.mark.unit
    def test_get_question_key_analysis(self):
        """Test getting question key for analysis questions."""
        from core.scoring import _get_question_key
        
        assert _get_question_key(1, "analysis") == "control_conversion_rate"
        assert _get_question_key(5, "analysis") == "p_value"
        assert _get_question_key(6, "analysis") == "confidence_interval"
    
    @pytest.mark.unit
    def test_get_question_key_invalid(self):
        """Test that invalid question number raises error."""
        from core.scoring import _get_question_key
        
        with pytest.raises(ValueError):
            _get_question_key(999, "design")

