"""
Orchestration handler for Agent-Tron
Coordinates LPM calls and builds responses
"""

from typing import Dict
import os
import logging

logger = logging.getLogger(__name__)

from ..schemas.request import PersonaDecisionRequest
from ..schemas.response import (
    PersonaDecisionResponse, DecisionSample, Uncertainty, EvidenceItem, SampledResponse
)
from .lpm_adapter import LPMAdapter
from .seeding import derive_seed
from .evidence_retriever import EvidenceRetriever
from ..utils.validation import (
    validate_distribution, compute_entropy, compute_confidence, extract_dominant_drivers
)


class DecisionHandler:
    """Handles persona decision requests"""
    
    def __init__(self, 
                 phase1_checkpoint: str = 'checkpoints/best_model.pt',
                 phase2_checkpoint: str = 'checkpoints_phase2/best_model_phase2.pt',
                 data_dir: str = 'data'):
        """Initialize handler with LPM adapter"""
        # Use absolute path for checkpoints
        # Get project root (go up from agent_tron/core/handler.py to project root)
        current_file = os.path.abspath(__file__)
        # agent_tron/core/handler.py -> agent_tron/core -> agent_tron -> project root
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(current_file)))
        base_dir = os.path.join(project_root, '4_phases')
        
        self.phase1_checkpoint = os.path.join(base_dir, phase1_checkpoint) if not os.path.isabs(phase1_checkpoint) else phase1_checkpoint
        self.phase2_checkpoint = os.path.join(base_dir, phase2_checkpoint) if not os.path.isabs(phase2_checkpoint) else phase2_checkpoint
        self.data_dir = os.path.join(base_dir, data_dir) if not os.path.isabs(data_dir) else data_dir
        
        self.adapter = LPMAdapter(
            phase1_checkpoint=self.phase1_checkpoint,
            phase2_checkpoint=self.phase2_checkpoint,
            data_dir=self.data_dir
        )
        
        # Initialize evidence retriever
        try:
            print("[DecisionHandler] Initializing EvidenceRetriever...")
            self.evidence_retriever = EvidenceRetriever()
            if self.evidence_retriever and self.evidence_retriever.data_engine:
                logger.info("✓ Evidence retriever initialized successfully with Data Engine")
                print("[DecisionHandler] ✓ Evidence retriever initialized successfully with Data Engine")
            elif self.evidence_retriever:
                logger.warning("⚠ Evidence retriever initialized but Data Engine is None - evidence retrieval will return empty")
                print("[DecisionHandler] ⚠ Evidence retriever initialized but Data Engine is None")
            else:
                logger.warning("⚠ Evidence retriever initialization returned None")
                print("[DecisionHandler] ⚠ Evidence retriever initialization returned None")
        except Exception as e:
            logger.warning(f"Failed to initialize evidence retriever: {e}", exc_info=True)
            print(f"[DecisionHandler] ❌ Failed to initialize evidence retriever: {e}")
            import traceback
            traceback.print_exc()
            self.evidence_retriever = None
    
    def process_request(self, request: PersonaDecisionRequest) -> PersonaDecisionResponse:
        """
        Process persona decision request
        Returns: PersonaDecisionResponse
        """
        # Determine seed
        seed = derive_seed(
            request_id=request.request_id,
            agent_id=request.persona.agent_id,
            provided_seed=request.seed
        )
        
        # Convert persona to dict format
        persona_dict = {
            'archetype': request.persona.archetype,
            'demographics': request.persona.demographics.dict(),
            'psychographics': request.persona.psychographics.dict()
        }
        
        # Convert context to dict format
        context_dict = request.context.dict()
        
        # Step 1: Get population prior
        try:
            prior = self.adapter.get_prior(
                archetype=request.persona.archetype,
                context=context_dict
            )
            validate_distribution(prior)
            logger.info(f"[LPM] Agent {request.persona.agent_id}: Got population prior with {len(prior)} products, top 3: {sorted(prior.items(), key=lambda x: x[1], reverse=True)[:3]}")
            print(f"[LPM] Agent {request.persona.agent_id}: Population prior has {len(prior)} products")
        except Exception as e:
            raise ValueError(f"Failed to get population prior: {str(e)}")
        
        # Step 2: Condition on persona and context
        try:
            conditioned = self.adapter.condition(
                prior=prior,
                persona=persona_dict,
                context=context_dict
            )
            validate_distribution(conditioned)
            top_3_conditioned = sorted(conditioned.items(), key=lambda x: x[1], reverse=True)[:3]
            logger.info(f"[LPM] Agent {request.persona.agent_id}: Conditioned distribution top 3: {top_3_conditioned}")
            print(f"[LPM] Agent {request.persona.agent_id}: Conditioned distribution top 3: {[(p, f'{prob:.3f}') for p, prob in top_3_conditioned]}")
        except Exception as e:
            raise ValueError(f"Failed to condition distribution: {str(e)}")
        
        # Step 3: Sample decision(s)
        num_samples = getattr(request, 'num_samples', 1) or 1
        
        try:
            # Primary sample (for backward compatibility)
            sampled_product_id, sampled_prob = self.adapter.sample(
                distribution=conditioned,
                seed=seed
            )
            logger.info(f"[LPM] Agent {request.persona.agent_id}: Sampled decision: {sampled_product_id} (prob: {sampled_prob:.4f}, seed: {seed})")
            print(f"[LPM] ✓ Agent {request.persona.agent_id}: Sampled {sampled_product_id} with prob {sampled_prob:.4f}")
            
            # Generate multiple samples if requested
            sampled_responses = []
            if num_samples > 1:
                import numpy as np
                # Import derive_seed at module level scope
                from .seeding import derive_seed as derive_seed_func
                for i in range(num_samples - 1):  # -1 because we already have primary sample
                    # Use different seed for each sample (deterministic but varied)
                    sample_seed = seed + i + 1 if seed is not None else None
                    if sample_seed is None:
                        # Derive seed from request_id + agent_id + sample index
                        sample_seed = derive_seed_func(
                            request_id=f"{request.request_id}_sample_{i+1}",
                            agent_id=request.persona.agent_id,
                            provided_seed=None
                        )
                    
                    sample_product_id, sample_prob = self.adapter.sample(
                        distribution=conditioned,
                        seed=sample_seed
                    )
                    sampled_responses.append(SampledResponse(
                        sample_id=i + 1,
                        choice=sample_product_id,
                        probability=float(sample_prob),
                        seed=sample_seed
                    ))
        except Exception as e:
            raise ValueError(f"Failed to sample decision: {str(e)}")
        
        # Step 4: Build LPM outputs for evidence grounding
        lpm_outputs = {
            'sampled_decision': {
                'choice': sampled_product_id,
                'probability': float(sampled_prob)
            },
            'conditioned_distribution': conditioned,
            'population_prior': prior
        }
        
        # Step 5: Get Phase 4 grounding (legacy)
        try:
            grounding_result = self.adapter.grounding(
                hypothesis=request.hypothesis,
                persona=persona_dict,
                context=context_dict
            )
        except Exception as e:
            # Don't fail if grounding fails, just use empty evidence
            grounding_result = {'evidence_items': []}
        
        # Step 6: Retrieve Data Engine evidence (persona-specific, LPM-grounded)
        data_engine_evidence = []
        if self.evidence_retriever:
            try:
                print(f"[Handler] Calling evidence retriever for agent {request.persona.agent_id}")
                print(f"[Handler] Evidence retriever.data_engine is None: {self.evidence_retriever.data_engine is None}")
                logger.info(f"Calling evidence retriever for agent {request.persona.agent_id}, hypothesis: {request.hypothesis[:100]}")
                logger.info(f"DEBUG: evidence_retriever.data_engine is None: {self.evidence_retriever.data_engine is None}")
                data_engine_evidence = self.evidence_retriever.retrieve_evidence(
                    persona=persona_dict,
                    hypothesis=request.hypothesis,
                    lpm_outputs=lpm_outputs,
                    context=context_dict
                )
                evidence_ids = [item.get('evidence_id', 'unknown') for item in data_engine_evidence]
                print(f"[Handler] Evidence retriever returned {len(data_engine_evidence)} evidence items")
                logger.info(f"Evidence retriever returned {len(data_engine_evidence)} evidence items for agent {request.persona.agent_id}")
                logger.info(f"Agent {request.persona.agent_id} evidence IDs: {[eid[:24] + '...' for eid in evidence_ids[:5]]}")
                print(f"[Handler] Agent {request.persona.agent_id}: Evidence IDs (first 3): {[eid[:20] + '...' for eid in evidence_ids[:3]]}")
            except Exception as e:
                print(f"[Handler] ❌ Data Engine evidence retrieval failed: {e}")
                import traceback
                traceback.print_exc()
                logger.error(f"Data Engine evidence retrieval failed: {e}", exc_info=True)
                data_engine_evidence = []
        else:
            print(f"[Handler] ⚠️ Evidence retriever not available for agent {request.persona.agent_id}")
            logger.warning(f"Evidence retriever not available for agent {request.persona.agent_id}")
            logger.warning(f"DEBUG: self.evidence_retriever is None: {self.evidence_retriever is None}")
        
        # Step 7: Compute uncertainty metrics
        entropy = compute_entropy(conditioned)
        confidence = compute_confidence(conditioned)
        
        # Step 8: Extract dominant drivers
        dominant_drivers = extract_dominant_drivers(conditioned, top_k=5)
        
        # Step 9: Build alternatives dict (top alternatives excluding sampled)
        alternatives = {}
        sorted_items = sorted(conditioned.items(), key=lambda x: x[1], reverse=True)
        for product_id, prob in sorted_items[:5]:
            if product_id != sampled_product_id:
                alternatives[product_id] = float(prob)
        
        # Step 10: Combine evidence items (Phase 4 + Data Engine)
        evidence_items = []
        
        # Add Phase 4 evidence first
        phase4_evidence = grounding_result.get('evidence_items', [])
        logger.info(f"DEBUG: Phase 4 evidence count: {len(phase4_evidence)}")
        for item in phase4_evidence:
            evidence_items.append(EvidenceItem(
                evidence_id=item.get('evidence_id', ''),
                source_type=item.get('source_type', 'unknown'),
                title=item.get('title'),
                date=item.get('date'),
                region=item.get('region'),
                sample_size=item.get('sample_size'),
                excerpt=item.get('excerpt'),
                tags=item.get('tags', []),
                weight=item.get('weight')
            ))
        
        # Add Data Engine evidence (persona-specific, LPM-grounded)
        logger.info(f"DEBUG: Data Engine evidence count: {len(data_engine_evidence)}")
        for item in data_engine_evidence:
            evidence_items.append(EvidenceItem(
                evidence_id=item.get('evidence_id', ''),
                source_type=item.get('source_type', 'survey_interview'),
                title=item.get('title'),
                date=item.get('date'),
                region=item.get('region'),
                sample_size=item.get('sample_size'),
                excerpt=item.get('excerpt'),
                tags=item.get('tags', []),
                weight=item.get('weight')
            ))
        
        logger.info(f"DEBUG: Total evidence items after combining: {len(evidence_items)}")
        
        # Step 11: Build LPM trace (all values must be strings per schema)
        lpm_trace = {
            'phase4_output_dir': str(grounding_result.get('phase4_output_dir', '')),
            'signals_dir': str(grounding_result.get('signals_dir', '') or ''),
            'model_version': '1.0',
            'run_id': request.request_id,
            'data_engine_evidence_count': str(len(data_engine_evidence)),
            'phase4_evidence_count': str(len(phase4_evidence)),
            'total_evidence_count': str(len(evidence_items)),
            'evidence_retriever_available': str(self.evidence_retriever is not None),
            'data_engine_available': str(self.evidence_retriever.data_engine is not None if self.evidence_retriever else False)
        }
        
        # Step 10: Build constraints for downstream LLM
        constraints_for_downstream_llm = {
            'decision_fixed': True,
            'no_new_evidence': True,
            'must_cite_evidence_ids': True,
            'max_confidence': confidence,
            'entropy': entropy
        }
        
        # Build response
        response = PersonaDecisionResponse(
            request_id=request.request_id,
            agent_id=request.persona.agent_id,
            hypothesis=request.hypothesis,
            population_prior={k: float(v) for k, v in prior.items()},
            conditioned_distribution={k: float(v) for k, v in conditioned.items()},
            sampled_decision=DecisionSample(
                choice=sampled_product_id,
                probability=float(sampled_prob),
                alternatives=alternatives
            ),
            sampled_responses=sampled_responses,
            dominant_drivers=dominant_drivers,
            uncertainty=Uncertainty(
                entropy=entropy,
                confidence=confidence
            ),
            ground_truth_evidence=evidence_items,
            lpm_trace=lpm_trace,
            constraints_for_downstream_llm=constraints_for_downstream_llm
        )
        
        return response

