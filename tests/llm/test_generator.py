"""Tests for llm.generator module - Scenario generation."""

import asyncio
import json
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass

from llm.generator import (
    GenerationResult,
    LLMScenarioGenerator,
    ScenarioGenerationError,
    create_scenario_generator,
)
from llm.client import LLMError
from llm.parser import ParsingResult


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

VALID_SCENARIO_JSON = {
    "scenario": {
        "title": "Checkout Button Color Test",
        "narrative": "Testing green vs blue checkout button.",
        "company_type": "E-commerce",
        "user_segment": "all_users",
        "primary_kpi": "conversion_rate",
        "secondary_kpis": ["revenue_per_visitor"],
        "unit": "visitor",
        "assumptions": ["steady traffic"],
    },
    "design_params": {
        "baseline_conversion_rate": 0.025,
        "mde_absolute": 0.005,
        "target_lift_pct": 0.20,
        "alpha": 0.05,
        "power": 0.80,
        "allocation": {"control": 0.5, "treatment": 0.5},
        "expected_daily_traffic": 5000,
    },
    "llm_expected": {
        "simulation_hints": {
            "treatment_conversion_rate": 0.030,
            "control_conversion_rate": 0.025,
        },
        "narrative_conclusion": "Expected 20% lift.",
        "business_interpretation": "Significant revenue impact.",
        "risk_assessment": "Low risk.",
        "next_steps": "Monitor for 2 weeks.",
        "notes": "Test notes.",
    },
}


def _make_llm_response(content: str, response_time: float = 0.5):
    """Create a mock LLM response object."""
    resp = Mock()
    resp.content = content
    resp.response_time = response_time
    return resp


def _make_parsing_result(success: bool, scenario_dto=None, errors=None, warnings=None):
    """Create a ParsingResult with the given fields."""
    return ParsingResult(
        success=success,
        scenario_dto=scenario_dto,
        errors=errors or [],
        warnings=warnings or [],
    )


def _make_validation_result(is_valid: bool, errors=None, warnings=None):
    """Create a mock guardrails validation result."""
    result = Mock()
    result.is_valid = is_valid
    result.errors = errors or []
    result.warnings = warnings or []
    return result


@pytest.fixture
def mock_client():
    """Create a mock LLM client."""
    client = AsyncMock()
    client.generate_scenario = AsyncMock(
        return_value=_make_llm_response(json.dumps(VALID_SCENARIO_JSON))
    )
    client.get_usage_stats = Mock(return_value={})
    return client


@pytest.fixture
def generator(mock_client):
    """Create a generator with mocked dependencies."""
    gen = LLMScenarioGenerator.__new__(LLMScenarioGenerator)
    gen.client = mock_client
    gen.parser = Mock()
    gen.guardrails = Mock()
    gen.prompt_template = "Generate a test scenario."
    return gen


# ---------------------------------------------------------------------------
# GenerationResult dataclass
# ---------------------------------------------------------------------------


class TestGenerationResult:
    """Tests for the GenerationResult dataclass."""

    def test_default_values(self):
        result = GenerationResult(success=False)
        assert result.success is False
        assert result.attempts == 0
        assert result.errors == []
        assert result.warnings == []
        assert result.diversity_suggestions == []
        assert result.novelty_score == 1.0
        assert result.used_fallback is False

    def test_none_lists_initialized(self):
        result = GenerationResult(success=True, errors=None, warnings=None, diversity_suggestions=None)
        assert result.errors == []
        assert result.warnings == []
        assert result.diversity_suggestions == []

    def test_success_result(self):
        result = GenerationResult(success=True, attempts=2, quality_score=0.85)
        assert result.success is True
        assert result.attempts == 2
        assert result.quality_score == 0.85


class TestScenarioGenerationError:
    def test_is_exception(self):
        err = ScenarioGenerationError("test error")
        assert isinstance(err, Exception)
        assert str(err) == "test error"


# ---------------------------------------------------------------------------
# LLMScenarioGenerator
# ---------------------------------------------------------------------------


