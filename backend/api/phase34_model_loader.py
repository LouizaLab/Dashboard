"""
Phase 3-4 Model Loader
Loads Phase 1 and Phase 2 models from Louiza directory for use in recipe simulation.
"""
import sys
import os
from pathlib import Path
import torch
import pandas as pd
import numpy as np
from typing import Dict, Optional, Tuple

# Add Louiza directory to path
LOUIZA_PATH = Path(__file__).parent.parent.parent / 'Louiza'
if LOUIZA_PATH.exists():
    sys.path.insert(0, str(LOUIZA_PATH))

try:
    from models import ProductEmbeddingModel, ContextEmbeddingModel, SegmentEmbeddingModel
    from models_phase2 import BehavioralDynamicEngine
    from data_utils import Vocabulary
except ImportError as e:
    print(f"Warning: Could not import Louiza models: {e}")
    print("Falling back to simplified simulation")
    ProductEmbeddingModel = None
    ContextEmbeddingModel = None
    SegmentEmbeddingModel = None
    BehavioralDynamicEngine = None


class Phase34ModelLoader:
    """Loads and manages Phase 1-2 models for Phase 3-4 simulation"""
    
    def __init__(self, 
                 phase1_checkpoint: Optional[str] = None,
                 phase2_checkpoint: Optional[str] = None,
                 data_dir: Optional[str] = None,
                 device: str = 'cpu'):
        """
        Initialize model loader.
        
        Args:
            phase1_checkpoint: Path to Phase 1 checkpoint (default: Louiza/checkpoints/best_model.pt)
            phase2_checkpoint: Path to Phase 2 checkpoint (default: Louiza/checkpoints_phase2/best_model_phase2.pt)
            data_dir: Directory containing data files (default: Louiza/data)
            device: Device to load models on ('cpu' or 'cuda')
        """
        self.device = device
        
        # Set default paths
        if phase1_checkpoint is None:
            phase1_checkpoint = str(LOUIZA_PATH / 'checkpoints' / 'best_model.pt')
        if phase2_checkpoint is None:
            phase2_checkpoint = str(LOUIZA_PATH / 'checkpoints_phase2' / 'best_model_phase2.pt')
        if data_dir is None:
            data_dir = str(LOUIZA_PATH / 'data')
        
        self.phase1_checkpoint = phase1_checkpoint
        self.phase2_checkpoint = phase2_checkpoint
        self.data_dir = data_dir
        
        self.phase1_models = None
        self.phase2_model = None
        self.vocabularies = None
        self.models_loaded = False
        
    def load_models(self) -> Tuple[bool, Optional[str]]:
        """
        Load Phase 1 and Phase 2 models.
        
        Returns:
            (success, error_message)
        """
        if self.models_loaded:
            return True, None
        
        if not Path(self.phase1_checkpoint).exists():
            return False, f"Phase 1 checkpoint not found: {self.phase1_checkpoint}"
        
        if not Path(self.phase2_checkpoint).exists():
            return False, f"Phase 2 checkpoint not found: {self.phase2_checkpoint}"
        
        if ProductEmbeddingModel is None:
            return False, "Louiza models not available (import failed)"
        
        try:
            # Load Phase 1 checkpoint
            print(f"Loading Phase 1 models from {self.phase1_checkpoint}...")
            checkpoint = torch.load(self.phase1_checkpoint, map_location=self.device, weights_only=False)
            
            # Extract vocab sizes
            vocab_sizes = checkpoint.get('vocab_sizes', {})
            ingredient_vocab_size = vocab_sizes.get('ingredient', 100)
            tag_vocab_size = vocab_sizes.get('tag', 100)
            text_vocab_size = vocab_sizes.get('text', 100)
            
            # Store vocab sizes for segment encoding
            self.vocab_sizes = vocab_sizes
            
            # Try to load actual data to get correct mappings
            segments_path = Path(self.data_dir) / 'segments.csv'
            if segments_path.exists():
                try:
                    segments_df = pd.read_csv(segments_path)
                    self.age_buckets = sorted(segments_df['age_bucket'].unique())
                    self.regions = sorted(segments_df['region'].unique())
                    self.psychographics = sorted(segments_df['psychographic'].unique())
                    print(f"Loaded segment mappings: {len(self.age_buckets)} ages, {len(self.regions)} regions, {len(self.psychographics)} psychographics")
                    print(f"  Ages: {self.age_buckets}")
                    print(f"  Regions: {self.regions}")
                    print(f"  Psychographics: {self.psychographics}")
                except Exception as e:
                    print(f"Warning: Could not load segments.csv: {e}")
                    # Use defaults based on data_generator.py
                    self.age_buckets = ['18-25', '26-35', '36-45', '46-55', '56+']
                    self.regions = ['north', 'south', 'east', 'west', 'central']
                    self.psychographics = ['health_focused', 'adventurous', 'budget_sensitive', 'premium_seeker', 'routine_lover']
            else:
                print(f"Warning: segments.csv not found at {segments_path}")
                # Use defaults based on data_generator.py
                self.age_buckets = ['18-25', '26-35', '36-45', '46-55', '56+']
                self.regions = ['north', 'south', 'east', 'west', 'central']
                self.psychographics = ['health_focused', 'adventurous', 'budget_sensitive', 'premium_seeker', 'routine_lover']
            
            # Initialize Phase 1 models
            product_model = ProductEmbeddingModel(
                vocab_size=max(ingredient_vocab_size, tag_vocab_size, text_vocab_size),
                embedding_dim=64,
                hidden_dim=128,
                output_dim=128
            )
            
            context_model = ContextEmbeddingModel(
                time_of_day_vocab=vocab_sizes.get('time_of_day', 4),
                location_vocab=vocab_sizes.get('location', 5),
                occasion_vocab=vocab_sizes.get('occasion', 6),
                embedding_dim=32,
                hidden_dim=64,
                output_dim=64
            )
            
            segment_model = SegmentEmbeddingModel(
                age_vocab=vocab_sizes.get('age', 5),
                region_vocab=vocab_sizes.get('region', 4),
                psychographic_vocab=vocab_sizes.get('psychographic', 7),
                embedding_dim=32,
                hidden_dim=64,
                output_dim=64
            )
            
            # Load state dicts
            product_model.load_state_dict(checkpoint['product_model_state_dict'])
            context_model.load_state_dict(checkpoint['context_model_state_dict'])
            segment_model.load_state_dict(checkpoint['segment_model_state_dict'])
            
            product_model = product_model.to(self.device).eval()
            context_model = context_model.to(self.device).eval()
            segment_model = segment_model.to(self.device).eval()
            
            self.phase1_models = {
                'product': product_model,
                'context': context_model,
                'segment': segment_model
            }
            
            # Load vocabularies if available
            self.vocabularies = checkpoint.get('vocabularies', {})
            
            # Load Phase 2 checkpoint
            print(f"Loading Phase 2 model from {self.phase2_checkpoint}...")
            try:
                phase2_checkpoint = torch.load(self.phase2_checkpoint, map_location=self.device, weights_only=False)
            except Exception as load_error:
                return False, f"Failed to load Phase 2 checkpoint: {str(load_error)}"
            
            phase2_model = BehavioralDynamicEngine(
                segment_dim=64,
                product_dim=128,
                context_dim=64,
                state_dim=128,
                hidden_dim=256
            )
            
            phase2_model.load_state_dict(phase2_checkpoint['model_state_dict'])
            phase2_model = phase2_model.to(self.device).eval()
            
            self.phase2_model = phase2_model
            
            self.models_loaded = True
            print("Phase 1-2 models loaded successfully!")
            return True, None
            
        except Exception as e:
            import traceback
            error_msg = f"Error loading models: {str(e)}\n{traceback.format_exc()}"
            print(error_msg)
            return False, error_msg
    
    def get_phase1_models(self) -> Dict:
        """Get Phase 1 models"""
        if not self.models_loaded:
            success, error = self.load_models()
            if not success:
                raise RuntimeError(f"Failed to load models: {error}")
        return self.phase1_models
    
    def get_phase2_model(self):
        """Get Phase 2 model"""
        if not self.models_loaded:
            success, error = self.load_models()
            if not success:
                raise RuntimeError(f"Failed to load models: {error}")
        return self.phase2_model
    
    def get_vocabularies(self) -> Dict:
        """Get vocabularies"""
        if not self.models_loaded:
            success, error = self.load_models()
            if not success:
                return {}
        return self.vocabularies or {}
    
    def encode_product(self, product_data: Dict) -> np.ndarray:
        """
        Encode a product using Phase 1 product model.
        
        Args:
            product_data: Dict with 'ingredients', 'sensory_tags', 'nutrition', 'description'
        
        Returns:
            Product embedding vector
        """
        if not self.models_loaded:
            self.load_models()
        
        product_model = self.phase1_models['product']
        vocabularies = self.get_vocabularies()
        
        # Encode ingredients
        ingredient_vocab = vocabularies.get('ingredient', Vocabulary())
        ingredients = product_data.get('ingredients', '').split(',')
        ingredient_ids = []
        for ing in ingredients[:10]:
            if hasattr(ingredient_vocab, 'word_to_idx'):
                ing_id = ingredient_vocab.word_to_idx.get(ing.strip(), 0)
            else:
                ing_id = 0
            ingredient_ids.append(ing_id)
        while len(ingredient_ids) < 10:
            ingredient_ids.append(1)
        
        # Encode tags
        tag_vocab = vocabularies.get('tag', Vocabulary())
        tags = product_data.get('sensory_tags', '').split(',')
        tag_ids = []
        for tag in tags[:8]:
            if hasattr(tag_vocab, 'word_to_idx'):
                tag_id = tag_vocab.word_to_idx.get(tag.strip(), 0)
            else:
                tag_id = 0
            tag_ids.append(tag_id)
        while len(tag_ids) < 8:
            tag_ids.append(1)
        
        # Nutrition
        nutrition = product_data.get('nutrition', {})
        nutrition_tensor = torch.FloatTensor([[
            nutrition.get('sugar', 0),
            nutrition.get('caffeine', 0),
            nutrition.get('calories', 0),
            nutrition.get('protein', 0)
        ]]).to(self.device)
        
        # Text
        text_vocab = vocabularies.get('text', Vocabulary())
        description = product_data.get('description', '')
        if hasattr(text_vocab, 'encode'):
            text_ids = text_vocab.encode(description, 50)
        else:
            text_ids = [0] * 50
        
        # Convert to tensors
        ingredient_ids_t = torch.LongTensor([ingredient_ids]).to(self.device)
        tag_ids_t = torch.LongTensor([tag_ids]).to(self.device)
        text_ids_t = torch.LongTensor([text_ids]).to(self.device)
        
        with torch.no_grad():
            z_product = product_model(ingredient_ids_t, tag_ids_t, nutrition_tensor, text_ids_t)
            return z_product.cpu().numpy()[0]
    
    def encode_segment(self, segment_data: Dict) -> np.ndarray:
        """
        Encode a segment using Phase 1 segment model.
        
        Args:
            segment_data: Dict with 'age_bucket', 'region', 'psychographic'
        
        Returns:
            Segment embedding vector
        """
        if not self.models_loaded:
            self.load_models()
        
        segment_model = self.phase1_models['segment']
        
        # Get vocab sizes from checkpoint (these are the actual model embedding table sizes)
        vocab_sizes = getattr(self, 'vocab_sizes', {})
        age_vocab_size = vocab_sizes.get('age', 5)  # Use checkpoint value, not list length
        region_vocab_size = vocab_sizes.get('region', 5)  # Use checkpoint value
        psychographic_vocab_size = vocab_sizes.get('psychographic', 7)  # Use checkpoint value
        
        # Get actual training data mappings (for finding correct indices)
        age_buckets = getattr(self, 'age_buckets', ['18-25', '26-35', '36-45', '46-55', '56+'])
        regions = getattr(self, 'regions', ['north', 'south', 'east', 'west', 'central'])
        psychographics = getattr(self, 'psychographics', ['health_focused', 'adventurous', 'budget_sensitive', 'premium_seeker', 'routine_lover'])
        
        # Ensure we have valid lists
        if not age_buckets:
            age_buckets = ['18-25', '26-35', '36-45', '46-55', '56+']
        if not regions:
            regions = ['north', 'south', 'east', 'west', 'central']
        if not psychographics:
            psychographics = ['health_focused', 'adventurous', 'budget_sensitive', 'premium_seeker', 'routine_lover']
        
        # Map PersonaAgent values to training data values
        # Age bucket mapping (PersonaAgent uses different format)
        age_value = segment_data.get('age_bucket', '25-34')
        age_mapping = {
            '18-24': '18-25',
            '25-34': '26-35',
            '35-44': '36-45',
            '45-54': '46-55',
            '55+': '56+'
        }
        age_value = age_mapping.get(age_value, age_value)
        
        # Region mapping (PersonaAgent uses capitalized, training uses lowercase)
        region_value = segment_data.get('region', 'West')
        region_mapping = {
            'West': 'west',
            'Midwest': 'central',  # Map to closest match
            'South': 'south',
            'Northeast': 'east'  # Map to closest match
        }
        region_value = region_mapping.get(region_value, region_value.lower() if region_value else 'west')
        
        # Psychographic mapping (archetype -> psychographic)
        psychographic_value = segment_data.get('psychographic', segment_data.get('archetype', 'value_seeker'))
        psychographic_mapping = {
            'value_seeker': 'budget_sensitive',
            'health_optimizer': 'health_focused',
            'convenience_loyalist': 'routine_lover',
            'late_night_craver': 'adventurous',
            'trend_chaser': 'adventurous',
            'family_bundle_buyer': 'budget_sensitive',
            'protein_maximizer': 'health_focused'
        }
        psychographic_value = psychographic_mapping.get(psychographic_value, psychographic_value)
        
        # Find indices, with fallback to 0 if not found
        try:
            if age_value in age_buckets:
                age_id = age_buckets.index(age_value)
            else:
                # Find closest match or use middle value
                age_id = len(age_buckets) // 2 if age_buckets else 0
        except (ValueError, AttributeError, IndexError):
            age_id = 0
        
        try:
            if region_value in regions:
                region_id = regions.index(region_value)
            else:
                # Try lowercase version
                region_value_lower = region_value.lower()
                if region_value_lower in regions:
                    region_id = regions.index(region_value_lower)
                else:
                    # Use first available region
                    region_id = 0 if regions else 0
        except (ValueError, AttributeError, IndexError):
            region_id = 0
        
        try:
            if psychographic_value in psychographics:
                psychographic_id = psychographics.index(psychographic_value)
            else:
                # Use first available psychographic
                psychographic_id = 0 if psychographics else 0
        except (ValueError, AttributeError, IndexError):
            psychographic_id = 0
        
        # Clamp to valid range (critical - prevents index out of range errors)
        age_id = max(0, min(age_id, age_vocab_size - 1))
        region_id = max(0, min(region_id, region_vocab_size - 1))
        psychographic_id = max(0, min(psychographic_id, psychographic_vocab_size - 1))
        
        # Debug logging (first few encodings only)
        if not hasattr(self, '_encode_debug_count'):
            self._encode_debug_count = 0
        self._encode_debug_count += 1
        if self._encode_debug_count <= 3:  # Log first 3 encodings
            print(f"  Segment encoding #{self._encode_debug_count}: age={age_value}->{age_id}/{age_vocab_size-1}, region={region_value}->{region_id}/{region_vocab_size-1}, psychographic={psychographic_value}->{psychographic_id}/{psychographic_vocab_size-1}")
        
        age_ids_t = torch.LongTensor([[age_id]]).to(self.device)
        region_ids_t = torch.LongTensor([[region_id]]).to(self.device)
        psychographic_ids_t = torch.LongTensor([[psychographic_id]]).to(self.device)
        
        try:
            with torch.no_grad():
                z_segment = segment_model(age_ids_t, region_ids_t, psychographic_ids_t)
                return z_segment.cpu().numpy()[0]
        except IndexError as e:
            print(f"ERROR in segment encoding: age_id={age_id}, region_id={region_id}, psychographic_id={psychographic_id}")
            print(f"  Vocab sizes: age={age_vocab_size}, region={region_vocab_size}, psychographic={psychographic_vocab_size}")
            print(f"  Available: ages={age_buckets}, regions={regions}, psychographics={psychographics}")
            raise RuntimeError(f"Segment encoding failed - index out of range: {e}. Check vocab sizes match model.")


# Global model loader instance (lazy-loaded)
_model_loader_instance = None

def get_model_loader(device: str = 'cpu') -> Phase34ModelLoader:
    """Get or create global model loader instance"""
    global _model_loader_instance
    if _model_loader_instance is None:
        _model_loader_instance = Phase34ModelLoader(device=device)
    return _model_loader_instance

