"""
Integration layer between LLM outputs and core simulation engine.

This module converts LLM-generated scenarios into core domain types
and orchestrates the complete simulation pipeline.
"""

import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

from .generator import LLMScenarioGenerator, GenerationResult
from .parser import LLMOutputParser, ParsingResult

from core.types import DesignParams, Allocation, SimResult, AnalysisResult
from core.design import compute_sample_size
from core.simulate import simulate_trial
from core.analyze import analyze_results

from schemas.scenario import ScenarioResponseDTO
from schemas.design import DesignParamsDTO
from schemas.shared import AllocationDTO

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SimulationPipelineResult:
    """Result of the complete simulation pipeline."""
    success: bool
    scenario_dto: Optional[ScenarioResponseDTO] = None
    design_params: Optional[DesignParams] = None
    sample_size: Optional[Dict] = None
    simulation_result: Optional[SimResult] = None
    analysis_result: Optional[AnalysisResult] = None
    comparison: Optional[Dict] = None
    errors: List[str] = None
    warnings: List[str] = None
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class LLMIntegrationError(Exception):
    """Exception raised when LLM integration fails."""
    pass


class LLMIntegration:
    """Integration layer between LLM outputs and core simulation engine."""
    
    def __init__(self, generator: LLMScenarioGenerator):
        self.generator = generator
        self.parser = LLMOutputParser()
    
    async def run_complete_pipeline(
        self,
        request: Optional[Dict] = None,
        max_attempts: int = 3,
        min_quality_score: float = 0.7
    ) -> SimulationPipelineResult:
        """
        Run the complete pipeline: LLM generation → Simulation → Analysis.
        
        Args:
            request: Optional scenario generation request
            max_attempts: Maximum LLM generation attempts
            min_quality_score: Minimum quality score for LLM output
            
        Returns:
            SimulationPipelineResult with complete pipeline results
        """
        result = SimulationPipelineResult(success=False)
        
        try:
            logger.info("🚀 Starting complete simulation pipeline...")
            
            # Step 1: Generate scenario with LLM
            logger.info("Step 1: Generating scenario with LLM...")
            generation_result = await self.generator.generate_scenario(
                request, max_attempts, min_quality_score
            )
            
            if not generation_result.success:
                result.errors.extend(generation_result.errors)
                logger.error(f"LLM generation failed: {generation_result.errors}")
                return result
            
            result.scenario_dto = generation_result.scenario_dto
            logger.info(f"✅ Scenario generated: {generation_result.scenario_dto.scenario.title}")
            
            # Step 2: Convert to core types
            logger.info("Step 2: Converting to core domain types...")
            design_params = self._convert_to_core_types(generation_result.scenario_dto)
            result.design_params = design_params
            logger.info("✅ Converted to core types")
            
            # Step 3: Calculate sample size
            logger.info("Step 3: Calculating sample size...")
            sample_size_result = compute_sample_size(design_params)
            result.sample_size = {
                "per_arm": sample_size_result.per_arm,
                "total": sample_size_result.total,
                "days_required": sample_size_result.days_required,
                "power_achieved": sample_size_result.power_achieved
            }
            logger.info(f"✅ Sample size calculated: {sample_size_result.total} total users")
            
            # Step 4: Simulate data
            logger.info("Step 4: Simulating trial data...")
            simulation_result = simulate_trial(design_params, sample_size_result)
            result.simulation_result = simulation_result
            logger.info(f"✅ Simulation completed: {simulation_result.control_conversions}/{simulation_result.control_n} vs {simulation_result.treatment_conversions}/{simulation_result.treatment_n}")
            
            # Step 5: Analyze results
            logger.info("Step 5: Analyzing results...")
            analysis_result = analyze_results(
                control_n=simulation_result.control_n,
                control_conversions=simulation_result.control_conversions,
                treatment_n=simulation_result.treatment_n,
                treatment_conversions=simulation_result.treatment_conversions,
                test_type="two_proportion_z",
                test_direction="two_tailed",
                alpha=design_params.alpha
            )
            result.analysis_result = analysis_result
            logger.info(f"✅ Analysis completed: p-value = {analysis_result.p_value:.4f}")
            
            # Step 6: Compare with LLM expectations
            logger.info("Step 6: Comparing with LLM expectations...")
            comparison = self._compare_with_llm_expectations(
                generation_result.scenario_dto,
                analysis_result,
                simulation_result
            )
            result.comparison = comparison
            logger.info("✅ Comparison completed")
            
            result.success = True
            result.warnings.extend(generation_result.warnings)
            
            logger.info("🎉 Complete pipeline finished successfully!")
            return result
            
        except Exception as e:
            logger.error(f"Pipeline failed: {e}")
            result.errors.append(f"Pipeline error: {str(e)}")
            return result
    
    def _convert_to_core_types(self, scenario_dto: ScenarioResponseDTO) -> DesignParams:
        """Convert LLM DTOs to core domain types."""
        design_dto = scenario_dto.design_params
        
        # Convert allocation
        allocation = Allocation(
            control=design_dto.allocation.control,
            treatment=design_dto.allocation.treatment
        )
        
        # Create core DesignParams
        design_params = DesignParams(
            baseline_conversion_rate=design_dto.baseline_conversion_rate,
            target_lift_pct=design_dto.target_lift_pct,
            alpha=design_dto.alpha,
            power=design_dto.power,
            allocation=allocation,
            expected_daily_traffic=design_dto.expected_daily_traffic
        )
        
        return design_params
    
    def _compare_with_llm_expectations(
        self,
        scenario_dto: ScenarioResponseDTO,
        analysis_result: AnalysisResult,
        simulation_result: SimResult
    ) -> Dict:
        """Compare actual results with LLM expectations."""
        llm_expected = scenario_dto.llm_expected
        simulation_hints = llm_expected.simulation_hints
        
        # Calculate actual conversion rates
        actual_control_rate = simulation_result.control_conversions / simulation_result.control_n
        actual_treatment_rate = simulation_result.treatment_conversions / simulation_result.treatment_n
        actual_lift = (actual_treatment_rate - actual_control_rate) / actual_control_rate
        
        # LLM expected rates
        expected_control_rate = simulation_hints.control_conversion_rate
        expected_treatment_rate = simulation_hints.treatment_conversion_rate
        expected_lift = (expected_treatment_rate - expected_control_rate) / expected_control_rate
        
        comparison = {
            "conversion_rates": {
                "actual": {
                    "control": actual_control_rate,
                    "treatment": actual_treatment_rate,
                    "lift": actual_lift
                },
                "expected": {
                    "control": expected_control_rate,
                    "treatment": expected_treatment_rate,
                    "lift": expected_lift
                },
                "differences": {
                    "control_diff": actual_control_rate - expected_control_rate,
                    "treatment_diff": actual_treatment_rate - expected_treatment_rate,
                    "lift_diff": actual_lift - expected_lift
                }
            },
            "statistical_results": {
                "p_value": analysis_result.p_value,
                "significant": analysis_result.p_value < scenario_dto.design_params.alpha,
                "confidence_interval": analysis_result.confidence_interval,
                "effect_size": analysis_result.effect_size
            },
            "llm_expectations": {
                "narrative_conclusion": llm_expected.narrative_conclusion,
                "business_interpretation": llm_expected.business_interpretation,
                "risk_assessment": llm_expected.risk_assessment,
                "next_steps": llm_expected.next_steps
            }
        }
        
        return comparison
    
    def get_pipeline_summary(self, result: SimulationPipelineResult) -> Dict:
        """Get a summary of the pipeline results."""
        if not result.success:
            return {"status": "failed", "errors": result.errors}
        
        summary = {
            "status": "success",
            "scenario": {
                "title": result.scenario_dto.scenario.title,
                "company_type": result.scenario_dto.scenario.company_type,
                "primary_kpi": result.scenario_dto.scenario.primary_kpi
            },
            "design": {
                "baseline_rate": result.design_params.baseline_conversion_rate,
                "target_lift": result.design_params.target_lift_pct,
                "alpha": result.design_params.alpha,
                "power": result.design_params.power,
                "daily_traffic": result.design_params.expected_daily_traffic
            },
            "sample_size": result.sample_size,
            "simulation": {
                "control_rate": result.simulation_result.control_conversions / result.simulation_result.control_n,
                "treatment_rate": result.simulation_result.treatment_conversions / result.simulation_result.treatment_n,
                "actual_lift": (result.simulation_result.treatment_conversions / result.simulation_result.treatment_n - 
                              result.simulation_result.control_conversions / result.simulation_result.control_n) / 
                              (result.simulation_result.control_conversions / result.simulation_result.control_n)
            },
            "analysis": {
                "p_value": result.analysis_result.p_value,
                "significant": result.analysis_result.p_value < result.design_params.alpha,
                "confidence_interval": result.analysis_result.confidence_interval
            }
        }
        
        if result.comparison:
            summary["comparison"] = {
                "rate_accuracy": {
                    "control_diff": result.comparison["conversion_rates"]["differences"]["control_diff"],
                    "treatment_diff": result.comparison["conversion_rates"]["differences"]["treatment_diff"],
                    "lift_diff": result.comparison["conversion_rates"]["differences"]["lift_diff"]
                }
            }
        
        return summary


def create_llm_integration(
    provider: str = "mock",
    api_key: Optional[str] = None,
    model: str = "gpt-4",
    **kwargs
) -> LLMIntegration:
    """
    Factory function to create LLM integration.
    
    Args:
        provider: LLM provider ("openai", "anthropic", "mock")
        api_key: API key for the provider
        model: Model name to use
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured LLMIntegration instance
    """
    from .generator import create_scenario_generator
    
    generator = create_scenario_generator(provider, api_key, model, **kwargs)
    return LLMIntegration(generator)
