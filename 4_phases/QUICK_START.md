# Quick Start Guide

## Minimal Example (5 minutes)

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate synthetic data
python main.py --mode generate_data --n_products 20 --n_logs 500

# 3. Train Phase 1
python main.py --mode train --n_epochs 10

# 4. Train Phase 2
python main.py --mode train_phase2 --phase2_n_epochs 5

# 5. Run simulation
python main.py --mode simulate_phase3 --n_agents 5 --sim_days 7

# 6. Generate signals
python main.py --mode phase4
```

## Using Your Own Data

### Step 1: Prepare Data Files

Create these CSV files in `data/` directory:

**products.csv** (required columns):
- product_id, category, ingredients, sensory_tags, sugar_g, caffeine_mg, calories, protein_g, description, price

**segments.csv** (required columns):
- segment_id, age_bucket, region, psychographic

**contexts.csv** (required columns):
- context_id, time_of_day, hour, location, occasion, price_shown

**intent_logs.csv** (required columns):
- log_id, timestamp, product_id, segment_id, context_id, preference_value

### Step 2: Run Pipeline

```bash
# Train Phase 1 with your data
python main.py --mode train --data_dir data --n_epochs 50

# Continue with Phase 2, 3, 4 as above
```

### Step 3: Calibrate with Real Intent Data

Place your real intent data in `data/real_intent_data.csv` with columns:
- timestamp (or date)
- product_id (or product_category)
- intent_value

Then run:
```bash
python main.py --mode phase4 --real_data_path data/real_intent_data.csv
```

## Common Commands

```bash
# Full pipeline
python main.py --mode all_phases

# Just data generation
python main.py --mode generate_data

# Just training Phase 1
python main.py --mode train

# Just visualization
python main.py --mode visualize

# Just Phase 4 signals
python main.py --mode phase4
```

## Output Locations

- **Models**: `checkpoints/`, `checkpoints_phase2/`
- **Simulation data**: `simulations/intent_trajectories.csv`
- **Signals**: `phase4_output/signals/`
- **Visualizations**: `visualizations/`, `phase4_output/visualizations/`

## Troubleshooting

**Import errors**: Run from `4_phases/` directory
**Memory errors**: Reduce batch_size or n_agents
**CUDA errors**: Models auto-fallback to CPU

## Next Steps

See `README.md` for detailed documentation on:
- Phase architecture details
- Customization options
- Advanced usage
- Signal interpretation

