# Data Adaptation Guide

This guide provides detailed instructions for adapting the 4-phase pipeline to work with your real-world data.

## Data Schema Requirements

### 1. Products Data (`data/products.csv`)

**Required Columns:**
- `product_id` (string): Unique identifier for each product
- `category` (string): Product category (e.g., "energy_drink", "soda", "juice")
- `ingredients` (string): Comma-separated list of ingredients (e.g., "water,sugar,caffeine")
- `sensory_tags` (string): Comma-separated sensory tags (e.g., "sweet,fizzy,refreshing")
- `sugar_g` (float): Sugar content in grams
- `caffeine_mg` (float): Caffeine content in milligrams
- `calories` (float): Calorie count
- `protein_g` (float): Protein content in grams
- `description` (string): Text description of the product
- `price` (float): Product price

**Example:**
```csv
product_id,category,ingredients,sensory_tags,sugar_g,caffeine_mg,calories,protein_g,description,price
prod_001,energy_drink,"water,sugar,caffeine,citric_acid","sweet,fizzy,energizing",25.0,150.0,110.0,0.0,"A refreshing energy drink with natural flavors",2.99
```

**Data Transformation Example:**
```python
import pandas as pd

# Your existing products data
your_products = pd.read_csv('your_products.csv')

# Transform to required format
products = pd.DataFrame({
    'product_id': your_products['id'].astype(str),
    'category': your_products['category'],
    'ingredients': your_products['ingredient_list'].str.join(','),  # Convert list to comma-separated
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

### 2. Segments Data (`data/segments.csv`)

**Required Columns:**
- `segment_id` (string): Unique identifier for each segment
- `age_bucket` (string): Age range (e.g., "18-25", "26-35", "36-45", "46-55", "56+")
- `region` (string): Geographic region
- `psychographic` (string): Psychographic profile (e.g., "health_focused", "budget_sensitive", "premium_seeker")

**Example:**
```csv
segment_id,age_bucket,region,psychographic,segment_name
seg_01,26-35,north,health_focused,Segment_1
seg_02,18-25,south,adventurous,Segment_2
```

**Data Transformation Example:**
```python
# Your user segments
your_segments = pd.read_csv('your_segments.csv')

segments = pd.DataFrame({
    'segment_id': your_segments['segment_id'],
    'age_bucket': your_segments['age_range'],  # Map to standard buckets if needed
    'region': your_segments['region'],
    'psychographic': your_segments['psychographic_profile'],
    'segment_name': your_segments.get('name', 'Segment_' + your_segments['segment_id'])
})

segments.to_csv('data/segments.csv', index=False)
```

### 3. Contexts Data (`data/contexts.csv`)

**Required Columns:**
- `context_id` (string): Unique identifier for each context
- `time_of_day` (string): One of ["morning", "afternoon", "evening", "late_night"]
- `hour` (int): Hour of day (0-23)
- `location` (string): Location type (e.g., "home", "work", "cafe", "gym")
- `occasion` (string): Occasion type (e.g., "work", "social", "post_gym")
- `price_shown` (float): Price shown to user in this context

**Example:**
```csv
context_id,time_of_day,hour,location,occasion,price_shown
ctx_001,morning,8,work,morning,2.99
ctx_002,afternoon,14,cafe,social,3.49
```

**Data Transformation Example:**
```python
# Your context data
your_contexts = pd.read_csv('your_contexts.csv')

def map_time_of_day(hour):
    if 5 <= hour < 12:
        return 'morning'
    elif 12 <= hour < 17:
        return 'afternoon'
    elif 17 <= hour < 21:
        return 'evening'
    else:
        return 'late_night'

contexts = pd.DataFrame({
    'context_id': your_contexts['context_id'],
    'time_of_day': your_contexts['hour'].apply(map_time_of_day),
    'hour': your_contexts['hour'],
    'location': your_contexts['location'],
    'occasion': your_contexts['occasion'],
    'price_shown': your_contexts['displayed_price']
})

contexts.to_csv('data/contexts.csv', index=False)
```

### 4. Intent Logs (`data/intent_logs.csv`)

**Required Columns:**
- `log_id` (string): Unique identifier for each log entry
- `timestamp` (string): Timestamp in format "YYYY-MM-DD HH:MM:SS"
- `product_id` (string): Must match product_id in products.csv
- `segment_id` (string): Must match segment_id in segments.csv
- `context_id` (string): Must match context_id in contexts.csv
- `preference_value` (float): Preference/intent value between 0 and 1
- `rating` (int, optional): Rating on 1-5 scale
- `liked` (int, optional): Binary indicator (0 or 1)

**Example:**
```csv
log_id,timestamp,product_id,segment_id,context_id,preference_value,rating,liked
log_0001,2024-01-15 08:30:00,prod_001,seg_01,ctx_001,0.75,4,1
log_0002,2024-01-15 14:20:00,prod_002,seg_02,ctx_002,0.45,2,0
```

**Data Transformation Example:**
```python
# Your interaction/rating data
your_logs = pd.read_csv('your_interactions.csv')

# Normalize preference_value to 0-1 scale if needed
# If you have ratings 1-5, convert: (rating - 1) / 4
# If you have binary likes, use directly: liked (0 or 1)

intent_logs = pd.DataFrame({
    'log_id': your_logs['interaction_id'],
    'timestamp': pd.to_datetime(your_logs['timestamp']).dt.strftime('%Y-%m-%d %H:%M:%S'),
    'product_id': your_logs['product_id'],
    'segment_id': your_logs['user_segment_id'],  # Map to your segment IDs
    'context_id': your_logs['context_id'],
    'preference_value': (your_logs['rating'] - 1) / 4.0,  # Normalize 1-5 to 0-1
    'rating': your_logs['rating'],
    'liked': (your_logs['rating'] >= 4).astype(int)
})

