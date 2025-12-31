#!/bin/bash
# Full Pipeline: Enhanced Phase 3 + Phase 4
# Runs complete simulation and signal generation

echo "============================================================"
echo "Running Full Pipeline: Enhanced Phase 3 + Phase 4"
echo "============================================================"

# Step 1: Run enhanced Phase 3 simulation
echo ""
echo "Step 1: Running Enhanced Phase 3 Simulation..."
python main.py --mode simulate_phase3 \
    --n_agents 10 \
    --sim_days 30 \
    --interactions_per_day 1

# Step 2: Generate Phase 4 signals
echo ""
echo "Step 2: Generating Phase 4 Signals..."
python main.py --mode phase4 \
    --sim_output_dir simulations \
    --phase4_output_dir phase4_output

echo ""
echo "============================================================"
echo "Pipeline Complete!"
echo "============================================================"
echo ""
echo "Results available in:"
echo "  - simulations/intent_trajectories.csv (enhanced with price, season, inflation)"
echo "  - phase4_output/signals/ (all generated signals)"
echo "  - phase4_output/calibration_report.txt (calibration analysis)"

