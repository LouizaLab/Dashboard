# Data Engine Indexing Performance Notes

## Why Indexing Takes Time

Indexing can be slow due to several factors:

### 1. **Embedding Generation (Main Bottleneck)**
   - **Problem**: Generating embeddings for text is computationally expensive
   - **Impact**: With 46 interview files, each chunked into ~1000 character segments, you could have hundreds or thousands of text chunks
   - **Time**: Generating embeddings one-by-one can take **minutes to hours** depending on:
     - Number of records
     - Length of text per record
     - Hardware (CPU vs GPU)
     - Model size

### 2. **Text Enrichment**
   - Cleaning and processing text adds overhead
   - Usually much faster than embeddings, but still takes time

### 3. **File I/O**
   - Writing thousands of JSON files to disk
   - Updating metadata indexes
   - Saving vector indexes (FAISS)

## Performance Optimizations Applied

### ✅ Batch Embedding Generation
**Before**: Embeddings generated one-by-one in a loop
```python
for record in batch_records:
    embedding = encoder.encode(text)  # SLOW - one at a time!
```

**After**: Batch encoding (10-100x faster)
```python
# Collect all texts
texts = [record.get_text_for_embedding() for record in batch_records]
# Encode all at once
embeddings = encoder.encode(texts, batch_size=64)  # FAST!
```

### ✅ Skip Embeddings Option
For faster indexing when semantic search isn't needed:
```bash
python ingest_all_buckets.py --no-embeddings
```
This indexes metadata only (brand, source, filters) but skips vector embeddings.

### ✅ Progress Indicators
Added progress messages so you can see what's happening:
- Batch processing status
- Embedding generation progress
- Indexing status

## Speed Comparison

| Mode | Records | Time Estimate |
|------|---------|---------------|
| With embeddings (old) | 1000 | ~10-30 minutes |
| With embeddings (optimized) | 1000 | ~1-3 minutes |
| Without embeddings | 1000 | ~10-30 seconds |

*Times vary based on hardware and text length*

## Recommendations

### For Fast Initial Indexing (Metadata Only)
```bash
# Fast mode - no embeddings
python ingest_all_buckets.py --no-embeddings
```
- Indexes all metadata (brand, source, bucket, etc.)
- Enables filtering and structured queries
- **Cannot** do semantic search
- Takes ~10-30 seconds per 1000 records

### For Full Semantic Search
```bash
# Full mode - with embeddings
python ingest_all_buckets.py
```
- Includes vector embeddings for semantic search
- Slower but enables text similarity search
- Takes ~1-3 minutes per 1000 records (optimized)

### For Large Datasets
```bash
# Adjust batch size for your system
python ingest_all_buckets.py --batch-size 10000
```
- Larger batches = fewer I/O operations
- But requires more memory

## Monitoring Progress

The script now shows:
- Number of records per bucket
- Batch processing progress
- Embedding generation status
- Indexing completion

If indexing seems stuck, check:
1. Is it generating embeddings? (look for "Generating embeddings..." message)
2. How many records? (check the batch progress)
3. CPU/Memory usage (embedding generation is CPU-intensive)

## Troubleshooting Slow Indexing

### If indexing is very slow:

1. **Check if embeddings are being generated**
   - Look for "Generating embeddings..." messages
   - If you don't need semantic search, use `--no-embeddings`

2. **Check number of records**
   - 46 interview files × ~10-50 chunks each = potentially 500-2000+ records
   - Each record needs embedding generation

3. **Check system resources**
   - Embedding generation is CPU-intensive
   - Monitor CPU usage during indexing

4. **Consider indexing in stages**
   - Index Bucket 2 (interviews) separately first
   - Then add other buckets later

## Example: Indexing 11 Labs Interviews Only

```python
from Data_Engine.data_engine import DataEngine
from pathlib import Path

engine = DataEngine(storage_dir=Path("storage_data"))

# Find interview files
interview_dir = Path("ingestion/bucket2_survey_interviews/11_labs_interviews")
interview_files = sorted(interview_dir.glob("Interview*.txt"))

# Ingest and index
all_records = []
for interview_file in interview_files:
    records = list(engine.ingest_survey(
        interview_file,
        source_name="11_labs_interviews",
        chunk_size=1000,
        chunk_overlap=200
    ))
    all_records.extend(records)

# Index WITHOUT embeddings for speed
engine.index_records(all_records, generate_embeddings=False, enrich_text=True)
```

This will be much faster than generating embeddings for all chunks!

