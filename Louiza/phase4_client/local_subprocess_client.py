"""
Local Subprocess Phase-4 Client

Runs Phase-4 anchoring code via subprocess by calling an external script.
"""

import json
import subprocess
import os
from typing import Optional
from pathlib import Path

from .interface import AnchorClient
from .schemas import AnchorRequest, AnchorResponse


class LocalSubprocessClient:
    """
    Client that runs Phase-4 anchoring via subprocess.
    
    Assumes Phase-4 code is in another repo/codebase and can be invoked
    via a command-line entrypoint.
    """
    
    def __init__(
        self,
        phase4_repo_path: str,
        entrypoint_command: str = "python -m phase4.anchor",
        timeout: int = 60,
    ):
        """
        Initialize subprocess client.
        
        Args:
            phase4_repo_path: Path to Phase-4 repository/codebase
            entrypoint_command: Command to run (e.g., "python -m phase4.anchor")
            timeout: Timeout in seconds for subprocess execution
        """
        self.phase4_repo_path = Path(phase4_repo_path)
        if not self.phase4_repo_path.exists():
            raise ValueError(f"Phase-4 repo path does not exist: {phase4_repo_path}")
        
        self.entrypoint_command = entrypoint_command.split()
        self.timeout = timeout
    
    def anchor(self, request: AnchorRequest) -> AnchorResponse:
        """
        Call Phase-4 anchoring via subprocess.
        
        Args:
            request: AnchorRequest
            
        Returns:
            AnchorResponse
        """
        # Create temporary JSON file with request
        import tempfile
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
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
            json.dump(request_dict, f)
            request_file = f.name
        
        try:
            # Run Phase-4 command
            cmd = self.entrypoint_command + [request_file]
            result = subprocess.run(
                cmd,
                cwd=str(self.phase4_repo_path),
                capture_output=True,
                text=True,
                timeout=self.timeout,
            )
            
            if result.returncode != 0:
                return AnchorResponse(
                    anchored_score=0.0,
                    calibration_details={},
                    updated_confidence=request.confidence or 0.0,
                    notes=[],
                    warnings=[f"Phase-4 subprocess failed with return code {result.returncode}"],
                    success=False,
                    error_message=result.stderr,
                )
            
            # Parse response from stdout (should be JSON)
            try:
                response_data = json.loads(result.stdout)
                return AnchorResponse.from_dict(response_data)
            except json.JSONDecodeError:
                # Try to read from a response file if stdout is not JSON
                # (some implementations might write to a file)
                response_file = request_file.replace('.json', '_response.json')
                if os.path.exists(response_file):
                    with open(response_file, 'r') as f:
                        response_data = json.load(f)
                    return AnchorResponse.from_dict(response_data)
                else:
                    return AnchorResponse(
                        anchored_score=0.0,
                        calibration_details={},
                        updated_confidence=request.confidence or 0.0,
                        notes=[],
                        warnings=["Could not parse Phase-4 response"],
                        success=False,
                        error_message=f"Invalid JSON response: {result.stdout[:200]}",
                    )
        
        except subprocess.TimeoutExpired:
            return AnchorResponse(
                anchored_score=0.0,
                calibration_details={},
                updated_confidence=request.confidence or 0.0,
                notes=[],
                warnings=[f"Phase-4 subprocess timed out after {self.timeout}s"],
                success=False,
                error_message="Timeout",
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
        
        finally:
            # Clean up temp file
            if os.path.exists(request_file):
                os.unlink(request_file)

