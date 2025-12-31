# Chatbot Setup Guide

## Overview

The dashboard includes an AI-powered chatbot that can answer questions about insights, data patterns, and behavioral trends. The chatbot reads all dashboard data as context and provides conversational insights.

## Setup

### Option 1: OpenAI (Recommended)

1. Get an OpenAI API key from https://platform.openai.com/api-keys
2. Set the environment variable:
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```
3. The chatbot will use `gpt-4o-mini` by default (cost-effective)

### Option 2: Anthropic Claude

1. Get an Anthropic API key from https://console.anthropic.com/
2. Set the environment variable:
   ```bash
   export ANTHROPIC_API_KEY="your-api-key-here"
   ```
3. Update the chatbot initialization in `app.py`:
   ```python
   st.session_state.chatbot = DashboardChatbot(
       data=data,
       insights=insights_list,
       use_openai=False,  # Use Anthropic instead
       model="claude-3-haiku-20240307"
   )
   ```

## Usage

1. **Start the dashboard**:
   ```bash
   streamlit run app.py
   ```

2. **Access the chatbot**: The chatbot appears in the right sidebar

3. **Ask questions**: Type questions like:
   - "What are the key insights from the data?"
   - "Which segment has the highest intent?"
   - "What are the top product categories?"
   - "How does intent change over time?"
   - "What is the price sensitivity?"
   - "Which categories show strong momentum?"

4. **Use suggested questions**: Click on suggested questions for quick insights

5. **Reset conversation**: Click "Reset Conversation" to start fresh

## Features

- **Context-Aware**: Reads all dashboard data (products, segments, trajectories, insights)
- **Conversational**: Maintains conversation history for context
- **Insight Summarization**: Can summarize auto-generated insights
- **Data Analysis**: Answers questions about metrics, trends, and patterns
- **Business Insights**: Explains metrics in business terms

## Data Context

The chatbot has access to:
- Products metadata (categories, ingredients, nutrition, price)
- User segments (age, region, psychographics)
- Behavioral trajectories (intent over time)
- Phase 4 anchored data (calibrated results)
- Intent index signals
- Momentum signals
- Auto-generated insights

## Example Questions

- "What are the key insights from the data?"
- "Which segment has the highest intent?"
- "What are the top product categories?"
- "How does intent change over time?"
- "What is the price sensitivity?"
- "Which categories show strong momentum?"
- "What are the substitution patterns?"
- "How does context affect intent?"
- "What is the repeat purchase rate?"
- "Compare Phase 3 vs Phase 4 results"

## Troubleshooting

### "LLM API not configured"
- Set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` environment variable
- Restart the Streamlit app after setting the variable

### "Error: Invalid API key"
- Check that your API key is correct
- Ensure you have credits/quota available
- For OpenAI, check https://platform.openai.com/usage

### Chatbot not responding
- Check your internet connection
- Verify API key is set correctly
- Check API rate limits/quota

### No suggested questions
- Ensure data is loaded
- Select at least one segment in the sidebar
- Wait for insights to be generated

## Cost Considerations

- **OpenAI gpt-4o-mini**: ~$0.15 per 1M input tokens, ~$0.60 per 1M output tokens
- **Anthropic Claude Haiku**: ~$0.25 per 1M input tokens, ~$1.25 per 1M output tokens

Typical conversation uses ~500-1000 tokens per exchange.

