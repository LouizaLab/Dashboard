# File Structure Reference

Complete listing of all files in the 4-phase pipeline and their purposes.

## Root Directory

- `main.py` - Main entry point for running all phases
- `requirements.txt` - Python package dependencies
- `README.md` - Comprehensive documentation
- `QUICK_START.md` - Quick start guide
- `DATA_ADAPTATION_GUIDE.md` - Guide for adapting to your real data
- `FILE_STRUCTURE.md` - This file

## Phase 1: Taste Embedding Model

**Location**: `phase1/`

- `models.py` - Model architectures:
  - `ProductEmbeddingModel` - Encodes products (ingredients, tags, nutrition, text) → 128D
  - `ContextEmbeddingModel` - Encodes contexts (time, location, occasion, price) → 64D
  - `SegmentEmbeddingModel` - Encodes segments (age, region, psychographic) → 64D
  - `CombinedEmbeddingModel` - Combines all three embeddings

- `train_phase1.py` - Training script for Phase 1:
  - `train_phase1()` - Main training function
  - `PreferencePredictor` - Predicts preference from embeddings
  - Training loop with validation

- `data_utils.py` - Data preprocessing utilities:
  - `Vocabulary` - Text vocabulary builder
  - `EmbeddingDataset` - PyTorch dataset for training
  - `build_vocabularies()` - Builds vocabularies from product data

- `__init__.py` - Package initialization

## Phase 2: Behavioral Dynamic Engine

**Location**: `phase2/`

- `models_phase2.py` - Model architectures:
  - `BehavioralState` - Latent state representation (128D)
  - `ObservationModel` - P(like | s_t, z_product, z_context)
  - `StateTransitionModel` - s_{t+1} = f(s_t, z_product, z_context, y_t)
  - `BehavioralDynamicEngine` - Complete system

- `train_phase2.py` - Training script for Phase 2:
  - `train_phase2()` - Main training function
  - `load_phase1_models()` - Loads Phase 1 models
  - Sequence-level training

- `data_phase2.py` - Sequence data utilities:
  - `SequenceDataset` - PyTorch dataset for sequences
  - Sequence encoding functions

- `__init__.py` - Package initialization

## Phase 3: Large Population Simulation

**Location**: `phase3/`

- `models_phase3.py` - Simulation components:
  - `Agent` - Represents a user with state and personality
  - `Environment` - Manages products, contexts, prices, macro context
  - `PopulationSimulator` - Orchestrates population simulation

- `simulate_phase3.py` - Main simulation script:
  - `run_simulation()` - Main simulation function
  - `encode_all_products_and_contexts()` - Pre-compute embeddings
  - `encode_segments()` - Encode segment embeddings

- `__init__.py` - Package initialization

## Phase 4: Ground Truth Anchoring & Signals

**Location**: `phase4/`

- `phase4_main.py` - Main Phase 4 script:
  - `run_phase4()` - Orchestrates Phase 4 execution
  - Coordinates calibration, anchoring, and signal generation

- `phase4_calibration.py` - Calibration utilities:
  - `IntentDataCalibrator` - Compares simulated vs real distributions
  - `compute_distribution_metrics()` - Computes calibration metrics
  - `compare_distributions()` - Compares simulated vs real

- `phase4_signals.py` - Signal generation:
  - `SignalGenerator` - Generates investment signals
  - `compute_intent_index()` - Intent index over time
  - `compute_category_momentum_index()` - Momentum signals
  - `compute_trend_acceleration()` - Trend acceleration
  - `compute_forecasts()` - Demand forecasts
  - `compute_substitution_matrix()` - Substitution patterns
  - `compute_price_elasticity()` - Price sensitivity

- `phase4_anchoring.py` - Ground truth anchoring:
  - `GroundTruthAnchoring` - Anchors models to real data
  - `ParameterCalibrator` - Calibrates simulation parameters

- `phase4_sales_validation.py` - Sales validation:
  - `SalesValidator` - Validates intent predicts sales
  - Phase 4.2 validation utilities

- `phase4_dashboard.py` - Dashboard interface:
  - `Phase4Dashboard` - Interactive dashboard (if implemented)

- `__init__.py` - Package initialization

## Data Generation

**Location**: `data_generation/`

