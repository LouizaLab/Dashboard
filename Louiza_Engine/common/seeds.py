"""
Seed management for reproducible randomness.

All randomness in the system must be seeded and reproducible.
"""

import numpy as np
from typing import Optional


class SeedManager:
    """Manages random seeds for reproducibility."""
    
    def __init__(self, base_seed: int):
        """
        Initialize seed manager with a base seed.
        
        Args:
            base_seed: Base seed for the entire run
        """
        self.base_seed = base_seed
        self._rng = np.random.default_rng(base_seed)
    
    def get_seed(self, component: str, index: Optional[int] = None) -> int:
        """
        Get a deterministic seed for a component.
        
        Args:
            component: Component name (e.g., 'ibde', 'lpm_sampling')
            index: Optional index for multiple seeds per component
        
        Returns:
            Deterministic seed value
        """
        # Create a hash-based seed from component name and index
        seed_value = hash((self.base_seed, component, index))
        # Ensure positive seed
        return abs(seed_value) % (2**31)
    
    def get_rng(self, component: str, index: Optional[int] = None) -> np.random.Generator:
        """
        Get a numpy RNG for a component.
        
        Args:
            component: Component name
            index: Optional index
        
        Returns:
            Seeded numpy RNG
        """
        seed = self.get_seed(component, index)
        return np.random.default_rng(seed)

