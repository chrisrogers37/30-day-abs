"""
Validation and scoring logic for AB test simulator.

This module provides validation and scoring functions for quiz answers,
ensuring consistent logic across all UI components.
"""

from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass

from .types import SimResult, DesignParams
from .design import compute_sample_size


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
