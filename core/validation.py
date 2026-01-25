"""
Validation and scoring logic for AB test simulator.

This module provides validation and scoring functions for quiz answers,
ensuring consistent logic across all UI components.

Supports both:
1. Legacy question number-based validation (backward compatible)
2. New question ID-based validation (from question_bank.py)
"""

from typing import Dict, Any, Optional, Tuple, List, Union
from dataclasses import dataclass

from .types import SimResult, DesignParams
from .design import compute_sample_size
from .question_bank import (
    Question, AnswerType, DESIGN_QUESTIONS, ANALYSIS_QUESTIONS,
    get_question_by_id, get_default_design_questions, get_default_analysis_questions
)


@dataclass(frozen=True)
class ValidationResult:
    """Result of answer validation."""
    is_correct: bool
    correct_answer: Any
    feedback: str
    tolerance: float


@dataclass(frozen=True)
class ScoringResult:
    """Result of quiz scoring."""
    scores: Dict[str, Dict[str, Any]]
    total_score: int
    max_score: int
    percentage: float
    grade: str


def validate_design_answer(question_num: int, user_answer: float, 
                          design_params: DesignParams, 
                          sample_size_result: Optional[Any] = None,
                          mde_absolute: Optional[float] = None) -> ValidationResult:
    """
    Validate a single design question answer.
    
    Args:
        question_num: Question number (1-6)
        user_answer: User's answer
        design_params: Design parameters from scenario
        sample_size_result: Sample size calculation result
        
    Returns:
        ValidationResult with correctness and feedback
    """
    baseline = design_params.baseline_conversion_rate
    target_lift = design_params.target_lift_pct
    # Use provided mde_absolute or calculate as fallback
    if mde_absolute is None:
        mde_absolute = baseline * target_lift  # Fallback calculation
    
    if question_num == 1:
        # Question 1: Business's targeted MDE
        correct_answer = mde_absolute * 100  # Convert to percentage points
        tolerance = 0.5  # 0.5 percentage points tolerance
        is_correct = abs(user_answer - correct_answer) <= tolerance
        feedback = f"Correct answer: {correct_answer:.1f} percentage points"
        
    elif question_num == 2:
        # Question 2: Target conversion rate calculation
        correct_answer = (baseline + mde_absolute) * 100  # Convert to percentage
        tolerance = 0.5  # 0.5% tolerance
        is_correct = abs(user_answer - correct_answer) <= tolerance
        feedback = f"Correct answer: {correct_answer:.1f}%"
        
    elif question_num == 3:
        # Question 3: Relative lift calculation from MDE
        correct_answer = (mde_absolute / baseline) * 100  # Convert to relative lift percentage
        tolerance = 2.0  # 2% tolerance for relative lift
        is_correct = abs(user_answer - correct_answer) <= tolerance
        feedback = f"Correct answer: {correct_answer:.1f}%"
        
    elif question_num == 4:
        # Question 4: Sample size calculation
        if sample_size_result is None:
            sample_size_result = compute_sample_size(design_params)
        correct_answer = sample_size_result.per_arm
        tolerance = 50  # 50 users tolerance
        is_correct = abs(user_answer - correct_answer) <= tolerance
        feedback = f"Correct answer: {correct_answer:,} users per group"
        
    elif question_num == 5:
        # Question 5: Duration calculation
        if sample_size_result is None:
            sample_size_result = compute_sample_size(design_params)
        required_sample_size = sample_size_result.per_arm * 2  # Total sample size
        correct_answer = max(1, round(required_sample_size / design_params.expected_daily_traffic))
        tolerance = 1  # 1 day tolerance
        is_correct = abs(user_answer - correct_answer) <= tolerance
        feedback = f"Correct answer: {correct_answer} days"
        
    elif question_num == 6:
        # Question 6: Additional conversions per day
        correct_answer = round(design_params.expected_daily_traffic * mde_absolute)
        tolerance = 5  # 5 conversions tolerance
        is_correct = abs(user_answer - correct_answer) <= tolerance
        feedback = f"Correct answer: {correct_answer} additional conversions per day"
        
    else:
        raise ValueError(f"Invalid question number: {question_num}")
    
    return ValidationResult(
        is_correct=is_correct,
        correct_answer=correct_answer,
        feedback=feedback,
        tolerance=tolerance
    )


