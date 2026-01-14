"""
PME Runner - Orchestrates Persona Modeling Engine execution.

For POC, this mainly handles initialization. Full lifecycle management
(Phase 1-4) will be implemented in later phases.
"""

from typing import Optional, Dict, Any
from datetime import datetime
import json
from pathlib import Path

from pme.persona_schema import PersonaSet
from pme.initializer import SeedPersonaInitializer
from common.versioning import generate_personaset_version


class PMERunner:
    """
    PME execution orchestrator.
    
    For POC, handles seed persona initialization.
    Future phases will add:
    - Persona fit evaluation
    - Residual analysis
    - Candidate persona proposal
    - Shadow evaluation
    """
    
    def __init__(self, data_version: str):
        """
        Initialize PME runner.
        
        Args:
            data_version: Data version ID to use
        """
        self.data_version = data_version
        self.pme_run_id = f"pme_run_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    
    def initialize_seed_personas(
        self,
        num_personas: int = 10,
        version: Optional[str] = None
    ) -> PersonaSet:
        """
        Initialize seed personas (Phase 0).
        
        Args:
            num_personas: Number of seed personas (8-12 recommended)
            version: Optional PersonaSet version
            
        Returns:
            PersonaSet with seed personas
        """
        if version is None:
            version = generate_personaset_version(version_number=1)
        
        initializer = SeedPersonaInitializer(
            data_version=self.data_version,
            pme_run_id=self.pme_run_id
        )
        
        personaset = initializer.create_personaset(
            num_personas=num_personas,
            version=version
        )
        
        return personaset
    
    def save_personaset(self, personaset: PersonaSet, output_path: str):
        """
        Save PersonaSet to JSON file.
        
        Args:
            personaset: PersonaSet to save
            output_path: Output file path
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Convert to dict with proper serialization
        personaset_dict = personaset.model_dump(mode='json')
        
        with open(output_path, 'w') as f:
            json.dump(personaset_dict, f, indent=2)
    
    def load_personaset(self, file_path: str) -> PersonaSet:
        """
        Load PersonaSet from JSON file.
        
        Args:
            file_path: Path to PersonaSet JSON file
            
        Returns:
            Loaded PersonaSet
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        return PersonaSet(**data)
    
    def validate_personaset(self, personaset: PersonaSet) -> Dict[str, Any]:
        """
        Validate PersonaSet and return diagnostics.
        
        Args:
            personaset: PersonaSet to validate
            
        Returns:
            Validation results dictionary
        """
        results = {
            "valid": True,
            "version": personaset.version,
            "num_personas": len(personaset.personas),
            "num_active": len(personaset.get_active_personas()),
            "total_weight": sum(p.population_weight.global_weight for p in personaset.get_active_personas()),
            "persona_ids": [p.persona_id for p in personaset.personas],
            "errors": []
        }
        
        # Check weight sum
        weight_sum = results["total_weight"]
        if not 0.99 <= weight_sum <= 1.01:
            results["valid"] = False
            results["errors"].append(f"Active persona weights sum to {weight_sum}, expected 1.0")
        
        # Check for duplicate IDs
        if len(results["persona_ids"]) != len(set(results["persona_ids"])):
            results["valid"] = False
            results["errors"].append("Duplicate persona IDs found")
        
        return results

