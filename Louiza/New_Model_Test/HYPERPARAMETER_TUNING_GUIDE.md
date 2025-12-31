# Hyperparameter Tuning Guide for LEM

## Current Configuration

```python
# Training hyperparameters
batch_size = 32
sequence_length = 10
learning_rate = 0.001
n_epochs = 1  # ⚠️ TOO LOW - This is the main issue!
alpha = 1.0   # NLL weight
beta = 0.1    # Smoothness weight
gamma = 0.01  # Entropy regularization weight

# Model architecture
latent_dim = 64
hidden_dim = 128
n_layers = 2
dropout = 0.1
action_embed_dim = 32
context_embed_dim = 32
```

---

## Priority 1: Increase Training Epochs ⭐ **MOST IMPORTANT**

### Current: `n_epochs = 1`
### Recommended: `n_epochs = 25-30`

**Why:** With only 1 epoch, the model has barely seen the data. This is the #1 reason for suboptimal performance.

**Expected improvements:**
- NLL should decrease from 2.32 → ~2.0-2.1
- Entropy should decrease from 3.28 → ~2.5-2.8
- Accuracy may improve from 25.9% → 30-35%

**How to implement:**
```python
n_epochs = 25  # Start here
# Monitor validation loss - stop if it plateaus or increases
```

---

## Priority 2: Learning Rate Schedule

### Current: Fixed LR = 0.001
### Recommended: Learning rate scheduling

**Options:**

#### Option A: ReduceLROnPlateau (Already implemented, but adjust)
```python
scheduler = optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, 
    mode='min', 
    factor=0.5,      # Reduce by half
    patience=5,      # Wait 5 epochs (increase from 3)
    min_lr=1e-5      # Don't go below this
)
```

#### Option B: Cosine Annealing (Better for longer training)
```python
scheduler = optim.lr_scheduler.CosineAnnealingLR(
    optimizer,
    T_max=n_epochs,
    eta_min=1e-5
)
```

#### Option C: Warmup + Cosine
```python
# Warmup for first 3 epochs, then cosine decay
def get_lr(epoch):
    if epoch < 3:
        return 0.001 * (epoch + 1) / 3  # Warmup
    else:
        return 0.001 * 0.5 * (1 + np.cos(np.pi * (epoch - 3) / (n_epochs - 3)))
```

**Recommended learning rates:**
- Start: `0.001` (current is good)
- Try: `0.0005` (more conservative) or `0.002` (more aggressive)
- Minimum: `1e-5`

---

## Priority 3: Model Architecture Hyperparameters

### 3.1 Hidden Dimension (`hidden_dim`)

**Current:** `128`
**Try:** `[128, 256, 512]`

**Trade-offs:**
- **128**: Fast training, may underfit
- **256**: Good balance (RECOMMENDED)
- **512**: More capacity, slower, risk of overfitting

**Recommendation:** Start with `256`

```python
hidden_dim = 256  # Increase from 128
```

### 3.2 Latent Dimension (`latent_dim`)

**Current:** `64`
**Try:** `[64, 128, 256]`

**Trade-offs:**
- **64**: May be too small for complex state space
- **128**: Good balance (RECOMMENDED)
- **256**: More expressive, but harder to train

**Recommendation:** Try `128` to match hidden_dim scaling

```python
latent_dim = 128  # Increase from 64
```

### 3.3 Number of Layers (`n_layers`)

**Current:** `2`
**Try:** `[2, 3, 4]`

**Trade-offs:**
- **2**: Current - good for most cases
- **3**: More capacity, better for long sequences
- **4**: Risk of vanishing gradients

**Recommendation:** Try `3` if you increase sequence_length

```python
n_layers = 3  # Increase from 2
```

### 3.4 Dropout (`dropout`)

**Current:** `0.1`
**Try:** `[0.1, 0.2, 0.3]`

