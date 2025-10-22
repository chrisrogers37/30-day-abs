"""
Integration tests for data export functionality.
"""

import pytest
from tests.helpers.factories import create_design_params
from core.simulate import simulate_trial


class TestDataExport:
    """Test data export workflow."""
    
    @pytest.mark.integration
    def test_user_data_export(self):
        """Test that user data can be exported."""
        params = create_design_params()
        result = simulate_trial(params, seed=42)
        
        # Should have user data if requested
        assert result.control_n > 0
        assert result.treatment_n > 0

