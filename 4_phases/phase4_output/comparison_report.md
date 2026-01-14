# Phase 3 vs Phase 4 vs Real Data Comparison

**Generated:** 2026-01-07 07:08:44

---

## Overview

This report compares Phase 3 (Initial Approximation), Phase 4 (Ground Truth Anchored), and Real Data (Ground Truth) to demonstrate improvement.

## Key Metrics Comparison

| Metric | Phase 3 (Initial) | Real Data (Target) | Phase 4 (Anchored) | Phase 3 Error | Phase 4 Error | Improvement |
|--------|-------------------|---------------------|---------------------|---------------|---------------|-------------|
| Product Intent Mean | 0.6284 | 0.6201 | N/A | 0.0083 | N/A | N/A |
| Switching Rate | 0.9552 | 0.9559 | N/A | 0.0007 | N/A | N/A |
| Daily Trend | 0.000064 | 0.000429 | N/A | 0.000365 | N/A | N/A |

---

## Category-Level Comparison

| Category | Phase 3 | Real Data | Phase 4 | Phase 3 Error | Phase 4 Error | Improvement |
|----------|---------|-----------|---------|---------------|---------------|-------------|
| coffee_drink | 0.6305 | 0.6469 | N/A | 0.0163 | N/A | N/A |
| energy_drink | 0.6214 | 0.6160 | N/A | 0.0055 | N/A | N/A |
| juice | 0.6782 | 0.6878 | N/A | 0.0096 | N/A | N/A |
| soda | 0.6268 | 0.6250 | N/A | 0.0018 | N/A | N/A |
| sports_drink | 0.6316 | 0.6243 | N/A | 0.0073 | N/A | N/A |
| tea | 0.6110 | 0.6176 | N/A | 0.0066 | N/A | N/A |
| water_enhanced | 0.6266 | 0.6160 | N/A | 0.0105 | N/A | N/A |

---

## Segment-Level Comparison

| Segment | Phase 3 | Real Data | Phase 4 | Phase 3 Error | Phase 4 Error | Improvement |
|---------|---------|-----------|---------|---------------|---------------|-------------|
| seg_00 | 0.6382 | 0.6454 | N/A | 0.0071 | N/A | N/A |
| seg_01 | 0.6117 | 0.6075 | N/A | 0.0042 | N/A | N/A |
| seg_02 | 0.6609 | 0.6585 | N/A | 0.0024 | N/A | N/A |
| seg_03 | 0.6436 | 0.6455 | N/A | 0.0019 | N/A | N/A |
| seg_05 | 0.6107 | 0.6020 | N/A | 0.0086 | N/A | N/A |
| seg_08 | 0.6120 | 0.6089 | N/A | 0.0031 | N/A | N/A |
| seg_09 | 0.6102 | 0.6083 | N/A | 0.0019 | N/A | N/A |

---

## Summary


---

## File Locations

- **Phase 3 Data:** `simulations/intent_trajectories.csv`
- **Phase 4 Data:** `simulations/phase4_anchored.csv`
- **Real Data:** `data/real_intent_data.csv`
- **Visualizations:** `phase4_output/visualizations/`
- **Calibration Metrics:** `phase4_output/calibration_metrics.json`
