# Phase 1: Taste Embedding Model

A multi-modal embedding system that learns dense vector representations for food & beverage products, capturing sensory profiles, ingredient composition, nutrition signals, category similarity, and descriptive language.

## Table of Contents

1. [Overview](#overview)
2. [Project Structure](#project-structure)
3. [Installation](#installation)
4. [Quick Start](#quick-start)
5. [Training Models](#training-models)
6. [Generating Embeddings](#generating-embeddings)
7. [Evaluation](#evaluation)
8. [How It Works](#how-it-works)
9. [Troubleshooting](#troubleshooting)

## Overview

Phase 1 builds a **static** product embedding model (no temporal dynamics, no behavior evolution). The model combines multiple input modalities:

- **Text**: Product descriptions and ingredients (using transformers)
- **Sensory Tags**: Multi-hot encoding of sensory attributes (sweet, bitter, spicy, creamy, etc.)
- **Nutrition**: Normalized numeric features (calories, sugar, fat, protein, sodium, caffeine)
- **Category**: Categorical embeddings for product categories

The output is a **128-dimensional normalized embedding vector** per product that can be used for:
- Similarity search
- Product clustering
- Recommendation systems
- Category classification

## Project Structure

```
Phase_1_Taste_Embedding_Model/
├── data/
│   ├── raw/              # Raw datasets
│   └── processed/        # Normalized canonical schema (products.csv)
├── models/               # Trained model checkpoints
├── embeddings/           # Generated embeddings and indices
├── notebooks/            # Example notebooks
├── preprocess.py         # Data preprocessing pipeline
├── data_loader.py        # PyTorch dataset and loaders
├── model.py              # Model architecture
├── train_minimal.py      # Minimal training (no text, fast)
├── train_full.py         # Full training (with text)
├── embed_minimal.py      # Generate embeddings from minimal model
├── embed.py              # Generate embeddings from full model
├── evaluate.py           # Evaluation utilities
└── test_similarity.py    # Simple similarity search test
```

## Installation

1. Install dependencies:
```bash
pip install -r ../requirements.txt
```

2. Ensure you have the required datasets in `data/raw/`:
   - `mcd.csv` - McDonald's menu data
   - `burger-king-menu.csv` - Burger King menu data
   - `wendys-menu.csv` - Wendy's menu data

## Quick Start

### Step 1: Preprocess Data

Normalize all datasets into the canonical schema:

```bash
python3 preprocess.py
```

This creates `data/processed/products.csv` with 239 products.

### Step 2: Train Model (Choose One)

**Option A: Minimal Model (Recommended for macOS, fast)**
```bash
python3 train_minimal.py --epochs 50 --batch_size 32
```

**Option B: Full Model (Better embeddings, includes text)**
```bash
python3 train_full.py --epochs 50 --batch_size 32
```

### Step 3: Generate Embeddings

**For minimal model:**
```bash
python3 embed_minimal.py --model_file models/best_model_minimal.pt
```

**For full model:**
```bash
python3 embed.py --model_dir models --model_file best_model.pt
```

### Step 4: Evaluate

```bash
python3 evaluate.py \
    --embeddings embeddings/product_embeddings.npy \
    --metadata embeddings/product_metadata.json \
    --products data/processed/products.csv
```

### Step 5: Test Similarity Search

```bash
python3 test_similarity.py
```

## Training Models

### Minimal Model (`train_minimal.py`)

**What it does:**
- Trains embeddings using only tags, nutrition, and category features
- Skips text encoding to avoid macOS mutex issues
- Fast training (~1 second per epoch)
- Reliable and works everywhere

**Usage:**
```bash
python3 train_minimal.py \
    --data data/processed/products.csv \
    --output_dir models \
    --epochs 50 \
    --batch_size 32 \
    --lr 1e-3 \
    --hidden_dim 256 \
    --output_dim 128
```

**Arguments:**
- `--data`: Path to processed products CSV (default: `data/processed/products.csv`)
- `--output_dir`: Directory to save models (default: `models`)
- `--epochs`: Number of training epochs (default: 50)
- `--batch_size`: Batch size (default: 32)
- `--lr`: Learning rate (default: 1e-3)
- `--hidden_dim`: Hidden layer dimension (default: 256)
- `--output_dim`: Embedding dimension (default: 128)
- `--train_ratio`: Train/validation split ratio (default: 0.8)

**Output:**
- `models/best_model_minimal.pt` - Best model checkpoint (lowest validation loss)

### Full Model (`train_full.py`)

**What it does:**
- Trains embeddings with ALL features including text
- Uses simple text encoder (avoids macOS mutex issues)
- Better embeddings but slower training (~2 minutes per epoch)
- Recommended for production

**Usage:**
```bash
python3 train_full.py \
    --data data/processed/products.csv \
    --output_dir models \
    --epochs 50 \
    --batch_size 32 \
    --lr 1e-3 \
    --hidden_dim 256 \
    --output_dim 128 \
    --text_model all-MiniLM-L6-v2
```

**Arguments:**
- Same as minimal model, plus:
- `--text_model`: Sentence transformer model name (default: `all-MiniLM-L6-v2`)
- `--device`: Device to use (default: `auto`)

**Output:**
- `models/best_model.pt` - Best model checkpoint
- `models/final_model.pt` - Final epoch checkpoint
- `models/metadata.pkl` - Vocabularies and encoders
- `models/training_history.json` - Training loss history

**What happens during training:**
1. Loads and preprocesses product data
2. Initializes text encoder (downloads model on first run)
3. Pre-computes text embeddings for all products (~30-60 seconds)
4. Creates train/validation splits
5. Trains model with contrastive loss
6. Saves best model based on validation loss

## Generating Embeddings

### From Minimal Model (`embed_minimal.py`)

**Usage:**
```bash
python3 embed_minimal.py \
    --data data/processed/products.csv \
    --model_file models/best_model_minimal.pt \
    --output_dir embeddings \
    --batch_size 32
```

**Arguments:**
- `--data`: Path to products CSV (default: `data/processed/products.csv`)
- `--model_file`: Path to trained model (default: `models/best_model_minimal.pt`)
- `--output_dir`: Output directory (default: `embeddings`)
- `--batch_size`: Batch size for inference (default: 32)

**Output:**
- `embeddings/product_embeddings.npy` - NumPy array of all embeddings (239 x 128)
- `embeddings/product_metadata.json` - Product IDs and names mapping
- `embeddings/faiss_index.bin` - FAISS index for fast search (if FAISS installed)

### From Full Model (`embed.py`)

**Usage:**
```bash
python3 embed.py \
    --data data/processed/products.csv \
    --model_dir models \
    --model_file best_model.pt \
    --output_dir embeddings \
    --batch_size 32
```

**Arguments:**
- `--data`: Path to products CSV (default: `data/processed/products.csv`)
- `--model_dir`: Directory containing model (default: `models`)
- `--model_file`: Model checkpoint file (default: `best_model.pt`)
- `--output_dir`: Output directory (default: `embeddings`)
- `--batch_size`: Batch size for inference (default: 32)

**Output:**
- Same as minimal model embedding generation

## Evaluation

### Running Evaluation (`evaluate.py`)

**Usage:**
```bash
python3 evaluate.py \
    --embeddings embeddings/product_embeddings.npy \
    --metadata embeddings/product_metadata.json \
    --faiss_index embeddings/faiss_index.bin \
    --products data/processed/products.csv \
    --output_dir embeddings
```

**Arguments:**
- `--embeddings`: Path to embeddings numpy file
- `--metadata`: Path to metadata JSON file
- `--faiss_index`: Path to FAISS index (optional)
- `--products`: Path to products CSV
- `--output_dir`: Output directory for results

**What it does:**
1. **Category Separation Analysis**: Measures how well embeddings separate different categories
   - Intra-category similarity (should be high)
   - Inter-category similarity (should be low)
   - Separation score (difference, higher is better)

2. **Sanity Checks**: Validates expected similarities
   - Tests if similar products (e.g., Coke vs Pepsi) are close in embedding space
   - Tests if different products are far apart

3. **Clustering**: Groups products into clusters using K-means
   - Creates 10 clusters by default
   - Saves cluster assignments to JSON

4. **Visualization**: Creates t-SNE visualization of clusters
   - Saves `cluster_visualization.png`
   - Shows how products cluster in 2D space

**Output:**
- `embeddings/clusters.json` - Cluster assignments
- `embeddings/cluster_visualization.png` - t-SNE visualization

### Example Output

```
Category Separation Metrics:
Intra-category similarity (mean): 0.9871
Inter-category similarity (mean): -0.0512
Separation score: 1.0383
(Higher separation score = better category separation)
```

## How It Works

### Architecture

The embedding model combines multiple input modalities:

1. **Text Features** (Full model only):
   - Product descriptions + ingredients
   - Encoded using transformers (all-MiniLM-L6-v2)
   - 384-dimensional text embeddings
   - Projected to hidden_dim // 2

2. **Sensory Tags**:
   - Multi-hot encoding of tags (sweet, bitter, spicy, etc.)
   - Embedded and averaged
   - Projected to hidden_dim // 4

3. **Nutrition Features**:
   - 6 features: calories, sugar_g, fat_g, protein_g, sodium_mg, caffeine_mg
   - Normalized using StandardScaler
   - Projected to hidden_dim // 4

4. **Category Embedding**:
   - Category ID → embedding lookup
   - Projected to hidden_dim // 4

All features are concatenated and passed through a fusion MLP:
```
Input: [text_features, tag_features, nutrition_features, category_features]
↓
Fusion MLP (2 hidden layers, ReLU, Dropout)
↓
Output: 128D normalized embedding
```

### Training Objective

**Contrastive Loss** with temperature scaling:
- Maximizes similarity for products in the same category
- Minimizes similarity for products in different categories
- Uses cosine similarity in normalized embedding space
- Temperature parameter (0.1) controls softness of similarity

**Loss Formula:**
```
L = -log(σ(sim_pos / τ)) - log(σ(-sim_neg / τ))
```
Where:
- `sim_pos` = similarity between same-category products
- `sim_neg` = similarity between different-category products
- `τ` = temperature (0.1)
- `σ` = sigmoid function

### Data Flow

```
Raw Datasets (CSV)
    ↓
preprocess.py
    ↓
Canonical Schema (products.csv)
    ↓
data_loader.py → ProductDataset
    ↓
train_minimal.py / train_full.py
    ↓
Trained Model (best_model.pt)
    ↓
embed_minimal.py / embed.py
    ↓
Product Embeddings (product_embeddings.npy)
    ↓
evaluate.py / test_similarity.py
    ↓
Similarity Search, Clustering, Analysis
```

### Canonical Data Schema

All datasets are normalized into:

| Field | Type | Description |
|-------|------|-------------|
| `product_id` | string | Unique product identifier |
| `product_name` | string | Product name |
| `brand` | string | Brand name |
| `category` | string | Product category |
| `subcategory` | string | Product subcategory |
| `ingredients` | string | Comma-separated ingredients |
| `sensory_tags` | string | Comma-separated sensory tags |
| `nutrition_json` | JSON | Nutrition data (calories, sugar_g, fat_g, etc.) |
| `description` | string | Product description text |
| `price` | float | Product price (optional) |
| `source_dataset` | string | Source dataset identifier |

## Troubleshooting

### macOS Mutex Lock Issues

If you see errors like:
```
mutex lock failed: Invalid argument
[mutex.cc : 452] RAW: Lock blocking
```

**Solution**: Use `train_minimal.py` instead of `train_full.py`. The minimal model skips text encoding and avoids this issue.

### FAISS Not Installed

If you see:
```
ModuleNotFoundError: No module named 'faiss'
```

**Solution**: 
- Install FAISS: `pip install faiss-cpu`
- Or continue without it - evaluation will use sklearn (slower but works)

### Model File Not Found

If embedding generation fails:
```
FileNotFoundError: Model file not found
```

**Solution**: Make sure you've trained a model first:
```bash
python3 train_minimal.py --epochs 50
```

### Out of Memory

**Solution**: Reduce batch size:
```bash
python3 train_minimal.py --batch_size 16
```

### Poor Similarity Results

**Solution**: 
- Train for more epochs: `--epochs 100`
- Adjust learning rate: `--lr 5e-4`
- Check data quality in `data/processed/products.csv`

### Text Encoder Download Issues

If `train_full.py` hangs when downloading the model:

**Solution**:
1. Pre-download manually:
```python
from transformers import AutoTokenizer, AutoModel
tokenizer = AutoTokenizer.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
model = AutoModel.from_pretrained('sentence-transformers/all-MiniLM-L6-v2')
```

2. Or use minimal model instead

## Example Workflows

### Complete Workflow: Minimal Model

```bash
# 1. Preprocess
python3 preprocess.py

# 2. Train
python3 train_minimal.py --epochs 50 --batch_size 32

# 3. Generate embeddings
python3 embed_minimal.py --model_file models/best_model_minimal.pt

# 4. Evaluate
python3 evaluate.py \
    --embeddings embeddings/product_embeddings.npy \
    --metadata embeddings/product_metadata.json \
    --products data/processed/products.csv

# 5. Test similarity
python3 test_similarity.py
```

### Complete Workflow: Full Model

```bash
# 1. Preprocess
python3 preprocess.py

# 2. Train
python3 train_full.py --epochs 50 --batch_size 32

# 3. Generate embeddings
python3 embed.py --model_dir models --model_file best_model.pt

# 4. Evaluate
python3 evaluate.py \
    --embeddings embeddings/product_embeddings.npy \
    --metadata embeddings/product_metadata.json \
    --products data/processed/products.csv
```

### Using Embeddings in Python

```python
import numpy as np
import json
from sklearn.metrics.pairwise import cosine_similarity

# Load embeddings
embeddings = np.load('embeddings/product_embeddings.npy')

# Load metadata
with open('embeddings/product_metadata.json', 'r') as f:
    metadata = json.load(f)

product_names = metadata['product_names']

# Find similar products
def find_similar(product_name, top_k=5):
    idx = product_names.index(product_name)
    query = embeddings[idx:idx+1]
    similarities = cosine_similarity(query, embeddings)[0]
    top_indices = np.argsort(similarities)[::-1][1:top_k+1]
    return [(product_names[i], similarities[i]) for i in top_indices]

# Example
for name, sim in find_similar("Coca Cola- 16 fl oz", top_k=5):
    print(f"{name}: {sim:.4f}")
```

## Model Comparison

| Feature | Minimal Model | Full Model |
|---------|---------------|------------|
| **Text Encoding** | ❌ No | ✅ Yes |
| **Sensory Tags** | ✅ Yes | ✅ Yes |
| **Nutrition** | ✅ Yes | ✅ Yes |
| **Category** | ✅ Yes | ✅ Yes |
| **Training Speed** | ~1 sec/epoch | ~2 min/epoch |
| **macOS Compatibility** | ✅ Perfect | ✅ Good (uses simple encoder) |
| **Embedding Quality** | Good | Better |
| **Use Case** | Quick testing, development | Production, research |

## Next Steps

After Phase 1 is complete:

1. **Explore Embeddings**: Use `test_similarity.py` to find similar products
2. **Analyze Clusters**: Check `embeddings/clusters.json` for product groupings
3. **View Visualization**: Open `embeddings/cluster_visualization.png`
4. **Add More Data**: Add more products to `data/raw/` and re-run preprocessing
5. **Fine-tune**: Adjust hyperparameters for better results
6. **Move to Phase 2**: Build behavioral dynamic engine on top of these embeddings

## Files Reference

### Training Scripts
- `train_minimal.py` - Fast training without text (recommended for macOS)
- `train_full.py` - Full training with text features
- `train.py` - Original training script (may have mutex issues)

### Embedding Generation
- `embed_minimal.py` - Generate embeddings from minimal model
- `embed.py` - Generate embeddings from full model

### Evaluation
- `evaluate.py` - Comprehensive evaluation (clustering, separation, visualization)
- `test_similarity.py` - Simple similarity search test

### Data Processing
- `preprocess.py` - Normalize datasets into canonical schema
- `data_loader.py` - PyTorch dataset and data loaders

### Models
- `model.py` - ProductEmbeddingModel architecture
- `text_encoder_simple.py` - Simple text encoder (avoids mutex issues)

## License

See main project README for license information.
