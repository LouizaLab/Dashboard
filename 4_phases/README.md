# 4-Phase Intent Modeling Pipeline

A complete end-to-end pipeline for modeling consumer intent and generating actionable signals for hedge funds and investment analysis.

## Overview

This pipeline consists of four sequential phases that transform raw product/context/segment data into calibrated intent predictions and investment signals:

1. **Phase 1: Taste Embedding Model (TEM)** - Creates embeddings for products, contexts, and user segments
2. **Phase 2: Behavioral Dynamic Engine** - Models how intent evolves over time using latent state
3. **Phase 3: Large Population Simulation** - Scales to simulate large populations of agents
4. **Phase 4: Ground Truth Anchoring & Signals** - Calibrates models to real data and generates investment signals

## Directory Structure

```
4_phases/
├── phase1/              # Phase 1: Taste Embedding Model
│   ├── models.py        # Model architectures (Product, Context, Segment embeddings)
│   ├── train_phase1.py  # Training script
│   └── data_utils.py    # Data preprocessing utilities
├── phase2/              # Phase 2: Behavioral Dynamic Engine
│   ├── models_phase2.py # Behavioral state and transition models
│   ├── train_phase2.py  # Training script
│   └── data_phase2.py   # Sequence dataset utilities
├── phase3/              # Phase 3: Large Population Simulation
│   ├── models_phase3.py # Agent, Environment, PopulationSimulator
│   └── simulate_phase3.py # Main simulation script
├── phase4/              # Phase 4: Anchoring & Signals
│   ├── phase4_main.py   # Main Phase 4 script
│   ├── phase4_calibration.py # Calibration utilities
│   ├── phase4_signals.py    # Signal generation
│   ├── phase4_anchoring.py  # Ground truth anchoring
│   ├── phase4_sales_validation.py # Sales validation
│   └── phase4_dashboard.py  # Dashboard interface
├── data_generation/     # Synthetic data generation
│   ├── data_generator.py     # Main data generator
│   └── generate_sales_data.py # Sales data generation
├── visualizations/      # Visualization utilities
│   ├── visualize.py           # Phase 1 embeddings visualization
│   ├── visualize_anchoring.py # Phase 4 anchoring visualization
│   ├── visualize_improvement.py # Improvement visualization
│   ├── create_comparison_report.py # Comparison reports
│   └── create_summary_report.py   # Summary reports
├── main.py              # Main entry point
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Installation

1. **Install dependencies:**
```bash
cd 4_phases
pip install -r requirements.txt
```

2. **Verify installation:**
```bash
python -c "import torch; import pandas; import numpy; print('Dependencies OK')"
```

## Quick Start

### Run All Phases (End-to-End)

```bash
python main.py --mode all_phases \
    --n_products 50 \
    --n_logs 1000 \
    --n_epochs 50 \
    --phase2_n_epochs 30 \
    --n_agents 10 \
    --sim_days 30
```

### Step-by-Step Execution

#### Step 1: Generate Synthetic Data
```bash
python main.py --mode generate_data \
    --n_products 50 \
    --n_segments 5 \
    --n_contexts 100 \
    --n_logs 1000 \
    --data_dir data
```

**Output:** `data/products.csv`, `data/segments.csv`, `data/contexts.csv`, `data/intent_logs.csv`

#### Step 2: Train Phase 1 Models
```bash
python main.py --mode train \
    --data_dir data \
    --checkpoint_dir checkpoints \
    --batch_size 32 \
    --learning_rate 0.001 \
    --n_epochs 50
```

**Output:** `checkpoints/best_model.pt` (contains all Phase 1 models)

#### Step 3: Visualize Phase 1 Embeddings
```bash
python main.py --mode visualize \
    --checkpoint_dir checkpoints \
    --data_dir data \
    --viz_dir visualizations
```

**Output:** Embedding visualizations in `visualizations/`

#### Step 4: Train Phase 2 Models
```bash
python main.py --mode train_phase2 \
    --phase1_checkpoint checkpoints/best_model.pt \
    --data_dir data \
    --sequence_length 10 \
    --phase2_n_epochs 30 \
    --batch_size 8
