"""
Enhanced tests for Streamlit UI application.
"""

import pytest


class TestStreamlitImports:
    """Test Streamlit application imports."""
    
    @pytest.mark.unit
    def test_streamlit_import(self):
        """Test that streamlit can be imported."""
        try:
            import streamlit as st
            assert st is not None
        except ImportError:
            pytest.skip("Streamlit not installed")
    
    @pytest.mark.unit
    def test_app_modules_import(self):
        """Test that app modules can be imported."""
        from core.simulate import simulate_trial
        from core.analyze import analyze_results
        from core.design import compute_sample_size
        
        assert simulate_trial is not None
        assert analyze_results is not None
        assert compute_sample_size is not None


class TestStreamlitBasicFunctionality:
    """Test basic Streamlit app functionality."""
    
    @pytest.mark.unit
    def test_mock_client_creation(self):
        """Test mock LLM client creation for UI."""
        from tests.helpers.mocks import create_mock_llm_client
        
        client = create_mock_llm_client()
        assert client is not None
        assert hasattr(client, "generate_completion")
    
    @pytest.mark.unit
    def test_ui_data_preparation(self):
        """Test UI data preparation."""
        from tests.helpers.factories import create_design_params
        from core.design import compute_sample_size
        
        params = create_design_params()
        result = compute_sample_size(params)
        
        # UI would display these values
        assert result.per_arm > 0
        assert result.days_required > 0

