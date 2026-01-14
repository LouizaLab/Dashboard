"""
LPM API: Programmatic interface to the 4-phase Latent Preference Model
This module wraps the existing LPM functionality to expose clean functions for Agent-Tron.
"""

import torch
import pandas as pd
import numpy as np
import os
from typing import Dict, List, Optional, Tuple, Any
import json
from pathlib import Path

# Import phase modules
import sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'phase1'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'phase2'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'phase3'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'phase4'))

from phase1.models import ProductEmbeddingModel, ContextEmbeddingModel, SegmentEmbeddingModel
from phase1.data_utils import Vocabulary
from phase2.models_phase2 import BehavioralDynamicEngine, BehavioralState
from phase2.train_phase2 import load_phase1_models
from phase3.simulate_phase3 import encode_all_products_and_contexts, encode_segments


class LPMManager:
    """Manages LPM models and provides inference interface"""
    
    def __init__(self, 
                 phase1_checkpoint: str = 'checkpoints/best_model.pt',
                 phase2_checkpoint: str = 'checkpoints_phase2/best_model_phase2.pt',
                 data_dir: str = 'data',
                 device: str = None):
        """Initialize LPM manager with trained models"""
        if device is None:
            device = 'cuda' if torch.cuda.is_available() else 'cpu'
        self.device = device
        
        # Load models
        print(f"Loading Phase 1 models from {phase1_checkpoint}...")
        self.phase1_models, self.vocabularies = load_phase1_models(
            phase1_checkpoint, data_dir, device
        )
        
        print(f"Loading Phase 2 model from {phase2_checkpoint}...")
        checkpoint = torch.load(phase2_checkpoint, map_location=device, weights_only=False)
        self.phase2_model = BehavioralDynamicEngine(
            segment_dim=64,
            product_dim=128,
            context_dim=64,
            state_dim=128,
            hidden_dim=256
        )
        self.phase2_model.load_state_dict(checkpoint['model_state_dict'])
        self.phase2_model = self.phase2_model.to(device)
        self.phase2_model.eval()
        
        # Load data
        self.data_dir = data_dir
        self.products_df = pd.read_csv(os.path.join(data_dir, 'products.csv'))
        self.contexts_df = pd.read_csv(os.path.join(data_dir, 'contexts.csv'))
        self.segments_df = pd.read_csv(os.path.join(data_dir, 'segments.csv'))
        
        # Pre-compute embeddings
        print("Pre-computing product and context embeddings...")
        self.product_embeddings, self.context_embeddings = encode_all_products_and_contexts(
            self.phase1_models, self.products_df, self.contexts_df, 
            self.vocabularies, device
        )
        self.segment_embeddings = encode_segments(
            self.phase1_models, self.segments_df, device
        )
        
        # Create mappings
        self._create_mappings()
        
        print("LPM Manager initialized successfully")
    
    def _create_mappings(self):
        """Create ID mappings for categorical features"""
        self.time_of_days = sorted(self.contexts_df['time_of_day'].unique())
        self.locations = sorted(self.contexts_df['location'].unique())
        self.occasions = sorted(self.contexts_df['occasion'].unique())
        self.age_buckets = sorted(self.segments_df['age_bucket'].unique())
        self.regions = sorted(self.segments_df['region'].unique())
        self.psychographics = sorted(self.segments_df['psychographic'].unique())
        
        self.time_of_day_to_idx = {td: idx for idx, td in enumerate(self.time_of_days)}
        self.location_to_idx = {loc: idx for idx, loc in enumerate(self.locations)}
        self.occasion_to_idx = {occ: idx for idx, occ in enumerate(self.occasions)}
        self.age_to_idx = {age: idx for idx, age in enumerate(self.age_buckets)}
        self.region_to_idx = {reg: idx for idx, reg in enumerate(self.regions)}
        self.psychographic_to_idx = {psy: idx for idx, psy in enumerate(self.psychographics)}
    
    def get_segment_embedding(self, archetype: str, demographics: Dict, psychographics: Dict) -> torch.Tensor:
        """Get segment embedding from persona attributes"""
        # Map persona to segment attributes
        age_bucket = demographics.get('age_bucket', self.age_buckets[0])
        region = demographics.get('region', self.regions[0])
        psychographic = psychographics.get('psychographic', self.psychographics[0])
        
        # Find matching segment or create synthetic
        matching_segments = self.segments_df[
            (self.segments_df['age_bucket'] == age_bucket) &
            (self.segments_df['region'] == region) &
            (self.segments_df['psychographic'] == psychographic)
        ]
        
        if len(matching_segments) > 0:
            segment_id = matching_segments.iloc[0]['segment_id']
            if segment_id in self.segment_embeddings:
                return torch.FloatTensor(self.segment_embeddings[segment_id]).to(self.device)
        
        # Fallback: encode directly
        age_id = self.age_to_idx.get(age_bucket, 0)
        region_id = self.region_to_idx.get(region, 0)
        psychographic_id = self.psychographic_to_idx.get(psychographic, 0)
        
        age_ids_t = torch.LongTensor([[age_id]]).to(self.device)
        region_ids_t = torch.LongTensor([[region_id]]).to(self.device)
        psychographic_ids_t = torch.LongTensor([[psychographic_id]]).to(self.device)
        
        with torch.no_grad():
            z_segment = self.phase1_models['segment'](
                age_ids_t, region_ids_t, psychographic_ids_t
            )
        return z_segment[0]
    
    def get_product_embedding(self, product_id: str) -> torch.Tensor:
        """Get product embedding"""
        if product_id in self.product_embeddings:
            return torch.FloatTensor(self.product_embeddings[product_id]).to(self.device)
        else:
            # Fallback: return first product
            first_product_id = list(self.product_embeddings.keys())[0]
            return torch.FloatTensor(self.product_embeddings[first_product_id]).to(self.device)
    
    def get_context_embedding(self, context: Dict) -> torch.Tensor:
        """Get context embedding from context dict"""
        time_of_day = context.get('time_of_day') or self.time_of_days[0]
        location = context.get('location') or self.locations[0]
        occasion = context.get('occasion') or self.occasions[0]
        price_shown = context.get('price_shown')
        if price_shown is None:
            price_shown = 2.5
        
        # Find matching context or create synthetic
        matching_contexts = self.contexts_df[
            (self.contexts_df['time_of_day'] == time_of_day) &
            (self.contexts_df['location'] == location) &
            (self.contexts_df['occasion'] == occasion)
        ]
        
        if len(matching_contexts) > 0:
            context_id = matching_contexts.iloc[0]['context_id']
            if context_id in self.context_embeddings:
                return torch.FloatTensor(self.context_embeddings[context_id]).to(self.device)
        
        # Fallback: encode directly
        time_id = self.time_of_day_to_idx.get(time_of_day, 0)
        location_id = self.location_to_idx.get(location, 0)
        occasion_id = self.occasion_to_idx.get(occasion, 0)
        price = torch.FloatTensor([[price_shown]]).to(self.device)
        
        time_ids_t = torch.LongTensor([[time_id]]).to(self.device)
        location_ids_t = torch.LongTensor([[location_id]]).to(self.device)
        occasion_ids_t = torch.LongTensor([[occasion_id]]).to(self.device)
        
        with torch.no_grad():
            z_context = self.phase1_models['context'](
                time_ids_t, location_ids_t, occasion_ids_t, price
            )
        return z_context[0]
    
    def get_population_prior(self, archetype: str, context: Dict) -> Dict[str, float]:
        """
        Get population-level prior distribution over products for archetype
        Returns: dict mapping product_id -> probability
        """
        # Get segment embedding
        demographics = {'age_bucket': archetype.split('_')[0] if '_' in archetype else '26-35',
                       'region': context.get('region', 'north'),
                       'psychographic': archetype}
        psychographics = {'psychographic': archetype}
        
        z_segment = self.get_segment_embedding(archetype, demographics, psychographics)
        
        # Get context embedding
        z_context = self.get_context_embedding(context)
        
        # Initialize state
        with torch.no_grad():
            s_t = self.phase2_model.initialize_state(z_segment.unsqueeze(0))
        
        # Compute preferences for all products
        product_probs = {}
        total_score = 0.0
        
        for product_id in self.product_embeddings.keys():
            z_product = self.get_product_embedding(product_id)
            
            with torch.no_grad():
                intent = self.phase2_model.predict_intent(
                    s_t, z_product.unsqueeze(0), z_context.unsqueeze(0)
                )
                score = float(intent[0, 0].item())
            
            # Convert to probability (softmax)
            product_probs[product_id] = np.exp(score)
            total_score += np.exp(score)
        
        # Normalize
        for product_id in product_probs:
            product_probs[product_id] = product_probs[product_id] / total_score
        
        return product_probs
    
    def condition_on_context(self, prior: Dict[str, float], persona: Dict, context: Dict) -> Dict[str, float]:
        """
        Condition prior distribution on persona and context
        Returns: updated distribution
        """
        # Get embeddings
        demographics = persona.get('demographics', {})
        psychographics = persona.get('psychographics', {})
        archetype = persona.get('archetype', 'balanced')
        
        z_segment = self.get_segment_embedding(archetype, demographics, psychographics)
        z_context = self.get_context_embedding(context)
        
        # Initialize state
        with torch.no_grad():
            s_t = self.phase2_model.initialize_state(z_segment.unsqueeze(0))
        
        # Apply psychographic adjustments
        price_sensitivity = psychographics.get('price_sensitivity', 0.5)
        novelty_seeking = psychographics.get('novelty_seeking', 0.5)
        health_consciousness = psychographics.get('health_consciousness', 0.5)
        brand_loyalty = psychographics.get('brand_loyalty', 0.5)
        
        # Compute conditioned distribution
        conditioned_probs = {}
        total_score = 0.0
        
        for product_id, base_prob in prior.items():
            z_product = self.get_product_embedding(product_id)
            
            with torch.no_grad():
                intent = self.phase2_model.predict_intent(
                    s_t, z_product.unsqueeze(0), z_context.unsqueeze(0)
                )
                score = float(intent[0, 0].item())
            
            # Apply psychographic adjustments
            product_row = self.products_df[self.products_df['product_id'] == product_id]
            if len(product_row) > 0:
                product = product_row.iloc[0]
                
                # Price adjustment
                try:
                    price = float(product['price']) if 'price' in product.index else 2.5
                    if price != price:  # Check for NaN
                        price = 2.5
                except (ValueError, TypeError, KeyError):
                    price = 2.5
                price_factor = 1.0 - (price_sensitivity * (price - 2.5) / 2.5)
                
                # Health adjustment
                try:
                    calories = float(product['calories']) if 'calories' in product.index else 100
                    if calories != calories:  # Check for NaN
                        calories = 100
                except (ValueError, TypeError, KeyError):
                    calories = 100
                health_factor = 1.0 + (health_consciousness * (100 - calories) / 100)
                
                # Novelty adjustment (simplified)
                novelty_factor = 1.0 + (novelty_seeking * 0.2)
                
                adjusted_score = score * price_factor * health_factor * novelty_factor
            else:
                adjusted_score = score
            
            conditioned_probs[product_id] = np.exp(adjusted_score)
            total_score += np.exp(adjusted_score)
        
        # Normalize
        for product_id in conditioned_probs:
            conditioned_probs[product_id] = conditioned_probs[product_id] / total_score
        
        return conditioned_probs
    
    def sample_decision(self, distribution: Dict[str, float], seed: int) -> Tuple[str, float]:
        """
        Sample a decision from distribution
        Returns: (product_id, probability)
        """
        np.random.seed(seed)
        product_ids = list(distribution.keys())
        probs = list(distribution.values())
        
        sampled_idx = np.random.choice(len(product_ids), p=probs)
        sampled_product_id = product_ids[sampled_idx]
        sampled_prob = probs[sampled_idx]
        
        return sampled_product_id, sampled_prob
    
    def get_phase4_grounding(self, hypothesis: str, persona: Dict, context: Dict) -> Dict:
        """
        Get Phase 4 ground truth evidence and artifacts
        Returns: dict with evidence items and phase4 output paths
        """
        # Check if phase4_output exists
        phase4_output_dir = 'phase4_output'
        evidence_items = []
        
        # Load signals if available
        signals_dir = os.path.join(phase4_output_dir, 'signals')
        if os.path.exists(signals_dir):
            # Load intent_index as evidence
            intent_index_path = os.path.join(signals_dir, 'intent_index.csv')
            if os.path.exists(intent_index_path):
                intent_df = pd.read_csv(intent_index_path)
                # Create evidence items from recent data
                for idx, row in intent_df.tail(10).iterrows():
                    evidence_items.append({
                        'evidence_id': f'intent_index_{idx}',
                        'source_type': 'intent_index',
                        'date': str(row.get('date', '')),
                        'excerpt': f"Intent value: {row.get('intent_value', 0):.3f}",
                        'tags': ['intent', 'time_series'],
                        'weight': 0.8
                    })
        
        # Load calibration metrics
        calibration_path = os.path.join(phase4_output_dir, 'calibration_metrics.json')
        if os.path.exists(calibration_path):
            with open(calibration_path, 'r') as f:
                calibration_data = json.load(f)
                evidence_items.append({
                    'evidence_id': 'calibration_metrics',
                    'source_type': 'calibration',
                    'excerpt': f"Calibration accuracy: {calibration_data.get('accuracy', 0):.3f}",
                    'tags': ['calibration', 'metrics'],
                    'weight': 1.0
                })
        
        return {
            'evidence_items': evidence_items,
            'phase4_output_dir': phase4_output_dir,
            'signals_dir': signals_dir if os.path.exists(signals_dir) else None
        }


