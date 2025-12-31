# Cursor Prompt: Adapt Phase 1 for Real Restaurant Revenue Data

## Task: Adapt Phase 1 Embedding Model for Restaurant Revenue Data

I have real restaurant revenue data and need to adapt Phase 1 to create embeddings for restaurants. The original Phase 1 uses products + contexts + segments + intent logs, but I only have revenue data with restaurant characteristics.

### My Data Structure

I have a CSV file with restaurant revenue data containing:
- `date`: Date (datetime)
- `week`: Week number (0-51, or can be computed from date)
- `brand`: Restaurant brand name (e.g., "McDonalds", "BurgerKing", "Wendys", "TacoBell")
- `region`: Geographic region (e.g., "Northeast", "South", "Midwest", "West", "Southwest")
- `revenue`: Revenue value (continuous float)
- `price`: Price value (continuous float)
- `promotion`: Boolean (True/False)
- `holiday`: Boolean (True/False)

I do NOT have: contexts, segments, or intent logs. I only have some data.

### Goal

Create a Phase 1-style embedding model that:
1. Learns 128D embeddings for restaurants from revenue data
2. Uses revenue prediction as the self-supervised training task
3. Can reason over restaurant similarities and relationships
4. Follows the same architecture patterns as the original Phase 1

### What I Need

Please create these 4 files to adapt Phase 1:

#### 1. `models_restaurant.py`

Create a PyTorch model file with:

**RestaurantEmbeddingModel(nn.Module)**:
- **Inputs**: brand_id (LongTensor), region_id (LongTensor), price (FloatTensor, normalized), promotion (FloatTensor, 0/1), holiday (FloatTensor, 0/1), week (LongTensor, 0-51)
- **Architecture**:
  - Brand embedding: `nn.Embedding(brand_vocab_size, 64)`
  - Region embedding: `nn.Embedding(region_vocab_size, 64)`
  - Price projection: `nn.Linear(1, 64)` - projects normalized price
  - Promotion projection: `nn.Linear(1, 32)` - projects binary flag
  - Holiday projection: `nn.Linear(1, 32)` - projects binary flag
  - Week projection: `nn.Linear(2, 64)` - projects cyclical encoding (sin/cos of week/52 * 2π)
- **Fusion**: MLP combining all features:
  - Input dim: `64*4 + 32*2 = 320` (brand + region + price + week + promotion + holiday)
  - Layers: `320 → 256 → 128 → 128` with ReLU and Dropout(0.2)
- **Output**: 128D vector, L2 normalized using `F.normalize(..., p=2, dim=1)`
- Handle dimension mismatches (squeeze/unsqueeze tensors as needed)

**RevenuePredictor(nn.Module)**:
- Input: 128D restaurant embedding
- Architecture: `128 → 128 → 64 → 1` with ReLU, Dropout(0.3)
- Output: Predicted revenue (regression, no activation)

#### 2. `data_utils_restaurant.py`

Create data utilities:

**RestaurantDataset(Dataset)**:
- `__init__(self, revenue_df, normalize_revenue=True, normalize_price=True)`:
  - Takes pandas DataFrame
  - Creates `brand_to_idx` and `region_to_idx` mappings
  - Normalizes revenue and price (store mean/std)
  - Handles week column (create from date if missing: `pd.to_datetime(df['date']).dt.isocalendar().week - 1`)
- `__getitem__(self, idx)`: Returns dict with:
  - `brand_id`: LongTensor([brand_idx])
  - `region_id`: LongTensor([region_idx])
  - `price`: FloatTensor([normalized_price])
  - `promotion`: FloatTensor([1.0 if True else 0.0])
  - `holiday`: FloatTensor([1.0 if True else 0.0])
  - `week`: LongTensor([week_number])
  - `revenue`: FloatTensor([normalized_revenue]) - used as target
  - `brand`: string (for reference)
  - `region`: string (for reference)
- `get_vocab_sizes()`: Returns `{'brand_vocab_size': int, 'region_vocab_size': int}`
- `get_normalization_stats()`: Returns `{'revenue_mean': float, 'revenue_std': float, 'price_mean': float, 'price_std': float}`

**load_revenue_data(file_path)**:
- Loads CSV with `pd.read_csv()`
- Validates required columns: `brand`, `region`, `revenue`, `price`, `promotion`, `holiday`
- Creates `week` from `date` if missing
- Returns DataFrame

#### 3. `train_phase1_restaurant.py`

Create training script:

**train_phase1_restaurant(data_path, output_dir='checkpoints_restaurant', batch_size=32, learning_rate=0.001, n_epochs=50, device=None)**:
- Load data using `load_revenue_data()`
- Create `RestaurantDataset` instance
- Split 80/20 train/val
- Create DataLoaders
- Initialize:
  - `RestaurantEmbeddingModel` with vocab sizes from dataset
  - `RevenuePredictor`
- Setup: Adam optimizer, MSE loss
- Training loop:
  - Train epoch: forward → loss → backward → step
  - Validate epoch: forward → loss (no grad)
  - Save best model based on val loss
- Save checkpoint with:
  - Model state dicts
  - Vocab sizes and mappings
  - Normalization stats
  - Training history

**Command-line args**: `--data_path`, `--output_dir`, `--batch_size`, `--learning_rate`, `--n_epochs`

#### 4. `extract_restaurant_embeddings.py`

Create utility to extract embeddings:

**extract_embeddings(model_path, data_path, output_path='restaurant_embeddings.csv')**:
- Load checkpoint
- Reconstruct model
- Set to eval mode
- Extract embeddings for all data points
- Save CSV with metadata + embedding columns (emb_0 through emb_127)

**get_brand_embeddings(embeddings_df)**: Group by brand, compute mean embeddings

**get_region_embeddings(embeddings_df)**: Group by region, compute mean embeddings

### Key Implementation Details

1. **Normalization**: Normalize revenue and price using mean/std, store stats in checkpoint
2. **Cyclical Week Encoding**: `sin(week/52 * 2π)` and `cos(week/52 * 2π)` for temporal patterns
3. **L2 Normalization**: Always normalize final embeddings for similarity computation
4. **Dimension Handling**: Handle both `[B]` and `[B, 1]` tensor shapes appropriately

### Usage

After implementation, I should be able to run:

```bash
# Train
python train_phase1_restaurant.py --data_path revenue.csv --n_epochs 50

# Extract embeddings
python extract_restaurant_embeddings.py --model_path checkpoints_restaurant/best_model.pt --data_path revenue.csv
```

### Requirements

- Use PyTorch
- Follow original Phase 1 architecture patterns
- Include proper error handling and validation
- Add docstrings to all classes/functions
- Handle device placement (CPU/GPU auto-detect)
- Save checkpoints in standard format

Please implement all 4 files following these specifications. The code should be production-ready and well-documented.
