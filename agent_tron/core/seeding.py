"""
Deterministic seeding utilities
"""

import hashlib
from typing import Optional


def derive_seed(request_id: str, agent_id: str, provided_seed: Optional[int] = None) -> int:
    """
    Derive deterministic seed from request_id and agent_id
    If provided_seed is given, use it directly
    """
    if provided_seed is not None:
        return provided_seed
    
    # Create stable hash from request_id + agent_id
    seed_string = f"{request_id}_{agent_id}"
    seed_hash = int(hashlib.md5(seed_string.encode()).hexdigest(), 16)
    # Convert to 32-bit integer
    seed = seed_hash % (2**31)
    return seed

