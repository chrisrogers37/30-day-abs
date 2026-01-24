"""
Scenario Complications Schema

This module defines the complications that can be added to A/B testing scenarios
to make them more realistic and educational. Complications introduce real-world
challenges that practitioners face when running experiments.

Future Enhancement: These complications can be used by the LLM to generate
more complex scenarios and by the quiz to ask additional contextual questions.
"""

from enum import Enum
from typing import List, Optional
from pydantic import BaseModel, Field


class ComplicationType(str, Enum):
    """Types of complications that can affect an A/B test scenario."""

    # Timing Complications
    SEASONALITY = "seasonality"
    """The metric is affected by seasonal patterns (holidays, weekends, etc.)"""

    TIME_PRESSURE = "time_pressure"
    """Stakeholders need a decision within a constrained timeframe"""

    DAY_OF_WEEK_EFFECT = "day_of_week_effect"
    """Behavior varies significantly by day of week"""

    # Business Complications
    OPPORTUNITY_COST = "opportunity_cost"
    """Running the experiment has significant costs (engineering time, revenue delay)"""

    CANNIBALIZATION = "cannibalization"
    """The treatment may improve one metric but hurt another"""

    SEGMENT_HETEROGENEITY = "segment_heterogeneity"
    """Treatment effect varies significantly across user segments"""

    NETWORK_EFFECTS = "network_effects"
    """Users interact, potentially contaminating control/treatment groups"""

    # Statistical Complications
    NOVELTY_EFFECT = "novelty_effect"
    """Early results may not persist as users adapt to the change"""

    MULTIPLE_TESTING = "multiple_testing"
    """Multiple experiments or metrics being tested simultaneously"""

    EARLY_STOPPING_PRESSURE = "early_stopping_pressure"
    """Stakeholders want to peek at results and make early decisions"""

    LOW_TRAFFIC = "low_traffic"
    """Limited traffic makes reaching statistical significance challenging"""

    HIGH_VARIANCE = "high_variance"
    """The metric has high natural variance, requiring larger samples"""

    # Ethical/Risk Complications
    USER_HARM_RISK = "user_harm_risk"
    """Treatment may negatively impact some users"""

    FAIRNESS_CONCERN = "fairness_concern"
    """Potential for disparate impact across demographic groups"""

    REGULATORY_REQUIREMENT = "regulatory_requirement"
    """Specific statistical thresholds required by regulation"""

    # Technical Complications
    IMPLEMENTATION_RISK = "implementation_risk"
    """Technical complexity in implementing the treatment correctly"""

    MEASUREMENT_CHALLENGE = "measurement_challenge"
    """Difficulty in accurately measuring the primary metric"""

    DELAYED_OUTCOME = "delayed_outcome"
    """The true effect takes time to manifest (e.g., retention metrics)"""


class Complication(BaseModel):
    """A specific complication affecting a scenario."""

    type: ComplicationType = Field(description="The type of complication")

    description: str = Field(
        description="Specific description of how this complication manifests in the scenario"
    )

    severity: str = Field(
        default="medium",
        pattern="^(low|medium|high)$",
        description="How significantly this complication affects the experiment"
    )

    mitigation_hint: Optional[str] = Field(
        default=None,
        description="Optional hint about how to address this complication"
    )

    affects_analysis: bool = Field(
        default=False,
        description="Whether this complication should affect how the user analyzes results"
    )

    additional_questions: List[str] = Field(
        default_factory=list,
        description="Additional questions this complication introduces"
    )


class ScenarioComplications(BaseModel):
    """Collection of complications for a scenario."""

    complications: List[Complication] = Field(
        default_factory=list,
        max_length=3,  # Limit to avoid overwhelming complexity
        description="List of complications affecting this scenario"
    )

    overall_complexity: str = Field(
        default="standard",
        pattern="^(simple|standard|complex|advanced)$",
        description="Overall complexity level based on complications"
    )

    @property
    def has_timing_complications(self) -> bool:
        """Check if scenario has timing-related complications."""
        timing_types = {
            ComplicationType.SEASONALITY,
            ComplicationType.TIME_PRESSURE,
            ComplicationType.DAY_OF_WEEK_EFFECT
        }
        return any(c.type in timing_types for c in self.complications)

    @property
    def has_statistical_complications(self) -> bool:
        """Check if scenario has statistical complications."""
        stat_types = {
            ComplicationType.NOVELTY_EFFECT,
            ComplicationType.MULTIPLE_TESTING,
            ComplicationType.EARLY_STOPPING_PRESSURE,
            ComplicationType.LOW_TRAFFIC,
            ComplicationType.HIGH_VARIANCE
        }
        return any(c.type in stat_types for c in self.complications)

    @property
    def has_ethical_complications(self) -> bool:
        """Check if scenario has ethical/risk complications."""
        ethical_types = {
            ComplicationType.USER_HARM_RISK,
            ComplicationType.FAIRNESS_CONCERN,
            ComplicationType.REGULATORY_REQUIREMENT
        }
        return any(c.type in ethical_types for c in self.complications)