intent_logs.to_csv('data/intent_logs.csv', index=False)
```

### 5. Real Intent Data (`data/real_intent_data.csv`) - For Phase 4

**Required Columns:**
- `timestamp` or `date`: Time information
- `product_id` or `product_category`: Product information
- `intent_value`: Intent/preference value (0-1 scale)
- `segment_id` (optional): Segment information

**Example:**
```csv
timestamp,product_category,intent_value,segment_id
2024-01-15,energy_drink,0.72,seg_01
2024-01-15,soda,0.58,seg_02
```

## Step-by-Step Adaptation Process

### Step 1: Data Preparation

1. **Collect your data** from your systems
2. **Transform to required schemas** using examples above
3. **Validate data**:
   ```python
   # Check for missing values
   products.isnull().sum()
   segments.isnull().sum()
   contexts.isnull().sum()
   intent_logs.isnull().sum()
   
   # Check ID consistency
   assert set(intent_logs['product_id']).issubset(set(products['product_id']))
   assert set(intent_logs['segment_id']).issubset(set(segments['segment_id']))
   assert set(intent_logs['context_id']).issubset(set(contexts['context_id']))
   ```

### Step 2: Update Vocabulary (if needed)

The pipeline automatically builds vocabularies from your data. However, if you have:
- **Very large vocabularies**: You may want to filter rare ingredients/tags
- **Special tokens**: Add them to the Vocabulary class in `phase1/data_utils.py`

### Step 3: Adjust Model Parameters (optional)

If your data characteristics differ significantly:

**In `phase1/models.py`:**
```python
# Adjust embedding dimensions if needed
product_model = ProductEmbeddingModel(
    vocab_size=vocab_size,
    embedding_dim=64,      # Increase for richer representations
    hidden_dim=128,         # Increase for more capacity
    output_dim=128          # Keep consistent
)
```

**In `phase2/models_phase2.py`:**
```python
# Adjust state dimensions if needed
model = BehavioralDynamicEngine(
    segment_dim=64,
    product_dim=128,
    context_dim=64,
    state_dim=128,          # Increase for more complex behaviors
    hidden_dim=256           # Increase for more capacity
)
```

### Step 4: Run Pipeline

```bash
# 1. Train Phase 1
python main.py --mode train \
    --data_dir data \
    --n_epochs 50 \
    --batch_size 32

# 2. Train Phase 2
python main.py --mode train_phase2 \
    --phase1_checkpoint checkpoints/best_model.pt \
    --data_dir data \
    --phase2_n_epochs 30

# 3. Run simulation
python main.py --mode simulate_phase3 \
    --n_agents 100 \
    --sim_days 90 \
    --data_dir data

# 4. Calibrate with real data
python main.py --mode phase4 \
    --real_data_path data/real_intent_data.csv \
    --simulation_data simulations/intent_trajectories.csv
```

### Step 5: Validate Results

1. **Check calibration report**: `phase4_output/calibration_report.txt`
2. **Review signals**: `phase4_output/signals/`
3. **Examine visualizations**: `phase4_output/visualizations/`

## Common Data Issues and Solutions

### Issue 1: Missing Columns

**Problem**: Your data doesn't have all required columns

**Solution**: 
- Use default values for optional columns
- Create derived columns from existing data
- Use data transformation scripts (see examples above)

### Issue 2: Different Data Types

**Problem**: Your data uses different formats (e.g., ratings 1-10 instead of 1-5)

**Solution**: Normalize in transformation step:
```python
# Normalize 1-10 rating to 0-1 preference
preference_value = (rating - 1) / 9.0
```

### Issue 3: Missing Relationships

**Problem**: Your intent logs reference products/segments/contexts that don't exist

**Solution**: Filter logs to only include valid IDs:
```python
valid_products = set(products['product_id'])
valid_segments = set(segments['segment_id'])
valid_contexts = set(contexts['context_id'])

intent_logs = intent_logs[
    intent_logs['product_id'].isin(valid_products) &
    intent_logs['segment_id'].isin(valid_segments) &
    intent_logs['context_id'].isin(valid_contexts)
]
```

### Issue 4: Temporal Mismatches

**Problem**: Your timestamps are in different format or timezone

**Solution**: Standardize timestamps:
```python
intent_logs['timestamp'] = pd.to_datetime(intent_logs['timestamp'], utc=True)
intent_logs['timestamp'] = intent_logs['timestamp'].dt.tz_convert('UTC')
intent_logs['timestamp'] = intent_logs['timestamp'].dt.strftime('%Y-%m-%d %H:%M:%S')
```

## Testing Your Data

Before running the full pipeline, test with a small subset:

```python
# Create test subset
products_test = products.head(10)
segments_test = segments.head(3)
contexts_test = contexts.head(20)
intent_logs_test = intent_logs.head(100)

# Save test data
products_test.to_csv('data_test/products.csv', index=False)
segments_test.to_csv('data_test/segments.csv', index=False)
contexts_test.to_csv('data_test/contexts.csv', index=False)
intent_logs_test.to_csv('data_test/intent_logs.csv', index=False)

# Run with test data
python main.py --mode train --data_dir data_test --n_epochs 5
```

## Next Steps

1. **Start with synthetic data** to understand the pipeline
2. **Transform your data** using examples above
3. **Run with small subset** to validate
4. **Scale up** to full dataset
5. **Calibrate** with real intent data in Phase 4

For more details, see `README.md` and `QUICK_START.md`.

