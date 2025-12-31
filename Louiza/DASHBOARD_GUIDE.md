# Phase 4 Dashboard Guide

## Overview

The Phase 4 Dashboard provides interactive analysis of signal correlations, pattern detection, and behavioral insights after calibration. It helps identify which signals indicate patterns and trends from a behavioral standpoint.

## Features

### 1. **Signal Correlation Analysis**
- Correlation heatmap showing relationships between different signals
- Identifies which signals move together or inversely
- Helps understand signal dependencies

### 2. **Pattern Detection**
- **Strong Momentum**: Categories with consistently strong positive/negative momentum
- **Trend Reversals**: Categories experiencing trend direction changes
- **Substitution Patterns**: Product category substitution relationships
- **Price Sensitivity**: Categories with high price elasticity

### 3. **Behavioral Insights**
- **Segment Preferences**: Average intent by segment and category
- **Category Switching Rates**: Distribution of agent switching behavior
- **Temporal Patterns**: Hourly intent distribution (peak/low hours)
- **Calibration Impact**: Phase 3 vs Phase 4 error comparison
- **Signal Strength**: Signal-to-noise ratios for momentum and acceleration
- **Predictive Power**: Lead-lag correlations showing signal predictive ability

### 4. **Signal Time Series**
- Interactive time series visualization
- Filter by category to see specific trends
- Overlays momentum on intent index

## Usage

### Static HTML Dashboard

```bash
# Generate static dashboard
python launch_dashboard.py

# Or directly
python phase4_dashboard.py
```

The dashboard will be saved to `phase4_output/dashboard.html`. Open it in your browser.

### Interactive Dashboard (Dash)

```bash
# Launch interactive dashboard
python launch_dashboard.py interactive

# Or directly
python phase4_dashboard.py interactive
```

Then open http://localhost:8050 in your browser.

## Dashboard Components

### Correlation Heatmap
- Shows correlation coefficients between signals
- Red = positive correlation, Blue = negative correlation
- Values range from -1 to +1
- Helps identify redundant signals or complementary signals

### Pattern Detection Charts
- **Strong Momentum**: Bar chart showing categories with strongest momentum trends
- **Trend Reversals**: Count of trend reversals per category
- **Substitution Patterns**: Top substitution relationships (from → to)
- **Price Sensitivity**: Price elasticity by category

### Behavioral Insights
- **Segment Preferences**: Top categories by average intent across segments
- **Switching Rates**: Histogram of agent switching behavior
- **Temporal Patterns**: Hourly intent distribution showing peak consumption times
- **Calibration Impact**: Visual comparison of Phase 3 vs Phase 4 accuracy
- **Signal Strength**: Signal-to-noise ratios (higher = stronger signal)
- **Predictive Power**: Correlation between signals and future outcomes

### Signal Time Series
- Time series plot of intent index and momentum
- Filterable by category
- Shows trends over time
- Momentum overlay (scaled for visibility)

## Interpreting Results

### Strong Correlations (>0.7 or <-0.7)
- **Positive**: Signals move together - can use one to predict the other
- **Negative**: Signals move inversely - complementary information

### Pattern Detection
- **Strong Momentum**: Categories with consistent trends (good for forecasting)
- **Trend Reversals**: Categories experiencing change (watch for opportunities)
- **Substitution Patterns**: High substitution probability indicates competitive relationships
- **Price Sensitivity**: Elastic categories (<-1.0) are price-sensitive

### Behavioral Insights
- **Segment Preferences**: Identifies which segments prefer which categories
- **Switching Rates**: High switching = low loyalty, low switching = high loyalty
- **Temporal Patterns**: Peak hours indicate optimal timing for interventions
- **Signal Strength**: Higher values = more reliable signals
- **Predictive Power**: Positive correlations indicate signals predict future outcomes

## Example Use Cases

### 1. Finding Predictive Signals
Look at the "Predictive Power" chart:
- Signals with high positive correlation (>0.5) are good predictors
- Use these signals for forecasting

### 2. Identifying Substitution Opportunities
Check "Substitution Patterns":
- High substitution probability from Category A → Category B
- Suggests opportunity to capture market share

### 3. Price Strategy
Review "Price Sensitivity":
- Elastic categories (<-1.0) respond strongly to price changes
- Inelastic categories (>-1.0) are less price-sensitive

### 4. Timing Interventions
Check "Temporal Patterns":
- Peak hours indicate best times for marketing/promotions
- Low hours indicate opportunities for growth

## Data Requirements

The dashboard requires:
- Phase 4 signals in `phase4_output/signals/`
- Phase 3 simulation data: `simulations/intent_trajectories.csv`
- Phase 4 anchored data: `simulations/phase4_anchored.csv`
- Real data (optional): `data/real_intent_data.csv`

## Troubleshooting

### Dashboard not generating
- Ensure Phase 4 has been run: `python main.py --mode phase4`
- Check that signal files exist in `phase4_output/signals/`

### Missing visualizations
- Some charts require specific data columns
- Check that Phase 3/Phase 4 data includes required fields (agent_id, segment_id, timestamp, etc.)

### Interactive dashboard not starting
- Check if port 8050 is available
- Try a different port: modify `app.run_server(port=8051)` in `phase4_dashboard.py`

## Next Steps

1. **Run Phase 4** to generate signals:
   ```bash
   python main.py --mode phase4
   ```

2. **Generate Dashboard**:
   ```bash
   python launch_dashboard.py
   ```

3. **Analyze Results**:
   - Open `phase4_output/dashboard.html`
   - Review correlations, patterns, and behavioral insights
   - Identify actionable signals

4. **Iterate**:
   - Adjust calibration parameters
   - Re-run Phase 4
   - Regenerate dashboard to see changes

