"""
Comprehensive tests for llm.generator module - Real generator with mock clients.

These tests exercise the actual LLMScenarioGenerator class with mocked dependencies
to achieve better coverage than the pure mock approach.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from dataclasses import dataclass
from typing import Optional

from llm.generator import (
    LLMScenarioGenerator,
    GenerationResult,
    ScenarioGenerationError,
    create_scenario_generator,
)
from llm.client import LLMClient, LLMError
from llm.parser import ParsingResult
from llm.guardrails import ValidationResult
from schemas.scenario import ScenarioRequestDTO
from schemas.shared import CompanyType, UserSegment


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def mock_client():
    """Create a mock LLM client."""
    client = Mock(spec=LLMClient)

    # Create a mock response with content attribute
    mock_response = Mock()
    mock_response.content = '{"scenario": {"title": "Test"}, "design_params": {}}'
    mock_response.response_time = 1.5

    # Make generate_scenario return the mock asynchronously
    async def mock_generate(*args, **kwargs):
        return mock_response

    client.generate_scenario = mock_generate
    client.get_usage_stats = Mock(return_value={"calls": 1})
    return client


@pytest.fixture
def mock_parser():
    """Create a mock parser."""
    parser = Mock()
    mock_dto = Mock()
    mock_dto.scenario = Mock()
    mock_dto.scenario.title = "Test Scenario"
    mock_dto.scenario.company_type = CompanyType.ECOMMERCE
    mock_dto.scenario.user_segment = UserSegment.ALL_USERS
    mock_dto.design_params = Mock()

    result = Mock(spec=ParsingResult)
    result.success = True
    result.scenario_dto = mock_dto
    result.errors = []

    parser.parse_llm_response = Mock(return_value=result)
    parser.create_fallback_scenario = Mock(return_value=mock_dto)
    return parser


@pytest.fixture
def mock_guardrails():
    """Create a mock guardrails validator."""
    guardrails = Mock()
    validation = Mock(spec=ValidationResult)
    validation.is_valid = True
    validation.errors = []
    validation.warnings = []

    guardrails.validate_scenario = Mock(return_value=validation)
    guardrails.get_quality_score = Mock(return_value=0.85)
    return guardrails


# ============================================================================
# GenerationResult Tests
# ============================================================================


class TestGenerationResult:
    """Test suite for GenerationResult dataclass."""

    @pytest.mark.unit
    def test_generation_result_defaults(self):
        """Test GenerationResult with default values."""
        result = GenerationResult(success=False)
        assert result.success is False
        assert result.scenario_dto is None
        assert result.attempts == 0
        assert result.total_time == 0.0
        assert result.errors == []
        assert result.warnings == []
        assert result.quality_score == 0.0
        assert result.novelty_score == 1.0
        assert result.diversity_suggestions == []
        assert result.used_fallback is False

    @pytest.mark.unit
    def test_generation_result_with_values(self):
        """Test GenerationResult with provided values."""
        mock_dto = Mock()
        result = GenerationResult(
            success=True,
            scenario_dto=mock_dto,
            attempts=2,
            total_time=3.5,
            errors=["error1"],
            warnings=["warning1"],
            quality_score=0.9,
            novelty_score=0.7,
            diversity_suggestions=["suggestion1"],
            used_fallback=True,
        )
        assert result.success is True
        assert result.scenario_dto == mock_dto
        assert result.attempts == 2
        assert result.total_time == 3.5
        assert result.errors == ["error1"]
        assert result.warnings == ["warning1"]
        assert result.quality_score == 0.9
        assert result.novelty_score == 0.7
        assert result.diversity_suggestions == ["suggestion1"]
        assert result.used_fallback is True

    @pytest.mark.unit
    def test_generation_result_post_init_none_lists(self):
        """Test that None lists are initialized to empty lists."""
        result = GenerationResult(
            success=True, errors=None, warnings=None, diversity_suggestions=None
        )
        assert result.errors == []
        assert result.warnings == []
        assert result.diversity_suggestions == []


# ============================================================================
# LLMScenarioGenerator Tests
# ============================================================================


class TestLLMScenarioGenerator:
    """Test suite for LLMScenarioGenerator class."""

    @pytest.mark.unit
    def test_generator_initialization(self, mock_client):
        """Test generator initialization."""
        with patch("llm.generator.LLMOutputParser") as MockParser, patch(
            "llm.generator.LLMGuardrails"
        ) as MockGuardrails:
            generator = LLMScenarioGenerator(mock_client)

            assert generator.client == mock_client
            MockParser.assert_called_once()
            MockGuardrails.assert_called_once()

    @pytest.mark.unit
    def test_load_prompt_template_fallback(self, mock_client):
        """Test that default prompt is used when template file is missing."""
        with patch("pathlib.Path.read_text", side_effect=FileNotFoundError()), patch(
            "llm.generator.LLMOutputParser"
        ), patch("llm.generator.LLMGuardrails"):
            generator = LLMScenarioGenerator(mock_client)

            # Should have loaded default prompt
            assert "Generate a realistic AB test scenario" in generator.prompt_template
            assert "JSON" in generator.prompt_template

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_success(
        self, mock_client, mock_parser, mock_guardrails
    ):
        """Test successful scenario generation."""
        with patch("llm.generator.LLMOutputParser", return_value=mock_parser), patch(
            "llm.generator.LLMGuardrails", return_value=mock_guardrails
        ), patch("llm.generator.score_scenario_novelty", return_value=(0.8, [])), patch(
            "llm.generator.record_generated_scenario"
        ):
            generator = LLMScenarioGenerator(mock_client)
            result = await generator.generate_scenario()

            assert result.success is True
            assert result.scenario_dto is not None
            assert result.quality_score == 0.85
            assert result.attempts >= 1

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_parsing_failure_retry(
        self, mock_client, mock_guardrails
    ):
        """Test retry on parsing failure."""
        mock_parser = Mock()
        # First call fails, second succeeds
        mock_dto = Mock()
        mock_dto.scenario = Mock(
            title="Test", company_type=CompanyType.ECOMMERCE, user_segment=UserSegment.ALL_USERS
        )

        failed_result = Mock(success=False, errors=["Parse error"])
        success_result = Mock(success=True, scenario_dto=mock_dto, errors=[])

        mock_parser.parse_llm_response = Mock(
            side_effect=[failed_result, success_result]
        )
        mock_parser.create_fallback_scenario = Mock(return_value=mock_dto)

        with patch("llm.generator.LLMOutputParser", return_value=mock_parser), patch(
            "llm.generator.LLMGuardrails", return_value=mock_guardrails
        ), patch("llm.generator.score_scenario_novelty", return_value=(0.8, [])), patch(
            "llm.generator.record_generated_scenario"
        ):
            generator = LLMScenarioGenerator(mock_client)
            result = await generator.generate_scenario(max_attempts=3)

            assert result.success is True
            assert result.attempts >= 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_validation_failure_retry(
        self, mock_client, mock_parser
    ):
        """Test retry on validation failure."""
        mock_guardrails = Mock()
        # First call fails, second succeeds
        failed_validation = Mock(is_valid=False, errors=["Invalid params"], warnings=[])
        success_validation = Mock(is_valid=True, errors=[], warnings=[])

        mock_guardrails.validate_scenario = Mock(
            side_effect=[failed_validation, success_validation]
        )
        mock_guardrails.get_quality_score = Mock(return_value=0.85)

        with patch("llm.generator.LLMOutputParser", return_value=mock_parser), patch(
            "llm.generator.LLMGuardrails", return_value=mock_guardrails
        ), patch("llm.generator.score_scenario_novelty", return_value=(0.8, [])), patch(
            "llm.generator.record_generated_scenario"
        ):
            generator = LLMScenarioGenerator(mock_client)
            result = await generator.generate_scenario(max_attempts=3)

            assert result.success is True
            assert result.attempts >= 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_quality_below_threshold_retry(
        self, mock_client, mock_parser, mock_guardrails
    ):
        """Test retry when quality score is below threshold."""
        # First call returns low quality, second returns acceptable
        mock_guardrails.get_quality_score = Mock(side_effect=[0.5, 0.85])

        with patch("llm.generator.LLMOutputParser", return_value=mock_parser), patch(
            "llm.generator.LLMGuardrails", return_value=mock_guardrails
        ), patch("llm.generator.score_scenario_novelty", return_value=(0.8, [])), patch(
            "llm.generator.record_generated_scenario"
        ):
            generator = LLMScenarioGenerator(mock_client)
            result = await generator.generate_scenario(
                max_attempts=3, min_quality_score=0.7
            )

            assert result.success is True
            assert result.quality_score == 0.85

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_llm_error_retry(
        self, mock_parser, mock_guardrails
    ):
        """Test retry on LLM error."""
        mock_client = Mock(spec=LLMClient)

        call_count = 0

        async def mock_generate(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise LLMError("API timeout")
            mock_response = Mock()
            mock_response.content = '{"scenario": {}, "design_params": {}}'
            mock_response.response_time = 1.0
            return mock_response

        mock_client.generate_scenario = mock_generate
        mock_client.get_usage_stats = Mock(return_value={})

        with patch("llm.generator.LLMOutputParser", return_value=mock_parser), patch(
            "llm.generator.LLMGuardrails", return_value=mock_guardrails
        ), patch("llm.generator.score_scenario_novelty", return_value=(0.8, [])), patch(
            "llm.generator.record_generated_scenario"
        ):
            generator = LLMScenarioGenerator(mock_client)
            result = await generator.generate_scenario(max_attempts=3)

            assert result.success is True
            assert call_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_all_attempts_fail_uses_fallback(
        self, mock_client
    ):
        """Test fallback scenario when all attempts fail."""
        mock_parser = Mock()
        failed_result = Mock(success=False, errors=["Parse error"])
        mock_parser.parse_llm_response = Mock(return_value=failed_result)

        mock_dto = Mock()
        mock_dto.scenario = Mock(
            title="Fallback", company_type=CompanyType.ECOMMERCE, user_segment=UserSegment.ALL_USERS
        )
        mock_parser.create_fallback_scenario = Mock(return_value=mock_dto)

        mock_guardrails = Mock()

        with patch("llm.generator.LLMOutputParser", return_value=mock_parser), patch(
            "llm.generator.LLMGuardrails", return_value=mock_guardrails
        ), patch("llm.generator.score_scenario_novelty", return_value=(0.8, [])), patch(
            "llm.generator.record_generated_scenario"
        ):
            generator = LLMScenarioGenerator(mock_client)
            result = await generator.generate_scenario(max_attempts=2)

            assert result.success is True
            assert result.used_fallback is True
            mock_parser.create_fallback_scenario.assert_called_once()

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_low_novelty_warning(
        self, mock_client, mock_parser, mock_guardrails
    ):
        """Test warning for low novelty score."""
        with patch("llm.generator.LLMOutputParser", return_value=mock_parser), patch(
            "llm.generator.LLMGuardrails", return_value=mock_guardrails
        ), patch(
            "llm.generator.score_scenario_novelty", return_value=(0.3, ["Try different company type"])
        ), patch(
            "llm.generator.record_generated_scenario"
        ):
            generator = LLMScenarioGenerator(mock_client)
            result = await generator.generate_scenario()

            assert result.success is True
            assert result.novelty_score == 0.3
            assert any("novelty" in w.lower() for w in result.warnings)
            assert "Try different company type" in result.diversity_suggestions

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_novelty_scoring_failure(
        self, mock_client, mock_parser, mock_guardrails
    ):
        """Test graceful handling of novelty scoring failure."""
        with patch("llm.generator.LLMOutputParser", return_value=mock_parser), patch(
            "llm.generator.LLMGuardrails", return_value=mock_guardrails
        ), patch(
            "llm.generator.score_scenario_novelty", side_effect=Exception("Scoring failed")
        ), patch(
            "llm.generator.record_generated_scenario"
        ):
            generator = LLMScenarioGenerator(mock_client)
            result = await generator.generate_scenario()

            assert result.success is True
            assert result.novelty_score == 1.0  # Default when scoring fails


class TestCreatePrompt:
    """Test suite for prompt creation."""

    @pytest.mark.unit
    def test_create_prompt_no_request(self, mock_client):
        """Test prompt creation without request."""
        with patch("llm.generator.LLMOutputParser"), patch("llm.generator.LLMGuardrails"):
            generator = LLMScenarioGenerator(mock_client)
            prompt = generator._create_prompt(None)

            assert prompt == generator.prompt_template

    @pytest.mark.unit
    def test_create_prompt_with_company_type(self, mock_client):
        """Test prompt customization with company type."""
        with patch("llm.generator.LLMOutputParser"), patch("llm.generator.LLMGuardrails"):
            generator = LLMScenarioGenerator(mock_client)
            request = Mock(spec=ScenarioRequestDTO)
            request.company_type = CompanyType.SAAS
            request.user_segment = None
            request.complexity_level = None
            request.previous_experiments = None

            prompt = generator._create_prompt(request)

            assert "SaaS" in prompt

    @pytest.mark.unit
    def test_create_prompt_with_user_segment(self, mock_client):
        """Test prompt customization with user segment."""
        with patch("llm.generator.LLMOutputParser"), patch("llm.generator.LLMGuardrails"):
            generator = LLMScenarioGenerator(mock_client)
            request = Mock(spec=ScenarioRequestDTO)
            request.company_type = None
            request.user_segment = UserSegment.NEW_USERS
            request.complexity_level = None
            request.previous_experiments = None

            prompt = generator._create_prompt(request)

            assert "new_users" in prompt

    @pytest.mark.unit
    def test_create_prompt_with_complexity_level(self, mock_client):
        """Test prompt customization with complexity level."""
        with patch("llm.generator.LLMOutputParser"), patch("llm.generator.LLMGuardrails"):
            generator = LLMScenarioGenerator(mock_client)
            request = Mock(spec=ScenarioRequestDTO)
            request.company_type = None
            request.user_segment = None
            request.complexity_level = "high"
            request.previous_experiments = None

            prompt = generator._create_prompt(request)

            assert "complex scenario" in prompt.lower()


class TestGenerateMultipleScenarios:
    """Test suite for parallel scenario generation."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_multiple_scenarios_success(
        self, mock_client, mock_parser, mock_guardrails
    ):
        """Test successful parallel generation."""
        with patch("llm.generator.LLMOutputParser", return_value=mock_parser), patch(
            "llm.generator.LLMGuardrails", return_value=mock_guardrails
        ), patch("llm.generator.score_scenario_novelty", return_value=(0.8, [])), patch(
            "llm.generator.record_generated_scenario"
        ):
            generator = LLMScenarioGenerator(mock_client)
            results = await generator.generate_multiple_scenarios(count=3)

            assert len(results) == 3
            assert all(r.success for r in results)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_multiple_scenarios_handles_exceptions(self, mock_client):
        """Test handling of exceptions in parallel generation."""
        mock_parser = Mock()
        mock_dto = Mock()
        mock_dto.scenario = Mock(
            title="Test", company_type=CompanyType.ECOMMERCE, user_segment=UserSegment.ALL_USERS
        )

        call_count = 0

        def mock_parse(*args):
            nonlocal call_count
            call_count += 1
            if call_count == 2:
                raise Exception("Parsing error")
            return Mock(success=True, scenario_dto=mock_dto, errors=[])

        mock_parser.parse_llm_response = Mock(side_effect=mock_parse)
        mock_parser.create_fallback_scenario = Mock(return_value=mock_dto)

        mock_guardrails = Mock()
        mock_guardrails.validate_scenario = Mock(
            return_value=Mock(is_valid=True, errors=[], warnings=[])
        )
        mock_guardrails.get_quality_score = Mock(return_value=0.85)

        with patch("llm.generator.LLMOutputParser", return_value=mock_parser), patch(
            "llm.generator.LLMGuardrails", return_value=mock_guardrails
        ), patch("llm.generator.score_scenario_novelty", return_value=(0.8, [])), patch(
            "llm.generator.record_generated_scenario"
        ):
            generator = LLMScenarioGenerator(mock_client)
            results = await generator.generate_multiple_scenarios(count=3)

            assert len(results) == 3
            # Some may have succeeded, some may have used fallback


