"""
Simple text encoder that avoids sentence-transformers mutex issues
Uses transformers library directly with a simpler approach
"""

import os
# CRITICAL: Set these BEFORE any imports
os.environ['TOKENIZERS_PARALLELISM'] = 'false'
os.environ['OMP_NUM_THREADS'] = '1'
os.environ['MKL_NUM_THREADS'] = '1'
os.environ['NUMEXPR_NUM_THREADS'] = '1'

import torch
torch.set_num_threads(1)

import torch.nn as nn
from transformers import AutoTokenizer, AutoModel
import numpy as np
from typing import List, Union
import warnings
warnings.filterwarnings('ignore')


class SimpleTextEncoder:
    """
    Simple text encoder that avoids sentence-transformers mutex issues
    Uses transformers library directly
    """
    
    def __init__(self, model_name: str = 'sentence-transformers/all-MiniLM-L6-v2', device: str = 'cpu'):
        self.device = device
        self.model_name = model_name
        
        print(f"Loading tokenizer and model: {model_name}")
        print("  (This may take a moment on first run - downloading model)")
        
        # Ensure single-threaded loading
        import threading
        lock = threading.Lock()
        
        try:
            with lock:
                # Load tokenizer first
                print("  Loading tokenizer...")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    model_name,
                    use_fast=True,
                    local_files_only=False
                )
                
                # Load model
                print("  Loading model...")
                self.model = AutoModel.from_pretrained(
                    model_name,
                    torch_dtype=torch.float32,
                    low_cpu_mem_usage=True
                ).to(device)
                self.model.eval()
                print(f"✓ Model loaded successfully")
        except Exception as e:
            print(f"✗ Error loading model: {e}")
            print("\nTroubleshooting:")
            print("  1. Check internet connection (model downloads on first run)")
            print("  2. Try: pip install --upgrade transformers")
            print("  3. On macOS, ensure: export TOKENIZERS_PARALLELISM=false")
            raise
        
        # Get embedding dimension
        with torch.no_grad():
            test_input = self.tokenizer("test", return_tensors="pt", padding=True, truncation=True).to(device)
            test_output = self.model(**test_input)
            self.embedding_dim = test_output.last_hidden_state.size(-1)
        
        print(f"Embedding dimension: {self.embedding_dim}")
    
    def get_sentence_embedding_dimension(self):
        return self.embedding_dim
    
    def encode(self, texts: Union[str, List[str]], convert_to_tensor: bool = False, 
               device: str = None, show_progress_bar: bool = False, batch_size: int = 32):
        """
        Encode texts into embeddings
        """
        if isinstance(texts, str):
            texts = [texts]
        
        if device is None:
            device = self.device
        
        all_embeddings = []
        
        # Process in batches
        for i in range(0, len(texts), batch_size):
            batch_texts = texts[i:i+batch_size]
            
            # Tokenize
            encoded = self.tokenizer(
                batch_texts,
                return_tensors="pt",
                padding=True,
                truncation=True,
                max_length=128
            ).to(device)
            
            # Get embeddings
            with torch.no_grad():
                outputs = self.model(**encoded)
                # Mean pooling
                embeddings = outputs.last_hidden_state.mean(dim=1)
                all_embeddings.append(embeddings.cpu())
        
        # Concatenate
        result = torch.cat(all_embeddings, dim=0)
        
        if convert_to_tensor:
            return result.to(device)
        else:
            return result.numpy()


# Compatibility wrapper for sentence-transformers API
class SentenceTransformerWrapper:
    """
    Wrapper that mimics sentence-transformers API but uses SimpleTextEncoder
    """
    
    def __init__(self, model_name: str = 'all-MiniLM-L6-v2', device: str = 'cpu'):
        # Convert model name if needed
        if not model_name.startswith('sentence-transformers/'):
            if '/' in model_name:
                model_name = f"sentence-transformers/{model_name}"
            else:
                model_name = f"sentence-transformers/{model_name}"
        
        self.encoder = SimpleTextEncoder(model_name, device=device)
        self._embedding_dim = self.encoder.get_sentence_embedding_dimension()
    
    def get_sentence_embedding_dimension(self):
        return self._embedding_dim
    
    def encode(self, sentences, convert_to_tensor=False, device=None, show_progress_bar=False, batch_size=32):
        if device is None:
            device = 'cpu'
        return self.encoder.encode(sentences, convert_to_tensor=convert_to_tensor, 
                                  device=device, show_progress_bar=show_progress_bar, 
                                  batch_size=batch_size)


# Test
if __name__ == '__main__':
    print("Testing SimpleTextEncoder...")
    encoder = SentenceTransformerWrapper('all-MiniLM-L6-v2', device='cpu')
    
    test_texts = ["This is a test", "Another test sentence"]
    embeddings = encoder.encode(test_texts, convert_to_tensor=True)
    print(f"Encoded {len(test_texts)} texts, shape: {embeddings.shape}")
    print("✓ Test passed!")

