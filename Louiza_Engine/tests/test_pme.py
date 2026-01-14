"""
Tests for Persona Modeling Engine (Layer 2).

Tests enforce:
- Schema validation
- PersonaSet constraints (weights sum to 1.0)
- Immutability checks
- Seed persona initialization
"""

import pytest
import json
from pathlib import Path
from datetime import datetime

from pme.persona_schema import (
    Persona, PersonaSet,
    PopulationWeight, BehavioralParams, StatePriors, TasteEmbedding,
    FeatureGates, InteractionEffects, Constraints, CalibrationHooks,
    Diagnostics, Lineage, Explainability
)
from pme.initializer import SeedPersonaInitializer
from pme.pme_runner import PMERunner


def test_persona_schema_validation():
    """Test that persona schema validation works."""
    # Valid persona
    persona = Persona(
        persona_id="test_persona",
        population_weight=PopulationWeight(global_weight=0.5),
        behavioral_params=BehavioralParams(
            price_sensitivity=1.5,
            promo_responsiveness=1.2,
            habit_strength=1.0,
            brand_loyalty_bias=1.0,
            choice_noise=0.1
        ),
        state_priors=StatePriors(
            taste_embedding=TasteEmbedding(
                mean=[0.1, 0.2, 0.3],
                cov=[[0.1, 0, 0], [0, 0.1, 0], [0, 0, 0.1]]
            )
        ),
        lineage=Lineage(data_version="data_test"),
        explainability=Explainability(human_label="Test Persona")
    )
    
    assert persona.persona_id == "test_persona"
    assert persona.population_weight.global_weight == 0.5


def test_persona_status_validation():
    """Test that persona status validation works."""
    # Valid statuses
    for status in ["active", "shadow", "deprecated"]:
        persona = Persona(
            persona_id="test",
            population_weight=PopulationWeight(global_weight=0.5),
            behavioral_params=BehavioralParams(
                price_sensitivity=1.0, promo_responsiveness=1.0,
                habit_strength=1.0, brand_loyalty_bias=1.0, choice_noise=0.1
            ),
            state_priors=StatePriors(
                taste_embedding=TasteEmbedding(
                    mean=[0.1], cov=[[0.1]]
                )
            ),
            status=status,
            lineage=Lineage(data_version="data_test"),
            explainability=Explainability(human_label="Test")
        )
        assert persona.status == status
    
    # Invalid status
    with pytest.raises(Exception):
        Persona(
            persona_id="test",
            population_weight=PopulationWeight(global_weight=0.5),
            behavioral_params=BehavioralParams(
                price_sensitivity=1.0, promo_responsiveness=1.0,
                habit_strength=1.0, brand_loyalty_bias=1.0, choice_noise=0.1
            ),
            state_priors=StatePriors(
                taste_embedding=TasteEmbedding(
                    mean=[0.1], cov=[[0.1]]
                )
            ),
            status="invalid",
            lineage=Lineage(data_version="data_test"),
            explainability=Explainability(human_label="Test")
        )


def test_personaset_weight_validation():
    """Test that PersonaSet validates weights sum to 1.0."""
    # Valid PersonaSet (weights sum to 1.0)
    personas = []
    for i in range(3):
        persona = Persona(
            persona_id=f"persona_{i}",
            population_weight=PopulationWeight(global_weight=1.0/3),
            behavioral_params=BehavioralParams(
                price_sensitivity=1.0, promo_responsiveness=1.0,
                habit_strength=1.0, brand_loyalty_bias=1.0, choice_noise=0.1
            ),
            state_priors=StatePriors(
                taste_embedding=TasteEmbedding(
                    mean=[0.1], cov=[[0.1]]
                )
            ),
            lineage=Lineage(data_version="data_test"),
            explainability=Explainability(human_label=f"Persona {i}")
        )
        personas.append(persona)
    
    personaset = PersonaSet(
        version="PersonaSet_v1",
        data_version="data_test",
        personas=personas
    )
    
    assert len(personaset.personas) == 3
    assert abs(sum(p.population_weight.global_weight for p in personaset.get_active_personas()) - 1.0) < 0.01
    
    # Invalid PersonaSet (weights don't sum to 1.0)
    personas[0].population_weight.global_weight = 0.8
    personas[1].population_weight.global_weight = 0.3
    
    with pytest.raises(Exception):
        PersonaSet(
            version="PersonaSet_v1",
            data_version="data_test",
            personas=personas
        )


def test_personaset_duplicate_ids():
    """Test that PersonaSet rejects duplicate persona IDs."""
    persona1 = Persona(
        persona_id="duplicate",
        population_weight=PopulationWeight(global_weight=0.5),
        behavioral_params=BehavioralParams(
            price_sensitivity=1.0, promo_responsiveness=1.0,
            habit_strength=1.0, brand_loyalty_bias=1.0, choice_noise=0.1
        ),
        state_priors=StatePriors(
            taste_embedding=TasteEmbedding(
                mean=[0.1], cov=[[0.1]]
            )
        ),
        lineage=Lineage(data_version="data_test"),
        explainability=Explainability(human_label="Persona 1")
    )
    
    persona2 = Persona(
        persona_id="duplicate",  # Same ID
        population_weight=PopulationWeight(global_weight=0.5),
        behavioral_params=BehavioralParams(
            price_sensitivity=1.0, promo_responsiveness=1.0,
            habit_strength=1.0, brand_loyalty_bias=1.0, choice_noise=0.1
        ),
        state_priors=StatePriors(
            taste_embedding=TasteEmbedding(
                mean=[0.1], cov=[[0.1]]
            )
        ),
        lineage=Lineage(data_version="data_test"),
        explainability=Explainability(human_label="Persona 2")
    )
    
    with pytest.raises(Exception):
        PersonaSet(
            version="PersonaSet_v1",
            data_version="data_test",
            personas=[persona1, persona2]
        )


