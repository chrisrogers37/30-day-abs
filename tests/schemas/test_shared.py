"""Tests for schemas.shared module."""
import pytest
from schemas.shared import AllocationDTO, CompanyType, UserSegment

class TestAllocationDTO:
    @pytest.mark.unit
    def test_allocation_dto_valid(self, standard_allocation_dto):
        assert standard_allocation_dto.control == 0.5
        assert standard_allocation_dto.treatment == 0.5

class TestEnums:
    @pytest.mark.unit
    def test_company_types(self):
        assert CompanyType.ECOMMERCE == "E-commerce"
        assert CompanyType.SAAS == "SaaS"
    
    @pytest.mark.unit
    def test_user_segments(self):
        assert UserSegment.ALL_USERS == "all_users"
        assert UserSegment.NEW_USERS == "new_users"

