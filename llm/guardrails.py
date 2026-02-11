"""
Guardrails Module - Comprehensive Validation and Parameter Bounds Checking

This module provides comprehensive validation and parameter bounds checking for
LLM-generated AB test scenarios. It ensures that all generated scenarios meet
statistical soundness requirements, business context consistency, and realism
criteria through a multi-layered validation system.

Key Features:
- Parameter bounds validation with statistical soundness checks
- Business context consistency validation (company type, user segment)
- Mathematical consistency validation (parameter relationships)
- Realism and feasibility assessment
- Parameter clamping with automatic correction
- Quality scoring with quantitative assessment
- Regeneration hints for failed validations
- Comprehensive error reporting and suggestions

Validation Layers:
1. Parameter Bounds: Statistical parameter range validation
2. Business Context: Company type and user segment consistency
3. Parameter Consistency: Mathematical relationship validation
4. Metric Consistency: Proportion-based metric validation
5. Realism Checks: Feasibility and business realism assessment

Parameter Bounds:
- baseline_conversion_rate: 0.001 to 0.5 (0.1% to 50%)
- mde_absolute: 0.001 to 0.1 (0.1% to 10% percentage points)
- target_lift_pct: -0.5 to 0.5 (-50% to +50%)
- alpha: 0.01 to 0.1 (1% to 10%)
- power: 0.7 to 0.95 (70% to 95%)
- expected_daily_traffic: 500 to 5,000

Business Context Validation:
- Company type scenarios (E-commerce, SaaS, Media, Fintech, etc.)
- User segment contexts (new users, returning users, premium users)
- KPI appropriateness for proportion-based testing
- Unit consistency with measurement type

Mathematical Consistency:
- Baseline vs control rate consistency
- Target lift vs actual lift consistency
- MDE absolute vs target lift percentage relationship
- Allocation proportion validation (must sum to 1.0)

Quality Scoring:
- Quantitative assessment (0-1 scale)
- Penalties for unrealistic values
- Consistency bonus for aligned parameters
- Business context alignment scoring

Error Handling:
- Specific validation error types
- Detailed error messages with context
- Regeneration hints for common issues
- Graceful degradation with warnings

Usage Examples:
    Basic validation:
        guardrails = LLMGuardrails()
        result = guardrails.validate_scenario(scenario_dto)
    
    Parameter clamping:
        clamped_scenario, clamped_values = guardrails.clamp_parameters(scenario_dto)
    
    Quality scoring:
        quality_score = guardrails.get_quality_score(scenario_dto)
    
    Regeneration hints:
        hints = guardrails.generate_regeneration_hints(validation_result)

Dependencies:
- schemas.scenario: Scenario DTOs for validation
- schemas.design: Design parameter DTOs
- schemas.shared: Shared enums and types
- logging: Built-in logging support
"""

from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from schemas.scenario import ScenarioResponseDTO
from schemas.shared import (
    MetricType, EffectSizeProfile, TrafficTier
)

from core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ValidationResult:
    """
    Comprehensive result dataclass for guardrail validation operations.
    
    This dataclass encapsulates all information about a validation attempt,
    including validation status, quality assessment, detailed error/warning
    information, and parameter clamping results.
    
    Attributes:
        is_valid (bool): Whether the scenario passed all validation checks
        quality_score (float): Quantitative quality score (0-1)
        errors (List[str]): List of validation errors that must be fixed
        warnings (List[str]): List of warnings about potential issues
        suggestions (List[str]): List of suggestions for improvement
        clamped_values (Dict[str, Tuple[float, float]]): Dictionary mapping
            field names to (original_value, clamped_value) tuples for parameters
            that were automatically corrected
    
    Examples:
        Check validation status:
            result = guardrails.validate_scenario(scenario_dto)
            if result.is_valid:
                print("Scenario passed validation")
            else:
                print(f"Validation failed: {result.errors}")
        
        Analyze quality:
            if result.quality_score < 0.7:
                print(f"Low quality scenario: {result.quality_score:.2f}")
        
        Review warnings:
            for warning in result.warnings:
                print(f"Warning: {warning}")
        
        Check parameter clamping:
            if result.clamped_values:
                print("Some parameters were automatically corrected:")
                for field, (original, clamped) in result.clamped_values.items():
                    print(f"  {field}: {original} -> {clamped}")
    """
    is_valid: bool
    quality_score: float = 0.0
    errors: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    clamped_values: Dict[str, Tuple[float, float]] = None  # field_name: (original, clamped)
    
    def __post_init__(self):
        """Initialize empty lists and dictionaries if None."""
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []
        if self.suggestions is None:
            self.suggestions = []
        if self.clamped_values is None:
            self.clamped_values = {}


class GuardrailError(Exception):
    """Exception raised when guardrail validation fails."""
    pass


