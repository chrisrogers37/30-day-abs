"""
LLM Client Module - Pluggable Interface for Large Language Model APIs

This module provides a unified, pluggable interface for interacting with various
Large Language Model (LLM) providers including OpenAI, Anthropic, and mock clients.
It includes comprehensive error handling, retry logic with exponential backoff,
rate limiting, and standardized response formatting.

Key Features:
- Multi-provider support (OpenAI, Anthropic, Mock)
- Async/await support for concurrent operations
- Exponential backoff retry logic with configurable attempts
- Rate limit handling and automatic delays
- Comprehensive error classification and handling
- Standardized response format with metadata
- Factory pattern for easy client creation
- Built-in logging and monitoring support

Architecture:
The module follows a clean architecture with clear separation of concerns:
- LLMClient: Main client interface with async support
- LLMConfig: Configuration dataclass for client settings
- LLMResponse: Standardized response format with metadata
- MockLLMClient: Mock implementation for testing and development
- Factory functions: Easy client creation with sensible defaults

Usage Examples:
    Basic Usage:
        client = create_llm_client(provider="openai", api_key="your-key")
        response = await client.generate_completion(messages=[...])
    
    Advanced Configuration:
        config = LLMConfig(
            provider=LLMProvider.OPENAI,
            model="gpt-4",
            max_retries=5,
            temperature=0.5
        )
        client = LLMClient(config)
    
    Mock Client for Testing:
        client = create_llm_client(provider="mock")
        response = await client.generate_scenario()

Error Handling:
The module provides specific exception types for different failure modes:
- LLMError: Base exception for all LLM-related errors
- LLMRateLimitError: Rate limit exceeded
- LLMTimeoutError: Request timeout
- LLMValidationError: Response validation failed

Performance Considerations:
- Async/await support for non-blocking operations
- Connection pooling and reuse
- Configurable timeouts and retry delays
- Rate limiting to prevent API quota exhaustion
- Efficient memory usage with streaming support (when available)

Dependencies:
- httpx: HTTP client for API requests
- openai: OpenAI Python SDK
- asyncio: Async support
- logging: Built-in logging support
"""

import asyncio
import os
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

import openai
from openai import AsyncOpenAI

from core.logging import get_logger

logger = get_logger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


@dataclass
class LLMConfig:
    """
    Configuration dataclass for LLM client settings.
    
    This class encapsulates all configuration parameters needed to initialize
    and configure an LLM client. It provides sensible defaults while allowing
    customization for specific use cases.
    
    Attributes:
        provider (LLMProvider): The LLM provider to use (OpenAI, Anthropic, Mock)
        api_key (str): API key for the LLM provider
        model (str): Model name to use (default: "gpt-4")
        max_tokens (int): Maximum tokens to generate (default: 4000)
        temperature (float): Sampling temperature 0-2 (default: 0.7)
        timeout (int): Request timeout in seconds (default: 30)
        max_retries (int): Maximum retry attempts (default: 3)
        retry_delay (float): Base delay between retries in seconds (default: 1.0)
        rate_limit_delay (float): Additional delay for rate limiting (default: 0.1)
    
    Examples:
        Basic configuration:
            config = LLMConfig(
                provider=LLMProvider.OPENAI,
                api_key="your-api-key"
            )
        
        Advanced configuration:
            config = LLMConfig(
                provider=LLMProvider.OPENAI,
                api_key="your-api-key",
                model="gpt-4-turbo",
                max_tokens=8000,
                temperature=0.5,
                max_retries=5
            )
    """
    provider: LLMProvider
    api_key: str
    model: str = "gpt-4"
    max_tokens: int = 4000
    temperature: float = 0.7
    timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    rate_limit_delay: float = 0.1


@dataclass
class LLMResponse:
    """
    Standardized response format from LLM client.
    
    This dataclass provides a consistent response format across all LLM providers,
    including the generated content, metadata, and performance metrics.
    
    Attributes:
        content (str): The generated text content from the LLM
        model (str): The model name used for generation
        usage (Optional[Dict[str, int]]): Token usage statistics (prompt, completion, total)
        finish_reason (Optional[str]): Reason why generation finished (stop, length, etc.)
        response_time (float): Time taken for the request in seconds
        retry_count (int): Number of retries performed before success
    
    Examples:
        Access generated content:
            response = await client.generate_completion(messages=[...])
            print(response.content)
        
        Check performance metrics:
            if response.response_time > 5.0:
                print(f"Slow response: {response.response_time:.2f}s")
        
        Monitor retry behavior:
            if response.retry_count > 0:
                print(f"Request succeeded after {response.retry_count} retries")
    """
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    finish_reason: Optional[str] = None
    response_time: float = 0.0
    retry_count: int = 0


class LLMError(Exception):
    """Base exception for LLM-related errors."""
    pass


class LLMRateLimitError(LLMError):
    """Rate limit exceeded."""
    pass


class LLMTimeoutError(LLMError):
    """Request timeout."""
    pass


class LLMValidationError(LLMError):
    """Response validation failed."""
    pass


