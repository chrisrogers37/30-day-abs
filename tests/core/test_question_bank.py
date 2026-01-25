"""
Tests for core.question_bank module - Question pool system for variable quizzes.
"""

import pytest
from core.question_bank import (
    Question, QuestionCategory, QuestionDifficulty, AnswerType,
    DESIGN_QUESTIONS, ANALYSIS_QUESTIONS,
    get_question_by_id, get_all_questions,
    get_default_design_questions, get_default_analysis_questions,
    select_design_questions, select_analysis_questions
)


class TestQuestionDefinitions:
    """Test that question definitions are valid and complete."""

    @pytest.mark.unit
    def test_design_questions_have_required_fields(self):
        """All design questions should have required fields."""
        for qid, question in DESIGN_QUESTIONS.items():
            assert question.id == qid, f"Question ID mismatch for {qid}"
            assert question.text, f"Question {qid} missing text"
            assert isinstance(question.category, QuestionCategory)
            assert isinstance(question.answer_type, AnswerType)
            assert isinstance(question.difficulty, QuestionDifficulty)
            assert question.tolerance >= 0, f"Question {qid} has negative tolerance"

    @pytest.mark.unit
    def test_analysis_questions_have_required_fields(self):
        """All analysis questions should have required fields."""
        for qid, question in ANALYSIS_QUESTIONS.items():
            assert question.id == qid, f"Question ID mismatch for {qid}"
            assert question.text, f"Question {qid} missing text"
            assert isinstance(question.category, QuestionCategory)
            assert isinstance(question.answer_type, AnswerType)
            assert isinstance(question.difficulty, QuestionDifficulty)
            assert question.tolerance >= 0, f"Question {qid} has negative tolerance"

    @pytest.mark.unit
    def test_design_questions_count(self):
        """Should have at least 6 design questions."""
        assert len(DESIGN_QUESTIONS) >= 6

    @pytest.mark.unit
    def test_analysis_questions_count(self):
        """Should have at least 7 analysis questions."""
        assert len(ANALYSIS_QUESTIONS) >= 7

    @pytest.mark.unit
    def test_question_categories_are_appropriate(self):
        """Design questions should be in design categories, analysis in analysis."""
        design_categories = {
            QuestionCategory.MDE_UNDERSTANDING,
            QuestionCategory.SAMPLE_SIZE,
            QuestionCategory.DURATION,
            QuestionCategory.POWER_ANALYSIS
        }
        analysis_categories = {
            QuestionCategory.RATE_CALCULATION,
            QuestionCategory.LIFT_CALCULATION,
            QuestionCategory.STATISTICAL_TESTING,
            QuestionCategory.DECISION_MAKING
        }

        for qid, question in DESIGN_QUESTIONS.items():
            assert question.category in design_categories, f"Design question {qid} has wrong category"

        for qid, question in ANALYSIS_QUESTIONS.items():
            assert question.category in analysis_categories, f"Analysis question {qid} has wrong category"


class TestQuestionLookup:
    """Test question lookup functions."""

    @pytest.mark.unit
    def test_get_question_by_id_design(self):
        """Should return correct design question by ID."""
        question = get_question_by_id("mde_absolute")
        assert question is not None
        assert question.id == "mde_absolute"
        assert question.category == QuestionCategory.MDE_UNDERSTANDING

    @pytest.mark.unit
    def test_get_question_by_id_analysis(self):
        """Should return correct analysis question by ID."""
        question = get_question_by_id("control_rate")
        assert question is not None
        assert question.id == "control_rate"
        assert question.category == QuestionCategory.RATE_CALCULATION

    @pytest.mark.unit
    def test_get_question_by_id_invalid(self):
        """Should return None for invalid question ID."""
        question = get_question_by_id("invalid_question_id")
        assert question is None

    @pytest.mark.unit
    def test_get_all_questions(self):
        """Should return all questions from both pools."""
        all_questions = get_all_questions()
        assert len(all_questions) == len(DESIGN_QUESTIONS) + len(ANALYSIS_QUESTIONS)

        # Check that all design questions are included
        for qid in DESIGN_QUESTIONS:
            assert qid in all_questions

        # Check that all analysis questions are included
        for qid in ANALYSIS_QUESTIONS:
            assert qid in all_questions


