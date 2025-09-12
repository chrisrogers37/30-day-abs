"""
Scenario-related DTOs for business context and LLM-generated content.

This module contains schemas for business scenarios, LLM expected outcomes,
and related business context information.
"""

from typing import Dict, List, Optional, TYPE_CHECKING
from pydantic import BaseModel, Field, field_validator

from .shared import BusinessContextDTO, CompanyType, UserSegment

if TYPE_CHECKING:
    from .design import DesignParamsDTO


class ScenarioDTO(BaseModel):
    """Complete business scenario for AB testing."""
    title: str = Field(min_length=1, description="Scenario title")
    narrative: str = Field(min_length=1, description="Detailed scenario description")
    company_type: CompanyType = Field(description="Type of company")
    user_segment: UserSegment = Field(description="Target user segment")
    primary_kpi: str = Field(min_length=1, description="Primary key performance indicator")
    secondary_kpis: List[str] = Field(default_factory=list, description="Secondary KPIs to monitor")
    unit: str = Field(min_length=1, description="Unit of measurement (e.g., 'visitor', 'session')")
    assumptions: List[str] = Field(default_factory=list, description="Key assumptions for the test")
    business_context: Optional[BusinessContextDTO] = Field(None, description="Enhanced business context")
    
    @field_validator('assumptions')
    @classmethod
    def validate_assumptions(cls, v):
        """Ensure assumptions are non-empty strings."""
        for assumption in v:
            if not assumption.strip():
                raise ValueError("Assumptions cannot be empty strings")
        return v


class SimulationHintsDTO(BaseModel):
    """LLM-generated hints for simulation parameters."""
    treatment_conversion_rate: float = Field(ge=0.0, le=1.0, description="Expected treatment conversion rate")
    control_conversion_rate: float = Field(ge=0.0, le=1.0, description="Expected control conversion rate")
    
    @field_validator('treatment_conversion_rate', 'control_conversion_rate')
    @classmethod
    def validate_conversion_rates(cls, v):
        """Ensure conversion rates are reasonable."""
        if v < 0.001:
            raise ValueError("Conversion rates should be at least 0.001 (0.1%)")
        if v > 0.5:
            raise ValueError("Conversion rates should not exceed 0.5 (50%)")
        return v


class LlmExpectedDTO(BaseModel):
    """LLM-generated expected outcomes and interpretations."""
    simulation_hints: SimulationHintsDTO = Field(description="Expected conversion rates for simulation")
    narrative_conclusion: str = Field(min_length=1, description="LLM's narrative conclusion")
    business_interpretation: str = Field(min_length=1, description="Business interpretation of results")
    risk_assessment: str = Field(min_length=1, description="Risk assessment and considerations")
    next_steps: str = Field(min_length=1, description="Recommended next steps")
    notes: str = Field(
        default="These are suggestions only; use your simulator for ground truth.",
        description="Additional notes and disclaimers"
    )
    
    @field_validator('simulation_hints')
    @classmethod
    def validate_simulation_consistency(cls, v):
        """Ensure simulation hints are consistent."""
        if v.treatment_conversion_rate <= v.control_conversion_rate:
            # Allow for negative lift scenarios
            pass
        return v


class ScenarioRequestDTO(BaseModel):
    """Request to generate a new scenario."""
    company_type: Optional[CompanyType] = Field(None, description="Preferred company type")
    user_segment: Optional[UserSegment] = Field(None, description="Preferred user segment")
    complexity_level: str = Field(default="medium", pattern="^(low|medium|high)$", description="Scenario complexity")
    include_business_context: bool = Field(default=True, description="Include enhanced business context")
    previous_experiments: Optional[str] = Field(None, description="Context about previous experiments")


class ScenarioResponseDTO(BaseModel):
    """Response containing generated scenario and metadata."""
    scenario: ScenarioDTO = Field(description="Generated business scenario")
    design_params: 'DesignParamsDTO' = Field(description="Design parameters for the test")
    llm_expected: LlmExpectedDTO = Field(description="LLM's expected outcomes")
    generation_metadata: Dict[str, str] = Field(default_factory=dict, description="Metadata about generation process")
    scenario_id: str = Field(description="Unique identifier for this scenario")
    created_at: str = Field(description="ISO timestamp of creation")


# Note: Model rebuild will be done after all schemas are imported
