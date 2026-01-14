# Market Simulation Demo Guide

## Overview

The Market Insight feature now includes:
- **3D Interactive Manifold**: Visualize markets/brands/products in 3D space
- **Market Simulation Engine**: Deterministic synthetic simulation of market perturbations
- **GPT-4 Integration**: Converts simulation results into consultant-grade insights
- **Scenario Analysis**: What-if analysis with visual impact overlay

## Architecture

```
User Question
    ↓
Market Simulator (deterministic synthetic)
    ↓
Simulation Result (impacted clusters, reactivity scores)
    ↓
GPT-4 Insight Generator (or mock mode)
    ↓
Structured Consultant Answer
    ↓
3D Manifold Visualization (with impact overlay)
```

## Setup

### 1. Install Dependencies

```bash
# Backend
cd backend
pip install plotly  # For 3D visualization support (optional, backend uses numpy)
pip install sentence-transformers umap-learn scikit-learn  # For manifold building

# Frontend
cd frontend
npm install plotly.js react-plotly.js
```

### 2. Environment Variables

Create `backend/.env` file:

```bash
# OpenAI API Key (for GPT-4 mode)
OPENAI_API_KEY=sk-your-key-here

# Market Insight Mode (mock or gpt)
MARKET_INSIGHT_MODE=mock  # or 'gpt' for real GPT-4
```

### 3. Database Migrations

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### 4. Seed Data & Build Manifold

```bash
# Seed data
python manage.py shell
>>> from api.market_insight_seed import seed_all
>>> seed_all(vertical='beauty', clear_existing=True)

# Build 3D manifold
python manage.py rebuild_market_manifold --vertical beauty --region US
```

### 5. Start Servers

```bash
# Backend
cd backend
python manage.py runserver

# Frontend
cd frontend
npm run dev
```

## Usage

### Basic Flow

1. **Open Market Insight Tab**
   - Navigate to "Hypothesis Test" → Select "Market Insight" view

2. **Explore 3D Manifold**
   - Rotate, zoom, pan the 3D plot
   - Filter by category, tier, brand type, momentum
   - Toggle view: Markets / Brands / Products
   - Click nodes to see details
   - Shift+Click to pin nodes

3. **Ask a Question**
   - Type any strategic question
   - Click "Ask Question" or press Cmd/Ctrl + Enter
   - System runs: Simulation → GPT Insight → Results

4. **View Results**
   - Executive Summary
   - Direct Answers
   - Market Map Takeaways (impacted clusters)
   - Recommended Actions (Now/Next/Long-term)
   - Confidence & Entropy scores
   - Evidence links

5. **Run Scenarios**
   - Adjust scenario parameters (price tier, channel, claims, bundle strategy)
   - Click "Run Scenario"
   - See impact overlay on 3D manifold (red gradient = reactivity)
   - Compare scenario results with baseline

## Modes

### Mock Mode (Default)

- No external API calls
- Deterministic synthetic outputs
- Fast and reproducible
- Good for demos

Set: `MARKET_INSIGHT_MODE=mock` in `.env`

### GPT Mode

- Uses GPT-4o for insight generation
- Requires `OPENAI_API_KEY`
- Caches responses (24h)
- More sophisticated analysis

Set: `MARKET_INSIGHT_MODE=gpt` in `.env`

## API Endpoints

### GET /api/market-insight-new/manifold/
Returns 3D manifold points:
```json
{
  "points": [
    {
      "id": "...",
      "type": "market",
      "label": "...",
      "x": 0.234,
      "y": -0.567,
      "z": 0.123,
      "cluster_id": 3,
      "cluster_label": "Skincare Premium",
      "reactivity_score": 0.75
    }
  ]
}
```

### POST /api/market-insight-new/simulate/
Run market simulation:
```json
{
  "question": "What categories should we prioritize?",
  "vertical": "beauty",
  "region": "US",
  "pinned_nodes": ["node-id-1"],
  "scenario_params": {
    "price_tier_shift": "super_premium",
    "channel_shift": "dtc_heavy",
    "claim_emphasis": "clean"
  }
}
```

Returns simulation result with impacted clusters and reactivity scores.

### POST /api/market-insight-new/insight/
Generate GPT insight from simulation:
```json
{
  "result_id": "sim-result-id",
  "question": "...",
  "vertical": "beauty",
  "region": "US"
}
```

Returns structured JSON insight.

### POST /api/market-insight-new/ask/
Full pipeline (simulate + insight):
```json
{
  "question": "...",
  "vertical": "beauty",
  "region": "US",
  "pinned_nodes": [],
  "scenario_params": {}
}
```

