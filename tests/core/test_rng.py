"""
Tests for core.rng module - Random number generation.
"""

import pytest
import numpy as np
from core.rng import get_rng, generate_bernoulli_samples, set_global_seed, reset_rng


class TestRNGDeterminism:
    """Test suite for RNG determinism."""
    
    @pytest.mark.unit
    def test_get_rng_reproducible(self):
        """Test that RNG produces same results with same component name."""
        # Set global seed and get first generator
        set_global_seed(42)
        rng1 = get_rng("test")
        values1 = rng1.random(10)
        
        # Reset and get another generator with same name and seed
        set_global_seed(42)
        rng2 = get_rng("test")
        values2 = rng2.random(10)
        
        np.testing.assert_array_equal(values1, values2)
    
    @pytest.mark.unit
    def test_generate_bernoulli_deterministic(self):
        """Test that Bernoulli samples are reproducible."""
        set_global_seed(42)
        samples1 = generate_bernoulli_samples(
            rate=0.5,
            n=100,
            rng_name="test"
        )
        
        set_global_seed(42)
        samples2 = generate_bernoulli_samples(
            rate=0.5,
            n=100,
            rng_name="test"
        )
        
        np.testing.assert_array_equal(samples1, samples2)
    
    @pytest.mark.unit
    def test_bernoulli_sample_properties(self):
        """Test that Bernoulli samples have correct properties."""
        set_global_seed(42)
        samples = generate_bernoulli_samples(
            rate=0.5,
            n=10000,
            rng_name="test"
        )
        
        # Should be binary (0 or 1)
        assert set(samples).issubset({0, 1})
        
        # Mean should be close to rate (for large n)
        assert 0.45 < np.mean(samples) < 0.55
    
    @pytest.mark.unit
    def test_different_components_different_seeds(self):
        """Test that different component names get different seeds."""
        set_global_seed(42)
        rng1 = get_rng("component_a")
        rng2 = get_rng("component_b")
        
        values1 = rng1.random(10)
        values2 = rng2.random(10)
        
        # Different components should produce different values
        assert not np.array_equal(values1, values2)


class TestDistributionGenerators:
    """Test various distribution generators."""
    
    @pytest.mark.unit
    def test_generate_uniform_samples(self):
        """Test uniform sample generation."""
        from core.rng import generate_uniform_samples, set_global_seed
        
        set_global_seed(42)
        samples = generate_uniform_samples(low=0.0, high=1.0, n=100)
        
        assert len(samples) == 100
        assert np.all(samples >= 0.0)
        assert np.all(samples <= 1.0)
    
    @pytest.mark.unit
    def test_generate_normal_samples(self):
        """Test normal sample generation."""
        from core.rng import generate_normal_samples, set_global_seed
        
        set_global_seed(42)
        samples = generate_normal_samples(mean=0.0, std=1.0, n=1000)
        
        assert len(samples) == 1000
        # Mean should be close to 0
        assert -0.1 < np.mean(samples) < 0.1
    
    @pytest.mark.unit
    def test_generate_choice_samples(self):
        """Test choice sample generation."""
        from core.rng import generate_choice_samples, set_global_seed
        
        set_global_seed(42)
        choices = ["A", "B", "C"]
        samples = generate_choice_samples(choices=choices, n=100)
        
        assert len(samples) == 100
        assert all(s in choices for s in samples)

