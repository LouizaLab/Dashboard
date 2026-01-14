"""
Data loading utilities for reading versioned datasets.

Provides read-only access to materialized outputs.
"""

import pandas as pd
import os
from typing import Optional, Dict, List, Any
from pathlib import Path


class DataLoader:
    """
    Loads versioned datasets from the data warehouse.
    
    Provides read-only access to materialized outputs.
    """
    
    def __init__(self, data_dir: str, data_version: str):
        """
        Initialize data loader.
        
        Args:
            data_dir: Base directory containing versioned data directories
            data_version: Data version ID (e.g., "data_2026_01_08_run01")
        """
        self.data_dir = Path(data_dir)
        self.data_version = data_version
        self.version_dir = self.data_dir / data_version
        
        if not self.version_dir.exists():
            raise ValueError(f"Data version directory not found: {self.version_dir}")
    
    def load_table(self, table_name: str) -> pd.DataFrame:
        """
        Load a table by name.
        
        Args:
            table_name: Name of the table (without .csv extension)
            
        Returns:
            DataFrame with the table data
        """
        file_path = self.version_dir / f"{table_name}.csv"
        
        if not file_path.exists():
            raise FileNotFoundError(f"Table not found: {file_path}")
        
        return pd.read_csv(file_path)
    
    def load_brands(self) -> pd.DataFrame:
        """Load brands entity table."""
        return self.load_table("brands")
    
    def load_regions(self) -> pd.DataFrame:
        """Load regions entity table."""
        return self.load_table("regions")
    
    def load_channels(self) -> pd.DataFrame:
        """Load channels entity table."""
        return self.load_table("channels")
    
    def load_price_schedule(self) -> pd.DataFrame:
        """Load brand price schedule."""
        return self.load_table("brand_price_schedule")
    
    def load_promo_schedule(self) -> pd.DataFrame:
        """Load brand promotion schedule."""
        return self.load_table("brand_promo_schedule")
    
    def load_menu_availability(self) -> pd.DataFrame:
        """Load brand menu availability."""
        return self.load_table("brand_menu_availability")
    
    def load_survey_responses(self) -> pd.DataFrame:
        """Load survey responses."""
        return self.load_table("survey_responses")
    
    def load_taste_ratings(self) -> pd.DataFrame:
        """Load taste ratings."""
        return self.load_table("taste_ratings")
    
    def load_choice_experiments(self) -> pd.DataFrame:
        """Load choice experiments."""
        return self.load_table("choice_experiments")
    
    def load_observed_metrics(self) -> pd.DataFrame:
        """Load observed market aggregates."""
        return self.load_table("observed_metrics_brand_week_region")
    
    def list_tables(self) -> List[str]:
        """
        List all available tables for this data version.
        
        Returns:
            List of table names (without .csv extension)
        """
        tables = []
        for file_path in self.version_dir.glob("*.csv"):
            tables.append(file_path.stem)
        return sorted(tables)
    
    def get_table_info(self, table_name: str) -> Dict[str, Any]:
        """
        Get metadata about a table.
        
        Args:
            table_name: Name of the table
            
        Returns:
            Dictionary with table metadata
        """
        df = self.load_table(table_name)
        
        return {
            "table_name": table_name,
            "data_version": self.data_version,
            "num_rows": len(df),
            "num_columns": len(df.columns),
            "columns": list(df.columns),
            "dtypes": {col: str(dtype) for col, dtype in df.dtypes.items()},
            "file_path": str(self.version_dir / f"{table_name}.csv")
        }