- `data_generator.py` - Synthetic data generation:
  - `SyntheticDataGenerator` - Generates synthetic data
  - `generate_products()` - Generate product metadata
  - `generate_segments()` - Generate user segments
  - `generate_contexts()` - Generate contexts
  - `generate_intent_logs()` - Generate intent logs
  - `generate_all_data()` - Generate all data at once

- `generate_sales_data.py` - Sales data generation:
  - `generate_sales_from_intent()` - Generate sales from intent data
  - Used for Phase 4.2 validation

- `__init__.py` - Package initialization

## Visualizations

**Location**: `visualizations/`

- `visualize.py` - Phase 1 visualization:
  - `EmbeddingVisualizer` - Visualizes embeddings
  - `visualize_product_embeddings()` - Product embedding plots
  - `visualize_training_curves()` - Training loss curves
  - `analyze_embeddings()` - Embedding analysis

- `visualize_anchoring.py` - Phase 4 anchoring visualization:
  - `AnchoringVisualizer` - Visualizes anchoring results
  - Before/after comparison plots

- `visualize_improvement.py` - Improvement visualization:
  - `create_improvement_visualization()` - Shows improvement metrics

- `create_comparison_report.py` - Comparison reports:
  - `create_comparison_report()` - Phase 3 vs Phase 4 vs Real comparison

- `create_summary_report.py` - Summary reports:
  - `create_improvement_summary_report()` - Improvement summary

- `__init__.py` - Package initialization

## Output Directories (Created at Runtime)

- `data/` - Input data files (products.csv, segments.csv, contexts.csv, intent_logs.csv)
- `checkpoints/` - Phase 1 model checkpoints
- `checkpoints_phase2/` - Phase 2 model checkpoints
- `simulations/` - Phase 3 simulation outputs
- `phase4_output/` - Phase 4 outputs:
  - `signals/` - Generated signals (CSV files)
  - `visualizations/` - Phase 4 visualizations
- `visualizations/` - Phase 1 visualizations

## Key Dependencies

All phases depend on:
- `torch` - PyTorch for deep learning
- `pandas` - Data manipulation
- `numpy` - Numerical computing
- `matplotlib`, `seaborn`, `plotly` - Visualization
- `scikit-learn` - Machine learning utilities

## File Relationships

```
main.py
├── data_generation/data_generator.py (Step 1: Generate data)
├── phase1/
│   ├── train_phase1.py (Step 2: Train Phase 1)
│   └── models.py (Phase 1 models)
├── visualizations/visualize.py (Step 3: Visualize)
├── phase2/
│   ├── train_phase2.py (Step 4: Train Phase 2)
│   ├── models_phase2.py (Phase 2 models)
│   └── data_phase2.py (Sequence data)
├── phase3/
│   ├── simulate_phase3.py (Step 5: Simulate)
│   └── models_phase3.py (Simulation models)
└── phase4/
    ├── phase4_main.py (Step 6: Calibrate & Signals)
    ├── phase4_calibration.py (Calibration)
    ├── phase4_signals.py (Signal generation)
    └── phase4_anchoring.py (Anchoring)
```

## Usage Flow

1. **Data Generation**: `data_generation/data_generator.py` → `data/*.csv`
2. **Phase 1 Training**: `phase1/train_phase1.py` → `checkpoints/best_model.pt`
3. **Visualization**: `visualizations/visualize.py` → `visualizations/*.png`
4. **Phase 2 Training**: `phase2/train_phase2.py` → `checkpoints_phase2/best_model_phase2.pt`
5. **Phase 3 Simulation**: `phase3/simulate_phase3.py` → `simulations/intent_trajectories.csv`
6. **Phase 4 Execution**: `phase4/phase4_main.py` → `phase4_output/`

## Customization Points

To customize the pipeline:

1. **Model Architectures**: Edit `phase1/models.py`, `phase2/models_phase2.py`
2. **Data Processing**: Edit `phase1/data_utils.py`, `phase2/data_phase2.py`
3. **Simulation Logic**: Edit `phase3/models_phase3.py`
4. **Signal Generation**: Edit `phase4/phase4_signals.py`
5. **Visualizations**: Edit files in `visualizations/`

## Notes

- All Python files use relative imports with `sys.path` modifications
- Run `main.py` from the `4_phases/` directory
- Output directories are created automatically
- Models are saved as PyTorch checkpoints (`.pt` files)
- Signals are saved as CSV files for easy integration

