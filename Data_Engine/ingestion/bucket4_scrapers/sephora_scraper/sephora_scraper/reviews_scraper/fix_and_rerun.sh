#!/bin/bash
# Delete old CSV and rerun scraper with fixes

echo "Deleting old CSV file..."
rm -f Output/product_reviews.csv

echo "Running scraper with product name extraction..."
python3 reviews_scraper.py

echo "Done! Check Output/product_reviews.csv for results with product_name column."



