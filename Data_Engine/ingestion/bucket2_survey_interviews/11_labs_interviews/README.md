# 11 Labs Interview Files

This directory contains interview transcript text files (`.txt`) from 11 Labs.

## 📁 Directory Purpose

This directory is the **source location** for interview text files. Place new interview `.txt` files here for indexing.

## 📝 File Format

- **Format**: Plain text files (`.txt`)
- **Naming**: Use descriptive names like `Interview29.txt`, `Interview30.txt`, etc.
- **Content**: Interview transcripts, Q&A, or conversation logs

## 🚀 Indexing New Files

To index these files into the Data Engine, use the dedicated indexing scripts:

### Quick Index (Metadata Only - Fast)
```bash
cd /path/to/Consumer_Engine
python3 Data_Engine/indexing/11labs_interviews/quick_index_11labs.py
```

### Full Index (With Embeddings - Recommended)
```bash
cd /path/to/Consumer_Engine
python3 Data_Engine/indexing/11labs_interviews/index_11labs_optimized.py
```

### Verify Indexing
```bash
cd /path/to/Consumer_Engine
python3 Data_Engine/indexing/11labs_interviews/verify_11labs_indexed.py
```

## 📚 Documentation

For complete documentation on indexing, see:
- **Main Guide**: `Data_Engine/indexing/11labs_interviews/README.md`
- **Quick Reference**: `Data_Engine/indexing/11labs_interviews/QUICK_REFERENCE.md`

## 🔄 Workflow

1. **Add files** → Place new `.txt` files in this directory
2. **Index** → Run indexing script from `Data_Engine/indexing/11labs_interviews/`
3. **Verify** → Run verification script to confirm indexing

## 📊 Current Status

- **46 interview .txt files** in this directory
- **299 interview records** indexed and retrievable
- Files are automatically detected by indexing scripts

## ⚠️ Note

- **Don't modify files** after indexing (re-index if needed)
- **Keep original files** as source of truth
- **Use consistent naming** for easier management
