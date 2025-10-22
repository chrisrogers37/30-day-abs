"""
Tests for Jupyter notebook templates.
"""

import pytest
import os


class TestNotebookTemplates:
    """Test notebook template validity."""
    
    @pytest.mark.unit
    def test_design_template_exists(self):
        """Test that design template notebook exists."""
        template_path = "notebooks/ab_test_design_template.ipynb"
        assert os.path.exists(template_path)
    
    @pytest.mark.unit
    def test_analysis_template_exists(self):
        """Test that analysis template notebook exists."""
        template_path = "notebooks/ab_experimental_analysis_template.ipynb"
        assert os.path.exists(template_path)

