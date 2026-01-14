# ElevenLabs Transcript Fetcher

Automatically fetches interview transcripts from ElevenLabs API and saves them to the local `11_labs_interviews/` directory for automatic ingestion by Cursor.

## Quick Start

### 1. Set API Key

```bash
export ELEVENLABS_API_KEY="your-api-key-here"
```

Or add to your shell profile (`~/.zshrc` or `~/.bashrc`):
```bash
echo 'export ELEVENLABS_API_KEY="your-api-key-here"' >> ~/.zshrc
source ~/.zshrc
```

### 2. Install Dependencies

```bash
pip install requests
```

### 3. Run the Script

**Fetch all available transcripts:**
```bash
python scripts/fetch_transcripts.py
```

**Fetch specific interview IDs:**
```bash
python scripts/fetch_transcripts.py --ids interview1 interview2 interview3
```

**Use custom output directory:**
```bash
python scripts/fetch_transcripts.py --output ./custom_folder
```

**Verbose logging:**
```bash
python scripts/fetch_transcripts.py --verbose
```

## How It Works

1. **API Integration**: Connects to ElevenLabs API using your API key
2. **Transcript Discovery**: Fetches list of available transcripts (or uses provided IDs)
3. **Idempotent Download**: Only downloads new transcripts (skips existing files)
4. **File Naming**: Saves as `<interview_id>__<YYYY-MM-DD>.txt`
5. **Index Tracking**: Maintains `downloaded_ids.json` to track downloaded transcripts

## File Structure

```
repo/
├── 11_labs_interviews/
│   ├── interview123__2025-01-15.txt
│   ├── interview456__2025-01-16.txt
│   └── downloaded_ids.json  # Index of downloaded transcripts
└── scripts/
    └── fetch_transcripts.py
```

## Features

- ✅ **Idempotent**: Safe to run multiple times (won't re-download)
- ✅ **Error Handling**: Continues even if individual transcripts fail
- ✅ **Metadata**: Includes title, duration, date in file headers
- ✅ **Logging**: Clear console output showing progress
- ✅ **Index Tracking**: Tracks downloaded IDs to avoid duplicates

## Output Format

Each transcript file includes:

```
Title: Interview with John Doe
Duration: 15m 30s
Date: 2025-01-15 14:30:00
Interview ID: interview123

======================================================================
Transcript:

[Transcript text content here...]
```

## Automation

### Cron Job (Linux/Mac)

Run daily at 9 AM:
```bash
# Edit crontab
crontab -e

# Add this line (adjust path):
0 9 * * * cd /path/to/repo && /usr/bin/python3 scripts/fetch_transcripts.py >> logs/transcript_fetch.log 2>&1
```

### Systemd Timer (Linux)

Create `/etc/systemd/user/fetch-transcripts.service`:
```ini
[Unit]
Description=Fetch ElevenLabs Transcripts

[Service]
Type=oneshot
WorkingDirectory=/path/to/repo
ExecStart=/usr/bin/python3 scripts/fetch_transcripts.py
Environment="ELEVENLABS_API_KEY=your-key-here"
```

Create `/etc/systemd/user/fetch-transcripts.timer`:
```ini
[Unit]
Description=Daily ElevenLabs Transcript Fetch

[Timer]
OnCalendar=daily
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
systemctl --user enable fetch-transcripts.timer
systemctl --user start fetch-transcripts.timer
```

### LaunchAgent (macOS)

Create `~/Library/LaunchAgents/com.elevenlabs.fetch-transcripts.plist`:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.elevenlabs.fetch-transcripts</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/path/to/repo/scripts/fetch_transcripts.py</string>
    </array>
    <key>WorkingDirectory</key>
    <string>/path/to/repo</string>
    <key>EnvironmentVariables</key>
    <dict>
        <key>ELEVENLABS_API_KEY</key>
        <string>your-key-here</string>
    </dict>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

Load:
```bash
launchctl load ~/Library/LaunchAgents/com.elevenlabs.fetch-transcripts.plist
```

## Cursor Integration

Cursor automatically watches the `11_labs_interviews/` folder. When new transcript files appear:

1. Files are automatically detected
2. Content is indexed for search
3. Available for analysis and queries

No additional configuration needed!

## Troubleshooting

### "Invalid API key" error
- Verify your API key is correct
- Check that `ELEVENLABS_API_KEY` environment variable is set
- Try using `--api-key` flag directly

### "No transcripts found"
- Check API key permissions
- Verify you have transcripts in your ElevenLabs account
- Try fetching specific IDs with `--ids`

### Files not appearing
- Check file permissions on `11_labs_interviews/` directory
- Verify script has write access
- Check logs for errors

## API Endpoint Notes

The script tries multiple possible ElevenLabs API endpoints:
- `/v1/transcripts`
- `/v1/conversations`
- `/v1/interviews`

If your ElevenLabs API uses different endpoints, modify the `list_transcripts()` and `get_transcript()` methods in `fetch_transcripts.py`.

## Extending

The code is modular and easy to extend:

- **Add metadata fields**: Modify `parse_metadata()`
- **Change file format**: Modify `save_transcript()`
- **Add filtering**: Add filters in `fetch_and_save_transcripts()`
- **JSON output**: Add `--format json` option

## License

MIT

