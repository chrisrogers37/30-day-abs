"""Tests for schemas.scenario module."""
import pytest

class TestScenarioDTO:
    @pytest.mark.unit
    def test_scenario_dict_structure(self, sample_scenario_dict):
        assert "scenario" in sample_scenario_dict
        assert "design_params" in sample_scenario_dict
        assert sample_scenario_dict["scenario"]["company_type"] == "E-commerce"

