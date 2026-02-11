"""
Tests for llm.client module - LLM client operations.
"""

import pytest
from tests.helpers.mocks import create_mock_llm_client


class TestMockLLMClient:
    """Test suite for mock LLM client (used for testing)."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mock_client_basic(self):
        """Test basic mock client functionality."""
        client = create_mock_llm_client()
        
        response = await client.generate_completion(
            messages=[{"role": "user", "content": "Test"}]
        )
        
        assert response is not None
        assert "choices" in response
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mock_client_tracks_calls(self):
        """Test that mock client tracks calls."""
        client = create_mock_llm_client()
        
        assert client.call_count == 0
        
        await client.generate_completion(
            messages=[{"role": "user", "content": "Test"}]
        )
        
        assert client.call_count == 1
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_mock_client_failure(self):
        """Test mock client failure simulation."""
        client = create_mock_llm_client(should_fail=True)
        
        with pytest.raises(Exception):
            await client.generate_completion(
                messages=[{"role": "user", "content": "Test"}]
            )

