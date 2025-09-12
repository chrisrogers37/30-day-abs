"""
Shared types, enums, and common validation helpers for API schemas.

This module contains common enums and types used across multiple schema modules.
"""

from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class TestType(str, Enum):
    """Statistical test types supported by the simulator."""
    TWO_PROPORTION_Z = "two_proportion_z"
    CHI_SQUARE = "chi_square"
    FISHER_EXACT = "fisher_exact"


class TestDirection(str, Enum):
    """Test direction for one-tailed vs two-tailed tests."""
    ONE_TAILED = "one_tailed"
    TWO_TAILED = "two_tailed"


class CompanyType(str, Enum):
    """Company types for realistic business context."""
    SAAS = "SaaS"
    ECOMMERCE = "E-commerce"
    MEDIA = "Media"
    MEDIA_CONTENT = "Media/Content"
    FINTECH = "Fintech"
    MARKETPLACE = "Marketplace"
    GAMING = "Gaming"


class UserSegment(str, Enum):
    """User segments for targeted testing."""
    NEW_USERS = "new_users"
    NEW_SIGNUPS = "new_sign-ups"
    RETURNING_USERS = "returning_users"
    PREMIUM_USERS = "premium_users"
    TRIAL_USERS = "trial_users"
    ALL_USERS = "all_users"


class RiskTolerance(str, Enum):
    """Risk tolerance levels for test design."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class RolloutRecommendation(str, Enum):
    """Rollout recommendations based on test results."""
    PROCEED_WITH_CAUTION = "proceed_with_caution"
    FULL_ROLLOUT = "full_rollout"
    DO_NOT_ROLLOUT = "do_not_rollout"
    NEEDS_MORE_DATA = "needs_more_data"


class AllocationDTO(BaseModel):
    """Traffic allocation between control and treatment groups."""
    control: float = Field(ge=0.0, le=1.0, description="Control group allocation proportion")
    treatment: float = Field(ge=0.0, le=1.0, description="Treatment group allocation proportion")
    
    @field_validator('treatment')
    @classmethod
    def validate_allocation_sum(cls, v, info):
        """Ensure allocation sums to 1.0."""
        if hasattr(info, 'data') and 'control' in info.data:
            total = info.data['control'] + v
            if abs(total - 1.0) > 1e-6:
                raise ValueError(f"Allocation must sum to 1.0, got {total}")
        return v
    
    @property
    def total(self) -> float:
        """Total allocation (should always be 1.0)."""
        return self.control + self.treatment


class DurationConstraintsDTO(BaseModel):
    """Duration constraints for test design."""
    max_days: Optional[int] = Field(None, ge=1, le=365, description="Maximum test duration in days")
    min_days: Optional[int] = Field(None, ge=1, le=365, description="Minimum test duration in days")
    
    @field_validator('min_days')
    @classmethod
    def validate_duration_order(cls, v, info):
        """Ensure min_days <= max_days."""
        if v is not None and hasattr(info, 'data') and 'max_days' in info.data and info.data['max_days'] is not None:
            if v > info.data['max_days']:
                raise ValueError("min_days cannot be greater than max_days")
        return v


class BusinessContextDTO(BaseModel):
    """Business context for enhanced scenario generation."""
    company_type: CompanyType
    user_segment: UserSegment
    primary_kpi: str = Field(min_length=1, description="Primary key performance indicator")
    secondary_kpis: list[str] = Field(default_factory=list, description="Secondary KPIs to monitor")
    previous_experiments: Optional[str] = Field(None, description="Description of previous experiments")
    business_goals: Optional[str] = Field(None, description="Business goals and objectives")
    success_metrics: Optional[str] = Field(None, description="Success metrics and thresholds")


class TestQualityDTO(BaseModel):
    """Test quality indicators and potential issues."""
    early_stopping_risk: str = Field(default="low", pattern="^(low|medium|high)$")
    novelty_effect_potential: str = Field(default="medium", pattern="^(low|medium|high)$")
    seasonality_impact: str = Field(default="none", pattern="^(none|low|medium|high)$")
    traffic_consistency: float = Field(default=0.95, ge=0.0, le=1.0)
    allocation_balance: float = Field(default=0.5, ge=0.0, le=1.0)
    sample_size_adequacy: bool = Field(default=True)
    power_achieved: float = Field(default=0.8, ge=0.0, le=1.0)


class BusinessImpactDTO(BaseModel):
    """Business impact calculations and interpretations."""
    absolute_lift: float = Field(description="Absolute difference in conversion rates")
    relative_lift_pct: float = Field(description="Relative lift as percentage")
    revenue_impact_monthly: Optional[float] = Field(None, ge=0, description="Monthly revenue impact")
    confidence_in_revenue: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence in revenue projections")
    rollout_recommendation: RolloutRecommendation = Field(default=RolloutRecommendation.PROCEED_WITH_CAUTION)
    risk_level: str = Field(default="medium", pattern="^(low|medium|high)$")
    implementation_complexity: str = Field(default="low", pattern="^(low|medium|high)$")
