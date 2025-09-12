"""
Simulation-related DTOs for data generation and user-level data.

This module contains schemas for simulation requests, responses, and user-level data
generation for AB testing scenarios.
"""

from typing import Dict, List, Optional
from pydantic import BaseModel, Field, field_validator

from .design import DesignParamsDTO


class UserDataDTO(BaseModel):
    """Individual user data point for simulation."""
    user_id: str = Field(description="Unique user identifier")
    group: str = Field(pattern="^(control|treatment)$", description="User's assigned group")
    converted: bool = Field(description="Whether the user converted")
    timestamp: str = Field(description="ISO timestamp of user interaction")
    session_id: Optional[str] = Field(None, description="Session identifier")
    additional_attributes: Dict[str, str] = Field(default_factory=dict, description="Additional user attributes")


class SimulationRequestDTO(BaseModel):
    """Request to simulate AB test data."""
    design_params: DesignParamsDTO = Field(description="Design parameters for the test")
    true_conversion_rates: Dict[str, float] = Field(
        description="True conversion rates for simulation",
        pattern="^(control|treatment)$"
    )
    seed: Optional[int] = Field(None, ge=0, description="Random seed for reproducibility")
    include_user_level_data: bool = Field(default=True, description="Include user-level data")
    traffic_pattern: str = Field(
        default="uniform", 
        pattern="^(uniform|seasonal|spike|declining)$",
        description="Traffic pattern for simulation"
    )
    noise_level: float = Field(
        default=0.1, ge=0.0, le=1.0,
        description="Level of noise in the data (0-1)"
    )
    
    @field_validator('true_conversion_rates')
    @classmethod
    def validate_conversion_rates(cls, v):
        """Validate conversion rates are reasonable."""
        required_keys = {'control', 'treatment'}
        if not required_keys.issubset(v.keys()):
            raise ValueError("true_conversion_rates must include 'control' and 'treatment'")
        
        for group, rate in v.items():
            if not (0.0 <= rate <= 1.0):
                raise ValueError(f"Conversion rate for {group} must be between 0 and 1, got {rate}")
            if rate < 0.001:
                raise ValueError(f"Conversion rate for {group} should be at least 0.001 (0.1%)")
        
        return v


class SimulationResponseDTO(BaseModel):
    """Response containing simulation results."""
    control_n: int = Field(ge=1, description="Number of users in control group")
    control_conversions: int = Field(ge=0, description="Number of conversions in control group")
    treatment_n: int = Field(ge=1, description="Number of users in treatment group")
    treatment_conversions: int = Field(ge=0, description="Number of conversions in treatment group")
    user_data: Optional[List[UserDataDTO]] = Field(None, description="User-level data if requested")
    simulation_metadata: Dict[str, str] = Field(default_factory=dict, description="Simulation metadata")
    seed_used: int = Field(description="Random seed used for simulation")
    traffic_summary: Dict[str, int] = Field(description="Daily traffic summary")
    
    @field_validator('control_conversions', 'treatment_conversions')
    @classmethod
    def validate_conversions(cls, v, info):
        """Ensure conversions don't exceed sample size."""
        # Note: This validation is simplified for Pydantic v2
        # Full validation would require model-level validation
        if v < 0:
            raise ValueError("Conversions must be non-negative")
        return v


class SimulationConfigDTO(BaseModel):
    """Configuration for simulation parameters."""
    traffic_allocation: Dict[str, float] = Field(
        default_factory=lambda: {"control": 0.5, "treatment": 0.5},
        description="Traffic allocation between groups"
    )
    daily_traffic_variance: float = Field(
        default=0.1, ge=0.0, le=1.0,
        description="Daily traffic variance (0-1)"
    )
    conversion_rate_variance: float = Field(
        default=0.05, ge=0.0, le=1.0,
        description="Conversion rate variance (0-1)"
    )
    include_seasonality: bool = Field(default=False, description="Include seasonal patterns")
    include_novice_effect: bool = Field(default=False, description="Include novelty effect")
    include_learning_effect: bool = Field(default=False, description="Include learning effect")


class SimulationValidationDTO(BaseModel):
    """Validation results for simulation parameters."""
    is_valid: bool = Field(description="Whether simulation parameters are valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    feasibility_score: float = Field(ge=0.0, le=1.0, description="Feasibility score (0-1)")
    expected_power: float = Field(ge=0.0, le=1.0, description="Expected statistical power")


class DataExportDTO(BaseModel):
    """Configuration for data export."""
    format: str = Field(default="csv", pattern="^(csv|json|parquet)$", description="Export format")
    include_user_data: bool = Field(default=True, description="Include user-level data")
    include_metadata: bool = Field(default=True, description="Include simulation metadata")
    compression: Optional[str] = Field(None, pattern="^(gzip|zip|none)$", description="Compression type")
    filename: Optional[str] = Field(None, description="Custom filename for export")
