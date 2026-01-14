"""
Seed persona initialization for POC.

Creates initial set of seed personas based on expert-defined archetypes.
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import numpy as np

from pme.persona_schema import (
    Persona, PersonaSet,
    PopulationWeight, BehavioralParams, StatePriors, TasteEmbedding,
    FeatureGates, InteractionEffects, Constraints, CalibrationHooks,
    Diagnostics, Lineage, Explainability
)
from common.versioning import generate_personaset_version


class SeedPersonaInitializer:
    """
    Initializes seed personas for POC.
    
    Creates K seed personas (recommended 8-12) representing behavioral archetypes.
    """
    
    def __init__(self, data_version: str, pme_run_id: Optional[str] = None):
        """
        Initialize seed persona creator.
        
        Args:
            data_version: Data version ID used for lineage
            pme_run_id: Optional PME run ID
        """
        self.data_version = data_version
        self.pme_run_id = pme_run_id or f"pme_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def create_seed_personas(self, num_personas: int = 10) -> List[Persona]:
        """
        Create seed personas.
        
        Args:
            num_personas: Number of seed personas to create (8-12 recommended)
            
        Returns:
            List of seed personas
        """
        if num_personas < 1 or num_personas > 20:
            raise ValueError(f"Number of personas must be between 1 and 20, got {num_personas}")
        
        # Define seed persona templates
        templates = self._get_persona_templates()
        
        # Select templates (cycle if num_personas > templates)
        selected_templates = []
        for i in range(num_personas):
            template = templates[i % len(templates)]
            selected_templates.append(template)
        
        # Create personas
        personas = []
        total_weight = 0.0
        
        for i, template in enumerate(selected_templates):
            persona_id = f"persona_{i+1:02d}_{template['id_suffix']}"
            
            # Distribute weights evenly (will be normalized)
            weight = 1.0 / num_personas
            
            persona = Persona(
                persona_id=persona_id,
                version="v1.0",
                status="active",
                created_at=datetime.now(),
                population_weight=PopulationWeight(
                    global_weight=weight,
                    by_region={}
                ),
                behavioral_params=BehavioralParams(
                    price_sensitivity=template["price_sensitivity"],
                    promo_responsiveness=template["promo_responsiveness"],
                    habit_strength=template["habit_strength"],
                    brand_loyalty_bias=template["brand_loyalty_bias"],
                    choice_noise=template["choice_noise"]
                ),
                state_priors=StatePriors(
                    taste_embedding=TasteEmbedding(
                        mean=template["taste_mean"],
                        cov=template["taste_cov"]
                    )
                ),
                feature_gates=FeatureGates(
                    health_signal=template.get("health_signal", 0.5),
                    convenience_signal=template.get("convenience_signal", 0.5),
                    promo_signal=template.get("promo_signal", 1.0),
                    advertising_signal=template.get("advertising_signal", 0.5)
                ),
                interaction_effects=InteractionEffects(
                    price_x_loyalty=template.get("price_x_loyalty", 0.0),
                    promo_x_habit=template.get("promo_x_habit", 0.0)
                ),
                constraints=Constraints(
                    max_price_tolerance=template.get("max_price_tolerance", 1.5),
                    min_repeat_interval_days=template.get("min_repeat_interval_days", 1)
                ),
                calibration_hooks=CalibrationHooks(
                    anchor_targets=["transactions", "revenue"],
                    adjustable_params=["population_weight.global", "price_sensitivity"],
                    regularization_strength=0.15
                ),
                diagnostics=Diagnostics(
                    fit_score=0.0,  # Will be computed later
                    residual_explained=0.0,
                    stability_score=1.0  # Seed personas start stable
                ),
                lineage=Lineage(
                    parent_personas=[],
                    creation_reason="seed_persona_initialization",
                    data_version=self.data_version,
                    pme_run_id=self.pme_run_id
                ),
                explainability=Explainability(
                    human_label=template["label"],
                    dominant_drivers=template["dominant_drivers"]
                )
            )
            
            personas.append(persona)
            total_weight += weight
        
        # Normalize weights to sum to 1.0
        for persona in personas:
            persona.population_weight.global_weight /= total_weight
        
        return personas
    
    def _get_persona_templates(self) -> List[Dict[str, Any]]:
        """
        Get seed persona templates.
        
        Returns:
            List of template dictionaries
        """
        return [
            {
                "id_suffix": "price_sensitive_loyalist",
                "label": "Price-Sensitive Loyalists",
                "price_sensitivity": 2.5,
                "promo_responsiveness": 1.8,
                "habit_strength": 1.6,
                "brand_loyalty_bias": 1.2,
                "choice_noise": 0.1,
                "taste_mean": [0.3, -0.2, 0.1],
                "taste_cov": [[0.1, 0, 0], [0, 0.08, 0], [0, 0, 0.12]],
                "dominant_drivers": ["price_sensitivity", "habit_strength"],
                "price_x_loyalty": 0.3
            },
            {
                "id_suffix": "promo_driven_switcher",
                "label": "Promotion-Driven Switchers",
                "price_sensitivity": 1.5,
                "promo_responsiveness": 2.5,
                "habit_strength": 0.8,
                "brand_loyalty_bias": 0.6,
                "choice_noise": 0.2,
                "taste_mean": [-0.1, 0.4, -0.2],
                "taste_cov": [[0.15, 0, 0], [0, 0.12, 0], [0, 0, 0.1]],
                "dominant_drivers": ["promo_responsiveness", "choice_noise"],
                "promo_x_habit": 0.4
            },
            {
                "id_suffix": "novelty_seeker",
                "label": "Novelty Seekers",
                "price_sensitivity": 1.2,
                "promo_responsiveness": 1.5,
                "habit_strength": 0.5,
                "brand_loyalty_bias": 0.4,
                "choice_noise": 0.25,
                "taste_mean": [0.5, 0.3, 0.4],
                "taste_cov": [[0.2, 0, 0], [0, 0.18, 0], [0, 0, 0.15]],
                "dominant_drivers": ["choice_noise", "promo_responsiveness"],
                "convenience_signal": 0.7
            },
            {
                "id_suffix": "convenience_first_regular",
                "label": "Convenience-First Regulars",
                "price_sensitivity": 1.0,
                "promo_responsiveness": 0.8,
                "habit_strength": 2.0,
                "brand_loyalty_bias": 1.5,
                "choice_noise": 0.08,
                "taste_mean": [-0.2, -0.1, 0.2],
                "taste_cov": [[0.08, 0, 0], [0, 0.1, 0], [0, 0, 0.09]],
                "dominant_drivers": ["habit_strength", "brand_loyalty_bias"],
                "convenience_signal": 1.0,
                "min_repeat_interval_days": 2
            },
            {
                "id_suffix": "brand_a_loyalist",
                "label": "Brand-A Loyalists",
                "price_sensitivity": 1.3,
                "promo_responsiveness": 0.9,
                "habit_strength": 1.8,
                "brand_loyalty_bias": 2.5,
                "choice_noise": 0.05,
                "taste_mean": [0.4, 0.1, -0.1],
                "taste_cov": [[0.09, 0, 0], [0, 0.07, 0], [0, 0, 0.11]],
                "dominant_drivers": ["brand_loyalty_bias", "habit_strength"],
                "max_price_tolerance": 1.8
            },
            {
                "id_suffix": "brand_b_loyalist",
                "label": "Brand-B Loyalists",
                "price_sensitivity": 1.4,
                "promo_responsiveness": 1.0,
                "habit_strength": 1.7,
                "brand_loyalty_bias": 2.3,
                "choice_noise": 0.06,
                "taste_mean": [-0.3, 0.2, 0.3],
                "taste_cov": [[0.1, 0, 0], [0, 0.08, 0], [0, 0, 0.12]],
                "dominant_drivers": ["brand_loyalty_bias", "habit_strength"],
                "max_price_tolerance": 1.7
            },
            {
                "id_suffix": "value_seeker",
                "label": "Value Seekers",
                "price_sensitivity": 2.8,
                "promo_responsiveness": 2.0,
                "habit_strength": 0.7,
                "brand_loyalty_bias": 0.5,
                "choice_noise": 0.18,
                "taste_mean": [0.1, -0.3, 0.2],
                "taste_cov": [[0.12, 0, 0], [0, 0.1, 0], [0, 0, 0.13]],
                "dominant_drivers": ["price_sensitivity", "promo_responsiveness"],
                "max_price_tolerance": 1.2
            },
            {
                "id_suffix": "quality_focused",
                "label": "Quality-Focused Consumers",
                "price_sensitivity": 0.8,
                "promo_responsiveness": 0.6,
                "habit_strength": 1.4,
                "brand_loyalty_bias": 1.8,
                "choice_noise": 0.12,
                "taste_mean": [0.6, 0.4, 0.5],
                "taste_cov": [[0.11, 0, 0], [0, 0.09, 0], [0, 0, 0.1]],
                "dominant_drivers": ["brand_loyalty_bias", "habit_strength"],
                "health_signal": 0.9,
                "max_price_tolerance": 2.5
            },
            {
                "id_suffix": "casual_explorer",
                "label": "Casual Explorers",
                "price_sensitivity": 1.1,
                "promo_responsiveness": 1.3,
                "habit_strength": 0.9,
                "brand_loyalty_bias": 0.7,
                "choice_noise": 0.22,
                "taste_mean": [0.2, 0.1, 0.3],
                "taste_cov": [[0.14, 0, 0], [0, 0.11, 0], [0, 0, 0.12]],
                "dominant_drivers": ["choice_noise", "promo_responsiveness"]
            },
            {
                "id_suffix": "routine_follower",
                "label": "Routine Followers",
                "price_sensitivity": 1.0,
                "promo_responsiveness": 0.7,
                "habit_strength": 2.2,
                "brand_loyalty_bias": 1.3,
                "choice_noise": 0.07,
                "taste_mean": [-0.1, -0.2, 0.1],
                "taste_cov": [[0.07, 0, 0], [0, 0.08, 0], [0, 0, 0.09]],
                "dominant_drivers": ["habit_strength", "brand_loyalty_bias"],
                "min_repeat_interval_days": 3
            }
        ]
    
    def create_personaset(self, num_personas: int = 10, version: Optional[str] = None) -> PersonaSet:
        """
        Create a complete PersonaSet with seed personas.
        
        Args:
            num_personas: Number of seed personas to create
            version: Optional PersonaSet version (auto-generated if None)
            
        Returns:
            PersonaSet with seed personas
        """
        if version is None:
            version = generate_personaset_version(version_number=1)
        
        personas = self.create_seed_personas(num_personas=num_personas)
        
        personaset = PersonaSet(
            version=version,
            created_at=datetime.now(),
            data_version=self.data_version,
            pme_run_id=self.pme_run_id,
            personas=personas,
            metadata={
                "initialization_type": "seed",
                "num_personas": len(personas),
                "persona_ids": [p.persona_id for p in personas]
            }
        )
        
        return personaset