def validate_analysis_answer(question_num: int, user_answer: float, 
                           sim_result: SimResult, business_target_absolute: float = None) -> ValidationResult:
    """
    Validate a single analysis question answer.
    
    Args:
        question_num: Question number (1-7)
        user_answer: User's answer
        sim_result: Simulation results
        business_target_absolute: Business target absolute lift for Question 7
        
    Returns:
        ValidationResult with correctness and feedback
    """
    if question_num == 1:
        # Question 1: Control conversion rate
        correct_answer = sim_result.control_rate * 100  # Convert to percentage
        tolerance = 0.05  # 0.05% tolerance
        is_correct = abs(user_answer - correct_answer) <= tolerance
        feedback = f"Correct answer: {correct_answer:.3f}%"
        
    elif question_num == 2:
        # Question 2: Treatment conversion rate
        correct_answer = sim_result.treatment_rate * 100  # Convert to percentage
        tolerance = 0.05  # 0.05% tolerance
        is_correct = abs(user_answer - correct_answer) <= tolerance
        feedback = f"Correct answer: {correct_answer:.3f}%"
        
    elif question_num == 3:
        # Question 3: Absolute lift
        correct_answer = sim_result.absolute_lift * 100  # Convert to percentage points
        tolerance = 0.01  # 0.01 percentage point tolerance
        is_correct = abs(user_answer - correct_answer) <= tolerance
        feedback = f"Correct answer: {correct_answer:.3f} percentage points"
        
    elif question_num == 4:
        # Question 4: Relative lift
        correct_answer = sim_result.relative_lift_pct * 100  # Convert to percentage
        tolerance = 0.5  # 0.5% tolerance
        is_correct = abs(user_answer - correct_answer) <= tolerance
        feedback = f"Correct answer: {correct_answer:.1f}%"
        
    elif question_num == 5:
        # Question 5: P-value
        from .analyze import analyze_results
        analysis = analyze_results(sim_result, alpha=0.05)
        correct_answer = analysis.p_value
        tolerance = 0.001  # 0.001 tolerance
        is_correct = abs(user_answer - correct_answer) <= tolerance
        feedback = f"Correct answer: {correct_answer:.3f}"
        
    elif question_num == 6:
        # Question 6: Confidence interval
        from .analyze import analyze_results
        analysis = analyze_results(sim_result, alpha=0.05)
        ci_lower, ci_upper = analysis.confidence_interval
        correct_answer = (ci_lower * 100, ci_upper * 100)  # Convert to percentage points
        tolerance = 0.01  # 0.01 percentage point tolerance
        
        # For confidence interval, we need to check if user provided both bounds
        if isinstance(user_answer, tuple) and len(user_answer) == 2:
            user_lower, user_upper = user_answer
            is_correct = (abs(user_lower - correct_answer[0]) <= tolerance and 
                         abs(user_upper - correct_answer[1]) <= tolerance)
        else:
            is_correct = False
            
        feedback = f"Correct answer: [{correct_answer[0]:.2f}%, {correct_answer[1]:.2f}%]"
        
    elif question_num == 7:
        # Question 7: Rollout decision
        if business_target_absolute is None:
            raise ValueError("business_target_absolute is required for Question 7")
        
        from .analyze import analyze_results, make_rollout_decision
        analysis = analyze_results(sim_result, alpha=0.05)
        correct_answer = make_rollout_decision(sim_result, analysis, business_target_absolute)
        tolerance = "exact_match"
        is_correct = str(user_answer).lower() == correct_answer.lower()
        feedback = f"Correct answer: {correct_answer}"
        
    else:
        raise ValueError(f"Invalid question number: {question_num}")
    
    return ValidationResult(
        is_correct=is_correct,
        correct_answer=correct_answer,
        feedback=feedback,
        tolerance=tolerance
    )


