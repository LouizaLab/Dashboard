# Downloading Kaggle Datasets

This guide shows you how to easily download Kaggle datasets to `bucket1_online_datasets`.

## Quick Start

### 1. Install kagglehub

```bash
pip install kagglehub
```

Or install from requirements:
```bash
pip install -r Data_Engine/requirements.txt
```

### 2. Authenticate with Kaggle

On first use, kagglehub will prompt you to authenticate. You'll need:
- A Kaggle account
- API credentials from https://www.kaggle.com/account

The authentication is automatic - just follow the prompts!

### 3. Download a Dataset

Use the helper script:

```bash
cd Data_Engine/ingestion/bucket1_online_datasets

# Download to a new folder
python download_kaggle_dataset.py <owner>/<dataset-name> --output-dir <folder-name>

# Example: Download food recipes dataset
python download_kaggle_dataset.py ruchi798/food-com-recipes-and-user-interactions --output-dir food_recipes
```

## Examples

### Example 1: Food Reviews Dataset

```bash
python download_kaggle_dataset.py dataindustry/fast-food-restaurants --output-dir fast_food_data
```

### Example 2: Restaurant Reviews

```bash
python download_kaggle_dataset.py dataindustry/restaurant-reviews --output-dir restaurant_reviews
```

### Example 3: Download to Existing Folder

```bash
python download_kaggle_dataset.py <owner>/<dataset> --output-dir food_online_data
```

## Finding Dataset Paths

1. Go to the Kaggle dataset page (e.g., https://www.kaggle.com/datasets/ruchi798/food-com-recipes-and-user-interactions)
2. Look at the URL: `kaggle.com/datasets/<owner>/<dataset-name>`
3. Use format: `<owner>/<dataset-name>`

## Manual Download (Alternative)

If you prefer to download manually:

1. Go to the Kaggle dataset page
2. Click "Download" button
3. Extract the files
4. Place them in a folder under `bucket1_online_datasets/`

## After Downloading

Once you've downloaded a dataset:

1. **Review the files** - Check what CSV/data files are included
2. **Update ingestion configs** - Add configuration in `ingest_phase1_data.py` if needed
3. **Run ingestion** - Use the main ingestion script to add to Data Engine

```bash
python Data_Engine/ingest_phase1_data.py
```

## Troubleshooting

### Authentication Issues

If you get authentication errors:
1. Visit https://www.kaggle.com/account
2. Scroll to "API" section
3. Click "Create New Token" - this downloads `kaggle.json`
4. Place it in `~/.kaggle/kaggle.json` (or follow kagglehub prompts)

### Dataset Not Found

- Check the dataset path format: `owner/dataset-name`
- Ensure the dataset is public (or you have access)
- Verify spelling/capitalization

### Permission Errors

- Make sure you have write permissions in the target directory
- Check that the output directory path is correct

## Why kagglehub?

`kagglehub` is simpler than the Kaggle CLI because:
- ✅ No manual API setup needed
- ✅ Automatic authentication prompts
- ✅ Simple Python API
- ✅ Handles caching automatically
- ✅ Works seamlessly with Python scripts

## More Information

- Kaggle Datasets: https://www.kaggle.com/datasets
- kagglehub docs: https://github.com/Kaggle/kagglehub

