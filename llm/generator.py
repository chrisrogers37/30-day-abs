"""
Scenario generator with retry logic and fallback scenarios.

This module orchestrates the complete LLM scenario generation process,
including client calls, parsing, validation, and retry logic.
"""

import asyncio
import logging
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from .client import LLMClient, LLMConfig, LLMProvider, LLMError
from .parser import LLMOutputParser, ParsingResult
from .guardrails import LLMGuardrails, ValidationResult

from schemas.scenario import ScenarioResponseDTO, ScenarioRequestDTO
from schemas.shared import CompanyType, UserSegment

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class GenerationResult:
    """Result of scenario generation."""
    success: bool
    scenario_dto: Optional[ScenarioResponseDTO] = None
    attempts: int = 0
    total_time: float = 0.0
    errors: List[str] = None
    warnings: List[str] = None
    quality_score: float = 0.0
    used_fallback: bool = False
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class ScenarioGenerationError(Exception):
    """Exception raised when scenario generation fails."""
    pass


class LLMScenarioGenerator:
    """Main scenario generator with comprehensive retry logic and validation."""
    
    def __init__(self, client: LLMClient):
        self.client = client
        self.parser = LLMOutputParser()
        self.guardrails = LLMGuardrails()
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """Load the scenario generation prompt template."""
        prompt_path = Path(__file__).parent / "prompts" / "scenario_prompt.txt"
        try:
            return prompt_path.read_text(encoding='utf-8')
        except FileNotFoundError:
            logger.warning("Prompt template not found, using default")
            return self._get_default_prompt()
    
    def _get_default_prompt(self) -> str:
        """Get default prompt if template file is not found."""
        return """Generate a realistic AB test scenario with the following JSON structure:

{
  "scenario": {
    "title": "Brief, descriptive title",
    "narrative": "Detailed scenario description",
    "company_type": "SaaS|E-commerce|Media|Fintech|Marketplace|Gaming",
    "user_segment": "new_users|returning_users|premium_users|all_users",
    "primary_kpi": "conversion_rate|click_through_rate|revenue_per_user|engagement_rate",
    "secondary_kpis": ["list", "of", "secondary", "metrics"],
    "unit": "visitor|session|user|impression",
    "assumptions": ["key assumption 1", "key assumption 2"]
  },
  "design_params": {
    "baseline_conversion_rate": 0.025,
    "mde_absolute": 0.005,
    "target_lift_pct": 0.20,
    "alpha": 0.01,
    "power": 0.95,
    "allocation": {"control": 0.5, "treatment": 0.5},
    "expected_daily_traffic": 3200
  },
  "llm_expected": {
    "simulation_hints": {
      "treatment_conversion_rate": 0.030,
      "control_conversion_rate": 0.025
    },
    "narrative_conclusion": "Expected conclusion",
    "business_interpretation": "Business impact",
    "risk_assessment": "Risk assessment",
    "next_steps": "Recommended next steps",
    "notes": "These are suggestions only; use your simulator for ground truth."
  }
}

Return ONLY valid JSON."""
    
    async def generate_scenario(
        self,
        request: Optional[ScenarioRequestDTO] = None,
        max_attempts: int = 3,
        min_quality_score: float = 0.7
    ) -> GenerationResult:
        """
        Generate a scenario with retry logic and validation.
        
        Args:
            request: Optional scenario generation request
            max_attempts: Maximum number of generation attempts
            min_quality_score: Minimum quality score to accept
            
        Returns:
            GenerationResult with generated scenario or error details
        """
        start_time = time.time()
        result = GenerationResult(success=False)
        
        try:
            # Generate prompt based on request
            prompt = self._create_prompt(request)
            logger.info(f"Starting scenario generation - Max attempts: {max_attempts}, Min quality: {min_quality_score}")
            logger.debug(f"Generated prompt length: {len(prompt)} characters")
            
            # Attempt generation with retries
            for attempt in range(max_attempts):
                result.attempts = attempt + 1
                logger.info(f"Generation attempt {attempt + 1}/{max_attempts}")
                
                try:
                    # Call LLM
                    llm_response = await self.client.generate_scenario(prompt)
                    logger.info(f"LLM response received - Length: {len(llm_response.content)} chars, Time: {llm_response.response_time:.2f}s")
                    
                    # Parse response
                    parsing_result = self.parser.parse_llm_response(llm_response.content)
                    
                    if not parsing_result.success:
                        result.errors.extend(parsing_result.errors)
                        logger.warning(f"Parsing failed on attempt {attempt + 1}: {parsing_result.errors}")
                        continue
                    
                    logger.info("Parsing successful, validating with guardrails...")
                    
                    # Validate with guardrails
                    validation_result = self.guardrails.validate_scenario(parsing_result.scenario_dto)
                    
                    if not validation_result.is_valid:
                        result.errors.extend(validation_result.errors)
                        logger.warning(f"Validation failed on attempt {attempt + 1}: {validation_result.errors}")
                        continue
                    
                    # Check quality score
                    quality_score = self.guardrails.get_quality_score(parsing_result.scenario_dto)
                    result.quality_score = quality_score
                    logger.info(f"Quality score: {quality_score:.2f} (threshold: {min_quality_score})")
                    
                    if quality_score < min_quality_score:
                        result.warnings.append(f"Quality score {quality_score:.2f} below threshold {min_quality_score}")
                        if attempt < max_attempts - 1:
                            logger.warning("Quality below threshold, retrying...")
                            continue
                    
                    # Success!
                    result.success = True
                    result.scenario_dto = parsing_result.scenario_dto
                    result.warnings.extend(validation_result.warnings)
                    result.total_time = time.time() - start_time
                    
                    logger.info(f"✅ Scenario generated successfully in {result.attempts} attempts, quality: {quality_score:.2f}")
                    logger.info(f"Scenario title: {parsing_result.scenario_dto.scenario.title}")
                    logger.info(f"Company type: {parsing_result.scenario_dto.scenario.company_type}")
                    return result
                    
                except LLMError as e:
                    result.errors.append(f"LLM error on attempt {attempt + 1}: {str(e)}")
                    logger.warning(f"LLM error on attempt {attempt + 1}: {e}")
                    
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(1.0 * (attempt + 1))  # Exponential backoff
                        continue
                
                except Exception as e:
                    result.errors.append(f"Unexpected error on attempt {attempt + 1}: {str(e)}")
                    logger.error(f"Unexpected error on attempt {attempt + 1}: {e}")
                    
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(1.0 * (attempt + 1))
                        continue
            
            # All attempts failed, try fallback
            logger.warning("All generation attempts failed, using fallback scenario")
            result.used_fallback = True
            result.scenario_dto = self.parser.create_fallback_scenario()
            result.success = True
            result.total_time = time.time() - start_time
            
        except Exception as e:
            logger.error(f"Critical error in scenario generation: {e}")
            result.errors.append(f"Critical error: {str(e)}")
            result.total_time = time.time() - start_time
        
        return result
    
    def _create_prompt(self, request: Optional[ScenarioRequestDTO]) -> str:
        """Create generation prompt based on request."""
        if request is None:
            return self.prompt_template
        
        # Customize prompt based on request
        prompt = self.prompt_template
        
        if request.company_type:
            prompt += f"\n\nFocus on {request.company_type.value} company type."
        
        if request.user_segment:
            prompt += f"\n\nTarget user segment: {request.user_segment.value}."
        
        if request.complexity_level:
            complexity_hints = {
                "low": "Keep the scenario simple and straightforward.",
                "medium": "Create a moderately complex scenario with realistic business context.",
                "high": "Create a complex scenario with multiple considerations and edge cases."
            }
            prompt += f"\n\nComplexity level: {complexity_hints.get(request.complexity_level, '')}"
        
        if request.previous_experiments:
            prompt += f"\n\nPrevious experiment context: {request.previous_experiments}"
        
        return prompt
    
    async def generate_multiple_scenarios(
        self,
        count: int = 3,
        request: Optional[ScenarioRequestDTO] = None,
        **kwargs
    ) -> List[GenerationResult]:
        """
        Generate multiple scenarios in parallel.
        
        Args:
            count: Number of scenarios to generate
            request: Optional scenario generation request
            **kwargs: Additional parameters for generation
            
        Returns:
            List of GenerationResult objects
        """
        tasks = [
            self.generate_scenario(request, **kwargs)
            for _ in range(count)
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Handle exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                error_result = GenerationResult(
                    success=False,
                    errors=[f"Generation failed: {str(result)}"],
                    attempts=1
                )
                processed_results.append(error_result)
            else:
                processed_results.append(result)
        
        return processed_results
    
    def get_generation_stats(self) -> Dict[str, any]:
        """Get statistics about scenario generation."""
        return {
            "client_config": self.client.get_usage_stats(),
            "prompt_length": len(self.prompt_template),
            "guardrails_enabled": True,
            "parser_enabled": True
        }


def create_scenario_generator(
    provider: str = "mock",
    api_key: Optional[str] = None,
    model: str = "gpt-4",
    **kwargs
) -> LLMScenarioGenerator:
    """
    Factory function to create scenario generator.
    
    Args:
        provider: LLM provider ("openai", "anthropic", "mock")
        api_key: API key for the provider
        model: Model name to use
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured LLMScenarioGenerator instance
    """
    from .client import create_llm_client
    
    client = create_llm_client(provider, api_key, model, **kwargs)
    return LLMScenarioGenerator(client)


# Example usage and testing
async def test_scenario_generation():
    """Test scenario generation functionality."""
    generator = create_scenario_generator(provider="mock")
    
    # Test basic generation
    result = await generator.generate_scenario()
    
    if result.success:
        print(f"✅ Scenario generated successfully!")
        print(f"   Title: {result.scenario_dto.scenario.title}")
        print(f"   Company: {result.scenario_dto.scenario.company_type}")
        print(f"   Quality Score: {result.quality_score:.2f}")
        print(f"   Attempts: {result.attempts}")
        print(f"   Time: {result.total_time:.2f}s")
    else:
        print(f"❌ Scenario generation failed: {result.errors}")
    
    return result


if __name__ == "__main__":
    # Run test
    asyncio.run(test_scenario_generation())
