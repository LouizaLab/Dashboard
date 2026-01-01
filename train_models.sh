#!/bin/bash
# Script to train Phase 1-2 models for Phase 3-4 integration

set -e  # Exit on error

echo "=========================================="
echo "Training Phase 1-2 Models for Phase 3-4"
echo "=========================================="

cd Louiza

# Step 1: Generate data if it doesn't exist
if [ ! -f "data/products.csv" ]; then
    echo "Generating training data..."
    python data_generator.py
else
    echo "Training data already exists, skipping generation..."
fi

# Step 2: Train Phase 1
echo ""
echo "=========================================="
echo "Training Phase 1: Embedding Models"
echo "=========================================="
python train_phase1.py \
    --data_dir data \
    --output_dir checkpoints \
    --batch_size 32 \
    --learning_rate 0.001 \
    --n_epochs 50

# Step 3: Train Phase 2 (requires Phase 1 checkpoint)
if [ -f "checkpoints/best_model.pt" ]; then
    echo ""
    echo "=========================================="
    echo "Training Phase 2: Behavioral Dynamic Engine"
    echo "=========================================="
    python train_phase2.py \
        --phase1_checkpoint checkpoints/best_model.pt \
        --data_dir data \
        --output_dir checkpoints_phase2 \
        --batch_size 32 \
        --learning_rate 0.0001 \
        --n_epochs 30 \
        --sequence_length 10
else
    echo "ERROR: Phase 1 checkpoint not found! Cannot train Phase 2."
    exit 1
fi

# Step 4: Verify checkpoints
echo ""
echo "=========================================="
echo "Verifying Checkpoints"
echo "=========================================="
if [ -f "checkpoints/best_model.pt" ] && [ -f "checkpoints_phase2/best_model_phase2.pt" ]; then
    echo "✓ Phase 1 checkpoint: checkpoints/best_model.pt"
    echo "✓ Phase 2 checkpoint: checkpoints_phase2/best_model_phase2.pt"
    echo ""
    echo "Training complete! The dashboard will now use real Phase 3-4 models."
else
    echo "ERROR: Checkpoints not found!"
    exit 1
fi