def calculate_correct_design_answers(design_params: DesignParams, 
                                   sample_size_result: Any,
                                   mde_absolute: Optional[float] = None) -> Dict[str, Any]:
    """
    Calculate correct answers for all design questions.
    
    Args:
        design_params: Design parameters from scenario
        sample_size_result: Sample size calculation result
        
    Returns:
        Dictionary with correct answers for all design questions
    """
    baseline = design_params.baseline_conversion_rate
    target_lift = design_params.target_lift_pct
    # Use provided mde_absolute or calculate as fallback
    if mde_absolute is None:
        mde_absolute = baseline * target_lift  # Fallback calculation
    
    # Calculate correct answers
    correct_mde_absolute = mde_absolute * 100  # Convert to percentage points
    correct_target_rate = (baseline + mde_absolute) * 100  # Convert to percentage
    correct_relative_lift = (mde_absolute / baseline) * 100  # Convert to percentage
    correct_sample_size = sample_size_result.per_arm
    
    # Calculate duration
    required_sample_size = correct_sample_size * 2  # Total sample size
    correct_duration = max(1, round(required_sample_size / design_params.expected_daily_traffic))
    
    # Calculate additional conversions per day
    correct_additional_conversions = round(design_params.expected_daily_traffic * mde_absolute)
    
    return {
        "mde_absolute": correct_mde_absolute,
        "target_conversion_rate": correct_target_rate,
        "relative_lift_pct": correct_relative_lift,
        "sample_size": correct_sample_size,
        "duration": correct_duration,
        "additional_conversions": correct_additional_conversions
    }


def calculate_correct_analysis_answers(sim_result: SimResult, business_target_absolute: float = None) -> Dict[str, Any]:
    """
    Calculate correct answers for all analysis questions.
    
    Args:
        sim_result: Simulation results
        business_target_absolute: Business target absolute lift for rollout decision
        
    Returns:
        Dictionary with correct answers for all analysis questions
    """
    from .analyze import analyze_results, make_rollout_decision
    
    # Run analysis to get p-value and confidence interval
    analysis = analyze_results(sim_result, alpha=0.05)
    
    # Calculate correct answers
    correct_control_rate = sim_result.control_rate * 100  # Convert to percentage
    correct_treatment_rate = sim_result.treatment_rate * 100  # Convert to percentage
    correct_absolute_lift = sim_result.absolute_lift * 100  # Convert to percentage points
    correct_relative_lift = sim_result.relative_lift_pct * 100  # Convert to percentage
    correct_p_value = analysis.p_value
    correct_ci_lower, correct_ci_upper = analysis.confidence_interval
    correct_ci = (correct_ci_lower * 100, correct_ci_upper * 100)  # Convert to percentage points
    
    # Calculate rollout decision if business target provided
    correct_rollout_decision = None
    if business_target_absolute is not None:
        correct_rollout_decision = make_rollout_decision(sim_result, analysis, business_target_absolute)
    
    result = {
        "control_conversion_rate": correct_control_rate,
        "treatment_conversion_rate": correct_treatment_rate,
        "absolute_lift": correct_absolute_lift,
        "relative_lift": correct_relative_lift,
        "p_value": correct_p_value,
        "confidence_interval": correct_ci
    }
    
    if correct_rollout_decision is not None:
        result["rollout_decision"] = correct_rollout_decision
    
    return result


