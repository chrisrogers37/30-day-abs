"""
Tests for variable question set scoring in core.scoring module.

These tests verify the new variable quiz result system that works
with the question_bank.py module.
"""

import pytest
from core.scoring import (
    VariableAnswerKey, VariableQuizResult,
    generate_variable_design_answer_key,
    generate_variable_analysis_answer_key,
    generate_variable_quiz_feedback,
    create_variable_quiz_result,
    select_and_create_design_quiz,
    select_and_create_analysis_quiz
)
from core.validation import (
    ScoringContext,
    calculate_design_answer_by_id,
    calculate_analysis_answer_by_id,
    ScoringResult
)
from core.question_bank import (
    get_default_design_questions
)
from core.design import compute_sample_size
from tests.helpers.factories import create_sim_result


class TestVariableAnswerKey:
    """Test VariableAnswerKey dataclass."""

    @pytest.mark.unit
    def test_generate_design_answer_key(self, standard_design_params):
        """Generate answer key for design questions."""
        sample_size = compute_sample_size(standard_design_params)
        question_ids = ["mde_absolute", "target_conversion_rate", "sample_size_per_arm"]

        answer_key = generate_variable_design_answer_key(
            question_ids,
            standard_design_params,
            sample_size
        )

        assert answer_key.question_type == "design"
        assert answer_key.question_ids == question_ids
        assert len(answer_key.questions) == 3
        assert answer_key.max_score == 3

        # Check correct answers are calculated
        for qid in question_ids:
            assert qid in answer_key.correct_answers

    @pytest.mark.unit
    def test_generate_analysis_answer_key(self):
        """Generate answer key for analysis questions."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )
        question_ids = ["control_rate", "treatment_rate", "absolute_lift"]

        answer_key = generate_variable_analysis_answer_key(
            question_ids,
            sim_result
        )

        assert answer_key.question_type == "analysis"
        assert answer_key.question_ids == question_ids
        assert len(answer_key.questions) == 3
        assert answer_key.max_score == 3

    @pytest.mark.unit
    def test_answer_key_invalid_question_raises(self, standard_design_params):
        """Invalid question ID should raise error."""
        sample_size = compute_sample_size(standard_design_params)

        with pytest.raises(ValueError, match="Unknown question ID"):
            generate_variable_design_answer_key(
                ["invalid_question_id"],
                standard_design_params,
                sample_size
            )


class TestVariableQuizFeedback:
    """Test feedback generation for variable quizzes."""

    @pytest.mark.unit
    def test_feedback_includes_overall_score(self, standard_design_params):
        """Feedback should include overall score."""
        sample_size = compute_sample_size(standard_design_params)
        question_ids = ["mde_absolute", "target_conversion_rate"]

        answer_key = generate_variable_design_answer_key(
            question_ids,
            standard_design_params,
            sample_size
        )

        # Create a scoring result
        scoring_result = ScoringResult(
            scores={"mde_absolute": {"correct": True, "user": 1.0, "correct_answer": 1.0, "tolerance": 0.5}},
            total_score=1,
            max_score=2,
            percentage=50.0,
            grade="F"
        )

        feedback = generate_variable_quiz_feedback(scoring_result, answer_key)

        assert any("Score" in f for f in feedback)
        assert any("Grade" in f for f in feedback)

    @pytest.mark.unit
    def test_feedback_marks_correct_incorrect(self, standard_design_params):
        """Feedback should mark correct and incorrect answers."""
        sample_size = compute_sample_size(standard_design_params)
        question_ids = ["mde_absolute", "target_conversion_rate"]

        answer_key = generate_variable_design_answer_key(
            question_ids,
            standard_design_params,
            sample_size
        )

        scoring_result = ScoringResult(
            scores={
                "mde_absolute": {"correct": True, "user": 1.0, "correct_answer": 1.0, "tolerance": 0.5},
                "target_conversion_rate": {"correct": False, "user": 99.0, "correct_answer": 11.0, "tolerance": 0.5}
            },
            total_score=1,
            max_score=2,
            percentage=50.0,
            grade="F"
        )

        feedback = generate_variable_quiz_feedback(scoring_result, answer_key)
        feedback_text = "\n".join(feedback)

        # Should have correct and incorrect markers
        assert "Correct" in feedback_text or "correct" in feedback_text


class TestCreateVariableQuizResult:
    """Test creating complete variable quiz results."""

    @pytest.mark.unit
    def test_create_design_quiz_result(self, standard_design_params):
        """Create complete design quiz result."""
        sample_size = compute_sample_size(standard_design_params)
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde = baseline * target_lift

        question_ids = get_default_design_questions()

        # Get correct answers for user_answers
        user_answers = {}
        for qid in question_ids:
            correct, _ = calculate_design_answer_by_id(
                qid, standard_design_params, sample_size, mde
            )
            user_answers[qid] = correct

        result = create_variable_quiz_result(
            user_answers=user_answers,
            question_ids=question_ids,
            ctx=ScoringContext(
                design_params=standard_design_params,
                sample_size_result=sample_size,
                mde_absolute=mde,
            ),
        )

        assert isinstance(result, VariableQuizResult)
        assert result.answer_key.question_type == "design"
        assert result.scoring_result.total_score == len(question_ids)
        assert len(result.feedback) > 0

    @pytest.mark.unit
    def test_create_analysis_quiz_result(self):
        """Create complete analysis quiz result."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        question_ids = ["control_rate", "treatment_rate", "absolute_lift"]

        # Get correct answers
        user_answers = {}
        for qid in question_ids:
            correct, _ = calculate_analysis_answer_by_id(qid, sim_result)
            user_answers[qid] = correct

        result = create_variable_quiz_result(
            user_answers=user_answers,
            question_ids=question_ids,
            ctx=ScoringContext(sim_result=sim_result),
        )

        assert isinstance(result, VariableQuizResult)
        assert result.answer_key.question_type == "analysis"
        assert result.scoring_result.total_score == 3

    @pytest.mark.unit
    def test_create_result_requires_params(self):
        """Should raise error if required params missing."""
        with pytest.raises(ValueError):
            create_variable_quiz_result(
                user_answers={},
                question_ids=["mde_absolute"]
                # Missing design_params
            )


