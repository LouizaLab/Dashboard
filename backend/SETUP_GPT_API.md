# Setting Up GPT API for Market Insight

The Market Insight feature can use GPT-4 to generate consultant-grade insights from simulation results.

## Quick Setup

1. **Get your OpenAI API key** from https://platform.openai.com/api-keys

2. **Set the API key** in one of these ways:

   **Option A: Environment variable (recommended)**
   ```bash
   export OPENAI_API_KEY=sk-your-key-here
   ```

   **Option B: Create backend/.env file**
   ```bash
   cd backend
   echo "OPENAI_API_KEY=sk-your-key-here" >> .env
   ```

3. **Restart the Django server** to load the new environment variable

4. **Verify it's working** - Check the server logs when starting. You should see:
   ```
   ✓ OpenAI client initialized successfully (GPT-4o ready for agent chat)
   ```

## Using GPT Mode

By default, the system will **auto-detect** whether to use GPT or mock mode:
- If `OPENAI_API_KEY` is set and valid → uses GPT-4
- Otherwise → uses mock mode (deterministic synthetic responses)

### Force GPT Mode

You can force GPT mode even if auto-detection fails:

**Via environment variable:**
```bash
export MARKET_INSIGHT_MODE=gpt
```

**Via API request** (add to request body or query param):
```json
{
  "question": "...",
  "force_gpt": true
}
```

### Bypass Cache

To force fresh GPT responses (bypass cache):

```bash
export MARKET_INSIGHT_BYPASS_CACHE=true
```

Or add to request:
```json
{
  "question": "...",
  "force_gpt": true
}
```

## Testing

1. Start the Django server:
   ```bash
   cd backend
   python3 manage.py runserver
   ```

2. Submit a question in the Market Insight tab

3. Check server logs - you should see:
   ```
   [Market Insight] Using GPT-4 API (model: gpt-4o)
   [Market Insight] GPT-4 response generated successfully (tokens: XXX)
   ```

## Troubleshooting

**"Using mock mode" message:**
- Check that `OPENAI_API_KEY` is set: `echo $OPENAI_API_KEY`
- Verify the key is valid (starts with `sk-`)
- Restart the Django server after setting the key

**"GPT-4 error" messages:**
- Check your API key is valid and has credits
- Check OpenAI API status: https://status.openai.com/
- Review error details in server logs

**Still using cached results:**
- Set `MARKET_INSIGHT_BYPASS_CACHE=true` to bypass cache
- Or clear Django cache: `python3 manage.py shell` → `from django.core.cache import cache; cache.clear()`