def score_design_answers(user_answers: Dict[str, Any], 
                        design_params: DesignParams,
                        sample_size_result: Any,
                        mde_absolute: Optional[float] = None) -> ScoringResult:
    """
    Score design question answers.
    
    Args:
        user_answers: User's answers
        design_params: Design parameters from scenario
        sample_size_result: Sample size calculation result
        
    Returns:
        ScoringResult with scores and feedback
    """
    # Calculate correct answers
    correct_answers = calculate_correct_design_answers(design_params, sample_size_result, mde_absolute)
    
    # Score each answer
    scores = {}
    total_score = 0
    max_score = 6
    
    # Question 1: MDE (absolute)
    user_mde = user_answers.get("mde_absolute", 0)
    correct_mde = correct_answers["mde_absolute"]
    tolerance = 0.5
    is_correct = abs(user_mde - correct_mde) <= tolerance
    scores["mde_absolute"] = {
        "correct": is_correct,
        "user": user_mde,
        "correct_answer": correct_mde,
        "tolerance": tolerance
    }
    if is_correct:
        total_score += 1
    
    # Question 2: Target conversion rate
    user_target = user_answers.get("target_conversion_rate", 0)
    correct_target = correct_answers["target_conversion_rate"]
    tolerance = 0.5
    is_correct = abs(user_target - correct_target) <= tolerance
    scores["target_conversion_rate"] = {
        "correct": is_correct,
        "user": user_target,
        "correct_answer": correct_target,
        "tolerance": tolerance
    }
    if is_correct:
        total_score += 1
    
    # Question 3: Relative lift
    user_relative = user_answers.get("relative_lift_pct", 0)
    correct_relative = correct_answers["relative_lift_pct"]
    tolerance = 2.0
    is_correct = abs(user_relative - correct_relative) <= tolerance
    scores["relative_lift_pct"] = {
        "correct": is_correct,
        "user": user_relative,
        "correct_answer": correct_relative,
        "tolerance": tolerance
    }
    if is_correct:
        total_score += 1
    
    # Question 4: Sample size
    user_sample = user_answers.get("sample_size", 0)
    correct_sample = correct_answers["sample_size"]
    tolerance = 50
    is_correct = abs(user_sample - correct_sample) <= tolerance
    scores["sample_size"] = {
        "correct": is_correct,
        "user": user_sample,
        "correct_answer": correct_sample,
        "tolerance": tolerance
    }
    if is_correct:
        total_score += 1
    
    # Question 5: Duration
    user_duration = user_answers.get("duration", 0)
    correct_duration = correct_answers["duration"]
    tolerance = 1
    is_correct = abs(user_duration - correct_duration) <= tolerance
    scores["duration"] = {
        "correct": is_correct,
        "user": user_duration,
        "correct_answer": correct_duration,
        "tolerance": tolerance
    }
    if is_correct:
        total_score += 1
    
    # Question 6: Additional conversions
    user_conversions = user_answers.get("additional_conversions", 0)
    correct_conversions = correct_answers["additional_conversions"]
    tolerance = 5
    is_correct = abs(user_conversions - correct_conversions) <= tolerance
    scores["additional_conversions"] = {
        "correct": is_correct,
        "user": user_conversions,
        "correct_answer": correct_conversions,
        "tolerance": tolerance
    }
    if is_correct:
        total_score += 1
    
    # Calculate percentage and grade
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    grade = "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D" if percentage >= 60 else "F"
    
    return ScoringResult(
        scores=scores,
        total_score=total_score,
        max_score=max_score,
        percentage=percentage,
        grade=grade
    )


