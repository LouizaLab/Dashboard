#!/bin/bash

# Complete pipeline script for New Model Test
# Runs all steps in sequence

set -e  # Exit on error

echo "=========================================="
echo "Large Emotional Model (LEM) Pipeline"
echo "=========================================="

# Step 1: Generate data
echo ""
echo "Step 1: Generating synthetic data..."
python generate_data.py

# Step 2: Train model
echo ""
echo "Step 2: Training LEM model..."
python train.py

# Step 3: Evaluate
echo ""
echo "Step 3: Evaluating models..."
python eval.py

# Step 4: Generate visualizations
echo ""
echo "Step 4: Generating visualizations..."
python visualize.py

# Step 5: Interpretability analysis
echo ""
echo "Step 5: Running interpretability analysis..."
python interpretability.py

# Step 6: Generate conclusion
echo ""
echo "Step 6: Generating research conclusion..."
python generate_conclusion.py

echo ""
echo "=========================================="
echo "Pipeline complete!"
echo "=========================================="
echo ""
echo "Results saved in:"
echo "  - eval/metrics.json"
echo "  - eval/conclusion.txt"
echo "  - plots/*.png"
echo ""