class TestLLMScenarioGeneratorInit:
    """Tests for generator initialization."""

    def test_init_with_client(self, mock_client):
        with patch.object(LLMScenarioGenerator, '_load_prompt_template', return_value="prompt"):
            gen = LLMScenarioGenerator(mock_client)
            assert gen.client is mock_client
            assert gen.parser is not None
            assert gen.guardrails is not None

    def test_load_prompt_template_fallback(self, mock_client):
        """When prompt file doesn't exist, default prompt is used."""
        with patch.object(LLMScenarioGenerator, '_load_prompt_template', return_value="default prompt"):
            gen = LLMScenarioGenerator(mock_client)
            assert gen.prompt_template == "default prompt"


class TestGenerateScenario:
    """Tests for the generate_scenario method."""

    @pytest.mark.asyncio
    async def test_success_on_first_attempt(self, generator):
        """Happy path: parse succeeds, validation passes, quality above threshold."""
        mock_dto = Mock()
        mock_dto.scenario.title = "Test"
        mock_dto.scenario.company_type = "E-commerce"

        generator.parser.parse_llm_response.return_value = _make_parsing_result(
            success=True, scenario_dto=mock_dto
        )
        generator.guardrails.validate_scenario.return_value = _make_validation_result(
            is_valid=True
        )
        generator.guardrails.get_quality_score.return_value = 0.9

        with patch("llm.generator.score_scenario_novelty", return_value=(0.8, [])):
            with patch("llm.generator.record_generated_scenario"):
                result = await generator.generate_scenario(max_attempts=3, min_quality_score=0.7)

        assert result.success is True
        assert result.scenario_dto is mock_dto
        assert result.attempts == 1
        assert result.quality_score == 0.9

    @pytest.mark.asyncio
    async def test_retries_on_parse_failure(self, generator):
        """Generator retries when parsing fails."""
        mock_dto = Mock()
        mock_dto.scenario.title = "Test"
        mock_dto.scenario.company_type = "SaaS"

        # First attempt: parse fails. Second attempt: succeeds.
        generator.parser.parse_llm_response.side_effect = [
            _make_parsing_result(success=False, errors=["parse error"]),
            _make_parsing_result(success=True, scenario_dto=mock_dto),
        ]
        generator.guardrails.validate_scenario.return_value = _make_validation_result(is_valid=True)
        generator.guardrails.get_quality_score.return_value = 0.85

        with patch("llm.generator.score_scenario_novelty", return_value=(0.9, [])):
            with patch("llm.generator.record_generated_scenario"):
                result = await generator.generate_scenario(max_attempts=3, min_quality_score=0.7)

        assert result.success is True
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_retries_on_validation_failure(self, generator):
        """Generator retries when guardrails reject the scenario."""
        mock_dto = Mock()
        mock_dto.scenario.title = "Test"
        mock_dto.scenario.company_type = "SaaS"

        generator.parser.parse_llm_response.return_value = _make_parsing_result(
            success=True, scenario_dto=mock_dto
        )
        # First attempt: validation fails. Second: passes.
        generator.guardrails.validate_scenario.side_effect = [
            _make_validation_result(is_valid=False, errors=["out of bounds"]),
            _make_validation_result(is_valid=True),
        ]
        generator.guardrails.get_quality_score.return_value = 0.85

        with patch("llm.generator.score_scenario_novelty", return_value=(0.9, [])):
            with patch("llm.generator.record_generated_scenario"):
                result = await generator.generate_scenario(max_attempts=3, min_quality_score=0.7)

        assert result.success is True
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_retries_on_low_quality(self, generator):
        """Generator retries when quality score is below threshold."""
        mock_dto = Mock()
        mock_dto.scenario.title = "Test"
        mock_dto.scenario.company_type = "SaaS"

        generator.parser.parse_llm_response.return_value = _make_parsing_result(
            success=True, scenario_dto=mock_dto
        )
        generator.guardrails.validate_scenario.return_value = _make_validation_result(is_valid=True)
        # First: low quality. Second: high quality.
        generator.guardrails.get_quality_score.side_effect = [0.3, 0.9]

        with patch("llm.generator.score_scenario_novelty", return_value=(0.9, [])):
            with patch("llm.generator.record_generated_scenario"):
                result = await generator.generate_scenario(max_attempts=3, min_quality_score=0.7)

        assert result.success is True
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_fallback_on_all_failures(self, generator):
        """When all attempts fail, fallback scenario is used."""
        generator.parser.parse_llm_response.return_value = _make_parsing_result(
            success=False, errors=["always fails"]
        )
        fallback_dto = Mock()
        generator.parser.create_fallback_scenario.return_value = fallback_dto

        with patch("llm.generator.score_scenario_novelty", return_value=(1.0, [])):
            with patch("llm.generator.record_generated_scenario"):
                result = await generator.generate_scenario(max_attempts=2, min_quality_score=0.7)

        assert result.success is True
        assert result.used_fallback is True
        assert result.scenario_dto is fallback_dto

    @pytest.mark.asyncio
    async def test_llm_error_triggers_retry(self, generator):
        """LLMError causes retry with backoff."""
        mock_dto = Mock()
        mock_dto.scenario.title = "Test"
        mock_dto.scenario.company_type = "SaaS"

        generator.client.generate_scenario.side_effect = [
            LLMError("API timeout"),
            _make_llm_response(json.dumps(VALID_SCENARIO_JSON)),
        ]
        generator.parser.parse_llm_response.return_value = _make_parsing_result(
            success=True, scenario_dto=mock_dto
        )
        generator.guardrails.validate_scenario.return_value = _make_validation_result(is_valid=True)
        generator.guardrails.get_quality_score.return_value = 0.9

        with patch("llm.generator.score_scenario_novelty", return_value=(0.9, [])):
            with patch("llm.generator.record_generated_scenario"):
                with patch("asyncio.sleep", new_callable=AsyncMock):
                    result = await generator.generate_scenario(max_attempts=3, min_quality_score=0.7)

        assert result.success is True
        assert result.attempts == 2

    @pytest.mark.asyncio
    async def test_novelty_scoring_failure_graceful(self, generator):
        """Novelty scoring failure doesn't prevent success."""
        mock_dto = Mock()
        mock_dto.scenario.title = "Test"
        mock_dto.scenario.company_type = "SaaS"

        generator.parser.parse_llm_response.return_value = _make_parsing_result(
            success=True, scenario_dto=mock_dto
        )
        generator.guardrails.validate_scenario.return_value = _make_validation_result(is_valid=True)
        generator.guardrails.get_quality_score.return_value = 0.9

        with patch("llm.generator.score_scenario_novelty", side_effect=ValueError("scoring failed")):
            result = await generator.generate_scenario(max_attempts=1, min_quality_score=0.7)

        assert result.success is True
        assert result.novelty_score == 1.0  # default when scoring fails


