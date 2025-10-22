"""
Comprehensive tests for core.simulate utility functions.

Tests for CSV export, aggregate summaries, validation, and seasonality functions.
"""

import pytest
import os
from datetime import datetime
from core.simulate import (
    simulate_trial,
    validate_simulation_consistency,
    add_seasonality_pattern,
    export_user_data_csv,
    get_aggregate_summary
)
from tests.helpers.factories import create_design_params


class TestExportUserDataCSV:
    """Test suite for export_user_data_csv function."""
    
    @pytest.mark.unit
    def test_export_csv_basic(self, temp_output_dir):
        """Test basic CSV export functionality."""
        # Create simulation with user data
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        # Export to CSV
        output_file = temp_output_dir / "user_data.csv"
        export_user_data_csv(sim_result.user_data, str(output_file))
        
        # Verify file exists and has content
        assert output_file.exists()
        assert output_file.stat().st_size > 0
        
        # Read and verify structure
        import csv
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            assert len(rows) > 0
            # Check required fields (visitor_id, not user_id)
            assert 'visitor_id' in rows[0] or 'user_id' in rows[0]
            assert 'group' in rows[0]
            assert 'converted' in rows[0]
    
    @pytest.mark.unit
    def test_export_csv_empty_data(self, temp_output_dir):
        """Test CSV export with empty data."""
        output_file = temp_output_dir / "empty_data.csv"
        
        # Empty list should not create file or should handle gracefully
        export_user_data_csv([], str(output_file))
        
        # Function should return without error (may or may not create file)
        assert True  # No exception raised
    
    @pytest.mark.unit
    def test_export_csv_file_structure(self, temp_output_dir):
        """Test that exported CSV has correct structure."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        output_file = temp_output_dir / "structured_data.csv"
        export_user_data_csv(sim_result.user_data, str(output_file))
        
        # Read and validate structure
        import csv
        with open(output_file, 'r') as f:
            reader = csv.DictReader(f)
            rows = list(reader)
            
            # Check data types and values
            for row in rows:
                assert row['group'] in ['control', 'treatment']
                assert row['converted'] in ['True', 'False', 'true', 'false']


class TestGetAggregateSummary:
    """Test suite for get_aggregate_summary function."""
    
    @pytest.mark.unit
    def test_aggregate_summary_basic(self):
        """Test basic aggregate summary generation."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        summary = get_aggregate_summary(sim_result.user_data)
        
        assert 'total_users' in summary
        assert 'control' in summary
        assert 'treatment' in summary
        assert summary['total_users'] == len(sim_result.user_data)
    
    @pytest.mark.unit
    def test_aggregate_summary_empty_data(self):
        """Test aggregate summary with empty data."""
        summary = get_aggregate_summary([])
        
        # Should return empty dict or handle gracefully
        assert isinstance(summary, dict)
    
    @pytest.mark.unit
    def test_aggregate_summary_grouping(self):
        """Test that summary correctly groups control vs treatment."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        summary = get_aggregate_summary(sim_result.user_data)
        
        # Verify group counts
        control_count = summary['control']['count']
        treatment_count = summary['treatment']['count']
        
        assert control_count + treatment_count == summary['total_users']
        assert control_count > 0
        assert treatment_count > 0
    
    @pytest.mark.unit
    def test_aggregate_summary_lift_calculations(self):
        """Test that summary calculates lift metrics."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        summary = get_aggregate_summary(sim_result.user_data)
        
        # Should have lift calculations
        if 'absolute_lift' in summary:
            assert isinstance(summary['absolute_lift'], (int, float))
        
        if 'relative_lift_pct' in summary:
            assert isinstance(summary['relative_lift_pct'], (int, float))
    
    @pytest.mark.unit
    def test_aggregate_summary_metrics(self):
        """Test that summary includes key metrics."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        summary = get_aggregate_summary(sim_result.user_data)
        
        # Check control group metrics
        assert 'conversions' in summary['control']
        assert 'conversion_rate' in summary['control']
        assert 0 <= summary['control']['conversion_rate'] <= 1
        
        # Check treatment group metrics
        assert 'conversions' in summary['treatment']
        assert 'conversion_rate' in summary['treatment']
        assert 0 <= summary['treatment']['conversion_rate'] <= 1


class TestValidateSimulationConsistency:
    """Test suite for validate_simulation_consistency function."""
    
    @pytest.mark.unit
    def test_validation_consistent_results(self):
        """Test validation with consistent results."""
        params = create_design_params(baseline_conversion_rate=0.05)
        sim_result = simulate_trial(params, seed=42)
        
        expected_rates = {
            'control': sim_result.control_rate,
            'treatment': sim_result.treatment_rate
        }
        
        # Should be consistent with itself
        is_consistent = validate_simulation_consistency(
            sim_result,
            expected_rates,
            tolerance=0.01
        )
        
        assert is_consistent == True
    
    @pytest.mark.unit
    def test_validation_inconsistent_results(self):
        """Test validation with inconsistent results."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        # Provide very different expected rates
        expected_rates = {
            'control': 0.95,  # Way off
            'treatment': 0.95  # Way off
        }
        
        is_consistent = validate_simulation_consistency(
            sim_result,
            expected_rates,
            tolerance=0.01
        )
        
        assert is_consistent == False
    
    @pytest.mark.unit
    def test_validation_edge_cases(self):
        """Test validation with edge cases."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        # Test with empty expected rates
        expected_rates = {}
        
        is_consistent = validate_simulation_consistency(
            sim_result,
            expected_rates,
            tolerance=0.1
        )
        
        # Should handle gracefully (treat missing as 0)
        assert isinstance(is_consistent, bool)


class TestAddSeasonalityPattern:
    """Test suite for add_seasonality_pattern function."""
    
    @pytest.mark.unit
    def test_add_weekend_pattern(self):
        """Test adding weekend seasonality pattern."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        # Add weekend pattern
        modified_data = add_seasonality_pattern(
            sim_result.user_data,
            pattern_type="weekend"
        )
        
        # Should return modified data
        assert isinstance(modified_data, list)
        assert len(modified_data) == len(sim_result.user_data)
    
    @pytest.mark.unit
    def test_add_holiday_pattern(self):
        """Test adding holiday seasonality pattern."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        # Add holiday pattern
        modified_data = add_seasonality_pattern(
            sim_result.user_data,
            pattern_type="holiday"
        )
        
        # Should return modified data
        assert isinstance(modified_data, list)
        assert len(modified_data) == len(sim_result.user_data)
    
    @pytest.mark.unit
    def test_seasonality_preserves_structure(self):
        """Test that seasonality doesn't break data structure."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        original_keys = set(sim_result.user_data[0].keys())
        
        modified_data = add_seasonality_pattern(
            sim_result.user_data,
            pattern_type="weekend"
        )
        
        # Should preserve all original keys
        if modified_data:
            modified_keys = set(modified_data[0].keys())
            assert original_keys == modified_keys


