"""
FastAPI server for Agent-Tron
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from ..schemas.request import PersonaDecisionRequest, BatchRequest
from ..schemas.response import PersonaDecisionResponse, AggregateResponse
from ..core.handler import DecisionHandler
from ..aggregation.aggregate import aggregate_responses

app = FastAPI(
    title="Agent-Tron API",
    description="API layer for grounded LPM decision-making",
    version="1.0.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize handler (lazy loaded)
_handler: DecisionHandler = None


def get_handler() -> DecisionHandler:
    """Get or create handler instance"""
    global _handler
    if _handler is None:
        _handler = DecisionHandler()
    return _handler


@app.get("/")
def root():
    """Root endpoint"""
    return {
        "service": "Agent-Tron",
        "version": "1.0.0",
        "description": "API layer for grounded LPM decision-making"
    }


@app.post("/agent_tron/persona_decision", response_model=PersonaDecisionResponse)
def persona_decision(request: PersonaDecisionRequest) -> PersonaDecisionResponse:
    """
    Single agent decision endpoint
    Accepts persona JSON + hypothesis/context JSON
    Returns decision with population prior, conditioned distribution, sampled decision,
    dominant drivers, entropy/confidence, and phase-4 evidence references
    """
    try:
        handler = get_handler()
        response = handler.process_request(request)
        return response
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/agent_tron/batch_decisions", response_model=List[PersonaDecisionResponse])
def batch_decisions(request: BatchRequest) -> List[PersonaDecisionResponse]:
    """
    Batch decisions endpoint
    Accepts multiple personas with shared hypothesis/context
    Returns list of PersonaDecisionResponse
    """
    try:
        handler = get_handler()
        responses = []
        
        for persona in request.personas:
            # Create individual request for each persona
            individual_request = PersonaDecisionRequest(
                request_id=f"{request.request_id}_{persona.agent_id}",
                hypothesis=request.hypothesis,
                question_type=request.question_type,
                time_horizon=request.time_horizon,
                persona=persona,
                constraints=request.constraints,
                context=request.context,
                seed=request.seed
            )
            
            response = handler.process_request(individual_request)
            responses.append(response)
        
        return responses
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


@app.post("/agent_tron/aggregate", response_model=AggregateResponse)
def aggregate(responses: List[PersonaDecisionResponse]) -> AggregateResponse:
    """
    Aggregation endpoint
    Accepts list of PersonaDecisionResponse
    Returns executive summary JSON with:
    - agents_tested
    - preference breakdown
    - segment insights (by archetype)
    - top drivers (counts/weights)
    - overall entropy/confidence (weighted)
    - evidence coverage stats
    """
    try:
        aggregated = aggregate_responses(responses)
        return aggregated
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal error: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.getenv("AGENT_TRON_PORT", "8001"))
    uvicorn.run(app, host="0.0.0.0", port=port)

