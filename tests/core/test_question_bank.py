"""
Tests for core.question_bank module - Question pool system for variable quizzes.
"""

import pytest
from core.question_bank import (
    Question, QuestionCategory, QuestionDifficulty, AnswerType,
    DESIGN_QUESTIONS, ANALYSIS_QUESTIONS, PLANNING_QUESTIONS, INTERPRETATION_QUESTIONS,
    get_question_by_id, get_all_questions, get_questions_by_category, get_question_pool_summary,
    get_default_design_questions, get_default_analysis_questions,
    get_default_planning_questions, get_default_interpretation_questions,
    select_design_questions, select_analysis_questions,
    select_planning_questions, select_interpretation_questions, select_advanced_questions
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
        """Should return all questions from all pools."""
        all_questions = get_all_questions()
        expected_count = (
            len(DESIGN_QUESTIONS) + len(ANALYSIS_QUESTIONS) +
            len(PLANNING_QUESTIONS) + len(INTERPRETATION_QUESTIONS)
        )
        assert len(all_questions) == expected_count

        # Check that all questions from each pool are included
        for qid in DESIGN_QUESTIONS:
            assert qid in all_questions

        for qid in ANALYSIS_QUESTIONS:
            assert qid in all_questions

        for qid in PLANNING_QUESTIONS:
            assert qid in all_questions

        for qid in INTERPRETATION_QUESTIONS:
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


class TestPlanningQuestions:
    """Test planning phase question definitions and selection."""

    @pytest.mark.unit
    def test_planning_questions_have_required_fields(self):
        """All planning questions should have required fields."""
        for qid, question in PLANNING_QUESTIONS.items():
            assert question.id == qid, f"Question ID mismatch for {qid}"
            assert question.text, f"Question {qid} missing text"
            assert isinstance(question.category, QuestionCategory)
            assert isinstance(question.answer_type, AnswerType)
            assert isinstance(question.difficulty, QuestionDifficulty)
            assert question.tolerance >= 0, f"Question {qid} has negative tolerance"

    @pytest.mark.unit
    def test_planning_questions_count(self):
        """Should have at least 10 planning questions."""
        assert len(PLANNING_QUESTIONS) >= 10

    @pytest.mark.unit
    def test_planning_questions_category(self):
        """All planning questions should be in PLANNING category."""
        for qid, question in PLANNING_QUESTIONS.items():
            assert question.category == QuestionCategory.PLANNING, f"{qid} has wrong category"

    @pytest.mark.unit
    def test_planning_questions_have_hints(self):
        """Planning questions should have hints."""
        for qid, question in PLANNING_QUESTIONS.items():
            assert question.hint is not None, f"Question {qid} missing hint"
            assert len(question.hint) > 0, f"Question {qid} has empty hint"

    @pytest.mark.unit
    def test_get_question_by_id_planning(self):
        """Should return correct planning question by ID."""
        question = get_question_by_id("hypothesis_null")
        assert question is not None
        assert question.id == "hypothesis_null"
        assert question.category == QuestionCategory.PLANNING

    @pytest.mark.unit
    def test_default_planning_questions(self):
        """Default planning questions should be valid IDs."""
        default_ids = get_default_planning_questions()
        assert len(default_ids) == 5

        for qid in default_ids:
            question = get_question_by_id(qid)
            assert question is not None, f"Invalid default planning question: {qid}"
            assert qid in PLANNING_QUESTIONS

    @pytest.mark.unit
    def test_select_planning_questions_default(self):
        """Should select 5 planning questions by default."""
        questions = select_planning_questions(seed=42)
        assert len(questions) == 5

    @pytest.mark.unit
    def test_select_planning_questions_by_difficulty(self):
        """Should filter planning questions by difficulty."""
        questions = select_planning_questions(
            count=10,
            difficulty=QuestionDifficulty.HARD,
            seed=42
        )
        for q in questions:
            assert q.difficulty == QuestionDifficulty.HARD

    @pytest.mark.unit
    def test_select_planning_questions_reproducible(self):
        """Same seed should produce same selection."""
        q1 = select_planning_questions(count=3, seed=42)
        q2 = select_planning_questions(count=3, seed=42)
        assert [q.id for q in q1] == [q.id for q in q2]


class TestInterpretationQuestions:
    """Test interpretation phase question definitions and selection."""

    @pytest.mark.unit
    def test_interpretation_questions_have_required_fields(self):
        """All interpretation questions should have required fields."""
        for qid, question in INTERPRETATION_QUESTIONS.items():
            assert question.id == qid, f"Question ID mismatch for {qid}"
            assert question.text, f"Question {qid} missing text"
            assert isinstance(question.category, QuestionCategory)
            assert isinstance(question.answer_type, AnswerType)
            assert isinstance(question.difficulty, QuestionDifficulty)
            assert question.tolerance >= 0, f"Question {qid} has negative tolerance"

    @pytest.mark.unit
    def test_interpretation_questions_count(self):
        """Should have at least 10 interpretation questions."""
        assert len(INTERPRETATION_QUESTIONS) >= 10

    @pytest.mark.unit
    def test_interpretation_questions_category(self):
        """All interpretation questions should be in INTERPRETATION category."""
        for qid, question in INTERPRETATION_QUESTIONS.items():
            assert question.category == QuestionCategory.INTERPRETATION, f"{qid} has wrong category"

    @pytest.mark.unit
    def test_interpretation_questions_have_hints(self):
        """Interpretation questions should have hints."""
        for qid, question in INTERPRETATION_QUESTIONS.items():
            assert question.hint is not None, f"Question {qid} missing hint"
            assert len(question.hint) > 0, f"Question {qid} has empty hint"

    @pytest.mark.unit
    def test_get_question_by_id_interpretation(self):
        """Should return correct interpretation question by ID."""
        question = get_question_by_id("statistical_vs_practical")
        assert question is not None
        assert question.id == "statistical_vs_practical"
        assert question.category == QuestionCategory.INTERPRETATION

    @pytest.mark.unit
    def test_default_interpretation_questions(self):
        """Default interpretation questions should be valid IDs."""
        default_ids = get_default_interpretation_questions()
        assert len(default_ids) == 5

        for qid in default_ids:
            question = get_question_by_id(qid)
            assert question is not None, f"Invalid default interpretation question: {qid}"
            assert qid in INTERPRETATION_QUESTIONS

    @pytest.mark.unit
    def test_select_interpretation_questions_default(self):
        """Should select 5 interpretation questions by default."""
        questions = select_interpretation_questions(seed=42)
        assert len(questions) == 5

    @pytest.mark.unit
    def test_select_interpretation_questions_by_difficulty(self):
        """Should filter interpretation questions by difficulty."""
        questions = select_interpretation_questions(
            count=10,
            difficulty=QuestionDifficulty.MEDIUM,
            seed=42
        )
        for q in questions:
            assert q.difficulty == QuestionDifficulty.MEDIUM

    @pytest.mark.unit
    def test_select_interpretation_questions_reproducible(self):
        """Same seed should produce same selection."""
        q1 = select_interpretation_questions(count=3, seed=42)
        q2 = select_interpretation_questions(count=3, seed=42)
        assert [q.id for q in q1] == [q.id for q in q2]


class TestAdvancedQuestionSelection:
    """Test combined advanced question selection."""

    @pytest.mark.unit
    def test_select_advanced_questions_default(self):
        """Should select mixed planning and interpretation questions."""
        questions = select_advanced_questions(seed=42)
        assert len(questions) == 6  # 3 planning + 3 interpretation

    @pytest.mark.unit
    def test_select_advanced_questions_custom_counts(self):
        """Should respect custom counts for each category."""
        questions = select_advanced_questions(
            planning_count=2,
            interpretation_count=4,
            seed=42
        )
        assert len(questions) == 6

        planning_count = sum(1 for q in questions if q.category == QuestionCategory.PLANNING)
        interpretation_count = sum(1 for q in questions if q.category == QuestionCategory.INTERPRETATION)
        assert planning_count == 2
        assert interpretation_count == 4

    @pytest.mark.unit
    def test_select_advanced_questions_by_difficulty(self):
        """Should filter by difficulty."""
        questions = select_advanced_questions(
            planning_count=5,
            interpretation_count=5,
            difficulty=QuestionDifficulty.HARD,
            seed=42
        )
        for q in questions:
            assert q.difficulty == QuestionDifficulty.HARD


class TestQuestionPoolUtilities:
    """Test utility functions for question pools."""

    @pytest.mark.unit
    def test_get_all_questions_includes_all_pools(self):
        """Should return all questions from all four pools."""
        all_questions = get_all_questions()
        expected_count = (
            len(DESIGN_QUESTIONS) +
            len(ANALYSIS_QUESTIONS) +
            len(PLANNING_QUESTIONS) +
            len(INTERPRETATION_QUESTIONS)
        )
        assert len(all_questions) == expected_count

        # Check that all pools are included
        for qid in DESIGN_QUESTIONS:
            assert qid in all_questions
        for qid in ANALYSIS_QUESTIONS:
            assert qid in all_questions
        for qid in PLANNING_QUESTIONS:
            assert qid in all_questions
        for qid in INTERPRETATION_QUESTIONS:
            assert qid in all_questions

    @pytest.mark.unit
    def test_get_questions_by_category(self):
        """Should filter questions by category."""
        planning = get_questions_by_category(QuestionCategory.PLANNING)
        assert len(planning) == len(PLANNING_QUESTIONS)
        for qid, q in planning.items():
            assert q.category == QuestionCategory.PLANNING

        interpretation = get_questions_by_category(QuestionCategory.INTERPRETATION)
        assert len(interpretation) == len(INTERPRETATION_QUESTIONS)
        for qid, q in interpretation.items():
            assert q.category == QuestionCategory.INTERPRETATION

    @pytest.mark.unit
    def test_get_question_pool_summary(self):
        """Should return correct counts for each pool."""
        summary = get_question_pool_summary()

        assert summary["design"] == len(DESIGN_QUESTIONS)
        assert summary["analysis"] == len(ANALYSIS_QUESTIONS)
        assert summary["planning"] == len(PLANNING_QUESTIONS)
        assert summary["interpretation"] == len(INTERPRETATION_QUESTIONS)
        assert summary["total"] == len(get_all_questions())

    @pytest.mark.unit
    def test_question_pool_summary_matches_all_questions(self):
        """Summary total should match get_all_questions count."""
        summary = get_question_pool_summary()
        all_questions = get_all_questions()
        assert summary["total"] == len(all_questions)
