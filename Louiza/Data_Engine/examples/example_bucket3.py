"""
Example: Ingesting Financial Data (Bucket 3)

Demonstrates how to ingest financial/foot-traffic CSV data.
"""

from pathlib import Path
import sys
from datetime import datetime

# Add parent directory to path so we can import Data_Engine as a package
parent_dir = Path(__file__).parent.parent.parent
sys.path.insert(0, str(parent_dir))

from Data_Engine.ingestion.bucket3_financial_data import FinancialDataIngester
from Data_Engine.indexing.index_manager import IndexManager
from Data_Engine.retrieval.retrieval_manager import RetrievalManager


def main():
    """Example ingestion for financial data"""
    
    storage_dir = Path(__file__).parent.parent / "storage_data"
    index_manager = IndexManager(storage_dir=storage_dir)
    
    # Initialize ingester with client ID
    ingester = FinancialDataIngester(
        source_name="client_abc_transactions",
        client_id="client_abc"
    )
    
    # Create sample financial data
    sample_csv = Path(__file__).parent / "sample_financial.csv"
    if not sample_csv.exists():
        print(f"Creating sample financial CSV: {sample_csv}")
        import pandas as pd
        from datetime import timedelta
        
        dates = [datetime.now() - timedelta(days=i) for i in range(10)]
        df = pd.DataFrame({
            'timestamp': dates,
            'merchant': ['McDonald\'s', 'Burger King', 'Wendy\'s'] * 3 + ['McDonald\'s'],
            'amount': [12.50, 15.00, 8.75, 20.00, 10.25, 9.50, 18.00, 11.00, 7.50, 13.25],
            'location': ['NYC', 'LA', 'Chicago', 'NYC', 'LA', 'Chicago', 'NYC', 'LA', 'Chicago', 'NYC'],
            'transaction_type': ['card', 'card', 'card', 'card', 'card', 'card', 'card', 'card', 'card', 'card']
        })
        df.to_csv(sample_csv, index=False)
    
    if sample_csv.exists():
        records = list(ingester.ingest(
            sample_csv,
            timestamp_column="timestamp",
            amount_column="amount",
            location_column="location",
            brand_column="merchant"
        ))
        
        print(f"Created {len(records)} financial records")
        
        index_manager.index_batch(records)
        print(f"✓ Indexed {len(records)} records")
        
        # Example queries
        retrieval_manager = RetrievalManager(index_manager)
        
        # Query by brand
        print("\nQuerying transactions for McDonald's...")
        mcd_records = retrieval_manager.query_by_brand("McDonald's")
        print(f"Found {len(mcd_records)} transactions")
        
        # Query by client
        print("\nQuerying by client...")
        client_records = retrieval_manager.query_by_filters({"client_id": "client_abc"})
        print(f"Found {len(client_records)} records for client_abc")
        
        # Query by time range
        print("\nQuerying by time range...")
        from datetime import timedelta
        start_time = datetime.now() - timedelta(days=7)
        end_time = datetime.now()
        time_records = retrieval_manager.query_by_time_range(start_time, end_time)
        print(f"Found {len(time_records)} records in last 7 days")


if __name__ == "__main__":
    main()

