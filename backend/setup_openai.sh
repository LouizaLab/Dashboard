#!/bin/bash
# Quick setup script for OpenAI API key

echo "🔑 OpenAI API Key Setup"
echo "======================"
echo ""
echo "This script will help you set up your OpenAI API key."
echo ""

# Check if .env exists
if [ -f .env ]; then
    echo "⚠️  .env file already exists."
    read -p "Do you want to overwrite it? (y/N): " overwrite
    if [[ ! $overwrite =~ ^[Yy]$ ]]; then
        echo "Keeping existing .env file."
        exit 0
    fi
fi

# Get API key from user
read -p "Enter your OpenAI API key (or press Enter to skip): " api_key

if [ -z "$api_key" ]; then
    echo "⚠️  No API key provided. GPT mode will use mock responses."
    echo "You can set it later by:"
    echo "  export OPENAI_API_KEY='your-key-here'"
    echo "  or edit backend/.env file"
    exit 0
fi

# Create .env file
cat > .env << EOF
# OpenAI API Configuration
# Get your API key from: https://platform.openai.com/api-keys
OPENAI_API_KEY=$api_key
EOF

echo ""
echo "✅ .env file created successfully!"
echo ""
echo "To verify, restart your Django server and check for:"
echo "  ✓ OpenAI client initialized successfully"
echo ""
echo "To use GPT mode:"
echo "  1. Toggle 'Use GPT' switch ON in the TEST HYPOTHESIS tab"
echo "  2. Agents will now use GPT for realistic responses"
echo ""