def score_analysis_answers(user_answers: Dict[str, Any], 
                          sim_result: SimResult,
                          business_target_absolute: float = None) -> ScoringResult:
    """
    Score analysis question answers.
    
    Args:
        user_answers: User's answers
        sim_result: Simulation results
        business_target_absolute: Business target absolute lift for rollout decision
        
    Returns:
        ScoringResult with scores and feedback
    """
    # Calculate correct answers
    correct_answers = calculate_correct_analysis_answers(sim_result, business_target_absolute)
    
    # Score each answer
    scores = {}
    total_score = 0
    max_score = 6
    
    # Question 1: Control conversion rate
    user_control = user_answers.get("control_conversion_rate")
    if user_control is not None:
        correct_control = correct_answers["control_conversion_rate"]
        tolerance = 0.05
        is_correct = abs(user_control - correct_control) <= tolerance
        scores["control_conversion_rate"] = {
            "correct": is_correct,
            "user": user_control,
            "correct_answer": correct_control,
            "tolerance": tolerance
        }
        if is_correct:
            total_score += 1
    else:
        scores["control_conversion_rate"] = {
            "correct": False,
            "user": "No answer",
            "correct_answer": correct_answers["control_conversion_rate"],
            "tolerance": 0.05
        }
    
    # Question 2: Treatment conversion rate
    user_treatment = user_answers.get("treatment_conversion_rate")
    if user_treatment is not None:
        correct_treatment = correct_answers["treatment_conversion_rate"]
        tolerance = 0.05
        is_correct = abs(user_treatment - correct_treatment) <= tolerance
        scores["treatment_conversion_rate"] = {
            "correct": is_correct,
            "user": user_treatment,
            "correct_answer": correct_treatment,
            "tolerance": tolerance
        }
        if is_correct:
            total_score += 1
    else:
        scores["treatment_conversion_rate"] = {
            "correct": False,
            "user": "No answer",
            "correct_answer": correct_answers["treatment_conversion_rate"],
            "tolerance": 0.05
        }
    
    # Question 3: Absolute lift
    user_absolute = user_answers.get("absolute_lift")
    if user_absolute is not None:
        correct_absolute = correct_answers["absolute_lift"]
        tolerance = 0.01
        is_correct = abs(user_absolute - correct_absolute) <= tolerance
        scores["absolute_lift"] = {
            "correct": is_correct,
            "user": user_absolute,
            "correct_answer": correct_absolute,
            "tolerance": tolerance
        }
        if is_correct:
            total_score += 1
    else:
        scores["absolute_lift"] = {
            "correct": False,
            "user": "No answer",
            "correct_answer": correct_answers["absolute_lift"],
            "tolerance": 0.01
        }
    
    # Question 4: Relative lift
    user_relative = user_answers.get("relative_lift")
    if user_relative is not None:
        correct_relative = correct_answers["relative_lift"]
        tolerance = 0.5
        is_correct = abs(user_relative - correct_relative) <= tolerance
        scores["relative_lift"] = {
            "correct": is_correct,
            "user": user_relative,
            "correct_answer": correct_relative,
            "tolerance": tolerance
        }
        if is_correct:
            total_score += 1
    else:
        scores["relative_lift"] = {
            "correct": False,
            "user": "No answer",
            "correct_answer": correct_answers["relative_lift"],
            "tolerance": 0.5
        }
    
    # Question 5: P-value
    user_p_value = user_answers.get("p_value")
    if user_p_value is not None:
        correct_p_value = correct_answers["p_value"]
        tolerance = 0.001
        is_correct = abs(user_p_value - correct_p_value) <= tolerance
        scores["p_value"] = {
            "correct": is_correct,
            "user": user_p_value,
            "correct_answer": correct_p_value,
            "tolerance": tolerance
        }
        if is_correct:
            total_score += 1
    else:
        scores["p_value"] = {
            "correct": False,
            "user": "No answer",
            "correct_answer": correct_answers["p_value"],
            "tolerance": 0.001
        }
    
    # Question 6: Confidence interval
    user_ci = user_answers.get("confidence_interval")
    if user_ci is not None:
        correct_ci = correct_answers["confidence_interval"]
        tolerance = 0.01
        if isinstance(user_ci, tuple) and len(user_ci) == 2:
            user_lower, user_upper = user_ci
            is_correct = (abs(user_lower - correct_ci[0]) <= tolerance and 
                         abs(user_upper - correct_ci[1]) <= tolerance)
        else:
            is_correct = False
        scores["confidence_interval"] = {
            "correct": is_correct,
            "user": f"[{user_ci[0]:.2f}%, {user_ci[1]:.2f}%]" if isinstance(user_ci, tuple) else str(user_ci),
            "correct_answer": f"[{correct_ci[0]:.2f}%, {correct_ci[1]:.2f}%]",
            "tolerance": tolerance
        }
        if is_correct:
            total_score += 1
    else:
        scores["confidence_interval"] = {
            "correct": False,
            "user": "No answer",
            "correct_answer": f"[{correct_answers['confidence_interval'][0]:.2f}%, {correct_answers['confidence_interval'][1]:.2f}%]",
            "tolerance": 0.01
        }
    
    # Question 7: Rollout decision
    user_decision = user_answers.get("rollout_decision")
    if user_decision is not None:
        correct_decision = correct_answers["rollout_decision"]
        is_correct = user_decision.lower() == correct_decision.lower()
        scores["rollout_decision"] = {
            "correct": is_correct,
            "user": user_decision,
            "correct_answer": correct_decision,
            "tolerance": "exact_match"
        }
        if is_correct:
            total_score += 1
    else:
        scores["rollout_decision"] = {
            "correct": False,
            "user": "No answer",
            "correct_answer": correct_answers["rollout_decision"],
            "tolerance": "exact_match"
        }
    
    # Calculate percentage and grade
    max_score = 7  # Updated for 7 questions
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    grade = "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D" if percentage >= 60 else "F"

    return ScoringResult(
        scores=scores,
        total_score=total_score,
        max_score=max_score,
        percentage=percentage,
        grade=grade
    )


