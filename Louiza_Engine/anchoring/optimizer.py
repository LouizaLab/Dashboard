"""
Optimization strategy for anchoring.

Implements persona weight calibration and optional behavioral parameter adjustment.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Tuple, Any
from scipy.optimize import minimize, minimize_scalar
from scipy.optimize import Bounds

from anchoring.objective import AnchoringObjective
from pme.persona_schema import PersonaSet, Persona


class AnchoringOptimizer:
    """
    Optimizer for anchoring calibration.
    
    Implements two-step optimization:
    1. Persona weight calibration (required)
    2. Optional behavioral parameter calibration
    """
    
    def __init__(
        self,
        objective: AnchoringObjective,
        personaset: PersonaSet,
        max_iterations: int = 1000,
        tolerance: float = 1e-8
    ):
        """
        Initialize optimizer.
        
        Args:
            objective: AnchoringObjective instance
            personaset: PersonaSet to calibrate
            max_iterations: Maximum optimization iterations
            tolerance: Convergence tolerance
        """
        self.objective = objective
        self.personaset = personaset
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        
        # Get active personas
        self.active_personas = personaset.get_active_personas()
        self.persona_ids = [p.persona_id for p in self.active_personas]
        
        # Store base parameters
        self.base_weights = {p.persona_id: p.population_weight.global_weight for p in self.active_personas}
    
    def optimize_global_scale(
        self,
        train_data: Optional[pd.DataFrame] = None
    ) -> float:
        """
        Optimize global scaling factor to match overall magnitude.
        
        This addresses systematic bias where simulated values are consistently
        too high or too low compared to observed.
        
        Args:
            train_data: Optional training data subset
            
        Returns:
            Optimal global scale factor
        """
        if train_data is None:
            train_data = self.objective.aligned_data
        
        # Compute observed and simulated totals
        obs_total = train_data["transactions_obs"].sum()
        sim_total = train_data["transactions_sim"].sum()
        
        if sim_total > 0:
            # For very large scale mismatches (>100x), use direct ratio
            # Optimization can get stuck in local minima for extreme mismatches
            initial_scale = obs_total / sim_total
            print(f"  Initial scale estimate: {initial_scale:.2f}x (obs={obs_total:.0f}, sim={sim_total:.0f})")
            
            # For very large scale mismatches, use optimization but with better bounds
            # We'll optimize around a reasonable range to avoid overfitting
            if initial_scale > 1000.0:
                # Use optimization with bounds around 100-2000x range
                # This allows finding a good balance without extreme overfitting
                print(f"  Very large scale mismatch ({initial_scale:.0f}x), optimizing in 100-2000x range")
                # Continue to optimization below
            elif initial_scale > 100.0:
                # For moderate-large mismatches, optimize in a range around initial
                print(f"  Large scale mismatch ({initial_scale:.0f}x), optimizing")
                # Continue to optimization below
        else:
            initial_scale = 1.0
            print(f"  Warning: Simulated total is zero, using initial scale = 1.0")
            return initial_scale
        
        # For smaller mismatches, refine with optimization
        from scipy.optimize import minimize_scalar
        
        def objective_func(scale):
            scaled_metrics = self.objective.scale_simulated_by_weights(
                self.base_weights,
                base_weights=self.base_weights,
                global_scale=scale
            )
            
            merged = pd.merge(
                train_data[["week_id", "brand_id", "region_id", "transactions_obs", "revenue_obs", "confidence_weight"]],
                scaled_metrics,
                on=["week_id", "brand_id", "region_id"],
                how="inner"
            )
            
            if len(merged) == 0:
                return 1e10  # Penalty for no matches
            
            if self.objective.use_relative_error:
                transaction_error = ((merged["transactions_obs"] - merged["transactions_sim"]) / 
                                    (merged["transactions_obs"] + self.objective.epsilon)) ** 2
            else:
                transaction_error = (merged["transactions_obs"] - merged["transactions_sim"]) ** 2
            
            if "confidence_weight" in merged.columns:
                transaction_error = transaction_error * merged["confidence_weight"]
            
            return self.objective.alpha * transaction_error.sum()
        
        # Optimize scale factor - use smart bounds based on initial estimate
        if initial_scale > 1000.0:
            # For very large mismatches, optimize in a reasonable range (100-2000x)
            lower_bound = 100.0
            upper_bound = 2000.0
        elif initial_scale > 100.0:
            # For large mismatches, optimize in range around initial (50% to 200%)
            lower_bound = max(0.01, initial_scale * 0.5)
            upper_bound = min(10000.0, initial_scale * 2.0)
        else:
            # For smaller mismatches, optimize in wider range
            lower_bound = max(0.01, initial_scale * 0.1)
            upper_bound = min(10000.0, initial_scale * 10.0)
        
        result = minimize_scalar(
            objective_func,
            bounds=(lower_bound, upper_bound),
            method='bounded',
            options={'maxiter': 200, 'xatol': 1e-3}
        )
        
        optimized_scale = float(result.x)
        print(f"  Optimized scale: {optimized_scale:.2f}x")
        
        return optimized_scale
    
    def optimize_weights(
        self,
        train_data: Optional[pd.DataFrame] = None,
        global_scale: float = 1.0
    ) -> Dict[str, float]:
        """
        Optimize persona weights (Step 1).
        
        Uses constrained optimization to ensure weights sum to 1.0.
        
        Args:
            train_data: Optional training data subset
            
        Returns:
            Dictionary mapping persona_id to optimized weight
        """
        # Use full data if train_data not provided
        if train_data is None:
            train_data = self.objective.aligned_data
        
        # Initial weights (normalized)
        initial_weights = np.array([self.base_weights[pid] for pid in self.persona_ids])
        initial_weights = initial_weights / initial_weights.sum()
        
        # Bounds: weights must be >= 0 and constrained to prevent extreme adjustments
        # Limit weight changes to prevent overfitting: weights can't be more than 5x base weight
        # This prevents the optimizer from making extreme adjustments that overfit
        max_weight_multiplier = 5.0
        lb_list = []
        ub_list = []
        for pid in self.persona_ids:
            base_w = self.base_weights[pid]
            # Allow weights to range from 0.1x base to max_weight_multiplier * base_weight
            # But ensure at least a small minimum (0.001) to prevent zero weights
            lb_list.append(max(0.001, base_w * 0.1))
            ub_list.append(base_w * max_weight_multiplier)
        bounds = Bounds(lb=lb_list, ub=ub_list)
        
        # Constraint: weights must sum to 1.0
        def weight_sum_constraint(x):
            return x.sum() - 1.0
        
        constraints = [{"type": "eq", "fun": weight_sum_constraint}]
        
        # Objective function
        def objective_func(x):
            weights_dict = {pid: w for pid, w in zip(self.persona_ids, x)}
            scaled_metrics = self.objective.scale_simulated_by_weights(
                weights_dict, 
                base_weights=self.base_weights,
                global_scale=global_scale
            )
            
            # Merge with train_data
            merged = pd.merge(
                train_data[["week_id", "brand_id", "region_id", "transactions_obs", "revenue_obs", "confidence_weight"]],
                scaled_metrics,
                on=["week_id", "brand_id", "region_id"],
                how="inner"
            )
            
            # Compute loss (using same error type as objective)
            if self.objective.use_relative_error:
                transaction_error = ((merged["transactions_obs"] - merged["transactions_sim"]) / 
                                    (merged["transactions_obs"] + self.objective.epsilon)) ** 2
                revenue_error = ((merged["revenue_obs"] - merged["revenue_sim"]) / 
                                (merged["revenue_obs"] + self.objective.epsilon)) ** 2
            else:
                transaction_error = (merged["transactions_obs"] - merged["transactions_sim"]) ** 2
                revenue_error = (merged["revenue_obs"] - merged["revenue_sim"]) ** 2
            
            if "confidence_weight" in merged.columns:
                transaction_error = transaction_error * merged["confidence_weight"]
                revenue_error = revenue_error * merged["confidence_weight"]
            
            loss = self.objective.alpha * transaction_error.sum() + self.objective.beta * revenue_error.sum()
            
            # Regularization: penalize deviations from base weights
            # Use relative deviation to normalize by base weight magnitude
            deltas = {}
            for i, pid in enumerate(self.persona_ids):
                base_w = self.base_weights[pid]
                if base_w > 0:
                    # Relative deviation: (new_weight - base_weight) / base_weight
                    relative_delta = (x[i] - base_w) / base_w
                    deltas[pid] = relative_delta
                else:
                    deltas[pid] = x[i]  # Absolute deviation if base is zero
            
            # Regularization: penalize squared relative deviations
            reg = self.objective.lambda_reg * sum(d ** 2 for d in deltas.values())
            
            return loss + reg
        
        # Optimize
        result = minimize(
            objective_func,
            initial_weights,
            method="SLSQP",
            bounds=bounds,
            constraints=constraints,
            options={"maxiter": self.max_iterations * 5, "ftol": self.tolerance * 10, "disp": False}
        )
        
        # Handle optimization failures more gracefully
        if not result.success:
            # Check if we got a result anyway
            if hasattr(result, 'x') and result.x is not None and len(result.x) > 0:
                # Check if result is reasonable (all positive, sum close to 1)
                if np.all(result.x > 0) and abs(result.x.sum() - 1.0) < 0.1:
                    # Normalize result to ensure sum = 1.0
                    result.x = result.x / result.x.sum()
                    print(f"Warning: Optimization had issues ({result.message}), but using normalized result")
                    print(f"  Final function value: {result.fun:.2f}")
                else:
                    # Result is not reasonable, try with increased regularization
                    print(f"Warning: Optimization failed ({result.message}), trying with increased regularization...")
                    original_lambda = self.objective.lambda_reg
                    self.objective.lambda_reg = original_lambda * 5.0
                    
                    # Retry optimization
                    result_retry = minimize(
                        objective_func,
                        initial_weights,
                        method="SLSQP",
                        bounds=bounds,
                        constraints=constraints,
                        options={"maxiter": self.max_iterations * 3, "ftol": self.tolerance * 100, "disp": False}
                    )
                    
                    self.objective.lambda_reg = original_lambda
                    
                    if result_retry.success or (hasattr(result_retry, 'x') and result_retry.x is not None and np.all(result_retry.x > 0)):
                        result = result_retry
                        if not result.success:
                            result.x = result.x / result.x.sum()
                            print(f"  Retry succeeded with increased regularization")
                    else:
                        raise RuntimeError(f"Weight optimization failed even with increased regularization: {result_retry.message}")
            else:
                # No result at all, try with increased regularization
                print(f"Warning: Optimization failed ({result.message}), trying with increased regularization...")
                original_lambda = self.objective.lambda_reg
                self.objective.lambda_reg = original_lambda * 5.0
                
                result_retry = minimize(
                    objective_func,
                    initial_weights,
                    method="SLSQP",
                    bounds=bounds,
                    constraints=constraints,
                    options={"maxiter": self.max_iterations * 3, "ftol": self.tolerance * 100, "disp": False}
                )
                
                self.objective.lambda_reg = original_lambda
                
                if result_retry.success or (hasattr(result_retry, 'x') and result_retry.x is not None and np.all(result_retry.x > 0)):
                    result = result_retry
                    if not result.success:
                        result.x = result.x / result.x.sum()
                        print(f"  Retry succeeded with increased regularization")
                else:
                    raise RuntimeError(f"Weight optimization failed: {result.message}")
        
        # Ensure weights sum to 1.0 (normalize if needed)
        if abs(result.x.sum() - 1.0) > 1e-6:
            result.x = result.x / result.x.sum()
        
        # Return optimized weights
        optimized_weights = {pid: w for pid, w in zip(self.persona_ids, result.x)}
        
        return optimized_weights
    
    def optimize_behavioral_param(
        self,
        param_name: str,
        persona_id: Optional[str] = None,
        train_data: Optional[pd.DataFrame] = None
    ) -> Tuple[float, Dict[str, float]]:
        """
        Optimize a single behavioral parameter (Step 2, optional).
        
        Args:
            param_name: Name of parameter to optimize (e.g., "price_sensitivity")
            persona_id: Optional persona ID (if None, applies globally)
            train_data: Optional training data subset
            
        Returns:
            Tuple of (optimized_value, updated_weights_dict)
        """
        if train_data is None:
            train_data = self.objective.aligned_data
        
        # Get base parameter value
        if persona_id:
            persona = self.personaset.get_persona_by_id(persona_id)
            if not persona:
                raise ValueError(f"Persona {persona_id} not found")
            base_value = getattr(persona.behavioral_params, param_name, None)
            if base_value is None:
                raise ValueError(f"Parameter {param_name} not found in persona {persona_id}")
        else:
            # Use average across personas
            values = [getattr(p.behavioral_params, param_name, None) for p in self.active_personas]
            values = [v for v in values if v is not None]
            if not values:
                raise ValueError(f"Parameter {param_name} not found in any persona")
            base_value = np.mean(values)
        
        # Bounds: allow ±50% change
        bounds = Bounds(lb=base_value * 0.5, ub=base_value * 1.5)
        
        # Objective function
        def objective_func(x):
            # Create temporary persona with updated parameter
            # For simplicity, we'll scale simulated metrics by a factor
            # This is a simplified approach; full implementation would re-run simulation
            scale_factor = x / base_value
            
            # Scale persona contributions
            scaled_contributions = self.objective.persona_contributions.copy()
            if persona_id:
                mask = scaled_contributions["persona_id"] == persona_id
            else:
                mask = scaled_contributions["persona_id"].isin(self.persona_ids)
            
            scaled_contributions.loc[mask, "transactions_sim"] *= scale_factor
            scaled_contributions.loc[mask, "revenue_sim"] *= scale_factor
            
            # Aggregate
            scaled_metrics = scaled_contributions.groupby(
                ["week_id", "brand_id", "region_id"]
            ).agg({
                "transactions_sim": "sum",
                "revenue_sim": "sum"
            }).reset_index()
            
            # Merge with train_data
            merged = pd.merge(
                train_data[["week_id", "brand_id", "region_id", "transactions_obs", "revenue_obs", "confidence_weight"]],
                scaled_metrics,
                on=["week_id", "brand_id", "region_id"],
                how="inner"
            )
            
            # Compute loss (using same error type as objective)
            if self.objective.use_relative_error:
                transaction_error = ((merged["transactions_obs"] - merged["transactions_sim"]) / 
                                    (merged["transactions_obs"] + self.objective.epsilon)) ** 2
                revenue_error = ((merged["revenue_obs"] - merged["revenue_sim"]) / 
                                (merged["revenue_obs"] + self.objective.epsilon)) ** 2
            else:
                transaction_error = (merged["transactions_obs"] - merged["transactions_sim"]) ** 2
                revenue_error = (merged["revenue_obs"] - merged["revenue_sim"]) ** 2
            
            if "confidence_weight" in merged.columns:
                transaction_error = transaction_error * merged["confidence_weight"]
                revenue_error = revenue_error * merged["confidence_weight"]
            
            loss = self.objective.alpha * transaction_error.sum() + self.objective.beta * revenue_error.sum()
            
            # Strong regularization
            delta = x - base_value
            reg = 10.0 * self.objective.lambda_reg * (delta ** 2)
            
            return loss + reg
        
        # Optimize
        result = minimize(
            objective_func,
            base_value,
            method="L-BFGS-B",
            bounds=bounds,
            options={"maxiter": self.max_iterations * 2, "ftol": self.tolerance, "disp": True}
        )
        
        if not result.success:
            raise RuntimeError(f"Parameter optimization failed: {result.message}")
        
        return result.x[0], self.base_weights.copy()

