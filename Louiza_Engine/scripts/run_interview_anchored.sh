#!/bin/bash
# Full pipeline: Simulation + Anchoring for interview-extracted data

set -e  # Exit on error

DATA_VERSION="data_2026_01_15_interviews01"
PERSONA_VERSION="PersonaSet_v1.json"
SCENARIO="configs/baseline_scenario.json"
NUM_AGENTS=10000
BASELINE_DIR="runs/interview_baseline"
ANCHORED_DIR="runs/interview_anchored"

echo "============================================================"
echo "Full Anchored Simulation Pipeline"
echo "============================================================"
echo "Data version: $DATA_VERSION"
echo "Persona version: $PERSONA_VERSION"
echo "Number of agents: $NUM_AGENTS"
echo ""

# Step 1: Run baseline simulation
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

echo ""
echo "✓ Simulation complete"
echo ""

# Step 2: Run anchoring
echo "Step 2: Running anchoring calibration..."
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
echo "  1. View plots: python3 scripts/generate_all_plots.py --run-dir $ANCHORED_DIR"
echo "  2. Run prompt workflow: python3 scripts/run_from_prompt.py \"Your question here\" --data-version $DATA_VERSION --enable-anchoring"

