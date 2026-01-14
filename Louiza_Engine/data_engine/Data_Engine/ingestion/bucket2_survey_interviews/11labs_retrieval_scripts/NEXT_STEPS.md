# Next Steps - Using the ElevenLabs Transcript Fetcher

## ✅ Step 1: API Key Set (Done!)

Your API key is now configured.

## Step 2: Test the Script

Run the script to fetch transcripts:

```bash
python scripts/fetch_transcripts.py
```

This will:
- Connect to ElevenLabs API
- Fetch all available transcripts
- Save them to `11_labs_interviews/` folder
- Skip any that are already downloaded

## Step 3: Check the Output

After running, check what was downloaded:

```bash
ls -la 11_labs_interviews/
```

You should see:
- Transcript files: `interview123__2025-01-15.txt`
- Index file: `downloaded_ids.json`

## Step 4: View a Transcript

```bash
cat 11_labs_interviews/interview123__2025-01-15.txt
```

Each file includes:
- Title, duration, date metadata
- Full transcript text

## Step 5: Fetch Specific Interviews (Optional)

If you know specific interview IDs:

```bash
python scripts/fetch_transcripts.py --ids interview1 interview2 interview3
```

## Step 6: Set Up Automation (Optional)

### Option A: Run Daily with Cron

```bash
# Edit crontab
crontab -e

# Add this line (runs daily at 9 AM):
0 9 * * * cd /Users/larissatyagi/Desktop/Consumer_Engine && /usr/bin/python3 scripts/fetch_transcripts.py >> logs/transcript_fetch.log 2>&1
```

### Option B: Run Manually When Needed

Just run:
```bash
python scripts/fetch_transcripts.py
```

Whenever you want to check for new transcripts.

## Troubleshooting

**"No transcripts found"**
- Check your API key has access to transcripts
- Verify you have transcripts in your ElevenLabs account
- Try fetching specific IDs: `python scripts/fetch_transcripts.py --ids <id>`

**"Invalid API key"**
- Verify: `echo $ELEVENLABS_API_KEY`
- Make sure you reloaded shell: `source ~/.zshrc`

**Script runs but no files appear**
- Check permissions on `11_labs_interviews/` folder
- Run with `--verbose` to see detailed logs

## What Happens Next?

Once transcripts are in `11_labs_interviews/`:
- ✅ Cursor automatically indexes them
- ✅ They're available for search and analysis
- ✅ Can be queried through your data engine

## Quick Commands Reference

```bash
# Fetch all transcripts
python scripts/fetch_transcripts.py

# Fetch specific IDs
python scripts/fetch_transcripts.py --ids id1 id2

# Verbose logging
python scripts/fetch_transcripts.py --verbose

# Custom output folder
python scripts/fetch_transcripts.py --output ./custom_folder

# Check what's downloaded
ls -la 11_labs_interviews/
cat 11_labs_interviews/downloaded_ids.json
```

