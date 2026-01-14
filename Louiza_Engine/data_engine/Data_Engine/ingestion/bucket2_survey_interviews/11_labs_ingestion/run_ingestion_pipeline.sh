#!/bin/bash
# Run the complete 11 Labs ingestion pipeline
# This script runs both the fetcher and watcher together

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

cd "$REPO_ROOT"

echo "=========================================="
echo "11 Labs Ingestion Pipeline"
echo "=========================================="
echo ""

# Check for API key
if [ -z "$ELEVENLABS_API_KEY" ]; then
    echo "ERROR: ELEVENLABS_API_KEY not set"
    echo "Set it with: export ELEVENLABS_API_KEY='your-key-here'"
    exit 1
fi

# Check if watchdog is installed
if ! python3 -c "import watchdog" 2>/dev/null; then
    echo "Installing watchdog library..."
    pip install watchdog
fi

echo "Step 1: Fetching new transcripts..."
echo "-----------------------------------"
python3 "$SCRIPT_DIR/fetch_to_incoming.py"

echo ""
echo "Step 2: Starting file watcher..."
echo "-----------------------------------"
echo "The watcher will monitor for new files."
echo "Press Ctrl+C to stop."
echo ""

# Run watcher (this will run until interrupted)
python3 "$SCRIPT_DIR/watch_incoming.py"