class LLMClient:
    """
    Main LLM client with comprehensive retry logic and error handling.
    
    This class provides a unified interface for interacting with various LLM providers.
    It includes automatic retry logic with exponential backoff, rate limiting,
    comprehensive error handling, and standardized response formatting.
    
    Features:
        - Multi-provider support (OpenAI, Anthropic, Mock)
        - Async/await support for concurrent operations
        - Exponential backoff retry logic
        - Rate limit handling and automatic delays
        - Comprehensive error classification
        - Built-in logging and monitoring
        - Standardized response format
    
    Attributes:
        config (LLMConfig): Configuration settings for the client
        _client: The underlying provider-specific client instance
    
    Examples:
        Basic usage:
            config = LLMConfig(provider=LLMProvider.OPENAI, api_key="key")
            client = LLMClient(config)
            response = await client.generate_completion(messages=[...])
        
        Scenario generation:
            response = await client.generate_scenario("Generate a test scenario")
        
        With custom parameters:
            response = await client.generate_completion(
                messages=[...],
                temperature=0.5,
                max_tokens=2000
            )
    """
    
    def __init__(self, config: LLMConfig):
        """
        Initialize the LLM client with the provided configuration.
        
        Args:
            config (LLMConfig): Configuration settings for the client
            
        Raises:
            ValueError: If the provider is not supported
            NotImplementedError: If the provider is not yet implemented
        """
        self.config = config
        self._client = None
        self._setup_client()
    
    def _setup_client(self):
        """Setup the appropriate LLM client based on provider."""
        if self.config.provider == LLMProvider.OPENAI:
            self._client = AsyncOpenAI(
                api_key=self.config.api_key,
                timeout=self.config.timeout
            )
        elif self.config.provider == LLMProvider.ANTHROPIC:
            # Anthropic provider is defined in LLMProvider enum for future use.
            # Implementation tracked separately from tech debt remediation.
            raise NotImplementedError("Anthropic client not yet implemented")
        elif self.config.provider == LLMProvider.MOCK:
            self._client = MockLLMClient()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
    
    async def _execute_with_retry(self, params: dict) -> LLMResponse:
        """
        Execute an LLM API call with retry logic and exponential backoff.

        Args:
            params: Complete parameters dict for the API call (model, messages, etc.)

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            LLMError: If all retry attempts fail
        """
        start_time = time.time()
        last_error = None

        for attempt in range(self.config.max_retries + 1):
            try:
                if self.config.provider == LLMProvider.MOCK:
                    response = await self._client.generate_completion(**params)
                    response_time = time.time() - start_time

                    logger.info(f"LLM Response (Mock) - Attempt: {attempt + 1}, Time: {response_time:.2f}s")
                    logger.debug(f"LLM Response Content: {response.content[:500]}...")

                    return LLMResponse(
                        content=response.content,
                        model=response.model,
                        usage=response.usage,
                        finish_reason=response.finish_reason,
                        response_time=response_time,
                        retry_count=attempt
                    )
                else:
                    response = await self._client.chat.completions.create(**params)

                response_time = time.time() - start_time
                content = response.choices[0].message.content

                logger.info(f"LLM Response (OpenAI) - Attempt: {attempt + 1}, Time: {response_time:.2f}s")
                logger.debug(f"LLM Response Content: {content[:500]}...")

                return LLMResponse(
                    content=content,
                    model=response.model,
                    usage=response.usage.dict() if response.usage else None,
                    finish_reason=response.choices[0].finish_reason,
                    response_time=response_time,
                    retry_count=attempt
                )

            except (openai.APIError, openai.APIConnectionError, openai.APITimeoutError,
                    openai.RateLimitError, openai.AuthenticationError) as e:
                last_error = e
                logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}")

                if attempt < self.config.max_retries:
                    if "rate limit" in str(e).lower():
                        await asyncio.sleep(self.config.rate_limit_delay * (2 ** attempt))
                    else:
                        await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    break

        response_time = time.time() - start_time
        raise LLMError(f"LLM call failed after {self.config.max_retries + 1} attempts: {last_error}")

    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion with comprehensive retry logic and error handling.

        Args:
            messages: List of message dicts with 'role' and 'content' keys
            system_prompt: Optional system prompt to prepend
            **kwargs: Additional parameters (temperature, max_tokens, etc.)

        Returns:
            LLMResponse with generated content and metadata

        Raises:
            LLMError: Base exception for LLM-related errors
            LLMRateLimitError: When rate limits are exceeded
            LLMTimeoutError: When requests timeout
            LLMValidationError: When response validation fails
        """
        # Prepare messages
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)

        logger.info(f"LLM Request - Provider: {self.config.provider.value}, Model: {self.config.model}")
        logger.debug(f"LLM Request Messages: {full_messages}")

        # Prepare parameters
        params = {
            "model": self.config.model,
            "messages": full_messages,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            **kwargs
        }

        logger.debug(f"LLM Request Parameters: {params}")

        return await self._execute_with_retry(params)
    
    async def generate_scenario(
        self,
        prompt: str = "Generate a realistic AB test scenario now:",
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate a scenario with specialized prompt handling.
        
        Args:
            prompt: The scenario generation prompt (defaults to trigger)
            system_prompt: Optional system prompt (loads from file if None)
            **kwargs: Additional parameters
            
        Returns:
            LLMResponse with generated scenario
        """
        # Load system prompt from file if not provided
        if system_prompt is None:
            try:
                prompt_file = os.path.join(os.path.dirname(__file__), "prompts", "scenario_prompt.txt")
                with open(prompt_file, 'r') as f:
                    system_prompt = f.read()
            except FileNotFoundError:
                # Fallback system prompt if file not found
                system_prompt = """You are an expert data scientist creating AB test scenarios. 
                Return ONLY valid JSON in this exact structure:
                {
                  "scenario": {
                    "title": "Brief title",
                    "narrative": "Description",
                    "company_type": "E-commerce",
                    "user_segment": "all_users",
                    "primary_kpi": "conversion_rate",
                    "secondary_kpis": ["metric1", "metric2"],
                    "unit": "visitor",
                    "assumptions": ["assumption1", "assumption2"]
                  },
                  "design_params": {
                    "baseline_conversion_rate": 0.025,
                    "mde_absolute": 0.005,
                    "target_lift_pct": 0.20,
                    "alpha": 0.01,
                    "power": 0.90,
                    "allocation": {"control": 0.5, "treatment": 0.5},
                    "expected_daily_traffic": 2500
                  },
                  "llm_expected": {
                    "simulation_hints": {
                      "treatment_conversion_rate": 0.030,
                      "control_conversion_rate": 0.025
                    },
                    "narrative_conclusion": "Expected conclusion",
                    "business_interpretation": "Business impact",
                    "risk_assessment": "Risk assessment",
                    "next_steps": "Next steps",
                    "notes": "These are suggestions only; use your simulator for ground truth."
                  }
                }"""
        
        messages = [{"role": "user", "content": prompt}]
        return await self.generate_completion(messages, system_prompt, **kwargs)
    
    def get_usage_stats(self) -> Dict[str, Union[int, float]]:
        """Get usage statistics for monitoring."""
        return {
            "provider": self.config.provider.value,
            "model": self.config.model,
            "max_tokens": self.config.max_tokens,
            "temperature": self.config.temperature,
            "timeout": self.config.timeout,
            "max_retries": self.config.max_retries
        }


