#!/bin/bash
# Quick setup script for ElevenLabs API key

echo "=========================================="
echo "ElevenLabs API Key Setup"
echo "=========================================="
echo ""
echo "1. Go to: https://elevenlabs.io/app/settings/api-keys"
echo "2. Sign in and create/copy your API key"
echo ""
read -sp "3. Paste your API key here: " API_KEY
echo ""
echo ""

if [ -z "$API_KEY" ]; then
    echo "❌ No API key provided. Exiting."
    exit 1
fi

# Detect shell
if [ -n "$ZSH_VERSION" ]; then
    SHELL_FILE="$HOME/.zshrc"
elif [ -n "$BASH_VERSION" ]; then
    SHELL_FILE="$HOME/.bashrc"
else
    SHELL_FILE="$HOME/.profile"
fi

# Check if already exists
if grep -q "ELEVENLABS_API_KEY" "$SHELL_FILE" 2>/dev/null; then
    echo "⚠️  API key already exists in $SHELL_FILE"
    read -p "Replace it? (y/n): " REPLACE
    if [ "$REPLACE" != "y" ]; then
        echo "Keeping existing key."
        exit 0
    fi
    # Remove old line
    sed -i.bak '/ELEVENLABS_API_KEY/d' "$SHELL_FILE"
fi

# Add to shell file
echo "" >> "$SHELL_FILE"
echo "# ElevenLabs API Key" >> "$SHELL_FILE"
echo "export ELEVENLABS_API_KEY=\"$API_KEY\"" >> "$SHELL_FILE"

echo "✅ API key added to $SHELL_FILE"
echo ""
echo "Reloading shell configuration..."
source "$SHELL_FILE"

echo ""
echo "✅ Setup complete!"
echo ""
echo "Test it with:"
echo "  python scripts/fetch_transcripts.py"
echo ""
echo "Or verify the key is set:"
echo "  echo \$ELEVENLABS_API_KEY"

