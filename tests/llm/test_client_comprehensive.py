"""
Comprehensive tests for llm.client module - LLM Client Interface.

These tests exercise the LLMClient class, LLMConfig, LLMResponse, MockLLMClient,
and factory functions with proper test coverage of initialization, retry logic,
error handling, and response formatting.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
import asyncio

from llm.client import (
    LLMProvider,
    LLMConfig,
    LLMResponse,
    LLMError,
    LLMRateLimitError,
    LLMTimeoutError,
    LLMValidationError,
    LLMClient,
    MockLLMClient,
    create_llm_client,
)


# ============================================================================
# LLMProvider Tests
# ============================================================================


class TestLLMProvider:
    """Test suite for LLMProvider enum."""

    @pytest.mark.unit
    def test_provider_values(self):
        """Test provider enum values."""
        assert LLMProvider.OPENAI.value == "openai"
        assert LLMProvider.ANTHROPIC.value == "anthropic"
        assert LLMProvider.MOCK.value == "mock"

    @pytest.mark.unit
    def test_provider_is_string_enum(self):
        """Test provider can be used as string through value."""
        assert LLMProvider.OPENAI.value == "openai"
        # Also verify it inherits from str
        assert isinstance(LLMProvider.OPENAI, str)


# ============================================================================
# LLMConfig Tests
# ============================================================================


class TestLLMConfig:
    """Test suite for LLMConfig dataclass."""

    @pytest.mark.unit
    def test_config_required_fields(self):
        """Test config with required fields only."""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            api_key="test-key"
        )
        assert config.provider == LLMProvider.OPENAI
        assert config.api_key == "test-key"

    @pytest.mark.unit
    def test_config_defaults(self):
        """Test config default values."""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            api_key="test-key"
        )
        assert config.model == "gpt-4"
        assert config.max_tokens == 4000
        assert config.temperature == 0.7
        assert config.timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.rate_limit_delay == 0.1

    @pytest.mark.unit
    def test_config_custom_values(self):
        """Test config with custom values."""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            api_key="test-key",
            model="gpt-4-turbo",
            max_tokens=8000,
            temperature=0.5,
            timeout=60,
            max_retries=5,
            retry_delay=2.0,
            rate_limit_delay=0.5
        )
        assert config.model == "gpt-4-turbo"
        assert config.max_tokens == 8000
        assert config.temperature == 0.5
        assert config.timeout == 60
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        assert config.rate_limit_delay == 0.5


# ============================================================================
# LLMResponse Tests
# ============================================================================


class TestLLMResponse:
    """Test suite for LLMResponse dataclass."""

    @pytest.mark.unit
    def test_response_required_fields(self):
        """Test response with required fields only."""
        response = LLMResponse(
            content="Test content",
            model="gpt-4"
        )
        assert response.content == "Test content"
        assert response.model == "gpt-4"

    @pytest.mark.unit
    def test_response_defaults(self):
        """Test response default values."""
        response = LLMResponse(
            content="Test content",
            model="gpt-4"
        )
        assert response.usage is None
        assert response.finish_reason is None
        assert response.response_time == 0.0
        assert response.retry_count == 0

    @pytest.mark.unit
    def test_response_full(self):
        """Test response with all fields."""
        usage = {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30}
        response = LLMResponse(
            content="Test content",
            model="gpt-4",
            usage=usage,
            finish_reason="stop",
            response_time=1.5,
            retry_count=2
        )
        assert response.usage == usage
        assert response.finish_reason == "stop"
        assert response.response_time == 1.5
        assert response.retry_count == 2


# ============================================================================
# Exception Tests
# ============================================================================


class TestExceptions:
    """Test suite for LLM exception classes."""

    @pytest.mark.unit
    def test_llm_error_inheritance(self):
        """Test LLMError is proper exception."""
        error = LLMError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    @pytest.mark.unit
    def test_rate_limit_error_inheritance(self):
        """Test LLMRateLimitError inherits from LLMError."""
        error = LLMRateLimitError("Rate limit exceeded")
        assert isinstance(error, LLMError)
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_timeout_error_inheritance(self):
        """Test LLMTimeoutError inherits from LLMError."""
        error = LLMTimeoutError("Request timeout")
        assert isinstance(error, LLMError)
        assert isinstance(error, Exception)

    @pytest.mark.unit
    def test_validation_error_inheritance(self):
        """Test LLMValidationError inherits from LLMError."""
        error = LLMValidationError("Validation failed")
        assert isinstance(error, LLMError)
        assert isinstance(error, Exception)


# ============================================================================
# MockLLMClient Tests
# ============================================================================


class TestMockLLMClient:
    """Test suite for MockLLMClient class."""

    @pytest.mark.unit
    def test_mock_client_initialization(self):
        """Test mock client initializes correctly."""
        client = MockLLMClient()
        assert client.call_count == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mock_client_generate_completion(self):
        """Test mock client generates completion."""
        client = MockLLMClient()
        response = await client.generate_completion()

        assert isinstance(response, LLMResponse)
        assert response.model == "mock-model"
        assert response.finish_reason == "stop"
        assert "scenario" in response.content

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mock_client_tracks_calls(self):
        """Test mock client tracks call count."""
        client = MockLLMClient()

        await client.generate_completion()
        assert client.call_count == 1

        await client.generate_completion()
        assert client.call_count == 2

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mock_client_returns_valid_json(self):
        """Test mock client returns valid JSON content."""
        import json
        client = MockLLMClient()
        response = await client.generate_completion()

        # Should be valid JSON
        data = json.loads(response.content)
        assert "scenario" in data
        assert "design_params" in data
        assert "llm_expected" in data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mock_client_usage_stats(self):
        """Test mock client returns usage stats."""
        client = MockLLMClient()
        response = await client.generate_completion()

        assert response.usage is not None
        assert "prompt_tokens" in response.usage
        assert "completion_tokens" in response.usage
        assert "total_tokens" in response.usage


# ============================================================================
# LLMClient Tests
# ============================================================================


class TestLLMClientInit:
    """Test suite for LLMClient initialization."""

    @pytest.mark.unit
    def test_client_init_mock_provider(self):
        """Test client initialization with mock provider."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            api_key="mock-key"
        )
        client = LLMClient(config)

        assert client.config == config
        assert isinstance(client._client, MockLLMClient)

    @pytest.mark.unit
    def test_client_init_openai_provider(self):
        """Test client initialization with OpenAI provider."""
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            api_key="test-openai-key"
        )

        with patch("llm.client.AsyncOpenAI") as mock_openai:
            client = LLMClient(config)
            mock_openai.assert_called_once_with(
                api_key="test-openai-key",
                timeout=30
            )

    @pytest.mark.unit
    def test_client_init_anthropic_not_implemented(self):
        """Test client raises NotImplementedError for Anthropic."""
        config = LLMConfig(
            provider=LLMProvider.ANTHROPIC,
            api_key="test-key"
        )

        with pytest.raises(NotImplementedError, match="Anthropic"):
            LLMClient(config)


