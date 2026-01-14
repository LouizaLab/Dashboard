# Online Data Folder

Place your CSV files (from Kaggle, public datasets, etc.) in this folder.

## How to use:

1. **Place your CSV file** in this folder (`Data_Engine/ingestion/bucket1_online_datasets/online_data/`)
2. **Run the ingestion script:**

```bash
# For a single file
python Data_Engine/ingestion/bucket1_online_datasets/ingest_kaggle_csv.py \
    Data_Engine/ingestion/bucket1_online_datasets/online_data/your_file.csv \
    --source-name my_dataset

# For all CSV files in this folder
python Data_Engine/ingestion/bucket1_online_datasets/ingest_kaggle_csv.py \
    Data_Engine/ingestion/bucket1_online_datasets/online_data/ \
    --source-name my_datasets
```

## Example:

```bash
# If you have a file called "food_reviews.csv"
python Data_Engine/ingestion/bucket1_online_datasets/ingest_kaggle_csv.py \
    Data_Engine/ingestion/bucket1_online_datasets/online_data/food_reviews.csv \
    --source-name food_reviews \
    --text-columns "review" "description" \
    --brand-column "brand"
```

The data will be ingested into **Bucket 1 (Online Datasets)** automatically.

