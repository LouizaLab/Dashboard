#!/bin/bash
# Full pipeline with STRONG anchoring settings

set -e

DATA_VERSION="data_2026_01_15_interviews01"
PERSONA_VERSION="PersonaSet_v1.json"
SCENARIO="configs/baseline_scenario.json"
NUM_AGENTS=10000
BASELINE_DIR="runs/interview_baseline"
ANCHORED_DIR="runs/interview_anchored_strong"

echo "============================================================"
echo "Full Anchored Simulation Pipeline (STRONG SETTINGS)"
echo "============================================================"
echo "Data version: $DATA_VERSION"
echo "Persona version: $PERSONA_VERSION"
echo "Number of agents: $NUM_AGENTS"
echo "Lambda reg: 0.0001 (very low = more aggressive)"
echo ""

# Step 1: Run baseline simulation (skip if already exists)
if [ ! -f "$BASELINE_DIR/simulated_metrics_brand_week_region.csv" ]; then
    echo "Step 1: Running baseline simulation..."
    python3 scripts/run_simulation.py \
        --data-version "$DATA_VERSION" \
        --persona-version "$PERSONA_VERSION" \
        --scenario "$SCENARIO" \
        --output-dir "$BASELINE_DIR" \
        --num-agents $NUM_AGENTS
    
    if [ $? -ne 0 ]; then
        echo "✗ Simulation failed"
        exit 1
    fi
    echo "✓ Simulation complete"
else
    echo "Step 1: Using existing baseline simulation"
fi

echo ""

# Step 2: Run STRONG anchoring
echo "Step 2: Running STRONG anchoring calibration..."
python3 scripts/run_anchoring.py \
    --observed-data "data/synthetic/$DATA_VERSION/observed_metrics_brand_week_region.csv" \
    --simulated-data "$BASELINE_DIR/simulated_metrics_brand_week_region.csv" \
    --persona-contributions "$BASELINE_DIR/persona_contributions.csv" \
    --persona-version "$PERSONA_VERSION" \
    --output-dir "$ANCHORED_DIR" \
    --lambda-reg 0.0001 \
    --use-relative-error

if [ $? -ne 0 ]; then
    echo "✗ Anchoring failed"
    exit 1
fi

echo ""
echo "============================================================"
echo "✓ Full pipeline complete!"
echo "============================================================"
echo ""
echo "Results:"
echo "  Baseline simulation: $BASELINE_DIR"
echo "  Anchored results: $ANCHORED_DIR"
echo ""
echo "Next steps:"
echo "  1. View plots: ./scripts/generate_interview_plots.sh"
echo "  2. Check improvement: python3 -c \"import json; r=json.load(open('$ANCHORED_DIR/anchoring_report.json')); print(f'Improvement: {r[\\\"improvement\\\"][\\\"train_loss_reduction\\\"]:.1f}%')\""

