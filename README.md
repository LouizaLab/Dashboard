Django Full scale update


To Do:
1. Scale frontend and backend
2. Scale to the cloud



Run the seed command to create demo agents:

```bash
cd backend
python manage.py seed_hypothesis_demo
```

This will create:
- **150 agents** by default (or specify `--agents 500` for more)
- **20 survey questions**
- **200 evidence snippets**

## Verify Agents Were Created

After running the seed command, you should see:
```
Creating persona agents...
  Created 150 agents
Creating survey questions...
  Created 20 survey questions
Creating evidence survey data...
  Created 200 evidence snippets

Successfully seeded hypothesis demo data!
  Agents: 150
  Survey questions: 20
  Evidence snippets: 200
```

## Check in Browser

1. Refresh the Hypothesis Test tab
2. You should now see agents displayed in the grid
3. Agents are grouped by archetype (Value Seeker, Health Optimizer, etc.)

## Troubleshooting

### Still No Agents?

1. **Check API endpoint:**
   ```bash
   curl http://localhost:8000/api/agents/
   ```
   Should return a list of agents (or empty array `[]`)

2. **Check browser console:**
   - Open DevTools (F12)
   - Look for errors in Console tab
   - Check Network tab for `/api/agents/` request

3. **Check filters:**
   - Make sure no filters are applied (they might filter out all agents)
   - Clear all filters in the left panel

4. **Check database:**
   ```bash
   cd backend
   python manage.py shell
   ```
   Then:
   ```python
   from api.sim_models import PersonaAgent
   print(f"Total agents: {PersonaAgent.objects.count()}")
   ```

### Create More Agents

To create more agents:
```bash
python manage.py seed_hypothesis_demo --agents 500
```

### Reset Agents

To delete all agents and recreate:
```bash
python manage.py shell
```
Then:
```python
from api.sim_models import PersonaAgent
PersonaAgent.objects.all().delete()
exit()
```
Then run seed command again.

## Agent Details

Agents are created with:
- **7 archetypes**: value_seeker, health_optimizer, convenience_loyalist, late_night_craver, trend_chaser, family_bundle_buyer, protein_maximizer
- **5 age buckets**: 18-24, 25-34, 35-44, 45-54, 55+
- **4 genders**: Male, Female, Nonbinary, Prefer not to say
- **4 regions**: West, Midwest, South, Northeast
- **4 income levels**: $0-50k, $50-100k, $100-150k, $150k+
- **Random taste profiles**: spicy, sweet, savory, crispy, etc.
- **Behavioral parameters**: price_sensitivity, health_bias, brand_loyalty, etc.

## API Endpoint

The agents are served via:
- `GET /api/agents/` - List all agents (with optional filters)
- `GET /api/agents/{id}/` - Get specific agent
- `GET /api/agents/network/` - Get network graph data

Query parameters:
- `age_bucket` - Filter by age
- `gender` - Filter by gender
- `region` - Filter by region
- `income` - Filter by income
- `archetype` - Filter by archetype
- `limit` - Limit number of results (default: 100)

Example:
```
GET /api/agents/?archetype=health_optimizer&limit=50
```