```

**Output:** `checkpoints_phase2/best_model_phase2.pt`

#### Step 5: Run Phase 3 Simulation
```bash
python main.py --mode simulate_phase3 \
    --n_agents 10 \
    --sim_days 30 \
    --interactions_per_day 1 \
    --phase1_checkpoint checkpoints/best_model.pt \
    --phase2_checkpoint checkpoints_phase2/best_model_phase2.pt \
    --data_dir data \
    --sim_output_dir simulations
```

**Output:** `simulations/intent_trajectories.csv`, `simulations/simulation_stats.json`

#### Step 6: Run Phase 4 (Calibration & Signals)
```bash
python main.py --mode phase4 \
    --simulation_data simulations/intent_trajectories.csv \
    --real_data_path data/real_intent_data.csv \
    --output_dir phase4_output
```

**Output:** 
- `phase4_output/calibration_report.txt`
- `phase4_output/signals/` (all generated signals)
- `phase4_output/visualizations/` (calibration visualizations)

## Phase Details

### Phase 1: Taste Embedding Model (TEM)

**Purpose:** Learn dense vector representations (embeddings) for products, contexts, and user segments.

**Architecture:**
- **ProductEmbeddingModel**: Encodes product features (ingredients, tags, nutrition, description) → 128D vector
- **ContextEmbeddingModel**: Encodes context (time, location, occasion, price) → 64D vector
- **SegmentEmbeddingModel**: Encodes user segment (age, region, psychographic) → 64D vector
- **PreferencePredictor**: Predicts preference from combined embeddings

**Training:** End-to-end training using preference prediction task (MSE loss)

**Key Files:**
- `phase1/models.py`: Model architectures
- `phase1/train_phase1.py`: Training script
- `phase1/data_utils.py`: Data preprocessing

### Phase 2: Behavioral Dynamic Engine

**Purpose:** Model how behavioral intent evolves over time using latent state representation.

**Architecture:**
- **BehavioralState**: 128D latent state with components (taste, novelty, habit, health, price)
- **ObservationModel**: P(like | s_t, z_product, z_context)
- **StateTransitionModel**: s_{t+1} = f(s_t, z_product, z_context, y_t) using GRU
- **BehavioralDynamicEngine**: Complete system combining all components

**Training:** Sequence-level training on intent logs (MSE loss on sequences)

**Key Files:**
- `phase2/models_phase2.py`: Model architectures
- `phase2/train_phase2.py`: Training script
- `phase2/data_phase2.py`: Sequence dataset

### Phase 3: Large Population Simulation

**Purpose:** Scale Phase 2 to simulate large populations of agents with dynamic features.

**Components:**
- **Agent**: Represents a user with segment, behavioral state, and personality parameters
- **Environment**: Manages product catalog, contexts, price dynamics, macro context
- **PopulationSimulator**: Orchestrates simulation with social influence, new product launches, etc.

**Features:**
- Dynamic pricing (inflation-based)
- New product launches
- Macro context (season, inflation regime)
- Social influence
- Probabilistic state initialization

**Key Files:**
- `phase3/models_phase3.py`: Agent, Environment, PopulationSimulator
- `phase3/simulate_phase3.py`: Main simulation script

### Phase 4: Ground Truth Anchoring & Signals

**Purpose:** Calibrate models to real data and generate investment-ready signals.

**Components:**
- **IntentDataCalibrator**: Compares simulated vs real intent distributions
- **GroundTruthAnchoring**: Fine-tunes models on real data
- **SignalGenerator**: Generates investment signals:
  - Intent Index: I_c(t) = E[ŷ_t | category = c]
  - Momentum 7d/30d: Change in intent over time windows
  - Trend Acceleration: Second derivative of intent
  - Forecasts: 30d and 90d demand forecasts
  - Substitution Matrix: Product switching patterns
  - Price Elasticity: Sensitivity to price changes

**Key Files:**
- `phase4/phase4_main.py`: Main Phase 4 script
- `phase4/phase4_calibration.py`: Calibration utilities
- `phase4/phase4_signals.py`: Signal generation
- `phase4/phase4_anchoring.py`: Anchoring framework

## Adapting for Your Real Data

### Data Format Requirements

To use your real data, ensure it follows these schemas:

#### Products (`data/products.csv`)
Required columns:
- `product_id`: Unique product identifier
- `category`: Product category
- `ingredients`: Comma-separated list of ingredients
- `sensory_tags`: Comma-separated sensory tags
- `sugar_g`: Sugar in grams
- `caffeine_mg`: Caffeine in mg
- `calories`: Calories
- `protein_g`: Protein in grams
- `description`: Text description
- `price`: Product price

#### Contexts (`data/contexts.csv`)
Required columns:
- `context_id`: Unique context identifier
- `time_of_day`: One of ['morning', 'afternoon', 'evening', 'late_night']
- `hour`: Hour of day (0-23)
- `location`: Location type
- `occasion`: Occasion type
- `price_shown`: Price shown to user

#### Segments (`data/segments.csv`)
Required columns:
- `segment_id`: Unique segment identifier
- `age_bucket`: Age bucket (e.g., '18-25', '26-35', etc.)
- `region`: Geographic region
- `psychographic`: Psychographic profile

#### Intent Logs (`data/intent_logs.csv`)
Required columns:
- `log_id`: Unique log identifier
- `timestamp`: Timestamp (YYYY-MM-DD HH:MM:SS)
- `product_id`: Product ID (must match products.csv)
- `segment_id`: Segment ID (must match segments.csv)
- `context_id`: Context ID (must match contexts.csv)
- `preference_value`: Preference/intent value (0-1 scale)
- `rating`: Optional rating (1-5 scale)
- `liked`: Optional binary like indicator

#### Real Intent Data (`data/real_intent_data.csv`)
For Phase 4 calibration, provide real-world intent data with:
- `timestamp` or `date`: Time information
- `product_id` or `product_category`: Product information
- `intent_value`: Intent/preference value
- `segment_id`: Optional segment information

### Step-by-Step Adaptation Guide

#### 1. Prepare Your Data

```python
# Example: Convert your data to required format
import pandas as pd

