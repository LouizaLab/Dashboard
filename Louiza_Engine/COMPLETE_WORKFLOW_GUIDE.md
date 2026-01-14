# Complete Louiza Engine Workflow Guide

A comprehensive guide from persona creation to prompt-based simulation with anchoring and hyperparameter optimization.

---

## Table of Contents

1. [Phase 1: Data Generation](#phase-1-data-generation)
2. [Phase 2: Persona Creation](#phase-2-persona-creation)
3. [Phase 3: Baseline Simulation](#phase-3-baseline-simulation)
4. [Phase 4: Anchoring & Calibration](#phase-4-anchoring--calibration)
5. [Phase 5: Hyperparameter Tuning](#phase-5-hyperparameter-tuning)
6. [Phase 6: Prompt-Based Simulation](#phase-6-prompt-based-simulation)
7. [Phase 7: Comparing Results & Iteration](#phase-7-comparing-results--iteration)

---

## Phase 1: Data Generation

### Step 1.1: Generate Synthetic Data

First, create synthetic observed data that will serve as ground truth for anchoring.

```bash
python3 scripts/generate_synthetic_data.py \
    --config configs/synthetic_config.json \
    --seed 42 \
    --output-dir data/synthetic/
```

**Output**: Creates versioned directory like `data/synthetic/data_2026_01_08_run01/`

**Files Created**:
- `observed_metrics_brand_week_region.csv` - Ground truth metrics
- `brand_price_schedule.csv` - Price history
- `brand_promo_schedule.csv` - Promo history
- `entities.csv` - Brand/region metadata

### Step 1.2: Verify Data Quality

```bash
# Check data coverage
python3 -c "
import pandas as pd
obs = pd.read_csv('data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv')
print(f'Weeks: {sorted(obs[\"week_id\"].unique())}')
print(f'Brands: {sorted(obs[\"brand_id\"].unique())}')
print(f'Regions: {sorted(obs[\"region_id\"].unique())}')
print(f'Total rows: {len(obs)}')
"
```

**Expected**: 10-12 weeks, multiple brands/regions, thousands of rows

---

## Phase 2: Persona Creation

### Step 2.1: Initialize PersonaSet

Create an initial set of diverse personas that represent different consumer archetypes.

```bash
python3 scripts/initialize_personas.py \
    --data-version data_2026_01_08_run01 \
    --output PersonaSet_v1.json \
    --num-personas 10
```

**Output**: `PersonaSet_v1.json` with 10 personas

**Persona Types** (examples):
- `persona_01_price_sensitive_loyalist` - Price-conscious but loyal
- `persona_02_promo_driven_switcher` - Switches based on promotions
- `persona_03_novelty_seeker` - Tries new products
- `persona_04_convenience_first_regular` - Values convenience
- `persona_05_brand_a_loyalist` - Strong brand loyalty
- `persona_06_brand_b_loyalist` - Strong brand loyalty (different brand)
- `persona_07_value_seeker` - Seeks best value
- `persona_08_quality_focused` - Prioritizes quality
- `persona_09_casual_explorer` - Tries different options
- `persona_10_routine_follower` - Sticks to routine

### Step 2.2: Inspect PersonaSet

```bash
# View persona weights
python3 -c "
import json
with open('PersonaSet_v1.json') as f:
    ps = json.load(f)
    for p in ps['personas']:
        if p['status'] == 'active':
            print(f\"{p['persona_id']}: {p['population_weight']['global']:.3f}\")
"
```

**Expected**: All active persona weights sum to 1.0

### Step 2.3: Customize Personas (Optional)

Edit `PersonaSet_v1.json` to adjust:
- **Population weights**: Change `population_weight.global` values
- **Behavioral parameters**: Adjust `price_sensitivity`, `promo_sensitivity`, etc.
- **State priors**: Modify initial state distributions

**Important**: Ensure weights still sum to 1.0 after changes!

---

## Phase 3: Baseline Simulation

### Step 3.1: Create Baseline Scenario

Create `configs/baseline_scenario.json`:

```json
{
  "scenario_id": "S0_baseline",
  "time_horizon_weeks": 12,
  "interventions": []
}
```

### Step 3.2: Run Baseline Simulation

```bash
python3 scripts/run_simulation.py \
    --persona-version PersonaSet_v1.json \
    --scenario configs/baseline_scenario.json \
    --data-version data_2026_01_08_run01 \
    --seed 123 \
    --num-agents 10000 \
    --output-dir runs/baseline_v1/
```

**Output**:
- `simulated_metrics_brand_week_region.csv` - Simulated outcomes
- `persona_contributions.csv` - Per-persona contributions
- `run_metadata.json` - Run configuration

### Step 3.3: Check Initial Alignment

```bash
python3 -c "
import pandas as pd
obs = pd.read_csv('data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv')
sim = pd.read_csv('runs/baseline_v1/simulated_metrics_brand_week_region.csv')

obs_total = obs['transactions_obs'].sum()
sim_total = sim['transactions_sim'].sum()

print(f'Observed total: {obs_total:,.0f}')
print(f'Simulated total: {sim_total:,.0f}')
print(f'Ratio: {obs_total/sim_total:.2f}x')
print(f'Simulated is {((sim_total/obs_total - 1) * 100):.1f}% of observed')
"
```

**Expected**: You'll likely see simulated is 20-30% of observed (this is what anchoring fixes!)

---

## Phase 4: Anchoring & Calibration

### Step 4.1: Basic Anchoring Run

Run anchoring with default hyperparameters:

```bash
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/baseline_v1/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/baseline_v1/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --output-dir runs/anchored_baseline/
```

**Default Hyperparameters**:
- `alpha=1.0` - Weight for transactions error
- `beta=0.5` - Weight for revenue error
- `lambda_reg=0.01` - Regularization strength
- `use_relative_error=True` - Use relative error (recommended)
- Global scaling: Automatically optimized

### Step 4.2: Check Anchoring Results

```bash
cat runs/anchored_baseline/anchoring_report.json | python3 -m json.tool
```

**Key Metrics**:
- `improvement.train_loss_reduction`: Should be 80-90%
- `global_scale`: Typically 2-5x if simulated was too low
- `parameter_deltas`: Shows which personas were adjusted

### Step 4.3: Generate Visualizations

```bash
python3 scripts/generate_all_plots.py \
    --run-id anchored_baseline \
    --artifacts-dir runs/baseline_v1 \
    --output-dir plots/anchored_baseline/ \
    --data-version data_2026_01_08_run01 \
    --personaset-path PersonaSet_v1.json \
    --anchoring-dir runs/anchored_baseline
```

**Key Plots**:
- `anchoring_before_after.png` - Visual alignment check
- `anchoring_error_reduction.png` - Error metrics
- `persona_weight_adjustments.png` - Weight changes

---

## Phase 5: Hyperparameter Tuning

### Step 5.1: Understanding Hyperparameters

**Anchoring Hyperparameters**:

1. **`alpha`** (default: 1.0)
   - Weight for transactions error
   - Increase to prioritize transaction accuracy
   - Range: 0.1 - 10.0

2. **`beta`** (default: 0.5)
   - Weight for revenue error
   - Increase to prioritize revenue accuracy
   - Range: 0.1 - 10.0

3. **`lambda_reg`** (default: 0.01)
   - Regularization strength
   - Lower = larger weight adjustments (risk overfitting)
   - Higher = smaller adjustments (more stable)
   - Range: 0.001 - 0.1

4. **`use_relative_error`** (default: True)
   - Use relative error vs absolute error
   - Relative: Normalizes by observed values (recommended)
   - Absolute: Raw squared error

5. **Train/Holdout Split**
   - `train_weeks`: Weeks used for optimization
   - `holdout_weeks`: Weeks used for validation
   - Typical: 80/20 split

### Step 5.2: Experiment 1: Vary Regularization

Test different regularization strengths:

```bash
# Low regularization (more aggressive adjustments)
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/baseline_v1/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/baseline_v1/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --lambda-reg 0.001 \
    --output-dir runs/anchored_low_reg/

# Medium regularization (default)
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/baseline_v1/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/baseline_v1/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --lambda-reg 0.01 \
    --output-dir runs/anchored_med_reg/

# High regularization (more conservative)
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/baseline_v1/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/baseline_v1/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --lambda-reg 0.05 \
    --output-dir runs/anchored_high_reg/
```

**Compare Results**:
```bash
for dir in runs/anchored_*_reg/; do
    echo "=== $dir ==="
    cat $dir/anchoring_report.json | python3 -c "
import json, sys
r = json.load(sys.stdin)
print(f\"Improvement: {r['improvement']['train_loss_reduction']:.1f}%\")
print(f\"Holdout loss: {r['after_anchoring']['holdout_loss']:.2f}\")
"
done
```

**What to Look For**:
- Higher improvement on train set
- But check holdout loss doesn't increase too much
- If holdout loss increases >20%, regularization might be too low

### Step 5.3: Experiment 2: Vary Error Weights

Test different alpha/beta ratios:

```bash
# Prioritize transactions
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/baseline_v1/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/baseline_v1/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --alpha 2.0 \
    --beta 0.5 \
    --output-dir runs/anchored_high_tx/

# Prioritize revenue
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/baseline_v1/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/baseline_v1/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --alpha 1.0 \
    --beta 2.0 \
    --output-dir runs/anchored_high_rev/

# Balanced
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/baseline_v1/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/baseline_v1/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --alpha 1.0 \
    --beta 1.0 \
    --output-dir runs/anchored_balanced/
```

### Step 5.4: Experiment 3: Different Train/Holdout Splits

```bash
# Early weeks for training (weeks 1-8), later for holdout (9-12)
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/baseline_v1/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/baseline_v1/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --train-weeks 1,2,3,4,5,6,7,8 \
    --holdout-weeks 9,10,11,12 \
    --output-dir runs/anchored_split_early/

# Later weeks for training (weeks 5-12), earlier for holdout (1-4)
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/baseline_v1/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/baseline_v1/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --train-weeks 5,6,7,8,9,10,11,12 \
    --holdout-weeks 1,2,3,4 \
    --output-dir runs/anchored_split_late/
```

### Step 5.5: Compare All Experiments

Create a comparison script:

```bash
cat > compare_anchoring_runs.py << 'EOF'
import json
import glob
from pathlib import Path

runs = glob.glob('runs/anchored_*/anchoring_report.json')

print("Anchoring Run Comparison")
print("=" * 80)
print(f"{'Run':<30} {'Train Loss':<15} {'Holdout Loss':<15} {'Improvement':<15}")
print("-" * 80)

for run_file in sorted(runs):
    with open(run_file) as f:
        report = json.load(f)
    
    run_name = Path(run_file).parent.name
    train_loss = report['after_anchoring']['train_loss']
    holdout_loss = report['after_anchoring']['holdout_loss']
    improvement = report['improvement']['train_loss_reduction']
    
    print(f"{run_name:<30} {train_loss:<15.2f} {holdout_loss:<15.2f} {improvement:<15.1f}%")
EOF

python3 compare_anchoring_runs.py
```

**Select Best Configuration**:
- Highest improvement on train set
- Low holdout loss (indicates good generalization)
- Stable persona weight adjustments (not too extreme)

---

## Phase 6: Prompt-Based Simulation

### Step 6.1: Run Prompt Workflow with Anchoring

Use the best anchoring configuration from Phase 5:

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

**What Happens**:
1. Parses prompt → extracts constraints
2. Generates hypotheses
3. Creates scenarios (baseline + counterfactuals)
4. Runs simulations
5. **Runs anchoring** (with improved hyperparameters)
6. Compares scenarios
7. Generates report + visualizations

### Step 6.2: Check Results

```bash
# Find latest reasoning run
LATEST_RUN=$(ls -td runs/reasoning_* | head -1)

# View report
cat $LATEST_RUN/report/report.md

# Check anchoring results
cat $LATEST_RUN/anchoring/anchoring_report.json | python3 -m json.tool | head -20

# View plots
ls -lh $LATEST_RUN/report/plots/
```

### Step 6.3: Try Different Prompts

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

# Multiple interventions
python3 scripts/run_from_prompt.py \
    "What happens if we reduce prices by 5% and launch a new product simultaneously?" \
    --enable-anchoring
```

---

## Phase 7: Comparing Results & Iteration

### Step 7.1: Compare Multiple Runs

```bash
cat > compare_prompt_runs.py << 'EOF'
import json
import glob
from pathlib import Path

runs = glob.glob('runs/reasoning_*/anchoring/anchoring_report.json')

print("Prompt Run Comparison")
print("=" * 100)
print(f"{'Run ID':<40} {'Improvement':<15} {'Holdout Loss':<15} {'Global Scale':<15}")
print("-" * 100)

for run_file in sorted(runs):
    try:
        with open(run_file) as f:
            report = json.load(f)
        
        run_id = Path(run_file).parent.parent.name
        improvement = report.get('improvement', {}).get('train_loss_reduction', 0)
        holdout_loss = report.get('after_anchoring', {}).get('holdout_loss', 0)
        global_scale = report.get('global_scale', 1.0)
        
        print(f"{run_id:<40} {improvement:<15.1f}% {holdout_loss:<15.2f} {global_scale:<15.3f}")
    except:
        pass
EOF

python3 compare_prompt_runs.py
```

### Step 7.2: Analyze Persona Weight Changes

```bash
cat > analyze_persona_changes.py << 'EOF'
import json
import glob
from collections import defaultdict

runs = glob.glob('runs/anchored_*/anchoring_patch.json')

persona_deltas = defaultdict(list)

for run_file in runs:
    with open(run_file) as f:
        patch = json.load(f)
    
    run_name = Path(run_file).parent.name
    for persona_id, updates in patch.get('parameter_updates', {}).items():
        if 'population_weight.global' in updates:
            delta = updates['population_weight.global']
            persona_deltas[persona_id].append((run_name, delta))

print("Persona Weight Changes Across Runs")
print("=" * 80)
for persona_id, changes in sorted(persona_deltas.items()):
    print(f"\n{persona_id}:")
    for run_name, delta in changes:
        print(f"  {run_name}: {delta:+.4f}")
EOF

python3 analyze_persona_changes.py
```

### Step 7.3: Iterative Improvement Process

**Iteration Loop**:

1. **Run baseline simulation** → Check initial alignment
2. **Run anchoring** → Optimize weights
3. **Analyze results** → Check improvement metrics
4. **Adjust hyperparameters** → Try different settings
5. **Re-run anchoring** → Compare results
6. **Select best config** → Use for prompt workflows
7. **Run prompts** → Test different scenarios
8. **Compare outcomes** → Identify patterns
9. **Refine personas** → Adjust if needed
10. **Repeat** → Iterate for better alignment

### Step 7.4: Best Practices

**For Better Anchoring Results**:

1. **Start with default hyperparameters** (`lambda_reg=0.01`, `alpha=1.0`, `beta=0.5`)
2. **Use relative error** (default) - better for magnitude mismatches
3. **Ensure sufficient data** - At least 8-10 weeks for train/holdout split
4. **Check holdout performance** - Should improve or stay stable
5. **Monitor weight changes** - Should be reasonable (±20% max)
6. **Visual inspection** - Before/after plots should show alignment

**Red Flags**:

- Holdout loss increases >20% → Overfitting, increase regularization
- Weight changes >50% → Unstable, increase regularization
- Global scale >10x → Check if simulated data is correct
- Improvement <50% → Check data alignment, try different hyperparameters

**Success Indicators**:

- ✅ 80-90% loss reduction
- ✅ Holdout loss similar to train loss
- ✅ Mean relative error <15%
- ✅ Visual alignment in plots
- ✅ Stable persona weights

---

## Quick Reference: Common Commands

### Data & Personas
```bash
# Generate data
python3 scripts/generate_synthetic_data.py --config configs/synthetic_config.json --seed 42

# Create personas
python3 scripts/initialize_personas.py --data-version data_2026_01_08_run01 --output PersonaSet_v1.json
```

### Simulation
```bash
# Run baseline
python3 scripts/run_simulation.py --persona-version PersonaSet_v1.json --scenario configs/baseline_scenario.json --num-agents 10000
```

### Anchoring
```bash
# Basic anchoring
python3 scripts/run_anchoring.py --observed-data <obs> --simulated-data <sim> --persona-contributions <contrib> --persona-version PersonaSet_v1.json

# With custom hyperparameters
python3 scripts/run_anchoring.py ... --lambda-reg 0.005 --alpha 2.0 --beta 1.0
```

### Prompts
```bash
# Run prompt workflow
python3 scripts/run_from_prompt.py "Your question here" --enable-anchoring
```

### Visualization
```bash
# Generate all plots
python3 scripts/generate_all_plots.py --run-id <id> --artifacts-dir <dir> --output-dir <plots> --anchoring-dir <anchoring>
```

---

## Troubleshooting

**Problem**: Anchoring shows low improvement (<50%)
- **Solution**: Check data alignment, try lower `lambda_reg`, verify global scaling is working

**Problem**: Holdout loss increases significantly
- **Solution**: Increase `lambda_reg`, check for overfitting, use more training data

**Problem**: Persona weights change too dramatically
- **Solution**: Increase `lambda_reg` to 0.02-0.05, check base weights are reasonable

**Problem**: Global scale is very high (>10x)
- **Solution**: Check simulated data generation, verify number of agents is sufficient

**Problem**: Prompt workflow fails
- **Solution**: Check data version exists, verify PersonaSet path, reduce `--max-agents` if memory issues

---

## Next Steps

1. **Experiment with different persona sets** - Try varying number of personas
2. **Optimize behavioral parameters** - Not just weights, but also sensitivity parameters
3. **Multi-objective optimization** - Balance multiple metrics simultaneously
4. **Time-varying calibration** - Different weights for different time periods
5. **Segment-specific anchoring** - Different calibration for different regions/brands

---

## Summary

This workflow enables you to:
1. ✅ Create diverse personas representing consumer archetypes
2. ✅ Generate synthetic ground truth data
3. ✅ Run simulations and identify misalignment
4. ✅ Calibrate using anchoring with global scaling
5. ✅ Experiment with hyperparameters for optimal results
6. ✅ Run prompt-based scenarios with automatic anchoring
7. ✅ Compare results and iterate for continuous improvement

The key to success is **iterative refinement**: start with defaults, measure results, adjust hyperparameters, and repeat until you achieve desired alignment between simulated and observed metrics.

