# Large Emotional Model (LEM) - Phase-2 Behavioral Dynamic Engine

## Overview

This repository contains a proof-of-concept implementation demonstrating that modeling consumer behavior as **next-state prediction** (analogous to next-token prediction in language models) improves prediction accuracy, lowers entropy, and produces interpretable behavioral dynamics compared to static or heuristic baselines.

## Key Claim

**Modeling consumer behavior as next-state prediction improves prediction accuracy, lowers entropy, and produces interpretable behavioral dynamics compared to static or heuristic baselines.**

## Repository Structure

```
New_Model_Test/
├── data/                    # Generated synthetic data
│   ├── events.csv          # Consumer action events
│   └── states_hidden.npy   # True latent states (for evaluation)
├── models/                  # Model definitions
│   ├── baselines.py        # Baseline models (Random, Static)
│   ├── lem.py              # Large Emotional Model
│   ├── vocab.json          # Vocabulary mappings
│   └── lem_best.pt         # Trained model checkpoint
├── eval/                    # Evaluation results
│   ├── metrics.json        # Evaluation metrics
│   ├── training_history.json
│   └── conclusion.txt       # Research conclusion
├── plots/                   # Generated visualizations
│   ├── before_vs_after_accuracy.png
│   ├── entropy_comparison.png
│   ├── state_trajectories.png
│   ├── population_state_distribution.png
│   ├── behavioral_regime_shifts.png
│   └── training_history.png
├── notebooks/              # Demo notebook
│   └── demo.ipynb
├── generate_data.py        # Synthetic data generation
├── train.py                # Model training script
├── eval.py                 # Evaluation script
├── visualize.py            # Visualization generation
├── interpretability.py     # Interpretability analysis
├── generate_conclusion.py  # Research conclusion generator
└── README.md
```

## Quick Start

### 1. Generate Synthetic Data

```bash
python generate_data.py
```

This generates:
- `data/events.csv`: 5,000 consumers × 100 timesteps of action events
- `data/states_hidden.npy`: True latent emotional-taste states

### 2. Train the Model

```bash
python train.py
```

This trains the LEM model for 25 epochs, saving the best model to `models/lem_best.pt`.

### 3. Evaluate Models

```bash
python eval.py
```

This evaluates LEM against baselines and saves metrics to `eval/metrics.json`.

### 4. Generate Visualizations

```bash
python visualize.py
```

This generates all required plots in the `plots/` directory.

### 5. Interpretability Analysis

```bash
python interpretability.py
```

This analyzes:
- Which latent dimensions drive indulgent behavior
- How promotions distort emotional states
- Why static models fail to capture fatigue and guilt loops

### 6. Generate Conclusion

```bash
python generate_conclusion.py
```

This generates a research-style conclusion based on results.

## Model Architecture

### Large Emotional Model (LEM)

- **Input**: Previous action (category + brand) + context signals
- **Architecture**: GRU-based sequence model with latent state inference
- **Latent State**: 64-dimensional emotional-taste state vector
- **Output**: Next action prediction (category, brand, spend)

### Loss Function

```
Loss = α * NLL(next action) + β * temporal smoothness + γ * entropy regularization
```

Where:
- `α = 1.0`: Weight for negative log-likelihood
- `β = 0.1`: Weight for temporal smoothness
- `γ = 0.01`: Weight for entropy regularization

## Baselines

1. **Baseline A: Random Predictor**
   - Predicts actions uniformly at random
   - Provides lower bound on performance

2. **Baseline B: Static Preference Model**
   - Uses only initial base traits (sweet_affinity, price_sensitivity, etc.)
   - Ignores temporal evolution
   - Represents traditional static preference models

## Synthetic Data Generation

The synthetic data includes:

- **5,000 consumers** with fixed base traits
- **100 timesteps** per consumer
- **Latent emotional-taste state** (7 dimensions):
  - Craving sweet
  - Craving salty
  - Fatigue
  - Novelty drive
  - Guilt
  - Brand attachment
  - Price alertness

- **Observable actions**:
  - Category: fast_food, healthy_food, dessert, skip
  - Brand: Brand_A, Brand_B, Brand_C
  - Spend: positive real number

- **Context signals**:
  - Time of day: morning, afternoon, evening, night
  - Day type: weekday, weekend
  - Promotion exposure: none, discount, ad
  - Social context: alone, friends, family

- **Ground-truth dynamics**:
  - Indulgent actions increase guilt and fatigue
  - Novelty decays without exploration
  - Repeated brand usage increases attachment
  - Promotions temporarily suppress price sensitivity

## Evaluation Metrics

- **Accuracy**: Exact match (category + brand)
- **Category Accuracy**: Category prediction accuracy
- **Negative Log-Likelihood (NLL)**: Probabilistic prediction quality
- **Predictive Entropy**: Uncertainty measure (lower is better when calibrated)
- **State Recovery**: Correlation between inferred and true latent states

## Results

The model demonstrates:

1. **Higher accuracy** than static baselines
2. **Lower predictive entropy** (more confident, calibrated predictions)
3. **Better NLL** (better probabilistic predictions)
4. **Interpretable latent states** correlated with true emotional-taste states
5. **Behavioral regime recognition** (indulgence → fatigue → restraint)

## Visualizations

All plots are saved in `plots/`:

1. **before_vs_after_accuracy.png**: Accuracy comparison
2. **entropy_comparison.png**: Entropy comparison
3. **state_trajectories.png**: True vs inferred state trajectories
4. **population_state_distribution.png**: State evolution over time
5. **behavioral_regime_shifts.png**: Regime transitions
6. **training_history.png**: Training curves

## Requirements

```
torch>=2.0.0
numpy>=1.24.0
pandas>=2.0.0
matplotlib>=3.7.0
seaborn>=0.12.0
scikit-learn>=1.3.0
tqdm>=4.65.0
```

## Reproducibility

All randomness is seeded (seed=42) for full reproducibility.

## Demo Notebook

See `notebooks/demo.ipynb` for an interactive demonstration.

## Research Conclusion

Run `generate_conclusion.py` to generate a detailed research-style conclusion explaining why next-state prediction outperforms static models.

## Key Insights

1. **Temporal Dynamics Matter**: Consumer behavior exhibits strong temporal dependencies that static models cannot capture.

2. **Latent State Inference**: The model learns meaningful representations of unobserved emotional-taste states.

3. **Behavioral Regimes**: The model identifies and transitions between indulgence, fatigue, and restraint regimes.

4. **Interpretability**: Latent dimensions correlate with specific behaviors (indulgence, fatigue, guilt).

5. **Context Sensitivity**: Promotions and social context create measurable distortions in emotional states.

## Future Directions

1. Scale to larger populations and longer sequences
2. Incorporate additional context signals
3. Extend to multi-modal inputs
4. Develop causal inference capabilities
5. Integrate with real-world recommendation systems

## License

This is a research proof-of-concept implementation.