# Load your products
your_products = pd.read_csv('your_products.csv')

# Map to required schema
products = pd.DataFrame({
    'product_id': your_products['id'],
    'category': your_products['category'],
    'ingredients': your_products['ingredients'].str.join(','),
    'sensory_tags': your_products['tags'].str.join(','),
    'sugar_g': your_products['sugar'],
    'caffeine_mg': your_products['caffeine'],
    'calories': your_products['calories'],
    'protein_g': your_products['protein'],
    'description': your_products['description'],
    'price': your_products['price']
})

products.to_csv('data/products.csv', index=False)
```

#### 2. Update Vocabulary Building

If your data has different ingredient/tag vocabularies, the vocabulary building in `phase1/data_utils.py` will automatically adapt. However, you may need to adjust:

- **Ingredient vocabulary**: Ensure ingredients are comma-separated
- **Tag vocabulary**: Ensure tags are comma-separated
- **Text vocabulary**: Description text will be tokenized automatically

#### 3. Adjust Model Dimensions (if needed)

If your data has significantly different characteristics, you may need to adjust model dimensions in `phase1/models.py`:

```python
# In ProductEmbeddingModel.__init__
product_model = ProductEmbeddingModel(
    vocab_size=max(ingredient_vocab_size, tag_vocab_size, text_vocab_size),
    embedding_dim=64,      # Can adjust
    hidden_dim=128,         # Can adjust
    output_dim=128          # Can adjust
)
```

#### 4. Train with Your Data

```bash
# Step 1: Place your data files in data/
# - data/products.csv
# - data/segments.csv
# - data/contexts.csv
# - data/intent_logs.csv

# Step 2: Train Phase 1
python main.py --mode train \
    --data_dir data \
    --n_epochs 50

# Step 3: Train Phase 2
python main.py --mode train_phase2 \
    --phase1_checkpoint checkpoints/best_model.pt

# Step 4: Run simulation
python main.py --mode simulate_phase3 \
    --n_agents 100 \
    --sim_days 90

