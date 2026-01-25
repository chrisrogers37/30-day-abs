"""
Tests for schemas.complications module - Scenario complications schema.
"""

import pytest
from schemas.complications import (
    ComplicationType,
    Complication,
    ScenarioComplications,
    COMPLICATION_TEMPLATES,
    get_random_complications,
)


class TestComplicationType:
    """Test suite for ComplicationType enum."""

    @pytest.mark.unit
    def test_complication_type_values(self):
        """Test that all complication types have string values."""
        assert ComplicationType.SEASONALITY.value == "seasonality"
        assert ComplicationType.TIME_PRESSURE.value == "time_pressure"
        assert ComplicationType.NOVELTY_EFFECT.value == "novelty_effect"
        assert ComplicationType.NETWORK_EFFECTS.value == "network_effects"

    @pytest.mark.unit
    def test_all_complication_types_defined(self):
        """Test that expected complication types exist."""
        expected_types = [
            "seasonality",
            "time_pressure",
            "day_of_week_effect",
            "opportunity_cost",
            "cannibalization",
            "segment_heterogeneity",
            "network_effects",
            "novelty_effect",
            "multiple_testing",
            "early_stopping_pressure",
            "low_traffic",
            "high_variance",
            "user_harm_risk",
            "fairness_concern",
            "regulatory_requirement",
            "implementation_risk",
            "measurement_challenge",
            "delayed_outcome",
        ]
        actual_values = [ct.value for ct in ComplicationType]
        for expected in expected_types:
            assert expected in actual_values, f"Missing complication type: {expected}"


class TestComplication:
    """Test suite for Complication model."""

    @pytest.mark.unit
    def test_complication_creation_minimal(self):
        """Test creating a complication with minimal fields."""
        complication = Complication(
            type=ComplicationType.SEASONALITY,
            description="Test description",
        )
        assert complication.type == ComplicationType.SEASONALITY
        assert complication.description == "Test description"
        assert complication.severity == "medium"  # default
        assert complication.mitigation_hint is None
        assert complication.affects_analysis is False  # default
        assert complication.additional_questions == []  # default

    @pytest.mark.unit
    def test_complication_creation_full(self):
        """Test creating a complication with all fields."""
        complication = Complication(
            type=ComplicationType.TIME_PRESSURE,
            description="Urgent deadline",
            severity="high",
            mitigation_hint="Plan for shorter experiment",
            affects_analysis=True,
            additional_questions=["What is the minimum detectable effect?"],
        )
        assert complication.type == ComplicationType.TIME_PRESSURE
        assert complication.severity == "high"
        assert complication.mitigation_hint == "Plan for shorter experiment"
        assert complication.affects_analysis is True
        assert len(complication.additional_questions) == 1

    @pytest.mark.unit
    @pytest.mark.parametrize("severity", ["low", "medium", "high"])
    def test_complication_valid_severity_values(self, severity):
        """Test that all valid severity values are accepted."""
        complication = Complication(
            type=ComplicationType.NOVELTY_EFFECT,
            description="Test",
            severity=severity,
        )
        assert complication.severity == severity


class TestScenarioComplications:
    """Test suite for ScenarioComplications model."""

    @pytest.mark.unit
    def test_empty_complications(self):
        """Test creating scenario with no complications."""
        scenario_complications = ScenarioComplications()
        assert scenario_complications.complications == []
        assert scenario_complications.overall_complexity == "standard"
        assert scenario_complications.has_timing_complications is False
        assert scenario_complications.has_statistical_complications is False
        assert scenario_complications.has_ethical_complications is False

    @pytest.mark.unit
    def test_timing_complications_property(self):
        """Test has_timing_complications property."""
        complications = ScenarioComplications(
            complications=[
                Complication(
                    type=ComplicationType.SEASONALITY, description="Holiday season"
                )
            ]
        )
        assert complications.has_timing_complications is True
        assert complications.has_statistical_complications is False
        assert complications.has_ethical_complications is False

    @pytest.mark.unit
    def test_statistical_complications_property(self):
        """Test has_statistical_complications property."""
        complications = ScenarioComplications(
            complications=[
                Complication(
                    type=ComplicationType.NOVELTY_EFFECT, description="Users adapt"
                ),
                Complication(
                    type=ComplicationType.MULTIPLE_TESTING, description="Multiple tests"
                ),
            ]
        )
        assert complications.has_statistical_complications is True
        assert complications.has_timing_complications is False

    @pytest.mark.unit
    def test_ethical_complications_property(self):
        """Test has_ethical_complications property."""
        complications = ScenarioComplications(
            complications=[
                Complication(
                    type=ComplicationType.USER_HARM_RISK, description="Risk to users"
                )
            ]
        )
        assert complications.has_ethical_complications is True

    @pytest.mark.unit
    @pytest.mark.parametrize(
        "complexity", ["simple", "standard", "complex", "advanced"]
    )
    def test_overall_complexity_values(self, complexity):
        """Test all valid complexity levels."""
        complications = ScenarioComplications(overall_complexity=complexity)
        assert complications.overall_complexity == complexity