class TestLLMClientGenerateCompletion:
    """Test suite for LLMClient.generate_completion method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_completion_mock(self):
        """Test generate_completion with mock provider."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            api_key="mock-key"
        )
        client = LLMClient(config)

        messages = [{"role": "user", "content": "Test message"}]
        response = await client.generate_completion(messages)

        assert isinstance(response, LLMResponse)
        assert response.content is not None
        assert response.retry_count == 0

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_completion_with_system_prompt(self):
        """Test generate_completion with system prompt."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            api_key="mock-key"
        )
        client = LLMClient(config)

        messages = [{"role": "user", "content": "Test message"}]
        system_prompt = "You are a helpful assistant."
        response = await client.generate_completion(messages, system_prompt)

        assert isinstance(response, LLMResponse)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_completion_retry_on_failure(self):
        """Test generate_completion retries on failure."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            api_key="mock-key",
            max_retries=2,
            retry_delay=0.01  # Fast retries for testing
        )
        client = LLMClient(config)

        # Make the mock client fail twice then succeed
        call_count = 0
        async def failing_generate(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Temporary failure")
            return LLMResponse(
                content="Success",
                model="mock",
                retry_count=call_count - 1
            )

        client._client.generate_completion = failing_generate

        messages = [{"role": "user", "content": "Test"}]
        response = await client.generate_completion(messages)

        assert call_count == 3
        assert response.content == "Success"

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_completion_all_retries_fail(self):
        """Test generate_completion raises after all retries fail."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            api_key="mock-key",
            max_retries=1,
            retry_delay=0.01
        )
        client = LLMClient(config)

        async def always_fail(**kwargs):
            raise Exception("Persistent failure")

        client._client.generate_completion = always_fail

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMError, match="failed after"):
            await client.generate_completion(messages)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_completion_rate_limit_delay(self):
        """Test rate limit errors get extra delay."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            api_key="mock-key",
            max_retries=1,
            rate_limit_delay=0.01
        )
        client = LLMClient(config)

        call_count = 0
        async def rate_limited_then_success(**kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise Exception("rate limit exceeded")
            return LLMResponse(content="Success", model="mock")

        client._client.generate_completion = rate_limited_then_success

        messages = [{"role": "user", "content": "Test"}]
        response = await client.generate_completion(messages)

        assert call_count == 2
        assert response.content == "Success"


class TestLLMClientGenerateScenario:
    """Test suite for LLMClient.generate_scenario method."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_default_prompt(self):
        """Test generate_scenario with default prompt."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            api_key="mock-key"
        )
        client = LLMClient(config)

        response = await client.generate_scenario()

        assert isinstance(response, LLMResponse)
        assert "scenario" in response.content

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_custom_prompt(self):
        """Test generate_scenario with custom prompt."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            api_key="mock-key"
        )
        client = LLMClient(config)

        response = await client.generate_scenario(
            prompt="Generate a SaaS scenario",
            system_prompt="You are an expert."
        )

        assert isinstance(response, LLMResponse)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_loads_prompt_file(self):
        """Test generate_scenario loads system prompt from file."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            api_key="mock-key"
        )
        client = LLMClient(config)

        mock_file_content = "System prompt from file"
        with patch("builtins.open", create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = mock_file_content
            response = await client.generate_scenario()

            assert isinstance(response, LLMResponse)

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_fallback_prompt(self):
        """Test generate_scenario uses fallback when file not found."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            api_key="mock-key"
        )
        client = LLMClient(config)

        with patch("builtins.open", side_effect=FileNotFoundError()):
            response = await client.generate_scenario()

            assert isinstance(response, LLMResponse)


class TestLLMClientUsageStats:
    """Test suite for LLMClient.get_usage_stats method."""

    @pytest.mark.unit
    def test_get_usage_stats(self):
        """Test get_usage_stats returns correct info."""
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            api_key="mock-key",
            model="gpt-4-turbo",
            max_tokens=8000,
            temperature=0.5,
            timeout=60,
            max_retries=5
        )
        client = LLMClient(config)

        stats = client.get_usage_stats()

        assert stats["provider"] == "mock"
        assert stats["model"] == "gpt-4-turbo"
        assert stats["max_tokens"] == 8000
        assert stats["temperature"] == 0.5
        assert stats["timeout"] == 60
        assert stats["max_retries"] == 5


# ============================================================================
# Factory Function Tests
# ============================================================================


class TestCreateLLMClient:
    """Test suite for create_llm_client factory function."""

    @pytest.mark.unit
    def test_create_mock_client(self):
        """Test creating mock client."""
        client = create_llm_client(provider="mock")

        assert isinstance(client, LLMClient)
        assert client.config.provider == LLMProvider.MOCK
        assert client.config.api_key == "mock-api-key"

    @pytest.mark.unit
    def test_create_client_with_api_key(self):
        """Test creating client with explicit API key."""
        with patch("llm.client.AsyncOpenAI"):
            client = create_llm_client(
                provider="openai",
                api_key="explicit-key"
            )

            assert client.config.api_key == "explicit-key"

    @pytest.mark.unit
    def test_create_client_from_env(self):
        """Test creating client from environment variable."""
        with patch("llm.client.AsyncOpenAI"):
            with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
                client = create_llm_client(provider="openai")

                assert client.config.api_key == "env-key"

    @pytest.mark.unit
    def test_create_client_missing_api_key(self):
        """Test creating client without API key raises error."""
        with patch.dict("os.environ", {}, clear=True):
            # Ensure OPENAI_API_KEY is not set
            import os
            if "OPENAI_API_KEY" in os.environ:
                del os.environ["OPENAI_API_KEY"]

            with pytest.raises(ValueError, match="API key"):
                create_llm_client(provider="openai")

    @pytest.mark.unit
    def test_create_client_custom_model(self):
        """Test creating client with custom model."""
        client = create_llm_client(
            provider="mock",
            model="gpt-4-turbo"
        )

        assert client.config.model == "gpt-4-turbo"

    @pytest.mark.unit
    def test_create_client_extra_kwargs(self):
        """Test creating client with extra configuration."""
        client = create_llm_client(
            provider="mock",
            max_tokens=8000,
            temperature=0.3
        )

        assert client.config.max_tokens == 8000
        assert client.config.temperature == 0.3


# ============================================================================
# Integration Tests
# ============================================================================


class TestLLMClientIntegration:
    """Integration tests for complete LLM client workflows."""

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_full_scenario_generation_flow(self):
        """Test complete scenario generation workflow."""
        import json

        client = create_llm_client(provider="mock")
        response = await client.generate_scenario()

        # Verify response structure
        assert isinstance(response, LLMResponse)
        assert response.content is not None

        # Verify content is valid JSON with expected structure
        data = json.loads(response.content)
        assert "scenario" in data
        assert "title" in data["scenario"]
        assert "design_params" in data
        assert "baseline_conversion_rate" in data["design_params"]
        assert "llm_expected" in data

    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_multiple_concurrent_requests(self):
        """Test handling multiple concurrent requests."""
        client = create_llm_client(provider="mock")

        # Make 5 concurrent requests
        tasks = [
            client.generate_scenario()
            for _ in range(5)
        ]

        responses = await asyncio.gather(*tasks)

        assert len(responses) == 5
        for response in responses:
            assert isinstance(response, LLMResponse)
            assert response.content is not None
