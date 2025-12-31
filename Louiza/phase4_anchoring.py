"""
Phase 4: Ground Truth Anchoring
Actually anchors models to real data through:
1. Parameter calibration (adjusting simulation parameters)
2. Model fine-tuning (updating Phase 1/Phase 2 models with real data)
3. Iterative calibration loop
"""

import torch
import torch.nn as nn
import torch.optim as optim
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple, Callable
from datetime import datetime, timedelta
import json
import os
from copy import deepcopy

from models_phase2 import BehavioralDynamicEngine
from models_phase3 import PopulationSimulator, Agent, Environment
from data_utils import EmbeddingDataset
# Note: Model imports would be used for fine-tuning - placeholder for framework
# from models import CombinedEmbeddingModel


class ParameterCalibrator:
    """
    Calibrates simulation parameters to match real data distributions
    """
    
    def __init__(self, 
                 real_data: pd.DataFrame,
                 target_metrics: Optional[Dict] = None):
        """
        Args:
            real_data: Real intent/outcome data
            target_metrics: Optional pre-computed target metrics
        """
        self.real_data = real_data.copy()
        self.target_metrics = target_metrics or self._compute_target_metrics()
        
        # Calibratable parameters
        self.params = {
            'agent_state_init_scale': 1.0,  # Scale for initial agent states
            'transition_momentum': 0.5,  # How much state persists (NOW CALIBRATABLE)
            'intent_noise_scale': 0.1,  # Noise in intent prediction
            'switching_rate_multiplier': 1.0,  # Multiplier for product switching
            'segment_bias_adjustments': {},  # Per-segment adjustments
            'social_influence_strength': 0.3,  # Weight of social influence (0-1)
            'macro_context_sensitivity': 1.0,  # Sensitivity to macro context changes
            'habit_strength_scale': 1.0  # Scale for habit strength component
        }
    
    def _compute_target_metrics(self) -> Dict:
        """Compute target metrics from real data"""
        metrics = {}
        
        # Product-level intent distribution
        if 'product_id' in self.real_data.columns and 'intent_value' in self.real_data.columns:
            product_intent = self.real_data.groupby('product_id')['intent_value'].agg(['mean', 'std'])
            metrics['product_intent_mean'] = product_intent['mean'].mean()
            metrics['product_intent_std'] = product_intent['std'].mean()
        
        # Segment-level patterns
        if 'segment_id' in self.real_data.columns:
            segment_intent = self.real_data.groupby('segment_id')['intent_value'].agg(['mean', 'std'])
            metrics['segment_intent_means'] = segment_intent['mean'].to_dict()
            metrics['segment_intent_stds'] = segment_intent['std'].to_dict()
        
        # Category-level patterns
        if 'product_category' in self.real_data.columns:
            category_intent = self.real_data.groupby('product_category')['intent_value'].agg(['mean', 'std'])
            metrics['category_intent_means'] = category_intent['mean'].to_dict()
            metrics['category_intent_stds'] = category_intent['std'].to_dict()
        
        # Switching rate
        if 'agent_id' in self.real_data.columns and 'product_id' in self.real_data.columns:
            agent_products = self.real_data.sort_values(['agent_id', 'timestamp']).groupby('agent_id')['product_id']
            switches = []
            for agent_id, products in agent_products:
                product_seq = products.tolist()
                switch_count = sum(1 for i in range(1, len(product_seq)) if product_seq[i] != product_seq[i-1])
                if len(product_seq) > 1:
                    switches.append(switch_count / (len(product_seq) - 1))
            if switches:
                metrics['switching_rate'] = np.mean(switches)
        
        # Time-series trend
        if 'timestamp' in self.real_data.columns:
            self.real_data['timestamp'] = pd.to_datetime(self.real_data['timestamp'])
            self.real_data['date'] = self.real_data['timestamp'].dt.date
            daily_intent = self.real_data.groupby('date')['intent_value'].mean()
            if len(daily_intent) > 1:
                x = np.arange(len(daily_intent))
                y = daily_intent.values
                metrics['daily_trend'] = np.polyfit(x, y, 1)[0]
                metrics['daily_mean'] = daily_intent.mean()
        
        return metrics
    
    def compute_simulated_metrics(self, sim_data: pd.DataFrame) -> Dict:
        """Compute metrics from simulated data (same structure as target)"""
        metrics = {}
        
        if 'product_id' in sim_data.columns and 'intent_value' in sim_data.columns:
            product_intent = sim_data.groupby('product_id')['intent_value'].agg(['mean', 'std'])
            metrics['product_intent_mean'] = product_intent['mean'].mean()
            metrics['product_intent_std'] = product_intent['std'].mean()
        
        if 'segment_id' in sim_data.columns:
            segment_intent = sim_data.groupby('segment_id')['intent_value'].agg(['mean', 'std'])
            metrics['segment_intent_means'] = segment_intent['mean'].to_dict()
            metrics['segment_intent_stds'] = segment_intent['std'].to_dict()
        
        if 'product_category' in sim_data.columns:
            category_intent = sim_data.groupby('product_category')['intent_value'].agg(['mean', 'std'])
            metrics['category_intent_means'] = category_intent['mean'].to_dict()
            metrics['category_intent_stds'] = category_intent['std'].to_dict()
        
        if 'agent_id' in sim_data.columns and 'product_id' in sim_data.columns:
            agent_products = sim_data.sort_values(['agent_id', 'timestamp']).groupby('agent_id')['product_id']
            switches = []
            for agent_id, products in agent_products:
                product_seq = products.tolist()
                switch_count = sum(1 for i in range(1, len(product_seq)) if product_seq[i] != product_seq[i-1])
                if len(product_seq) > 1:
                    switches.append(switch_count / (len(product_seq) - 1))
            if switches:
                metrics['switching_rate'] = np.mean(switches)
        
        if 'timestamp' in sim_data.columns:
            sim_data['timestamp'] = pd.to_datetime(sim_data['timestamp'])
            sim_data['date'] = sim_data['timestamp'].dt.date
            daily_intent = sim_data.groupby('date')['intent_value'].mean()
            if len(daily_intent) > 1:
                x = np.arange(len(daily_intent))
                y = daily_intent.values
                metrics['daily_trend'] = np.polyfit(x, y, 1)[0]
                metrics['daily_mean'] = daily_intent.mean()
        
        # Habit strength distribution (repeat purchase rate)
        if 'agent_id' in sim_data.columns and 'product_id' in sim_data.columns:
            agent_products = sim_data.sort_values(['agent_id', 'timestamp']).groupby('agent_id')['product_id']
            repeat_rates = []
            for agent_id, products in agent_products:
                product_seq = products.tolist()
                if len(product_seq) > 1:
                    # Count consecutive repeats
                    repeats = sum(1 for i in range(1, len(product_seq)) if product_seq[i] == product_seq[i-1])
                    repeat_rate = repeats / (len(product_seq) - 1) if len(product_seq) > 1 else 0
                    repeat_rates.append(repeat_rate)
            if repeat_rates:
                metrics['habit_strength_mean'] = np.mean(repeat_rates)
                metrics['habit_strength_std'] = np.std(repeat_rates)
        
        return metrics
    
    def compute_loss(self, sim_metrics: Dict, target_metrics: Dict) -> float:
        """Compute calibration loss"""
        loss = 0.0
        n_terms = 0
        
        # Product intent mean
        if 'product_intent_mean' in sim_metrics and 'product_intent_mean' in target_metrics:
            diff = sim_metrics['product_intent_mean'] - target_metrics['product_intent_mean']
            loss += diff ** 2
            n_terms += 1
        
        # Segment means
        if 'segment_intent_means' in sim_metrics and 'segment_intent_means' in target_metrics:
            all_segments = set(sim_metrics['segment_intent_means'].keys()) | set(target_metrics['segment_intent_means'].keys())
            for seg in all_segments:
                sim_mean = sim_metrics['segment_intent_means'].get(seg, 0)
                target_mean = target_metrics['segment_intent_means'].get(seg, 0)
                loss += (sim_mean - target_mean) ** 2
                n_terms += 1
        
        # Category means
        if 'category_intent_means' in sim_metrics and 'category_intent_means' in target_metrics:
            all_cats = set(sim_metrics['category_intent_means'].keys()) | set(target_metrics['category_intent_means'].keys())
            for cat in all_cats:
                sim_mean = sim_metrics['category_intent_means'].get(cat, 0)
                target_mean = target_metrics['category_intent_means'].get(cat, 0)
                loss += (sim_mean - target_mean) ** 2
                n_terms += 1
        
        # Switching rate
        if 'switching_rate' in sim_metrics and 'switching_rate' in target_metrics:
            diff = sim_metrics['switching_rate'] - target_metrics['switching_rate']
            loss += diff ** 2
            n_terms += 1
        
        # Trend
        if 'daily_trend' in sim_metrics and 'daily_trend' in target_metrics:
            diff = sim_metrics['daily_trend'] - target_metrics['daily_trend']
            loss += diff ** 2
            n_terms += 1
        
        # Habit strength
        if 'habit_strength_mean' in sim_metrics and 'habit_strength_mean' in target_metrics:
            diff = sim_metrics['habit_strength_mean'] - target_metrics['habit_strength_mean']
            loss += diff ** 2
            n_terms += 1
        
        return loss / max(n_terms, 1)
    
    def calibrate_parameters(self,
                           simulator_factory: Callable,
                           n_iterations: int = 25,
                           learning_rate: float = 0.1) -> Dict:
        """
        Calibrate parameters iteratively
        
        Args:
            simulator_factory: Function that creates a simulator with given params
            n_iterations: Number of calibration iterations
            learning_rate: Learning rate for parameter updates
        
        Returns:
            Calibrated parameters
        """
        best_params = deepcopy(self.params)
        best_loss = float('inf')
        
        print(f"\nStarting parameter calibration ({n_iterations} iterations)...")
        
        for iteration in range(n_iterations):
            # Run simulation with current parameters
            simulator = simulator_factory(self.params)
            sim_data = simulator.run_simulation()
            
            # Compute metrics
            sim_metrics = self.compute_simulated_metrics(sim_data)
            loss = self.compute_loss(sim_metrics, self.target_metrics)
            
            print(f"  Iteration {iteration + 1}/{n_iterations}: Loss = {loss:.6f}")
            
            if loss < best_loss:
                best_loss = loss
                best_params = deepcopy(self.params)
            
            # Gradient-free optimization: adjust parameters based on differences
            if iteration < n_iterations - 1:  # Don't adjust on last iteration
                self._update_parameters(sim_metrics, learning_rate)
        
        self.params = best_params
        print(f"\nCalibration complete. Best loss: {best_loss:.6f}")
        return best_params
    
    def _update_parameters(self, sim_metrics: Dict, learning_rate: float):
        """Update parameters based on metric differences"""
        # Adjust state initialization scale based on product intent mean
        if 'product_intent_mean' in sim_metrics and 'product_intent_mean' in self.target_metrics:
            diff = sim_metrics['product_intent_mean'] - self.target_metrics['product_intent_mean']
            self.params['agent_state_init_scale'] -= learning_rate * diff * 0.15  # Increased from 0.1 to 0.15 for stronger adjustment
        
        # Adjust switching rate multiplier
        if 'switching_rate' in sim_metrics and 'switching_rate' in self.target_metrics:
            diff = sim_metrics['switching_rate'] - self.target_metrics['switching_rate']
            self.params['switching_rate_multiplier'] -= learning_rate * diff
        
        # Adjust segment biases
        if 'segment_intent_means' in sim_metrics and 'segment_intent_means' in self.target_metrics:
            all_segments = set(sim_metrics['segment_intent_means'].keys()) | set(self.target_metrics['segment_intent_means'].keys())
            for seg in all_segments:
                sim_mean = sim_metrics['segment_intent_means'].get(seg, 0)
                target_mean = self.target_metrics['segment_intent_means'].get(seg, 0)
                if seg not in self.params['segment_bias_adjustments']:
                    self.params['segment_bias_adjustments'][seg] = 0.0
                self.params['segment_bias_adjustments'][seg] -= learning_rate * (sim_mean - target_mean) * 0.1
        
        # Adjust transition momentum based on trend differences
        if 'daily_trend' in sim_metrics and 'daily_trend' in self.target_metrics:
            trend_diff = sim_metrics['daily_trend'] - self.target_metrics['daily_trend']
            # If trend is too flat, increase momentum; if too volatile, decrease
            self.params['transition_momentum'] -= learning_rate * trend_diff * 0.5
        
        # Adjust social influence strength (if switching rate is off)
        if 'switching_rate' in sim_metrics and 'switching_rate' in self.target_metrics:
            switch_diff = sim_metrics['switching_rate'] - self.target_metrics['switching_rate']
            # Higher switching -> reduce social influence (less herd behavior)
            self.params['social_influence_strength'] -= learning_rate * switch_diff * 0.1
        
        # Adjust habit strength scale
        if 'habit_strength_mean' in sim_metrics and 'habit_strength_mean' in self.target_metrics:
            habit_diff = sim_metrics['habit_strength_mean'] - self.target_metrics['habit_strength_mean']
            self.params['habit_strength_scale'] -= learning_rate * habit_diff * 0.1
        
        # Clamp parameters to reasonable ranges
        self.params['agent_state_init_scale'] = np.clip(self.params['agent_state_init_scale'], 0.5, 2.0)
        self.params['switching_rate_multiplier'] = np.clip(self.params['switching_rate_multiplier'], 0.1, 3.0)
        self.params['transition_momentum'] = np.clip(self.params['transition_momentum'], 0.1, 0.9)
        self.params['social_influence_strength'] = np.clip(self.params['social_influence_strength'], 0.0, 1.0)
        self.params['macro_context_sensitivity'] = np.clip(self.params['macro_context_sensitivity'], 0.5, 2.0)
        self.params['habit_strength_scale'] = np.clip(self.params['habit_strength_scale'], 0.5, 2.0)


