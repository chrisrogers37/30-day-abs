"""
Core domain types for AB Test Simulator.

These dataclasses represent the pure mathematical domain objects with validation methods.
All types are immutable (frozen=True) to ensure data integrity.

This module contains only mathematical types - business context types are in schemas/.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class Allocation:
    """Traffic allocation between control and treatment groups."""
    control: float
    treatment: float
    
    def __post_init__(self):
        """Validate allocation proportions."""
        if not (0 < self.control < 1 and 0 < self.treatment < 1):
            raise ValueError("Allocation proportions must be between 0 and 1")
        if abs(self.control + self.treatment - 1.0) > 1e-6:
            raise ValueError(f"Allocation must sum to 1.0, got {self.control + self.treatment}")
    
    @property
    def total(self) -> float:
        """Total allocation (should always be 1.0)."""
        return self.control + self.treatment


@dataclass(frozen=True)
class DesignParams:
    """Core design parameters for AB test (mathematical only)."""
    baseline_conversion_rate: float
    target_lift_pct: float
    alpha: float
    power: float
    allocation: Allocation
    expected_daily_traffic: int
    
    def __post_init__(self):
        """Validate design parameters."""
        if not (0.001 <= self.baseline_conversion_rate <= 1.0):
            raise ValueError(f"Baseline conversion rate must be between 0.001 and 1.0, got {self.baseline_conversion_rate}")
        
        if not (-1.0 <= self.target_lift_pct <= 1.0):
            raise ValueError(f"Target lift must be between -1.0 and 1.0, got {self.target_lift_pct}")
        
        if not (0.01 <= self.alpha <= 0.1):
            raise ValueError(f"Alpha must be between 0.01 and 0.1, got {self.alpha}")
        
        if not (0.7 <= self.power <= 0.95):
            raise ValueError(f"Power must be between 0.7 and 0.95, got {self.power}")
        
        if self.expected_daily_traffic < 1000:
            raise ValueError(f"Expected daily traffic must be at least 1000, got {self.expected_daily_traffic}")


@dataclass(frozen=True)
class SampleSize:
    """Sample size calculation results."""
    per_arm: int
    total: int
    days_required: int
    power_achieved: float
    
    def __post_init__(self):
        """Validate sample size results."""
        if self.per_arm <= 0:
            raise ValueError(f"Sample size per arm must be positive, got {self.per_arm}")
        if self.total != 2 * self.per_arm:
            raise ValueError(f"Total sample size must be 2 * per_arm, got {self.total} != 2 * {self.per_arm}")
        if self.days_required <= 0:
            raise ValueError(f"Days required must be positive, got {self.days_required}")
        if not (0 <= self.power_achieved <= 1):
            raise ValueError(f"Power achieved must be between 0 and 1, got {self.power_achieved}")


@dataclass(frozen=True)
class SimResult:
    """Simulation results with user-level data."""
    control_n: int
    control_conversions: int
    treatment_n: int
    treatment_conversions: int
    user_data: Optional[List[Dict]] = None  # User-level data for detailed analysis
    
    def __post_init__(self):
        """Validate simulation results."""
        if self.control_n <= 0 or self.treatment_n <= 0:
            raise ValueError("Sample sizes must be positive")
        if self.control_conversions < 0 or self.treatment_conversions < 0:
            raise ValueError("Conversion counts cannot be negative")
        if self.control_conversions > self.control_n or self.treatment_conversions > self.treatment_n:
            raise ValueError("Conversion counts cannot exceed sample sizes")
    
    @property
    def control_rate(self) -> float:
        """Control group conversion rate."""
        return self.control_conversions / self.control_n if self.control_n > 0 else 0.0
    
    @property
    def treatment_rate(self) -> float:
        """Treatment group conversion rate."""
        return self.treatment_conversions / self.treatment_n if self.treatment_n > 0 else 0.0
    
    @property
    def absolute_lift(self) -> float:
        """Absolute difference in conversion rates."""
        return self.treatment_rate - self.control_rate
    
    @property
    def relative_lift_pct(self) -> float:
        """Relative lift as percentage."""
        if self.control_rate == 0:
            return 0.0
        return (self.treatment_rate - self.control_rate) / self.control_rate


@dataclass(frozen=True)
class AnalysisResult:
    """Statistical analysis results."""
    test_statistic: float
    p_value: float
    confidence_interval: Tuple[float, float]
    confidence_level: float
    significant: bool
    effect_size: float
    power_achieved: float
    recommendation: str
    
    def __post_init__(self):
        """Validate analysis results."""
        if not (0 <= self.p_value <= 1):
            raise ValueError(f"P-value must be between 0 and 1, got {self.p_value}")
        if not (0 < self.confidence_level < 1):
            raise ValueError(f"Confidence level must be between 0 and 1, got {self.confidence_level}")
        if len(self.confidence_interval) != 2:
            raise ValueError("Confidence interval must have exactly 2 values")
        if self.confidence_interval[0] >= self.confidence_interval[1]:
            raise ValueError("Confidence interval lower bound must be less than upper bound")
        if not (0 <= self.power_achieved <= 1):
            raise ValueError(f"Power achieved must be between 0 and 1, got {self.power_achieved}")


@dataclass(frozen=True)
class BusinessImpact:
    """Business impact calculations and interpretations (mathematical results)."""
    absolute_lift: float
    relative_lift_pct: float
    revenue_impact_monthly: Optional[float] = None
    confidence_in_revenue: Optional[float] = None
    rollout_recommendation: str = "proceed_with_caution"
    risk_level: str = "medium"
    implementation_complexity: str = "low"
    
    def __post_init__(self):
        """Validate business impact."""
        if self.revenue_impact_monthly is not None and self.revenue_impact_monthly < 0:
            raise ValueError("Revenue impact cannot be negative")
        if self.confidence_in_revenue is not None and not (0 <= self.confidence_in_revenue <= 1):
            raise ValueError("Confidence in revenue must be between 0 and 1")


@dataclass(frozen=True)
class TestQuality:
    """Test quality indicators and potential issues (mathematical assessment)."""
    early_stopping_risk: str = "low"  # low, medium, high
    novelty_effect_potential: str = "medium"
    seasonality_impact: str = "none"
    traffic_consistency: float = 0.95
    allocation_balance: float = 0.5
    sample_size_adequacy: bool = True
    power_achieved: float = 0.8
    
    def __post_init__(self):
        """Validate test quality indicators."""
        if not (0 <= self.traffic_consistency <= 1):
            raise ValueError(f"Traffic consistency must be between 0 and 1, got {self.traffic_consistency}")
        if not (0 <= self.allocation_balance <= 1):
            raise ValueError(f"Allocation balance must be between 0 and 1, got {self.allocation_balance}")
        if not (0 <= self.power_achieved <= 1):
            raise ValueError(f"Power achieved must be between 0 and 1, got {self.power_achieved}")