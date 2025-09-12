"""
Evaluation-related DTOs for user response scoring and feedback.

This module contains schemas for evaluating user responses, scoring criteria,
and generating interview-style feedback.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator


class EvaluationCriteriaDTO(BaseModel):
    """Evaluation criteria for user responses."""
    statistical_significance: str = Field(
        default="correct", 
        pattern="^(correct|incorrect|partially_correct)$",
        description="Evaluation of statistical significance interpretation"
    )
    business_interpretation: str = Field(
        default="correct",
        pattern="^(correct|incorrect|partially_correct)$",
        description="Evaluation of business interpretation"
    )
    risk_assessment: str = Field(
        default="correct",
        pattern="^(correct|incorrect|partially_correct)$",
        description="Evaluation of risk assessment"
    )
    next_steps: str = Field(
        default="correct",
        pattern="^(correct|incorrect|partially_correct)$",
        description="Evaluation of recommended next steps"
    )
    overall_score: float = Field(
        default=8.5, ge=0.0, le=10.0,
        description="Overall score (0-10)"
    )
    feedback: str = Field(
        default="Good analysis with minor areas for improvement",
        description="Detailed feedback for the user"
    )


class UserResponseDTO(BaseModel):
    """User's response to be evaluated."""
    p_value_interpretation: str = Field(description="User's interpretation of p-value")
    statistical_significance: bool = Field(description="User's conclusion about significance")
    effect_size_interpretation: str = Field(description="User's interpretation of effect size")
    business_impact: str = Field(description="User's assessment of business impact")
    risk_assessment: str = Field(description="User's risk assessment")
    recommendation: str = Field(description="User's recommendation")
    confidence_level: float = Field(ge=0.0, le=1.0, description="User's confidence in their analysis")
    additional_notes: Optional[str] = Field(None, description="Additional user notes")


class EvaluationRequestDTO(BaseModel):
    """Request to evaluate a user's response."""
    user_response: UserResponseDTO = Field(description="User's response to evaluate")
    answer_key: Dict[str, str] = Field(description="Correct answers and expected responses")
    scenario_context: str = Field(description="Context about the test scenario")
    evaluation_weights: Optional[Dict[str, float]] = Field(None, description="Weights for different criteria")
    include_detailed_feedback: bool = Field(default=True, description="Include detailed feedback")
    include_improvement_suggestions: bool = Field(default=True, description="Include improvement suggestions")


class EvaluationResponseDTO(BaseModel):
    """Response containing evaluation results and feedback."""
    evaluation_criteria: EvaluationCriteriaDTO = Field(description="Detailed evaluation criteria")
    overall_score: float = Field(ge=0.0, le=10.0, description="Overall score (0-10)")
    grade: str = Field(description="Letter grade (A, B, C, D, F)")
    strengths: List[str] = Field(description="Identified strengths")
    weaknesses: List[str] = Field(description="Identified weaknesses")
    improvement_suggestions: List[str] = Field(description="Specific improvement suggestions")
    interview_feedback: str = Field(description="Interview-style feedback")
    follow_up_questions: List[str] = Field(description="Suggested follow-up questions")
    evaluation_metadata: Dict[str, str] = Field(default_factory=dict, description="Evaluation metadata")


class ScoringRubricDTO(BaseModel):
    """Scoring rubric for different response types."""
    criteria: Dict[str, Dict[str, float]] = Field(description="Scoring criteria and weights")
    grade_thresholds: Dict[str, float] = Field(description="Grade thresholds")
    bonus_points: Dict[str, float] = Field(default_factory=dict, description="Bonus point opportunities")
    penalty_points: Dict[str, float] = Field(default_factory=dict, description="Penalty point categories")
    
    @field_validator('grade_thresholds')
    @classmethod
    def validate_grade_thresholds(cls, v):
        """Ensure grade thresholds are valid."""
        required_grades = ['A', 'B', 'C', 'D', 'F']
        for grade in required_grades:
            if grade not in v:
                raise ValueError(f"Missing grade threshold for {grade}")
            if not (0.0 <= v[grade] <= 10.0):
                raise ValueError(f"Grade threshold for {grade} must be between 0 and 10")
        return v


class FeedbackTemplateDTO(BaseModel):
    """Template for generating feedback."""
    positive_feedback: List[str] = Field(description="Positive feedback templates")
    constructive_feedback: List[str] = Field(description="Constructive feedback templates")
    improvement_suggestions: List[str] = Field(description="Improvement suggestion templates")
    follow_up_questions: List[str] = Field(description="Follow-up question templates")
    encouragement_messages: List[str] = Field(description="Encouragement message templates")


class EvaluationMetricsDTO(BaseModel):
    """Metrics for evaluation system performance."""
    total_evaluations: int = Field(ge=0, description="Total number of evaluations performed")
    average_score: float = Field(ge=0.0, le=10.0, description="Average score across all evaluations")
    score_distribution: Dict[str, int] = Field(description="Distribution of scores by grade")
    common_mistakes: Dict[str, int] = Field(description="Frequency of common mistakes")
    improvement_areas: Dict[str, int] = Field(description="Most common improvement areas")
    user_satisfaction: float = Field(ge=0.0, le=1.0, description="User satisfaction with feedback")


class ComparativeEvaluationDTO(BaseModel):
    """Comparative evaluation between multiple user responses."""
    user_responses: List[UserResponseDTO] = Field(description="Multiple user responses to compare")
    comparative_scores: List[float] = Field(description="Scores for each response")
    ranking: List[int] = Field(description="Ranking of responses (1-based)")
    strengths_comparison: Dict[str, List[str]] = Field(description="Strengths comparison across responses")
    weaknesses_comparison: Dict[str, List[str]] = Field(description="Weaknesses comparison across responses")
    best_practices: List[str] = Field(description="Best practices identified from top responses")