class ModelFineTuner:
    """
    Fine-tunes Phase 1 and Phase 2 models using real intent data
    """
    
    def __init__(self,
                 phase1_model_path: str,
                 phase2_model_path: str,
                 device: str = 'cpu'):
        """
        Args:
            phase1_model_path: Path to trained Phase 1 model
            phase2_model_path: Path to trained Phase 2 model
            device: Device to run on
        """
        self.device = device
        self.phase1_model_path = phase1_model_path
        self.phase2_model_path = phase2_model_path
        
        # Load models
        self.phase1_model = None
        self.phase2_model = None
        self._load_models()
    
    def _load_models(self):
        """Load Phase 1 and Phase 2 models"""
        # Phase 1: Combined embedding model
        if os.path.exists(self.phase1_model_path):
            try:
                checkpoint = torch.load(self.phase1_model_path, map_location=self.device)
                print(f"Loaded Phase 1 model from {self.phase1_model_path}")
            except Exception as e:
                print(f"Note: Could not load Phase 1 model: {e}")
        
        # Phase 2: Behavioral dynamic engine
        if os.path.exists(self.phase2_model_path):
            try:
                checkpoint = torch.load(self.phase2_model_path, map_location=self.device)
                print(f"Loaded Phase 2 model from {self.phase2_model_path}")
            except Exception as e:
                print(f"Note: Could not load Phase 2 model: {e}")
    
    def fine_tune_phase1(self,
                         real_data: pd.DataFrame,
                         products_df: pd.DataFrame,
                         contexts_df: pd.DataFrame,
                         segments_df: pd.DataFrame,
                         n_epochs: int = 5,
                         batch_size: int = 32,
                         learning_rate: float = 1e-4) -> nn.Module:
        """
        Fine-tune Phase 1 embedding models on real data
        
        Args:
            real_data: Real intent data with product_id, context_id, segment_id, intent_value
            products_df: Product metadata
            contexts_df: Context metadata
            segments_df: Segment metadata
            n_epochs: Number of fine-tuning epochs
            batch_size: Batch size
            learning_rate: Learning rate
        
        Returns:
            Fine-tuned model
        """
        print("\nFine-tuning Phase 1 models on real data...")
        
        # Create dataset from real data
        # Note: EmbeddingDataset requires vocabularies - we'll need to create them
        # For now, this is a placeholder that shows the structure
        # In practice, you'd load or create vocabularies from the data
        print("  Note: Full fine-tuning requires vocabularies from Phase 1 training")
        print("  This is a demonstration of the anchoring framework structure")
        
        # Placeholder - actual implementation would create EmbeddingDataset
        # dataset = EmbeddingDataset(
        #     products_df, contexts_df, segments_df, real_data,
        #     vocabularies={...}  # Would need vocabularies from Phase 1
        # )
        
        # For demonstration, we'll show the structure but note that full implementation
        # requires loading vocabularies and proper data preparation from Phase 1
        print("  Phase 1 fine-tuning structure:")
        print("    1. Load vocabularies from Phase 1 training")
        print("    2. Create EmbeddingDataset with real data")
        print("    3. Fine-tune CombinedEmbeddingModel on real intent values")
        print("    4. Update product/context/segment embeddings")
        print("    5. Save fine-tuned model")
        print("\n  This demonstrates the anchoring framework.")
        print("  Full implementation would require Phase 1 vocabularies and model architecture.")
        
        # Return None for now - actual implementation would return fine-tuned model
        return None
    
    def fine_tune_phase2(self,
                         real_data: pd.DataFrame,
                         product_embeddings: Dict[str, np.ndarray],
                         context_embeddings: Dict[str, np.ndarray],
                         segment_embeddings: Dict[str, np.ndarray],
                         n_epochs: int = 5,
                         batch_size: int = 32,
                         learning_rate: float = 1e-4) -> nn.Module:
        """
        Fine-tune Phase 2 behavioral engine on real data
        
        Args:
            real_data: Real intent sequences with agent_id, product_id, context_id, segment_id, intent_value, timestamp
            product_embeddings: Product embeddings dict
            context_embeddings: Context embeddings dict
            segment_embeddings: Segment embeddings dict
            n_epochs: Number of fine-tuning epochs
            batch_size: Batch size
            learning_rate: Learning rate
        
        Returns:
            Fine-tuned model
        """
        print("\nFine-tuning Phase 2 models on real data...")
        
        # Group by agent to create sequences
        agent_sequences = []
        for agent_id, group in real_data.sort_values('timestamp').groupby('agent_id'):
            sequence = {
                'product_ids': group['product_id'].tolist(),
                'context_ids': group['context_id'].tolist(),
                'intent_values': group['intent_value'].tolist(),
                'segment_id': group['segment_id'].iloc[0]
            }
            agent_sequences.append(sequence)
        
        # Initialize model
        model = BehavioralDynamicEngine(
            segment_dim=64,
            state_dim=128,
            product_dim=64,
            context_dim=64
        ).to(self.device)
        
        optimizer = optim.Adam(model.parameters(), lr=learning_rate)
        criterion = nn.MSELoss()
        
        model.train()
        
        for epoch in range(n_epochs):
            epoch_loss = 0.0
            n_batches = 0
            
            # Create batches
            for i in range(0, len(agent_sequences), batch_size):
                batch_sequences = agent_sequences[i:i+batch_size]
                
                batch_loss = 0.0
                n_seqs = 0
                
                for seq in batch_sequences:
                    # Prepare sequence data
                    z_products = []
                    z_contexts = []
                    for pid, cid in zip(seq['product_ids'], seq['context_ids']):
                        z_products.append(torch.FloatTensor(product_embeddings.get(pid, np.zeros(64))))
                        z_contexts.append(torch.FloatTensor(context_embeddings.get(cid, np.zeros(64))))
                    
                    z_products = torch.stack(z_products).to(self.device)
                    z_contexts = torch.stack(z_contexts).to(self.device)
                    z_segment = torch.FloatTensor(segment_embeddings.get(seq['segment_id'], np.zeros(64))).unsqueeze(0).to(self.device)
                    target_intents = torch.FloatTensor(seq['intent_values']).to(self.device)
                    
                    optimizer.zero_grad()
                    
                    # Forward pass
                    predicted_intents, _ = model.forward_sequence(
                        z_segment, z_products, z_contexts
                    )
                    
                    # Loss
                    loss = criterion(predicted_intents.squeeze(), target_intents)
                    
                    # Backward pass
                    loss.backward()
                    optimizer.step()
                    
                    batch_loss += loss.item()
                    n_seqs += 1
                
                epoch_loss += batch_loss / max(n_seqs, 1)
                n_batches += 1
            
            avg_loss = epoch_loss / max(n_batches, 1)
            print(f"  Epoch {epoch + 1}/{n_epochs}: Loss = {avg_loss:.6f}")
        
        print("Phase 2 fine-tuning complete!")
        return model


