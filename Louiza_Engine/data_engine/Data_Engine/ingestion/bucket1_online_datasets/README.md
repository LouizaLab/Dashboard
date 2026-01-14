# Bucket 1: Online Datasets Utilities

This folder contains the core ingestion class for online datasets (Kaggle, public datasets, etc.) into Bucket 1.

## Structure

- `bucket1_online_datasets.py` - Core ingestion class (`OnlineDatasetsIngester`)
- `online_data/` - Folder for CSV files to ingest

## Usage

**Use the unified ingestion script:**

```bash
python Data_Engine/ingest_phase1_data.py
```

This script automatically ingests CSV files from:
1. Phase 1 menu data: `Phase_1_Taste_Embedding_Model/data/raw/`
2. Online datasets: `Data_Engine/ingestion/bucket1_online_datasets/online_data/`

Simply place your CSV files in the `online_data/` folder and run the script!

## Core Class

The main ingestion class is `OnlineDatasetsIngester` in `bucket1_online_datasets.py`. 
It's used by the unified `ingest_phase1_data.py` script via the DataEngine API.