def test_seed_persona_initializer():
    """Test seed persona initialization."""
    initializer = SeedPersonaInitializer(
        data_version="data_test",
        pme_run_id="test_run"
    )
    
    personas = initializer.create_seed_personas(num_personas=5)
    
    assert len(personas) == 5
    assert all(p.status == "active" for p in personas)
    assert all(p.lineage.data_version == "data_test" for p in personas)
    
    # Check weights sum to 1.0
    total_weight = sum(p.population_weight.global_weight for p in personas)
    assert abs(total_weight - 1.0) < 0.01


def test_personaset_get_active_personas():
    """Test PersonaSet.get_active_personas() method."""
    personas = []
    # Create 3 active personas with weights summing to 1.0
    for i in range(3):
        persona = Persona(
            persona_id=f"persona_{i}",
            population_weight=PopulationWeight(global_weight=1.0/3),
            behavioral_params=BehavioralParams(
                price_sensitivity=1.0, promo_responsiveness=1.0,
                habit_strength=1.0, brand_loyalty_bias=1.0, choice_noise=0.1
            ),
            state_priors=StatePriors(
                taste_embedding=TasteEmbedding(
                    mean=[0.1], cov=[[0.1]]
                )
            ),
            status="active",
            lineage=Lineage(data_version="data_test"),
            explainability=Explainability(human_label=f"Persona {i}")
        )
        personas.append(persona)
    
    # Add 2 shadow personas (don't count toward weight sum)
    for i in range(3, 5):
        persona = Persona(
            persona_id=f"persona_{i}",
            population_weight=PopulationWeight(global_weight=0.0),  # Shadow personas have 0 weight
            behavioral_params=BehavioralParams(
                price_sensitivity=1.0, promo_responsiveness=1.0,
                habit_strength=1.0, brand_loyalty_bias=1.0, choice_noise=0.1
            ),
            state_priors=StatePriors(
                taste_embedding=TasteEmbedding(
                    mean=[0.1], cov=[[0.1]]
                )
            ),
            status="shadow",
            lineage=Lineage(data_version="data_test"),
            explainability=Explainability(human_label=f"Persona {i}")
        )
        personas.append(persona)
    
    personaset = PersonaSet(
        version="PersonaSet_v1",
        data_version="data_test",
        personas=personas
    )
    
    active = personaset.get_active_personas()
    assert len(active) == 3
    assert all(p.status == "active" for p in active)


def test_pme_runner():
    """Test PME runner initialization."""
    runner = PMERunner(data_version="data_test")
    
    personaset = runner.initialize_seed_personas(num_personas=5)
    
    assert personaset.version.startswith("PersonaSet_v")
    assert len(personaset.personas) == 5
    assert personaset.data_version == "data_test"
    
    # Validate
    validation = runner.validate_personaset(personaset)
    assert validation["valid"]
    assert validation["num_personas"] == 5


def test_personaset_save_load():
    """Test PersonaSet save and load."""
    import tempfile
    
    runner = PMERunner(data_version="data_test")
    personaset = runner.initialize_seed_personas(num_personas=3)
    
    with tempfile.TemporaryDirectory() as tmpdir:
        output_path = Path(tmpdir) / "test_personaset.json"
        
        # Save
        runner.save_personaset(personaset, str(output_path))
        assert output_path.exists()
        
        # Load
        loaded = runner.load_personaset(str(output_path))
        assert loaded.version == personaset.version
        assert len(loaded.personas) == len(personaset.personas)
        assert loaded.personas[0].persona_id == personaset.personas[0].persona_id


def test_taste_embedding_covariance_validation():
    """Test that taste embedding covariance matrix validation works."""
    # Valid: square matrix matching mean dimension
    embedding = TasteEmbedding(
        mean=[0.1, 0.2, 0.3],
        cov=[[0.1, 0, 0], [0, 0.1, 0], [0, 0, 0.1]]
    )
    assert len(embedding.mean) == 3
    assert len(embedding.cov) == 3
    
    # Invalid: wrong number of rows
    with pytest.raises(Exception):
        TasteEmbedding(
            mean=[0.1, 0.2, 0.3],
            cov=[[0.1, 0], [0, 0.1]]  # Only 2 rows, need 3
        )
    
    # Invalid: non-square matrix
    with pytest.raises(Exception):
        TasteEmbedding(
            mean=[0.1, 0.2],
            cov=[[0.1, 0, 0], [0, 0.1, 0]]  # 2x3, not square
        )

