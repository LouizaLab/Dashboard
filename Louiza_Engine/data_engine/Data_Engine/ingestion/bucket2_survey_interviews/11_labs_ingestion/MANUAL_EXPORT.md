# Manual Export Instructions

Since ElevenLabs agent conversations may not be available via the REST API, you can manually export conversations and place them in the `incoming/` folder.

## Option 1: Manual Copy-Paste

1. Go to https://elevenlabs.io/app/agents/conversations
2. Open each conversation you want to export
3. Copy the transcript text
4. Create a new `.txt` file in `11_labs_ingestion/incoming/` with:
   - Filename format: `{conversation_id}__{date}.txt`
   - Include metadata header (see example below)
   - Paste the transcript content

## Option 2: Browser Export (if available)

1. Check if ElevenLabs UI has an export feature
2. Export conversations as `.txt` or `.json` files
3. Place exported files in `11_labs_ingestion/incoming/`

## File Format Example

```txt
Agent: louiza Main
Duration: 4:03
Messages: 20
Status: Successful
Date: 2025-12-31 16:59:00
ID: CONV_12345

======================================================================
Transcript:
======================================================================

[Conversation transcript content here...]
```

## File Naming Convention

- Format: `{ID}__{YYYY-MM-DD}.txt`
- Example: `CONV_abc123__2025-12-31.txt`
- The watcher will detect any `.txt` or `.json` files in `incoming/`

## Processing

Once files are in `incoming/`, the watcher script (`watch_incoming.py`) will detect them automatically. You can then add processing logic to:
- Move files to `processed/` after handling
- Index transcripts in your data engine
- Extract metadata
- Send notifications