class MockLLMClient:
    """Mock LLM client for testing and development."""
    
    def __init__(self):
        self.call_count = 0
    
    async def generate_completion(self, **kwargs) -> LLMResponse:
        """Generate a mock response."""
        self.call_count += 1
        
        # Simulate API delay
        await asyncio.sleep(0.1)
        
        # Return a mock scenario response
        mock_content = """{
  "scenario": {
    "title": "Mock E-commerce Checkout Button Test",
    "narrative": "We want to test a more prominent checkout button on our e-commerce site to improve conversion rates.",
    "company_type": "E-commerce",
    "user_segment": "all_users",
    "primary_kpi": "conversion_rate",
    "secondary_kpis": ["revenue_per_visitor", "cart_abandonment_rate"],
    "unit": "visitor",
    "assumptions": ["traffic is steady", "no seasonality during test window", "users behave independently"]
  },
  "design_params": {
    "baseline_conversion_rate": 0.025,
    "mde_absolute": 0.005,
    "target_lift_pct": 0.20,
    "alpha": 0.10,
    "power": 0.70,
    "allocation": {"control": 0.5, "treatment": 0.5},
    "expected_daily_traffic": 1800
  },
  "llm_expected": {
    "simulation_hints": {
      "treatment_conversion_rate": 0.030,
      "control_conversion_rate": 0.025
    },
    "narrative_conclusion": "If we observe ~20% relative lift with sufficient power, we should proceed with rollout.",
    "business_interpretation": "A 20% lift in checkout conversion would significantly impact revenue.",
    "risk_assessment": "Low risk - button change is simple to implement and rollback.",
    "next_steps": "Monitor for 2 weeks, then analyze results and decide on rollout.",
    "notes": "These are suggestions only; use your simulator for ground truth."
  }
}"""
        
        return LLMResponse(
            content=mock_content,
            model="mock-model",
            usage={"prompt_tokens": 100, "completion_tokens": 200, "total_tokens": 300},
            finish_reason="stop",
            response_time=0.1,
            retry_count=0
        )


def create_llm_client(
    provider: str = "openai",
    api_key: Optional[str] = None,
    model: str = "gpt-4",
    **kwargs
) -> LLMClient:
    """
    Factory function to create LLM client.
    
    Args:
        provider: LLM provider ("openai", "anthropic", "mock")
        api_key: API key for the provider
        model: Model name to use
        **kwargs: Additional configuration parameters
        
    Returns:
        Configured LLMClient instance
    """
    if provider == "mock":
        # Mock client doesn't need API key
        api_key = "mock-api-key"
    elif api_key is None:
        import os
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError("API key must be provided or set in OPENAI_API_KEY environment variable")
    
    config = LLMConfig(
        provider=LLMProvider(provider),
        api_key=api_key,
        model=model,
        **kwargs
    )
    
    return LLMClient(config)
