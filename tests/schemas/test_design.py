"""Tests for schemas.design module."""
import pytest
from pydantic import ValidationError
from schemas.design import DesignParamsDTO

class TestDesignParamsDTO:
    @pytest.mark.unit
    def test_design_params_dto_valid(self, standard_allocation_dto):
        params = DesignParamsDTO(
            baseline_conversion_rate=0.025,
            mde_absolute=0.005,
            target_lift_pct=0.20,
            alpha=0.05,
            power=0.80,
            allocation=standard_allocation_dto,
            expected_daily_traffic=5000
        )
        assert params.baseline_conversion_rate == 0.025
    
    @pytest.mark.unit
    def test_design_params_dto_invalid_baseline(self, standard_allocation_dto):
        with pytest.raises(ValidationError):
            DesignParamsDTO(
                baseline_conversion_rate=1.5,  # Invalid
                mde_absolute=0.005,
                target_lift_pct=0.20,
                alpha=0.05,
                power=0.80,
                allocation=standard_allocation_dto,
                expected_daily_traffic=5000
            )

