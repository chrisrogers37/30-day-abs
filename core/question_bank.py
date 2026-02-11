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
from typing import List, Dict, Optional
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

# =============================================================================
# PLANNING PHASE QUESTION POOL
# =============================================================================

PLANNING_QUESTIONS: Dict[str, Question] = {
    # Hypothesis Formulation Questions
    "hypothesis_null": Question(
        id="hypothesis_null",
        text="What is the null hypothesis for this experiment?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.EASY,
        tolerance=0,
        skills_tested=["hypothesis_formulation", "experimental_design"],
        hint="The null hypothesis typically states there is no effect or difference.",
        explanation_template="H0: The treatment has no effect on {metric} (p_treatment = p_control)"
    ),

    "hypothesis_alternative": Question(
        id="hypothesis_alternative",
        text="What is the alternative hypothesis for this experiment?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.EASY,
        tolerance=0,
        skills_tested=["hypothesis_formulation", "experimental_design"],
        hint="The alternative hypothesis states the expected effect exists.",
        explanation_template="H1: The treatment improves {metric} (p_treatment > p_control)"
    ),

    "one_vs_two_tailed": Question(
        id="one_vs_two_tailed",
        text="Should this experiment use a one-tailed or two-tailed test? Why?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["test_selection", "hypothesis_testing"],
        hint="One-tailed: directional hypothesis. Two-tailed: non-directional.",
        explanation_template="Use {correct} test because {reason}"
    ),

    "test_type_selection": Question(
        id="test_type_selection",
        text="Which statistical test is most appropriate for this scenario?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["test_selection", "statistical_knowledge"],
        hint="Consider the type of metric (proportion vs. continuous) and sample size.",
        explanation_template="Use {correct} because {reason}"
    ),

    "fisher_vs_chi_square": Question(
        id="fisher_vs_chi_square",
        text="When should you use Fisher's exact test instead of chi-square?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["test_selection", "sample_size_considerations"],
        hint="Consider the expected cell counts in the contingency table.",
        explanation_template="Use Fisher's exact test when any expected cell count is below 5, as chi-square assumptions are violated."
    ),

    "expected_cell_count": Question(
        id="expected_cell_count",
        text="What is the minimum expected cell count rule for chi-square test validity?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.NUMERIC,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["test_assumptions", "statistical_validity"],
        hint="This is a standard rule of thumb for contingency tables.",
        explanation_template="All expected cell counts should be at least 5 for chi-square test to be valid."
    ),

    "z_test_assumptions": Question(
        id="z_test_assumptions",
        text="What sample size condition must be met for the two-proportion z-test normal approximation to be valid?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["test_assumptions", "normal_approximation"],
        hint="Consider the np and n(1-p) rule.",
        explanation_template="Both np ≥ 5 and n(1-p) ≥ 5 for each group, or approximately n ≥ 30 per group."
    ),

    "small_sample_test": Question(
        id="small_sample_test",
        text="You have 50 users per group with 2 conversions in control and 5 in treatment. Which test should you use?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["test_selection", "practical_application"],
        hint="Calculate the expected cell counts first.",
        explanation_template="Fisher's exact test: with only 7 total conversions across 100 users, expected cell counts are too small for chi-square."
    ),

    # Experimental Design Questions
    "allocation_justification": Question(
        id="allocation_justification",
        text="Why might you choose a 50/50 allocation split for this experiment?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["experimental_design", "power_efficiency"],
        hint="Consider statistical power and sample size efficiency.",
        explanation_template="50/50 allocation maximizes power for a given total sample size."
    ),

    "unequal_allocation_reason": Question(
        id="unequal_allocation_reason",
        text="In what situation would an unequal allocation (e.g., 80/20) be appropriate?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["experimental_design", "risk_assessment"],
        hint="Consider risk mitigation and business constraints.",
        explanation_template="Unequal allocation when: {reason}"
    ),

    "primary_metric_selection": Question(
        id="primary_metric_selection",
        text="Why is it important to define a single primary metric before the experiment?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["experimental_design", "statistical_validity"],
        hint="Consider the risks of multiple testing and p-hacking.",
        explanation_template="Single primary metric prevents multiple testing inflation and p-hacking."
    ),

    "guardrail_metrics": Question(
        id="guardrail_metrics",
        text="What guardrail metrics should be monitored alongside the primary metric?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.TEXT,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["experimental_design", "business_acumen"],
        hint="Think about what could go wrong if we only optimize for the primary metric.",
        explanation_template="Guardrail metrics protect against unintended consequences."
    ),

    # Risk Assessment Questions
    "alpha_justification": Question(
        id="alpha_justification",
        text="When might you use a stricter alpha (e.g., 0.01 instead of 0.05)?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["statistical_thresholds", "risk_assessment"],
        hint="Consider the cost of false positives in this context.",
        explanation_template="Stricter alpha when: {reason}"
    ),

    "power_justification": Question(
        id="power_justification",
        text="Why might you want 90% power instead of the standard 80%?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["power_analysis", "risk_assessment"],
        hint="Consider the cost of missing a real effect.",
        explanation_template="Higher power when: {reason}"
    ),

    "minimum_runtime": Question(
        id="minimum_runtime",
        text="Why is it important to run the experiment for at least one full week?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.EASY,
        tolerance=0,
        skills_tested=["experimental_design", "seasonality_awareness"],
        hint="Think about how user behavior might vary during the week.",
        explanation_template="Full week captures day-of-week effects and natural variance cycles."
    ),

    "pre_registration": Question(
        id="pre_registration",
        text="What are the benefits of pre-registering your analysis plan?",
        category=QuestionCategory.PLANNING,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["experimental_rigor", "statistical_validity"],
        hint="Consider how decisions made after seeing data can bias results.",
        explanation_template="Pre-registration prevents HARKing and p-hacking."
    ),
}