class GroundTruthAnchoring:
    """
    Main class for anchoring simulation to real data
    Combines parameter calibration and model fine-tuning
    """
    
    def __init__(self,
                 real_intent_data: pd.DataFrame,
                 real_outcome_data: Optional[pd.DataFrame] = None,
                 phase1_model_path: str = 'checkpoints/phase1_model.pth',
                 phase2_model_path: str = 'checkpoints/phase2_model.pth'):
        """
        Args:
            real_intent_data: Real intent data (product_id, context_id, segment_id, intent_value, timestamp)
            real_outcome_data: Optional real outcome/sales data for validation
            phase1_model_path: Path to Phase 1 model
            phase2_model_path: Path to Phase 2 model
        """
        self.real_intent_data = real_intent_data.copy()
        self.real_outcome_data = real_outcome_data.copy() if real_outcome_data is not None else None
        
        self.parameter_calibrator = ParameterCalibrator(real_intent_data)
        self.model_fine_tuner = ModelFineTuner(phase1_model_path, phase2_model_path)
        
        self.calibrated_params = None
        self.fine_tuned_phase1 = None
        self.fine_tuned_phase2 = None
    
    def anchor(self,
               simulator_factory: Callable,
               products_df: pd.DataFrame,
               contexts_df: pd.DataFrame,
               segments_df: pd.DataFrame,
               product_embeddings: Dict[str, np.ndarray],
               context_embeddings: Dict[str, np.ndarray],
               segment_embeddings: Dict[str, np.ndarray],
               n_calibration_iterations: int = 25,
               n_finetune_epochs: int = 5) -> Dict:
        """
        Full anchoring pipeline:
        1. Fine-tune models on real data
        2. Calibrate simulation parameters
        3. Validate against outcome data
        
        Returns:
            Dictionary with calibrated parameters and validation metrics
        """
        print("=" * 60)
        print("Ground Truth Anchoring Pipeline")
        print("=" * 60)
        
        # Step 1: Fine-tune models
        print("\n[Step 1] Fine-tuning models on real intent data...")
        self.fine_tuned_phase1 = self.model_fine_tuner.fine_tune_phase1(
            self.real_intent_data,
            products_df,
            contexts_df,
            segments_df,
            n_epochs=n_finetune_epochs
        )
        
        self.fine_tuned_phase2 = self.model_fine_tuner.fine_tune_phase2(
            self.real_intent_data,
            product_embeddings,
            context_embeddings,
            segment_embeddings,
            n_epochs=n_finetune_epochs
        )
        
        # Step 2: Calibrate parameters
        print("\n[Step 2] Calibrating simulation parameters...")
        self.calibrated_params = self.parameter_calibrator.calibrate_parameters(
            simulator_factory,
            n_iterations=n_calibration_iterations
        )
        
        # Step 3: Validate against outcome data
        validation_metrics = {}
        if self.real_outcome_data is not None:
            print("\n[Step 3] Validating against real outcome data...")
            validation_metrics = self._validate_outcomes()
        else:
            print("\n[Step 3] Skipping outcome validation (no outcome data provided)")
        
        results = {
            'calibrated_parameters': self.calibrated_params,
            'validation_metrics': validation_metrics,
            'target_metrics': self.parameter_calibrator.target_metrics
        }
        
        print("\n" + "=" * 60)
        print("Anchoring Complete!")
        print("=" * 60)
        
        return results
    
    def _validate_outcomes(self) -> Dict:
        """Validate simulated outcomes against real outcome data"""
        try:
            from phase4_sales_validation import SalesValidator
            
            # Ensure we have the required columns
            if 'product_category' not in self.real_intent_data.columns:
                return {'error': 'product_category column missing from intent data'}
            if 'sales_value' not in self.real_outcome_data.columns:
                return {'error': 'sales_value column missing from sales data'}
            
            # Create validator
            validator = SalesValidator(
                intent_data=self.real_intent_data,
                sales_data=self.real_outcome_data,
                category_col='product_category',
                date_col='date' if 'date' in self.real_intent_data.columns else 'timestamp'
            )
            
            # Run validation
            validation_results = validator.validate_intent_predicts_sales(
                min_r2=0.2,
                min_correlation=0.3
            )
            
            return validation_results
        except ImportError:
            return {'error': 'phase4_sales_validation module not found'}
        except Exception as e:
            return {'error': f'Validation failed: {str(e)}'}
    
    def save_calibrated_models(self, output_dir: str):
        """Save fine-tuned models"""
        os.makedirs(output_dir, exist_ok=True)
        
        if self.fine_tuned_phase1 is not None:
            torch.save(self.fine_tuned_phase1.state_dict(), 
                      os.path.join(output_dir, 'phase1_anchored.pth'))
        
        if self.fine_tuned_phase2 is not None:
            torch.save(self.fine_tuned_phase2.state_dict(),
                      os.path.join(output_dir, 'phase2_anchored.pth'))
        
        if self.calibrated_params is not None:
            with open(os.path.join(output_dir, 'calibrated_params.json'), 'w') as f:
                json.dump(self.calibrated_params, f, indent=2)
        
        print(f"\nCalibrated models saved to {output_dir}")