# Predefined complication templates for common scenarios
COMPLICATION_TEMPLATES = {
    ComplicationType.SEASONALITY: Complication(
        type=ComplicationType.SEASONALITY,
        description="This experiment will run through a major holiday season, which historically shows 40% higher conversion rates.",
        severity="high",
        mitigation_hint="Consider extending the experiment to capture both holiday and non-holiday periods, or analyze cohorts separately.",
        affects_analysis=True,
        additional_questions=[
            "How would you account for seasonality in your analysis?",
            "Should you wait until after the holiday season to make a decision?"
        ]
    ),

    ComplicationType.TIME_PRESSURE: Complication(
        type=ComplicationType.TIME_PRESSURE,
        description="Leadership needs a decision within 2 weeks, regardless of statistical significance.",
        severity="high",
        mitigation_hint="Consider what decision you would make with directional evidence, and communicate confidence levels clearly.",
        affects_analysis=True,
        additional_questions=[
            "What is the minimum detectable effect given the time constraint?",
            "How would you communicate results if you haven't reached significance?"
        ]
    ),

    ComplicationType.NOVELTY_EFFECT: Complication(
        type=ComplicationType.NOVELTY_EFFECT,
        description="Users may initially engage more with the new feature simply because it's new.",
        severity="medium",
        mitigation_hint="Plan for a longer experiment or analyze engagement over time to see if effect persists.",
        affects_analysis=True,
        additional_questions=[
            "How would you detect if the effect is driven by novelty?",
            "What follow-up analysis would you recommend?"
        ]
    ),

    ComplicationType.MULTIPLE_TESTING: Complication(
        type=ComplicationType.MULTIPLE_TESTING,
        description="Two other experiments are running simultaneously on overlapping user populations.",
        severity="medium",
        mitigation_hint="Consider interaction effects and potentially adjust significance thresholds.",
        affects_analysis=True,
        additional_questions=[
            "How does running multiple tests affect your interpretation?",
            "Should you apply a correction for multiple comparisons?"
        ]
    ),

    ComplicationType.CANNIBALIZATION: Complication(
        type=ComplicationType.CANNIBALIZATION,
        description="Improving this metric may reduce another important business metric.",
        severity="medium",
        mitigation_hint="Monitor guardrail metrics closely and consider the net business impact.",
        affects_analysis=True,
        additional_questions=[
            "What guardrail metrics should you monitor?",
            "How would you weigh tradeoffs between metrics?"
        ]
    ),

    ComplicationType.SEGMENT_HETEROGENEITY: Complication(
        type=ComplicationType.SEGMENT_HETEROGENEITY,
        description="Initial analysis suggests the treatment effect varies significantly between mobile and desktop users.",
        severity="medium",
        mitigation_hint="Conduct segmented analysis and consider whether to roll out only to specific segments.",
        affects_analysis=True,
        additional_questions=[
            "Should you analyze segments separately?",
            "What would you recommend if the effect is positive for one segment but negative for another?"
        ]
    ),
}


def get_random_complications(
    count: int = 1,
    exclude_types: Optional[List[ComplicationType]] = None,
    severity_filter: Optional[str] = None
) -> List[Complication]:
    """
    Get random complications from the templates.

    Args:
        count: Number of complications to return
        exclude_types: Types to exclude from selection
        severity_filter: Only include complications of this severity

    Returns:
        List of Complication objects
    """
    import random

    available = list(COMPLICATION_TEMPLATES.values())

    if exclude_types:
        available = [c for c in available if c.type not in exclude_types]

    if severity_filter:
        available = [c for c in available if c.severity == severity_filter]

    count = min(count, len(available))
    return random.sample(available, count)
