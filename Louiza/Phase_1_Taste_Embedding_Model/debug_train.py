"""
Debug script to isolate the mutex lock issue
"""

import os
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'

import sys
print("Python version:", sys.version)
print("Starting debug script...")

print("\n1. Testing basic imports...")
try:
    import torch
    print(f"  ✓ PyTorch {torch.__version__}")
except Exception as e:
    print(f"  ✗ PyTorch import failed: {e}")
    sys.exit(1)

try:
    import sentence_transformers
    print(f"  ✓ sentence-transformers imported")
except Exception as e:
    print(f"  ✗ sentence-transformers import failed: {e}")
    sys.exit(1)

print("\n2. Testing SentenceTransformer initialization...")
print("  (This is where the mutex lock usually occurs)")
try:
    from sentence_transformers import SentenceTransformer
    print("  ✓ SentenceTransformer class imported")
    
    print("  Attempting to load model 'all-MiniLM-L6-v2'...")
    print("  (This may download the model on first run)")
    
    import time
    start_time = time.time()
    
    # Try with explicit device and settings
    model = SentenceTransformer('all-MiniLM-L6-v2', device='cpu')
    
    elapsed = time.time() - start_time
    print(f"  ✓ Model loaded successfully in {elapsed:.2f} seconds")
    print(f"  ✓ Model dimension: {model.get_sentence_embedding_dimension()}")
    
except Exception as e:
    print(f"  ✗ Model loading failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n3. Testing text encoding...")
try:
    test_texts = ["This is a test product", "Another test"]
    embeddings = model.encode(test_texts, show_progress_bar=False)
    print(f"  ✓ Encoded {len(test_texts)} texts, shape: {embeddings.shape}")
except Exception as e:
    print(f"  ✗ Encoding failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\n4. Testing data loading...")
try:
    import pandas as pd
    from pathlib import Path
    
    data_path = Path('data/processed/products.csv')
    if data_path.exists():
        df = pd.read_csv(data_path)
        print(f"  ✓ Loaded {len(df)} products from CSV")
    else:
        print(f"  ⚠ Data file not found: {data_path}")
except Exception as e:
    print(f"  ✗ Data loading failed: {e}")
    import traceback
    traceback.print_exc()

print("\n✓ All debug checks passed!")
print("\nIf you see this message, the issue might be in:")
print("  - Data loader pre-computation")
print("  - Model initialization in train.py")
print("  - Multi-threading during training")

