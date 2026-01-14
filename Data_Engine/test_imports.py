"""
Test script to verify imports work correctly
"""

from pathlib import Path
import sys

# Add parent directory to path
parent_dir = Path(__file__).parent.parent
sys.path.insert(0, str(parent_dir))

try:
    from Data_Engine.data_engine import DataEngine
    print("✓ Successfully imported DataEngine")
    
    from Data_Engine.core.schema import DataRecord
    print("✓ Successfully imported DataRecord")
    
    from Data_Engine.ingestion.bucket1_online_datasets import OnlineDatasetsIngester
    print("✓ Successfully imported OnlineDatasetsIngester")
    
    print("\nAll imports successful!")
    
except ImportError as e:
    print(f"✗ Import error: {e}")
    import traceback
    traceback.print_exc()

