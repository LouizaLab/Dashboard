# Sephora Reviews Scraper

This scraper extracts customer reviews from Sephora products using the Bazaarvoice API.

## Configuration

### 1. Proxy Settings (Optional)

If you need to use a proxy, edit `reviews_scraper.py` and update the `make_request()` function:

```python
proxy = 'http://your-proxy-server:port'  # e.g., 'http://proxy.example.com:8080'
# Or with authentication:
proxy = 'http://username:password@proxy.example.com:8080'
```

If you don't need a proxy, leave it as `None` (already configured).

### 2. Product IDs

Add Sephora product IDs to `product_ids.txt`, one per line. Example:
```
P399755
P444614
P460622
P505392
```

To find product IDs:
1. Go to a Sephora product page
2. Look at the URL: `https://www.sephora.com/product/product-name-P399755`
3. The product ID is the part after the last `-` (e.g., `P399755`)

## Running the Scraper

```bash
cd sephora_scraper/reviews_scraper
python3 reviews_scraper.py
```

## Output

The scraper will create an `Output/` folder with `product_reviews.csv` containing all the scraped reviews.

## Notes

- The scraper uses threading for faster data collection
- It automatically handles pagination (multiple pages of reviews)
- Reviews are saved incrementally to avoid data loss