class TestComplicationTemplates:
    """Test suite for predefined complication templates."""

    @pytest.mark.unit
    def test_templates_exist(self):
        """Test that templates are defined for key complication types."""
        expected_types = [
            ComplicationType.SEASONALITY,
            ComplicationType.TIME_PRESSURE,
            ComplicationType.NOVELTY_EFFECT,
            ComplicationType.MULTIPLE_TESTING,
            ComplicationType.CANNIBALIZATION,
            ComplicationType.SEGMENT_HETEROGENEITY,
        ]
        for comp_type in expected_types:
            assert (
                comp_type in COMPLICATION_TEMPLATES
            ), f"Missing template for {comp_type}"

    @pytest.mark.unit
    def test_seasonality_template(self):
        """Test the seasonality complication template."""
        template = COMPLICATION_TEMPLATES[ComplicationType.SEASONALITY]
        assert template.type == ComplicationType.SEASONALITY
        assert template.severity == "high"
        assert template.affects_analysis is True
        assert "holiday" in template.description.lower()
        assert len(template.additional_questions) > 0

    @pytest.mark.unit
    def test_time_pressure_template(self):
        """Test the time pressure complication template."""
        template = COMPLICATION_TEMPLATES[ComplicationType.TIME_PRESSURE]
        assert template.type == ComplicationType.TIME_PRESSURE
        assert template.severity == "high"
        assert "2 weeks" in template.description

    @pytest.mark.unit
    def test_all_templates_have_required_fields(self):
        """Test that all templates have required fields populated."""
        for comp_type, template in COMPLICATION_TEMPLATES.items():
            assert template.type == comp_type
            assert len(template.description) > 10
            assert template.severity in ["low", "medium", "high"]
            assert template.mitigation_hint is not None
            assert template.affects_analysis is True  # All templates affect analysis


class TestGetRandomComplications:
    """Test suite for get_random_complications function."""

    @pytest.mark.unit
    def test_get_single_complication(self):
        """Test getting a single random complication."""
        complications = get_random_complications(count=1)
        assert len(complications) == 1
        assert isinstance(complications[0], Complication)

    @pytest.mark.unit
    def test_get_multiple_complications(self):
        """Test getting multiple random complications."""
        complications = get_random_complications(count=3)
        assert len(complications) == 3
        # All should be unique
        types = [c.type for c in complications]
        assert len(set(types)) == 3

    @pytest.mark.unit
    def test_count_exceeds_available(self):
        """Test that count is capped at available templates."""
        # Request more than available
        complications = get_random_complications(count=100)
        assert len(complications) <= len(COMPLICATION_TEMPLATES)

    @pytest.mark.unit
    def test_exclude_types(self):
        """Test excluding specific complication types."""
        excluded = [ComplicationType.SEASONALITY, ComplicationType.TIME_PRESSURE]
        complications = get_random_complications(count=3, exclude_types=excluded)
        returned_types = {c.type for c in complications}
        for excluded_type in excluded:
            assert excluded_type not in returned_types

    @pytest.mark.unit
    def test_severity_filter(self):
        """Test filtering by severity."""
        high_complications = get_random_complications(count=10, severity_filter="high")
        for c in high_complications:
            assert c.severity == "high"

    @pytest.mark.unit
    def test_severity_filter_medium(self):
        """Test filtering for medium severity."""
        medium_complications = get_random_complications(
            count=10, severity_filter="medium"
        )
        for c in medium_complications:
            assert c.severity == "medium"

    @pytest.mark.unit
    def test_combined_filters(self):
        """Test combining exclude and severity filters."""
        excluded = [ComplicationType.SEASONALITY]
        complications = get_random_complications(
            count=3, exclude_types=excluded, severity_filter="high"
        )
        for c in complications:
            assert c.type != ComplicationType.SEASONALITY
            assert c.severity == "high"
