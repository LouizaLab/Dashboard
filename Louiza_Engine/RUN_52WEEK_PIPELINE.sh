#!/bin/bash
# Complete 52-week pipeline for data_2026_01_09_run01
# This script runs: Persona initialization → Simulation → Anchoring → Visualizations

set -e  # Exit on error

DATA_VERSION="data_2026_01_09_run01"
PERSONA_VERSION="PersonaSet_v1.json"
BASELINE_RUN_DIR="runs/baseline_52w"
ANCHORED_RUN_DIR="runs/anchored_52w"
PLOTS_DIR="plots/baseline_52w"

echo "=========================================="
echo "Louiza Engine - 52 Week Pipeline"
echo "=========================================="
echo "Data Version: $DATA_VERSION"
echo ""

# Step 1: Initialize Personas
echo "Step 1: Initializing Personas..."
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

# Step 2: Run Baseline Simulation (52 weeks)
echo "Step 2: Running Baseline Simulation (52 weeks)..."
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

# Step 3: Run Anchoring (52 weeks with train/holdout split)
echo "Step 3: Running Anchoring Calibration..."
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
    --lambda-reg 0.01 \
    --use-relative-error \
    --output-dir $ANCHORED_RUN_DIR/

if [ ! -f "$ANCHORED_RUN_DIR/anchoring_report.json" ]; then
    echo "ERROR: Anchoring did not produce expected output!"
    exit 1
fi
echo "✓ Anchoring complete: $ANCHORED_RUN_DIR"
echo ""

# Step 4: Generate Visualizations
echo "Step 4: Generating Visualizations..."
python scripts/generate_all_plots.py \
    --run-id baseline_52w \
    --artifacts-dir $BASELINE_RUN_DIR/ \
    --output-dir $PLOTS_DIR/ \
    --data-version $DATA_VERSION \
    --personaset-path $PERSONA_VERSION \
    --anchoring-dir $ANCHORED_RUN_DIR/

echo ""
echo "=========================================="
echo "✓ Pipeline Complete!"
echo "=========================================="
echo "Results:"
echo "  - Personas: $PERSONA_VERSION"
echo "  - Simulation: $BASELINE_RUN_DIR/"
echo "  - Anchoring: $ANCHORED_RUN_DIR/"
echo "  - Visualizations: $PLOTS_DIR/"
echo ""
echo "View anchoring results:"
echo "  cat $ANCHORED_RUN_DIR/anchoring_report.json | python -m json.tool"
echo ""
echo "View plots:"
echo "  open $PLOTS_DIR/anchoring_before_after.png"

