"""
Metadata catalog for tracking dataset versions, lineage, and provenance.
"""

import json
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
from pathlib import Path
from pydantic import BaseModel, Field

from common.schemas import DataVersion


class DatasetCatalogEntry(BaseModel):
    """Catalog entry for a dataset version."""
    version_id: str
    created_at: datetime
    generation_config: Dict[str, Any]
    random_seed: int
    file_paths: Dict[str, str]  # table_name -> file_path
    metadata: Dict[str, Any] = Field(default_factory=dict)


class DataCatalog:
    """
    Metadata catalog for tracking dataset versions.
    
    Maintains version history, generation configs, and lineage.
    """
    
    def __init__(self, catalog_file: str):
        """
        Initialize catalog.
        
        Args:
            catalog_file: Path to catalog JSON file
        """
        self.catalog_file = Path(catalog_file)
        self.entries: Dict[str, DatasetCatalogEntry] = {}
        
        # Load existing catalog if it exists
        if self.catalog_file.exists():
            self._load()
    
    def _load(self):
        """Load catalog from disk."""
        with open(self.catalog_file, 'r') as f:
            data = json.load(f)
            
            for version_id, entry_data in data.items():
                # Convert datetime strings back to datetime objects
                entry_data['created_at'] = datetime.fromisoformat(entry_data['created_at'])
                self.entries[version_id] = DatasetCatalogEntry(**entry_data)
    
    def _save(self):
        """Save catalog to disk."""
        os.makedirs(self.catalog_file.parent, exist_ok=True)
        
        data = {}
        for version_id, entry in self.entries.items():
            entry_dict = entry.model_dump()
            # Convert datetime to ISO string for JSON
            entry_dict['created_at'] = entry.created_at.isoformat()
            data[version_id] = entry_dict
        
        with open(self.catalog_file, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register_dataset(
        self,
        version_id: str,
        generation_config: Dict[str, Any],
        random_seed: int,
        file_paths: Dict[str, str],
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Register a new dataset version in the catalog.
        
        Args:
            version_id: Data version ID
            generation_config: Configuration used for generation
            random_seed: Random seed used
            file_paths: Mapping of table names to file paths
            metadata: Optional additional metadata
        """
        if version_id in self.entries:
            raise ValueError(f"Dataset version already exists: {version_id}")
        
        entry = DatasetCatalogEntry(
            version_id=version_id,
            created_at=datetime.now(),
            generation_config=generation_config,
            random_seed=random_seed,
            file_paths=file_paths,
            metadata=metadata or {}
        )
        
        self.entries[version_id] = entry
        self._save()
    
    def get_entry(self, version_id: str) -> Optional[DatasetCatalogEntry]:
        """
        Get catalog entry for a version.
        
        Args:
            version_id: Data version ID
            
        Returns:
            Catalog entry or None if not found
        """
        return self.entries.get(version_id)
    
    def list_versions(self) -> List[str]:
        """
        List all registered dataset versions.
        
        Returns:
            List of version IDs, sorted by creation time (newest first)
        """
        versions = list(self.entries.keys())
        versions.sort(key=lambda v: self.entries[v].created_at, reverse=True)
        return versions
    
    def get_latest_version(self) -> Optional[str]:
        """
        Get the latest dataset version.
        
        Returns:
            Latest version ID or None if catalog is empty
        """
        versions = self.list_versions()
        return versions[0] if versions else None
    
    def validate_version(self, version_id: str) -> Dict[str, Any]:
        """
        Validate that a dataset version exists and files are accessible.
        
        Args:
            version_id: Data version ID
            
        Returns:
            Validation result dictionary
        """
        entry = self.get_entry(version_id)
        
        if entry is None:
            return {
                "valid": False,
                "error": f"Version not found in catalog: {version_id}"
            }
        
        missing_files = []
        for table_name, file_path in entry.file_paths.items():
            if not os.path.exists(file_path):
                missing_files.append(table_name)
        
        if missing_files:
            return {
                "valid": False,
                "error": f"Missing files for version {version_id}",
                "missing_files": missing_files
            }
        
        return {
            "valid": True,
            "version_id": version_id,
            "created_at": entry.created_at.isoformat(),
            "num_tables": len(entry.file_paths)
        }

