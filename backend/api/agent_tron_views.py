"""
Django views for Agent-Tron endpoints.

This replaces the FastAPI server with native Django views.
All Agent-Tron functionality is now integrated directly into Django.
"""

import logging
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from typing import Dict, Any, List, Optional

# Import Agent-Tron core components
import sys
import os
from pathlib import Path

# Add project root to path for Agent-Tron imports
current_file = Path(__file__).resolve()
project_root = current_file.parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from agent_tron.core.handler import DecisionHandler
from agent_tron.aggregation.aggregate import aggregate_responses
from agent_tron.schemas.request import (
    PersonaDecisionRequest, BatchRequest, Persona, Demographics, Psychographics,
    Context, Constraints
)
from agent_tron.schemas.response import PersonaDecisionResponse

logger = logging.getLogger(__name__)

# Singleton handler instance (lazy loaded)
_handler: Optional[DecisionHandler] = None


def get_handler() -> DecisionHandler:
    """Get or create DecisionHandler instance."""
    global _handler
    if _handler is None:
        logger.info("Initializing Agent-Tron DecisionHandler...")
        _handler = DecisionHandler()
        logger.info("✓ Agent-Tron DecisionHandler initialized")
    return _handler


class AgentTronViewSet(viewsets.ViewSet):
    """
    Django ViewSet for Agent-Tron endpoints.
    Replaces the FastAPI server with native Django REST Framework views.
    """
    
    @action(detail=False, methods=['get'])
    def health(self, request):
        """Health check endpoint."""
        return Response({
            "service": "Agent-Tron",
            "version": "1.0.0",
            "description": "API layer for grounded LPM decision-making",
            "status": "operational"
        })
    
    @action(detail=False, methods=['post'])
    def persona_decision(self, request):
        """
        Single agent decision endpoint.
        
        Accepts JSON with:
        - request_id: str
        - hypothesis: str
        - question_type: str ("comparison", "what_if", "forecast", "preference")
        - persona: dict with agent_id, archetype, demographics, psychographics
        - context: dict (optional)
        - constraints: dict (optional)
        - seed: int (optional)
        - num_samples: int (optional, default=1)
        
        Returns PersonaDecisionResponse dict.
        """
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['request_id', 'hypothesis', 'question_type', 'persona']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {'error': f'Missing required field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Build PersonaDecisionRequest from Django request data
            persona_data = data['persona']
            persona = Persona(
                agent_id=persona_data['agent_id'],
                archetype=persona_data['archetype'],
                demographics=Demographics(**persona_data['demographics']),
                psychographics=Psychographics(**persona_data['psychographics']),
                traits=persona_data.get('traits', {})
            )
            
            # Build context
            context_data = data.get('context', {})
            context = Context(**context_data)
            
            # Build constraints
            constraints_data = data.get('constraints', {})
            constraints = Constraints(**constraints_data)
            
            # Build request
            agent_request = PersonaDecisionRequest(
                request_id=data['request_id'],
                hypothesis=data['hypothesis'],
                question_type=data['question_type'],
                time_horizon=data.get('time_horizon'),
                persona=persona,
                context=context,
                constraints=constraints,
                seed=data.get('seed'),
                num_samples=data.get('num_samples', 1)
            )
            
            # Process request
            handler = get_handler()
            response = handler.process_request(agent_request)
            
            # Convert Pydantic model to dict for JSON response
            response_dict = response.dict()
            
            logger.info(
                f"Agent-Tron decision: {response.sampled_decision.choice} "
                f"(confidence: {response.uncertainty.confidence:.2f})"
            )
            
            return Response(response_dict, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Agent-Tron validation error: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Agent-Tron internal error: {e}", exc_info=True)
            return Response(
                {'error': f'Internal error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def batch_decisions(self, request):
        """
        Batch decisions endpoint.
        
        Accepts JSON with:
        - request_id: str
        - hypothesis: str
        - question_type: str
        - personas: list of persona dicts
        - context: dict (optional)
        - constraints: dict (optional)
        - seed: int (optional)
        
        Returns list of PersonaDecisionResponse dicts.
        """
        try:
            data = request.data
            
            # Validate required fields
            required_fields = ['request_id', 'hypothesis', 'question_type', 'personas']
            for field in required_fields:
                if field not in data:
                    return Response(
                        {'error': f'Missing required field: {field}'},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Build BatchRequest
            personas_list = []
            for persona_data in data['personas']:
                persona = Persona(
                    agent_id=persona_data['agent_id'],
                    archetype=persona_data['archetype'],
                    demographics=Demographics(**persona_data['demographics']),
                    psychographics=Psychographics(**persona_data['psychographics']),
                    traits=persona_data.get('traits', {})
                )
                personas_list.append(persona)
            
            context = Context(**data.get('context', {}))
            constraints = Constraints(**data.get('constraints', {}))
            
            batch_request = BatchRequest(
                request_id=data['request_id'],
                hypothesis=data['hypothesis'],
                question_type=data['question_type'],
                time_horizon=data.get('time_horizon'),
                personas=personas_list,
                context=context,
                constraints=constraints,
                seed=data.get('seed')
            )
            
            # Process each persona
            handler = get_handler()
            responses = []
            
            for persona in batch_request.personas:
                individual_request = PersonaDecisionRequest(
                    request_id=f"{batch_request.request_id}_{persona.agent_id}",
                    hypothesis=batch_request.hypothesis,
                    question_type=batch_request.question_type,
                    time_horizon=batch_request.time_horizon,
                    persona=persona,
                    constraints=batch_request.constraints,
                    context=batch_request.context,
                    seed=batch_request.seed
                )
                
                response = handler.process_request(individual_request)
                responses.append(response.dict())
            
            logger.info(f"Agent-Tron batch: processed {len(responses)} personas")
            
            return Response(responses, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Agent-Tron batch validation error: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Agent-Tron batch internal error: {e}", exc_info=True)
            return Response(
                {'error': f'Internal error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    @action(detail=False, methods=['post'])
    def aggregate(self, request):
        """
        Aggregation endpoint.
        
        Accepts JSON list of PersonaDecisionResponse dicts.
        Returns AggregateResponse dict with executive summary.
        """
        try:
            data = request.data
            
            if not isinstance(data, list):
                return Response(
                    {'error': 'Expected list of PersonaDecisionResponse objects'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not data:
                return Response(
                    {'error': 'Cannot aggregate empty list'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Convert dicts to Pydantic models
            responses = [PersonaDecisionResponse(**item) for item in data]
            
            # Aggregate
            aggregated = aggregate_responses(responses)
            
            # Convert to dict for JSON response
            result = aggregated.dict()
            
            logger.info(f"Agent-Tron aggregation: {aggregated.agents_tested} agents")
            
            return Response(result, status=status.HTTP_200_OK)
            
        except ValueError as e:
            logger.error(f"Agent-Tron aggregation validation error: {e}", exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Agent-Tron aggregation internal error: {e}", exc_info=True)
            return Response(
                {'error': f'Internal error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

