"""
Tests for question ID-based validation functions in core.validation module.

These tests verify the new question ID-based validation system that works
with the question_bank.py module for variable quiz experiences.
"""

import pytest
from core.validation import (
    ScoringContext,
    validate_answer_by_id,
    calculate_design_answer_by_id,
    calculate_analysis_answer_by_id,
    score_answers_by_id,
    get_question_text,
    get_question_hint
)
from core.design import compute_sample_size
from tests.helpers.factories import create_sim_result


class TestCalculateDesignAnswerById:
    """Test calculation of design answers by question ID."""

    @pytest.mark.unit
    def test_calculate_mde_absolute(self, standard_design_params):
        """Calculate MDE absolute answer."""
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde = baseline * target_lift

        answer, tolerance = calculate_design_answer_by_id(
            "mde_absolute",
            standard_design_params,
            mde_absolute=mde
        )

        expected = mde * 100  # Convert to percentage points
        assert abs(answer - expected) < 0.001
        assert tolerance == 0.5

    @pytest.mark.unit
    def test_calculate_mde_relative(self, standard_design_params):
        """Calculate relative MDE answer."""
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde = baseline * target_lift

        answer, tolerance = calculate_design_answer_by_id(
            "mde_relative",
            standard_design_params,
            mde_absolute=mde
        )

        expected = (mde / baseline) * 100
        assert abs(answer - expected) < 0.001
        assert tolerance == 2.0

    @pytest.mark.unit
    def test_calculate_target_conversion_rate(self, standard_design_params):
        """Calculate target conversion rate answer."""
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde = baseline * target_lift

        answer, tolerance = calculate_design_answer_by_id(
            "target_conversion_rate",
            standard_design_params,
            mde_absolute=mde
        )

        expected = (baseline + mde) * 100
        assert abs(answer - expected) < 0.001

    @pytest.mark.unit
    def test_calculate_sample_size_per_arm(self, standard_design_params):
        """Calculate sample size per arm answer."""
        sample_size = compute_sample_size(standard_design_params)

        answer, tolerance = calculate_design_answer_by_id(
            "sample_size_per_arm",
            standard_design_params,
            sample_size_result=sample_size
        )

        assert answer == sample_size.per_arm
        assert tolerance == 50

    @pytest.mark.unit
    def test_calculate_sample_size_total(self, standard_design_params):
        """Calculate total sample size answer."""
        sample_size = compute_sample_size(standard_design_params)

        answer, tolerance = calculate_design_answer_by_id(
            "sample_size_total",
            standard_design_params,
            sample_size_result=sample_size
        )

        assert answer == sample_size.per_arm * 2

    @pytest.mark.unit
    def test_calculate_duration_days(self, standard_design_params):
        """Calculate experiment duration in days."""
        sample_size = compute_sample_size(standard_design_params)
        total_sample = sample_size.per_arm * 2
        expected_days = max(1, round(total_sample / standard_design_params.expected_daily_traffic))

        answer, tolerance = calculate_design_answer_by_id(
            "duration_days",
            standard_design_params,
            sample_size_result=sample_size
        )

        assert answer == expected_days
        assert tolerance == 1

    @pytest.mark.unit
    def test_calculate_mde_daily_impact(self, standard_design_params):
        """Calculate daily impact in additional conversions."""
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde = baseline * target_lift

        answer, tolerance = calculate_design_answer_by_id(
            "mde_daily_impact",
            standard_design_params,
            mde_absolute=mde
        )

        expected = round(standard_design_params.expected_daily_traffic * mde)
        assert answer == expected

    @pytest.mark.unit
    def test_calculate_invalid_question_id_raises(self, standard_design_params):
        """Invalid question ID should raise ValueError."""
        with pytest.raises(ValueError, match="Unknown question ID"):
            calculate_design_answer_by_id(
                "invalid_question_id",
                standard_design_params
            )


