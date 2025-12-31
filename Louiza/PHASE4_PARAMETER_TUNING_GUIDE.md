# Phase 4 Parameter Tuning Guide

## Current Accuracy Status

Based on the comparison report, Phase 4 shows **18.8% improvement** over Phase 3, but there's still room for improvement:

- **Product Intent Mean Error**: 0.0287 (target: 0.6381, Phase 4: 0.6094)
- **Category Errors**: Range from 0.0236 to 0.0596
- **Segment Errors**: Range from 0.0163 to 0.0548
- **Daily Trend**: Still not matching (Phase 4: -0.000112, Real: 0.000025)

## Parameters Currently Being Calibrated

These are automatically adjusted by `ParameterCalibrator`:

### 1. **agent_state_init_scale** (Current: ~1.0035)
- **What it does**: Scales initial agent states when they're initialized
- **Impact**: Higher values → agents start with stronger preferences
- **How to tune**: 
  - If Phase 4 intent is too low → increase (try 1.05-1.10)
  - If Phase 4 intent is too high → decrease (try 0.95-0.98)
- **File**: `phase4_anchoring.py` → `ParameterCalibrator._update_parameters()`

### 2. **transition_momentum** (Current: 0.5)
- **What it does**: How much behavioral state persists vs changes
- **Impact**: Higher → more stable preferences, lower → more dynamic
- **How to tune**:
  - If switching rate is too high → increase (try 0.6-0.7)
  - If agents are too static → decrease (try 0.3-0.4)
- **File**: `models_phase2.py` → `StateTransitionModel`

### 3. **intent_noise_scale** (Current: 0.1)
- **What it does**: Random noise added to intent predictions
- **Impact**: Higher → more variance in intent values
- **How to tune**:
  - If intent variance is too low → increase (try 0.15-0.2)
  - If intent is too noisy → decrease (try 0.05-0.08)
- **File**: `models_phase3.py` → `PopulationSimulator.simulate()`

### 4. **switching_rate_multiplier** (Current: 1.0)
- **What it does**: Multiplies the probability of switching products
- **Impact**: Higher → agents switch products more often
- **How to tune**:
  - If switching rate is too low → increase (try 1.1-1.2)
  - If switching rate is too high → decrease (try 0.8-0.9)
- **File**: `models_phase3.py` → `Agent` sampling logic

### 5. **segment_bias_adjustments** (Current: 0.002-0.006 per segment)
- **What it does**: Per-segment adjustments to intent values
- **Impact**: Fine-tunes each segment's baseline intent
- **How to tune**:
  - Check `comparison_report.md` for segment errors
  - Increase adjustment for segments with negative errors
  - Decrease adjustment for segments with positive errors
- **File**: `phase4_anchoring.py` → `ParameterCalibrator._update_parameters()`

## Additional Parameters You Can Tune

### 6. **state_init_noise** (Current: 0.1)
- **What it does**: Noise added during probabilistic state initialization
- **Impact**: Higher → more diversity in initial agent states
- **How to tune**:
  - If agents are too similar → increase (try 0.15-0.2)
  - If agents are too diverse → decrease (try 0.05-0.08)
- **File**: `simulate_phase3.py` line 224, `models_phase3.py` line 325

### 7. **Personality Parameter Ranges**
- **novelty_bias**: Currently uniform(0.0, 1.0)
- **health_focus**: Currently uniform(0.0, 1.0)
- **exploration_rate**: Currently uniform(0.05, 0.2)
- **social_susceptibility**: Currently uniform(0.0, 0.5)
- **How to tune**: Adjust ranges in `simulate_phase3.py` lines 230-234
  - If real data shows more exploration → increase exploration_rate max
  - If real data shows more social influence → increase social_susceptibility max

### 8. **Calibration Learning Rate** (Current: 0.1)
- **What it does**: Step size for parameter updates during calibration
- **Impact**: Higher → faster convergence but may overshoot
- **How to tune**:
  - If calibration oscillates → decrease (try 0.05)
  - If calibration is too slow → increase (try 0.15-0.2)
- **File**: `phase4_main.py` → `run_phase4()` → `calibration_lr` parameter

### 9. **Calibration Iterations** (Current: 10)
- **What it does**: Number of calibration iterations
- **Impact**: More iterations → better convergence but slower
- **How to tune**: Increase to 20-30 for better accuracy
- **File**: `phase4_main.py` → `run_phase4()` → `n_calibration_iterations` parameter