# =============================================================================
# NEW: QUESTION ID-BASED VALIDATION SYSTEM
# =============================================================================

def calculate_design_answer_by_id(
    question_id: str,
    design_params: DesignParams,
    sample_size_result: Optional[Any] = None,
    mde_absolute: Optional[float] = None
) -> Tuple[Any, float]:
    """
    Calculate the correct answer for a design question by ID.

    Args:
        question_id: Question identifier from question_bank
        design_params: Design parameters from scenario
        sample_size_result: Sample size calculation result
        mde_absolute: Pre-calculated MDE absolute value

    Returns:
        Tuple of (correct_answer, tolerance)
    """
    question = get_question_by_id(question_id)
    if question is None:
        raise ValueError(f"Unknown question ID: {question_id}")

    baseline = design_params.baseline_conversion_rate
    target_lift = design_params.target_lift_pct

    if mde_absolute is None:
        mde_absolute = baseline * target_lift

    if sample_size_result is None:
        sample_size_result = compute_sample_size(design_params)

    # Calculate answer based on question ID
    if question_id == "mde_absolute":
        correct = mde_absolute * 100  # Convert to percentage points

    elif question_id == "mde_relative":
        correct = (mde_absolute / baseline) * 100  # Relative lift percentage

    elif question_id == "mde_daily_impact":
        correct = round(design_params.expected_daily_traffic * mde_absolute)

    elif question_id == "target_conversion_rate":
        correct = (baseline + mde_absolute) * 100  # Convert to percentage

    elif question_id == "sample_size_per_arm":
        correct = sample_size_result.per_arm

    elif question_id == "sample_size_total":
        correct = sample_size_result.per_arm * 2  # 50/50 allocation

    elif question_id == "sample_size_with_allocation":
        # Calculate control size with given allocation
        allocation = getattr(design_params, 'allocation', {'control': 0.5, 'treatment': 0.5})
        control_alloc = allocation.get('control', 0.5) if isinstance(allocation, dict) else 0.5
        total_sample = sample_size_result.per_arm * 2
        correct = round(total_sample * control_alloc)

    elif question_id == "duration_days":
        total_sample = sample_size_result.per_arm * 2
        correct = max(1, round(total_sample / design_params.expected_daily_traffic))

    elif question_id == "duration_weeks":
        total_sample = sample_size_result.per_arm * 2
        days = max(1, round(total_sample / design_params.expected_daily_traffic))
        correct = round(days / 7, 1)

    elif question_id == "power_tradeoff":
        # What relative lift could you detect with 2 weeks of traffic?
        # This is a reverse calculation - more complex
        two_week_sample = design_params.expected_daily_traffic * 14
        # Approximate: larger sample = smaller detectable effect
        # For simplicity, estimate as: detectable_lift ∝ sqrt(original_sample / available_sample)
        original_sample = sample_size_result.per_arm * 2
        if two_week_sample < original_sample:
            scale_factor = (original_sample / two_week_sample) ** 0.5
            correct = (mde_absolute / baseline) * 100 * scale_factor
        else:
            correct = (mde_absolute / baseline) * 100  # Can detect original MDE

    elif question_id == "sample_for_higher_power":
        # Recalculate sample size with power=0.95
        from .types import Allocation
        high_power_params = DesignParams(
            baseline_conversion_rate=design_params.baseline_conversion_rate,
            target_lift_pct=design_params.target_lift_pct,
            alpha=design_params.alpha,
            power=0.95,
            allocation=design_params.allocation,
            expected_daily_traffic=design_params.expected_daily_traffic
        )
        high_power_result = compute_sample_size(high_power_params)
        correct = high_power_result.per_arm

    else:
        raise ValueError(f"No calculation logic for design question: {question_id}")

    return (correct, question.tolerance)


