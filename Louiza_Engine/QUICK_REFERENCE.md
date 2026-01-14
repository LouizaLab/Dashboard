# Louiza Engine Quick Reference

## 🚀 Quick Start (5 Steps)

```bash
# 1. Generate data
python3 scripts/generate_synthetic_data.py --config configs/synthetic_config.json --seed 42

# 2. Create personas
python3 scripts/initialize_personas.py --data-version data_2026_01_08_run01 --output PersonaSet_v1.json

# 3. Run baseline simulation
python3 scripts/run_simulation.py --persona-version PersonaSet_v1.json --scenario configs/baseline_scenario.json --num-agents 10000 --output-dir runs/baseline/

# 4. Anchor to ground truth
python3 scripts/run_anchoring.py \
    --observed-data data/synthetic/data_2026_01_08_run01/observed_metrics_brand_week_region.csv \
    --simulated-data runs/baseline/simulated_metrics_brand_week_region.csv \
    --persona-contributions runs/baseline/persona_contributions.csv \
    --persona-version PersonaSet_v1.json \
    --output-dir runs/anchored/

# 5. Run prompt workflow
python3 scripts/run_from_prompt.py "What happens if we launch a promo campaign?" --enable-anchoring
```

## 📊 Anchoring Hyperparameters

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `--lambda-reg` | 0.01 | 0.001-0.1 | Lower = larger adjustments, Higher = more stable |
| `--alpha` | 1.0 | 0.1-10.0 | Weight for transactions error |
| `--beta` | 0.5 | 0.1-10.0 | Weight for revenue error |
| `--use-relative-error` | True | True/False | Normalize by observed values (recommended) |

## 🎯 Common Scenarios

### Test Different Regularization
```bash
for reg in 0.001 0.01 0.05; do
    python3 scripts/run_anchoring.py ... --lambda-reg $reg --output-dir runs/anchored_reg_$reg/
done
```

### Prioritize Transactions vs Revenue
```bash
# Transactions priority
python3 scripts/run_anchoring.py ... --alpha 2.0 --beta 0.5

# Revenue priority  
python3 scripts/run_anchoring.py ... --alpha 1.0 --beta 2.0
```

### Custom Train/Holdout Split
```bash
python3 scripts/run_anchoring.py ... \
    --train-weeks 1,2,3,4,5,6,7,8 \
    --holdout-weeks 9,10,11,12
```

## 📈 Success Metrics

- **Loss Reduction**: 80-90% (good), 50-80% (acceptable), <50% (needs tuning)
- **Mean Relative Error**: <15% (excellent), 15-25% (good), >25% (needs work)
- **Holdout Loss**: Should be similar to train loss (within 20%)
- **Global Scale**: 1-5x (normal), >10x (check data)

## 🔍 Check Results

```bash
# View anchoring report
cat runs/anchored/anchoring_report.json | python3 -m json.tool

# Compare multiple runs
for dir in runs/anchored_*/; do
    echo "$dir:"
    cat $dir/anchoring_report.json | python3 -c "import json,sys; r=json.load(sys.stdin); print(f\"Improvement: {r['improvement']['train_loss_reduction']:.1f}%\")"
done
```

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| Low improvement (<50%) | Lower `--lambda-reg`, check data alignment |
| Holdout loss increases | Increase `--lambda-reg`, check overfitting |
| Extreme weight changes | Increase `--lambda-reg` to 0.02-0.05 |
| High global scale (>10x) | Check simulated data, verify agent count |

## 📚 Full Documentation

See `COMPLETE_WORKFLOW_GUIDE.md` for:
- Detailed step-by-step instructions
- Hyperparameter tuning strategies
- Iterative improvement process
- Best practices and red flags

