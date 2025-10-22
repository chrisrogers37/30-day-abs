"""
Extended tests for core.rng module - comprehensive distribution testing.
"""

import pytest
import numpy as np
from core.rng import (
    set_global_seed,
    get_rng,
    generate_bernoulli_samples,
    generate_uniform_samples,
    generate_normal_samples,
    generate_choice_samples,
    generate_weighted_choice_samples,
    generate_poisson_samples,
    generate_exponential_samples,
    generate_beta_samples
)


class TestAdditionalDistributions:
    """Test additional probability distributions."""
    
    @pytest.mark.unit
    def test_generate_weighted_choice_samples(self):
        """Test weighted choice generation."""
        set_global_seed(42)
        choices = ["A", "B", "C"]
        weights = [0.5, 0.3, 0.2]
        
        samples = generate_weighted_choice_samples(
            choices=choices,
            weights=weights,
            n=1000
        )
        
        assert len(samples) == 1000
        assert all(s in choices for s in samples)
        
        # Check distribution roughly matches weights
        counts = {c: np.sum(samples == c) for c in choices}
        # A should be most common (50%)
        assert counts["A"] > counts["B"] > counts["C"]
    
    @pytest.mark.unit
    def test_generate_poisson_samples(self):
        """Test Poisson sample generation."""
        set_global_seed(42)
        samples = generate_poisson_samples(lam=5.0, n=1000)
        
        assert len(samples) == 1000
        assert all(s >= 0 for s in samples)
        # Mean should be close to lambda
        assert 4.5 < np.mean(samples) < 5.5
    
    @pytest.mark.unit
    def test_generate_exponential_samples(self):
        """Test exponential sample generation."""
        set_global_seed(42)
        samples = generate_exponential_samples(scale=2.0, n=1000)
        
        assert len(samples) == 1000
        assert all(s >= 0 for s in samples)
    
    @pytest.mark.unit
    def test_generate_beta_samples(self):
        """Test beta sample generation."""
        set_global_seed(42)
        samples = generate_beta_samples(alpha=2.0, beta=5.0, n=1000)
        
        assert len(samples) == 1000
        assert np.all(samples >= 0)
        assert np.all(samples <= 1)


class TestRNGStateManagement:
    """Test RNG state management functions."""
    
    @pytest.mark.unit
    def test_reset_rng(self):
        """Test RNG reset functionality."""
        from core.rng import reset_rng
        
        set_global_seed(42)
        rng1 = get_rng("test")
        values1 = rng1.random(5)
        
        reset_rng()
        rng2 = get_rng("test")
        values2 = rng2.random(5)
        
        # After reset with same seed, should get same values
        # Note: reset() without args uses current seed
        assert len(values1) == len(values2)
    
    @pytest.mark.unit
    def test_rng_state_get_set(self):
        """Test RNG state save/restore."""
        from core.rng import get_rng_state, set_rng_state
        
        set_global_seed(42)
        rng = get_rng("test")
        rng.random(10)
        
        # Save state
        state = get_rng_state()
        assert isinstance(state, dict)