def calculate_analysis_answer_by_id(
    question_id: str,
    sim_result: SimResult,
    business_target_absolute: Optional[float] = None,
    alpha: float = 0.05
) -> Tuple[Any, float]:
    """
    Calculate the correct answer for an analysis question by ID.

    Args:
        question_id: Question identifier from question_bank
        sim_result: Simulation results
        business_target_absolute: Business target for rollout decision
        alpha: Significance level

    Returns:
        Tuple of (correct_answer, tolerance)
    """
    question = get_question_by_id(question_id)
    if question is None:
        raise ValueError(f"Unknown question ID: {question_id}")

    from .analyze import analyze_results, make_rollout_decision
    analysis = analyze_results(sim_result, alpha=alpha)

    if question_id == "control_rate":
        correct = sim_result.control_rate * 100

    elif question_id == "treatment_rate":
        correct = sim_result.treatment_rate * 100

    elif question_id == "pooled_rate":
        total_conversions = sim_result.control_conversions + sim_result.treatment_conversions
        total_users = sim_result.control_n + sim_result.treatment_n
        correct = (total_conversions / total_users) * 100

    elif question_id == "absolute_lift":
        correct = sim_result.absolute_lift * 100

    elif question_id == "relative_lift":
        correct = sim_result.relative_lift_pct * 100

    elif question_id == "lift_direction":
        correct = "Yes" if sim_result.treatment_rate > sim_result.control_rate else "No"

    elif question_id == "p_value":
        correct = analysis.p_value

    elif question_id == "is_significant":
        correct = "Yes" if analysis.p_value < alpha else "No"

    elif question_id == "confidence_interval":
        ci_lower, ci_upper = analysis.confidence_interval
        correct = (ci_lower * 100, ci_upper * 100)

    elif question_id == "ci_includes_zero":
        ci_lower, ci_upper = analysis.confidence_interval
        correct = "Yes" if ci_lower <= 0 <= ci_upper else "No"

    elif question_id == "rollout_decision":
        if business_target_absolute is None:
            raise ValueError("business_target_absolute required for rollout_decision")
        decision = make_rollout_decision(sim_result, analysis, business_target_absolute)
        correct = "Yes" if decision.lower() == "yes" else "No"

    elif question_id == "practical_significance":
        if business_target_absolute is None:
            raise ValueError("business_target_absolute required for practical_significance")
        correct = "Yes" if sim_result.absolute_lift >= business_target_absolute else "No"

    elif question_id == "annual_impact":
        daily_traffic = getattr(sim_result, 'daily_traffic', 1000)  # Default if not available
        correct = round(daily_traffic * sim_result.absolute_lift * 365)

    else:
        raise ValueError(f"No calculation logic for analysis question: {question_id}")

    return (correct, question.tolerance)


def validate_answer_by_id(
    question_id: str,
    user_answer: Any,
    design_params: Optional[DesignParams] = None,
    sample_size_result: Optional[Any] = None,
    sim_result: Optional[SimResult] = None,
    mde_absolute: Optional[float] = None,
    business_target_absolute: Optional[float] = None,
    alpha: float = 0.05
) -> ValidationResult:
    """
    Validate an answer using question ID from the question bank.

    Args:
        question_id: Question identifier from question_bank
        user_answer: User's answer
        design_params: Design parameters (for design questions)
        sample_size_result: Sample size result (for design questions)
        sim_result: Simulation results (for analysis questions)
        mde_absolute: Pre-calculated MDE absolute value
        business_target_absolute: Business target for decision questions
        alpha: Significance level

    Returns:
        ValidationResult with correctness and feedback
    """
    question = get_question_by_id(question_id)
    if question is None:
        raise ValueError(f"Unknown question ID: {question_id}")

    # Determine if this is a design or analysis question
    if question_id in DESIGN_QUESTIONS:
        if design_params is None:
            raise ValueError("design_params required for design questions")
        correct_answer, tolerance = calculate_design_answer_by_id(
            question_id, design_params, sample_size_result, mde_absolute
        )
    else:
        if sim_result is None:
            raise ValueError("sim_result required for analysis questions")
        correct_answer, tolerance = calculate_analysis_answer_by_id(
            question_id, sim_result, business_target_absolute, alpha
        )

    # Validate based on answer type
    if question.answer_type == AnswerType.BOOLEAN:
        user_normalized = str(user_answer).lower().strip()
        correct_normalized = str(correct_answer).lower().strip()
        is_correct = user_normalized in ['yes', 'true', '1'] and correct_normalized in ['yes', 'true', '1'] or \
                     user_normalized in ['no', 'false', '0'] and correct_normalized in ['no', 'false', '0']
        feedback = f"Correct answer: {correct_answer}"

    elif question.answer_type == AnswerType.RANGE:
        # For confidence intervals (tuples)
        if isinstance(user_answer, (tuple, list)) and len(user_answer) == 2:
            is_correct = (abs(user_answer[0] - correct_answer[0]) <= tolerance and
                         abs(user_answer[1] - correct_answer[1]) <= tolerance)
        else:
            is_correct = False
        feedback = f"Correct answer: [{correct_answer[0]:.2f}, {correct_answer[1]:.2f}]"

    elif question.answer_type in [AnswerType.NUMERIC, AnswerType.PERCENTAGE]:
        try:
            user_value = float(user_answer)
            is_correct = abs(user_value - correct_answer) <= tolerance
        except (ValueError, TypeError):
            is_correct = False

        if question.answer_type == AnswerType.PERCENTAGE:
            feedback = f"Correct answer: {correct_answer:.2f}%"
        else:
            if isinstance(correct_answer, int) or correct_answer == int(correct_answer):
                feedback = f"Correct answer: {int(correct_answer):,}"
            else:
                feedback = f"Correct answer: {correct_answer:.3f}"
    else:
        # Default: string comparison
        is_correct = str(user_answer).lower().strip() == str(correct_answer).lower().strip()
        feedback = f"Correct answer: {correct_answer}"

    return ValidationResult(
        is_correct=is_correct,
        correct_answer=correct_answer,
        feedback=feedback,
        tolerance=tolerance
    )