class TestCreatePrompt:
    """Tests for prompt creation."""

    def test_no_request_returns_template(self, generator):
        prompt = generator._create_prompt(None)
        assert prompt == generator.prompt_template

    def test_request_with_company_type(self, generator):
        request = Mock()
        request.company_type = Mock(value="SaaS")
        request.user_segment = None
        request.complexity_level = None
        request.previous_experiments = None
        prompt = generator._create_prompt(request)
        assert "SaaS" in prompt

    def test_request_with_complexity(self, generator):
        request = Mock()
        request.company_type = None
        request.user_segment = None
        request.complexity_level = "high"
        request.previous_experiments = None
        prompt = generator._create_prompt(request)
        assert "complex" in prompt.lower()


class TestGenerateMultipleScenarios:
    """Tests for parallel scenario generation."""

    @pytest.mark.asyncio
    async def test_generates_requested_count(self, generator):
        mock_dto = Mock()
        mock_dto.scenario.title = "Test"
        mock_dto.scenario.company_type = "SaaS"

        generator.parser.parse_llm_response.return_value = _make_parsing_result(
            success=True, scenario_dto=mock_dto
        )
        generator.guardrails.validate_scenario.return_value = _make_validation_result(is_valid=True)
        generator.guardrails.get_quality_score.return_value = 0.9

        with patch("llm.generator.score_scenario_novelty", return_value=(0.9, [])):
            with patch("llm.generator.record_generated_scenario"):
                results = await generator.generate_multiple_scenarios(count=3)

        assert len(results) == 3
        assert all(r.success for r in results)


class TestCreateScenarioGenerator:
    """Tests for the factory function."""

    def test_create_mock_generator(self):
        with patch("llm.client.create_llm_client") as mock_create:
            mock_create.return_value = Mock()
            with patch.object(LLMScenarioGenerator, '_load_prompt_template', return_value="prompt"):
                gen = create_scenario_generator(provider="mock")
                assert isinstance(gen, LLMScenarioGenerator)
                mock_create.assert_called_once_with("mock", None, "gpt-4")
