"""
Scoring and answer key generation for AB test simulator.

This module provides comprehensive scoring functions and answer key generation
for both design and analysis questions.

Supports:
1. Legacy fixed question sets (backward compatible)
2. Variable question sets using question_bank IDs
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass

from .types import SimResult, DesignParams
from .validation import (
    ValidationResult, ScoringResult,
    calculate_correct_design_answers, calculate_correct_analysis_answers,
    score_answers_by_id, calculate_design_answer_by_id, calculate_analysis_answer_by_id
)
from .question_bank import (
    Question, DESIGN_QUESTIONS, ANALYSIS_QUESTIONS,
    get_question_by_id, get_default_design_questions, get_default_analysis_questions,
    select_design_questions, select_analysis_questions
)


@dataclass(frozen=True)
class AnswerKey:
    """Answer key for quiz questions."""
    question_type: str  # "design" or "analysis"
    questions: List[Dict[str, Any]]
    correct_answers: Dict[str, Any]
    max_score: int


@dataclass(frozen=True)
class QuizResult:
    """Complete quiz result with scoring and feedback."""
    answer_key: AnswerKey
    scoring_result: ScoringResult
    user_answers: Dict[str, Any]
    feedback: List[str]


def generate_design_answer_key(design_params: DesignParams, 
                              sample_size_result: Any) -> AnswerKey:
    """
    Generate answer key for design questions.
    
    Args:
        design_params: Design parameters from scenario
        sample_size_result: Sample size calculation result
        
    Returns:
        AnswerKey with all design questions and correct answers
    """
    questions = [
        {
            "number": 1,
            "question": "What is the business's targeted minimum detectable effect (MDE) in absolute terms?",
            "hint": "Look for the MDE value in the scenario description",
            "type": "percentage_points"
        },
        {
            "number": 2,
            "question": "What is the target conversion rate for the treatment group?",
            "hint": "Calculate: Baseline Rate + MDE",
            "type": "percentage"
        },
        {
            "number": 3,
            "question": "What is the relative lift percentage?",
            "hint": "Calculate: (MDE / Baseline Rate) × 100",
            "type": "percentage"
        },
        {
            "number": 4,
            "question": "What is the required sample size per group?",
            "hint": "Use the two-proportion z-test sample size formula",
            "type": "integer"
        },
        {
            "number": 5,
            "question": "How many days will the experiment need to run?",
            "hint": "Calculate: Total Sample Size ÷ Daily Traffic",
            "type": "integer"
        },
        {
            "number": 6,
            "question": "How many additional conversions per day will the treatment generate?",
            "hint": "Calculate: Daily Traffic × MDE",
            "type": "integer"
        }
    ]
    
    correct_answers = calculate_correct_design_answers(design_params, sample_size_result)
    
    return AnswerKey(
        question_type="design",
        questions=questions,
        correct_answers=correct_answers,
        max_score=6
    )


def generate_analysis_answer_key(sim_result: SimResult) -> AnswerKey:
    """
    Generate answer key for analysis questions.
    
    Args:
        sim_result: Simulation results
        
    Returns:
        AnswerKey with all analysis questions and correct answers
    """
    questions = [
        {
            "number": 1,
            "question": "What is the conversion rate for the control group?",
            "hint": "Calculate: Control Conversions ÷ Control Users",
            "type": "percentage"
        },
        {
            "number": 2,
            "question": "What is the conversion rate for the treatment group?",
            "hint": "Calculate: Treatment Conversions ÷ Treatment Users",
            "type": "percentage"
        },
        {
            "number": 3,
            "question": "What is the absolute lift between treatment and control?",
            "hint": "Calculate: Treatment Rate - Control Rate",
            "type": "percentage_points"
        },
        {
            "number": 4,
            "question": "What is the relative lift percentage?",
            "hint": "Calculate: (Treatment Rate - Control Rate) ÷ Control Rate × 100",
            "type": "percentage"
        },
        {
            "number": 5,
            "question": "What is the p-value for the difference between groups?",
            "hint": "Perform a two-proportion z-test",
            "type": "decimal"
        },
        {
            "number": 6,
            "question": "What is the 95% confidence interval for the difference?",
            "hint": "Calculate confidence interval for difference in proportions",
            "type": "interval"
        }
    ]
    
    correct_answers = calculate_correct_analysis_answers(sim_result)
    
    return AnswerKey(
        question_type="analysis",
        questions=questions,
        correct_answers=correct_answers,
        max_score=6
    )


def generate_quiz_feedback(scoring_result: ScoringResult, 
                          answer_key: AnswerKey) -> List[str]:
    """
    Generate detailed feedback for quiz results.
    
    Args:
        scoring_result: Scoring results
        answer_key: Answer key with questions
        
    Returns:
        List of feedback strings
    """
    feedback = []
    
    # Overall performance
    feedback.append(f"Overall Score: {scoring_result.total_score}/{scoring_result.max_score} ({scoring_result.percentage:.1f}%)")
    feedback.append(f"Grade: {scoring_result.grade}")
    
    # Detailed feedback for each question
    for question in answer_key.questions:
        question_num = question["number"]
        question_key = _get_question_key(question_num, answer_key.question_type)
        
        if question_key in scoring_result.scores:
            score_info = scoring_result.scores[question_key]
            if score_info["correct"]:
                feedback.append(f"✅ Question {question_num}: Correct! Your answer: {score_info['user']}")
            else:
                feedback.append(f"❌ Question {question_num}: Incorrect. Your answer: {score_info['user']}, Correct answer: {score_info['correct']}")
        else:
            feedback.append(f"⚠️ Question {question_num}: No answer provided")
    
    return feedback


def _get_question_key(question_num: int, question_type: str) -> str:
    """Get the key for a question number and type."""
    if question_type == "design":
        keys = ["mde_absolute", "target_conversion_rate", "relative_lift_pct", 
                "sample_size", "duration", "additional_conversions"]
    else:  # analysis
        keys = ["control_conversion_rate", "treatment_conversion_rate", 
                "absolute_lift", "relative_lift", "p_value", "confidence_interval"]
    
    if 1 <= question_num <= len(keys):
        return keys[question_num - 1]
    else:
        raise ValueError(f"Invalid question number: {question_num}")


def create_complete_quiz_result(user_answers: Dict[str, Any],
                               design_params: Optional[DesignParams] = None,
                               sample_size_result: Optional[Any] = None,
                               sim_result: Optional[SimResult] = None) -> QuizResult:
    """
    Create a complete quiz result with scoring and feedback.
    
    Args:
        user_answers: User's answers
        design_params: Design parameters (for design questions)
        sample_size_result: Sample size result (for design questions)
        sim_result: Simulation results (for analysis questions)
        
    Returns:
        Complete QuizResult with scoring and feedback
    """
    if design_params is not None and sample_size_result is not None:
        # Design questions
        answer_key = generate_design_answer_key(design_params, sample_size_result)
        from .validation import score_design_answers
        scoring_result = score_design_answers(user_answers, design_params, sample_size_result)
    elif sim_result is not None:
        # Analysis questions
        answer_key = generate_analysis_answer_key(sim_result)
        from .validation import score_analysis_answers
        scoring_result = score_analysis_answers(user_answers, sim_result)
    else:
        raise ValueError("Must provide either design_params+sample_size_result or sim_result")
    
    feedback = generate_quiz_feedback(scoring_result, answer_key)
    
    return QuizResult(
        answer_key=answer_key,
        scoring_result=scoring_result,
        user_answers=user_answers,
        feedback=feedback
    )


def export_answer_key_to_csv(answer_key: AnswerKey, filename: str) -> None:
    """
    Export answer key to CSV file.
    
    Args:
        answer_key: Answer key to export
        filename: Output filename
    """
    import csv
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['question_number', 'question', 'hint', 'type', 'correct_answer']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for question in answer_key.questions:
            question_key = _get_question_key(question["number"], answer_key.question_type)
            correct_answer = answer_key.correct_answers.get(question_key, "N/A")
            
            writer.writerow({
                'question_number': question["number"],
                'question': question["question"],
                'hint': question["hint"],
                'type': question["type"],
                'correct_answer': correct_answer
            })


def export_quiz_results_to_csv(quiz_result: QuizResult, filename: str) -> None:
    """
    Export quiz results to CSV file.
    
    Args:
        quiz_result: Quiz result to export
        filename: Output filename
    """
    import csv
    
    with open(filename, 'w', newline='') as csvfile:
        fieldnames = ['question_number', 'question', 'user_answer', 'correct_answer', 'is_correct', 'tolerance']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        writer.writeheader()
        for question in quiz_result.answer_key.questions:
            question_key = _get_question_key(question["number"], quiz_result.answer_key.question_type)
            
            if question_key in quiz_result.scoring_result.scores:
                score_info = quiz_result.scoring_result.scores[question_key]
                user_answer = score_info["user"]
                correct_answer = score_info["correct"]
                is_correct = score_info["correct"]
                tolerance = score_info.get("tolerance", "N/A")
            else:
                user_answer = "No answer"
                correct_answer = quiz_result.answer_key.correct_answers.get(question_key, "N/A")
                is_correct = False
                tolerance = "N/A"
            
            writer.writerow({
                'question_number': question["number"],
                'question': question["question"],
                'user_answer': user_answer,
                'correct_answer': correct_answer,
                'is_correct': is_correct,
                'tolerance': tolerance
            })
        
        # Add summary row
        writer.writerow({
            'question_number': 'SUMMARY',
            'question': f'Total Score: {quiz_result.scoring_result.total_score}/{quiz_result.scoring_result.max_score} ({quiz_result.scoring_result.percentage:.1f}%)',
            'user_answer': f'Grade: {quiz_result.scoring_result.grade}',
            'correct_answer': 'N/A',
            'is_correct': 'N/A',
            'tolerance': 'N/A'
        })


# =============================================================================
# NEW: VARIABLE QUESTION SET SUPPORT
# =============================================================================

@dataclass(frozen=True)
class VariableAnswerKey:
    """Answer key for variable question sets (using question IDs)."""
    question_type: str  # "design" or "analysis"
    question_ids: List[str]
    questions: List[Question]
    correct_answers: Dict[str, Any]
    max_score: int


@dataclass(frozen=True)
class VariableQuizResult:
    """Complete quiz result with variable question sets."""
    answer_key: VariableAnswerKey
    scoring_result: ScoringResult
    user_answers: Dict[str, Any]
    feedback: List[str]


def generate_variable_design_answer_key(
    question_ids: List[str],
    design_params: DesignParams,
    sample_size_result: Any,
    mde_absolute: Optional[float] = None
) -> VariableAnswerKey:
    """
    Generate answer key for a variable set of design questions.

    Args:
        question_ids: List of question IDs from question_bank
        design_params: Design parameters from scenario
        sample_size_result: Sample size calculation result
        mde_absolute: Pre-calculated MDE absolute value

    Returns:
        VariableAnswerKey with selected questions and correct answers
    """
    questions = []
    correct_answers = {}

    for qid in question_ids:
        question = get_question_by_id(qid)
        if question is None:
            raise ValueError(f"Unknown question ID: {qid}")
        questions.append(question)

        try:
            answer, _ = calculate_design_answer_by_id(
                qid, design_params, sample_size_result, mde_absolute
            )
            correct_answers[qid] = answer
        except Exception as e:
            correct_answers[qid] = f"Error: {str(e)}"

    return VariableAnswerKey(
        question_type="design",
        question_ids=question_ids,
        questions=questions,
        correct_answers=correct_answers,
        max_score=len(question_ids)
    )


def generate_variable_analysis_answer_key(
    question_ids: List[str],
    sim_result: SimResult,
    business_target_absolute: Optional[float] = None,
    alpha: float = 0.05
) -> VariableAnswerKey:
    """
    Generate answer key for a variable set of analysis questions.

    Args:
        question_ids: List of question IDs from question_bank
        sim_result: Simulation results
        business_target_absolute: Business target for rollout decision
        alpha: Significance level

    Returns:
        VariableAnswerKey with selected questions and correct answers
    """
    questions = []
    correct_answers = {}

    for qid in question_ids:
        question = get_question_by_id(qid)
        if question is None:
            raise ValueError(f"Unknown question ID: {qid}")
        questions.append(question)

        try:
            answer, _ = calculate_analysis_answer_by_id(
                qid, sim_result, business_target_absolute, alpha
            )
            correct_answers[qid] = answer
        except Exception as e:
            correct_answers[qid] = f"Error: {str(e)}"

    return VariableAnswerKey(
        question_type="analysis",
        question_ids=question_ids,
        questions=questions,
        correct_answers=correct_answers,
        max_score=len(question_ids)
    )


def generate_variable_quiz_feedback(
    scoring_result: ScoringResult,
    answer_key: VariableAnswerKey
) -> List[str]:
    """
    Generate detailed feedback for variable quiz results.

    Args:
        scoring_result: Scoring results
        answer_key: Variable answer key with questions

    Returns:
        List of feedback strings
    """
    feedback = []

    # Overall performance
    feedback.append(f"Overall Score: {scoring_result.total_score}/{scoring_result.max_score} ({scoring_result.percentage:.1f}%)")
    feedback.append(f"Grade: {scoring_result.grade}")

    # Detailed feedback for each question
    for i, question in enumerate(answer_key.questions, 1):
        qid = question.id
        if qid in scoring_result.scores:
            score_info = scoring_result.scores[qid]
            if score_info["correct"]:
                feedback.append(f"✅ Q{i} ({qid}): Correct! Your answer: {score_info['user']}")
            else:
                feedback.append(f"❌ Q{i} ({qid}): Incorrect. Your answer: {score_info['user']}, Correct: {score_info['correct_answer']}")

            # Add hint if available
            if question.hint and not score_info["correct"]:
                feedback.append(f"   Hint: {question.hint}")
        else:
            feedback.append(f"⚠️ Q{i} ({qid}): No answer provided")

    return feedback


def create_variable_quiz_result(
    user_answers: Dict[str, Any],
    question_ids: List[str],
    design_params: Optional[DesignParams] = None,
    sample_size_result: Optional[Any] = None,
    sim_result: Optional[SimResult] = None,
    mde_absolute: Optional[float] = None,
    business_target_absolute: Optional[float] = None,
    alpha: float = 0.05
) -> VariableQuizResult:
    """
    Create a complete variable quiz result with scoring and feedback.

    Args:
        user_answers: Dict mapping question_id to user's answer
        question_ids: List of question IDs to score
        design_params: Design parameters (for design questions)
        sample_size_result: Sample size result (for design questions)
        sim_result: Simulation results (for analysis questions)
        mde_absolute: Pre-calculated MDE absolute value
        business_target_absolute: Business target for decision questions
        alpha: Significance level

    Returns:
        Complete VariableQuizResult with scoring and feedback
    """
    # Determine if this is design or analysis based on first question
    first_qid = question_ids[0] if question_ids else None
    is_design = first_qid in DESIGN_QUESTIONS if first_qid else False

    if is_design:
        if design_params is None or sample_size_result is None:
            raise ValueError("design_params and sample_size_result required for design questions")
        answer_key = generate_variable_design_answer_key(
            question_ids, design_params, sample_size_result, mde_absolute
        )
    else:
        if sim_result is None:
            raise ValueError("sim_result required for analysis questions")
        answer_key = generate_variable_analysis_answer_key(
            question_ids, sim_result, business_target_absolute, alpha
        )

    # Score the answers
    scoring_result = score_answers_by_id(
        user_answers=user_answers,
        question_ids=question_ids,
        design_params=design_params,
        sample_size_result=sample_size_result,
        sim_result=sim_result,
        mde_absolute=mde_absolute,
        business_target_absolute=business_target_absolute,
        alpha=alpha
    )

    # Generate feedback
    feedback = generate_variable_quiz_feedback(scoring_result, answer_key)

    return VariableQuizResult(
        answer_key=answer_key,
        scoring_result=scoring_result,
        user_answers=user_answers,
        feedback=feedback
    )


def select_and_create_design_quiz(
    design_params: DesignParams,
    sample_size_result: Any,
    question_count: int = 6,
    mde_absolute: Optional[float] = None,
    seed: Optional[int] = None
) -> VariableAnswerKey:
    """
    Select random design questions and create an answer key.

    Args:
        design_params: Design parameters from scenario
        sample_size_result: Sample size calculation result
        question_count: Number of questions to select
        mde_absolute: Pre-calculated MDE absolute value
        seed: Random seed for reproducibility

    Returns:
        VariableAnswerKey with randomly selected questions
    """
    questions = select_design_questions(count=question_count, seed=seed)
    question_ids = [q.id for q in questions]

    return generate_variable_design_answer_key(
        question_ids, design_params, sample_size_result, mde_absolute
    )


def select_and_create_analysis_quiz(
    sim_result: SimResult,
    question_count: int = 7,
    business_target_absolute: Optional[float] = None,
    alpha: float = 0.05,
    seed: Optional[int] = None
) -> VariableAnswerKey:
    """
    Select random analysis questions and create an answer key.

    Args:
        sim_result: Simulation results
        question_count: Number of questions to select
        business_target_absolute: Business target for rollout decision
        alpha: Significance level
        seed: Random seed for reproducibility

    Returns:
        VariableAnswerKey with randomly selected questions
    """
    questions = select_analysis_questions(count=question_count, seed=seed)
    question_ids = [q.id for q in questions]

    return generate_variable_analysis_answer_key(
        question_ids, sim_result, business_target_absolute, alpha
    )