# Global LPM manager instance (lazy loaded)
_lpm_manager: Optional[LPMManager] = None


def get_lpm_manager(phase1_checkpoint: str = 'checkpoints/best_model.pt',
                   phase2_checkpoint: str = 'checkpoints_phase2/best_model_phase2.pt',
                   data_dir: str = 'data',
                   device: str = None) -> LPMManager:
    """Get or create LPM manager instance"""
    global _lpm_manager
    if _lpm_manager is None:
        _lpm_manager = LPMManager(phase1_checkpoint, phase2_checkpoint, data_dir, device)
    return _lpm_manager


# Public API functions (for Agent-Tron)
def get_population_prior(archetype: str, context: dict, 
                        phase1_checkpoint: str = 'checkpoints/best_model.pt',
                        phase2_checkpoint: str = 'checkpoints_phase2/best_model_phase2.pt',
                        data_dir: str = 'data') -> dict:
    """Get population prior distribution"""
    manager = get_lpm_manager(phase1_checkpoint, phase2_checkpoint, data_dir)
    return manager.get_population_prior(archetype, context)


def condition_on_context(prior: dict, persona: dict, context: dict,
                         phase1_checkpoint: str = 'checkpoints/best_model.pt',
                         phase2_checkpoint: str = 'checkpoints_phase2/best_model_phase2.pt',
                         data_dir: str = 'data') -> dict:
    """Condition prior on persona and context"""
    manager = get_lpm_manager(phase1_checkpoint, phase2_checkpoint, data_dir)
    return manager.condition_on_context(prior, persona, context)


def sample_decision(distribution: dict, seed: int) -> tuple:
    """Sample decision from distribution"""
    np.random.seed(seed)
    product_ids = list(distribution.keys())
    probs = list(distribution.values())
    
    sampled_idx = np.random.choice(len(product_ids), p=probs)
    sampled_product_id = product_ids[sampled_idx]
    sampled_prob = probs[sampled_idx]
    
    return sampled_product_id, sampled_prob


def get_phase4_grounding(hypothesis: str, persona: dict, context: dict,
                        phase4_output_dir: str = 'phase4_output') -> dict:
    """Get Phase 4 ground truth evidence"""
    manager = get_lpm_manager()
    return manager.get_phase4_grounding(hypothesis, persona, context)

