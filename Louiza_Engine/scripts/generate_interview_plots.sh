#!/bin/bash
# Generate all plots for interview-extracted data

python3 scripts/generate_all_plots.py \
    --run-id interview_anchored \
    --artifacts-dir runs/interview_baseline/ \
    --output-dir plots/interview_anchored/ \
    --data-version data_2026_01_15_interviews01 \
    --personaset-path PersonaSet_v1.json \
    --anchoring-dir runs/interview_anchored/ \
    --baseline-dir runs/interview_baseline/

echo ""
echo "✓ Plots generated in plots/interview_anchored/"

