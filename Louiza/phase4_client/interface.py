"""
Phase-4 Anchor Client Interface

Protocol/interface for Phase-4 anchoring clients.
"""

from typing import Protocol
from .schemas import AnchorRequest, AnchorResponse


class AnchorClient(Protocol):
    """
    Protocol for Phase-4 anchoring clients.
    
    All Phase-4 client implementations must provide this method.
    """
    
    def anchor(self, request: AnchorRequest) -> AnchorResponse:
        """
        Anchor retrieval results to ground truth.
        
        Args:
            request: AnchorRequest with query, evidence, and optional parameters
            
        Returns:
            AnchorResponse with anchored score, updated confidence, etc.
        """
        ...

