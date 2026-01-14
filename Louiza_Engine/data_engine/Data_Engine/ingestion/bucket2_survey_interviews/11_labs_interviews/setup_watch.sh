#!/bin/bash
# Setup script to start watching for new 11 Labs interviews

# Configuration
WATCH_DIR="${1:-$HOME/Downloads/11labs_interviews}"  # Default: Downloads/11labs_interviews
TARGET_DIR="$(dirname "$0")"
MIN_DURATION=10

echo "=========================================="
echo "11 Labs Interview Auto-Importer Setup"
echo "=========================================="
echo ""
echo "Watch directory: $WATCH_DIR"
echo "Target folder: $TARGET_DIR"
echo "Minimum duration: $MIN_DURATION minutes"
echo ""

# Create watch directory if it doesn't exist
mkdir -p "$WATCH_DIR"
echo "✓ Created watch directory: $WATCH_DIR"
echo ""

# Check if Python dependencies are installed
echo "Checking dependencies..."
if ! python3 -c "import watchdog" 2>/dev/null; then
    echo "⚠️  Installing watchdog..."
    pip3 install watchdog
fi
echo "✓ Dependencies OK"
echo ""

# Start the watcher
echo "Starting file watcher..."
echo "Press Ctrl+C to stop"
echo ""

python3 "$TARGET_DIR/auto_import.py" \
    --watch "$WATCH_DIR" \
    --target "$TARGET_DIR" \
    --min-duration "$MIN_DURATION"




