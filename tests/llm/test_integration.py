"""Tests for llm.integration module - LLM pipeline integration."""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from llm.integration import (
    LLMIntegration,
    LLMIntegrationError,
    SimulationPipelineResult,
    create_llm_integration,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_scenario_dto():
    """Build a mock ScenarioResponseDTO with all required nested attributes."""
    dto = Mock()

    # scenario sub-object
    dto.scenario.title = "Test Scenario"
    dto.scenario.company_type = "E-commerce"
    dto.scenario.primary_kpi = "conversion_rate"

    # design_params sub-object (with to_design_params method)
    design = Mock()
    design.baseline_conversion_rate = 0.025
    design.mde_absolute = 0.005
    design.target_lift_pct = 0.20
    design.alpha = 0.05
    design.power = 0.80
    design.allocation.control = 0.5
    design.allocation.treatment = 0.5
    design.expected_daily_traffic = 5000
    dto.design_params = design

    # llm_expected sub-object
    dto.llm_expected.simulation_hints.control_conversion_rate = 0.025
    dto.llm_expected.simulation_hints.treatment_conversion_rate = 0.030
    dto.llm_expected.narrative_conclusion = "Expected 20% lift."
    dto.llm_expected.business_interpretation = "Revenue impact."
    dto.llm_expected.risk_assessment = "Low."
    dto.llm_expected.next_steps = "Monitor."

    return dto


def _make_generation_result(success=True, scenario_dto=None, errors=None, warnings=None):
    result = Mock()
    result.success = success
    result.scenario_dto = scenario_dto
    result.errors = errors or []
    result.warnings = warnings or []
    return result


def _make_core_design_params():
    dp = Mock()
    dp.alpha = 0.05
    dp.baseline_conversion_rate = 0.025
    dp.target_lift_pct = 0.20
    dp.power = 0.80
    dp.expected_daily_traffic = 5000
    return dp


def _make_sample_size_result():
    ssr = Mock()
    ssr.per_arm = 3000
    ssr.total = 6000
    ssr.days_required = 2
    ssr.power_achieved = 0.82
    return ssr


def _make_sim_result():
    sr = Mock()
    sr.control_conversions = 75
    sr.control_n = 3000
    sr.treatment_conversions = 90
    sr.treatment_n = 3000
    sr.control_rate = 0.025
    sr.treatment_rate = 0.030
    return sr


def _make_analysis_result():
    ar = Mock()
    ar.p_value = 0.03
    ar.confidence_interval = (0.001, 0.009)
    ar.effect_size = 0.15
    return ar


@pytest.fixture
def mock_generator():
    gen = AsyncMock()
    return gen


@pytest.fixture
def integration(mock_generator):
    integ = LLMIntegration.__new__(LLMIntegration)
    integ.generator = mock_generator
    integ.parser = Mock()
    return integ


# ---------------------------------------------------------------------------
# SimulationPipelineResult
# ---------------------------------------------------------------------------


class TestSimulationPipelineResult:
    def test_default_values(self):
        result = SimulationPipelineResult(success=False)
        assert result.success is False
        assert result.errors == []
        assert result.warnings == []
        assert result.scenario_dto is None

    def test_none_lists_initialized(self):
        result = SimulationPipelineResult(success=True, errors=None, warnings=None)
        assert result.errors == []
        assert result.warnings == []


class TestLLMIntegrationError:
    def test_is_exception(self):
        err = LLMIntegrationError("pipeline failed")
        assert isinstance(err, Exception)


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class TestRunCompletePipeline:

    @pytest.mark.asyncio
    async def test_pipeline_success(self, integration):
        """Full pipeline succeeds end-to-end with mocks."""
        scenario_dto = _make_scenario_dto()
        core_dp = _make_core_design_params()
        ssr = _make_sample_size_result()
        sim = _make_sim_result()
        analysis = _make_analysis_result()

        # Mock generation result
        integration.generator.generate_scenario = AsyncMock(
            return_value=_make_generation_result(success=True, scenario_dto=scenario_dto)
        )

        # Mock DTO conversion
        scenario_dto.design_params.to_design_params = Mock(return_value=core_dp)

        with patch("llm.integration.compute_sample_size", return_value=ssr):
            with patch("llm.integration.simulate_trial", return_value=sim):
                with patch("llm.integration.analyze_results", return_value=analysis):
                    result = await integration.run_complete_pipeline()

        assert result.success is True
        assert result.scenario_dto is scenario_dto
        assert result.design_params is core_dp
        assert result.analysis_result is analysis

    @pytest.mark.asyncio
    async def test_pipeline_fails_on_generation_failure(self, integration):
        """Pipeline returns error when generation fails."""
        integration.generator.generate_scenario = AsyncMock(
            return_value=_make_generation_result(success=False, errors=["LLM failed"])
        )

        result = await integration.run_complete_pipeline()

        assert result.success is False
        assert "LLM failed" in result.errors

    @pytest.mark.asyncio
    async def test_pipeline_handles_exception(self, integration):
        """Pipeline catches exceptions and returns error result."""
        scenario_dto = _make_scenario_dto()
        integration.generator.generate_scenario = AsyncMock(
            return_value=_make_generation_result(success=True, scenario_dto=scenario_dto)
        )
        # DTO conversion raises
        scenario_dto.design_params.to_design_params = Mock(side_effect=ValueError("bad conversion"))

        result = await integration.run_complete_pipeline()

        assert result.success is False
        assert any("Pipeline error" in e for e in result.errors)


class TestConvertToCoreTypes:
    """Tests for DTO-to-core conversion (now delegates to DTO method)."""

    def test_delegates_to_dto(self, integration):
        scenario_dto = _make_scenario_dto()
        core_dp = _make_core_design_params()
        scenario_dto.design_params.to_design_params = Mock(return_value=core_dp)

        result = integration._convert_to_core_types(scenario_dto)

        assert result is core_dp
        scenario_dto.design_params.to_design_params.assert_called_once()


class TestGetPipelineSummary:
    """Tests for pipeline summary generation."""

    def test_summary_for_failed_result(self, integration):
        result = SimulationPipelineResult(success=False, errors=["Something went wrong"])
        summary = integration.get_pipeline_summary(result)
        assert summary["status"] == "failed"
        assert "Something went wrong" in summary["errors"]

    def test_summary_for_successful_result(self, integration):
        result = SimulationPipelineResult(success=True)
        result.scenario_dto = _make_scenario_dto()
        result.design_params = _make_core_design_params()
        result.sample_size = {"per_arm": 3000, "total": 6000, "days_required": 2, "power_achieved": 0.82}
        result.simulation_result = _make_sim_result()
        result.analysis_result = _make_analysis_result()
        result.comparison = None

        summary = integration.get_pipeline_summary(result)
        assert summary["status"] == "success"
        assert "scenario" in summary
        assert "design" in summary
        assert "analysis" in summary


class TestCreateLLMIntegration:
    """Tests for the factory function."""

    def test_create_returns_integration(self):
        with patch("llm.generator.create_scenario_generator") as mock_create:
            mock_create.return_value = Mock()
            integ = create_llm_integration(provider="mock")
            assert isinstance(integ, LLMIntegration)
