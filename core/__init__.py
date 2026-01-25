"""
Core domain logic for AB Test Simulator.

This module contains pure, deterministic domain logic with no HTTP, no LLM calls,
and no global state. All mathematical calculations are performed here.
"""

from .types import (
    Allocation,
    DesignParams,
    SampleSize,
    SimResult,
    AnalysisResult,
    BusinessImpact,
    TestQuality,
    StatisticalTestSelection,
)

from .validation import (
    ValidationResult,
    ScoringResult,
    validate_design_answer,
    validate_analysis_answer,
    score_design_answers,
    score_analysis_answers,
)

from .analyze import (
    make_rollout_decision,
    select_statistical_test,
    analyze_results,
)

from .scoring import (
    AnswerKey,
    QuizResult,
    generate_design_answer_key,
    generate_analysis_answer_key,
    create_complete_quiz_result,
)

__all__ = [
    "Allocation",
    "DesignParams",
    "SampleSize",
    "SimResult",
    "AnalysisResult",
    "BusinessImpact",
    "TestQuality",
    "StatisticalTestSelection",
    "ValidationResult",
    "ScoringResult",
    "validate_design_answer",
    "validate_analysis_answer",
    "score_design_answers",
    "score_analysis_answers",
    "make_rollout_decision",
    "select_statistical_test",
    "analyze_results",
    "AnswerKey",
    "QuizResult",
    "generate_design_answer_key",
    "generate_analysis_answer_key",
    "create_complete_quiz_result",
]