class LLMGuardrails:
    """
    Comprehensive guardrails for LLM output validation and parameter bounds checking.
    
    This class provides a multi-layered validation system for LLM-generated AB test
    scenarios, ensuring statistical soundness, business context consistency, and
    realism through comprehensive parameter validation and quality scoring.
    
    Features:
        - Parameter bounds validation with statistical soundness checks
        - Business context consistency validation (company type, user segment)
        - Mathematical consistency validation (parameter relationships)
        - Realism and feasibility assessment
        - Parameter clamping with automatic correction
        - Quality scoring with quantitative assessment
        - Regeneration hints for failed validations
        - Comprehensive error reporting and suggestions
    
    Validation Layers:
        1. Parameter Bounds: Statistical parameter range validation
        2. Business Context: Company type and user segment consistency
        3. Parameter Consistency: Mathematical relationship validation
        4. Metric Consistency: Proportion-based metric validation
        5. Realism Checks: Feasibility and business realism assessment
    
    Attributes:
        bounds (Dict[str, Tuple[float, float]]): Parameter bounds for validation
        business_rules (Dict): Business context validation rules
    
    Examples:
        Basic validation:
            guardrails = LLMGuardrails()
            result = guardrails.validate_scenario(scenario_dto)
        
        Parameter clamping:
            clamped_scenario, clamped_values = guardrails.clamp_parameters(scenario_dto)
        
        Quality scoring:
            quality_score = guardrails.get_quality_score(scenario_dto)
        
        Regeneration hints:
            hints = guardrails.generate_regeneration_hints(validation_result)
    
    Parameter Bounds:
        - baseline_conversion_rate: 0.001 to 0.5 (0.1% to 50%)
        - mde_absolute: 0.001 to 0.1 (0.1% to 10% percentage points)
        - target_lift_pct: -0.5 to 0.5 (-50% to +50%)
        - alpha: 0.01 to 0.1 (1% to 10%)
        - power: 0.7 to 0.95 (70% to 95%)
        - expected_daily_traffic: 500 to 5,000
    """
    
    def __init__(self):
        """
        Initialize the guardrails with parameter bounds and business rules.

        Sets up the validation system with:
        - Statistical parameter bounds for AB testing (expanded for variety)
        - Metric-specific baseline ranges
        - Traffic tier definitions
        - Effect size profiles
        """
        # Parameter bounds for statistical validation - EXPANDED for variety
        self.bounds = {
            'baseline_conversion_rate': (0.001, 0.8),  # 0.1% to 80% (expanded)
            'mde_absolute': (0.001, 0.2),  # 0.1% to 20% percentage points (expanded)
            'target_lift_pct': (-0.5, 1.0),  # -50% to +100% (expanded for transformational)
            'alpha': (0.001, 0.2),  # 0.1% to 20% (expanded)
            'power': (0.5, 0.99),  # 50% to 99% (expanded)
            'expected_daily_traffic': (100, 10_000_000),  # 100 to 10M daily (massively expanded)
            'treatment_conversion_rate': (0.001, 0.8),  # 0.1% to 80%
            'control_conversion_rate': (0.001, 0.8)  # 0.1% to 80%
        }

        # Traffic tier definitions for different company stages
        self.traffic_tiers = {
            TrafficTier.EARLY_STAGE: (100, 1_000),
            TrafficTier.GROWTH: (1_000, 10_000),
            TrafficTier.SCALE: (10_000, 100_000),
            TrafficTier.ENTERPRISE: (100_000, 10_000_000)
        }

        # Metric-specific baseline ranges for realistic scenarios
        self.metric_baseline_ranges = {
            # Conversion metrics - typically low
            MetricType.CONVERSION_RATE: (0.001, 0.15),
            MetricType.SIGNUP_RATE: (0.01, 0.40),
            MetricType.ACTIVATION_RATE: (0.10, 0.80),
            MetricType.PURCHASE_RATE: (0.005, 0.20),
            MetricType.CHECKOUT_COMPLETION: (0.30, 0.85),
            MetricType.FORM_COMPLETION: (0.10, 0.70),

            # Engagement metrics - varies widely
            MetricType.CLICK_THROUGH_RATE: (0.005, 0.30),
            MetricType.ENGAGEMENT_RATE: (0.05, 0.60),
            MetricType.FEATURE_ADOPTION: (0.01, 0.50),
            MetricType.CONTENT_COMPLETION: (0.20, 0.80),
            MetricType.VIDEO_COMPLETION: (0.15, 0.70),
            MetricType.SHARE_RATE: (0.001, 0.10),

            # Retention metrics - typically moderate to high
            MetricType.DAY_1_RETENTION: (0.20, 0.70),
            MetricType.DAY_7_RETENTION: (0.10, 0.50),
            MetricType.DAY_30_RETENTION: (0.05, 0.35),
            MetricType.WEEKLY_RETENTION: (0.30, 0.80),
            MetricType.MONTHLY_RETENTION: (0.20, 0.70),
            MetricType.CHURN_RATE: (0.01, 0.20),

            # Quality metrics - typically low (errors) or moderate (bounce)
            MetricType.ERROR_RATE: (0.001, 0.10),
            MetricType.BOUNCE_RATE: (0.20, 0.70),
            MetricType.SUPPORT_CONTACT_RATE: (0.01, 0.15),
            MetricType.REFUND_RATE: (0.01, 0.10),
            MetricType.NPS_PROMOTER_RATE: (0.20, 0.70),
        }

        # Effect size profiles for different experiment types
        self.effect_size_profiles = {
            EffectSizeProfile.INCREMENTAL: {
                'relative_lift_range': (0.02, 0.10),  # 2-10% relative
                'description': 'Mature product optimization - small iterative improvements'
            },
            EffectSizeProfile.SIGNIFICANT: {
                'relative_lift_range': (0.10, 0.30),  # 10-30% relative
                'description': 'Major UX overhaul, new feature launch, significant changes'
            },
            EffectSizeProfile.TRANSFORMATIONAL: {
                'relative_lift_range': (0.30, 1.00),  # 30-100% relative
                'description': 'Completely new approach, radical redesign, high-risk test'
            },
            EffectSizeProfile.DEFENSIVE: {
                'relative_lift_range': (-0.10, 0.05),  # -10% to +5%
                'description': 'Proving no harm - cost reduction, infrastructure change'
            }
        }

        # Alpha/power guidance based on business context
        self.alpha_guidance = {
            'high_stakes': 0.01,  # Irreversible changes, brand risk, regulatory
            'standard': 0.05,  # Standard product decisions
            'exploratory': 0.10,  # Easy rollback, low stakes
            'very_exploratory': 0.15,  # Quick directional signal
        }

        self.power_guidance = {
            'quick_signal': 0.60,  # Very limited resources, directional only
            'exploratory': 0.70,  # Quick directional signal
            'standard': 0.80,  # Balance of speed and confidence
            'important': 0.90,  # High-value opportunity
            'critical': 0.95,  # Must not miss true effect
        }

        # Note: Removed restrictive keyword validation rules
        # The LLM is now free to generate creative, varied narratives
        # without being constrained to specific keyword patterns
    
    def validate_scenario(self, scenario_response_dto: ScenarioResponseDTO) -> ValidationResult:
        """
        Comprehensive validation of generated scenario.
        
        Args:
            scenario_dto: Generated scenario to validate
            
        Returns:
            ValidationResult with validation results and suggestions
        """
        result = ValidationResult(is_valid=True)
        
        try:
            # Validate design parameters
            self._validate_design_params(scenario_response_dto, result)
            
            # Validate business context consistency
            self._validate_business_context(scenario_response_dto, result)
            
            # Validate parameter consistency
            self._validate_parameter_consistency(scenario_response_dto, result)
            
            # Validate metric consistency (proportion-based metrics only)
            self._validate_metric_consistency(scenario_response_dto, result)
            
            # Validate realism
            self._validate_realism(scenario_response_dto, result)
            
            # Calculate quality score
            result.quality_score = self.get_quality_score(scenario_response_dto)
            
            # Determine overall validity
            result.is_valid = len(result.errors) == 0
            
        except Exception as e:
            logger.error(f"Error in guardrail validation: {e}")
            result.is_valid = False
            result.errors.append(f"Validation error: {str(e)}")
        
        return result
    
    def _validate_design_params(self, scenario_response_dto: ScenarioResponseDTO, result: ValidationResult):
        """Validate design parameters against bounds."""
        design_params = scenario_response_dto.design_params
        
        # Check baseline conversion rate
        baseline = design_params.baseline_conversion_rate
        if not (self.bounds['baseline_conversion_rate'][0] <= baseline <= self.bounds['baseline_conversion_rate'][1]):
            result.errors.append(
                f"Baseline conversion rate {baseline} is outside valid range "
                f"[{self.bounds['baseline_conversion_rate'][0]}, {self.bounds['baseline_conversion_rate'][1]}]"
            )
        
        # Check MDE absolute (must be in percentage points)
        mde_absolute = design_params.mde_absolute
        if not (self.bounds['mde_absolute'][0] <= mde_absolute <= self.bounds['mde_absolute'][1]):
            result.errors.append(
                f"MDE absolute {mde_absolute} is outside valid range "
                f"[{self.bounds['mde_absolute'][0]}, {self.bounds['mde_absolute'][1]}] "
                f"(must be a raw ratio between 0.001-0.1, not absolute time/revenue)"
            )
        
        # Check target lift
        target_lift = design_params.target_lift_pct
        if not (self.bounds['target_lift_pct'][0] <= target_lift <= self.bounds['target_lift_pct'][1]):
            result.errors.append(
                f"Target lift {target_lift} is outside valid range "
                f"[{self.bounds['target_lift_pct'][0]}, {self.bounds['target_lift_pct'][1]}]"
            )
        
        # Check alpha
        alpha = design_params.alpha
        if not (self.bounds['alpha'][0] <= alpha <= self.bounds['alpha'][1]):
            result.errors.append(
                f"Alpha {alpha} is outside valid range "
                f"[{self.bounds['alpha'][0]}, {self.bounds['alpha'][1]}]"
            )
        
        # Check power
        power = design_params.power
        if not (self.bounds['power'][0] <= power <= self.bounds['power'][1]):
            result.errors.append(
                f"Power {power} is outside valid range "
                f"[{self.bounds['power'][0]}, {self.bounds['power'][1]}]"
            )
        
        # Check daily traffic
        traffic = design_params.expected_daily_traffic
        if not (self.bounds['expected_daily_traffic'][0] <= traffic <= self.bounds['expected_daily_traffic'][1]):
            result.errors.append(
                f"Daily traffic {traffic} is outside valid range "
                f"[{self.bounds['expected_daily_traffic'][0]}, {self.bounds['expected_daily_traffic'][1]}]"
            )
        
        # Check allocation
        allocation = design_params.allocation
        if abs(allocation.control + allocation.treatment - 1.0) > 0.001:
            result.errors.append(
                f"Allocation must sum to 1.0, got {allocation.control + allocation.treatment}"
            )
    
    def _validate_business_context(self, scenario_response_dto: ScenarioResponseDTO, result: ValidationResult):
        """
        Validate business context consistency.

        Note: Keyword validation has been removed to allow more creative,
        varied scenario narratives. The LLM is now free to generate diverse
        scenarios without being constrained to specific keyword patterns.
        """
        scenario = scenario_response_dto.scenario

        # Basic validation - ensure required fields are present and non-empty
        if not scenario.title or len(scenario.title.strip()) < 10:
            result.warnings.append("Scenario title seems too short - consider more descriptive title")

        if not scenario.narrative or len(scenario.narrative.strip()) < 50:
            result.warnings.append("Scenario narrative seems too short - consider more detailed context")

        # Check that company_type and user_segment are valid enum values
        # (Pydantic should handle this, but double-check)
        try:
            _ = scenario.company_type.value
        except (AttributeError, ValueError):
            result.errors.append(f"Invalid company type: {scenario.company_type}")

        try:
            _ = scenario.user_segment.value
        except (AttributeError, ValueError):
            result.errors.append(f"Invalid user segment: {scenario.user_segment}")

        # Light validation for primary KPI format
        primary_kpi = scenario.primary_kpi.lower()
        if not primary_kpi or len(primary_kpi) < 3:
            result.warnings.append("Primary KPI should be clearly specified")
    
    def _validate_parameter_consistency(self, scenario_response_dto: ScenarioResponseDTO, result: ValidationResult):
        """Validate parameter consistency."""
        design_params = scenario_response_dto.design_params
        llm_expected = scenario_response_dto.llm_expected
        simulation_hints = llm_expected.simulation_hints
        
        # Check baseline vs control rate consistency
        baseline = design_params.baseline_conversion_rate
        control_rate = simulation_hints.control_conversion_rate
        if abs(baseline - control_rate) > 0.001:
            result.warnings.append(
                f"Baseline rate ({baseline:.3f}) doesn't match control rate ({control_rate:.3f})"
            )
        
        # Check target lift vs actual lift consistency
        target_lift = design_params.target_lift_pct
        treatment_rate = simulation_hints.treatment_conversion_rate
        if baseline > 0:
            actual_lift = (treatment_rate - baseline) / baseline
            if abs(actual_lift - target_lift) > 0.05:  # 5% tolerance
                result.warnings.append(
                    f"Target lift ({target_lift:.1%}) doesn't match actual lift ({actual_lift:.1%})"
                )
        
        # Check conversion rate bounds
        for rate_name, rate_value in [
            ('control_conversion_rate', control_rate),
            ('treatment_conversion_rate', treatment_rate)
        ]:
            bounds = self.bounds.get(rate_name)
            if bounds and not (bounds[0] <= rate_value <= bounds[1]):
                result.errors.append(
                    f"{rate_name} {rate_value} is outside valid range [{bounds[0]}, {bounds[1]}]"
                )
    
    def _validate_metric_consistency(self, scenario_response_dto: ScenarioResponseDTO, result: ValidationResult):
        """Validate that metrics are proportion-based and consistent with statistical tests."""
        scenario = scenario_response_dto.scenario
        design_params = scenario_response_dto.design_params
        
        # Check that MDE is reasonable for proportion-based metrics
        mde_absolute = design_params.mde_absolute
        baseline = design_params.baseline_conversion_rate
        target_lift = design_params.target_lift_pct
        
        # CRITICAL: Check mathematical consistency between mde_absolute and target_lift_pct
        expected_target_lift = mde_absolute / baseline if baseline > 0 else 0
        if abs(target_lift - expected_target_lift) > 0.001:  # 0.1% tolerance
            result.errors.append(
                f"Mathematical inconsistency: mde_absolute ({mde_absolute:.3f}) and target_lift_pct ({target_lift:.3f}) are not consistent. "
                f"Expected target_lift_pct = mde_absolute / baseline = {expected_target_lift:.3f}. "
                f"Please ensure: mde_absolute = baseline × target_lift_pct"
            )
        
        # MDE should be a reasonable percentage of baseline (not more than 50% of baseline)
        if mde_absolute > baseline * 0.5:
            result.warnings.append(
                f"MDE ({mde_absolute:.1%}) is very large relative to baseline ({baseline:.1%}). "
                f"Consider if this is realistic for a proportion-based metric."
            )
        
        # Check that primary KPI is appropriate for proportion-based testing
        primary_kpi = scenario.primary_kpi.lower()
        valid_proportion_kpis = ['conversion_rate', 'click_through_rate', 'engagement_rate']
        
        if primary_kpi not in valid_proportion_kpis:
            result.warnings.append(
                f"Primary KPI '{primary_kpi}' may not be appropriate for proportion-based testing. "
                f"Consider using: {valid_proportion_kpis}"
            )
    
    def _validate_realism(self, scenario_response_dto: ScenarioResponseDTO, result: ValidationResult):
        """
        Validate realism of the scenario with expanded, flexible bounds.

        This validation is now much more permissive to allow diverse scenarios
        across different company stages, industries, and experiment types.
        """
        design_params = scenario_response_dto.design_params

        # Check conversion rates against expanded bounds only
        baseline = design_params.baseline_conversion_rate
        if baseline > 0.8:  # 80% - truly extreme
            result.warnings.append(
                f"Baseline conversion rate {baseline:.1%} is very high - ensure this is realistic for the metric type"
            )
        elif baseline < 0.001:  # 0.1% - truly extreme
            result.warnings.append(
                f"Baseline conversion rate {baseline:.1%} is very low - ensure this is realistic for the metric type"
            )

        # Check target lift - only warn for truly extreme values
        target_lift = design_params.target_lift_pct
        if target_lift > 2.0:  # 200% relative lift
            result.warnings.append(
                f"Target lift {target_lift:.1%} is very ambitious - consider if this is achievable"
            )
        elif target_lift < -0.5:  # -50% relative lift
            result.warnings.append(
                f"Target lift {target_lift:.1%} suggests significant negative impact expected"
            )

        # Traffic validation is now informational, not restrictive
        traffic = design_params.expected_daily_traffic
        if traffic > 10_000_000:  # 10M daily - truly massive
            result.warnings.append(
                f"Daily traffic {traffic:,} is enterprise-scale - ensure experiment can handle this volume"
            )
        elif traffic < 100:  # Very small
            result.warnings.append(
                f"Daily traffic {traffic:,} is very low - experiment duration may be very long"
            )

        # Power validation - informational only
        power = design_params.power
        if power > 0.95:
            result.suggestions.append(
                f"Power {power:.1%} is very high - consider if this precision is needed vs. faster iteration"
            )
        elif power < 0.6:
            result.suggestions.append(
                f"Power {power:.1%} is low - results may be directional only, higher risk of false negatives"
            )
    
    def clamp_parameters(self, scenario_response_dto: ScenarioResponseDTO) -> Tuple[ScenarioResponseDTO, Dict[str, Tuple[float, float]]]:
        """
        Clamp parameters to valid ranges with warnings.
        
        Args:
            scenario_response_dto: Scenario to clamp
            
        Returns:
            Tuple of (clamped_scenario, clamped_values)
        """
        clamped_values = {}
        
        # Create a copy to modify
        import copy
        clamped_scenario = copy.deepcopy(scenario_response_dto)
        
        # Clamp design parameters
        design_params = clamped_scenario.design_params
        
        # Clamp baseline conversion rate
        original = design_params.baseline_conversion_rate
        clamped = max(self.bounds['baseline_conversion_rate'][0], 
                     min(self.bounds['baseline_conversion_rate'][1], original))
        if abs(original - clamped) > 0.001:
            design_params.baseline_conversion_rate = clamped
            clamped_values['baseline_conversion_rate'] = (original, clamped)
        
        # Clamp target lift
        original = design_params.target_lift_pct
        clamped = max(self.bounds['target_lift_pct'][0], 
                     min(self.bounds['target_lift_pct'][1], original))
        if abs(original - clamped) > 0.001:
            design_params.target_lift_pct = clamped
            clamped_values['target_lift_pct'] = (original, clamped)
        
        # Clamp alpha
        original = design_params.alpha
        clamped = max(self.bounds['alpha'][0], 
                     min(self.bounds['alpha'][1], original))
        if abs(original - clamped) > 0.001:
            design_params.alpha = clamped
            clamped_values['alpha'] = (original, clamped)
        
        # Clamp power
        original = design_params.power
        clamped = max(self.bounds['power'][0], 
                     min(self.bounds['power'][1], original))
        if abs(original - clamped) > 0.001:
            design_params.power = clamped
            clamped_values['power'] = (original, clamped)
        
        # Clamp daily traffic
        original = design_params.expected_daily_traffic
        clamped = max(self.bounds['expected_daily_traffic'][0], 
                     min(self.bounds['expected_daily_traffic'][1], original))
        if abs(original - clamped) > 0.001:
            design_params.expected_daily_traffic = clamped
            clamped_values['expected_daily_traffic'] = (original, clamped)
        
        # Clamp simulation hints
        simulation_hints = clamped_scenario.llm_expected.simulation_hints
        
        # Clamp control rate
        original = simulation_hints.control_conversion_rate
        clamped = max(self.bounds['control_conversion_rate'][0], 
                     min(self.bounds['control_conversion_rate'][1], original))
        if abs(original - clamped) > 0.001:
            simulation_hints.control_conversion_rate = clamped
            clamped_values['control_conversion_rate'] = (original, clamped)
        
        # Clamp treatment rate
        original = simulation_hints.treatment_conversion_rate
        clamped = max(self.bounds['treatment_conversion_rate'][0], 
                     min(self.bounds['treatment_conversion_rate'][1], original))
        if abs(original - clamped) > 0.001:
            simulation_hints.treatment_conversion_rate = clamped
            clamped_values['treatment_conversion_rate'] = (original, clamped)
        
        return clamped_scenario, clamped_values
    
    def generate_regeneration_hints(self, validation_result: ValidationResult) -> List[str]:
        """Generate hints for regenerating the scenario."""
        hints = []
        
        for error in validation_result.errors:
            if "outside valid range" in error:
                hints.append("Ensure all parameters are within the specified bounds")
            elif "must sum to 1.0" in error:
                hints.append("Ensure allocation proportions sum to exactly 1.0")
            elif "doesn't match" in error:
                hints.append("Ensure parameter consistency between design and expected outcomes")
        
        for warning in validation_result.warnings:
            if "doesn't seem to match" in warning:
                hints.append("Ensure scenario content matches the specified company type and user segment")
            elif "seems high" in warning or "seems low" in warning:
                hints.append("Use more realistic parameter values for the business context")
            elif "seems ambitious" in warning:
                hints.append("Consider more conservative target lift values")
        
        if not hints:
            hints.append("Review the scenario for overall realism and business context consistency")
        
        return hints
    
    def get_quality_score(self, scenario_response_dto: ScenarioResponseDTO) -> float:
        """
        Calculate a quality score for the scenario (0-1).

        Quality is now assessed based on internal consistency and completeness,
        not on narrow parameter ranges. Diverse scenarios are encouraged.

        Args:
            scenario_response_dto: Scenario to score

        Returns:
            Quality score between 0 and 1
        """
        score = 1.0

        design_params = scenario_response_dto.design_params
        scenario = scenario_response_dto.scenario

        # Deduct for truly extreme/impossible values only
        if design_params.baseline_conversion_rate > 0.95:  # Can't have >95% baseline
            score -= 0.2
        if design_params.baseline_conversion_rate < 0.0001:  # Too small to measure
            score -= 0.2

        # Deduct for impossible lifts
        if design_params.target_lift_pct > 5.0:  # 500% lift is unrealistic
            score -= 0.2
        if design_params.target_lift_pct < -0.9:  # -90% would eliminate the metric
            score -= 0.2

        # Deduct for internal inconsistency between baseline and simulation hints
        baseline = design_params.baseline_conversion_rate
        control_rate = scenario_response_dto.llm_expected.simulation_hints.control_conversion_rate
        if abs(baseline - control_rate) > 0.01:  # Allow 1% tolerance
            score -= 0.1

        # Bonus for rich narrative content
        if len(scenario.narrative) > 200:
            score += 0.05
        if len(scenario.title) > 30:
            score += 0.05

        # Deduct for missing or minimal content
        if len(scenario.narrative) < 50:
            score -= 0.15
        if len(scenario.title) < 10:
            score -= 0.1

        return max(0.0, min(1.0, score))


