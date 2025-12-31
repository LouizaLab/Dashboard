# Hypothesis Testing Feature - Implementation Summary

## Architecture Overview

### Backend (Django + DRF)
- **Models**: `PersonaAgent`, `SurveyQuestion`, `SurveyResponse`, `HypothesisRun`, `EvidenceSurveyDatum`
- **Services**: GPT integration with mock fallback (`services.py`)
- **API Endpoints**:
  - `GET /api/agents/` - List/filter agents
  - `GET /api/agents/<id>/` - Get agent details
  - `POST /api/hypothesis/run/` - Run hypothesis test
  - `POST /api/survey/run/` - Run survey on agents
  - `GET /api/survey/questions/` - List survey questions
  - `POST /api/taste_test/run/` - Run taste test
  - `POST /api/chat/chat/` - Chat with agent

### Frontend (React + Tailwind)
- **Main Page**: `HypothesisPage.jsx`
- **Components**:
  - `LeftFilters.jsx` - Filters sidebar (year, demographics, archetype, agent count, GPT toggle)
  - `HypothesisInput.jsx` - Input bar for hypothesis questions
  - `ResultsPanel.jsx` - Results display (summary, segments, evidence, charts)
  - `AgentDrawer.jsx` - Right drawer for agent interactions
  - `ChatPanel.jsx` - Chat interface
  - `SurveyPanel.jsx` - Survey runner
  - `TasteTestPanel.jsx` - Taste test runner
  - `NetworkBackground.jsx` - Subtle network graph background

## Setup Instructions

### 1. Backend Setup

```bash
cd fastfood_network_demo/backend

# Activate virtual environment
source .venv/bin/activate  # or .venv\Scripts\activate on Windows

# Install new dependency
pip install openai

# Create and run migrations
python manage.py makemigrations
python manage.py migrate

# Seed hypothesis data
python manage.py seed_hypothesis_demo

# Start server
python manage.py runserver
```

### 2. Frontend Setup

```bash
cd fastfood_network_demo/frontend

# Install dependencies (if not already done)
npm install

# Start dev server
npm run dev
```

### 3. GPT Integration (Optional)

To enable GPT mode:
```bash
export OPENAI_API_KEY="your-api-key-here"
# or
export OPENAI_KEY="your-api-key-here"
```

If no API key is set, the system automatically uses mock mode (deterministic responses).

## Demo Flow

### 1. Run a Hypothesis Test

1. Click "TEST HYPOTHESIS" tab
2. Adjust filters in left sidebar:
   - Year slider (2020-2025)
   - Demographics (age, gender, region, income)
   - Behavioral Archetype
   - Agent Count (10-150)
   - Toggle "Use GPT" if you have API key
3. Type hypothesis in input bar:
   - Example: "Will McDonald's foot traffic increase if Gen Z sees a high-protein campaign?"
   - Example: "Which brand benefits most from late-night cravings in the Midwest?"
4. Click send (→ icon)
5. View results:
   - Summary outcome (sentiment, confidence, agent count)
   - Top drivers (themes)
   - Segment differences (breakdown by demographics/archetype)
   - Response distribution chart
   - Evidence from "real surveys" (3-5 snippets)
   - Recommended follow-up questions

### 2. Chat with an Agent

1. After running a hypothesis, click on an agent from results (if available)
2. Or manually select an agent
3. In the drawer, click "Chat" tab
4. Type messages and have a conversation
5. Responses are generated based on agent's persona

### 3. Run a Survey

1. Open agent drawer → "Survey" tab
2. Select questions from the list (checkboxes)
3. Click "Run Survey"
4. View aggregated results per question:
   - Average scores (for Likert)
   - Distribution (for multiple choice)
   - Response counts

### 4. Run a Taste Test

1. Open agent drawer → "Taste Test" tab
2. Add/remove items to compare (default: McDonald's, Burger King, Chipotle, Taco Bell)
3. Click "Run Taste Test"
4. View rankings:
   - Items ranked by preference score
   - Visual bars showing scores
   - Response counts

## Key Features

### Agent System
- 150 persona agents with:
  - Demographics (age, gender, region, income)
  - Behavioral archetypes (7 types)
  - Taste profiles (tags)
  - Behavior parameters (price sensitivity, health bias, etc.)
  - GPT system prompts for realistic responses

### Behavioral Archetypes
1. **Value Seeker** - Price-focused, deal-hunting
2. **Health Optimizer** - Nutrition and ingredients matter
3. **Convenience Loyalist** - Speed and reliability
4. **Late-night Craver** - Late-night ordering patterns
5. **Trend Chaser** - Tries new items, follows trends
6. **Family Bundle Buyer** - Value and variety for families
7. **Protein Maximizer** - Protein content priority

### Evidence System
- 200 dummy "real survey" snippets
- Aligned with archetypes and regions
- Includes distribution data and metadata
- Shown alongside simulation results for credibility

### GPT Integration
- Uses OpenAI GPT-4o-mini for realistic responses
- Falls back to deterministic mock mode if no API key
- Efficient: aggregates responses rather than calling GPT 100+ times
- Rate limiting and error handling built-in

## File Structure

```
fastfood_network_demo/
├── backend/
│   ├── api/
│   │   ├── sim_models.py          # Hypothesis models
│   │   ├── sim_views.py           # Hypothesis API views
│   │   ├── sim_serializers.py    # Hypothesis serializers
│   │   ├── survey_views.py      # Survey question views
│   │   ├── services.py           # GPT + mock service
│   │   └── management/commands/
│   │       └── seed_hypothesis_demo.py
├── frontend/
│   └── src/
│       └── components/
│           ├── HypothesisPage.jsx
│           └── hypothesis/
│               ├── LeftFilters.jsx
│               ├── HypothesisInput.jsx
│               ├── ResultsPanel.jsx
│               ├── AgentDrawer.jsx
│               ├── ChatPanel.jsx
│               ├── SurveyPanel.jsx
│               ├── TasteTestPanel.jsx
│               └── NetworkBackground.jsx
```

## Notes

- All data is deterministically seeded (seed=42) for consistency
- Mock mode works without any API keys
- GPT mode requires OpenAI API key in environment
- Network background is subtle and non-interactive
- All components use dark theme matching the screenshot style

