"""
Comprehensive tests for llm.integration module - LLM to Simulation Pipeline.

These tests exercise the LLMIntegration class with mocked dependencies to achieve
proper test coverage of the integration layer.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass

from llm.integration import (
    LLMIntegration,
    SimulationPipelineResult,
    LLMIntegrationError,
)
from llm.generator import GenerationResult
from core.types import DesignParams, Allocation, SimResult, AnalysisResult


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_scenario_dto():
    """Create a mock scenario DTO."""
    scenario_dto = Mock()

    # Scenario attributes
    scenario_dto.scenario = Mock()
    scenario_dto.scenario.title = "Test Scenario"
    scenario_dto.scenario.company_type = "E-commerce"

    # Design params
    scenario_dto.design_params = Mock()
    scenario_dto.design_params.baseline_conversion_rate = 0.10
    scenario_dto.design_params.target_lift_pct = 0.20
    scenario_dto.design_params.alpha = 0.05
    scenario_dto.design_params.power = 0.80
    scenario_dto.design_params.expected_daily_traffic = 5000
    scenario_dto.design_params.allocation = Mock()
    scenario_dto.design_params.allocation.control = 0.5
    scenario_dto.design_params.allocation.treatment = 0.5

    # LLM expected values
    scenario_dto.llm_expected = Mock()
    scenario_dto.llm_expected.simulation_hints = Mock()
    scenario_dto.llm_expected.simulation_hints.control_conversion_rate = 0.10
    scenario_dto.llm_expected.simulation_hints.treatment_conversion_rate = 0.12
    scenario_dto.llm_expected.narrative_conclusion = "Test conclusion"
    scenario_dto.llm_expected.business_interpretation = "Test interpretation"
    scenario_dto.llm_expected.risk_assessment = "Low risk"
    scenario_dto.llm_expected.next_steps = "Monitor results"

    return scenario_dto


@pytest.fixture
def mock_generation_result(mock_scenario_dto):
    """Create a mock generation result."""
    result = Mock(spec=GenerationResult)
    result.success = True
    result.scenario_dto = mock_scenario_dto
    result.errors = []
    result.warnings = []
    return result


@pytest.fixture
def mock_sample_size_result():
    """Create a mock sample size result."""
    result = Mock()
    result.per_arm = 5000
    result.total = 10000
    result.days_required = 2
    result.power_achieved = 0.82
    return result


@pytest.fixture
def mock_sim_result():
    """Create a mock simulation result."""
    result = Mock(spec=SimResult)
    result.control_n = 5000
    result.treatment_n = 5000
    result.control_conversions = 500
    result.treatment_conversions = 600
    result.control_rate = 0.10
    result.treatment_rate = 0.12
    return result


@pytest.fixture
def mock_analysis_result():
    """Create a mock analysis result."""
    result = Mock(spec=AnalysisResult)
    result.p_value = 0.02
    result.confidence_interval = (0.01, 0.03)
    result.effect_size = 0.15
    result.significant = True
    return result


@pytest.fixture
def mock_generator(mock_generation_result):
    """Create a mock scenario generator."""
    generator = Mock()

    async def mock_generate(*args, **kwargs):
        return mock_generation_result

    generator.generate_scenario = mock_generate
    return generator


# ============================================================================
# SimulationPipelineResult Tests
# ============================================================================


class TestSimulationPipelineResult:
    """Test suite for SimulationPipelineResult dataclass."""

    @pytest.mark.unit
    def test_pipeline_result_defaults(self):
        """Test SimulationPipelineResult with default values."""
        result = SimulationPipelineResult(success=False)
        assert result.success is False
        assert result.scenario_dto is None
        assert result.design_params is None
        assert result.sample_size is None
        assert result.simulation_result is None
        assert result.analysis_result is None
        assert result.comparison is None
        assert result.errors == []
        assert result.warnings == []

    @pytest.mark.unit
    def test_pipeline_result_with_values(self):
        """Test SimulationPipelineResult with provided values."""
        mock_dto = Mock()
        mock_params = Mock()
        result = SimulationPipelineResult(
            success=True,
            scenario_dto=mock_dto,
            design_params=mock_params,
            sample_size={"total": 10000},
            errors=["error1"],
            warnings=["warning1"],
        )
        assert result.success is True
        assert result.scenario_dto == mock_dto
        assert result.design_params == mock_params
        assert result.sample_size == {"total": 10000}
        assert result.errors == ["error1"]
        assert result.warnings == ["warning1"]

    @pytest.mark.unit
    def test_pipeline_result_post_init_none_lists(self):
        """Test that None lists are initialized to empty lists."""
        result = SimulationPipelineResult(success=True, errors=None, warnings=None)
        assert result.errors == []
        assert result.warnings == []


# ============================================================================
# LLMIntegration Tests
# ============================================================================


class TestLLMIntegration:
    """Test suite for LLMIntegration class."""

    @pytest.mark.unit
    def test_integration_initialization(self, mock_generator):
        """Test integration initialization."""
        with patch("llm.integration.LLMOutputParser"):
            integration = LLMIntegration(mock_generator)

            assert integration.generator == mock_generator
            assert integration.parser is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_complete_pipeline_success(
        self,
        mock_generator,
        mock_sample_size_result,
        mock_sim_result,
        mock_analysis_result,
    ):
        """Test successful pipeline execution."""
        with patch("llm.integration.LLMOutputParser"), patch(
            "llm.integration.compute_sample_size", return_value=mock_sample_size_result
        ), patch(
            "llm.integration.simulate_trial", return_value=mock_sim_result
        ), patch(
            "llm.integration.analyze_results", return_value=mock_analysis_result
        ):
            integration = LLMIntegration(mock_generator)
            result = await integration.run_complete_pipeline()

            assert result.success is True
            assert result.scenario_dto is not None
            assert result.design_params is not None
            assert result.sample_size is not None
            assert result.simulation_result is not None
            assert result.analysis_result is not None
            assert result.comparison is not None

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_complete_pipeline_generation_failure(self):
        """Test pipeline when LLM generation fails."""
        mock_generator = Mock()
        failed_result = Mock()
        failed_result.success = False
        failed_result.errors = ["LLM generation failed"]

        async def mock_generate(*args, **kwargs):
            return failed_result

        mock_generator.generate_scenario = mock_generate

        with patch("llm.integration.LLMOutputParser"):
            integration = LLMIntegration(mock_generator)
            result = await integration.run_complete_pipeline()

            assert result.success is False
            assert "LLM generation failed" in result.errors

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_complete_pipeline_exception_handling(
        self, mock_generator, mock_sample_size_result
    ):
        """Test pipeline exception handling."""
        with patch("llm.integration.LLMOutputParser"), patch(
            "llm.integration.compute_sample_size", return_value=mock_sample_size_result
        ), patch(
            "llm.integration.simulate_trial", side_effect=Exception("Simulation error")
        ):
            integration = LLMIntegration(mock_generator)
            result = await integration.run_complete_pipeline()

            assert result.success is False
            assert any("Simulation error" in e for e in result.errors)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_run_complete_pipeline_with_warnings(
        self,
        mock_sample_size_result,
        mock_sim_result,
        mock_analysis_result,
        mock_scenario_dto,
    ):
        """Test pipeline preserves warnings from generation."""
        mock_generator = Mock()
        gen_result = Mock()
        gen_result.success = True
        gen_result.scenario_dto = mock_scenario_dto
        gen_result.errors = []
        gen_result.warnings = ["Low novelty score"]

        async def mock_generate(*args, **kwargs):
            return gen_result

        mock_generator.generate_scenario = mock_generate

        with patch("llm.integration.LLMOutputParser"), patch(
            "llm.integration.compute_sample_size", return_value=mock_sample_size_result
        ), patch(
            "llm.integration.simulate_trial", return_value=mock_sim_result
        ), patch(
            "llm.integration.analyze_results", return_value=mock_analysis_result
        ):
            integration = LLMIntegration(mock_generator)
            result = await integration.run_complete_pipeline()

            assert result.success is True
            assert "Low novelty score" in result.warnings


class TestConvertToCoreTypes:
    """Test suite for type conversion."""

    @pytest.mark.unit
    def test_convert_to_core_types(self, mock_generator, mock_scenario_dto):
        """Test conversion from DTOs to core types."""
        with patch("llm.integration.LLMOutputParser"):
            integration = LLMIntegration(mock_generator)
            design_params = integration._convert_to_core_types(mock_scenario_dto)

            assert isinstance(design_params, DesignParams)
            assert design_params.baseline_conversion_rate == 0.10
            assert design_params.target_lift_pct == 0.20
            assert design_params.alpha == 0.05
            assert design_params.power == 0.80
            assert design_params.expected_daily_traffic == 5000
            assert design_params.allocation.control == 0.5
            assert design_params.allocation.treatment == 0.5


class TestCompareWithLLMExpectations:
    """Test suite for LLM expectations comparison."""

    @pytest.mark.unit
    def test_compare_with_llm_expectations(
        self, mock_generator, mock_scenario_dto, mock_sim_result, mock_analysis_result
    ):
        """Test comparison of actual vs expected results."""
        with patch("llm.integration.LLMOutputParser"):
            integration = LLMIntegration(mock_generator)
            comparison = integration._compare_with_llm_expectations(
                mock_scenario_dto, mock_analysis_result, mock_sim_result
            )

            # Check structure
            assert "conversion_rates" in comparison
            assert "statistical_results" in comparison
            assert "llm_expectations" in comparison

            # Check conversion rates
            conv_rates = comparison["conversion_rates"]
            assert "actual" in conv_rates
            assert "expected" in conv_rates
            assert "differences" in conv_rates

            # Check actual rates
            assert conv_rates["actual"]["control"] == 0.10
            assert conv_rates["actual"]["treatment"] == 0.12

            # Check expected rates
            assert conv_rates["expected"]["control"] == 0.10
            assert conv_rates["expected"]["treatment"] == 0.12

            # Check statistical results
            stats = comparison["statistical_results"]
            assert stats["p_value"] == 0.02
            assert stats["significant"] is True

            # Check LLM expectations
            llm_exp = comparison["llm_expectations"]
            assert llm_exp["narrative_conclusion"] == "Test conclusion"
            assert llm_exp["business_interpretation"] == "Test interpretation"

    @pytest.mark.unit
    def test_compare_lift_calculation(
        self, mock_generator, mock_scenario_dto, mock_analysis_result
    ):
        """Test lift calculation in comparison."""
        mock_sim = Mock()
        mock_sim.control_n = 1000
        mock_sim.treatment_n = 1000
        mock_sim.control_conversions = 100  # 10%
        mock_sim.treatment_conversions = 120  # 12%

        with patch("llm.integration.LLMOutputParser"):
            integration = LLMIntegration(mock_generator)
            comparison = integration._compare_with_llm_expectations(
                mock_scenario_dto, mock_analysis_result, mock_sim
            )

            actual_lift = comparison["conversion_rates"]["actual"]["lift"]
            # (0.12 - 0.10) / 0.10 = 0.20
            assert abs(actual_lift - 0.20) < 0.01


# ============================================================================
# Pipeline Integration Tests
# ============================================================================


class TestPipelineSampleSize:
    """Test suite for sample size calculation in pipeline."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_sample_size_dict_structure(
        self,
        mock_generator,
        mock_sample_size_result,
        mock_sim_result,
        mock_analysis_result,
    ):
        """Test that sample_size dict has correct structure."""
        with patch("llm.integration.LLMOutputParser"), patch(
            "llm.integration.compute_sample_size", return_value=mock_sample_size_result
        ), patch(
            "llm.integration.simulate_trial", return_value=mock_sim_result
        ), patch(
            "llm.integration.analyze_results", return_value=mock_analysis_result
        ):
            integration = LLMIntegration(mock_generator)
            result = await integration.run_complete_pipeline()

            assert result.sample_size["per_arm"] == 5000
            assert result.sample_size["total"] == 10000
            assert result.sample_size["days_required"] == 2
            assert result.sample_size["power_achieved"] == 0.82