# =============================================================================
# NOVELTY SCORING SYSTEM
# =============================================================================

class NoveltyScorer:
    """
    Scores how different a new scenario is from recently generated ones.

    This helps prevent repetitive scenarios by tracking what types of scenarios
    have been generated recently and penalizing similar combinations.

    Features:
        - Tracks recent scenarios by company type, segment, traffic tier, etc.
        - Calculates novelty score (0-1) for new scenarios
        - Provides suggestions for increasing diversity

    Usage:
        scorer = NoveltyScorer(history_size=20)
        novelty = scorer.score_novelty(new_scenario)
        if novelty < 0.5:
            print("Consider a different company type or segment")
        scorer.record_scenario(new_scenario)  # Add to history after generation
    """

    def __init__(self, history_size: int = 20):
        """
        Initialize the novelty scorer.

        Args:
            history_size: Number of recent scenarios to track for comparison
        """
        self.history_size = history_size
        self.recent_scenarios: List[Dict] = []

    def _extract_features(self, scenario_dto: ScenarioResponseDTO) -> Dict:
        """Extract features from a scenario for comparison."""
        scenario = scenario_dto.scenario
        design_params = scenario_dto.design_params

        # Determine traffic tier
        traffic = design_params.expected_daily_traffic
        if traffic < 1000:
            traffic_tier = "early_stage"
        elif traffic < 10000:
            traffic_tier = "growth"
        elif traffic < 100000:
            traffic_tier = "scale"
        else:
            traffic_tier = "enterprise"

        # Determine baseline tier
        baseline = design_params.baseline_conversion_rate
        if baseline < 0.01:
            baseline_tier = "very_low"
        elif baseline < 0.05:
            baseline_tier = "low"
        elif baseline < 0.15:
            baseline_tier = "medium"
        elif baseline < 0.30:
            baseline_tier = "high"
        else:
            baseline_tier = "very_high"

        # Determine effect size tier
        lift = design_params.target_lift_pct
        if lift < 0.05:
            effect_tier = "incremental"
        elif lift < 0.20:
            effect_tier = "moderate"
        elif lift < 0.50:
            effect_tier = "significant"
        else:
            effect_tier = "transformational"

        return {
            "company_type": scenario.company_type.value if hasattr(scenario.company_type, 'value') else str(scenario.company_type),
            "user_segment": scenario.user_segment.value if hasattr(scenario.user_segment, 'value') else str(scenario.user_segment),
            "primary_kpi": scenario.primary_kpi,
            "traffic_tier": traffic_tier,
            "baseline_tier": baseline_tier,
            "effect_tier": effect_tier,
            "alpha": design_params.alpha,
            "power": design_params.power,
        }

    def score_novelty(self, scenario_dto: ScenarioResponseDTO) -> float:
        """
        Calculate a novelty score for a scenario compared to recent history.

        Args:
            scenario_dto: The scenario to score

        Returns:
            Novelty score from 0 (highly repetitive) to 1 (highly novel)
        """
        if not self.recent_scenarios:
            return 1.0  # First scenario is always novel

        new_features = self._extract_features(scenario_dto)

        # Calculate similarity to each recent scenario
        total_similarity = 0.0

        for recent in self.recent_scenarios:
            similarity = 0.0

            # Same company type: high penalty
            if new_features["company_type"] == recent["company_type"]:
                similarity += 0.25

            # Same user segment: moderate penalty
            if new_features["user_segment"] == recent["user_segment"]:
                similarity += 0.15

            # Same KPI: moderate penalty
            if new_features["primary_kpi"] == recent["primary_kpi"]:
                similarity += 0.10

            # Same traffic tier: low penalty
            if new_features["traffic_tier"] == recent["traffic_tier"]:
                similarity += 0.10

            # Same baseline tier: low penalty
            if new_features["baseline_tier"] == recent["baseline_tier"]:
                similarity += 0.10

            # Same effect tier: low penalty
            if new_features["effect_tier"] == recent["effect_tier"]:
                similarity += 0.10

            # Similar alpha (same band)
            if new_features["alpha"] == recent["alpha"]:
                similarity += 0.10

            # Similar power (same band)
            if new_features["power"] == recent["power"]:
                similarity += 0.10

            total_similarity += similarity

        # Average similarity across recent scenarios
        avg_similarity = total_similarity / len(self.recent_scenarios)

        # Weight more recent scenarios higher
        recency_weighted_similarity = 0.0
        for i, recent in enumerate(self.recent_scenarios):
            recency_weight = (i + 1) / len(self.recent_scenarios)  # More recent = higher weight

            similarity = 0.0
            if new_features["company_type"] == recent["company_type"]:
                similarity += 0.25
            if new_features["user_segment"] == recent["user_segment"]:
                similarity += 0.15
            if new_features["primary_kpi"] == recent["primary_kpi"]:
                similarity += 0.10

            recency_weighted_similarity += similarity * recency_weight

        # Combine average and recency-weighted similarity
        combined_similarity = (avg_similarity + recency_weighted_similarity) / 2

        # Convert to novelty score
        novelty = max(0.0, 1.0 - combined_similarity)

        return novelty

    def record_scenario(self, scenario_dto: ScenarioResponseDTO) -> None:
        """
        Record a scenario in the history for future novelty comparisons.

        Args:
            scenario_dto: The scenario to record
        """
        features = self._extract_features(scenario_dto)
        self.recent_scenarios.append(features)

        # Maintain history size
        if len(self.recent_scenarios) > self.history_size:
            self.recent_scenarios = self.recent_scenarios[-self.history_size:]

    def get_diversity_suggestions(self, scenario_dto: ScenarioResponseDTO) -> List[str]:
        """
        Get suggestions for making a scenario more novel.

        Args:
            scenario_dto: The scenario to analyze

        Returns:
            List of suggestions for increasing diversity
        """
        if not self.recent_scenarios:
            return []

        new_features = self._extract_features(scenario_dto)
        suggestions = []

        # Count occurrences of each feature in history
        company_counts = {}
        segment_counts = {}
        kpi_counts = {}
        traffic_counts = {}

        for recent in self.recent_scenarios:
            company_counts[recent["company_type"]] = company_counts.get(recent["company_type"], 0) + 1
            segment_counts[recent["user_segment"]] = segment_counts.get(recent["user_segment"], 0) + 1
            kpi_counts[recent["primary_kpi"]] = kpi_counts.get(recent["primary_kpi"], 0) + 1
            traffic_counts[recent["traffic_tier"]] = traffic_counts.get(recent["traffic_tier"], 0) + 1

        # Suggest alternatives for overused features
        if company_counts.get(new_features["company_type"], 0) >= 3:
            underused = [ct for ct in ["Telehealth", "EdTech", "PropTech", "Gaming", "Logistics"]
                        if company_counts.get(ct, 0) == 0]
            if underused:
                suggestions.append(f"Company type '{new_features['company_type']}' used frequently. Consider: {', '.join(underused[:3])}")

        if segment_counts.get(new_features["user_segment"], 0) >= 3:
            underused = [seg for seg in ["power users (top 10%)", "churned users (win-back)", "enterprise accounts"]
                        if segment_counts.get(seg, 0) == 0]
            if underused:
                suggestions.append(f"User segment used frequently. Consider: {', '.join(underused[:3])}")

        if traffic_counts.get(new_features["traffic_tier"], 0) >= 4:
            underused = [tier for tier in ["early_stage", "enterprise"]
                        if traffic_counts.get(tier, 0) <= 1]
            if underused:
                suggestions.append(f"Traffic tier '{new_features['traffic_tier']}' common. Consider: {', '.join(underused)}")

        return suggestions

    def get_history_summary(self) -> Dict:
        """
        Get a summary of the scenario history for diversity analysis.

        Returns:
            Dictionary with counts of each feature value
        """
        if not self.recent_scenarios:
            return {"total": 0}

        summary = {
            "total": len(self.recent_scenarios),
            "company_types": {},
            "user_segments": {},
            "kpis": {},
            "traffic_tiers": {},
            "effect_tiers": {}
        }

        # Map feature keys to summary keys
        key_mapping = {
            "company_type": "company_types",
            "user_segment": "user_segments",
            "primary_kpi": "kpis",
            "traffic_tier": "traffic_tiers",
            "effect_tier": "effect_tiers"
        }

        for scenario in self.recent_scenarios:
            for feature_key, summary_key in key_mapping.items():
                value = scenario.get(feature_key, "unknown")
                summary[summary_key][value] = summary[summary_key].get(value, 0) + 1

        return summary

    def clear_history(self) -> None:
        """Clear the scenario history."""
        self.recent_scenarios = []