def score_answers_by_id(
    user_answers: Dict[str, Any],
    question_ids: List[str],
    design_params: Optional[DesignParams] = None,
    sample_size_result: Optional[Any] = None,
    sim_result: Optional[SimResult] = None,
    mde_absolute: Optional[float] = None,
    business_target_absolute: Optional[float] = None,
    alpha: float = 0.05
) -> ScoringResult:
    """
    Score a set of answers using question IDs.

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
        ScoringResult with scores and feedback
    """
    scores = {}
    total_score = 0
    max_score = len(question_ids)

    for question_id in question_ids:
        user_answer = user_answers.get(question_id)

        if user_answer is None:
            question = get_question_by_id(question_id)
            # Calculate correct answer even for unanswered questions
            try:
                if question_id in DESIGN_QUESTIONS:
                    correct, tolerance = calculate_design_answer_by_id(
                        question_id, design_params, sample_size_result, mde_absolute
                    )
                else:
                    correct, tolerance = calculate_analysis_answer_by_id(
                        question_id, sim_result, business_target_absolute, alpha
                    )
            except Exception:
                correct, tolerance = "N/A", 0

            scores[question_id] = {
                "correct": False,
                "user": "No answer",
                "correct_answer": correct,
                "tolerance": tolerance
            }
            continue

        try:
            result = validate_answer_by_id(
                question_id=question_id,
                user_answer=user_answer,
                design_params=design_params,
                sample_size_result=sample_size_result,
                sim_result=sim_result,
                mde_absolute=mde_absolute,
                business_target_absolute=business_target_absolute,
                alpha=alpha
            )

            scores[question_id] = {
                "correct": result.is_correct,
                "user": user_answer,
                "correct_answer": result.correct_answer,
                "tolerance": result.tolerance
            }

            if result.is_correct:
                total_score += 1

        except Exception as e:
            scores[question_id] = {
                "correct": False,
                "user": user_answer,
                "correct_answer": f"Error: {str(e)}",
                "tolerance": 0
            }

    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    grade = "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D" if percentage >= 60 else "F"

    return ScoringResult(
        scores=scores,
        total_score=total_score,
        max_score=max_score,
        percentage=percentage,
        grade=grade
    )


def get_question_text(question_id: str) -> str:
    """Get the question text for a question ID."""
    question = get_question_by_id(question_id)
    if question is None:
        raise ValueError(f"Unknown question ID: {question_id}")
    return question.text


def get_question_hint(question_id: str) -> Optional[str]:
    """Get the hint for a question ID."""
    question = get_question_by_id(question_id)
    if question is None:
        return None
    return question.hint