class TestPipelineCustomSettings:
    """Test suite for pipeline with custom settings."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_custom_max_attempts(
        self,
        mock_scenario_dto,
        mock_sample_size_result,
        mock_sim_result,
        mock_analysis_result,
    ):
        """Test pipeline passes custom max_attempts to generator."""
        mock_generator = Mock()
        gen_result = Mock()
        gen_result.success = True
        gen_result.scenario_dto = mock_scenario_dto
        gen_result.errors = []
        gen_result.warnings = []

        calls = []

        async def mock_generate(request, max_attempts, min_quality_score):
            calls.append(
                {
                    "request": request,
                    "max_attempts": max_attempts,
                    "min_quality_score": min_quality_score,
                }
            )
            return gen_result

        mock_generator.generate_scenario = mock_generate

        with patch("llm.integration.LLMOutputParser"), patch(
            "llm.integration.compute_sample_size", return_value=mock_sample_size_result
        ), patch(
            "llm.integration.simulate_trial", return_value=mock_sim_result
        ), patch(
            "llm.integration.analyze_results", return_value=mock_analysis_result
        ):
            integration = LLMIntegration(mock_generator)
            await integration.run_complete_pipeline(
                max_attempts=5, min_quality_score=0.9
            )

            assert len(calls) == 1
            assert calls[0]["max_attempts"] == 5
            assert calls[0]["min_quality_score"] == 0.9
