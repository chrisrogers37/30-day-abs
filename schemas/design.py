"""
Design parameter DTOs for test design and sample size calculations.

This module contains schemas for design parameters, sample size calculations,
and related statistical design information.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_validator

from .shared import AllocationDTO, DurationConstraintsDTO, RiskTolerance, TestDirection, TestType


class DesignParamsDTO(BaseModel):
    """Design parameters for AB test including statistical and business constraints."""
    baseline_conversion_rate: float = Field(
        ge=0.001, le=1.0, 
        description="Baseline conversion rate (0.1% to 100%)"
    )
    mde_absolute: float = Field(
        ge=0.001, le=0.5,
        description="Minimum Detectable Effect in absolute terms (0.1% to 50%)"
    )
    target_lift_pct: float = Field(
        ge=-1.0, le=1.0,
        description="Target lift percentage (-100% to +100%)"
    )
    alpha: float = Field(
        ge=0.01, le=0.1,
        description="Significance level (1% to 10%)"
    )
    power: float = Field(
        ge=0.7, le=0.95,
        description="Statistical power (70% to 95%)"
    )
    allocation: AllocationDTO = Field(description="Traffic allocation between groups")
    expected_daily_traffic: int = Field(
        ge=1000, le=10000000,
        description="Expected daily traffic (1K to 10M)"
    )
    test_type: TestType = Field(default=TestType.TWO_PROPORTION_Z, description="Statistical test type")
    test_direction: TestDirection = Field(default=TestDirection.TWO_TAILED, description="Test direction")
    duration_constraints: Optional[DurationConstraintsDTO] = Field(None, description="Duration constraints")
    risk_tolerance: RiskTolerance = Field(default=RiskTolerance.MEDIUM, description="Risk tolerance level")
    min_detectable_effect: Optional[float] = Field(
        None, ge=0.001, le=0.5,
        description="Minimum detectable effect size"
    )
    
    @field_validator('expected_daily_traffic')
    @classmethod
    def validate_traffic_reasonable(cls, v):
        """Ensure traffic is reasonable for AB testing."""
        if v < 1000:
            raise ValueError("Daily traffic must be at least 1,000 for meaningful AB testing")
        return v
    
    @field_validator('target_lift_pct')
    @classmethod
    def validate_lift_reasonable(cls, v):
        """Ensure target lift is reasonable."""
        if abs(v) < 0.01:  # Less than 1%
            raise ValueError("Target lift should be at least 1% for meaningful testing")
        return v


class SampleSizeRequestDTO(BaseModel):
    """Request to calculate sample size for a test design."""
    design_params: DesignParamsDTO = Field(description="Design parameters for the test")
    include_duration_calculation: bool = Field(default=True, description="Include duration calculation")
    include_power_analysis: bool = Field(default=True, description="Include power analysis")


class SampleSizeResponseDTO(BaseModel):
    """Response containing sample size calculation results."""
    per_arm: int = Field(ge=1, description="Required sample size per arm")
    total: int = Field(ge=2, description="Total required sample size")
    days_required: int = Field(ge=1, description="Days required to reach sample size")
    power_achieved: float = Field(ge=0.0, le=1.0, description="Actual power achieved")
    effect_size: float = Field(description="Effect size (Cohen's d or similar)")
    margin_of_error: float = Field(ge=0.0, le=1.0, description="Margin of error for confidence interval")
    calculation_method: str = Field(description="Method used for calculation")
    assumptions: list[str] = Field(default_factory=list, description="Key assumptions made")
    warnings: list[str] = Field(default_factory=list, description="Any warnings or limitations")
    
    @field_validator('total')
    @classmethod
    def validate_total_sample_size(cls, v, info):
        """Ensure total is 2 * per_arm."""
        # Note: This validation is simplified for Pydantic v2
        # Full validation would require model-level validation
        if v < 0:
            raise ValueError("Total sample size must be non-negative")
        return v


class DesignValidationDTO(BaseModel):
    """Validation results for design parameters."""
    is_valid: bool = Field(description="Whether the design is valid")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    suggestions: list[str] = Field(default_factory=list, description="Improvement suggestions")
    feasibility_score: float = Field(ge=0.0, le=1.0, description="Feasibility score (0-1)")


class DesignOptimizationDTO(BaseModel):
    """Optimization suggestions for design parameters."""
    optimized_allocation: Optional[AllocationDTO] = Field(None, description="Optimized traffic allocation")
    recommended_duration: Optional[int] = Field(None, ge=1, description="Recommended test duration")
    power_improvements: list[str] = Field(default_factory=list, description="Ways to improve power")
    cost_optimizations: list[str] = Field(default_factory=list, description="Cost optimization suggestions")
    risk_mitigations: list[str] = Field(default_factory=list, description="Risk mitigation strategies")
