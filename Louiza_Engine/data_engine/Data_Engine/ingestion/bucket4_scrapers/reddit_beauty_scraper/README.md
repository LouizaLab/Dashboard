# Reddit Beauty Trends Scraper

Scrapes old.reddit.com to identify **emerging beauty trends** before they become mainstream. Focuses on **early signals**, not raw popularity.

## Features

- ✅ **No API Required** - Uses web scraping on old.reddit.com
- ✅ **Early Signal Detection** - Identifies trends with low baseline but rapid growth
- ✅ **Language Shift Detection** - Tracks new terminology and phrase evolution
- ✅ **Pain Point Clustering** - Identifies unmet consumer needs
- ✅ **Modular Architecture** - Easy to extend and maintain

## Architecture

```
reddit_scraper/
├── scraper.py          # Web scraping (old.reddit.com)
├── trend_extractor.py  # Trend detection & entity extraction
├── scorer.py          # Trend scoring & ranking
├── output.py          # CSV/JSON/Markdown export
└── main.py            # Main execution script
```

## Usage

```bash
cd reddit_scraper
python3 main.py
```

## What It Scrapes

### Subreddits
- r/SkincareAddiction
- r/AsianBeauty
- r/BeautyGuruChatter
- r/MakeupAddiction
- r/Sephora
- r/Ulta
- r/30PlusSkinCare
- r/SkincareOver30

### Pages Per Subreddit
- `/new/` (primary signal source)
- `/hot/`
- `/top/?t=week`
- `/top/?t=month`

## Outputs

1. **trends_analysis.json** - Full structured data
2. **trends.csv** - Spreadsheet-friendly format
3. **trend_summary.md** - Human-readable report
4. **raw_data.json** - All scraped posts/comments

## Trend Detection Logic

### Early Signals
- **Low baseline** (< 3 historical mentions)
- **Rapid growth** (> 1.5x recent vs baseline)
- **Cross-subreddit presence** (spreading across communities)
- **High engagement** (scores + comments)

### Scoring Weights
- Growth velocity: 30%
- Novelty: 25%
- Momentum: 20%
- Cross-subreddit: 15%
- Engagement: 10%

## Rate Limiting

Respects Reddit's servers with:
- 1.5-3 second delays between requests
- Proper User-Agent headers
- Error handling for rate limits

## Requirements

```bash
pip install requests beautifulsoup4
```

## Customization

Edit `main.py` to:
- Change subreddits
- Adjust pages to scrape
- Modify posts per page
- Change time windows for trend detection