# Step 5: Calibrate with real data
python main.py --mode phase4 \
    --real_data_path data/real_intent_data.csv
```

#### 5. Customize Signal Generation

To customize signals for your use case, edit `phase4/phase4_signals.py`:

```python
# Example: Add custom signal
def compute_custom_signal(self, ...):
    """Your custom signal logic"""
    # Your implementation
    return signal_dataframe
```

## Output Files

### Phase 1 Outputs
- `checkpoints/best_model.pt`: Trained Phase 1 models
- `visualizations/product_embeddings_*.png`: Embedding visualizations
- `visualizations/training_curves.png`: Training loss curves

### Phase 2 Outputs
- `checkpoints_phase2/best_model_phase2.pt`: Trained Phase 2 model

### Phase 3 Outputs
- `simulations/intent_trajectories.csv`: All agent interactions
- `simulations/simulation_stats.json`: Aggregate statistics

### Phase 4 Outputs
- `phase4_output/calibration_report.txt`: Calibration analysis
- `phase4_output/calibration_metrics.json`: Calibration metrics
- `phase4_output/target_metrics.json`: Target metrics from real data
- `phase4_output/signals/intent_index.csv`: Intent index over time
- `phase4_output/signals/momentum_7d.csv`: 7-day momentum
- `phase4_output/signals/momentum_30d.csv`: 30-day momentum
- `phase4_output/signals/trend_acceleration.csv`: Trend acceleration
- `phase4_output/signals/forecast_30d.csv`: 30-day forecasts
- `phase4_output/signals/forecast_90d.csv`: 90-day forecasts
- `phase4_output/signals/substitution_matrix.csv`: Substitution patterns
- `phase4_output/signals/price_elasticity.csv`: Price elasticity
- `phase4_output/visualizations/`: All visualizations

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure you're running from the `4_phases` directory
   - Check that all subdirectories exist
   - Verify Python path includes subdirectories

2. **CUDA/GPU Issues**
   - Models will automatically use CPU if CUDA unavailable
   - Set `device='cpu'` explicitly if needed

3. **Memory Issues**
   - Reduce `batch_size` in training
   - Reduce `n_agents` in Phase 3 simulation
   - Reduce `sequence_length` in Phase 2

4. **Data Format Issues**
   - Verify CSV files have required columns
   - Check for missing values
   - Ensure IDs match across files

### Performance Tuning

- **Training Speed**: Reduce `n_epochs`, increase `batch_size` (if memory allows)
- **Simulation Speed**: Reduce `n_agents`, `sim_days`, or `interactions_per_day`
- **Memory Usage**: Reduce batch sizes, sequence lengths, or number of agents

## Advanced Usage

### Custom Model Architectures

To use custom architectures, modify the model files:
- `phase1/models.py`: Customize embedding architectures
- `phase2/models_phase2.py`: Customize behavioral dynamics
- `phase3/models_phase3.py`: Customize agent/environment behavior

### Custom Signals

Add custom signals in `phase4/phase4_signals.py`:

```python
class SignalGenerator:
    def compute_custom_signal(self, ...):
        """Your custom signal"""
        # Implementation
        return signal_df
```

### Integration with External Systems

The pipeline outputs CSV files that can be easily integrated:
- Load signals: `pd.read_csv('phase4_output/signals/intent_index.csv')`
- Use in trading systems: Signals are timestamped and ready for backtesting
- API integration: Wrap `main.py` calls in API endpoints

## Citation

If you use this pipeline, please cite:
```
4-Phase Intent Modeling Pipeline
Consumer Intent Prediction and Signal Generation System
```

## License

[Your License Here]

## Support

For issues or questions:
1. Check the troubleshooting section
2. Review phase-specific documentation in each subdirectory
3. Examine example outputs in `phase4_output/`

## Version History

- **v1.0**: Initial release with all 4 phases
  - Phase 1: Taste Embedding Model
  - Phase 2: Behavioral Dynamic Engine
  - Phase 3: Large Population Simulation
  - Phase 4: Anchoring & Signal Generation

