# Anchoring Improvements Summary

## Changes Made

### 1. **Relative Error Instead of Absolute Error** (Most Important)
- **Before**: Used absolute squared error `(obs - sim)^2`
- **After**: Uses relative error `((obs - sim) / (obs + epsilon))^2`
- **Impact**: 
  - Small and large values contribute equally to the loss
  - Percentage improvements are more meaningful
  - Better alignment with business metrics
  - Example: 10% error on 100 transactions = 10% error on 10,000 transactions (same weight)

### 2. **Reduced Regularization**
- **Before**: `lambda_reg = 0.1`
- **After**: `lambda_reg = 0.01` (10x reduction)
- **Impact**: Allows larger weight adjustments while still preventing overfitting

### 3. **Increased Optimization Iterations**
- **Before**: `max_iterations = 100`, optimizer uses `max_iterations * 2 = 200`
- **After**: `max_iterations = 500`, optimizer uses `max_iterations * 3 = 1500`
- **Impact**: More iterations allow better convergence

### 4. **Tighter Tolerance**
- **Before**: `ftol = tolerance * 10` (relaxed)
- **After**: `ftol = tolerance` (tighter)
- **Impact**: More precise convergence

## Expected Improvements

With these changes, you should see:
- **10-30% loss reduction** instead of 2%
- **Larger weight adjustments** (±5-15% instead of ±1-2%)
- **Better alignment** between observed and simulated metrics
- **More meaningful improvements** in the before/after plots

## Usage

The improvements are enabled by default. To use absolute error (old behavior):

```python
runner = AnchoringRunner(
    personaset=personaset,
    observed_metrics=observed_metrics,
    simulated_metrics=simulated_metrics,
    persona_contributions=persona_contributions,
    use_relative_error=False  # Use absolute error
)
```

## Next Steps (Optional Further Improvements)

1. **Optimize Behavioral Parameters**: Currently only weights are optimized. Consider optimizing:
   - `price_sensitivity`
   - `promo_sensitivity`
   - `loyalty_decay_rate`

2. **Add Global Scaling Factor**: If simulated is consistently X% off, add a global multiplier:
   ```python
   global_scale = observed.sum() / simulated.sum()
   ```

3. **Multi-Objective Optimization**: Optimize both weights and behavioral parameters simultaneously

4. **Better Initialization**: Use data-driven initial weights instead of uniform

5. **Adaptive Regularization**: Reduce regularization as optimization progresses

