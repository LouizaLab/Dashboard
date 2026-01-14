# Market Insight Implementation Guide

## Overview

The Market Insight feature provides an interactive Large Market Manifold visualization and a consultant-friendly Insight Workspace for answering strategic questions about Beauty (prestige) and Food markets.

## Architecture

### Backend Components

1. **Domain Models** (`backend/api/market_insight_models.py`)
   - `MarketDefinition`: Observed markets (Beauty/Food)
   - `Brand`: Brand entities with positioning
   - `Product`: Product entities with claims, ingredients, pricing
   - `MarketSignal`: Time-series signals (intent, momentum, elasticity)
   - `InnovationEvent`: Innovation events (launches, campaigns)
   - `ManifoldPoint`: 2D coordinates for visualization
   - `InsightQuery` / `InsightAnswer`: Query logging and responses

2. **Seed Data** (`backend/api/market_insight_seed.py`)
   - Generates synthetic but realistic data for Beauty and Food markets
   - Includes 30+ prestige beauty brands
   - Creates 15-25 market definitions per vertical
   - Generates time-series signals and innovation events

3. **Manifold Builder** (`backend/api/market_insight_manifold.py`)
   - Computes embeddings using sentence-transformers (or mock fallback)
   - Projects to 2D using UMAP (or PCA fallback)
   - Clusters using HDBSCAN/KMeans
   - Caches results in `ManifoldPoint` table

4. **Insight Engine** (`backend/api/market_insight_engine.py`)
   - Multi-agent orchestration:
     - **Explorer**: Retrieves relevant markets/brands/products/signals
     - **Analyst**: Synthesizes trends and answers sub-questions
     - **Critic**: Checks for overreach and highlights uncertainty
     - **Anchoring**: Attaches evidence and computes confidence/entropy
   - Supports Case 1 (Food) and Case 2 (Beauty) templates
   - Returns structured JSON with evidence and confidence scores

5. **API Endpoints** (`backend/api/market_insight_views.py`)
   - `GET /api/market-insight-new/manifold/`: Returns manifold points
   - `GET /api/market-insight-new/node/<type>/<id>/`: Node details
   - `POST /api/market-insight-new/ask/`: Answer consultant questions
   - `POST /api/market-insight-new/scenario/`: What-if analysis
   - `POST /api/market-insight-new/seed/`: Seed data
   - `POST /api/market-insight-new/rebuild-manifold/`: Rebuild manifold

### Frontend Components

1. **MarketManifoldMap** (`frontend/src/components/market-insight/MarketManifoldMap.jsx`)
   - Interactive D3.js scatter plot
   - Filters: category, price tier, brand type, momentum
   - Click to select, Shift+Click to pin nodes
   - Hover tooltips with node details

2. **InsightWorkspace** (`frontend/src/components/market-insight/InsightWorkspace.jsx`)
   - Case template selector (Case 1, Case 2, Custom)
   - Question input with sub-question checkboxes
   - Context chips from pinned nodes
   - Results rendering with structured sections

3. **MarketInsightPanel** (`frontend/src/components/hypothesis/MarketInsightPanel.jsx`)
   - Two-panel layout (65% map, 35% workspace)
   - Node detail drawer
   - Vertical/region selector

## Setup Instructions

### 1. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt
pip install sentence-transformers umap-learn scikit-learn  # Optional but recommended

# Frontend
cd frontend
npm install
npm install d3  # For manifold visualization
```

### 2. Database Migrations

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### 3. Seed Data

```bash
# Seed Beauty markets
python manage.py shell
>>> from api.market_insight_seed import seed_all
>>> seed_all(vertical='beauty', clear_existing=True)

# Or use API endpoint
curl -X POST http://localhost:8000/api/market-insight-new/seed/ \
  -H "Content-Type: application/json" \
  -d '{"vertical": "beauty", "clear_existing": true}'
```

### 4. Build Manifold

```bash
# Using management command
python manage.py rebuild_market_manifold --vertical beauty --region US

# Or use API endpoint
curl -X POST http://localhost:8000/api/market-insight-new/rebuild-manifold/ \
  -H "Content-Type: application/json" \
  -d '{"vertical": "beauty", "region": "US"}'
```

### 5. Run Server

```bash
# Backend
cd backend
python manage.py runserver

