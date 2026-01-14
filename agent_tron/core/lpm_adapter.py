"""
LPM Adapter: Bridge to 4_phases/lpm_api.py
This is the ONLY place that touches the LPM
"""

import sys
import os
from typing import Dict, Tuple

# Add 4_phases to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '4_phases'))

from lpm_api import (
    get_population_prior as lpm_get_prior,
    condition_on_context as lpm_condition,
    sample_decision as lpm_sample,
    get_phase4_grounding as lpm_grounding
)


class LPMAdapter:
    """Adapter to LPM API - only bridge to 4_phases"""
    
    def __init__(self, 
                 phase1_checkpoint: str = 'checkpoints/best_model.pt',
                 phase2_checkpoint: str = 'checkpoints_phase2/best_model_phase2.pt',
                 data_dir: str = 'data'):
        """Initialize adapter with checkpoint paths"""
        self.phase1_checkpoint = phase1_checkpoint
        self.phase2_checkpoint = phase2_checkpoint
        self.data_dir = data_dir
    
    def get_prior(self, archetype: str, context: dict) -> Dict[str, float]:
        """
        Get population prior distribution
        Returns: dict mapping product_id -> probability
        """
        # Convert context to LPM format
        lpm_context = {
            'time_of_day': context.get('time_of_day'),
            'location': context.get('location'),
            'region': context.get('region'),
            'occasion': context.get('occasion'),
            'price_shown': context.get('price_shown', 2.5)
        }
        
        prior = lpm_get_prior(
            archetype=archetype,
            context=lpm_context,
            phase1_checkpoint=self.phase1_checkpoint,
            phase2_checkpoint=self.phase2_checkpoint,
            data_dir=self.data_dir
        )
        
        return prior
    
    def condition(self, prior: Dict[str, float], persona: dict, context: dict) -> Dict[str, float]:
        """
        Condition prior on persona and context
        Returns: updated distribution
        """
        # Convert persona to LPM format
        lpm_persona = {
            'archetype': persona.get('archetype', 'balanced'),
            'demographics': persona.get('demographics', {}),
            'psychographics': persona.get('psychographics', {})
        }
        
        # Convert context to LPM format
        lpm_context = {
            'time_of_day': context.get('time_of_day'),
            'location': context.get('location'),
            'region': context.get('region'),
            'occasion': context.get('occasion'),
            'price_shown': context.get('price_shown', 2.5)
        }
        
        conditioned = lpm_condition(
            prior=prior,
            persona=lpm_persona,
            context=lpm_context,
            phase1_checkpoint=self.phase1_checkpoint,
            phase2_checkpoint=self.phase2_checkpoint,
            data_dir=self.data_dir
        )
        
        return conditioned
    
    def sample(self, distribution: Dict[str, float], seed: int) -> Tuple[str, float]:
        """
        Sample decision from distribution
        Returns: (product_id, probability)
        """
        return lpm_sample(distribution, seed)
    
    def grounding(self, hypothesis: str, persona: dict, context: dict) -> Dict:
        """
        Get Phase 4 ground truth evidence
        Returns: dict with evidence items
        """
        lpm_persona = {
            'archetype': persona.get('archetype', 'balanced'),
            'demographics': persona.get('demographics', {}),
            'psychographics': persona.get('psychographics', {})
        }
        
        lpm_context = {
            'time_of_day': context.get('time_of_day'),
            'location': context.get('location'),
            'region': context.get('region'),
            'occasion': context.get('occasion'),
            'price_shown': context.get('price_shown', 2.5)
        }
        
        return lpm_grounding(
            hypothesis=hypothesis,
            persona=lpm_persona,
            context=lpm_context
        )

