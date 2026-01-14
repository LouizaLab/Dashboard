# Quick Setup Guide

## Step 1: Install Dependencies

```bash
pip install watchdog requests
```

## Step 2: Set Your API Key

```bash
export ELEVENLABS_API_KEY='your-api-key-here'
```

Or add to your shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
echo 'export ELEVENLABS_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

## Step 3: Run the Pipeline

### Option A: Complete Pipeline (Recommended)

Runs both fetching and watching:

```bash
./11_labs_ingestion/run_ingestion_pipeline.sh
```

### Option B: Just Fetch Once

Fetch transcripts and exit:

```bash
python 11_labs_ingestion/fetch_to_incoming.py
```

### Option C: Just Watch

Watch for manually added files:

```bash
python 11_labs_ingestion/watch_incoming.py
```

## How It Works

1. **Fetch Script** (`fetch_to_incoming.py`)
   - Connects to ElevenLabs API
   - Downloads new transcripts
   - Saves them to `11_labs_ingestion/incoming/`
   - Skips already downloaded transcripts

2. **Watcher Script** (`watch_incoming.py`)
   - Monitors `incoming/` folder for new files
   - Logs when `.txt` or `.json` files appear
   - Ready for processing logic to be added

3. **Pipeline Script** (`run_ingestion_pipeline.sh`)
   - Runs fetch script first
   - Then starts watcher
   - Keeps running until you press Ctrl+C

## Automation

### Run Periodically (Cron)

Add to crontab to fetch every hour:

```bash
crontab -e

# Add this line (adjust path):
0 * * * * cd /path/to/Consumer_Engine && /usr/bin/python3 11_labs_ingestion/fetch_to_incoming.py >> logs/fetch.log 2>&1
```

### Run Watcher as Background Service

Keep watcher running in background:

```bash
nohup python 11_labs_ingestion/watch_incoming.py > logs/watcher.log 2>&1 &
```

## Troubleshooting

### "ELEVENLABS_API_KEY not set"
- Make sure you've exported the environment variable
- Check with: `echo $ELEVENLABS_API_KEY`

### "watchdog library not found"
- Install with: `pip install watchdog`

### "Could not import fetch_transcripts"
- Make sure `scripts/fetch_transcripts.py` exists
- Check that you're running from the repository root

### Files not being detected
- Make sure files are `.txt` or `.json` format
- Check that files are in `11_labs_ingestion/incoming/` folder
- Verify watcher is running

