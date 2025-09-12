"""
Centralized random number generation for reproducible simulations.

This module provides a centralized PRNG factory to ensure consistent
random number generation across all simulation components.
"""

import random
import numpy as np
from typing import Generator, Optional


class RNGFactory:
    """
    Factory for creating reproducible random number generators.
    
    This class ensures that all random number generation in the simulator
    uses the same seed and generator type for reproducibility.
    """
    
    def __init__(self, seed: int = 42):
        """
        Initialize the RNG factory with a seed.
        
        Args:
            seed: Random seed for reproducibility
        """
        self.seed = seed
        self._generators = {}
    
    def get_generator(self, name: str = "default") -> Generator:
        """
        Get a random number generator for a specific component.
        
        Args:
            name: Name of the component requesting the generator
            
        Returns:
            Random number generator instance
        """
        if name not in self._generators:
            # Create a new generator with a deterministic seed based on name
            component_seed = self._generate_component_seed(name)
            self._generators[name] = np.random.default_rng(component_seed)
        
        return self._generators[name]
    
    def _generate_component_seed(self, name: str) -> int:
        """
        Generate a deterministic seed for a component based on its name.
        
        Args:
            name: Component name
            
        Returns:
            Deterministic seed for the component
        """
        # Use hash of name to create deterministic but different seeds
        name_hash = hash(name) % (2**31)
        return (self.seed + name_hash) % (2**31)
    
    def reset(self, seed: Optional[int] = None):
        """
        Reset all generators with a new seed.
        
        Args:
            seed: New seed (uses current seed if None)
        """
        if seed is not None:
            self.seed = seed
        
        self._generators.clear()
    
    def get_state(self) -> dict:
        """
        Get the current state of all generators.
        
        Returns:
            Dictionary with generator states
        """
        return {
            name: generator.bit_generator.state for name, generator in self._generators.items()
        }
    
    def set_state(self, state: dict):
        """
        Restore the state of all generators.
        
        Args:
            state: Dictionary with generator states
        """
        for name, generator_state in state.items():
            if name in self._generators:
                self._generators[name].bit_generator.state = generator_state


# Global RNG factory instance
_rng_factory = RNGFactory()


def get_rng(name: str = "default") -> Generator:
    """
    Get a random number generator for a specific component.
    
    Args:
        name: Name of the component requesting the generator
        
    Returns:
        Random number generator instance
    """
    return _rng_factory.get_generator(name)


def set_global_seed(seed: int):
    """
    Set the global seed for all random number generation.
    
    Args:
        seed: Random seed
    """
    global _rng_factory
    _rng_factory.reset(seed)


def reset_rng():
    """
    Reset all random number generators.
    """
    global _rng_factory
    _rng_factory.reset()


def get_rng_state() -> dict:
    """
    Get the current state of all random number generators.
    
    Returns:
        Dictionary with generator states
    """
    return _rng_factory.get_state()


def set_rng_state(state: dict):
    """
    Restore the state of all random number generators.
    
    Args:
        state: Dictionary with generator states
    """
    _rng_factory.set_state(state)


def generate_bernoulli_samples(rate: float, n: int, rng_name: str = "default") -> np.ndarray:
    """
    Generate Bernoulli samples with specified rate.
    
    Args:
        rate: Success probability (0-1)
        n: Number of samples
        rng_name: Name of the RNG to use
        
    Returns:
        Array of 0s and 1s
    """
    rng = get_rng(rng_name)
    return rng.binomial(1, rate, n)


def generate_uniform_samples(low: float, high: float, n: int, rng_name: str = "default") -> np.ndarray:
    """
    Generate uniform random samples.
    
    Args:
        low: Lower bound
        high: Upper bound
        n: Number of samples
        rng_name: Name of the RNG to use
        
    Returns:
        Array of uniform random samples
    """
    rng = get_rng(rng_name)
    return rng.uniform(low, high, n)


def generate_normal_samples(mean: float, std: float, n: int, rng_name: str = "default") -> np.ndarray:
    """
    Generate normal random samples.
    
    Args:
        mean: Mean of the distribution
        std: Standard deviation
        n: Number of samples
        rng_name: Name of the RNG to use
        
    Returns:
        Array of normal random samples
    """
    rng = get_rng(rng_name)
    return rng.normal(mean, std, n)


def generate_choice_samples(choices: list, n: int, rng_name: str = "default") -> np.ndarray:
    """
    Generate random choices from a list.
    
    Args:
        choices: List of choices
        n: Number of samples
        rng_name: Name of the RNG to use
        
    Returns:
        Array of random choices
    """
    rng = get_rng(rng_name)
    return rng.choice(choices, n)


