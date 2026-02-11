"""
Real API integration tests.

These tests are marked to skip in CI unless API keys are provided.
They test the complete end-to-end flow with real LLM API calls.
"""

import pytest
import os

# Helper to check if API key is available
HAS_API_KEY = os.getenv("OPENAI_API_KEY") is not None
SKIP_REASON = "Requires OPENAI_API_KEY environment variable"


@pytest.mark.skipif(not HAS_API_KEY, reason=SKIP_REASON)
class TestRealOpenAIIntegration:
    """Test real OpenAI API integration for complete E2E workflow."""

    @pytest.mark.requires_api
    @pytest.mark.asyncio
    @pytest.mark.timeout(120)  # 2 minute timeout for API calls
    async def test_complete_e2e_pipeline_with_real_llm(self):
        """
        Test complete E2E pipeline: LLM scenario generation -> design -> simulate -> analyze.

        This test:
        1. Generates a scenario using the real OpenAI API
        2. Converts to core domain types
        3. Calculates sample size
        4. Simulates trial data
        5. Analyzes results
        6. Validates all outputs end-to-end
        """
        from llm.integration import create_llm_integration

        # Create integration with real OpenAI API
        api_key = os.getenv("OPENAI_API_KEY")
        integration = create_llm_integration(
            provider="openai",
            api_key=api_key,
            model="gpt-4"
        )

        # Run the complete pipeline
        result = await integration.run_complete_pipeline(
            max_attempts=3,
            min_quality_score=0.6  # Lower threshold for faster tests
        )

        # Validate pipeline success
        assert result.success, f"Pipeline failed with errors: {result.errors}"

        # Validate scenario was generated
        assert result.scenario_dto is not None, "Scenario DTO should not be None"
        scenario = result.scenario_dto.scenario
        assert scenario.title, "Scenario should have a title"
        assert scenario.narrative, "Scenario should have a narrative"
        assert scenario.company_type, "Scenario should have a company type"
        assert scenario.primary_kpi, "Scenario should have a primary KPI"

        # Validate design params were converted
        assert result.design_params is not None, "Design params should not be None"
        design = result.design_params
        assert 0 < design.baseline_conversion_rate < 1, "Baseline rate should be between 0 and 1"
        assert design.alpha > 0, "Alpha should be positive"
        assert design.power > 0, "Power should be positive"
        assert design.expected_daily_traffic > 0, "Daily traffic should be positive"

        # Validate sample size calculation
        assert result.sample_size is not None, "Sample size should not be None"
        assert result.sample_size["per_arm"] > 0, "Sample size per arm should be positive"
        assert result.sample_size["total"] > 0, "Total sample size should be positive"

        # Validate simulation results
        assert result.simulation_result is not None, "Simulation result should not be None"
        sim = result.simulation_result
        assert sim.control_n > 0, "Control sample size should be positive"
        assert sim.treatment_n > 0, "Treatment sample size should be positive"
        assert 0 <= sim.control_conversions <= sim.control_n, "Control conversions should be valid"
        assert 0 <= sim.treatment_conversions <= sim.treatment_n, "Treatment conversions should be valid"

        # Validate analysis results
        assert result.analysis_result is not None, "Analysis result should not be None"
        analysis = result.analysis_result
        assert 0 <= analysis.p_value <= 1, "P-value should be between 0 and 1"
        assert len(analysis.confidence_interval) == 2, "CI should have two bounds"
        assert analysis.confidence_interval[0] <= analysis.confidence_interval[1], "CI bounds should be ordered"

        # Validate comparison with LLM expectations
        assert result.comparison is not None, "Comparison should not be None"
        assert "conversion_rates" in result.comparison
        assert "statistical_results" in result.comparison
        assert "llm_expectations" in result.comparison

    @pytest.mark.requires_api
    @pytest.mark.asyncio
    @pytest.mark.timeout(60)
    async def test_llm_scenario_generation_only(self):
        """
        Test just the LLM scenario generation component.

        This is a lighter test that only tests LLM generation,
        useful for verifying API connectivity without full pipeline.
        """
        from llm.generator import create_scenario_generator

        api_key = os.getenv("OPENAI_API_KEY")
        generator = create_scenario_generator(
            provider="openai",
            api_key=api_key,
            model="gpt-4"
        )

        result = await generator.generate_scenario(
            max_attempts=2,
            min_quality_score=0.5
        )

        assert result.success, f"Generation failed: {result.errors}"
        assert result.scenario_dto is not None
        assert result.quality_score >= 0.5
        assert result.attempts <= 2
        assert result.total_time > 0

        # Validate scenario structure
        scenario = result.scenario_dto.scenario
        assert scenario.title
        assert scenario.company_type
        assert scenario.primary_kpi

        # Validate design params structure
        design = result.scenario_dto.design_params
        assert design.baseline_conversion_rate > 0
        assert design.alpha in [0.01, 0.05, 0.10]  # Common alpha values
        assert design.power in [0.70, 0.80, 0.85, 0.90, 0.95]  # Common power values

    @pytest.mark.requires_api
    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_llm_client_connectivity(self):
        """
        Test basic LLM client connectivity.

        This is the simplest test - just verifies we can connect
        to the OpenAI API and get a response.
        """
        from llm.client import create_llm_client

        api_key = os.getenv("OPENAI_API_KEY")
        client = create_llm_client(
            provider="openai",
            api_key=api_key,
            model="gpt-4"
        )

        # Simple completion test
        response = await client.generate_completion(
            messages=[{"role": "user", "content": "Say 'hello' and nothing else."}],
            max_tokens=10
        )

        assert response.content is not None
        assert len(response.content) > 0
        assert response.model is not None
        assert response.response_time > 0


@pytest.mark.skipif(not HAS_API_KEY, reason=SKIP_REASON)
class TestRealAPIErrorHandling:
    """Test error handling with real API."""

    @pytest.mark.requires_api
    @pytest.mark.asyncio
    @pytest.mark.timeout(30)
    async def test_invalid_api_key_handling(self):
        """Test that invalid API key produces appropriate error."""
        from llm.client import create_llm_client, LLMError

        # Create client with invalid key
        client = create_llm_client(
            provider="openai",
            api_key="invalid-key-12345",
            model="gpt-4",
            max_retries=0  # Don't retry with invalid key
        )

        with pytest.raises(LLMError):
            await client.generate_completion(
                messages=[{"role": "user", "content": "test"}],
                max_tokens=10
            )


class TestMockFallback:
    """Test that mock fallback works when no API key is available."""

    @pytest.mark.asyncio
    async def test_mock_pipeline_works_without_api_key(self):
        """
        Test that the mock pipeline works without an API key.

        This test always runs and verifies the mock provider works
        correctly as a fallback for development and CI.
        """
        from llm.integration import create_llm_integration

        # Use mock provider - no API key needed
        integration = create_llm_integration(provider="mock")

        result = await integration.run_complete_pipeline()

        assert result.success
        assert result.scenario_dto is not None
        assert result.design_params is not None
        assert result.sample_size is not None
        assert result.simulation_result is not None
        assert result.analysis_result is not None


# Allow running tests directly
if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