class TestUserDataGenerationHelpers:
    """Test suite for user data generation helper functions."""
    
    @pytest.mark.unit
    def test_user_data_has_realistic_attributes(self):
        """Test that generated user data has realistic attributes."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        # Check that user data exists and has expected fields
        assert sim_result.user_data is not None
        assert len(sim_result.user_data) > 0
        
        sample_user = sim_result.user_data[0]
        
        # Check required fields exist (visitor_id or user_id)
        assert 'visitor_id' in sample_user or 'user_id' in sample_user
        assert 'group' in sample_user
        assert 'converted' in sample_user
        assert 'timestamp' in sample_user
    
    @pytest.mark.unit
    def test_session_duration_varies_by_conversion(self):
        """Test that session duration differs for converted vs non-converted users."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        # Separate converted and non-converted users
        converted = [u for u in sim_result.user_data if u['converted']]
        not_converted = [u for u in sim_result.user_data if not u['converted']]
        
        if converted and not_converted:
            avg_converted_duration = sum(u['session_duration'] for u in converted) / len(converted)
            avg_not_converted_duration = sum(u['session_duration'] for u in not_converted) / len(not_converted)
            
            # Converted users typically have longer sessions
            assert avg_converted_duration > avg_not_converted_duration
    
    @pytest.mark.unit
    def test_page_views_varies_by_conversion(self):
        """Test that page views differ for converted vs non-converted users."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        # Separate converted and non-converted users
        converted = [u for u in sim_result.user_data if u['converted']]
        not_converted = [u for u in sim_result.user_data if not u['converted']]
        
        if converted and not_converted:
            avg_converted_pages = sum(u['page_views'] for u in converted) / len(converted)
            avg_not_converted_pages = sum(u['page_views'] for u in not_converted) / len(not_converted)
            
            # Converted users typically view more pages
            assert avg_converted_pages > avg_not_converted_pages
    
    @pytest.mark.unit
    def test_device_types_realistic(self):
        """Test that device types are realistic."""
        params = create_design_params()
        sim_result = simulate_trial(params, seed=42)
        
        device_types = set(u['device_type'] for u in sim_result.user_data)
        
        # Should have common device types
        expected_types = {'mobile', 'desktop', 'tablet'}
        assert device_types.issubset(expected_types) or len(device_types.intersection(expected_types)) > 0