class TestDefaultQuestions:
    """Test default question set functions."""

    @pytest.mark.unit
    def test_default_design_questions(self):
        """Default design questions should be valid IDs."""
        default_ids = get_default_design_questions()
        assert len(default_ids) == 6

        for qid in default_ids:
            question = get_question_by_id(qid)
            assert question is not None, f"Invalid default design question: {qid}"
            assert qid in DESIGN_QUESTIONS

    @pytest.mark.unit
    def test_default_analysis_questions(self):
        """Default analysis questions should be valid IDs."""
        default_ids = get_default_analysis_questions()
        assert len(default_ids) == 7

        for qid in default_ids:
            question = get_question_by_id(qid)
            assert question is not None, f"Invalid default analysis question: {qid}"
            assert qid in ANALYSIS_QUESTIONS


class TestQuestionSelection:
    """Test random question selection functions."""

    @pytest.mark.unit
    def test_select_design_questions_default_count(self):
        """Should select 6 design questions by default."""
        questions = select_design_questions(seed=42)
        assert len(questions) == 6

    @pytest.mark.unit
    def test_select_design_questions_custom_count(self):
        """Should select specified number of questions."""
        questions = select_design_questions(count=3, seed=42)
        assert len(questions) == 3

    @pytest.mark.unit
    def test_select_design_questions_max_count(self):
        """Should not exceed available questions."""
        questions = select_design_questions(count=100, seed=42)
        assert len(questions) <= len(DESIGN_QUESTIONS)

    @pytest.mark.unit
    def test_select_design_questions_reproducible(self):
        """Same seed should produce same selection."""
        q1 = select_design_questions(count=3, seed=42)
        q2 = select_design_questions(count=3, seed=42)
        assert [q.id for q in q1] == [q.id for q in q2]

    @pytest.mark.unit
    def test_select_design_questions_by_category(self):
        """Should filter by category."""
        questions = select_design_questions(
            count=10,
            categories=[QuestionCategory.MDE_UNDERSTANDING],
            seed=42
        )
        for q in questions:
            assert q.category == QuestionCategory.MDE_UNDERSTANDING

    @pytest.mark.unit
    def test_select_design_questions_by_difficulty(self):
        """Should filter by difficulty."""
        questions = select_design_questions(
            count=10,
            difficulty=QuestionDifficulty.EASY,
            seed=42
        )
        for q in questions:
            assert q.difficulty == QuestionDifficulty.EASY

    @pytest.mark.unit
    def test_select_analysis_questions_default_count(self):
        """Should select 7 analysis questions by default."""
        questions = select_analysis_questions(seed=42)
        assert len(questions) == 7

    @pytest.mark.unit
    def test_select_analysis_questions_reproducible(self):
        """Same seed should produce same selection."""
        q1 = select_analysis_questions(count=3, seed=42)
        q2 = select_analysis_questions(count=3, seed=42)
        assert [q.id for q in q1] == [q.id for q in q2]


class TestQuestionDataclassFeatures:
    """Test Question dataclass features."""

    @pytest.mark.unit
    def test_question_has_skills_tested(self):
        """Questions should have skills_tested field."""
        question = get_question_by_id("mde_absolute")
        assert hasattr(question, 'skills_tested')
        assert isinstance(question.skills_tested, list)

    @pytest.mark.unit
    def test_question_has_hint(self):
        """Questions should have hint field."""
        question = get_question_by_id("mde_absolute")
        assert hasattr(question, 'hint')
        # Hint can be None or a string
        assert question.hint is None or isinstance(question.hint, str)

    @pytest.mark.unit
    def test_question_has_explanation_template(self):
        """Questions should have explanation_template field."""
        question = get_question_by_id("mde_absolute")
        assert hasattr(question, 'explanation_template')
        assert isinstance(question.explanation_template, str)