**Trade-offs:**
- **0.1**: Current - may be too low
- **0.2**: Good regularization (RECOMMENDED)
- **0.3**: Strong regularization, may hurt performance

**Recommendation:** Increase to `0.2` for better generalization

```python
dropout = 0.2  # Increase from 0.1
```

### 3.5 Embedding Dimensions

**Current:** `action_embed_dim = 32`, `context_embed_dim = 32`
**Try:** `[32, 64, 128]`

**Recommendation:** Increase to `64` for richer representations

```python
action_embed_dim = 64
context_embed_dim = 64
```

---

## Priority 4: Training Hyperparameters

### 4.1 Batch Size (`batch_size`)

**Current:** `32`
**Try:** `[32, 64, 128]`

**Trade-offs:**
- **32**: Current - good for memory
- **64**: Faster training, more stable gradients (RECOMMENDED)
- **128**: Even faster, but may hurt generalization

**Recommendation:** Increase to `64` if you have GPU memory

```python
batch_size = 64  # Increase from 32
```

### 4.2 Sequence Length (`sequence_length`)

**Current:** `10`
**Try:** `[10, 20, 30]`

**Trade-offs:**
- **10**: Current - short context
- **20**: Better temporal context (RECOMMENDED)
- **30**: Long context, more memory

**Recommendation:** Try `20` to capture longer patterns

```python
sequence_length = 20  # Increase from 10
```

**Note:** This requires more memory and training time.

---

## Priority 5: Loss Function Weights

### 5.1 Alpha (NLL Weight)

**Current:** `alpha = 1.0`
**Status:** ✅ Good - keep as is

### 5.2 Beta (Smoothness Weight)

**Current:** `beta = 0.1`
**Try:** `[0.05, 0.1, 0.2, 0.5]`

**What it does:** Encourages smooth state transitions

**Recommendation:** 
- Start with `0.1` (current)
- Increase to `0.2` if states are too noisy
- Decrease to `0.05` if model is too constrained

### 5.3 Gamma (Entropy Regularization)

**Current:** `gamma = 0.01`
**Try:** `[0.01, 0.05, 0.1]`

**What it does:** Encourages moderate prediction uncertainty

**Recommendation:**
- Current `0.01` is good
- Increase to `0.05` if predictions are too confident
- Decrease if model is too uncertain

---

## Recommended Configuration (Start Here)

```python
# Training hyperparameters
batch_size = 64              # Increased from 32
sequence_length = 15         # Increased from 10
learning_rate = 0.001        # Keep
n_epochs = 25                # ⭐ CRITICAL: Increase from 1
alpha = 1.0                  # Keep
beta = 0.1                   # Keep
gamma = 0.01                 # Keep

# Model architecture
latent_dim = 128             # Increased from 64
hidden_dim = 256             # Increased from 128
n_layers = 2                 # Keep (try 3 later)
dropout = 0.2                # Increased from 0.1
action_embed_dim = 64        # Increased from 32
context_embed_dim = 64       # Increased from 32

# Optimizer
optimizer = optim.Adam(model.parameters(), lr=learning_rate, weight_decay=1e-5)
scheduler = optim.lr_scheduler.ReduceLROnPlateau(
    optimizer, mode='min', factor=0.5, patience=5, min_lr=1e-5
)
```

---

## Hyperparameter Tuning Strategy

### Phase 1: Quick Wins (Do First)
1. ✅ **Increase epochs to 25** - Biggest impact
2. ✅ **Increase batch_size to 64** - Faster training
3. ✅ **Increase hidden_dim to 256** - More capacity
4. ✅ **Increase dropout to 0.2** - Better regularization

### Phase 2: Architecture Tuning
1. Try `latent_dim = 128`
2. Try `n_layers = 3`
3. Try `sequence_length = 20`
4. Try larger embedding dimensions

