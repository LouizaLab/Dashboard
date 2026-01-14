# 11 Labs Interview Ingestion System

## Purpose

This folder (`11_labs_ingestion/`) is the **active ingestion pipeline** for new ElevenLabs interview transcripts.

## Folder Structure

- **`incoming/`** - New transcript files (`.txt` or `.json`) are placed here for processing
- **`processed/`** - Transcripts that have been successfully processed
- **`archive/`** - Long-term storage for processed transcripts (optional)

## Legacy Folder

The `11_labs_interviews/` folder (located at the repository root) contains **historical/legacy transcripts** and should **NOT** be modified. It serves as a reference for existing data.

## Usage

### Quick Start - Complete Pipeline

Run the complete ingestion pipeline (fetches + watches):

```bash
# Make sure API key is set
export ELEVENLABS_API_KEY='your-api-key-here'

# Run the complete pipeline
./11_labs_ingestion/run_ingestion_pipeline.sh
```

This will:
1. Fetch new transcripts from ElevenLabs API → `incoming/` folder
2. Start the watcher to monitor for new files

### Option 1: Fetch New Transcripts

Fetch transcripts from ElevenLabs API and save to `incoming/`:

```bash
# Set API key
export ELEVENLABS_API_KEY='your-api-key-here'

# Fetch transcripts
python 11_labs_ingestion/fetch_to_incoming.py
```

### Option 2: Watch for New Transcripts

Run the file watcher to monitor the `incoming/` folder:

```bash
python 11_labs_ingestion/watch_incoming.py
```

The watcher will:
- Monitor `incoming/` for new `.txt` or `.json` files
- Log when new transcripts are detected
- Allow for future processing logic to be added

### Option 3: Manual File Addition

**Since agent conversations aren't available via REST API**, you can add them manually:

**Method A: Use the helper script (recommended):**
```bash
python 11_labs_ingestion/add_manual_transcript.py
```
Follow the prompts to enter conversation details and paste the transcript.

**Method B: Manual file creation:**
1. Copy conversation transcript from ElevenLabs web UI
2. Create a `.txt` file in `11_labs_ingestion/incoming/`
3. Use filename format: `{conversation_id}__{YYYY-MM-DD}.txt`
4. Include metadata header (see `MANUAL_EXPORT.md` for format)
5. The watcher script will detect them automatically

See `MANUAL_EXPORT.md` for detailed instructions.

## Dependencies

Install required libraries:

```bash
pip install watchdog requests
```

- `watchdog` - For file system watching
- `requests` - For API calls (used by fetch script)

## Notes

- This system is designed to be **additive** - safe to run multiple times
- Existing files in `11_labs_interviews/` are **never modified** by this system
- All paths are relative to the repository root

