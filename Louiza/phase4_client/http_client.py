"""
HTTP Phase-4 Client

Calls Phase-4 anchoring service via HTTP API.
"""

import json
from typing import Optional
import requests

from .interface import AnchorClient
from .schemas import AnchorRequest, AnchorResponse


class HTTPClient:
    """
    Client that calls Phase-4 anchoring via HTTP API.
    
    Assumes Phase-4 is deployed as a service with a REST API.
    """
    
    def __init__(
        self,
        base_url: str,
        endpoint: str = "/anchor",
        timeout: int = 30,
        api_key: Optional[str] = None,
    ):
        """
        Initialize HTTP client.
        
        Args:
            base_url: Base URL of Phase-4 service (e.g., "http://localhost:8000")
            endpoint: API endpoint path (default: "/anchor")
            timeout: Request timeout in seconds
            api_key: Optional API key for authentication
        """
        self.base_url = base_url.rstrip('/')
        self.endpoint = endpoint
        self.timeout = timeout
        self.api_key = api_key
        self.headers = {"Content-Type": "application/json"}
        if api_key:
            self.headers["Authorization"] = f"Bearer {api_key}"
    
    def anchor(self, request: AnchorRequest) -> AnchorResponse:
        """
        Call Phase-4 anchoring via HTTP.
        
        Args:
            request: AnchorRequest
            
        Returns:
            AnchorResponse
        """
        url = f"{self.base_url}{self.endpoint}"
        
        request_dict = {
            "query": request.query,
            "retrieved_evidence_summary": request.retrieved_evidence_summary,
            "structured_aggregates": request.structured_aggregates or {},
            "market_target_variable": request.market_target_variable,
            "time_range": request.time_range,
            "brands": request.brands,
            "confidence": request.confidence,
            "metadata": request.metadata,
        }
        
        try:
            response = requests.post(
                url,
                json=request_dict,
                headers=self.headers,
                timeout=self.timeout,
            )
            
            response.raise_for_status()
            
            response_data = response.json()
            return AnchorResponse.from_dict(response_data)
        
        except requests.exceptions.Timeout:
            return AnchorResponse(
                anchored_score=0.0,
                calibration_details={},
                updated_confidence=request.confidence or 0.0,
                notes=[],
                warnings=[f"Phase-4 HTTP request timed out after {self.timeout}s"],
                success=False,
                error_message="Timeout",
            )
        
        except requests.exceptions.RequestException as e:
            return AnchorResponse(
                anchored_score=0.0,
                calibration_details={},
                updated_confidence=request.confidence or 0.0,
                notes=[],
                warnings=[f"Phase-4 HTTP request failed: {str(e)}"],
                success=False,
                error_message=str(e),
            )
        
        except Exception as e:
            return AnchorResponse(
                anchored_score=0.0,
                calibration_details={},
                updated_confidence=request.confidence or 0.0,
                notes=[],
                warnings=[f"Error calling Phase-4: {str(e)}"],
                success=False,
                error_message=str(e),
            )

