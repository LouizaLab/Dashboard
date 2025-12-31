# Multi-Phase Behavioral Intent Modeling System

A comprehensive system for modeling behavioral intent and preferences across four phases: Taste Embedding, Behavioral Dynamics, Large Population Simulation, and Ground Truth Anchoring.

## Overview

This system models how user intent evolves over time by:
1. **Phase 1**: Creating embeddings for products, contexts, and segments
2. **Phase 2**: Modeling behavioral state transitions over time
3. **Phase 3**: Scaling to large populations with dynamic features
4. **Phase 4**: Anchoring to real data and generating hedge-fund-ready signals

## Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Phase 1: Taste Embedding Model](#phase-1-taste-embedding-model-tem)
- [Phase 2: Behavioral Dynamic Engine](#phase-2-behavioral-dynamic-engine)
- [Phase 3: Large Population Model](#phase-3-large-population-model-lpm)
- [Phase 4: Ground Truth Anchoring + Signals](#phase-4-ground-truth-anchoring--signals)
- [How Anchoring Works](#how-ground-truth-anchoring-works)
- [Visualizations](#visualizations)
- [Project Structure](#project-structure)
- [Output Files](#output-files)
- [Architecture Details](#architecture-details)

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Investor Demo Dashboard

Launch the interactive Streamlit dashboard:

```bash
# Install dependencies (if not already installed)
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

The dashboard will open in your browser at `http://localhost:8501` and includes:
- **Taste Snapshot**: Baseline preference profiles by segment
- **Behavioral Dynamics**: Time series of purchase probability, repeat rate, churn, adoption
- **Auto-Generated Insights**: 5-10 insight cards with evidence charts
- **What-If Simulation**: Counterfactual scenarios with price, sugar, and marketing adjustments

### Run All Phases

```bash
# Generate data, train models, simulate, and generate signals
python main.py --mode all_phases --n_products 50 --n_logs 1000 --n_epochs 50 --phase2_n_epochs 30 --n_agents 10 --sim_days 30
```

### Step-by-Step

```bash
# 1. Generate synthetic data
python main.py --mode generate_data --n_products 50 --n_logs 1000

# 2. Train Phase 1 models
python main.py --mode train --n_epochs 50

# 3. Visualize Phase 1 embeddings
python main.py --mode visualize

# 4. Train Phase 2 models
python main.py --mode train_phase2 --phase2_n_epochs 30

# 5. Run Phase 3 simulation
python main.py --mode simulate_phase3 --n_agents 10 --sim_days 30

# 6. Run Phase 4 (calibration + signals)
python main.py --mode phase4 --real_data_path data/real_intent_data.csv
```

### Using Shell Script

```bash
./run_full_pipeline.sh
```

## Phase 1: Taste Embedding Model (TEM)

Creates embeddings that encode product characteristics, context, and user segments into dense vector representations.

### Components

1. **Product Embeddings (z_product)**: 128D vectors encoding:
   - Ingredients (max 10)
   - Sensory tags (max 8)
   - Nutrition (sugar, caffeine, calories, protein)
   - Text descriptions (LSTM encoder)

2. **Context Embeddings (z_context)**: 64D vectors encoding:
   - Time of day
   - Location
   - Occasion
   - Price

3. **Segment Embeddings (z_segment)**: 64D vectors encoding:
   - Age bucket
   - Region
   - Psychographics

### Architecture

- **ProductEmbeddingModel**: Multi-modal fusion (ingredients, tags, nutrition, text) → 128D
- **ContextEmbeddingModel**: Categorical embeddings + price projection → 64D
- **SegmentEmbeddingModel**: Categorical embeddings → 64D
- **CombinedEmbeddingModel**: Combines all three embeddings
- **PreferencePredictor**: Predicts intent from combined embeddings

### Training

Models are trained end-to-end using preference prediction:
- Input: (product, context, segment)
- Output: Predicted preference value (0-1)
- Loss: MSE between predicted and actual preferences
- All embeddings are L2 normalized

### Usage

```bash
# Generate data
python main.py --mode generate_data

# Train models
python main.py --mode train --n_epochs 50 --batch_size 32

# Visualize embeddings
python main.py --mode visualize
```

### Outputs

- Model checkpoints: `checkpoints/best_model.pt`
- Visualizations: `visualizations/`
  - PCA/t-SNE plots of embeddings
  - Similarity matrices
  - Training curves

## Phase 2: Behavioral Dynamic Engine

Models how behavioral intent evolves over time using a latent state representation.

### Components

1. **BehavioralState (s_t)**: 128D latent state with components:
   - z_taste: Stable taste preferences (from segment)
   - z_novelty: Novelty vs routine preference
   - z_habit: Habit strength / inertia
   - z_health: Health vs indulgence bias
   - z_price: Price sensitivity

2. **ObservationModel**: P(like | s_t, z_product, z_context)
   - Predicts intent from current state + product + context

3. **StateTransitionModel**: s_{t+1} = f(s_t, z_product, z_context, y_t)
   - Updates state based on interaction outcome
   - Uses GRU to model temporal dynamics

4. **BehavioralDynamicEngine**: Complete system combining all components

### Architecture

- State initialized from segment embedding
- GRU-based transition model
- MLP observation model
- Sequence-level training

### Usage

```bash
# Train Phase 2
python main.py --mode train_phase2 --sequence_length 10 --phase2_n_epochs 30
```

### Outputs

- Model checkpoints: `checkpoints_phase2/best_model_phase2.pt`

## Phase 3: Large Population Model (LPM)

Scales Phase 2 to simulate large populations of agents with dynamic features.

### Components

1. **Agent**: Represents a user with:
   - Segment assignment
   - Behavioral state (s_t)
   - Personality parameters (novelty bias, health focus, exploration rate, social susceptibility)

2. **Environment**: Manages:
   - Product catalog (with dynamic launches)
   - Context pool
   - Price dynamics (inflation-based)
   - Macro context (season, inflation regime)

3. **PopulationSimulator**: Orchestrates simulation:
   - Agent initialization
   - Product/context sampling
   - Intent computation
   - State updates
   - Result aggregation

### Advanced Features

1. **Probabilistic State Initialization**: s_0 ~ p(s_0 | segment) with noise
2. **Dynamic Product Shelf**: New products launch over time
3. **Dynamic Price Levels**: Prices change based on inflation regime
4. **Macro Context**: Season and inflation regime tracking
5. **Social Influence**: Neighbors' choices affect agent behavior

### Usage

```bash
# Basic simulation
python main.py --mode simulate_phase3 --n_agents 10 --sim_days 30

# Larger simulation
python main.py --mode simulate_phase3 --n_agents 100 --sim_days 30 --interactions_per_day 3
```

### Outputs

- Intent trajectories: `simulations/intent_trajectories.csv`
- Simulation stats: `simulations/simulation_stats.json`

## Phase 4: Ground Truth Anchoring + Signals

Calibrates simulation to real data and generates hedge-fund-ready demand signals.

### Components

1. **Calibration System** (`phase4_calibration.py`):
   - Compares simulated vs real intent distributions
   - Analyzes product, segment, and category patterns
   - Computes time-series trends and switching rates

2. **Anchoring System** (`phase4_anchoring.py`):
   - Parameter calibration to match real data
   - Model fine-tuning framework
   - Iterative improvement loop

3. **Signal Generation** (`phase4_signals.py`):
   - Intent Index: Category-level intent over time
   - Momentum Index: 7-day and 30-day momentum
   - Trend Acceleration: Second derivative of trends
   - Demand Forecasts: 30-day and 90-day forecasts
   - Substitution Matrix: Share shifts between categories
   - Price Elasticity: Price sensitivity estimates

### Signals Generated

- **Intent Index**: I_c(t) = E[ŷ_t | category = c]
- **Category Momentum**: 7d and 30d momentum (Δ in I_c(t))
- **Trend Acceleration**: Second derivative of intent trends
- **Demand Forecasts**: Forward-looking 30d and 90d forecasts
- **Substitution Matrix**: Correlation-based substitution patterns
- **Price Elasticity**: Price sensitivity per category

### Usage

```bash
# Generate all signals
python main.py --mode phase4

# With real data for calibration
python main.py --mode phase4 --real_data_path data/real_intent_data.csv

# Standalone
python phase4_main.py --simulation_data simulations/intent_trajectories.csv
```

### Outputs

All signals saved to `phase4_output/signals/`:
- `intent_index.csv` - Category intent over time
- `momentum_7d.csv` - 7-day momentum
- `momentum_30d.csv` - 30-day momentum
- `trend_acceleration.csv` - Trend acceleration
- `forecast_30d.csv` - 30-day forecasts
- `forecast_90d.csv` - 90-day forecasts
- `substitution_matrix.csv` - Substitution pairs
- `price_elasticity.csv` - Price sensitivity
- `signals_summary.json` - Summary metadata

## How Ground Truth Anchoring Works

Phase 4 anchors the simulation to real data through **iterative parameter calibration**.

### The Process

1. **Extract Target Metrics** from real data:
   - Product intent mean, switching rate, segment/category patterns, trends

2. **Run Simulation** with current parameters:
   - Generate simulated intent trajectories

3. **Compute Simulated Metrics**:
   - Extract same metrics from simulation

4. **Compare and Adjust**:
   - Compute difference between sim and real metrics
   - Adjust parameters to reduce gap:
     - `agent_state_init_scale`: Agent optimism level
     - `switching_rate_multiplier`: Product switching frequency
     - `segment_bias_adjustments`: Per-segment corrections

5. **Iterate Until Convergence**:
   - Repeat until simulation matches real data patterns

### Parameters Calibrated

- **Agent State Initialization Scale**: How optimistic agents start
- **Transition Momentum**: How much state persists over time
- **Switching Rate Multiplier**: How often agents switch products
- **Segment Bias Adjustments**: Per-segment corrections

### Why Phase 4 is Better

1. **Grounded in Reality**: Calibrated to real ground truth data
2. **Parameter Calibration**: Parameters adjusted to match real patterns
3. **Error Reduction**: Errors minimized through calibration
4. **Better Outcomes**: More accurate predictions closer to reality

**Demonstrated Improvement**: 18.8% reduction in error from Phase 3 to Phase 4.

## Visualizations

Phase 4 generates comprehensive visualizations showing improvement from Phase 3 to Phase 4.

### Static PNG Visualizations

- **`intent_distribution.png`**: Distribution comparisons (overall, category, segment, time series)
- **`metrics_comparison.png`**: Key metrics side-by-side with improvement indicators
- **`category_comparison.png`**: Category-level detailed comparison
- **`convergence_path.png`**: Visual convergence journey from Phase 3 → Phase 4

### Interactive HTML Dashboard

- **`anchoring_dashboard.html`**: Interactive Plotly dashboard
  - 6 panels showing different aspects of improvement
  - Hover for detailed values
  - Zoom and explore data
  - **Best for presentations**

### Summary Report

- **`improvement_summary.md`**: Comprehensive markdown report with metrics and analysis

### Color Coding

- 🔵 **Blue** = Phase 3 (Initial Approximation)
- 🟢 **Green** = Real Data (Ground Truth Target)
- 🔴 **Red** = Phase 4 (Ground Truth Anchored)

### Generating Visualizations

```bash
# Automatically generated with Phase 4
python main.py --mode phase4

# Standalone
python visualize_anchoring.py
```

## Project Structure

```
Louiza/
├── Core Implementation
│   ├── data_generator.py          # Synthetic data generation
│   ├── data_utils.py               # Phase 1 data utilities
│   ├── data_phase2.py              # Phase 2 data utilities
│   ├── models.py                   # Phase 1 model architectures
│   ├── models_phase2.py            # Phase 2 model architectures
│   ├── models_phase3.py            # Phase 3 simulation models
│   ├── train_phase1.py             # Phase 1 training
│   ├── train_phase2.py             # Phase 2 training
│   ├── simulate_phase3.py          # Phase 3 simulation
│   ├── phase4_main.py              # Phase 4 main script
│   ├── phase4_calibration.py       # Calibration system
│   ├── phase4_anchoring.py         # Anchoring system
│   ├── phase4_signals.py           # Signal generation
│   ├── visualize.py                # Phase 1 visualizations
│   ├── visualize_anchoring.py     # Phase 4 visualizations
│   ├── create_summary_report.py   # Summary report generation
│   └── main.py                     # Main entry point
├── Configuration
│   ├── requirements.txt            # Python dependencies
│   └── run_full_pipeline.sh       # Full pipeline script
├── Data (generated)
│   └── data/                       # CSV files
├── Checkpoints
│   ├── checkpoints/                # Phase 1 models
│   └── checkpoints_phase2/         # Phase 2 models
└── Outputs
    ├── visualizations/             # Phase 1 visualizations
    ├── simulations/                # Phase 3 results
    └── phase4_output/              # Phase 4 outputs
        ├── signals/                # Generated signals
        └── visualizations/         # Phase 4 visualizations
```

## Output Files

### Phase 1 Outputs

- **Data**: `data/products.csv`, `data/segments.csv`, `data/contexts.csv`, `data/intent_logs.csv`
- **Models**: `checkpoints/best_model.pt`, `checkpoints/final_model.pt`
- **Visualizations**: `visualizations/product_embeddings_*.html`, `product_similarity_matrix.png`

### Phase 2 Outputs

- **Models**: `checkpoints_phase2/best_model_phase2.pt`

### Phase 3 Outputs

- **Trajectories**: `simulations/intent_trajectories.csv`
- **Stats**: `simulations/simulation_stats.json`

### Phase 4 Outputs

- **Signals**: `phase4_output/signals/*.csv` and `signals_summary.json`
- **Calibration**: `phase4_output/calibration_report.txt`, `calibration_metrics.json`, `target_metrics.json`
- **Visualizations**: `phase4_output/visualizations/*.png` and `anchoring_dashboard.html`
- **Summary**: `phase4_output/improvement_summary.md`

## Architecture Details

### Phase 1 Models

**ProductEmbeddingModel**:
- Ingredient embeddings (vocab size ~100)
- Tag embeddings (vocab size ~50)
- Nutrition MLP (4 → 32)
- Text LSTM (vocab size ~1000, hidden 64)
- Fusion MLP (all → 128)

**ContextEmbeddingModel**:
- Time-of-day embedding (vocab size ~4)
- Location embedding (vocab size ~10)
- Occasion embedding (vocab size ~8)
- Price MLP (1 → 16)
- Fusion MLP (all → 64)

**SegmentEmbeddingModel**:
- Age bucket embedding (vocab size ~5)
- Region embedding (vocab size ~10)
- Psychographic embedding (vocab size ~5)
- Fusion MLP (all → 64)

### Phase 2 Models

**BehavioralState**:
- Projects segment embedding to state components
- State dimension: 128
- Components: taste, novelty, habit, health, price

**ObservationModel**:
- MLP: (state_dim + product_dim + context_dim) → 1
- Outputs intent probability

**StateTransitionModel**:
- GRU: (state_dim + product_dim + context_dim) → state_dim
- Updates state based on interaction

### Phase 3 Models

**Agent**:
- Segment ID and embedding
- Current behavioral state (s_t)
- Personality parameters
- Interaction history

**Environment**:
- Product catalog with dynamic launches
- Context pool
- Price dynamics
- Macro context (season, inflation)

**PopulationSimulator**:
- Manages agent population
- Runs simulation loop
- Tracks results

### Phase 4 Components

**ParameterCalibrator**:
- Computes target metrics from real data
- Compares simulated vs real metrics
- Adjusts parameters iteratively

**ModelFineTuner**:
- Fine-tunes Phase 1 & Phase 2 models
- Uses real intent data
- Updates embeddings and transitions

**SignalGenerator**:
- Computes intent indices
- Calculates momentum and acceleration
- Generates forecasts
- Computes substitution patterns
- Estimates price elasticity

## Key Concepts

### Embeddings

All embeddings are **L2 normalized** for consistent similarity computation. Products in the same category should cluster together in embedding space.

### Behavioral State

The latent state `s_t` represents:
- **Stable preferences** (from segment)
- **Dynamic factors** (novelty, habit, health, price sensitivity)
- **Temporal evolution** (updated based on interactions)

### Ground Truth Anchoring

The process of calibrating simulation parameters to match real-world data patterns:
1. Extract patterns from real data
2. Run simulation with current parameters
3. Compare simulated vs real patterns
4. Adjust parameters to reduce difference
5. Iterate until convergence

### Signals

Hedge-fund-ready signals include:
- **Momentum**: Short-term trend indicators
- **Forecasts**: Forward-looking predictions
- **Substitution**: Category switching patterns
- **Elasticity**: Price sensitivity estimates

## Validation

The system has been validated to show:
- ✅ Phase 4 reduces error by **18.8%** compared to Phase 3
- ✅ All 7 categories show improvement after anchoring
- ✅ Parameters successfully calibrated to match real data
- ✅ Visualizations demonstrate clear convergence

## Notes

- Synthetic data is generated with realistic relationships (e.g., health-focused segments prefer low-sugar products)
- Models learn to cluster similar products in embedding space
- All embeddings are L2 normalized for consistent similarity computation
- Phase 3 includes advanced features: dynamic prices, new launches, macro context, social influence
- Phase 4 visualizations clearly show improvement from Phase 3 to Phase 4

## Quick Reference

### Common Commands

```bash
# Full pipeline
python main.py --mode all_phases --n_agents 10 --sim_days 30

# Phase 1 only
python main.py --mode all

# Phase 3 + Phase 4
python main.py --mode simulate_phase3 --n_agents 10 --sim_days 30 && \
python main.py --mode phase4

# With real data
python main.py --mode phase4 --real_data_path data/real_intent_data.csv
```

### Output Locations

- Phase 1: `checkpoints/`, `visualizations/`
- Phase 2: `checkpoints_phase2/`
- Phase 3: `simulations/`
- Phase 4: `phase4_output/`

## License

[Add your license here]

## Contact

[Add contact information here]
