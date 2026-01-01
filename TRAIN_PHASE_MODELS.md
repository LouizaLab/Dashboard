# Training Phase 1-2 Models for Phase 3-4 Integration

## Overview

To use the actual Phase 3-4 models (instead of simplified models), you need to train Phase 1 and Phase 2 models first. The checkpoints will be saved to `Louiza/checkpoints/` and `Louiza/checkpoints_phase2/`.

## Prerequisites

1. **Install dependencies**:
   ```bash
   cd Louiza
   pip install -r requirements.txt
   ```

2. **Verify data exists**:
   ```bash
   ls Louiza/data/
   # Should see: products.csv, contexts.csv, segments.csv, intent_logs.csv
   ```

## Step 1: Generate Training Data (if needed)

If the data files don't exist, generate them:

```bash
cd Louiza
python data_generator.py
```

This creates:
- `data/products.csv` - Product metadata
- `data/contexts.csv` - Context data
- `data/segments.csv` - Segment/demographic data
- `data/intent_logs.csv` - Intent/preference logs

## Step 2: Train Phase 1 Models

Phase 1 trains the embedding models (Product, Context, Segment):

```bash
cd Louiza
python train_phase1.py \
    --data_dir data \
    --output_dir checkpoints \
    --batch_size 32 \
    --learning_rate 0.001 \
    --n_epochs 50
```

**Expected output:**
- `checkpoints/best_model.pt` - Best model checkpoint
- `checkpoints/final_model.pt` - Final epoch checkpoint

**Training time:** ~5-15 minutes depending on data size

## Step 3: Train Phase 2 Models

Phase 2 trains the Behavioral Dynamic Engine (requires Phase 1 checkpoint):

```bash
cd Louiza
python train_phase2.py \
    --phase1_checkpoint checkpoints/best_model.pt \
    --data_dir data \
    --output_dir checkpoints_phase2 \
    --batch_size 32 \
    --learning_rate 0.0001 \
    --n_epochs 30 \
    --sequence_length 10
```

**Expected output:**
- `checkpoints_phase2/best_model_phase2.pt` - Best Phase 2 checkpoint
- `checkpoints_phase2/final_model_phase2.pt` - Final epoch checkpoint

**Training time:** ~10-30 minutes depending on data size

## Step 4: Verify Checkpoints

After training, verify checkpoints exist:

```bash
ls -lh Louiza/checkpoints/best_model.pt
ls -lh Louiza/checkpoints_phase2/best_model_phase2.pt
```

## Step 5: Test Phase 3-4 Integration

Run a simulation in the dashboard - it should now use the real models:

1. Navigate to "Recipe & Launch Simulation" tab
2. Select a recipe variant
3. Run simulation
4. Check logs - should see "Using Phase 3-4 LPM (Real Models)" instead of simplified

## Troubleshooting

### "No module named 'models'"
- Make sure you're in the `Louiza` directory when running training scripts
- Or add Louiza to PYTHONPATH: `export PYTHONPATH=$PYTHONPATH:/path/to/Louiza`

### "FileNotFoundError: data/products.csv"
- Run `python data_generator.py` first to generate data

### "CUDA out of memory"
- Reduce batch size: `--batch_size 16` or `--batch_size 8`
- Or use CPU: Set `device='cpu'` in training scripts

### Training takes too long
- Reduce epochs: `--n_epochs 20` (for testing)
- Reduce data size in `data_generator.py`

## Quick Training (Minimal)

For quick testing, use minimal epochs:

```bash
# Phase 1 (quick)
cd Louiza
python train_phase1.py --n_epochs 10 --batch_size 64

# Phase 2 (quick)
python train_phase2.py --phase1_checkpoint checkpoints/best_model.pt --n_epochs 10 --batch_size 64
```

## Full Training (Recommended)

For production use, train with full epochs:

```bash
# Phase 1 (full)
cd Louiza
python train_phase1.py --n_epochs 50 --batch_size 32

# Phase 2 (full)
python train_phase2.py --phase1_checkpoint checkpoints/best_model.pt --n_epochs 30 --batch_size 32
```

## What Gets Trained

### Phase 1 Models:
- **ProductEmbeddingModel**: Encodes products (ingredients, tags, nutrition, description) → 128-dim embedding
- **ContextEmbeddingModel**: Encodes contexts (time, location, occasion, price) → 64-dim embedding
- **SegmentEmbeddingModel**: Encodes segments (age, region, psychographic) → 64-dim embedding

### Phase 2 Model:
- **BehavioralDynamicEngine**: Models how agent states evolve over time
  - `initialize_state()`: Initializes agent state from segment
  - `predict_intent()`: Predicts purchase intent from state + product + context
  - `update_state()`: Updates agent state after interaction

## After Training

Once checkpoints are created:
1. The dashboard will automatically detect them
2. Phase 3-4 simulator will use real models
3. UI will show "✓ Phase 3-4 LPM Active" banner
4. Results will be more accurate (trained on data vs simplified)

## Model Checkpoints Location

- **Phase 1**: `Louiza/checkpoints/best_model.pt`
- **Phase 2**: `Louiza/checkpoints_phase2/best_model_phase2.pt`

The dashboard automatically looks for these paths.

