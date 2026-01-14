# 11 Labs Interview Auto-Importer

Automatically imports 11 Labs interviews that are over 10 minutes long.

## Setup

1. Install dependencies:
```bash
pip install watchdog
```

2. Configure the importer (see usage below)

## Usage

### Option 1: Watch a Directory (Automatic)

Watch a directory for new interview files and auto-import them:

```bash
python auto_import.py --watch /path/to/11labs/exports
```

This will:
- Monitor the directory for new `.txt` files
- Check if duration is over 10 minutes
- Automatically copy to `11_labs_interviews/` folder
- Rename to `Interview{N}.txt` format

### Option 2: Import from Directory (One-time)

Import all interviews from a directory:

```bash
python auto_import.py --import /path/to/interviews
```

### Option 3: Import Single File

Import a single interview file:

```bash
python auto_import.py --file /path/to/interview.txt
```

## Duration Detection

The importer checks interview duration in two ways:

1. **From filename**: Looks for patterns like:
   - `interview_15min.txt` → 15 minutes
   - `call_10_30.txt` → 10.5 minutes (if 10:30 format)

2. **From text**: Estimates based on word count:
   - Uses ~120 words per minute average
   - Counts words in transcript

## Configuration

Default settings:
- **Minimum duration**: 10 minutes
- **Target folder**: `11_labs_interviews/`
- **File pattern**: `*.txt`

You can customize:
```bash
python auto_import.py --watch /path/to/exports --min-duration 15 --target /custom/path
```

## Integration with 11 Labs

### Option A: File Export Folder

If 11 Labs exports interviews to a folder:
1. Set up the watch on that folder
2. New interviews will be automatically imported

### Option B: API Integration (Future)

To integrate with 11 Labs API:
1. Get API credentials from 11 Labs
2. Modify `auto_import.py` to poll API for new interviews
3. Download and import automatically

### Option C: Manual Export

1. Export interviews from 11 Labs dashboard
2. Save to a watched folder
3. Auto-import will pick them up

## File Naming

Files are automatically named:
- `Interview1.txt`
- `Interview2.txt`
- `Interview3.txt`
- etc.

Based on the highest existing number in the folder.

## Notes

- Only imports interviews over the minimum duration (default: 10 minutes)
- Skips files that are too short
- Preserves original file content
- Logs all import activity




