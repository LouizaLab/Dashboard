# Fast-Food Network Dashboard Demo

A demo-ready interactive network dashboard for fast-food companies showing the relationship between behavioral synthetic data and quant data (foot traffic, revenue) over time.

## Architecture

- **Backend**: Django + Django REST Framework (DRF)
- **Frontend**: React (Vite) + Tailwind CSS (dark UI)
- **Network Graph**: Cytoscape.js (interactive nodes/edges)
- **Charts**: ECharts (time-series plots)

## Features

- Interactive network graph with 7 fast-food companies
- Time-series charts comparing quant data vs behavioral indices
- Edge details with weight matrices and factor breakdowns
- Demographics filtering (Age, Income, Region)
- Multiple view modes (Market Insight, Foot Traffic, Revenue, Intent, Taste Dynamics)
- Simulation panel for demo scenarios

## Quick Start

### Prerequisites

- Python 3.8+
- Node.js 16+
- npm or yarn

### Backend Setup

```bash
cd fastfood_network_demo/backend

# Create virtual environment
python -m venv .venv

# Activate virtual environment
# On macOS/Linux:
source .venv/bin/activate
# On Windows:
# .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Seed demo data
python manage.py seed_demo

# Seed hypothesis testing data (agents, surveys, evidence)
python manage.py seed_hypothesis_demo

# Start development server
python manage.py runserver
```

The backend will be available at `http://localhost:8000`

### Frontend Setup

```bash
cd fastfood_network_demo/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

The frontend will be available at `http://localhost:5173`

## API Endpoints

- `GET /api/companies/` - List all companies
- `GET /api/companies/<id>/` - Get company details with KPIs
- `GET /api/companies/<id>/timeseries/?metric=<metric>&start=<date>&end=<date>` - Get time series data
- `GET /api/network/?view=<view_type>&filters=...` - Get network graph data (Cytoscape format)
- `GET /api/edges/<id>/` - Get edge details
- `GET /api/compare/?a=<company_id>&b=<company_id>&metric=<metric>` - Compare two companies

## Usage

1. Start both backend and frontend servers
2. Open `http://localhost:5173` in your browser
3. Click on nodes (companies) to view details and time-series charts
4. Click on edges to see relationship details and matrices
5. Use sidebar filters to adjust the view
6. Try different view modes from the "VIEW" dropdown
7. Use simulation buttons at the bottom to activate demo scenarios

## Project Structure

```
fastfood_network_demo/
├── backend/
│   ├── api/
│   │   ├── models.py          # Django models
│   │   ├── serializers.py     # DRF serializers
│   │   ├── views.py           # API views
│   │   ├── urls.py            # URL routing
│   │   └── management/
│   │       └── commands/
│   │           └── seed_demo.py  # Data seeding command
│   ├── network_demo/
│   │   ├── settings.py        # Django settings
│   │   └── urls.py            # Root URL config
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── TopNavigation.jsx
│   │   │   ├── Sidebar.jsx
│   │   │   ├── NetworkGraph.jsx
│   │   │   ├── DetailDrawer.jsx
│   │   │   └── SimulationPanel.jsx
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── index.css
│   ├── package.json
│   └── vite.config.js
└── README.md
```

## Demo Data

The seed command creates:
- 7 fast-food companies (McDonald's, Burger King, Wendy's, Taco Bell, KFC, Chipotle, Subway)
- 90 days of time-series data per company (foot traffic, revenue, intent index, taste index, sentiment)
- Edges between companies with weights, matrices, and factor breakdowns

All data is deterministically generated using seeded random numbers for consistency.

## Hypothesis Testing Feature

The TEST HYPOTHESIS tab provides a simulation system with 100+ persona agents that can:

- **Run hypothesis tests** on demographics + behavioral archetypes
- **Answer surveys** and return aggregated results
- **Direct chat** with selected personas
- **Run taste tests** comparing different brands/products
- **Show evidence** from "real survey dataset" (dummy but realistic)

### Demo Flow:

1. **Run a Hypothesis:**
   - Click "TEST HYPOTHESIS" tab
   - Type a hypothesis like: "Will McDonald's foot traffic increase if Gen Z sees a high-protein campaign?"
   - Adjust filters (demographics, archetype, agent count)
   - Click send (→ icon)
   - View results: summary, top drivers, segment differences, evidence

2. **Chat with an Agent:**
   - Click on an agent from results (if available)
   - Or select an agent from the agent list
   - Open "Chat" tab in drawer
   - Have a conversation with the persona

3. **Run a Survey:**
   - Open agent drawer → "Survey" tab
   - Select questions (checkboxes)
   - Click "Run Survey"
   - View aggregated results per question

4. **Run a Taste Test:**
   - Open agent drawer → "Taste Test" tab
   - Add/remove items to compare
   - Click "Run Taste Test"
   - View rankings and preference scores

### GPT Integration:

- Set `OPENAI_API_KEY` environment variable to enable GPT mode
- Toggle "Use GPT" switch in filters to switch between GPT and mock mode
- Mock mode works without API key (deterministic responses)
- **See [OPENAI_SETUP.md](OPENAI_SETUP.md) for detailed setup instructions**

## Notes

- CORS is enabled for all origins (demo only - restrict in production)
- No authentication required (demo only)
- Database uses SQLite (easy to reset: delete `db.sqlite3` and rerun migrations + seed)
- GPT integration is optional - mock mode works without API key

