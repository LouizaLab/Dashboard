#!/bin/bash
# Complete pipeline rerun with fixed observed metrics (minimum base transactions for all brands)
# This fixes BRAND_03 and BRAND_05 having near-zero observed revenue

set -e  # Exit on error

DATA_VERSION="data_2026_01_09_run01_clean_v2"
PERSONA_VERSION="PersonaSet_v1_clean_v2.json"
BASELINE_RUN_DIR="runs/baseline_52w_clean_v2"
ANCHORED_RUN_DIR="runs/anchored_52w_clean_v2"
PLOTS_DIR="plots/baseline_52w_clean_v2"

echo "=========================================="
echo "Louiza Engine - Fixed Pipeline Rerun"
echo "=========================================="
echo "Data Version: $DATA_VERSION"
echo ""

# Step 1: Data already compiled with fixes
echo "Step 1: Data compilation (already done with minimum base transactions)"
echo "✓ Data compiled: $DATA_VERSION"
echo ""

# Step 2: Initialize Personas
echo "Step 2: Initializing Personas..."
python scripts/initialize_personas.py \
    --data-version $DATA_VERSION \
    --output $PERSONA_VERSION \
    --num-personas 10

if [ ! -f "$PERSONA_VERSION" ]; then
    echo "ERROR: PersonaSet file not created!"
    exit 1
fi
echo "✓ Personas initialized: $PERSONA_VERSION"
echo ""

# Step 3: Run Baseline Simulation (52 weeks)
echo "Step 3: Running Baseline Simulation (52 weeks)..."
python scripts/run_simulation.py \
    --persona-version $PERSONA_VERSION \
    --data-version $DATA_VERSION \
    --scenario configs/baseline_scenario.json \
    --seed 123 \
    --num-agents 200000 \
    --start-week 1 \
    --output-dir $BASELINE_RUN_DIR/

if [ ! -f "$BASELINE_RUN_DIR/simulated_metrics_brand_week_region.csv" ]; then
    echo "ERROR: Simulation did not produce expected output!"
    exit 1
fi
echo "✓ Simulation complete: $BASELINE_RUN_DIR"
echo ""

# Step 4: Run Anchoring (52 weeks with train/holdout split)
echo "Step 4: Running Anchoring Calibration..."
echo "  Train weeks: 1-42 (80%)"
echo "  Holdout weeks: 43-52 (20%)"
python scripts/run_anchoring.py \
    --observed-data data/synthetic/$DATA_VERSION/observed_metrics_brand_week_region.csv \
    --simulated-data $BASELINE_RUN_DIR/simulated_metrics_brand_week_region.csv \
    --persona-contributions $BASELINE_RUN_DIR/persona_contributions.csv \
    --persona-version $PERSONA_VERSION \
    --train-weeks 1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23,24,25,26,27,28,29,30,31,32,33,34,35,36,37,38,39,40,41,42 \
    --holdout-weeks 43,44,45,46,47,48,49,50,51,52 \
    --alpha 1.0 \
    --beta 0.5 \
    --lambda-reg 0.05 \
    --use-relative-error \
    --output-dir $ANCHORED_RUN_DIR/

if [ ! -f "$ANCHORED_RUN_DIR/anchoring_report.json" ]; then
    echo "ERROR: Anchoring did not produce expected output!"
    exit 1
fi
echo "✓ Anchoring complete: $ANCHORED_RUN_DIR"
echo ""

# Step 5: Generate Visualizations
echo "Step 5: Generating Visualizations..."
python scripts/generate_all_plots.py \
    --run-id baseline_52w_clean_v2 \
    --artifacts-dir $BASELINE_RUN_DIR/ \
    --output-dir $PLOTS_DIR/ \
    --data-version $DATA_VERSION \
    --personaset-path $PERSONA_VERSION \
    --anchoring-dir $ANCHORED_RUN_DIR/

echo ""
echo "=========================================="
echo "✓ Fixed Pipeline Complete!"
echo "=========================================="
echo "Results:"
echo "  - Data: data/synthetic/$DATA_VERSION/"
echo "  - Personas: $PERSONA_VERSION"
echo "  - Simulation: $BASELINE_RUN_DIR/"
echo "  - Anchoring: $ANCHORED_RUN_DIR/"
echo "  - Visualizations: $PLOTS_DIR/"
echo ""
echo "View brands (should all have reasonable values now):"
echo "  cat data/synthetic/$DATA_VERSION/brands.csv"
echo ""
echo "View anchoring results:"
echo "  cat $ANCHORED_RUN_DIR/anchoring_report.json | python -m json.tool"
echo ""
echo "View revenue comparison plots:"
echo "  open $PLOTS_DIR/anchoring_before_after_by_brand_revenue.png"

