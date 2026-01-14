# Bucket 2: Surveys & Interviews Ingestion

This module handles ingestion of survey CSV files and interview TXT files.

## Features

- **CSV Survey Files**: Ingests survey responses with automatic field classification
  - Auto-detects text columns (free-text answers)
  - Extracts brand information (if specified)
  - Classifies fields into structured, numerical, and categorical types
  - Handles Likert scales, rankings, and free-text responses

- **TXT Interview Files**: Ingests long-form interview transcripts
  - Chunks long interviews into manageable segments
  - Configurable chunk size and overlap
  - Maintains parent-child relationships between chunks

## Usage

### CSV Survey Ingestion

```python
from Data_Engine.ingestion import SurveysInterviewsIngester
from pathlib import Path

# Initialize ingester
ingester = SurveysInterviewsIngester(
    source_name="chipotle_survey",
    survey_name="Chipotle Consumer Survey"
)

# Ingest CSV file
csv_file = Path("bucket2_survey_interviews/survey_interviews/Chipotle Survey (Responses) - Form Responses 1.csv")

# Validate file
if ingester.validate_file(csv_file):
    # Ingest records
    for record in ingester.ingest(csv_file, brand_column="Brand Name"):
        print(f"Record ID: {record.record_id}")
        print(f"Raw Text: {record.raw_text[:100]}...")
        print(f"Structured Fields: {len(record.structured_fields)}")
        print(f"Numerical Fields: {len(record.numerical_fields)}")
        print(f"Categorical Fields: {len(record.categorical_fields)}")
```

### TXT Interview Ingestion

```python
from Data_Engine.ingestion import SurveysInterviewsIngester
from pathlib import Path

# Initialize ingester
ingester = SurveysInterviewsIngester(
    source_name="11_labs_interviews",
    survey_name="Interview1"
)

# Ingest TXT file with chunking
txt_file = Path("bucket2_survey_interviews/11_labs_interviews/Interview1.txt")

# Ingest with custom chunking parameters
for record in ingester.ingest(
    txt_file,
    chunk_size=1000,      # Characters per chunk
    chunk_overlap=200     # Overlap between chunks
):
    print(f"Chunk {record.chunk_index}: {len(record.raw_text)} chars")
    print(f"Text: {record.raw_text[:200]}...")
```

## Parameters

### CSV Ingestion

- `file_path` (Path): Path to CSV file
- `brand_column` (Optional[str]): Column name containing brand information
- Additional kwargs are passed through

### TXT Ingestion

- `file_path` (Path): Path to TXT file
- `chunk_size` (int): Size of text chunks in characters (default: 1000)
- `chunk_overlap` (int): Overlap between chunks in characters (default: 200)

## Data Files

Survey CSV files are located in:
- `bucket2_survey_interviews/survey_interviews/`

Interview TXT files are located in:
- `bucket2_survey_interviews/11_labs_interviews/`

## Field Classification

The ingester automatically classifies CSV columns:

- **Text Columns**: Columns with average value length > 20 characters (free-text answers)
- **Numerical Fields**: Integer and float columns
- **Categorical Fields**: Object columns with < 20 unique values (Likert scales, rankings)
- **Structured Fields**: Other object columns with many unique values

## Output

All records are returned as `DataRecord` objects with:
- `bucket_id`: Set to `BucketType.SURVEYS_INTERVIEWS.value` (2)
- `source_name`: Name of the source
- `source_type`: `SourceType.CSV.value` or `SourceType.TXT.value`
- `raw_text`: Combined free-text from CSV or chunked text from TXT
- `structured_fields`: Dictionary of structured field values
- `numerical_fields`: Dictionary of numerical values
- `categorical_fields`: Dictionary of categorical values
- `metadata`: Additional metadata including survey name, response index, file path, etc.

