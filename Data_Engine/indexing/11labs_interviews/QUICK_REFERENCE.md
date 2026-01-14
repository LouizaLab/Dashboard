# Quick Reference: Indexing 11 Labs Interviews

## 🚀 One-Line Commands

### Index New Interview Files (Full - with embeddings)
```bash
cd /path/to/Consumer_Engine && python3 Data_Engine/indexing/11labs_interviews/index_11labs_optimized.py
```

### Quick Index (Metadata only - fast)
```bash
cd /path/to/Consumer_Engine && python3 Data_Engine/indexing/11labs_interviews/quick_index_11labs.py
```

### Verify Indexing
```bash
cd /path/to/Consumer_Engine && python3 Data_Engine/indexing/11labs_interviews/verify_11labs_indexed.py
```

## 📋 Workflow for New Files

1. **Add files** → Place `.txt` files in `Data_Engine/ingestion/bucket2_survey_interviews/11_labs_interviews/`

2. **Index** → Run `index_11labs_optimized.py` or `quick_index_11labs.py`

3. **Verify** → Run `verify_11labs_indexed.py` to confirm

## 📍 File Locations

- **Interview files**: `Data_Engine/ingestion/bucket2_survey_interviews/11_labs_interviews/`
- **Indexing scripts**: `Data_Engine/indexing/11labs_interviews/`
- **Storage**: `Data_Engine/storage_data/`

## ✅ Current Status

- **46 interview .txt files** in source directory
- **299 interview records** indexed and retrievable
- **All scripts working** from new location

## 🔍 Test Query

```python
from Data_Engine.data_engine import DataEngine
from pathlib import Path

engine = DataEngine(storage_dir=Path("Data_Engine/storage_data"))
interviews = engine.get_by_filters({"source_name": "11_labs_interviews"})
print(f"Found {len(interviews)} interview records")
```

