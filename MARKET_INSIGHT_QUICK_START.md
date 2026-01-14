# Market Insight Quick Start

## Quick Setup (5 minutes)

### 1. Install Dependencies

```bash
# Backend
cd backend
pip install sentence-transformers umap-learn scikit-learn  # Optional but recommended

# Frontend  
cd frontend
npm install d3
```

### 2. Create Migrations & Migrate

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

### 3. Seed Data

```bash
python manage.py shell
```

```python
from api.market_insight_seed import seed_all
seed_all(vertical='beauty', clear_existing=True)
```

### 4. Build Manifold

```bash
python manage.py rebuild_market_manifold --vertical beauty --region US
```

### 5. Start Servers

```bash
# Terminal 1: Backend
cd backend
python manage.py runserver

# Terminal 2: Frontend
cd frontend
npm run dev
```

### 6. Access Feature

1. Open http://localhost:5173 (or your frontend port)
2. Navigate to "Hypothesis Test" page
3. Select "Market Insight" from view dropdown
4. You should see the Market Manifold Map!

## Testing the Feature

### Test Case 2 (Beauty Portfolio Strategy)

1. In the Insight Workspace (right panel), ensure "Case 2" is selected
2. Click "Ask" button
3. You should see structured results with:
   - Executive summary
   - Category importance analysis
   - Tier analysis
   - Competitor positioning
   - Recommended actions
   - Confidence & entropy scores
   - Evidence links

### Test Manifold Interaction

1. Use filters (category, price tier) to narrow nodes
2. Click a node to see details in the drawer
3. Shift+Click to pin nodes
4. Hover to see tooltips

## Troubleshooting

**Manifold not showing?**
- Check if data exists: `MarketDefinition.objects.count()` in shell
- Rebuild manifold: `python manage.py rebuild_market_manifold --vertical beauty`

**API errors?**
- Check backend is running: `curl http://localhost:8000/api/market-insight-new/manifold/`
- Check CORS settings if frontend can't reach backend

**D3 not rendering?**
- Ensure d3 is installed: `npm list d3`
- Check browser console for errors

## Next Steps

- Try Case 1 (Food) by seeding food data and switching vertical
- Pin multiple nodes and ask custom questions
- Explore different filters and clusters
- Review evidence links back to manifold nodes

For full documentation, see `MARKET_INSIGHT_IMPLEMENTATION.md`.
