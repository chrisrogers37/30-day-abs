"""
LLM client wrapper with pluggable interface and retry logic.

This module provides a clean interface for LLM API calls with comprehensive
error handling, rate limiting, and retry logic.
"""

import asyncio
import logging
import os
import time
from typing import Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

import httpx
from openai import AsyncOpenAI, OpenAI
from openai.types.chat import ChatCompletion

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class LLMProvider(str, Enum):
    """Supported LLM providers."""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    MOCK = "mock"


@dataclass
class LLMConfig:
    """Configuration for LLM client."""
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
    """Response from LLM client."""
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
    """LLM client with retry logic and error handling."""
    
    def __init__(self, config: LLMConfig):
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
            # TODO: Implement Anthropic client
            raise NotImplementedError("Anthropic client not yet implemented")
        elif self.config.provider == LLMProvider.MOCK:
            self._client = MockLLMClient()
        else:
            raise ValueError(f"Unsupported LLM provider: {self.config.provider}")
    
    async def generate_completion(
        self,
        messages: List[Dict[str, str]],
        system_prompt: Optional[str] = None,
        **kwargs
    ) -> LLMResponse:
        """
        Generate completion with retry logic and error handling.
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            system_prompt: Optional system prompt
            **kwargs: Additional parameters for the LLM call
            
        Returns:
            LLMResponse with generated content
            
        Raises:
            LLMError: For various LLM-related errors
        """
        start_time = time.time()
        
        # Prepare messages
        full_messages = []
        if system_prompt:
            full_messages.append({"role": "system", "content": system_prompt})
        full_messages.extend(messages)
        
        # Log the request details
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
        
        # Retry logic
        last_error = None
        for attempt in range(self.config.max_retries + 1):
            try:
                if self.config.provider == LLMProvider.MOCK:
                    response = await self._client.generate_completion(**params)
                    # Mock client returns LLMResponse directly
                    response_time = time.time() - start_time
                    
                    logger.info(f"LLM Response (Mock) - Attempt: {attempt + 1}, Time: {response_time:.2f}s")
                    logger.debug(f"LLM Response Content: {response.content[:500]}...")  # First 500 chars
                    
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
                logger.debug(f"LLM Response Content: {content[:500]}...")  # First 500 chars
                
                return LLMResponse(
                    content=content,
                    model=response.model,
                    usage=response.usage.dict() if response.usage else None,
                    finish_reason=response.choices[0].finish_reason,
                    response_time=response_time,
                    retry_count=attempt
                )
                
            except Exception as e:
                last_error = e
                logger.warning(f"LLM call failed (attempt {attempt + 1}): {e}")
                
                if attempt < self.config.max_retries:
                    # Check if it's a rate limit error
                    if "rate limit" in str(e).lower():
                        await asyncio.sleep(self.config.rate_limit_delay * (2 ** attempt))
                    else:
                        await asyncio.sleep(self.config.retry_delay * (2 ** attempt))
                else:
                    break
        
        # If we get here, all retries failed
        response_time = time.time() - start_time
        raise LLMError(f"LLM call failed after {self.config.max_retries + 1} attempts: {last_error}")
    
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
