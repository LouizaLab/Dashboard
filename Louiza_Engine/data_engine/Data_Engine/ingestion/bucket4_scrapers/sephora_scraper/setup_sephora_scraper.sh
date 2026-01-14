#!/bin/bash

# Setup script for Sephora scraper
# This script clones the repository and sets it up in the correct location

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_URL="https://github.com/nadyinky/sephora-analysis.git"
TEMP_DIR="/tmp/sephora-analysis-$$"

echo "=========================================="
echo "Setting up Sephora Scraper"
echo "=========================================="

# Clone repository to temp location
echo "Cloning repository..."
git clone "$REPO_URL" "$TEMP_DIR"

# Copy sephora_scraper folder to our location
if [ -d "$TEMP_DIR/sephora_scraper" ]; then
    echo "Copying scraper files..."
    cp -r "$TEMP_DIR/sephora_scraper"/* "$SCRIPT_DIR/"
    
    # Create data directory if it doesn't exist
    mkdir -p "$SCRIPT_DIR/data"
    
    echo "✓ Setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Install dependencies: pip install -r requirements.txt"
    echo "2. Run the scraper scripts in order:"
    echo "   - python scrape_brand_links.py"
    echo "   - python scrape_product_links.py"
    echo "   - python scrape_product_info.py"
    echo "   - python scrape_reviews.py"
    echo "   - python parse_reviews.py"
else
    echo "Error: sephora_scraper folder not found in repository"
    exit 1
fi

# Cleanup
rm -rf "$TEMP_DIR"

echo ""
echo "Setup complete! Files are in: $SCRIPT_DIR"