def generate_weighted_choice_samples(choices: list, weights: list, n: int, 
                                   rng_name: str = "default") -> np.ndarray:
    """
    Generate weighted random choices from a list.
    
    Args:
        choices: List of choices
        weights: List of weights (must sum to 1)
        n: Number of samples
        rng_name: Name of the RNG to use
        
    Returns:
        Array of weighted random choices
    """
    rng = get_rng(rng_name)
    return rng.choice(choices, n, p=weights)


def generate_poisson_samples(lam: float, n: int, rng_name: str = "default") -> np.ndarray:
    """
    Generate Poisson random samples.
    
    Args:
        lam: Lambda parameter (mean)
        n: Number of samples
        rng_name: Name of the RNG to use
        
    Returns:
        Array of Poisson random samples
    """
    rng = get_rng(rng_name)
    return rng.poisson(lam, n)


def generate_exponential_samples(scale: float, n: int, rng_name: str = "default") -> np.ndarray:
    """
    Generate exponential random samples.
    
    Args:
        scale: Scale parameter (1/lambda)
        n: Number of samples
        rng_name: Name of the RNG to use
        
    Returns:
        Array of exponential random samples
    """
    rng = get_rng(rng_name)
    return rng.exponential(scale, n)


def generate_beta_samples(alpha: float, beta: float, n: int, rng_name: str = "default") -> np.ndarray:
    """
    Generate beta random samples.
    
    Args:
        alpha: Alpha parameter
        beta: Beta parameter
        n: Number of samples
        rng_name: Name of the RNG to use
        
    Returns:
        Array of beta random samples
    """
    rng = get_rng(rng_name)
    return rng.beta(alpha, beta, n)


def generate_gamma_samples(shape: float, scale: float, n: int, rng_name: str = "default") -> np.ndarray:
    """
    Generate gamma random samples.
    
    Args:
        shape: Shape parameter
        scale: Scale parameter
        n: Number of samples
        rng_name: Name of the RNG to use
        
    Returns:
        Array of gamma random samples
    """
    rng = get_rng(rng_name)
    return rng.gamma(shape, scale, n)


def generate_multinomial_samples(n_trials: int, pvals: list, n: int, 
                               rng_name: str = "default") -> np.ndarray:
    """
    Generate multinomial random samples.
    
    Args:
        n_trials: Number of trials
        pvals: List of probabilities (must sum to 1)
        n: Number of samples
        rng_name: Name of the RNG to use
        
    Returns:
        Array of multinomial random samples
    """
    rng = get_rng(rng_name)
    return rng.multinomial(n_trials, pvals, n)


def generate_correlated_samples(mean: np.ndarray, cov: np.ndarray, n: int, 
                              rng_name: str = "default") -> np.ndarray:
    """
    Generate correlated multivariate normal samples.
    
    Args:
        mean: Mean vector
        cov: Covariance matrix
        n: Number of samples
        rng_name: Name of the RNG to use
        
    Returns:
        Array of correlated samples
    """
    rng = get_rng(rng_name)
    return rng.multivariate_normal(mean, cov, n)


def generate_time_series_samples(n: int, trend: float = 0, seasonality: float = 0, 
                               noise: float = 1, rng_name: str = "default") -> np.ndarray:
    """
    Generate time series samples with trend, seasonality, and noise.
    
    Args:
        n: Number of samples
        trend: Linear trend coefficient
        seasonality: Seasonal component amplitude
        noise: Noise standard deviation
        rng_name: Name of the RNG to use
        
    Returns:
        Array of time series samples
    """
    rng = get_rng(rng_name)
    
    # Generate time index
    t = np.arange(n)
    
    # Generate trend component
    trend_component = trend * t
    
    # Generate seasonal component
    seasonal_component = seasonality * np.sin(2 * np.pi * t / 12)  # 12-period seasonality
    
    # Generate noise component
    noise_component = rng.normal(0, noise, n)
    
    # Combine components
    return trend_component + seasonal_component + noise_component


def generate_mixture_samples(components: list, weights: list, n: int, 
                           rng_name: str = "default") -> np.ndarray:
    """
    Generate samples from a mixture of distributions.
    
    Args:
        components: List of (distribution_type, params) tuples
        weights: List of mixture weights (must sum to 1)
        n: Number of samples
        rng_name: Name of the RNG to use
        
    Returns:
        Array of mixture samples
    """
    rng = get_rng(rng_name)
    
    # Generate component assignments
    component_assignments = rng.choice(len(components), n, p=weights)
    
    # Generate samples from each component
    samples = np.zeros(n)
    for i, (dist_type, params) in enumerate(components):
        mask = component_assignments == i
        n_component = np.sum(mask)
        
        if n_component > 0:
            if dist_type == "normal":
                samples[mask] = rng.normal(params["mean"], params["std"], n_component)
            elif dist_type == "uniform":
                samples[mask] = rng.uniform(params["low"], params["high"], n_component)
            elif dist_type == "exponential":
                samples[mask] = rng.exponential(params["scale"], n_component)
            # Add more distribution types as needed
    
    return samples
