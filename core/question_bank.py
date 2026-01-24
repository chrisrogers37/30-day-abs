"""
Question Bank Module - Diverse Question Pools for A/B Testing Quiz

This module provides a pool-based question system that allows for varied quiz
experiences. Instead of a fixed set of 13 questions, users can encounter
different combinations of questions from various categories.

Categories:
- Design Phase: MDE understanding, sample size, duration, power analysis
- Analysis Phase: Rate calculations, lift metrics, statistical testing, decisions
- Planning: Hypothesis formulation, test selection (future)
- Interpretation: Business recommendations, limitations (future)

Each question has:
- id: Unique identifier
- text: The question prompt
- category: Question category for selection
- answer_formula: How to calculate the correct answer
- tolerance: Acceptable margin of error
- difficulty: easy, medium, hard
- skills_tested: What concepts this question evaluates
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Dict, Optional, Callable, Any
import random


class QuestionCategory(str, Enum):
    """Categories of questions for selection."""
    # Design Phase
    MDE_UNDERSTANDING = "mde_understanding"
    SAMPLE_SIZE = "sample_size"
    DURATION = "duration"
    POWER_ANALYSIS = "power_analysis"

    # Analysis Phase
    RATE_CALCULATION = "rate_calculation"
    LIFT_CALCULATION = "lift_calculation"
    STATISTICAL_TESTING = "statistical_testing"
    DECISION_MAKING = "decision_making"

    # Advanced (Future)
    PLANNING = "planning"
    INTERPRETATION = "interpretation"


class QuestionDifficulty(str, Enum):
    """Question difficulty levels."""
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class AnswerType(str, Enum):
    """Types of expected answers."""
    NUMERIC = "numeric"  # Float or int with tolerance
    PERCENTAGE = "percentage"  # Percentage with tolerance
    BOOLEAN = "boolean"  # Yes/No, True/False
    CHOICE = "choice"  # Multiple choice selection
    RANGE = "range"  # Confidence interval (tuple)
    TEXT = "text"  # Free text (for future use)


@dataclass
class Question:
    """Definition of a quiz question."""
    id: str
    text: str
    category: QuestionCategory
    answer_type: AnswerType
    difficulty: QuestionDifficulty
    tolerance: float = 0.0  # For numeric answers
    skills_tested: List[str] = field(default_factory=list)
    hint: Optional[str] = None
    explanation_template: str = ""  # Template for explaining the answer

    # For percentage answers, this indicates if input is expected as
    # percentage (e.g., 5.2) or decimal (e.g., 0.052)
    expects_percentage_input: bool = True


# =============================================================================
# DESIGN PHASE QUESTION POOL
# =============================================================================

DESIGN_QUESTIONS: Dict[str, Question] = {
    # MDE Understanding Questions
    "mde_absolute": Question(
        id="mde_absolute",
        text="Based on the scenario, what is the business's targeted MDE (Minimum Detectable Effect) in percentage points?",
        category=QuestionCategory.MDE_UNDERSTANDING,
        answer_type=AnswerType.PERCENTAGE,
        difficulty=QuestionDifficulty.EASY,
        tolerance=0.5,  # ±0.5 percentage points
        skills_tested=["mde_interpretation", "scenario_comprehension"],
        hint="Look for the business goal in the narrative - it should mention the target improvement.",
        explanation_template="The MDE of {correct:.2f} percentage points comes from the business goal stated in the scenario."
    ),

    "mde_relative": Question(
        id="mde_relative",
        text="What is the MDE expressed as a relative lift percentage (relative to the baseline)?",
        category=QuestionCategory.MDE_UNDERSTANDING,
        answer_type=AnswerType.PERCENTAGE,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=2.0,  # ±2%
        skills_tested=["mde_interpretation", "relative_vs_absolute"],
        hint="Relative lift = (MDE absolute) / (baseline rate) × 100",
        explanation_template="Relative lift = MDE / baseline = {mde:.4f} / {baseline:.4f} = {correct:.1f}%"
    ),

    "mde_daily_impact": Question(
        id="mde_daily_impact",
        text="If the experiment succeeds, how many additional conversions per day would the treatment generate?",
        category=QuestionCategory.MDE_UNDERSTANDING,
        answer_type=AnswerType.NUMERIC,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=5,  # ±5 conversions
        skills_tested=["mde_interpretation", "business_impact"],
        hint="Additional conversions = Daily traffic × MDE (in decimal form)",
        explanation_template="Additional conversions = {traffic} × {mde:.4f} = {correct:.0f} per day"
    ),

    "target_conversion_rate": Question(
        id="target_conversion_rate",
        text="What is the target conversion rate for the treatment group (baseline + MDE)?",
        category=QuestionCategory.MDE_UNDERSTANDING,
        answer_type=AnswerType.PERCENTAGE,
        difficulty=QuestionDifficulty.EASY,
        tolerance=0.5,  # ±0.5%
        skills_tested=["arithmetic", "rate_calculation"],
        hint="Target rate = baseline rate + MDE (both in same units)",
        explanation_template="Target rate = {baseline:.2%} + {mde:.2%} = {correct:.2f}%"
    ),

    # Sample Size Questions
    "sample_size_per_arm": Question(
        id="sample_size_per_arm",
        text="Using the two-proportion z-test formula, what is the required sample size per group?",
        category=QuestionCategory.SAMPLE_SIZE,
        answer_type=AnswerType.NUMERIC,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=50,  # ±50 users
        skills_tested=["sample_size_calculation", "statistical_formulas"],
        hint="Use n = (z_α + z_β)² × [p₁(1-p₁) + p₂(1-p₂)] / (p₂-p₁)²",
        explanation_template="With α={alpha}, power={power}, baseline={baseline:.2%}, target={target:.2%}, n = {correct:,} per arm"
    ),

    "sample_size_total": Question(
        id="sample_size_total",
        text="What is the total sample size needed for both groups combined?",
        category=QuestionCategory.SAMPLE_SIZE,
        answer_type=AnswerType.NUMERIC,
        difficulty=QuestionDifficulty.EASY,
        tolerance=100,  # ±100 users
        skills_tested=["sample_size_calculation", "arithmetic"],
        hint="Total = 2 × sample size per arm (for 50/50 allocation)",
        explanation_template="Total sample = 2 × {per_arm:,} = {correct:,}"
    ),

    "sample_size_with_allocation": Question(
        id="sample_size_with_allocation",
        text="Given the allocation ratio, how many users are needed in the control group?",
        category=QuestionCategory.SAMPLE_SIZE,
        answer_type=AnswerType.NUMERIC,
        difficulty=QuestionDifficulty.HARD,
        tolerance=50,
        skills_tested=["sample_size_calculation", "allocation_understanding"],
        hint="Control size = Total sample × control allocation proportion",
        explanation_template="Control = {total:,} × {control_alloc:.0%} = {correct:,}"
    ),

    # Duration Questions
    "duration_days": Question(
        id="duration_days",
        text="How many days will the experiment need to run to collect sufficient data?",
        category=QuestionCategory.DURATION,
        answer_type=AnswerType.NUMERIC,
        difficulty=QuestionDifficulty.EASY,
        tolerance=1,  # ±1 day
        skills_tested=["duration_calculation", "traffic_understanding"],
        hint="Days = Total sample needed / Daily traffic",
        explanation_template="Duration = {total:,} / {daily:,} = {correct} days"
    ),

    "duration_weeks": Question(
        id="duration_weeks",
        text="Approximately how many weeks will the experiment run?",
        category=QuestionCategory.DURATION,
        answer_type=AnswerType.NUMERIC,
        difficulty=QuestionDifficulty.EASY,
        tolerance=0.5,  # ±0.5 weeks
        skills_tested=["duration_calculation", "unit_conversion"],
        hint="Weeks = Days / 7",
        explanation_template="Duration = {days} days / 7 = {correct:.1f} weeks"
    ),

    # Power Analysis Questions
    "power_tradeoff": Question(
        id="power_tradeoff",
        text="If you only have 2 weeks to run the experiment, what is the minimum relative lift you could reliably detect?",
        category=QuestionCategory.POWER_ANALYSIS,
        answer_type=AnswerType.PERCENTAGE,
        difficulty=QuestionDifficulty.HARD,
        tolerance=3.0,  # ±3%
        skills_tested=["power_analysis", "tradeoff_understanding"],
        hint="Work backwards: with limited sample, you need a larger effect to detect.",
        explanation_template="With {sample:,} users in 2 weeks, minimum detectable lift is {correct:.1f}%"
    ),

    "sample_for_higher_power": Question(
        id="sample_for_higher_power",
        text="What sample size would be needed to achieve 95% power (instead of the current power level)?",
        category=QuestionCategory.POWER_ANALYSIS,
        answer_type=AnswerType.NUMERIC,
        difficulty=QuestionDifficulty.HARD,
        tolerance=100,
        skills_tested=["power_analysis", "sample_size_calculation"],
        hint="Higher power requires larger sample size. Recalculate with power=0.95.",
        explanation_template="At 95% power, n = {correct:,} per arm (vs {original:,} at original power)"
    ),
}


# =============================================================================
# ANALYSIS PHASE QUESTION POOL
# =============================================================================

ANALYSIS_QUESTIONS: Dict[str, Question] = {
    # Rate Calculation Questions
    "control_rate": Question(
        id="control_rate",
        text="What is the observed conversion rate for the control group?",
        category=QuestionCategory.RATE_CALCULATION,
        answer_type=AnswerType.PERCENTAGE,
        difficulty=QuestionDifficulty.EASY,
        tolerance=0.05,  # ±0.05%
        skills_tested=["rate_calculation", "data_analysis"],
        hint="Rate = Conversions / Total users in group",
        explanation_template="Control rate = {conversions:,} / {total:,} = {correct:.2f}%"
    ),

    "treatment_rate": Question(
        id="treatment_rate",
        text="What is the observed conversion rate for the treatment group?",
        category=QuestionCategory.RATE_CALCULATION,
        answer_type=AnswerType.PERCENTAGE,
        difficulty=QuestionDifficulty.EASY,
        tolerance=0.05,  # ±0.05%
        skills_tested=["rate_calculation", "data_analysis"],
        hint="Rate = Conversions / Total users in group",
        explanation_template="Treatment rate = {conversions:,} / {total:,} = {correct:.2f}%"
    ),

    "pooled_rate": Question(
        id="pooled_rate",
        text="What is the pooled conversion rate across both groups?",
        category=QuestionCategory.RATE_CALCULATION,
        answer_type=AnswerType.PERCENTAGE,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0.05,
        skills_tested=["rate_calculation", "pooling_concept"],
        hint="Pooled rate = (Control conversions + Treatment conversions) / (Total users)",
        explanation_template="Pooled = ({c_conv:,} + {t_conv:,}) / ({c_n:,} + {t_n:,}) = {correct:.2f}%"
    ),

    # Lift Calculation Questions
    "absolute_lift": Question(
        id="absolute_lift",
        text="What is the absolute lift (difference) in percentage points?",
        category=QuestionCategory.LIFT_CALCULATION,
        answer_type=AnswerType.PERCENTAGE,
        difficulty=QuestionDifficulty.EASY,
        tolerance=0.05,  # ±0.05 pp
        skills_tested=["lift_calculation", "absolute_vs_relative"],
        hint="Absolute lift = Treatment rate - Control rate",
        explanation_template="Absolute lift = {treatment:.2f}% - {control:.2f}% = {correct:.2f} pp"
    ),

    "relative_lift": Question(
        id="relative_lift",
        text="What is the relative lift percentage?",
        category=QuestionCategory.LIFT_CALCULATION,
        answer_type=AnswerType.PERCENTAGE,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0.5,  # ±0.5%
        skills_tested=["lift_calculation", "relative_change"],
        hint="Relative lift = (Treatment - Control) / Control × 100",
        explanation_template="Relative lift = ({treatment:.2f}% - {control:.2f}%) / {control:.2f}% = {correct:.1f}%"
    ),

    "lift_direction": Question(
        id="lift_direction",
        text="Did the treatment outperform the control? (Yes/No)",
        category=QuestionCategory.LIFT_CALCULATION,
        answer_type=AnswerType.BOOLEAN,
        difficulty=QuestionDifficulty.EASY,
        tolerance=0,
        skills_tested=["lift_interpretation"],
        hint="Compare treatment rate to control rate.",
        explanation_template="Treatment ({treatment:.2f}%) vs Control ({control:.2f}%): {correct}"
    ),

    # Statistical Testing Questions
    "p_value": Question(
        id="p_value",
        text="What is the p-value from the two-proportion z-test?",
        category=QuestionCategory.STATISTICAL_TESTING,
        answer_type=AnswerType.NUMERIC,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0.005,  # ±0.005
        skills_tested=["statistical_testing", "p_value_calculation"],
        hint="Use two-proportion z-test: z = (p1-p2) / sqrt(p*(1-p)*(1/n1+1/n2))",
        explanation_template="z = {z_stat:.3f}, p-value = {correct:.4f}"
    ),

    "is_significant": Question(
        id="is_significant",
        text="Is this result statistically significant at the specified alpha level? (Yes/No)",
        category=QuestionCategory.STATISTICAL_TESTING,
        answer_type=AnswerType.BOOLEAN,
        difficulty=QuestionDifficulty.EASY,
        tolerance=0,
        skills_tested=["significance_interpretation", "hypothesis_testing"],
        hint="Significant if p-value < alpha",
        explanation_template="p-value ({pval:.4f}) {'<' if significant else '>='} α ({alpha}): {correct}"
    ),

    "confidence_interval": Question(
        id="confidence_interval",
        text="What is the 95% confidence interval for the difference in conversion rates (in percentage points)?",
        category=QuestionCategory.STATISTICAL_TESTING,
        answer_type=AnswerType.RANGE,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0.1,  # ±0.1 pp for each bound
        skills_tested=["confidence_interval", "statistical_inference"],
        hint="CI = (p1-p2) ± z × SE, where SE = sqrt(p1(1-p1)/n1 + p2(1-p2)/n2)",
        explanation_template="95% CI: [{lower:.2f}, {upper:.2f}] percentage points"
    ),

    "ci_includes_zero": Question(
        id="ci_includes_zero",
        text="Does the confidence interval include zero? (Yes/No)",
        category=QuestionCategory.STATISTICAL_TESTING,
        answer_type=AnswerType.BOOLEAN,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["confidence_interval_interpretation"],
        hint="If CI includes zero, the effect may not be real.",
        explanation_template="CI [{lower:.2f}, {upper:.2f}]: {'Includes' if includes else 'Does not include'} zero"
    ),

    # Decision Making Questions
    "rollout_decision": Question(
        id="rollout_decision",
        text="Based on the results and business target, should you roll out this treatment? (Yes/No)",
        category=QuestionCategory.DECISION_MAKING,
        answer_type=AnswerType.BOOLEAN,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["decision_making", "business_judgment"],
        hint="Consider: Is it significant? Does it meet the business target (MDE)?",
        explanation_template="Significant: {sig}, Meets target: {meets_target} → {correct}"
    ),

    "practical_significance": Question(
        id="practical_significance",
        text="Is this result practically significant (does the lift meet the business target)? (Yes/No)",
        category=QuestionCategory.DECISION_MAKING,
        answer_type=AnswerType.BOOLEAN,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["practical_vs_statistical", "business_judgment"],
        hint="Practical significance: Is the observed lift >= target MDE?",
        explanation_template="Observed lift ({lift:.2f}pp) {'≥' if practical else '<'} target ({target:.2f}pp)"
    ),

    "annual_impact": Question(
        id="annual_impact",
        text="What is the projected annual impact in additional conversions if rolled out?",
        category=QuestionCategory.DECISION_MAKING,
        answer_type=AnswerType.NUMERIC,
        difficulty=QuestionDifficulty.HARD,
        tolerance=1000,  # ±1000 conversions
        skills_tested=["business_impact", "extrapolation"],
        hint="Annual impact = Daily traffic × Observed lift × 365",
        explanation_template="Annual = {daily:,} × {lift:.4f} × 365 = {correct:,} additional conversions"
    ),
}


# =============================================================================
# QUESTION SELECTION LOGIC
# =============================================================================

def get_default_design_questions() -> List[str]:
    """Return the default set of design question IDs (backward compatible)."""
    return [
        "mde_absolute",
        "target_conversion_rate",
        "mde_relative",
        "sample_size_per_arm",
        "duration_days",
        "mde_daily_impact",
    ]


def get_default_analysis_questions() -> List[str]:
    """Return the default set of analysis question IDs (backward compatible)."""
    return [
        "control_rate",
        "treatment_rate",
        "absolute_lift",
        "relative_lift",
        "p_value",
        "confidence_interval",
        "rollout_decision",
    ]


def select_design_questions(
    count: int = 6,
    categories: Optional[List[QuestionCategory]] = None,
    difficulty: Optional[QuestionDifficulty] = None,
    seed: Optional[int] = None
) -> List[Question]:
    """
    Select a set of design phase questions.

    Args:
        count: Number of questions to select
        categories: Optional filter by categories
        difficulty: Optional filter by difficulty
        seed: Random seed for reproducibility

    Returns:
        List of selected Question objects
    """
    if seed is not None:
        random.seed(seed)

    pool = list(DESIGN_QUESTIONS.values())

    # Apply filters
    if categories:
        pool = [q for q in pool if q.category in categories]
    if difficulty:
        pool = [q for q in pool if q.difficulty == difficulty]

    # Ensure we have enough questions
    count = min(count, len(pool))

    return random.sample(pool, count)


def select_analysis_questions(
    count: int = 7,
    categories: Optional[List[QuestionCategory]] = None,
    difficulty: Optional[QuestionDifficulty] = None,
    seed: Optional[int] = None
) -> List[Question]:
    """
    Select a set of analysis phase questions.

    Args:
        count: Number of questions to select
        categories: Optional filter by categories
        difficulty: Optional filter by difficulty
        seed: Random seed for reproducibility

    Returns:
        List of selected Question objects
    """
    if seed is not None:
        random.seed(seed)

    pool = list(ANALYSIS_QUESTIONS.values())

    # Apply filters
    if categories:
        pool = [q for q in pool if q.category in categories]
    if difficulty:
        pool = [q for q in pool if q.difficulty == difficulty]

    # Ensure we have enough questions
    count = min(count, len(pool))

    return random.sample(pool, count)


def get_question_by_id(question_id: str) -> Optional[Question]:
    """Get a question by its ID from either pool."""
    if question_id in DESIGN_QUESTIONS:
        return DESIGN_QUESTIONS[question_id]
    if question_id in ANALYSIS_QUESTIONS:
        return ANALYSIS_QUESTIONS[question_id]
    return None


def get_all_questions() -> Dict[str, Question]:
    """Get all questions from both pools."""
    return {**DESIGN_QUESTIONS, **ANALYSIS_QUESTIONS}
