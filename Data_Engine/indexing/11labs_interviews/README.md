# 11 Labs Interview Indexing

This directory contains all scripts for indexing 11 Labs interview text files into the Data Engine.

## 📁 Directory Structure

```
Data_Engine/indexing/11labs_interviews/
├── README.md                    # This file
├── index_11labs_optimized.py   # Main indexing script (with embeddings)
├── quick_index_11labs.py       # Fast metadata-only indexing
└── verify_11labs_indexed.py    # Verification script
```

## 📍 Interview Data Location

Interview text files are located at:
```
Data_Engine/ingestion/bucket2_survey_interviews/11_labs_interviews/
```

## 🚀 Quick Start

### Option 1: Full Indexing (Recommended)

Index interviews with embeddings for semantic search:

```bash
cd /path/to/Consumer_Engine
python3 Data_Engine/indexing/11labs_interviews/index_11labs_optimized.py
```

**What it does:**
1. Quick indexes metadata (instant)
2. Generates embeddings in optimized batches
3. Updates the index with embeddings
4. Verifies RAG compatibility

**Time:** ~1-3 minutes for 299 interviews

### Option 2: Quick Indexing (Metadata Only)

Fast indexing without embeddings (for structured queries only):

```bash
cd /path/to/Consumer_Engine
python3 Data_Engine/indexing/11labs_interviews/quick_index_11labs.py
```

**What it does:**
- Indexes metadata only (no embeddings)
- Very fast - takes seconds
- Enables filtering and structured queries
- **Cannot** do semantic search

**Time:** ~10-30 seconds for 299 interviews

### Verify Indexing

Check if interviews are properly indexed:

```bash
cd /path/to/Consumer_Engine
python3 Data_Engine/indexing/11labs_interviews/verify_11labs_indexed.py
```

## 📝 How to Index New Interview TXT Files

### Step 1: Add Interview Files

Place new interview `.txt` files in the interview directory:

```bash
# Copy new interview files here:
Data_Engine/ingestion/bucket2_survey_interviews/11_labs_interviews/
```

**File naming:**
- Use descriptive names: `Interview29.txt`, `Interview30.txt`, etc.
- Or use conversation IDs: `CONV_abc123__2025-01-07.txt`

**File format:**
- Plain text files (`.txt`)
- Can contain interview transcripts, Q&A, or conversation logs
- No specific format required - the system will chunk long files automatically

### Step 2: Run Indexing

Choose one of the indexing methods above:

**For new files only:**
```bash
# The scripts automatically detect and index new files
python3 Data_Engine/indexing/11labs_interviews/index_11labs_optimized.py
```

**For quick indexing (no embeddings):**
```bash
python3 Data_Engine/indexing/11labs_interviews/quick_index_11labs.py
```

### Step 3: Verify

Check that new files were indexed:

```bash
python3 Data_Engine/indexing/11labs_interviews/verify_11labs_indexed.py
```

## 🔍 How It Works

### Indexing Process

1. **File Discovery**
   - Scans `11_labs_interviews/` directory for `.txt` files
   - Detects new files automatically

2. **Chunking** (for long files)
   - Files are split into ~1000 character chunks
   - Maintains context with overlap
   - Each chunk becomes a separate record

3. **Metadata Extraction**
   - Extracts source name: `11_labs_interviews`
   - Sets bucket: `2` (Surveys & Interviews)
   - Records file path and chunk information

4. **Embedding Generation** (if using optimized script)
   - Generates embeddings using `all-MiniLM-L6-v2` model
   - Batch processing for efficiency
   - Stores embeddings for semantic search

5. **Index Storage**
   - Saves records to `Data_Engine/storage_data/`
   - Updates metadata index
   - Updates vector index (if embeddings generated)

### Record Structure

Each indexed interview record contains:

```python
{
    "record_id": "unique-id",
    "bucket_id": 2,
    "source_name": "11_labs_interviews",
    "raw_text": "interview text content...",
    "metadata": {
        "file_path": "path/to/Interview1.txt",
        "chunk_index": 0,  # if file was chunked
        ...
    }
}
```