# =============================================================================
# INTERPRETATION PHASE QUESTION POOL
# =============================================================================

INTERPRETATION_QUESTIONS: Dict[str, Question] = {
    # Result Interpretation Questions
    "statistical_vs_practical": Question(
        id="statistical_vs_practical",
        text="A result is statistically significant but the lift is only 2% of the target MDE. What do you recommend?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["decision_making", "business_judgment"],
        hint="Statistical significance doesn't always mean business value.",
        explanation_template="Consider practical significance: observed effect vs. business needs."
    ),

    "inconclusive_results": Question(
        id="inconclusive_results",
        text="The experiment ended with p=0.08. What are the appropriate next steps?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["decision_making", "uncertainty_handling"],
        hint="Consider options beyond simple accept/reject.",
        explanation_template="Options include: extend experiment, larger MDE, iterate on treatment."
    ),

    "negative_result_value": Question(
        id="negative_result_value",
        text="The experiment shows a significant negative effect. Is this a failed experiment?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.BOOLEAN,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["learning_mindset", "experimental_value"],
        hint="Consider what learning value a negative result provides.",
        explanation_template="Negative results prevent bad rollouts and inform future experiments."
    ),

    # Business Communication Questions
    "stakeholder_summary": Question(
        id="stakeholder_summary",
        text="How would you summarize this experiment result for non-technical stakeholders?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.TEXT,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["communication", "business_translation"],
        hint="Focus on business impact, not statistical details.",
        explanation_template="Lead with impact and recommendation, simplify statistics."
    ),

    "confidence_communication": Question(
        id="confidence_communication",
        text="How would you communicate the uncertainty in this result to leadership?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.TEXT,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["communication", "uncertainty_quantification"],
        hint="Use confidence intervals and probabilistic language.",
        explanation_template="Use ranges and likelihood language: 'We're 95% confident the true effect is...'"
    ),

    "revenue_projection": Question(
        id="revenue_projection",
        text="Based on the observed lift, what is the estimated annual revenue impact?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.NUMERIC,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0.10,  # 10% tolerance for estimation
        skills_tested=["business_impact", "financial_translation"],
        hint="Multiply daily impact by 365, then by average conversion value.",
        explanation_template="Annual impact = Daily traffic × Lift × 365 × Average value per conversion"
    ),

    # Limitations and Caveats
    "external_validity": Question(
        id="external_validity",
        text="What factors might limit the generalizability of these results?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.TEXT,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["critical_thinking", "experimental_limitations"],
        hint="Consider timing, segment, and context factors.",
        explanation_template="Factors: seasonality, user segment, geography, competitive landscape"
    ),

    "novelty_effect_risk": Question(
        id="novelty_effect_risk",
        text="How would you determine if the observed lift is due to novelty effects?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["effect_persistence", "analytical_rigor"],
        hint="Consider how to track effect over time.",
        explanation_template="Monitor lift decay over time; compare early vs. late cohorts."
    ),

    "survivorship_bias": Question(
        id="survivorship_bias",
        text="Could survivorship bias affect the interpretation of these results?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.BOOLEAN,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["bias_awareness", "experimental_validity"],
        hint="Consider if you're only measuring users who stayed.",
        explanation_template="Risk if analysis excludes users who churned during experiment."
    ),

    # Follow-up Planning
    "follow_up_experiment": Question(
        id="follow_up_experiment",
        text="What follow-up experiment would you recommend based on these results?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.TEXT,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["experimental_iteration", "strategic_thinking"],
        hint="Consider optimizing the winner or exploring variants.",
        explanation_template="Options: optimize winner, test on new segments, refine treatment."
    ),

    "holdout_recommendation": Question(
        id="holdout_recommendation",
        text="Should you maintain a holdout group after rolling out the winner? Why?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["long_term_validation", "experimental_rigor"],
        hint="Consider long-term effect monitoring.",
        explanation_template="Holdouts help detect effect decay and enable long-term impact measurement."
    ),

    "segment_analysis": Question(
        id="segment_analysis",
        text="What segments would you analyze to understand heterogeneous treatment effects?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.TEXT,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["segmentation", "analytical_depth"],
        hint="Think about user attributes that might moderate the effect.",
        explanation_template="Common segments: device type, tenure, usage frequency, geography."
    ),

    "ci_interpretation": Question(
        id="ci_interpretation",
        text="The 95% CI for the lift is [-0.2%, +1.8%]. What does this tell you about the true effect?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["confidence_interval_interpretation", "uncertainty_quantification"],
        hint="Consider what values are plausible given this interval.",
        explanation_template="CI including zero means we cannot rule out no effect with 95% confidence."
    ),

    # Test Selection Understanding
    "test_selection_impact": Question(
        id="test_selection_impact",
        text="If you ran chi-square instead of Fisher's exact on a small sample, what could happen?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["test_selection_consequences", "statistical_validity"],
        hint="Consider what happens when test assumptions are violated.",
        explanation_template="Chi-square with small expected counts can give inaccurate p-values (usually too small)."
    ),

    "effect_size_interpretation": Question(
        id="effect_size_interpretation",
        text="What does Cohen's h of 0.15 indicate about the effect size?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.MEDIUM,
        tolerance=0,
        skills_tested=["effect_size_understanding", "result_interpretation"],
        hint="Cohen's h: 0.2 = small, 0.5 = medium, 0.8 = large.",
        explanation_template="Cohen's h of 0.15 is below small (0.2), indicating a very small effect."
    ),

    "power_post_hoc": Question(
        id="power_post_hoc",
        text="The experiment showed achieved power of 0.45. What does this mean for the interpretation?",
        category=QuestionCategory.INTERPRETATION,
        answer_type=AnswerType.CHOICE,
        difficulty=QuestionDifficulty.HARD,
        tolerance=0,
        skills_tested=["power_interpretation", "experimental_validity"],
        hint="Consider what low power means for detecting true effects.",
        explanation_template="45% power means 55% chance of missing a true effect. Non-significant results are inconclusive."
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


def get_default_planning_questions() -> List[str]:
    """Return the default set of planning question IDs."""
    return [
        "hypothesis_null",
        "hypothesis_alternative",
        "one_vs_two_tailed",
        "primary_metric_selection",
        "minimum_runtime",
    ]


def get_default_interpretation_questions() -> List[str]:
    """Return the default set of interpretation question IDs."""
    return [
        "statistical_vs_practical",
        "inconclusive_results",
        "ci_interpretation",
        "holdout_recommendation",
        "follow_up_experiment",
    ]


def select_planning_questions(
    count: int = 5,
    difficulty: Optional[QuestionDifficulty] = None,
    seed: Optional[int] = None
) -> List[Question]:
    """
    Select a set of planning phase questions.

    Args:
        count: Number of questions to select
        difficulty: Optional filter by difficulty
        seed: Random seed for reproducibility

    Returns:
        List of selected Question objects
    """
    if seed is not None:
        random.seed(seed)

    pool = list(PLANNING_QUESTIONS.values())

    if difficulty:
        pool = [q for q in pool if q.difficulty == difficulty]

    count = min(count, len(pool))
    return random.sample(pool, count)


def select_interpretation_questions(
    count: int = 5,
    difficulty: Optional[QuestionDifficulty] = None,
    seed: Optional[int] = None
) -> List[Question]:
    """
    Select a set of interpretation phase questions.

    Args:
        count: Number of questions to select
        difficulty: Optional filter by difficulty
        seed: Random seed for reproducibility

    Returns:
        List of selected Question objects
    """
    if seed is not None:
        random.seed(seed)

    pool = list(INTERPRETATION_QUESTIONS.values())

    if difficulty:
        pool = [q for q in pool if q.difficulty == difficulty]

    count = min(count, len(pool))
    return random.sample(pool, count)


def select_advanced_questions(
    planning_count: int = 3,
    interpretation_count: int = 3,
    difficulty: Optional[QuestionDifficulty] = None,
    seed: Optional[int] = None
) -> List[Question]:
    """
    Select a mixed set of advanced (planning + interpretation) questions.

    Args:
        planning_count: Number of planning questions
        interpretation_count: Number of interpretation questions
        difficulty: Optional filter by difficulty
        seed: Random seed for reproducibility

    Returns:
        List of selected Question objects
    """
    planning = select_planning_questions(planning_count, difficulty, seed)
    interpretation = select_interpretation_questions(interpretation_count, difficulty, seed)
    return planning + interpretation


def get_question_by_id(question_id: str) -> Optional[Question]:
    """Get a question by its ID from any pool."""
    if question_id in DESIGN_QUESTIONS:
        return DESIGN_QUESTIONS[question_id]
    if question_id in ANALYSIS_QUESTIONS:
        return ANALYSIS_QUESTIONS[question_id]
    if question_id in PLANNING_QUESTIONS:
        return PLANNING_QUESTIONS[question_id]
    if question_id in INTERPRETATION_QUESTIONS:
        return INTERPRETATION_QUESTIONS[question_id]
    return None


def get_all_questions() -> Dict[str, Question]:
    """Get all questions from all pools."""
    return {
        **DESIGN_QUESTIONS,
        **ANALYSIS_QUESTIONS,
        **PLANNING_QUESTIONS,
        **INTERPRETATION_QUESTIONS
    }


def get_questions_by_category(category: QuestionCategory) -> Dict[str, Question]:
    """Get all questions from a specific category."""
    all_questions = get_all_questions()
    return {
        qid: q for qid, q in all_questions.items()
        if q.category == category
    }


def get_question_pool_summary() -> Dict[str, int]:
    """Get a summary of question counts by pool."""
    return {
        "design": len(DESIGN_QUESTIONS),
        "analysis": len(ANALYSIS_QUESTIONS),
        "planning": len(PLANNING_QUESTIONS),
        "interpretation": len(INTERPRETATION_QUESTIONS),
        "total": len(get_all_questions())
    }
