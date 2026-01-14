"""
Versioning utilities for ensuring reproducibility and traceability.
"""

from datetime import datetime
from typing import Optional, Dict, Any
import hashlib
import json


def generate_data_version(run_number: int = 1) -> str:
    """Generate a data version ID in format: data_YYYY_MM_DD_runNN"""
    now = datetime.now()
    return f"data_{now.strftime('%Y_%m_%d')}_run{run_number:02d}"


def generate_personaset_version(version_number: int) -> str:
    """Generate a PersonaSet version ID in format: PersonaSet_vN"""
    return f"PersonaSet_v{version_number}"


def hash_scenario_config(config: Dict[str, Any]) -> str:
    """Generate a deterministic hash of scenario configuration."""
    config_str = json.dumps(config, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]


def hash_personaset(personaset: Dict[str, Any]) -> str:
    """Generate a deterministic hash of PersonaSet."""
    # Remove metadata fields that don't affect behavior
    clean_personaset = {
        k: v for k, v in personaset.items()
        if k not in ['created_at', 'lineage', 'diagnostics']
    }
    config_str = json.dumps(clean_personaset, sort_keys=True)
    return hashlib.sha256(config_str.encode()).hexdigest()[:16]