class TestSelectAndCreateQuiz:
    """Test random quiz selection and creation."""

    @pytest.mark.unit
    def test_select_and_create_design_quiz(self, standard_design_params):
        """Select random design questions and create answer key."""
        sample_size = compute_sample_size(standard_design_params)

        answer_key = select_and_create_design_quiz(
            design_params=standard_design_params,
            sample_size_result=sample_size,
            question_count=4,
            seed=42
        )

        assert isinstance(answer_key, VariableAnswerKey)
        assert answer_key.question_type == "design"
        assert len(answer_key.questions) == 4
        assert len(answer_key.correct_answers) == 4

    @pytest.mark.unit
    def test_select_and_create_design_quiz_reproducible(self, standard_design_params):
        """Same seed should produce same quiz."""
        sample_size = compute_sample_size(standard_design_params)

        key1 = select_and_create_design_quiz(
            standard_design_params, sample_size, question_count=3, seed=42
        )
        key2 = select_and_create_design_quiz(
            standard_design_params, sample_size, question_count=3, seed=42
        )

        assert key1.question_ids == key2.question_ids

    @pytest.mark.unit
    def test_select_and_create_analysis_quiz(self):
        """Select random analysis questions and create answer key."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        answer_key = select_and_create_analysis_quiz(
            sim_result=sim_result,
            question_count=5,
            seed=42
        )

        assert isinstance(answer_key, VariableAnswerKey)
        assert answer_key.question_type == "analysis"
        assert len(answer_key.questions) == 5

    @pytest.mark.unit
    def test_select_and_create_analysis_quiz_with_target(self):
        """Create analysis quiz with business target for rollout questions."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        answer_key = select_and_create_analysis_quiz(
            sim_result=sim_result,
            question_count=5,
            business_target_absolute=0.01,
            seed=42
        )

        assert isinstance(answer_key, VariableAnswerKey)


class TestIntegration:
    """Integration tests for the full variable quiz flow."""

    @pytest.mark.integration
    def test_full_design_quiz_flow(self, standard_design_params):
        """Test complete design quiz: select -> answer -> score -> feedback."""
        sample_size = compute_sample_size(standard_design_params)
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde = baseline * target_lift

        # 1. Select questions
        answer_key = select_and_create_design_quiz(
            standard_design_params,
            sample_size,
            question_count=4,
            mde_absolute=mde,
            seed=42
        )

        # 2. User provides answers (simulating correct answers)
        user_answers = {}
        for qid in answer_key.question_ids:
            user_answers[qid] = answer_key.correct_answers[qid]

        # 3. Create quiz result
        result = create_variable_quiz_result(
            user_answers=user_answers,
            question_ids=answer_key.question_ids,
            ctx=ScoringContext(
                design_params=standard_design_params,
                sample_size_result=sample_size,
                mde_absolute=mde,
            ),
        )

        # 4. Verify results
        assert result.scoring_result.total_score == 4
        assert result.scoring_result.percentage == 100.0
        assert result.scoring_result.grade == "A"
        assert len(result.feedback) >= 3  # At least score, grade, and question feedback

    @pytest.mark.integration
    def test_full_analysis_quiz_flow(self):
        """Test complete analysis quiz: select -> answer -> score -> feedback."""
        sim_result = create_sim_result(
            control_n=5000,
            control_conversions=250,
            treatment_n=5000,
            treatment_conversions=350
        )

        # 1. Select questions (avoiding ones that need business_target)
        answer_key = select_and_create_analysis_quiz(
            sim_result,
            question_count=5,
            seed=42
        )

        # 2. User provides answers (simulating 50% correct)
        user_answers = {}
        for i, qid in enumerate(answer_key.question_ids):
            if i % 2 == 0:  # Every other answer is correct
                user_answers[qid] = answer_key.correct_answers[qid]
            else:
                user_answers[qid] = 999.0  # Wrong answer

        # 3. Create quiz result
        result = create_variable_quiz_result(
            user_answers=user_answers,
            question_ids=answer_key.question_ids,
            ctx=ScoringContext(sim_result=sim_result),
        )

        # 4. Verify results
        assert result.scoring_result.max_score == 5
        # Should have some correct, some incorrect
        assert 0 < result.scoring_result.total_score < 5
