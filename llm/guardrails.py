"""
Guardrails for LLM output validation and regeneration.

This module provides comprehensive sanity checks, clamping logic, and
regeneration hints for LLM-generated scenarios.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from schemas.scenario import ScenarioResponseDTO
from schemas.design import DesignParamsDTO
from schemas.shared import CompanyType, UserSegment

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of guardrail validation."""
    is_valid: bool
    quality_score: float = 0.0
    errors: List[str] = None
    warnings: List[str] = None
    suggestions: List[str] = None
    clamped_values: Dict[str, Tuple[float, float]] = None  # field_name: (original, clamped)
    
    def __post_init__(self):
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
    """Comprehensive guardrails for LLM output validation."""
    
    def __init__(self):
        # Parameter bounds
        self.bounds = {
            'baseline_conversion_rate': (0.001, 0.5),
            'mde_absolute': (0.001, 0.1),  # 0.1% to 10% percentage points
            'target_lift_pct': (-0.5, 0.5),
            'alpha': (0.01, 0.1),
            'power': (0.7, 0.95),
            'expected_daily_traffic': (500, 5000),
            'treatment_conversion_rate': (0.001, 0.5),
            'control_conversion_rate': (0.001, 0.5)
        }
        
        # Business context validation rules
        self.business_rules = {
            'company_type_scenarios': {
                CompanyType.ECOMMERCE: ['checkout', 'cart', 'payment', 'shipping', 'product'],
                CompanyType.SAAS: ['onboarding', 'feature', 'pricing', 'trial', 'engagement'],
                CompanyType.MEDIA: ['article', 'video', 'subscription', 'content', 'ad'],
                CompanyType.FINTECH: ['account', 'payment', 'security', 'investment', 'loan'],
                CompanyType.MARKETPLACE: ['listing', 'search', 'seller', 'buyer', 'transaction'],
                CompanyType.GAMING: ['level', 'purchase', 'social', 'retention', 'monetization']
            },
            'user_segment_contexts': {
                UserSegment.NEW_USERS: ['onboarding', 'first-time', 'trial', 'signup'],
                UserSegment.RETURNING_USERS: ['engagement', 'retention', 'feature', 'upgrade'],
                UserSegment.PREMIUM_USERS: ['advanced', 'premium', 'enterprise', 'pro'],
                UserSegment.ALL_USERS: ['general', 'overall', 'site-wide', 'universal']
            }
        }
    
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
        """Validate business context consistency."""
        scenario = scenario_response_dto.scenario
        company_type = scenario.company_type
        user_segment = scenario.user_segment
        title = scenario.title.lower()
        narrative = scenario.narrative.lower()
        
        # Check company type consistency
        expected_keywords = self.business_rules['company_type_scenarios'].get(company_type, [])
        if expected_keywords:
            found_keywords = [kw for kw in expected_keywords if kw in title or kw in narrative]
            if not found_keywords:
                result.warnings.append(
                    f"Scenario doesn't seem to match company type {company_type.value}. "
                    f"Expected keywords: {expected_keywords}"
                )
        
        # Check user segment consistency
        segment_keywords = self.business_rules['user_segment_contexts'].get(user_segment, [])
        if segment_keywords:
            found_segment_keywords = [kw for kw in segment_keywords if kw in title or kw in narrative]
            if not found_segment_keywords:
                result.warnings.append(
                    f"Scenario doesn't seem to match user segment {user_segment.value}. "
                    f"Expected keywords: {segment_keywords}"
                )
        
        # Check KPI consistency
        primary_kpi = scenario.primary_kpi.lower()
        if 'conversion' in primary_kpi and 'rate' not in primary_kpi:
            result.warnings.append("Primary KPI should specify 'conversion_rate' for clarity")
        
        # Check unit consistency
        unit = scenario.unit.lower()
        if 'conversion' in primary_kpi and unit not in ['visitor', 'user', 'session']:
            result.warnings.append(
                f"Unit '{unit}' may not be appropriate for conversion rate measurement"
            )
    
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
        """Validate realism of the scenario."""
        design_params = scenario_response_dto.design_params
        scenario = scenario_response_dto.scenario
        
        # Check for unrealistic conversion rates
        baseline = design_params.baseline_conversion_rate
        if baseline > 0.2:  # 20%
            result.warnings.append(
                f"Baseline conversion rate {baseline:.1%} seems high for most scenarios"
            )
        elif baseline < 0.005:  # 0.5%
            result.warnings.append(
                f"Baseline conversion rate {baseline:.1%} seems low for most scenarios"
            )
        
        # Check for unrealistic target lifts
        target_lift = design_params.target_lift_pct
        if abs(target_lift) > 1.0:  # 100%
            result.warnings.append(
                f"Target lift {target_lift:.1%} seems ambitious for most scenarios"
            )
        
        # Check for unrealistic traffic
        traffic = design_params.expected_daily_traffic
        if traffic > 1000000:  # 1M daily
            result.warnings.append(
                f"Daily traffic {traffic:,} seems very high for most scenarios"
            )
        elif traffic < 5000:  # 5K daily
            result.warnings.append(
                f"Daily traffic {traffic:,} may be too low for meaningful AB testing"
            )
        
        # Check for unrealistic power
        power = design_params.power
        if power > 0.9:  # 90%
            result.warnings.append(
                f"Power {power:.1%} is very high and may require large sample sizes"
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
        
        Args:
            scenario_response_dto: Scenario to score
            
        Returns:
            Quality score between 0 and 1
        """
        score = 1.0
        
        # Calculate quality without calling validate_scenario to avoid recursion
        design_params = scenario_response_dto.design_params
        
        # Deduct for unrealistic values
        if design_params.baseline_conversion_rate > 0.2 or design_params.baseline_conversion_rate < 0.005:
            score -= 0.1
        
        if abs(design_params.target_lift_pct) > 1.0:
            score -= 0.1
        
        if design_params.expected_daily_traffic > 1000000 or design_params.expected_daily_traffic < 5000:
            score -= 0.1
        
        # Deduct for inconsistency
        baseline = design_params.baseline_conversion_rate
        control_rate = scenario_response_dto.llm_expected.simulation_hints.control_conversion_rate
        if abs(baseline - control_rate) > 0.001:
            score -= 0.1
        
        return max(0.0, min(1.0, score))
