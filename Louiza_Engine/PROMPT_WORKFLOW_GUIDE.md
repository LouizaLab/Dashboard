# Running Prompt-to-Simulation Workflow with Improved Anchoring

## Quick Start

The reasoning layer automatically uses the improved anchoring (with global scaling and relative error) when `--enable-anchoring` is used.

### Basic Command

```bash
python3 scripts/run_from_prompt.py \
    "What happens if we launch a promo campaign in US_South for 8 weeks?" \
    --data-version data_2026_01_08_run01 \
    --persona-version PersonaSet_v1.json \
    --enable-anchoring \
    --max-scenarios 3 \
    --max-runs 6 \
    --max-agents 10000
```

### Command Options

- **Prompt** (required): Natural language question describing your market scenario
- **--data-version**: Data version to use (default: auto-detect latest)
- **--persona-version**: PersonaSet version (default: PersonaSet_v1.json)
- **--enable-anchoring**: Enable anchoring calibration (uses improved version automatically)
- **--max-scenarios**: Maximum number of scenarios (default: 5)
- **--max-runs**: Maximum number of simulation runs (default: 10)
- **--max-agents**: Maximum agents per run (default: 10000)

### What Happens

1. **ParseRequest**: Extracts constraints from your prompt
2. **GenerateHypotheses**: Creates testable hypotheses
3. **RetrieveEvidence**: Loads observed data
4. **ScenarioBuilder**: Creates baseline + counterfactual scenarios
5. **RunPlanner**: Plans simulation runs
6. **SimulationRunner**: Executes LPM simulations
7. **AnchoringRunner**: **Runs improved anchoring** (if enabled)
   - Optimizes global scale factor (addresses magnitude mismatch)
   - Optimizes persona weights (fine-tunes distribution)
   - Uses relative error (better alignment)
8. **Comparator**: Compares scenarios
9. **InsightSynthesizer**: Generates insights
10. **ReportWriter**: Creates markdown report + visualizations

### Output Locations

- **Report**: `runs/reasoning_<timestamp>_<id>/report/report.md`
- **Anchoring Results**: `runs/reasoning_<timestamp>_<id>/anchoring/`
  - `anchoring_report.json` - Improvement metrics
  - `anchoring_patch.json` - Optimized parameters
  - `anchored_metrics_brand_week_region.csv` - Calibrated metrics
- **Plots**: `runs/reasoning_<timestamp>_<id>/report/plots/`
  - `anchoring_before_after.png` - Shows improved alignment
  - `anchoring_error_reduction.png` - Error reduction metrics
  - Other layer visualizations

### Example Prompts

```bash
# Promo campaign
python3 scripts/run_from_prompt.py \
    "What happens if BK launches a 20% discount promo in US_South for 6 weeks?" \
    --enable-anchoring

# Price change
python3 scripts/run_from_prompt.py \
    "How does a 10% price increase affect market share over 12 weeks?" \
    --enable-anchoring

# Menu launch
python3 scripts/run_from_prompt.py \
    "What is the impact of launching a new chicken wrap with promotional pricing?" \
    --enable-anchoring
```

### Improved Anchoring Features

The workflow automatically uses:
- ✅ **Global scaling**: Addresses magnitude mismatches (e.g., simulated 4x too low)
- ✅ **Relative error**: Normalizes by observed values for better alignment
- ✅ **Reduced regularization**: Allows larger weight adjustments
- ✅ **More iterations**: Better convergence

### Expected Results

With improved anchoring enabled, you should see:
- **80-90% loss reduction** (vs ~2% before)
- **Mean relative error: 10-15%** (vs 70%+ before)
- **Much better visual alignment** in before/after plots
- **Total transactions within 5-15%** of observed (vs 70%+ off before)

### Troubleshooting

**Anchoring fails with "No holdout data":**
- The workflow automatically detects available weeks and splits them
- If you have < 5 weeks, it uses all for training (no holdout)

**Simulations fail:**
- Check that data version exists: `ls data/synthetic/`
- Verify PersonaSet exists: `ls PersonaSet_v1.json`
- Reduce `--max-agents` if memory issues

**Want to see anchoring details:**
```bash
cat runs/reasoning_<id>/anchoring/anchoring_report.json | python3 -m json.tool
```

