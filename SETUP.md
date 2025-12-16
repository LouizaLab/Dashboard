# Setup Guide

## First Time Setup

1. **Virtual Environment** (already created)
   - Located at: `venv/`
   - All dependencies are installed

## Running the App

The app is configured to run with auto-reload enabled. To start it:

```bash
# Activate virtual environment
source venv/bin/activate

# Run the app
streamlit run app.py
```

The app will automatically open in your browser at `http://localhost:8501`

## Auto-Reload

Streamlit automatically reloads when you make changes to:
- `app.py` (main dashboard file)
- Any files in `src/dashboard/` directory
- Data files (may require manual refresh)

Just save your changes and the app will refresh automatically!

## Optional: Chatbot Setup

If you want to use the AI chatbot feature, set an API key:

```bash
export OPENAI_API_KEY="your-key-here"
# OR
export ANTHROPIC_API_KEY="your-key-here"
```

The app will work without the chatbot - it's optional.

## Troubleshooting

- If the app doesn't start, check that port 8501 is available
- If you see import errors, make sure the virtual environment is activated
- To stop the app, press `Ctrl+C` in the terminal

