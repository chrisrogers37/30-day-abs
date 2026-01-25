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


class IndustryCategory(str, Enum):
    """Industry categories for organizing company types."""
    TECHNOLOGY = "Technology"
    CONSUMER = "Consumer"
    FINANCIAL = "Financial Services"
    HEALTHCARE = "Healthcare"
    INDUSTRIAL = "Industrial"


class CompanyType(str, Enum):
    """Company types for realistic business context - expanded for variety."""
    # Technology
    SAAS_B2B = "B2B SaaS"
    SAAS_B2C = "B2C SaaS"
    DEVELOPER_TOOLS = "Developer Tools"
    CYBERSECURITY = "Cybersecurity"
    AI_ML_PLATFORM = "AI/ML Platform"

    # Consumer
    ECOMMERCE_DTC = "DTC E-commerce"
    MARKETPLACE = "Marketplace"
    SUBSCRIPTION_BOX = "Subscription Box"
    FOOD_DELIVERY = "Food Delivery"
    TRAVEL = "Travel & Hospitality"
    GAMING = "Gaming"
    STREAMING = "Streaming Media"
    SOCIAL_NETWORK = "Social Network"
    FITNESS_APP = "Fitness/Wellness App"
    DATING_APP = "Dating App"
    NEWS_MEDIA = "News & Media"

    # Financial Services
    NEOBANK = "Neobank"
    INVESTING_APP = "Investing Platform"
    INSURANCE = "Insurtech"
    PAYMENTS = "Payments"
    LENDING = "Lending Platform"
    CRYPTO = "Crypto/Web3"

    # Healthcare
    TELEHEALTH = "Telehealth"
    HEALTH_TRACKING = "Health Tracking"
    PHARMACY = "Digital Pharmacy"
    MENTAL_HEALTH = "Mental Health App"

    # Industrial / B2B
    LOGISTICS = "Logistics"
    HR_TECH = "HR Tech"
    EDTECH = "EdTech"
    REAL_ESTATE = "PropTech"
    LEGAL_TECH = "Legal Tech"

    # Legacy mappings for backward compatibility
    SAAS = "SaaS"  # Maps to SAAS_B2B
    ECOMMERCE = "E-commerce"  # Maps to ECOMMERCE_DTC
    MEDIA = "Media"  # Maps to NEWS_MEDIA
    MEDIA_CONTENT = "Media/Content"  # Maps to STREAMING
    FINTECH = "Fintech"  # Maps to NEOBANK


class UserSegment(str, Enum):
    """User segments for targeted testing - expanded for variety."""
    # Lifecycle Stages
    NEW_VISITORS = "first-time visitors"
    NEW_SIGNUPS = "new signups (< 7 days)"
    ACTIVATED_USERS = "activated users"
    ENGAGED_USERS = "weekly active users"
    POWER_USERS = "power users (top 10%)"
    AT_RISK_USERS = "at-risk users (inactive 14+ days)"
    CHURNED_REACTIVATION = "churned users (win-back)"
    DORMANT_USERS = "dormant users (30-90 days inactive)"

    # Value Tiers
    FREE_TIER = "free tier users"
    TRIAL_USERS = "trial users"
    PAID_USERS = "paid subscribers"
    ENTERPRISE = "enterprise accounts"
    HIGH_LTV = "high-LTV customers"
    LOW_LTV = "low-LTV customers"

    # Behavioral Segments
    MOBILE_USERS = "mobile app users"
    DESKTOP_USERS = "desktop users"
    HIGH_INTENT = "high-intent searchers"
    CART_ABANDONERS = "cart abandoners"
    REPEAT_PURCHASERS = "repeat purchasers"
    FIRST_TIME_BUYERS = "first-time buyers"
    BROWSERS = "browsers (no purchase history)"

    # Geographic Segments
    US_USERS = "US users"
    INTERNATIONAL = "international users"
    EMERGING_MARKETS = "emerging market users"
    EU_USERS = "EU users"

    # Legacy mappings for backward compatibility
    NEW_USERS = "new_users"
    RETURNING_USERS = "returning_users"
    PREMIUM_USERS = "premium_users"
    ALL_USERS = "all_users"


class MetricType(str, Enum):
    """Metric types for A/B testing - determines baseline ranges and analysis approach."""
    # Conversion Metrics (proportion-based)
    CONVERSION_RATE = "conversion_rate"
    SIGNUP_RATE = "signup_rate"
    ACTIVATION_RATE = "activation_rate"
    PURCHASE_RATE = "purchase_rate"
    CHECKOUT_COMPLETION = "checkout_completion_rate"
    FORM_COMPLETION = "form_completion_rate"

    # Engagement Metrics (proportion-based)
    CLICK_THROUGH_RATE = "click_through_rate"
    ENGAGEMENT_RATE = "engagement_rate"
    FEATURE_ADOPTION = "feature_adoption_rate"
    CONTENT_COMPLETION = "content_completion_rate"
    VIDEO_COMPLETION = "video_completion_rate"
    SHARE_RATE = "share_rate"

    # Retention Metrics (proportion-based)
    DAY_1_RETENTION = "day_1_retention"
    DAY_7_RETENTION = "day_7_retention"
    DAY_30_RETENTION = "day_30_retention"
    WEEKLY_RETENTION = "weekly_retention"
    MONTHLY_RETENTION = "monthly_retention"
    CHURN_RATE = "churn_rate"

    # Revenue Metrics (continuous - future support)
    REVENUE_PER_USER = "revenue_per_user"
    AVERAGE_ORDER_VALUE = "average_order_value"
    ARPU = "average_revenue_per_user"
    LTV = "lifetime_value"

    # Quality Metrics (proportion-based)
    ERROR_RATE = "error_rate"
    BOUNCE_RATE = "bounce_rate"
    SUPPORT_CONTACT_RATE = "support_contact_rate"
    REFUND_RATE = "refund_rate"
    NPS_PROMOTER_RATE = "nps_promoter_rate"


class EffectSizeProfile(str, Enum):
    """Effect size profiles for different experiment types."""
    INCREMENTAL = "incremental"  # 2-10% relative lift - mature product optimization
    SIGNIFICANT = "significant"  # 10-30% relative lift - major changes
    TRANSFORMATIONAL = "transformational"  # 30-100% relative lift - new approaches
    DEFENSIVE = "defensive"  # -10% to +5% - proving no harm


class TrafficTier(str, Enum):
    """Traffic tiers for different company stages."""
    EARLY_STAGE = "early_stage"  # 100 - 1,000 daily
    GROWTH = "growth"  # 1,000 - 10,000 daily
    SCALE = "scale"  # 10,000 - 100,000 daily
    ENTERPRISE = "enterprise"  # 100,000 - 1,000,000 daily


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