# Global novelty scorer instance for use across the application
_novelty_scorer: Optional[NoveltyScorer] = None


def get_novelty_scorer(history_size: int = 20) -> NoveltyScorer:
    """
    Get the global novelty scorer instance (singleton pattern).

    Args:
        history_size: Number of recent scenarios to track

    Returns:
        The global NoveltyScorer instance
    """
    global _novelty_scorer
    if _novelty_scorer is None:
        _novelty_scorer = NoveltyScorer(history_size=history_size)
    return _novelty_scorer


def score_scenario_novelty(scenario_dto: ScenarioResponseDTO) -> Tuple[float, List[str]]:
    """
    Convenience function to score novelty and get suggestions.

    Args:
        scenario_dto: The scenario to score

    Returns:
        Tuple of (novelty_score, list_of_suggestions)
    """
    scorer = get_novelty_scorer()
    novelty = scorer.score_novelty(scenario_dto)
    suggestions = scorer.get_diversity_suggestions(scenario_dto)
    return novelty, suggestions


def record_generated_scenario(scenario_dto: ScenarioResponseDTO) -> None:
    """
    Record a generated scenario in the novelty history.

    Call this after successfully generating a scenario to update the history.

    Args:
        scenario_dto: The scenario to record
    """
    scorer = get_novelty_scorer()
    scorer.record_scenario(scenario_dto)