### 10. **Model Fine-Tuning Parameters**
- **Phase 1 Fine-Tuning**: Currently disabled (placeholder)
- **Phase 2 Fine-Tuning**: Currently disabled (placeholder)
- **How to enable**: Implement fine-tuning in `phase4_anchoring.py` → `ModelFineTuner` class
- **Impact**: Can significantly improve accuracy by adapting models to real data

## Recommended Tuning Strategy

### Step 1: Increase Calibration Iterations
```python
# In phase4_main.py, modify:
n_calibration_iterations=20  # instead of 10
calibration_lr=0.08  # slightly lower for stability
```

### Step 2: Tune Based on Error Patterns

**If Product Intent Mean is too low** (current: 0.6094 vs target: 0.6381):
```python
# Increase agent_state_init_scale
agent_state_init_scale: 1.05  # instead of 1.0035
```

**If Category Errors are high** (especially tea: 0.0596 error):
```python
# Add category-specific adjustments in ParameterCalibrator
category_bias_adjustments = {
    'tea': 0.06,  # boost tea intent
    'energy_drink': 0.05,
    # ... etc
}
```

**If Daily Trend is wrong** (Phase 4: -0.000112 vs Real: 0.000025):
```python
# Adjust transition_momentum or add trend correction
transition_momentum: 0.45  # allow more change over time
```

### Step 3: Enable Model Fine-Tuning

Implement fine-tuning in `phase4_anchoring.py`:
```python
# In GroundTruthAnchoring.run_anchoring():
if fine_tune_models:
    print("Fine-tuning Phase 1 models...")
    self.model_fine_tuner.fine_tune_phase1(
        real_data, products_df, contexts_df, segments_df, vocabularies,
        n_epochs=5, batch_size=32
    )
    
    print("Fine-tuning Phase 2 models...")
    self.model_fine_tuner.fine_tune_phase2(
        real_data, products_df, contexts_df, segments_df, vocabularies,
        n_epochs=5, batch_size=8
    )
```

### Step 4: Adjust Simulation Parameters

**If switching rate doesn't match**:
```python
# In simulate_phase3.py, adjust personality ranges:
personality = {
    'exploration_rate': np.random.uniform(0.08, 0.25),  # increased
    # ...
}
```

**If intent variance is wrong**:
```python
# In models_phase3.py, adjust noise:
noise = torch.randn_like(s_0_base) * 0.12  # instead of 0.1
```

## Quick Fixes for Common Issues

### Issue: Overall intent too low
**Fix**: Increase `agent_state_init_scale` to 1.05-1.08

### Issue: Category errors (especially tea, energy_drink)
**Fix**: Add `category_bias_adjustments` to `ParameterCalibrator`

### Issue: Daily trend wrong direction
**Fix**: Decrease `transition_momentum` to 0.4-0.45

### Issue: Switching rate mismatch
**Fix**: Adjust `switching_rate_multiplier` or `exploration_rate` range

### Issue: Segment-level errors
**Fix**: Increase calibration iterations and check `segment_bias_adjustments`

## How to Apply Changes

1. **Edit calibration parameters**: Modify `phase4_anchoring.py` → `ParameterCalibrator._update_parameters()`
2. **Edit simulation parameters**: Modify `simulate_phase3.py` → `run_simulation()`
3. **Edit calibration settings**: Modify `phase4_main.py` → `run_phase4()`
4. **Re-run Phase 4**: `python main.py --mode phase4 --real_data_path data/real_intent_data.csv`
5. **Check results**: View `phase4_output/comparison_report.md` for improvements

## Expected Improvements

With proper tuning, you should see:
- **Product Intent Mean Error**: < 0.02 (currently 0.0287)
- **Category Errors**: < 0.03 for all categories (currently up to 0.0596)
- **Segment Errors**: < 0.03 for all segments (currently up to 0.0548)
- **Daily Trend Error**: < 0.00005 (currently 0.000137)

## Monitoring Progress

After each tuning iteration:
1. Check `phase4_output/comparison_report.md` for error metrics
2. View `phase4_output/visualizations/intent_distribution.png` for visual comparison
3. Compare `phase4_output/calibrated_params.json` to see parameter changes
4. Look for convergence in `phase4_output/visualizations/convergence_path.png`