Returns both simulation and insight.

### GET /api/market-insight-new/runs/
Get simulation run history:
```
GET /api/market-insight-new/runs/?limit=20&vertical=beauty
```

## Regenerating the Manifold

```bash
# Rebuild for a vertical/region
python manage.py rebuild_market_manifold --vertical beauty --region US

# Or via API
curl -X POST http://localhost:8000/api/market-insight-new/rebuild-manifold/ \
  -H "Content-Type: application/json" \
  -d '{"vertical": "beauty", "region": "US"}'
```

## Simulation Engine Details

### Deterministic Generation

- Uses seed (default: 42) for reproducibility
- Same inputs → same outputs
- Good for demos and testing

### Impact Propagation

1. **Pinned Nodes**: Direct impact on clusters containing pinned nodes
2. **Perturbation Type**: Price tier, channel, claim shifts affect matching clusters
3. **Distance Decay**: Impact decreases with distance from pinned nodes
4. **Cluster Aggregation**: Clusters aggregate impact from multiple points

### Reactivity Scores

- 0.0 = No impact
- 1.0 = Maximum impact
- Visualized as red gradient on 3D manifold
- Size of points also reflects reactivity

## GPT Prompt Structure

### System Prompt
- Defines consultant role
- Enforces strict JSON schema
- Prevents data fabrication

### User Prompt Includes
- Question context
- Scenario parameters
- Pinned nodes
- Simulation summary (top clusters, shifts, competitors, innovation)
- Instructions for consultant tone

### Output Schema
Strict JSON with:
- title
- executive_summary (bullets)
- direct_answers (keyed)
- market_map_takeaways
- recommended_actions (now/next/long_term)
- whitespace_opportunities
- risks_and_watchouts
- assumptions
- evidence
- confidence (score, entropy, rationale)
- next_questions

## Caching

- GPT responses cached for 24 hours
- Cache key = hash(question + scenario + pinned nodes + sim run id)
- Stored in Django cache + DB (MarketInsightAnswer)

## Troubleshooting

### 3D Plot Not Rendering
- Check browser console for errors
- Ensure plotly.js installed: `npm list plotly.js`
- Try refreshing the page

### Simulation Returns Empty Results
- Check if manifold is built: `ManifoldPoint.objects.count()`
- Rebuild manifold if needed
- Check pinned_nodes are valid IDs

### GPT Mode Not Working
- Verify `OPENAI_API_KEY` in `.env`
- Check `MARKET_INSIGHT_MODE=gpt`
- Check backend logs for API errors
- Falls back to mock mode on error

### Manifold Points Missing Z Coordinates
- Rebuild manifold (old 2D points don't have z)
- Check `ManifoldPoint.objects.filter(z__isnull=True).count()`

## Case Templates

### Case 1: Food Growth & Whitespace
- Question keywords: "food", "snack", "whitespace", "functional job"
- Outputs: functional jobs, cohort differences, whitespace matrix

### Case 2: Beauty Portfolio Strategy
- Question keywords: "beauty", "portfolio", "category", "tier"
- Outputs: category importance, tier evolution, competitor positioning, innovation patterns

## Performance Notes

- Manifold building: ~10-30 seconds for 300-1500 points
- Simulation: ~1-2 seconds (deterministic)
- GPT insight: ~3-10 seconds (or cached)
- 3D rendering: Smooth with Plotly (handles 1000+ points)

## Next Steps

1. **Add Real Data**: Connect to actual market data sources
2. **Advanced Simulations**: More sophisticated impact models
3. **Export**: PDF/PPT export of insights
4. **Collaboration**: Share runs and pinned nodes
5. **History**: Replay past runs

## File Structure

```
backend/api/
  ├── market_insight_models.py      # DB models (including sim runs)
  ├── market_insight_simulator.py   # Simulation engine
  ├── market_insight_gpt.py         # GPT integration
  ├── market_insight_manifold.py    # 3D manifold builder
  └── market_insight_views.py      # API endpoints

frontend/src/components/market-insight/
  ├── MarketManifold3D.jsx          # 3D Plotly visualization
  └── InsightWorkspace.jsx          # Question/answer UI
```

## Demo Checklist

- [ ] Seed data for Beauty
- [ ] Build 3D manifold
- [ ] Ask a question → see simulation + insight
- [ ] Pin nodes → see impact on clusters
- [ ] Run scenario → see reactivity overlay
- [ ] Switch to Food → test Case 1 template
- [ ] Check confidence/entropy scores
- [ ] Review evidence links

The system is now fully dynamic and demo-ready!