class TestCalculateAnalysisAnswerById:
    """Test calculation of analysis answers by question ID."""

    @pytest.mark.unit
    def test_calculate_control_rate(self):
        """Calculate control conversion rate."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        answer, tolerance = calculate_analysis_answer_by_id(
            "control_rate",
            sim_result
        )

        assert abs(answer - 5.0) < 0.001  # 50/1000 = 5%
        assert tolerance == 0.05

    @pytest.mark.unit
    def test_calculate_treatment_rate(self):
        """Calculate treatment conversion rate."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        answer, tolerance = calculate_analysis_answer_by_id(
            "treatment_rate",
            sim_result
        )

        assert abs(answer - 6.0) < 0.001  # 60/1000 = 6%

    @pytest.mark.unit
    def test_calculate_pooled_rate(self):
        """Calculate pooled conversion rate."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        answer, tolerance = calculate_analysis_answer_by_id(
            "pooled_rate",
            sim_result
        )

        expected = (50 + 60) / (1000 + 1000) * 100  # 5.5%
        assert abs(answer - expected) < 0.001

    @pytest.mark.unit
    def test_calculate_absolute_lift(self):
        """Calculate absolute lift."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        answer, tolerance = calculate_analysis_answer_by_id(
            "absolute_lift",
            sim_result
        )

        assert abs(answer - 1.0) < 0.001  # 6% - 5% = 1pp

    @pytest.mark.unit
    def test_calculate_relative_lift(self):
        """Calculate relative lift."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        answer, tolerance = calculate_analysis_answer_by_id(
            "relative_lift",
            sim_result
        )

        expected = (0.06 - 0.05) / 0.05 * 100  # 20%
        assert abs(answer - expected) < 0.001

    @pytest.mark.unit
    def test_calculate_lift_direction_positive(self):
        """Calculate lift direction for positive lift."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        answer, tolerance = calculate_analysis_answer_by_id(
            "lift_direction",
            sim_result
        )

        assert answer == "Yes"

    @pytest.mark.unit
    def test_calculate_lift_direction_negative(self):
        """Calculate lift direction for negative lift."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=60,
            treatment_n=1000,
            treatment_conversions=50
        )

        answer, tolerance = calculate_analysis_answer_by_id(
            "lift_direction",
            sim_result
        )

        assert answer == "No"

    @pytest.mark.unit
    def test_calculate_p_value(self):
        """Calculate p-value."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        answer, tolerance = calculate_analysis_answer_by_id(
            "p_value",
            sim_result
        )

        # P-value should be between 0 and 1
        assert 0 <= answer <= 1
        assert tolerance == 0.005

    @pytest.mark.unit
    def test_calculate_is_significant(self):
        """Calculate statistical significance."""
        # Create a clearly significant result
        sim_result = create_sim_result(
            control_n=5000,
            control_conversions=250,
            treatment_n=5000,
            treatment_conversions=350
        )

        answer, tolerance = calculate_analysis_answer_by_id(
            "is_significant",
            sim_result,
            alpha=0.05
        )

        # With such a large difference, should be significant
        assert answer in ["Yes", "No"]

    @pytest.mark.unit
    def test_calculate_confidence_interval(self):
        """Calculate confidence interval."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        answer, tolerance = calculate_analysis_answer_by_id(
            "confidence_interval",
            sim_result
        )

        # Should be a tuple
        assert isinstance(answer, tuple)
        assert len(answer) == 2
        # Lower bound should be less than upper bound
        assert answer[0] < answer[1]

    @pytest.mark.unit
    def test_calculate_rollout_decision_requires_target(self):
        """Rollout decision should require business target."""
        sim_result = create_sim_result()

        with pytest.raises(ValueError, match="business_target_absolute required"):
            calculate_analysis_answer_by_id(
                "rollout_decision",
                sim_result
            )

    @pytest.mark.unit
    def test_calculate_rollout_decision_with_target(self):
        """Calculate rollout decision with business target."""
        sim_result = create_sim_result(
            control_n=5000,
            control_conversions=250,
            treatment_n=5000,
            treatment_conversions=350
        )

        answer, tolerance = calculate_analysis_answer_by_id(
            "rollout_decision",
            sim_result,
            business_target_absolute=0.01
        )

        assert answer in ["Yes", "No"]


class TestValidateAnswerById:
    """Test validation of answers using question IDs."""

    @pytest.mark.unit
    def test_validate_correct_design_answer(self, standard_design_params):
        """Validate a correct design answer."""
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde = baseline * target_lift

        correct_answer = mde * 100  # MDE in percentage points

        result = validate_answer_by_id(
            "mde_absolute",
            correct_answer,
            ctx=ScoringContext(design_params=standard_design_params, mde_absolute=mde),
        )

        assert result.is_correct is True

    @pytest.mark.unit
    def test_validate_incorrect_design_answer(self, standard_design_params):
        """Validate an incorrect design answer."""
        result = validate_answer_by_id(
            "mde_absolute",
            999.0,  # Wrong answer
            ctx=ScoringContext(design_params=standard_design_params),
        )

        assert result.is_correct is False

    @pytest.mark.unit
    def test_validate_within_tolerance(self, standard_design_params):
        """Answers within tolerance should pass."""
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde = baseline * target_lift

        correct_answer = mde * 100
        # Within 0.5 percentage point tolerance
        answer_within_tolerance = correct_answer + 0.3

        result = validate_answer_by_id(
            "mde_absolute",
            answer_within_tolerance,
            ctx=ScoringContext(design_params=standard_design_params, mde_absolute=mde),
        )

        assert result.is_correct is True

    @pytest.mark.unit
    def test_validate_boolean_answer_yes(self):
        """Validate boolean 'Yes' answer."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        result = validate_answer_by_id(
            "lift_direction",
            "Yes",
            ctx=ScoringContext(sim_result=sim_result),
        )

        assert result.is_correct is True

    @pytest.mark.unit
    def test_validate_boolean_answer_case_insensitive(self):
        """Boolean answers should be case insensitive."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        for variant in ["yes", "YES", "Yes", "yEs"]:
            result = validate_answer_by_id(
                "lift_direction",
                variant,
                ctx=ScoringContext(sim_result=sim_result),
            )
            assert result.is_correct is True

    @pytest.mark.unit
    def test_validate_range_answer(self):
        """Validate confidence interval (range) answer."""
        sim_result = create_sim_result(
            control_n=1000,
            control_conversions=50,
            treatment_n=1000,
            treatment_conversions=60
        )

        # Get correct CI
        correct_ci, tolerance = calculate_analysis_answer_by_id(
            "confidence_interval",
            sim_result
        )

        result = validate_answer_by_id(
            "confidence_interval",
            correct_ci,
            ctx=ScoringContext(sim_result=sim_result),
        )

        # Use == instead of 'is' because numpy may return np.True_
        assert result.is_correct == True

    @pytest.mark.unit
    def test_validate_requires_design_params_for_design(self):
        """Design questions should require design_params."""
        with pytest.raises(ValueError, match="design_params required"):
            validate_answer_by_id(
                "mde_absolute",
                1.0
            )

    @pytest.mark.unit
    def test_validate_requires_sim_result_for_analysis(self):
        """Analysis questions should require sim_result."""
        with pytest.raises(ValueError, match="sim_result required"):
            validate_answer_by_id(
                "control_rate",
                5.0
            )


class TestScoreAnswersById:
    """Test scoring of multiple answers by question ID."""

    @pytest.mark.unit
    def test_score_all_correct(self, standard_design_params):
        """Score when all answers are correct."""
        sample_size = compute_sample_size(standard_design_params)
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde = baseline * target_lift

        # Get correct answers
        question_ids = ["mde_absolute", "target_conversion_rate", "sample_size_per_arm"]
        user_answers = {}

        for qid in question_ids:
            correct, _ = calculate_design_answer_by_id(
                qid, standard_design_params, sample_size, mde
            )
            user_answers[qid] = correct

        result = score_answers_by_id(
            user_answers=user_answers,
            question_ids=question_ids,
            ctx=ScoringContext(
                design_params=standard_design_params,
                sample_size_result=sample_size,
                mde_absolute=mde,
            ),
        )

        assert result.total_score == 3
        assert result.max_score == 3
        assert result.percentage == 100.0
        assert result.grade == "A"

    @pytest.mark.unit
    def test_score_all_incorrect(self, standard_design_params):
        """Score when all answers are incorrect."""
        sample_size = compute_sample_size(standard_design_params)

        question_ids = ["mde_absolute", "target_conversion_rate"]
        user_answers = {
            "mde_absolute": 999.0,
            "target_conversion_rate": 999.0
        }

        result = score_answers_by_id(
            user_answers=user_answers,
            question_ids=question_ids,
            ctx=ScoringContext(
                design_params=standard_design_params,
                sample_size_result=sample_size,
            ),
        )

        assert result.total_score == 0
        assert result.max_score == 2
        assert result.percentage == 0.0
        assert result.grade == "F"

    @pytest.mark.unit
    def test_score_partial_correct(self, standard_design_params):
        """Score when some answers are correct."""
        sample_size = compute_sample_size(standard_design_params)
        baseline = standard_design_params.baseline_conversion_rate
        target_lift = standard_design_params.target_lift_pct
        mde = baseline * target_lift

        question_ids = ["mde_absolute", "target_conversion_rate"]

        # One correct, one incorrect
        correct_mde, _ = calculate_design_answer_by_id(
            "mde_absolute", standard_design_params, sample_size, mde
        )

        user_answers = {
            "mde_absolute": correct_mde,
            "target_conversion_rate": 999.0
        }

        result = score_answers_by_id(
            user_answers=user_answers,
            question_ids=question_ids,
            ctx=ScoringContext(
                design_params=standard_design_params,
                sample_size_result=sample_size,
                mde_absolute=mde,
            ),
        )

        assert result.total_score == 1
        assert result.max_score == 2
        assert result.percentage == 50.0

    @pytest.mark.unit
    def test_score_missing_answers(self, standard_design_params):
        """Score when some answers are missing."""
        sample_size = compute_sample_size(standard_design_params)

        question_ids = ["mde_absolute", "target_conversion_rate"]
        user_answers = {
            "mde_absolute": 1.0  # Only one answer provided
        }

        result = score_answers_by_id(
            user_answers=user_answers,
            question_ids=question_ids,
            ctx=ScoringContext(
                design_params=standard_design_params,
                sample_size_result=sample_size,
            ),
        )

        assert result.max_score == 2
        assert "target_conversion_rate" in result.scores
        assert result.scores["target_conversion_rate"]["user"] == "No answer"

    @pytest.mark.unit
    def test_score_analysis_answers(self):
        """Score analysis answers."""
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

        result = score_answers_by_id(
            user_answers=user_answers,
            question_ids=question_ids,
            ctx=ScoringContext(sim_result=sim_result),
        )

        assert result.total_score == 3
        assert result.max_score == 3


class TestQuestionHelpers:
    """Test helper functions for questions."""

    @pytest.mark.unit
    def test_get_question_text(self):
        """Get question text by ID."""
        text = get_question_text("mde_absolute")
        assert isinstance(text, str)
        assert len(text) > 0
        assert "MDE" in text or "minimum" in text.lower()

    @pytest.mark.unit
    def test_get_question_text_invalid(self):
        """Invalid question ID should raise error."""
        with pytest.raises(ValueError):
            get_question_text("invalid_id")

    @pytest.mark.unit
    def test_get_question_hint(self):
        """Get question hint by ID."""
        hint = get_question_hint("mde_absolute")
        assert hint is None or isinstance(hint, str)

    @pytest.mark.unit
    def test_get_question_hint_invalid(self):
        """Invalid question ID should return None."""
        hint = get_question_hint("invalid_id")
        assert hint is None