# Frontend
cd frontend
npm run dev
```

## Usage

### Accessing the Feature

1. Open the dashboard
2. Navigate to "Hypothesis Test" page
3. Select "Market Insight" from the view dropdown
4. You should see the Market Manifold Map and Insight Workspace

### Using Case Templates

**Case 1: Food Growth & Whitespace**
- Select "Case 1" from the template dropdown
- Question is pre-filled
- Click "Ask" to get analysis of:
  - Emerging functional jobs
  - Cohort differences (Gen Z vs Millennials)
  - Whitespace opportunities (jobs × formats matrix)

**Case 2: Prestige Beauty Portfolio Strategy**
- Select "Case 2" from the template dropdown
- Question is pre-filled
- Click "Ask" to get analysis of:
  - Category strategic importance
  - Tier evolution (trade up/down)
  - Competitor positioning
  - Innovation patterns
  - Launch recommendations

### Interacting with the Manifold

1. **Filter**: Use filters (category, tier, brand type, momentum) to narrow down nodes
2. **Select**: Click a node to see details in the drawer
3. **Pin**: Shift+Click to pin nodes for analysis context
4. **Hover**: Hover over nodes to see tooltips

### Asking Custom Questions

1. Select "Custom Question" template
2. Enter your question
3. Optionally pin relevant nodes for context
4. Click "Ask"
5. Review structured results with evidence and confidence scores

## Data Model

### MarketDefinition Example

```python
{
  "name": "US Prestige Skincare | Serums | Vitamin C | Premium",
  "vertical": "beauty",
  "category": "Skincare",
  "sub_category": "Vitamin C",
  "price_tier": "premium",
  "channel_mix": {"Sephora": 45, "Ulta": 25, "DTC": 30},
  "competitor_set": ["brand-id-1", "brand-id-2"],
  "tags": ["prestige", "skincare", "premium"]
}
```

### ManifoldPoint Example

```python
{
  "node_type": "market",
  "node_id": "market-uuid",
  "x": 0.234,
  "y": -0.567,
  "cluster_id": 3,
  "cluster_label": "Skincare Premium",
  "vertical": "beauty",
  "region": "US"
}
```

## API Examples

### Get Manifold

```bash
curl http://localhost:8000/api/market-insight-new/manifold/?vertical=beauty&region=US
```

### Ask Question

```bash
curl -X POST http://localhost:8000/api/market-insight-new/ask/ \
  -H "Content-Type: application/json" \
  -d '{
    "vertical": "beauty",
    "case_template": "case2",
    "question": "What categories should we prioritize?",
    "filters": {
      "selected_markets": ["market-id-1"],
      "price_tier": "super_premium"
    },
    "mock_mode": true
  }'
```

### Get Node Details

```bash
curl http://localhost:8000/api/market-insight-new/node/market/{market-id}/
```

## Mock Mode vs LLM Mode

The system supports two modes:

1. **Mock Mode** (default): Uses deterministic synthetic outputs
   - No external API calls required
   - Fast and reproducible
   - Good for demos and development

2. **LLM Mode** (future): Uses actual LLM APIs
   - Requires OpenAI API key or similar
   - More sophisticated analysis
   - Set `mock_mode: false` in API calls

## Confidence & Entropy Scoring

- **Confidence Score** (1-5): Based on evidence coverage and critic flags
- **Entropy Score** (0-1): Based on signal dispersion and uncertainty factors
- Both include plain-English rationale

## Evidence Structure

Each answer includes evidence with:
- Node references (market/brand/product IDs)
- Evidence type (synthetic_demo or real data)
- Links back to manifold nodes for defensibility

## Troubleshooting

### Manifold Not Loading

1. Check if data is seeded: `python manage.py shell` → `MarketDefinition.objects.count()`
2. Rebuild manifold: `python manage.py rebuild_market_manifold --vertical beauty`
3. Check browser console for API errors

### No Results from Ask Endpoint

1. Ensure data is seeded for the selected vertical
2. Check that filters match existing data
3. Verify API endpoint is accessible: `curl http://localhost:8000/api/market-insight-new/manifold/`

### D3 Visualization Not Rendering

1. Ensure d3 is installed: `npm install d3`
2. Check browser console for JavaScript errors
3. Verify SVG container has proper dimensions

## Future Enhancements

1. **LLM Integration**: Replace mock mode with actual LLM calls
2. **Scenario Simulation**: Implement actual what-if perturbations
3. **Real Data Integration**: Connect to actual market data sources
4. **Advanced Clustering**: Improve cluster labeling with LLM
5. **Export Functionality**: Export insights as PDF/PPT
6. **Collaboration**: Share insights and pinned nodes

## File Structure

```
backend/api/
  ├── market_insight_models.py      # Domain models
  ├── market_insight_seed.py         # Seed data generators
  ├── market_insight_manifold.py     # Manifold computation
  ├── market_insight_engine.py       # Insight orchestration
  ├── market_insight_views.py        # API endpoints
  └── management/commands/
      └── rebuild_market_manifold.py # Management command

frontend/src/components/
  ├── market-insight/
  │   ├── MarketManifoldMap.jsx     # D3 visualization
  │   └── InsightWorkspace.jsx      # Question/answer UI
  └── hypothesis/
      └── MarketInsightPanel.jsx     # Main panel
```

## Testing

### Unit Tests (TODO)

```python
# Test manifold building
def test_manifold_build():
    builder = ManifoldBuilder(vertical='beauty')
    points = builder.build_manifold()
    assert points.count() > 0

# Test insight engine
def test_case2_analysis():
    engine = InsightEngine(mock_mode=True)
    result = engine.answer_question(
        question="What categories to prioritize?",
        case_template="case2",
        vertical="beauty"
    )
    assert 'executive_summary' in result
    assert 'confidence' in result
```

## Performance Notes

- Manifold building: ~5-10 seconds for 50-100 nodes
- Embeddings cached in ManifoldPoint table
- Use `force_rebuild=False` for cached results
- Consider background task for large manifolds

## License

Part of the Louiza Dashboard project.