## 📊 Querying Indexed Interviews

### Using Data Engine Directly

```python
from Data_Engine.data_engine import DataEngine
from pathlib import Path

engine = DataEngine(storage_dir=Path("Data_Engine/storage_data"))

# Get all interview records
interviews = engine.get_by_filters({"source_name": "11_labs_interviews"})
print(f"Found {len(interviews)} interview records")

# Get records from specific file
from_file = engine.get_by_filters({
    "source_name": "11_labs_interviews",
    "metadata.file_path": "path/to/Interview1.txt"
})
```

### Using Agent Tron Multi-Agent System

```bash
# Search interviews using multi-agent system
python3 Agent_Tron/search_interviews_multi_agent_simple.py \
    "What do people say about fast food preferences?"
```

The multi-agent system automatically:
- Detects when interview data is relevant
- Routes to appropriate agents (sentiment_agent, demographic_agent, etc.)
- Retrieves relevant interview content
- Synthesizes results

## 🛠️ Troubleshooting

### Issue: "No records found"

**Solution:**
1. Check that interview files exist in `11_labs_interviews/` directory
2. Run `quick_index_11labs.py` first to index metadata
3. Then run `index_11labs_optimized.py` for embeddings

### Issue: Mutex errors on macOS

**Solution:**
- The scripts already handle this with environment variables
- If issues persist, use `quick_index_11labs.py` (no embeddings)

### Issue: Files not being indexed

**Solution:**
1. Verify files are `.txt` format
2. Check file permissions
3. Run verification script to see what's indexed
4. Check logs for errors

### Issue: Embeddings not generating

**Solution:**
1. Install sentence-transformers: `pip install sentence-transformers`
2. Check available disk space
3. Use `quick_index_11labs.py` if embeddings aren't needed

## 📈 Performance

### Indexing Speed

| Method | Records | Time | Notes |
|--------|---------|------|-------|
| Quick Index | 299 | ~10-30s | Metadata only |
| Optimized Index | 299 | ~1-3 min | With embeddings |

### Storage

- **Metadata**: ~50-100 KB per interview file
- **Embeddings**: ~1-2 MB per interview file (384 dimensions)
- **Total**: ~300-600 MB for 299 interviews with embeddings

## 🔄 Updating Existing Indexes

The indexing scripts are **idempotent** - you can run them multiple times safely:

- **New files**: Automatically detected and indexed
- **Existing files**: Skipped (won't duplicate)
- **Modified files**: Will be re-indexed if file timestamp changed

## 📚 Related Documentation

- **Ingestion Pipeline**: `Data_Engine/ingestion/bucket2_survey_interviews/11_labs_ingestion/`
- **Data Engine**: `Data_Engine/README.md`
- **Agent Tron**: `Agent_Tron/README.md`

## ✅ Verification Checklist

After indexing, verify:

- [ ] Files are in `11_labs_interviews/` directory
- [ ] Verification script shows correct record count
- [ ] Records have correct `source_name: "11_labs_interviews"`
- [ ] Records have correct `bucket_id: 2`
- [ ] Text content is present in `raw_text` field
- [ ] Can query using `get_by_filters({"source_name": "11_labs_interviews"})`
- [ ] Multi-agent system can retrieve interview data

## 🎯 Best Practices

1. **File Organization**
   - Keep all interview files in `11_labs_interviews/` directory
   - Use consistent naming conventions
   - Don't modify files after indexing (re-index if needed)

2. **Indexing Frequency**
   - Index new files as they arrive
   - Re-index if files are updated
   - Use quick index for rapid updates, full index for semantic search

3. **Verification**
   - Always verify after indexing
   - Check record counts match file counts
   - Test retrieval with sample queries

4. **Backup**
   - Backup `storage_data/` directory regularly
   - Keep original `.txt` files as source of truth

