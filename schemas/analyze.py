"""
Analysis-related DTOs for statistical analysis and results.

This module contains schemas for statistical analysis requests, responses,
and comprehensive analysis results including business impact.
"""

from typing import Dict, List, Optional, Tuple
from pydantic import BaseModel, Field, field_validator

from .shared import BusinessImpactDTO, TestQualityDTO
from .design import DesignParamsDTO


class TestStatisticsDTO(BaseModel):
    """Statistical test results and metrics."""
    test_statistic: float = Field(description="Test statistic value (z-score, chi-square, etc.)")
    p_value: float = Field(ge=0.0, le=1.0, description="P-value from statistical test")
    confidence_interval: Tuple[float, float] = Field(description="Confidence interval for effect size")
    confidence_level: float = Field(ge=0.0, le=1.0, description="Confidence level (e.g., 0.95)")
    effect_size: float = Field(description="Effect size (Cohen's d, relative lift, etc.)")
    power_achieved: float = Field(ge=0.0, le=1.0, description="Statistical power achieved")
    degrees_of_freedom: Optional[int] = Field(None, description="Degrees of freedom (for chi-square)")
    
    @field_validator('confidence_interval')
    @classmethod
    def validate_confidence_interval(cls, v):
        """Ensure confidence interval is valid."""
        if len(v) != 2:
            raise ValueError("Confidence interval must have exactly 2 values")
        if v[0] >= v[1]:
            raise ValueError("Lower bound must be less than upper bound")
        return v


class AnalysisRequestDTO(BaseModel):
    """Request to perform statistical analysis on test data."""
    control_n: int = Field(ge=1, description="Sample size in control group")
    control_conversions: int = Field(ge=0, description="Conversions in control group")
    treatment_n: int = Field(ge=1, description="Sample size in treatment group")
    treatment_conversions: int = Field(ge=0, description="Conversions in treatment group")
    design_params: DesignParamsDTO = Field(description="Original design parameters")
    test_type: str = Field(default="two_proportion_z", description="Statistical test to perform")
    confidence_level: float = Field(default=0.95, ge=0.0, le=1.0, description="Confidence level")
    include_business_impact: bool = Field(default=True, description="Include business impact analysis")
    include_quality_assessment: bool = Field(default=True, description="Include test quality assessment")
    
    @field_validator('control_conversions', 'treatment_conversions')
    @classmethod
    def validate_conversions(cls, v, info):
        """Ensure conversions don't exceed sample size."""
        # Note: This validation is simplified for Pydantic v2
        # Full validation would require model-level validation
        if v < 0:
            raise ValueError("Conversions must be non-negative")
        return v


class AnalysisResponseDTO(BaseModel):
    """Response containing comprehensive analysis results."""
    test_statistics: TestStatisticsDTO = Field(description="Statistical test results")
    significant: bool = Field(description="Whether the result is statistically significant")
    recommendation: str = Field(description="Recommendation based on results")
    business_impact: Optional[BusinessImpactDTO] = Field(None, description="Business impact analysis")
    test_quality: Optional[TestQualityDTO] = Field(None, description="Test quality assessment")
    analysis_metadata: Dict[str, str] = Field(default_factory=dict, description="Analysis metadata")
    warnings: List[str] = Field(default_factory=list, description="Analysis warnings")
    limitations: List[str] = Field(default_factory=list, description="Analysis limitations")


class AnswerKeyDTO(BaseModel):
    """Comprehensive answer key for user evaluation."""
    scenario_summary: str = Field(description="Summary of the test scenario")
    expected_results: TestStatisticsDTO = Field(description="Expected statistical results")
    expected_business_impact: BusinessImpactDTO = Field(description="Expected business impact")
    expected_recommendation: str = Field(description="Expected recommendation")
    key_insights: List[str] = Field(description="Key insights to look for")
    common_mistakes: List[str] = Field(description="Common mistakes to avoid")
    evaluation_criteria: Dict[str, str] = Field(description="Evaluation criteria and weights")
    tolerance_ranges: Dict[str, Tuple[float, float]] = Field(description="Acceptable ranges for user responses")


class StatisticalTestDTO(BaseModel):
    """Configuration for statistical tests."""
    test_name: str = Field(description="Name of the statistical test")
    test_type: str = Field(description="Type of test (parametric, non-parametric)")
    assumptions: List[str] = Field(description="Statistical assumptions")
    use_case: str = Field(description="When to use this test")
    limitations: List[str] = Field(description="Test limitations")
    effect_size_interpretation: Dict[str, str] = Field(description="How to interpret effect sizes")


class AnalysisComparisonDTO(BaseModel):
    """Comparison between different analysis methods."""
    method_1: str = Field(description="First analysis method")
    method_2: str = Field(description="Second analysis method")
    p_value_difference: float = Field(description="Difference in p-values")
    effect_size_difference: float = Field(description="Difference in effect sizes")
    recommendation_agreement: bool = Field(description="Whether recommendations agree")
    notes: str = Field(description="Notes about the comparison")


class SensitivityAnalysisDTO(BaseModel):
    """Sensitivity analysis results."""
    parameter_variations: Dict[str, List[float]] = Field(description="Parameter variations tested")
    p_value_range: Tuple[float, float] = Field(description="Range of p-values observed")
    effect_size_range: Tuple[float, float] = Field(description="Range of effect sizes observed")
    recommendation_stability: str = Field(description="Stability of recommendations")
    critical_parameters: List[str] = Field(description="Parameters that most affect results")
