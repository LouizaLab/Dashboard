"""
Environment state and updates for LPM.

Manages market environment: prices, promotions, availability, context.
"""

import numpy as np
import pandas as pd
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from datetime import datetime

from data_engine.loaders import DataLoader


@dataclass
class EnvironmentState:
    """Environment state at a timestep."""
    prices: np.ndarray  # [B] prices per brand
    promotions: np.ndarray  # [B] promotion intensities
    availability: np.ndarray  # [B] availability scores
    ads: np.ndarray  # [B] advertising signals
    context: Dict[str, Any]  # week_id, season, etc.
    brand_ids: List[str]  # Brand IDs
    region_id: str  # Region ID


class EnvironmentManager:
    """
    Manages environment state and evolution.
    
    Loads schedules from Data Engine and applies scenario interventions.
    """
    
    def __init__(
        self,
        data_loader: DataLoader,
        region_id: str,
        brand_ids: List[str],
        scenario_config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize environment manager.
        
        Args:
            data_loader: DataLoader for accessing schedules
            region_id: Region ID
            brand_ids: List of brand IDs
            scenario_config: Optional scenario configuration with interventions
        """
        self.data_loader = data_loader
        self.region_id = region_id
        self.brand_ids = brand_ids
        self.scenario_config = scenario_config or {}
        
        # Load schedules
        self.price_schedule = self._load_schedule("brand_price_schedule")
        self.promo_schedule = self._load_schedule("brand_promo_schedule")
        self.availability_schedule = self._load_schedule("brand_menu_availability")
        
        # Initialize brand index mapping
        self.brand_to_idx = {brand_id: i for i, brand_id in enumerate(brand_ids)}
    
    def _load_schedule(self, table_name: str) -> pd.DataFrame:
        """Load a schedule table."""
        df = self.data_loader.load_table(table_name)
        
        # Filter by region
        if "region_id" in df.columns:
            df = df[df["region_id"] == self.region_id]
        
        return df
    
    def get_environment(self, week_id: int, timestep: int = 0) -> EnvironmentState:
        """
        Get environment state for a given week.
        
        Args:
            week_id: Week ID
            timestep: Timestep within week (for sub-week granularity)
            
        Returns:
            EnvironmentState
        """
        # Get base values from schedules
        prices = np.zeros(len(self.brand_ids), dtype=np.float32)
        promotions = np.zeros(len(self.brand_ids), dtype=np.float32)
        availability = np.ones(len(self.brand_ids), dtype=np.float32)
        ads = np.zeros(len(self.brand_ids), dtype=np.float32)
        
        # Load from schedules
        week_data_price = self.price_schedule[self.price_schedule["week_id"] == week_id]
        week_data_promo = self.promo_schedule[self.promo_schedule["week_id"] == week_id]
        week_data_avail = self.availability_schedule[self.availability_schedule["week_id"] == week_id]
        
        for _, row in week_data_price.iterrows():
            brand_id = row["brand_id"]
            if brand_id in self.brand_to_idx:
                idx = self.brand_to_idx[brand_id]
                prices[idx] = row["price_index"]
        
        for _, row in week_data_promo.iterrows():
            brand_id = row["brand_id"]
            if brand_id in self.brand_to_idx:
                idx = self.brand_to_idx[brand_id]
                promotions[idx] = row["promo_intensity"]
        
        for _, row in week_data_avail.iterrows():
            brand_id = row["brand_id"]
            if brand_id in self.brand_to_idx:
                idx = self.brand_to_idx[brand_id]
                availability[idx] = row["availability_score"]
        
        # Apply scenario interventions
        prices, promotions, availability = self._apply_interventions(
            week_id, prices, promotions, availability
        )
        
        return EnvironmentState(
            prices=prices,
            promotions=promotions,
            availability=availability,
            ads=ads,
            context={
                "week_id": week_id,
                "timestep": timestep,
                "season": self._get_season(week_id)
            },
            brand_ids=self.brand_ids,
            region_id=self.region_id
        )
    
    def _apply_interventions(
        self,
        week_id: int,
        prices: np.ndarray,
        promotions: np.ndarray,
        availability: np.ndarray
    ) -> tuple:
        """Apply scenario interventions."""
        interventions = self.scenario_config.get("interventions", [])
        
        for intervention in interventions:
            intervention_type = intervention.get("type")
            start_week = intervention.get("start_week", 0)
            end_week = intervention.get("end_week", 9999)
            
            if not (start_week <= week_id <= end_week):
                continue
            
            brand_id = intervention.get("brand_id")
            region_id = intervention.get("region_id")
            
            # Check if intervention applies to this region
            if region_id and region_id != self.region_id:
                continue
            
            if brand_id not in self.brand_to_idx:
                continue
            
            idx = self.brand_to_idx[brand_id]
            
            if intervention_type == "price_change":
                delta_pct = intervention.get("delta_pct", 0.0)
                prices[idx] *= (1.0 + delta_pct)
            
            elif intervention_type == "promo":
                intensity = intervention.get("intensity", 0.0)
                promotions[idx] = intensity
            
            elif intervention_type == "menu_launch":
                # Increase availability
                availability[idx] = min(1.0, availability[idx] + 0.1)
        
        return prices, promotions, availability
    
    def _get_season(self, week_id: int) -> str:
        """Get season from week ID (simplified)."""
        # Simple mapping: assume 52 weeks per year
        week_in_year = (week_id - 1) % 52
        
        if week_in_year < 13:
            return "winter"
        elif week_in_year < 26:
            return "spring"
        elif week_in_year < 39:
            return "summer"
        else:
            return "fall"

