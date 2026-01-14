"""
Objective function for anchoring calibration.

Implements the regularized error objective for aligning simulated and observed metrics.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple


class AnchoringObjective:
    """
    Objective function for anchoring.
    
    Minimizes weighted squared error between observed and simulated metrics,
    with regularization on parameter changes.
    """
    
    def __init__(
        self,
        observed_metrics: pd.DataFrame,
        simulated_metrics: pd.DataFrame,
        persona_contributions: pd.DataFrame,
        alpha: float = 1.0,
        beta: float = 0.5,
        lambda_reg: float = 0.01,
        use_relative_error: bool = True,
        epsilon: float = 1e-6
    ):
        """
        Initialize objective function.
        
        Args:
            observed_metrics: DataFrame with columns [week_id, brand_id, region_id, transactions_obs, revenue_obs, confidence_weight]
            simulated_metrics: DataFrame with columns [week_id, brand_id, region_id, transactions_sim, revenue_sim]
            persona_contributions: DataFrame with columns [week_id, brand_id, region_id, persona_id, transactions_sim, revenue_sim]
            alpha: Weight for transactions error
            beta: Weight for revenue error
            lambda_reg: Regularization strength
        """
        self.observed_metrics = observed_metrics.copy()
        self.simulated_metrics = simulated_metrics.copy()
        self.persona_contributions = persona_contributions.copy()
        self.alpha = alpha
        self.beta = beta
        self.lambda_reg = lambda_reg
        self.use_relative_error = use_relative_error
        self.epsilon = epsilon
        
        # Align and merge tables
        self.aligned_data = self._align_data()
    
    def _align_data(self) -> pd.DataFrame:
        """Align observed and simulated metrics."""
        # Merge on week_id, brand_id, region_id
        merged = pd.merge(
            self.observed_metrics,
            self.simulated_metrics,
            on=["week_id", "brand_id", "region_id"],
            how="inner"
        )
        
        # Mask missing or low-confidence data
        if "confidence_weight" in merged.columns:
            merged = merged[merged["confidence_weight"] > 0.1]
        
        return merged
    
    def compute_loss(
        self,
        simulated_metrics_scaled: pd.DataFrame,
        parameter_deltas: Dict[str, float],
        base_parameters: Dict[str, float]
    ) -> float:
        """
        Compute objective loss.
        
        Args:
            simulated_metrics_scaled: Scaled simulated metrics (after parameter adjustment)
            parameter_deltas: Dictionary of parameter changes
            base_parameters: Base parameter values
            
        Returns:
            Total loss value
        """
        # Merge scaled simulated metrics with observed
        merged = pd.merge(
            self.aligned_data[["week_id", "brand_id", "region_id", "transactions_obs", "revenue_obs", "confidence_weight"]],
            simulated_metrics_scaled,
            on=["week_id", "brand_id", "region_id"],
            how="inner"
        )
        
        # Compute errors (relative or absolute)
        if self.use_relative_error:
            # Relative error: ((obs - sim) / (obs + epsilon))^2
            # This normalizes by observed value, making small and large values equally important
            transaction_error = ((merged["transactions_obs"] - merged["transactions_sim"]) / 
                                (merged["transactions_obs"] + self.epsilon)) ** 2
            revenue_error = ((merged["revenue_obs"] - merged["revenue_sim"]) / 
                            (merged["revenue_obs"] + self.epsilon)) ** 2
        else:
            # Absolute squared error
            transaction_error = (merged["transactions_obs"] - merged["transactions_sim"]) ** 2
            revenue_error = (merged["revenue_obs"] - merged["revenue_sim"]) ** 2
        
        # Apply confidence weights
        if "confidence_weight" in merged.columns:
            transaction_error = transaction_error * merged["confidence_weight"]
            revenue_error = revenue_error * merged["confidence_weight"]
        
        # Sum errors
        transaction_loss = self.alpha * transaction_error.sum()
        revenue_loss = self.beta * revenue_error.sum()
        
        # Regularization term
        reg_loss = 0.0
        for param_name, delta in parameter_deltas.items():
            base_value = base_parameters.get(param_name, 0.0)
            reg_loss += self.lambda_reg * (delta ** 2)
        
        total_loss = transaction_loss + revenue_loss + reg_loss
        
        return total_loss
    
    def compute_baseline_loss(self) -> float:
        """Compute baseline loss (before calibration)."""
        # Use original simulated metrics
        merged = self.aligned_data.copy()
        
        # Compute errors (relative or absolute)
        if self.use_relative_error:
            transaction_error = ((merged["transactions_obs"] - merged["transactions_sim"]) / 
                                (merged["transactions_obs"] + self.epsilon)) ** 2
            revenue_error = ((merged["revenue_obs"] - merged["revenue_sim"]) / 
                            (merged["revenue_obs"] + self.epsilon)) ** 2
        else:
            transaction_error = (merged["transactions_obs"] - merged["transactions_sim"]) ** 2
            revenue_error = (merged["revenue_obs"] - merged["revenue_sim"]) ** 2
        
        if "confidence_weight" in merged.columns:
            transaction_error = transaction_error * merged["confidence_weight"]
            revenue_error = revenue_error * merged["confidence_weight"]
        
        transaction_loss = self.alpha * transaction_error.sum()
        revenue_loss = self.beta * revenue_error.sum()
        
        return transaction_loss + revenue_loss
    
    def scale_simulated_by_weights(
        self,
        persona_weights: Dict[str, float],
        base_weights: Optional[Dict[str, float]] = None,
        global_scale: float = 1.0
    ) -> pd.DataFrame:
        """
        Scale simulated metrics by persona weights.
        
        Args:
            persona_weights: Dictionary mapping persona_id to new weight
            base_weights: Optional dictionary mapping persona_id to base weight
                         (if None, assumes weights are normalized and scales proportionally)
            
        Returns:
            Scaled simulated metrics DataFrame
        """
        # Start with persona contributions
        scaled_contributions = self.persona_contributions.copy()
        
        # Ensure float dtype to avoid warnings
        scaled_contributions["transactions_sim"] = scaled_contributions["transactions_sim"].astype(float)
        scaled_contributions["revenue_sim"] = scaled_contributions["revenue_sim"].astype(float)
        
        if base_weights:
            # Scale relative to base weights
            for persona_id, new_weight in persona_weights.items():
                base_weight = base_weights.get(persona_id, new_weight)
                if base_weight > 0:
                    scale_factor = new_weight / base_weight
                else:
                    scale_factor = 1.0
                
                mask = scaled_contributions["persona_id"] == persona_id
                scaled_contributions.loc[mask, "transactions_sim"] *= scale_factor
                scaled_contributions.loc[mask, "revenue_sim"] *= scale_factor
        else:
            # Scale by weight ratio (assumes original weights sum to 1.0)
            # This is a simplified approach - multiply by new weight and renormalize
            total_new_weight = sum(persona_weights.values())
            if total_new_weight > 0:
                for persona_id, weight in persona_weights.items():
                    mask = scaled_contributions["persona_id"] == persona_id
                    # Scale proportionally to weight change
                    scale_factor = weight / (1.0 / len(persona_weights)) if len(persona_weights) > 0 else 1.0
                    scaled_contributions.loc[mask, "transactions_sim"] *= scale_factor
                    scaled_contributions.loc[mask, "revenue_sim"] *= scale_factor
        
        # Aggregate across personas
        scaled_metrics = scaled_contributions.groupby(
            ["week_id", "brand_id", "region_id"]
        ).agg({
            "transactions_sim": "sum",
            "revenue_sim": "sum"
        }).reset_index()
        
        # Apply global scaling factor
        scaled_metrics["transactions_sim"] *= global_scale
        scaled_metrics["revenue_sim"] *= global_scale
        
        return scaled_metrics
    
    def get_holdout_split(
        self,
        train_weeks: Optional[List[int]] = None,
        holdout_weeks: Optional[List[int]] = None,
        train_ratio: float = 0.8
    ) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Split data into training and holdout sets.
        
        Args:
            train_weeks: Optional explicit list of training weeks
            holdout_weeks: Optional explicit list of holdout weeks
            train_ratio: Ratio for train/holdout split if weeks not specified
            
        Returns:
            Tuple of (train_data, holdout_data)
        """
        if train_weeks is not None and holdout_weeks is not None:
            train_data = self.aligned_data[self.aligned_data["week_id"].isin(train_weeks)]
            holdout_data = self.aligned_data[self.aligned_data["week_id"].isin(holdout_weeks)]
        else:
            # Split by weeks
            all_weeks = sorted(self.aligned_data["week_id"].unique())
            split_idx = int(len(all_weeks) * train_ratio)
            train_weeks = all_weeks[:split_idx]
            holdout_weeks = all_weeks[split_idx:]
            
            train_data = self.aligned_data[self.aligned_data["week_id"].isin(train_weeks)]
            holdout_data = self.aligned_data[self.aligned_data["week_id"].isin(holdout_weeks)]
        
        return train_data, holdout_data

