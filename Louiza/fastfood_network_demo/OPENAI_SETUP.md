# OpenAI API Key Setup Guide

This guide will help you set up the OpenAI API key so that agents can use GPT for realistic responses.

## Step 1: Get Your OpenAI API Key

1. Go to [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in or create an account
3. Click "Create new secret key"
4. Copy the key (you won't be able to see it again!)

## Step 2: Set Up the API Key

### Option A: Using .env file (Recommended)

1. Copy the example file:
   ```bash
   cd fastfood_network_demo/backend
   cp .env.example .env
   ```

2. Edit `.env` and add your API key:
   ```bash
   OPENAI_API_KEY=sk-your-actual-api-key-here
   ```

3. The `.env` file is already in `.gitignore`, so your key won't be committed.

### Option B: Using Environment Variables

**macOS/Linux:**
```bash
export OPENAI_API_KEY="sk-your-actual-api-key-here"
```

**Windows (PowerShell):**
```powershell
$env:OPENAI_API_KEY="sk-your-actual-api-key-here"
```

**Windows (Command Prompt):**
```cmd
set OPENAI_API_KEY=sk-your-actual-api-key-here
```

### Option C: Using OPENAI_KEY (Alternative)

You can also use `OPENAI_KEY` instead of `OPENAI_API_KEY`:
```bash
export OPENAI_KEY="sk-your-actual-api-key-here"
```

## Step 3: Install Dependencies

Make sure you have the required packages:
```bash
cd fastfood_network_demo/backend
source .venv/bin/activate  # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

## Step 4: Verify Setup

1. Start the backend server:
   ```bash
   python manage.py runserver
   ```

2. Check the console output. You should see:
   - `✓ OpenAI client initialized successfully` if the key is set correctly
   - `⚠ OPENAI_API_KEY not set. GPT mode will use mock responses.` if not set

## Step 5: Use GPT Mode in the UI

1. Open the frontend: `http://localhost:5173`
2. Go to **TEST HYPOTHESIS** tab
3. In the left sidebar, toggle **"Use GPT"** to ON
4. Now when you:
   - **Chat with agents**: Uses GPT-4o with custom persona prompts for each agent
   - **Run hypothesis tests**: Agents respond based on their archetypes and demographics
   - **Run surveys**: Authentic survey responses from each persona
   - **Run taste tests**: Preference rankings based on persona traits
   
   The agents will use GPT-4o to generate realistic, persona-specific responses!

### Chatting with Agents

1. Click on any agent in the grid to open their drawer
2. Go to the **"Chat"** tab
3. Make sure **"Use GPT"** toggle is ON in the left sidebar
4. Start chatting! Each agent will respond as their persona:
   - **Value Seeker**: Talks about deals, prices, and value
   - **Health Optimizer**: Focuses on nutrition and ingredients
   - **Late-night Craver**: Mentions late-night ordering habits
   - And so on for each archetype...

## Troubleshooting

### "OpenAI package not installed"
```bash
pip install openai
```

### "OPENAI_API_KEY not set"
- Make sure you've set the environment variable or created the `.env` file
- Restart the Django server after setting the variable
- Check that the `.env` file is in `backend/` directory

### "Failed to initialize OpenAI client"
- Verify your API key is correct
- Check your OpenAI account has credits/billing set up
- Make sure you're using a valid API key format (starts with `sk-`)

### "Rate limit exceeded"
- You've hit OpenAI's rate limits
- Wait a few minutes or upgrade your OpenAI plan
- The system will automatically fall back to mock responses

### GPT responses not working
- Make sure "Use GPT" toggle is ON in the UI
- Check backend console for error messages
- Verify the API key is being loaded (check startup logs)

## Cost Considerations

- GPT-4o-mini is used (cost-effective model)
- Each agent response uses ~100-300 tokens
- For 100 agents: ~10,000-30,000 tokens per hypothesis test
- Monitor your usage at [OpenAI Usage Dashboard](https://platform.openai.com/usage)

## Security Notes

- **Never commit your API key to git**
- The `.env` file is already in `.gitignore`
- Use environment variables in production
- Rotate your API keys regularly

## Testing Without API Key

If you don't have an API key or want to test without costs:
- Leave the toggle OFF (mock mode)
- Agents will use deterministic mock responses
- All features work, just with simulated responses

