"""
Tests for llm.generator module - Scenario generation.
"""

import pytest
from tests.helpers.mocks import MockScenarioGenerator


class TestScenarioGenerator:
    """Test suite for scenario generator."""
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_success(self):
        """Test successful scenario generation."""
        generator = MockScenarioGenerator()
        
        result = await generator.generate_scenario()
        
        assert result["success"] == True
        assert result["scenario_dto"] is not None
    
    @pytest.mark.unit
    @pytest.mark.asyncio
    async def test_generate_scenario_failure(self):
        """Test failed scenario generation."""
        generator = MockScenarioGenerator(should_fail=True)
        
        result = await generator.generate_scenario()
        
        assert result["success"] == False

