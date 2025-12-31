# Phase 3 vs Phase 4 vs Real Data Comparison

**Generated:** 2025-12-06 16:47:24

---

## Overview

This report compares Phase 3 (Initial Approximation), Phase 4 (Ground Truth Anchored), and Real Data (Ground Truth) to demonstrate improvement.

## Key Metrics Comparison

| Metric | Phase 3 (Initial) | Real Data (Target) | Phase 4 (Anchored) | Phase 3 Error | Phase 4 Error | Improvement |
|--------|-------------------|---------------------|---------------------|---------------|---------------|-------------|
| Product Intent Mean | 0.6028 | 0.6381 | 0.6094 | 0.0353 | 0.0287 | 0.0066 (+18.8%) |
| Switching Rate | 0.9448 | 0.9474 | 0.9448 | 0.0026 | 0.0026 | 0.0000 (+0.0%) |
| Daily Trend | -0.000111 | 0.000025 | -0.000112 | 0.000137 | 0.000137 | -0.000000 (-0.3%) |

---

## Category-Level Comparison

| Category | Phase 3 | Real Data | Phase 4 | Phase 3 Error | Phase 4 Error | Improvement |
|----------|---------|-----------|---------|---------------|---------------|-------------|
| coffee_drink | 0.6053 | 0.6423 | 0.6121 | 0.0370 | 0.0302 | 0.0068 (+18.4%) ✅ |
| energy_drink | 0.6065 | 0.6590 | 0.6132 | 0.0525 | 0.0457 | 0.0068 (+12.9%) ✅ |
| juice | 0.5981 | 0.6287 | 0.6043 | 0.0306 | 0.0243 | 0.0062 (+20.4%) ✅ |
| soda | 0.5711 | 0.6199 | 0.5781 | 0.0488 | 0.0418 | 0.0069 (+14.2%) ✅ |
| sports_drink | 0.6090 | 0.6393 | 0.6157 | 0.0303 | 0.0236 | 0.0067 (+22.0%) ✅ |
| tea | 0.6137 | 0.6799 | 0.6203 | 0.0662 | 0.0596 | 0.0066 (+9.9%) ✅ |
| water_enhanced | 0.5970 | 0.6291 | 0.6036 | 0.0321 | 0.0255 | 0.0066 (+20.5%) ✅ |

---

## Segment-Level Comparison

| Segment | Phase 3 | Real Data | Phase 4 | Phase 3 Error | Phase 4 Error | Improvement |
|---------|---------|-----------|---------|---------------|---------------|-------------|
| seg_00 | 0.5996 | 0.6311 | 0.6048 | 0.0315 | 0.0262 | 0.0053 (+16.7%) ✅ |
| seg_01 | 0.6045 | 0.6659 | 0.6128 | 0.0615 | 0.0532 | 0.0083 (+13.5%) ✅ |
| seg_02 | 0.6092 | 0.6725 | 0.6177 | 0.0633 | 0.0548 | 0.0085 (+13.4%) ✅ |
| seg_03 | 0.6040 | 0.6524 | 0.6110 | 0.0484 | 0.0415 | 0.0070 (+14.4%) ✅ |
| seg_04 | 0.6110 | 0.6315 | 0.6152 | 0.0205 | 0.0163 | 0.0042 (+20.5%) ✅ |

---

## Summary

### Overall Error Reduction

- **Phase 3 Average Error:** 0.0190
- **Phase 4 Average Error:** 0.0156
- **Overall Improvement:** 0.0033 (+17.5% better)

✅ **Phase 4 successfully reduces error compared to Phase 3**

---

## File Locations

- **Phase 3 Data:** `simulations/intent_trajectories.csv`
- **Phase 4 Data:** `simulations/phase4_anchored.csv`
- **Real Data:** `data/real_intent_data.csv`
- **Visualizations:** `phase4_output/visualizations/`
- **Calibration Metrics:** `phase4_output/calibration_metrics.json`