class TestGetGenerationStats:
    """Test suite for generation statistics."""

    @pytest.mark.unit
    def test_get_generation_stats(self, mock_client):
        """Test getting generation statistics."""
        with patch("llm.generator.LLMOutputParser"), patch(
            "llm.generator.LLMGuardrails"
        ), patch(
            "llm.generator.get_novelty_scorer"
        ) as mock_scorer:
            mock_scorer.return_value.get_history_summary = Mock(
                return_value={"total": 10}
            )

            generator = LLMScenarioGenerator(mock_client)
            stats = generator.get_generation_stats()

            assert "client_config" in stats
            assert "prompt_length" in stats
            assert stats["guardrails_enabled"] is True
            assert stats["parser_enabled"] is True
            assert stats["novelty_scorer_enabled"] is True
            assert "novelty_history" in stats


# ============================================================================
# Factory Function Tests
# ============================================================================


class TestCreateScenarioGenerator:
    """Test suite for factory function."""

    @pytest.mark.unit
    def test_create_generator_mock_provider(self):
        """Test creating generator with mock provider."""
        # Patch at the source where it's imported from
        with patch("llm.client.create_llm_client") as mock_create:
            mock_client = Mock(spec=LLMClient)
            mock_create.return_value = mock_client

            with patch("llm.generator.LLMOutputParser"), patch(
                "llm.generator.LLMGuardrails"
            ):
                generator = create_scenario_generator(provider="mock")

                mock_create.assert_called_once_with("mock", None, "gpt-4")
                assert generator.client == mock_client

    @pytest.mark.unit
    def test_create_generator_with_api_key(self):
        """Test creating generator with API key."""
        with patch("llm.client.create_llm_client") as mock_create:
            mock_client = Mock(spec=LLMClient)
            mock_create.return_value = mock_client

            with patch("llm.generator.LLMOutputParser"), patch(
                "llm.generator.LLMGuardrails"
            ):
                generator = create_scenario_generator(
                    provider="openai", api_key="test-key", model="gpt-4-turbo"
                )

                mock_create.assert_called_once_with(
                    "openai", "test-key", "gpt-4-turbo"
                )

    @pytest.mark.unit
    def test_create_generator_with_kwargs(self):
        """Test creating generator with additional kwargs."""
        with patch("llm.client.create_llm_client") as mock_create:
            mock_client = Mock(spec=LLMClient)
            mock_create.return_value = mock_client

            with patch("llm.generator.LLMOutputParser"), patch(
                "llm.generator.LLMGuardrails"
            ):
                generator = create_scenario_generator(
                    provider="mock", temperature=0.7, max_tokens=1000
                )

                mock_create.assert_called_once_with(
                    "mock", None, "gpt-4", temperature=0.7, max_tokens=1000
                )
