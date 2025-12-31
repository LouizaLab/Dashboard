# Investor Demo Dashboard

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run the dashboard
streamlit run app.py
```

The dashboard will automatically open in your browser at `http://localhost:8501`.

## Features

### 🤖 AI Chatbot (Sidebar)
- **Conversational Interface**: Ask questions about insights and data
- **Context-Aware**: Reads all dashboard data as input
- **Insight Summarization**: Automatically summarizes insights
- **Suggested Questions**: Quick access to common questions
- **Conversation History**: Maintains context across messages

**Setup**: Set `OPENAI_API_KEY` environment variable (see CHATBOT_SETUP.md)

### 1. Taste Snapshot (Panel A)
- **Radar Chart**: Visual taste profile showing preferences across segments
- **Key Metrics**: Average intent, sugar preference, caffeine tolerance, price sensitivity
- **Detailed Table**: Complete segment profile data

### 2. Behavioral Dynamics (Panel B)
- **Time Series**: Purchase probability, repeat rate, churn rate, adoption rate over time
- **Multi-Metric View**: 2x2 subplot showing all behavioral metrics
- **Segment-Context Interaction**: Heatmap showing how context affects different segments

### 3. Auto-Generated Insights (Panel C)
- **5-10 Insight Cards**: Automatically generated from data
  - Biggest week-over-week changes
  - Segment-context interaction strength
  - Price sensitivity breakpoints
  - Repeat purchase lift after exposures
  - Momentum trends
  - Category switching patterns
  - Temporal patterns (peak hours)
  - Segment preference divergence
- **Evidence Charts**: Supporting visualizations for top insights

### 4. What-If Simulation (Panel D)
- **Counterfactual Analysis**: Compare baseline vs modified scenarios
- **Adjustable Parameters**:
  - Price multiplier (0.5x - 2.0x)
  - Sugar adjustment (-20g to +20g)
  - Marketing exposure multiplier (0x - 3x)
- **Comparison Metrics**: Intent delta, interaction delta, percentage changes
- **Overlay Visualization**: Side-by-side baseline vs counterfactual time series

## Data Sources

The dashboard uses existing data files from the repo:
- `data/products.csv`: Product metadata
- `data/segments.csv`: User segments
- `data/contexts.csv`: Context definitions
- `data/intent_logs.csv`: Historical intent logs
- `simulations/intent_trajectories.csv`: Phase 3 simulation results
- `simulations/phase4_anchored.csv`: Phase 4 calibrated results
- `phase4_output/signals/*.csv`: Generated signals

## Architecture

- **`app.py`**: Main Streamlit application
- **`src/dashboard/data_loader.py`**: Data loading and caching
- **`src/dashboard/metrics.py`**: Metric computation (taste profiles, behavioral dynamics)
- **`src/dashboard/insights.py`**: Auto-generated insight cards
- **`src/dashboard/simulate.py`**: Counterfactual simulation wrapper

## Usage Tips

1. **Select Segments**: Use sidebar to filter by specific user segments
2. **Filter Contexts**: Narrow down to specific contexts (time, location, occasion)
3. **Adjust Time Range**: Focus on specific time periods (0-90 days)
4. **Run What-If Scenarios**: Adjust sliders to see counterfactual outcomes
5. **Explore Insights**: Review auto-generated insights for key patterns

## Troubleshooting

- **No data showing**: Ensure Phase 3/4 simulations have been run
- **Missing visualizations**: Check that required columns exist in data files
- **Slow loading**: Data is cached - first load may be slower
- **Port conflict**: Change port with `streamlit run app.py --server.port 8502`

## Demo Script

See the "Demo Script" expander in the dashboard for 5 key talking points:
1. Taste Embedding Model
2. Behavioral Dynamics
3. Large Population Simulation
4. Ground Truth Anchoring
5. Actionable Signals

