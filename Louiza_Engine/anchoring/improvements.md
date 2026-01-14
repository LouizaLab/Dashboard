# Anchoring Improvement Recommendations

## Current Issues

1. **Low improvement (~2%)**: Only 2% loss reduction suggests optimization is constrained
2. **Small weight changes**: Weight deltas are only ±1-2%, indicating regularization is too strong
3. **Absolute error**: Using squared error on absolute values means large values dominate

## Recommended Improvements

### 1. Use Relative/Percentage Error (Most Important)

Instead of absolute squared error, use relative error normalized by observed values:

```python
# Current (absolute):
transaction_error = (observed - simulated) ** 2

# Improved (relative):
transaction_error = ((observed - simulated) / (observed + epsilon)) ** 2
# or percentage error:
transaction_error = ((observed - simulated) / observed) ** 2
```

This ensures:
- Small and large values contribute equally
- Percentage improvements are more meaningful
- Better alignment with business metrics

### 2. Reduce Regularization Strength

Current: `lambda_reg = 0.1`
Recommended: `lambda_reg = 0.01` or `0.001`

This allows larger weight adjustments while still preventing overfitting.

### 3. Increase Optimization Iterations

Current: `max_iterations = 100`
Recommended: `max_iterations = 500` or `1000`

### 4. Optimize Behavioral Parameters

Currently only weights are optimized. Consider optimizing:
- `price_sensitivity`
- `promo_sensitivity`
- `loyalty_decay_rate`
- `attention_decay_rate`

### 5. Add Systematic Bias Correction

If simulated is consistently X% higher/lower than observed, add a global scaling factor:

```python
global_scale = observed.sum() / simulated.sum()
scaled_metrics = simulated * global_scale
```

### 6. Use Normalized Loss

Normalize loss by the magnitude of observed values:

```python
normalized_loss = loss / (observed.sum() ** 2)
```

### 7. Check Data Alignment

Ensure:
- Same time periods
- Same brands/regions
- Same aggregation level
- No missing data causing misalignment

