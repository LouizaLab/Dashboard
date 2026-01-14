"""
Agent state schema and management for IBDE.

Defines the mutable latent state that IBDE evolves over time.
"""

from typing import Dict, List, Optional, Any
import numpy as np
from pydantic import BaseModel, Field, validator


class FatigueState(BaseModel):
    """Fatigue state components."""
    promo: float = Field(default=0.0, ge=0.0, description="Promotion fatigue")
    novelty: float = Field(default=0.0, ge=0.0, description="Novelty fatigue")


class MemoryState(BaseModel):
    """Memory state components."""
    ad_stock: float = Field(default=0.0, ge=0.0, description="Advertising stock")
    last_choice: Optional[int] = Field(default=None, description="Last chosen brand index")
    recency: float = Field(default=0.0, ge=0.0, le=1.0, description="Recency score")


class ScheduleState(BaseModel):
    """Schedule state components."""
    last_purchase_day: Optional[int] = Field(default=None, description="Last purchase day")


class AgentState(BaseModel):
    """
    Agent latent state schema.
    
    This state is owned and updated only by IBDE.
    """
    taste_embedding: List[float] = Field(..., description="Taste embedding vector [d]")
    brand_loyalty: List[float] = Field(..., description="Brand loyalty scores [B]")
    habit_strength: float = Field(default=1.0, ge=0.0, description="Habit strength scalar")
    reference_price: float = Field(default=1.0, gt=0.0, description="Reference price")
    attention: float = Field(default=1.0, ge=0.0, le=1.0, description="Attention level")
    fatigue: FatigueState = Field(default_factory=FatigueState, description="Fatigue components")
    memory: MemoryState = Field(default_factory=MemoryState, description="Memory components")
    schedule: ScheduleState = Field(default_factory=ScheduleState, description="Schedule components")
    
    @validator("taste_embedding")
    def validate_taste_embedding(cls, v):
        """Validate taste embedding is non-empty."""
        if len(v) == 0:
            raise ValueError("Taste embedding must be non-empty")
        return v
    
    @validator("brand_loyalty")
    def validate_brand_loyalty(cls, v):
        """Validate brand loyalty matches number of brands."""
        if len(v) == 0:
            raise ValueError("Brand loyalty must be non-empty")
        return v
    
    def to_numpy(self) -> Dict[str, np.ndarray]:
        """Convert state to numpy arrays for batched processing."""
        return {
            "taste_embedding": np.array(self.taste_embedding, dtype=np.float32),
            "brand_loyalty": np.array(self.brand_loyalty, dtype=np.float32),
            "habit_strength": np.array([self.habit_strength], dtype=np.float32),
            "reference_price": np.array([self.reference_price], dtype=np.float32),
            "attention": np.array([self.attention], dtype=np.float32),
            "fatigue_promo": np.array([self.fatigue.promo], dtype=np.float32),
            "fatigue_novelty": np.array([self.fatigue.novelty], dtype=np.float32),
            "ad_stock": np.array([self.memory.ad_stock], dtype=np.float32),
            "last_choice": np.array([self.memory.last_choice if self.memory.last_choice is not None else -1], dtype=np.int32),
            "recency": np.array([self.memory.recency], dtype=np.float32),
            "last_purchase_day": np.array([self.schedule.last_purchase_day if self.schedule.last_purchase_day is not None else -1], dtype=np.int32),
        }
    
    @classmethod
    def from_numpy(cls, state_dict: Dict[str, np.ndarray]) -> "AgentState":
        """Create AgentState from numpy arrays."""
        return cls(
            taste_embedding=state_dict["taste_embedding"].tolist(),
            brand_loyalty=state_dict["brand_loyalty"].tolist(),
            habit_strength=float(state_dict["habit_strength"][0]),
            reference_price=float(state_dict["reference_price"][0]),
            attention=float(state_dict["attention"][0]),
            fatigue=FatigueState(
                promo=float(state_dict["fatigue_promo"][0]),
                novelty=float(state_dict["fatigue_novelty"][0])
            ),
            memory=MemoryState(
                ad_stock=float(state_dict["ad_stock"][0]),
                last_choice=int(state_dict["last_choice"][0]) if state_dict["last_choice"][0] >= 0 else None,
                recency=float(state_dict["recency"][0])
            ),
            schedule=ScheduleState(
                last_purchase_day=int(state_dict["last_purchase_day"][0]) if state_dict["last_purchase_day"][0] >= 0 else None
            )
        )


class EnvironmentInputs(BaseModel):
    """
    Environment inputs provided by LPM.
    
    These are read-only signals.
    """
    prices: List[float] = Field(..., description="Prices for each brand [B]")
    availability: List[float] = Field(..., description="Availability scores [B]")
    promotions: List[float] = Field(..., description="Promotion intensities [B]")
    ads: List[float] = Field(default_factory=list, description="Advertising signals [B]")
    context: Dict[str, Any] = Field(default_factory=dict, description="Context (week_id, season, daypart)")
    
    @validator("prices", "availability", "promotions")
    def validate_same_length(cls, v, values):
        """Validate all brand arrays have same length."""
        if "prices" in values and len(values["prices"]) != len(v):
            raise ValueError(f"All brand arrays must have same length, got {len(values['prices'])} vs {len(v)}")
        return v
    
    def to_numpy(self) -> Dict[str, np.ndarray]:
        """Convert to numpy arrays for batched processing."""
        return {
            "prices": np.array(self.prices, dtype=np.float32),
            "availability": np.array(self.availability, dtype=np.float32),
            "promotions": np.array(self.promotions, dtype=np.float32),
            "ads": np.array(self.ads if self.ads else [0.0] * len(self.prices), dtype=np.float32),
        }


class Logits(BaseModel):
    """
    Decision logits output by IBDE.
    
    These are utilities, not probabilities. LPM will sample from these.
    """
    purchase_logits: List[float] = Field(..., description="Purchase logits for each brand [B]")
    no_purchase_logit: float = Field(default=0.0, description="No-purchase logit")
    
    def to_numpy(self) -> Dict[str, np.ndarray]:
        """Convert to numpy arrays."""
        return {
            "purchase_logits": np.array(self.purchase_logits, dtype=np.float32),
            "no_purchase_logit": np.array([self.no_purchase_logit], dtype=np.float32)
        }


class Diagnostics(BaseModel):
    """
    Optional diagnostics for debugging and analysis.
    """
    price_term: List[float] = Field(default_factory=list, description="Price term contribution [B]")
    promo_term: List[float] = Field(default_factory=list, description="Promo term contribution [B]")
    loyalty_term: List[float] = Field(default_factory=list, description="Loyalty term contribution [B]")
    constraint_mask: List[bool] = Field(default_factory=list, description="Constraint mask [B]")
    
    def to_numpy(self) -> Dict[str, np.ndarray]:
        """Convert to numpy arrays."""
        return {
            "price_term": np.array(self.price_term, dtype=np.float32) if self.price_term else np.array([]),
            "promo_term": np.array(self.promo_term, dtype=np.float32) if self.promo_term else np.array([]),
            "loyalty_term": np.array(self.loyalty_term, dtype=np.float32) if self.loyalty_term else np.array([]),
            "constraint_mask": np.array(self.constraint_mask, dtype=bool) if self.constraint_mask else np.array([]),
        }