### Phase 3: Fine-tuning
1. Adjust learning rate schedule
2. Tune loss weights (beta, gamma)
3. Add weight decay to optimizer
4. Try different optimizers (AdamW)

---

## Expected Performance Improvements

### With Recommended Config (25 epochs, larger model):

| Metric | Current (1 epoch) | Expected (25 epochs) | Improvement |
|--------|-------------------|----------------------|-------------|
| Accuracy | 25.93% | **30-35%** | +15-35% |
| Category Accuracy | 35.72% | **40-45%** | +12-26% |
| Brand Accuracy | 65.01% | **70-75%** | +8-15% |
| NLL | 2.32 | **2.0-2.1** | -10-14% |
| Entropy | 3.28 | **2.5-2.8** | -15-24% |

---

## Monitoring Training

### Key Metrics to Watch:

1. **Validation NLL** - Should decrease steadily
2. **Validation Accuracy** - Should increase
3. **Training vs Validation Gap** - Should be small (avoid overfitting)
4. **Learning Rate** - Should decrease when plateauing

### Early Stopping:

Add early stopping to prevent overfitting:

```python
patience = 7  # Stop if no improvement for 7 epochs
best_val_nll = float('inf')
patience_counter = 0

for epoch in range(n_epochs):
    # ... training code ...
    
    if val_metrics['nll'] < best_val_nll:
        best_val_nll = val_metrics['nll']
        patience_counter = 0
        # Save best model
    else:
        patience_counter += 1
        if patience_counter >= patience:
            print(f"Early stopping at epoch {epoch+1}")
            break
```

---

## Advanced Optimizations

### 1. Gradient Clipping
Already implemented (`max_norm=1.0`) - ✅ Good

### 2. Weight Decay (L2 Regularization)
```python
optimizer = optim.Adam(
    model.parameters(), 
    lr=learning_rate,
    weight_decay=1e-5  # Add this
)
```

### 3. Label Smoothing
Modify loss function to use label smoothing for better calibration.

### 4. Mixed Precision Training
If using GPU, enable mixed precision for faster training:
```python
from torch.cuda.amp import autocast, GradScaler
scaler = GradScaler()
```

### 5. Learning Rate Warmup
Warm up learning rate for first few epochs:
```python
def warmup_lr(epoch, warmup_epochs=3):
    if epoch < warmup_epochs:
        return (epoch + 1) / warmup_epochs
    return 1.0
```

---

## Quick Start: Updated train.py

Here's what to change in `train.py`:

```python
# Line 229-235: Update hyperparameters
batch_size = 64              # Changed from 32
sequence_length = 15          # Changed from 10
learning_rate = 0.001         # Keep
n_epochs = 25                # ⭐ Changed from 1
alpha = 1.0                  # Keep
beta = 0.1                   # Keep
gamma = 0.01                 # Keep

# Line 283-289: Update model architecture
model = LEM(
    n_categories=len(category_to_idx),
    n_brands=len(brand_to_idx) - 1,
    action_embed_dim=64,      # Changed from 32
    context_embed_dim=64,     # Changed from 32
    latent_dim=128,           # Changed from 64
    hidden_dim=256,           # Changed from 128
    n_layers=2,              # Keep (try 3 later)
    dropout=0.2               # Changed from 0.1
).to(device)

# Line 294: Add weight decay
optimizer = optim.Adam(
    model.parameters(), 
    lr=learning_rate,
    weight_decay=1e-5         # Add this
)
```

---

## Summary: Top 5 Changes to Make

1. ⭐⭐⭐ **n_epochs = 25** (from 1) - **CRITICAL**
2. ⭐⭐ **hidden_dim = 256** (from 128) - More capacity
3. ⭐⭐ **batch_size = 64** (from 32) - Faster, more stable
4. ⭐ **dropout = 0.2** (from 0.1) - Better regularization
5. ⭐ **latent_dim = 128** (from 64) - More expressive states

Start with these 5 changes and you should see significant improvements!

