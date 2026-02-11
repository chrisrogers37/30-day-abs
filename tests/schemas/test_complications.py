"""Tests for schemas.complications module."""

import pytest
from pydantic import ValidationError

from schemas.complications import (
    ComplicationType,
    Complication,
    ScenarioComplications,
    COMPLICATION_TEMPLATES,
    get_random_complications,
)


class TestComplicationType:
    """Tests for ComplicationType enum."""

    def test_all_types_are_strings(self):
        """Every ComplicationType value is a string."""
        for ct in ComplicationType:
            assert isinstance(ct.value, str)

    def test_expected_type_count(self):
        """Enum has the expected number of complication types."""
        assert len(ComplicationType) == 18

    def test_timing_types_exist(self):
        assert ComplicationType.SEASONALITY == "seasonality"
        assert ComplicationType.TIME_PRESSURE == "time_pressure"
        assert ComplicationType.DAY_OF_WEEK_EFFECT == "day_of_week_effect"

    def test_statistical_types_exist(self):
        assert ComplicationType.NOVELTY_EFFECT == "novelty_effect"
        assert ComplicationType.MULTIPLE_TESTING == "multiple_testing"
        assert ComplicationType.LOW_TRAFFIC == "low_traffic"

    def test_ethical_types_exist(self):
        assert ComplicationType.USER_HARM_RISK == "user_harm_risk"
        assert ComplicationType.FAIRNESS_CONCERN == "fairness_concern"
        assert ComplicationType.REGULATORY_REQUIREMENT == "regulatory_requirement"


class TestComplication:
    """Tests for Complication Pydantic model."""

    def test_valid_complication(self):
        c = Complication(
            type=ComplicationType.SEASONALITY,
            description="Holiday season affects traffic.",
        )
        assert c.type == ComplicationType.SEASONALITY
        assert c.severity == "medium"  # default
        assert c.mitigation_hint is None
        assert c.affects_analysis is False
        assert c.additional_questions == []

    def test_all_fields_populated(self):
        c = Complication(
            type=ComplicationType.LOW_TRAFFIC,
            description="Traffic is low.",
            severity="high",
            mitigation_hint="Wait for more traffic.",
            affects_analysis=True,
            additional_questions=["How would you handle this?"],
        )
        assert c.severity == "high"
        assert c.mitigation_hint == "Wait for more traffic."
        assert c.affects_analysis is True
        assert len(c.additional_questions) == 1

    def test_invalid_severity_rejected(self):
        with pytest.raises(ValidationError):
            Complication(
                type=ComplicationType.SEASONALITY,
                description="Test",
                severity="extreme",  # not in pattern
            )

    def test_serialization_roundtrip(self):
        original = Complication(
            type=ComplicationType.NOVELTY_EFFECT,
            description="Users may initially engage more.",
            severity="medium",
            affects_analysis=True,
        )
        data = original.model_dump()
        restored = Complication(**data)
        assert restored.type == original.type
        assert restored.description == original.description
        assert restored.severity == original.severity


class TestScenarioComplications:
    """Tests for ScenarioComplications model."""

    def test_empty_complications(self):
        sc = ScenarioComplications()
        assert sc.complications == []
        assert sc.overall_complexity == "standard"

    def test_with_complications(self):
        c = Complication(
            type=ComplicationType.SEASONALITY,
            description="Holiday effect.",
        )
        sc = ScenarioComplications(complications=[c])
        assert len(sc.complications) == 1

    def test_invalid_complexity_rejected(self):
        with pytest.raises(ValidationError):
            ScenarioComplications(overall_complexity="impossible")

    def test_has_timing_complications_true(self):
        c = Complication(type=ComplicationType.SEASONALITY, description="Test")
        sc = ScenarioComplications(complications=[c])
        assert sc.has_timing_complications is True
        assert sc.has_statistical_complications is False

    def test_has_statistical_complications_true(self):
        c = Complication(type=ComplicationType.LOW_TRAFFIC, description="Test")
        sc = ScenarioComplications(complications=[c])
        assert sc.has_statistical_complications is True
        assert sc.has_timing_complications is False

    def test_has_ethical_complications_true(self):
        c = Complication(type=ComplicationType.USER_HARM_RISK, description="Test")
        sc = ScenarioComplications(complications=[c])
        assert sc.has_ethical_complications is True

    def test_no_complications_all_false(self):
        sc = ScenarioComplications()
        assert sc.has_timing_complications is False
        assert sc.has_statistical_complications is False
        assert sc.has_ethical_complications is False

    def test_max_three_complications(self):
        """Model enforces max_length=3 on complications list."""
        comps = [
            Complication(type=ComplicationType.SEASONALITY, description="1"),
            Complication(type=ComplicationType.LOW_TRAFFIC, description="2"),
            Complication(type=ComplicationType.NOVELTY_EFFECT, description="3"),
            Complication(type=ComplicationType.TIME_PRESSURE, description="4"),
        ]
        with pytest.raises(ValidationError):
            ScenarioComplications(complications=comps)


class TestComplicationTemplates:
    """Tests for predefined complication templates."""

    def test_templates_exist(self):
        assert len(COMPLICATION_TEMPLATES) > 0

    def test_all_templates_are_valid_complications(self):
        for ct, complication in COMPLICATION_TEMPLATES.items():
            assert isinstance(complication, Complication)
            assert complication.type == ct
            assert len(complication.description) > 0

    def test_templates_have_mitigation_hints(self):
        for complication in COMPLICATION_TEMPLATES.values():
            assert complication.mitigation_hint is not None

    def test_templates_have_additional_questions(self):
        for complication in COMPLICATION_TEMPLATES.values():
            assert len(complication.additional_questions) > 0


class TestGetRandomComplications:
    """Tests for get_random_complications function."""

    def test_returns_requested_count(self):
        result = get_random_complications(count=2)
        assert len(result) == 2

    def test_returns_single_complication(self):
        result = get_random_complications(count=1)
        assert len(result) == 1
        assert isinstance(result[0], Complication)

    def test_count_exceeds_available(self):
        """Requesting more than available returns all available."""
        result = get_random_complications(count=100)
        assert len(result) == len(COMPLICATION_TEMPLATES)

    def test_exclude_types(self):
        result = get_random_complications(
            count=100,
            exclude_types=[ComplicationType.SEASONALITY],
        )
        types = {c.type for c in result}
        assert ComplicationType.SEASONALITY not in types

    def test_severity_filter(self):
        result = get_random_complications(count=100, severity_filter="high")
        for c in result:
            assert c.severity == "high"

    def test_severity_filter_no_matches(self):
        """Filtering by a severity with no matches returns empty."""
        result = get_random_complications(count=5, severity_filter="low")
        # All templates are medium or high, so low should return fewer/none
        for c in result:
            assert c.severity == "low"
