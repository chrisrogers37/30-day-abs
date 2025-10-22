"""
Real API integration tests.

These tests are marked to skip in CI unless API keys are provided.
"""

import pytest
import os


class TestRealAPI:
    """Test real API integration (skipped by default)."""
    
    @pytest.mark.requires_api
    @pytest.mark.skipif(
        os.getenv("OPENAI_API_KEY") is None,
        reason="Requires OPENAI_API_KEY environment variable"
    )
    def test_real_openai_integration(self):
        """Test real OpenAI API integration."""
        # This would test real API calls if key is provided
        pytest.skip("Real API tests not implemented yet")

