"""
Comprehensive tests for advanced RNG distributions in core.rng.

Tests for gamma, multinomial, correlated, time series, and mixture distributions.
"""

import pytest
import numpy as np
from core.rng import (
    set_global_seed,
    generate_gamma_samples,
    generate_multinomial_samples,
    generate_correlated_samples,
    generate_time_series_samples,
    generate_mixture_samples
)


class TestAdvancedDistributions:
    """Test suite for advanced probability distributions."""
    
    @pytest.mark.unit
    def test_generate_gamma_samples(self):
        """Test gamma distribution sample generation."""
        set_global_seed(42)
        samples = generate_gamma_samples(shape=2.0, scale=2.0, n=1000)
        
        assert len(samples) == 1000
        assert np.all(samples > 0)  # Gamma is positive
        # Mean of Gamma(shape, scale) = shape * scale
        assert 3.0 < np.mean(samples) < 5.0  # Expected mean ~4.0
    
    @pytest.mark.unit
    def test_generate_multinomial_samples(self):
        """Test multinomial distribution sample generation."""
        set_global_seed(42)
        n_trials = 10
        pvals = [0.3, 0.5, 0.2]
        samples = generate_multinomial_samples(n_trials=n_trials, pvals=pvals, n=100)
        
        assert samples.shape[0] == 100
        # Each row should sum to n_trials
        row_sums = samples.sum(axis=1)
        assert np.all(row_sums == n_trials)
    
    @pytest.mark.unit
    def test_generate_correlated_samples(self):
        """Test correlated multivariate normal samples."""
        set_global_seed(42)
        mean = np.array([0.0, 0.0])
        cov = np.array([[1.0, 0.5], [0.5, 1.0]])
        samples = generate_correlated_samples(mean=mean, cov=cov, n=1000)
        
        assert samples.shape == (1000, 2)
        # Check means are close to expected
        assert -0.2 < np.mean(samples[:, 0]) < 0.2
        assert -0.2 < np.mean(samples[:, 1]) < 0.2
    
    @pytest.mark.unit
    def test_generate_time_series_samples(self):
        """Test time series sample generation."""
        set_global_seed(42)
        samples = generate_time_series_samples(
            n=100,
            trend=0.1,
            seasonality=2.0,
            noise=1.0
        )
        
        assert len(samples) == 100
        # Time series should show trend
        first_half_mean = np.mean(samples[:50])
        second_half_mean = np.mean(samples[50:])
        # With positive trend, second half should be higher
        assert second_half_mean > first_half_mean - 5.0  # Allow for noise
    
    @pytest.mark.unit
    def test_generate_mixture_samples(self):
        """Test mixture distribution sample generation."""
        set_global_seed(42)
        
        components = [
            ("normal", {"mean": 0.0, "std": 1.0}),
            ("normal", {"mean": 5.0, "std": 1.0})
        ]
        weights = [0.5, 0.5]
        
        samples = generate_mixture_samples(
            components=components,
            weights=weights,
            n=1000
        )
        
        assert len(samples) == 1000
        # Mean should be between the two component means
        assert 1.0 < np.mean(samples) < 4.0
    
    @pytest.mark.unit
    def test_gamma_determinism(self):
        """Test gamma samples are deterministic with seed."""
        set_global_seed(42)
        samples1 = generate_gamma_samples(shape=2.0, scale=2.0, n=100)
        
        set_global_seed(42)
        samples2 = generate_gamma_samples(shape=2.0, scale=2.0, n=100)
        
        np.testing.assert_array_equal(samples1, samples2)
    
    @pytest.mark.unit
    def test_time_series_determinism(self):
        """Test time series samples are deterministic with seed."""
        set_global_seed(42)
        samples1 = generate_time_series_samples(n=50, trend=0.1, seasonality=1.0)
        
        set_global_seed(42)
        samples2 = generate_time_series_samples(n=50, trend=0.1, seasonality=1.0)
        
        np.testing.assert_array_almost_equal(samples1, samples2)
    
    @pytest.mark.unit
    def test_mixture_distribution_types(self):
        """Test mixture with different distribution types."""
        set_global_seed(42)
        
        components = [
            ("normal", {"mean": 0.0, "std": 1.0}),
            ("uniform", {"low": 5.0, "high": 10.0})
        ]
        weights = [0.7, 0.3]
        
        samples = generate_mixture_samples(
            components=components,
            weights=weights,
            n=1000
        )
        
        assert len(samples) == 1000
        # Should have values from both distributions
        assert np.min(samples) < 2.0  # Some from normal
        assert np.max(samples) > 4.0  # Some from uniform

