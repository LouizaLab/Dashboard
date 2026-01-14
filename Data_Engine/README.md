# Data Engine

A production-ready, modular data ingestion, indexing, and retrieval system designed for heterogeneous data sources. Built to power preference modeling, behavioral dynamics, and market inference systems.

## Table of Contents

1. [Overview](#overview)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Architecture](#architecture)
5. [Data Buckets](#data-buckets)
6. [Core Concepts](#core-concepts)
7. [Usage Examples](#usage-examples)
8. [Advanced Usage](#advanced-usage)
9. [API Reference](#api-reference)
10. [Running Examples](#running-examples)
11. [Troubleshooting](#troubleshooting)
12. [Future Enhancements](#future-enhancements)
13. [Contributing](#contributing)

## Overview

The Data Engine provides a unified interface for ingesting, normalizing, indexing, and retrieving data from multiple sources. It's designed to be:

- **Modular**: Clean separation of concerns across layers
- **Extensible**: Easy to add new data sources or swap implementations
- **Production-ready**: Built for real deployments and investor demos
- **Agent-ready**: APIs designed for RAG pipelines, LangGraph, and multi-agent systems

## Installation

### Quick Install

```bash
# Minimum required dependencies
pip install pandas numpy

# For semantic search (vector embeddings)
pip install faiss-cpu sentence-transformers

# Or for GPU support (if you have CUDA)
pip install faiss-gpu sentence-transformers
```

### Installation Options

#### Option 1: Basic (No Semantic Search)

If you only need structured queries (no semantic search), you can skip FAISS:

```bash
pip install pandas numpy
```

Then use the engine without embeddings:

```python
from Data_Engine.data_engine import DataEngine
from pathlib import Path

engine = DataEngine(storage_dir=Path("./storage"))
# Don't set embedding_fn
# Don't use generate_embeddings=True
```

#### Option 2: Full Installation (With Semantic Search)

For semantic similarity search, install FAISS:

```bash
pip install pandas numpy faiss-cpu sentence-transformers
```

Then use with embeddings:

```python
from Data_Engine.data_engine import DataEngine
from sentence_transformers import SentenceTransformer
from pathlib import Path

engine = DataEngine(storage_dir=Path("./storage"))
encoder = SentenceTransformer('all-MiniLM-L6-v2')
engine.set_embedding_fn(lambda text: encoder.encode(text))

# Now you can use semantic search
engine.index_records(records, generate_embeddings=True)
results = engine.search("your query")
```

### macOS Installation

On macOS, you might need:

```bash
# Install via conda (recommended for macOS)
conda install -c conda-forge faiss-cpu

# Or use pip
pip install faiss-cpu
```

### Verify Installation

Run the test script:

```bash
python Data_Engine/test_imports.py
```

## Quick Start

### Step 1: Import and Initialize

**Important**: Run scripts from the `Consumer_Engine` directory (parent of `Data_Engine`), not from inside `Data_Engine`.

```python
from pathlib import Path
from Data_Engine.data_engine import DataEngine
from sentence_transformers import SentenceTransformer

# Initialize the engine
engine = DataEngine(storage_dir=Path("./data_engine_storage"))

# Set up embedding function (for semantic search)
encoder = SentenceTransformer('all-MiniLM-L6-v2')
engine.set_embedding_fn(lambda text: encoder.encode(text))
```

### Step 2: Ingest Data

```python
# Example: Ingest a CSV file (Bucket 1 - Online Datasets)
records = engine.ingest_online_dataset(
    file_path=Path("path/to/your/data.csv"),
    source_name="my_dataset",
    text_columns=["description", "name"],  # Columns to use as text
    brand_column="brand"  # Column containing brand name
)

print(f"Ingested {len(records)} records")
```

### Step 3: Index Records

```python
# Index with embeddings for semantic search
engine.index_records(
    records,
    generate_embeddings=True,  # Generate embeddings
    enrich_text=True,          # Clean text
    enrich_sentiment=False     # Skip sentiment (not implemented yet)
)

print("Records indexed!")
```

### Step 4: Query Data

```python
# Semantic search
results = engine.search("juicy burger", top_k=10)
for record in results:
    print(f"- {record.structured_fields.get('name', 'N/A')}")

# Query by brand
mcd_records = engine.get_by_brand("McDonald's", limit=20)

# Query with filters
results = engine.search(
    "breakfast",
    filters={"brand": "McDonald's", "bucket_id": 1},
    top_k=5
)
```

## Architecture

### System Overview

The Data Engine is a modular, production-ready system for ingesting, normalizing, indexing, and retrieving heterogeneous data. It's designed as the foundation for preference modeling, behavioral dynamics, and market inference.

### Layer Architecture

```
┌─────────────────────────────────────────────────────────┐
│                  RETRIEVAL LAYER                        │
│  (Agent-ready APIs: semantic, filters, hybrid queries)  │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
┌─────────────────────────────────────────────────────────┐
│                   INDEXING LAYER                        │
│  (Multi-index: structured, semantic, metadata)          │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
┌─────────────────────────────────────────────────────────┐
│                  ENRICHMENT LAYER                       │
│  (Optional: text cleaning, sentiment, clustering)       │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
┌─────────────────────────────────────────────────────────┐
│                NORMALIZATION LAYER                      │
│  (Unified DataRecord schema)                            │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
┌─────────────────────────────────────────────────────────┐
│                  INGESTION LAYER                        │
│  (Bucket 1-4: datasets, surveys, financial, scraped)    │
└─────────────────────────────────────────────────────────┘
                           ▲
                           │
┌─────────────────────────────────────────────────────────┐
│                   STORAGE LAYER                         │
│  (Abstract interfaces: local, cloud, vector stores)      │
└─────────────────────────────────────────────────────────┘
```

### Data Flow

```
Raw Data (CSV/TXT/Scraped)
    ↓
Ingestion Module (Bucket-specific)
    ↓
DataRecord (Unified Schema)
    ↓
Enrichment Pipeline (Optional)
    ↓
Index Manager
    ├──→ Storage Backend (Raw records)
    ├──→ Vector Store (Embeddings)
    └──→ Metadata Store (Indexes)
    ↓
Retrieval Manager
    ↓
Query Results (DataRecord objects)
```

### Component Structure

```
Data_Engine/
├── core/                    # Core schema and exceptions
│   ├── schema.py           # DataRecord unified schema
│   └── exceptions.py        # Custom exceptions
├── ingestion/               # Data ingestion layer
│   ├── base.py             # Base ingestion class
│   ├── bucket1_online_datasets.py
│   ├── bucket2_surveys_interviews.py
│   ├── bucket3_financial_data.py
│   └── bucket4_scrapers/   # Scrapers (TODO)
├── enrichment/              # Optional enrichment pipelines
│   ├── base.py
│   ├── text_cleaner.py
│   └── sentiment_analyzer.py
├── indexing/                # Multi-indexing system
│   └── index_manager.py
├── storage/                 # Storage layer (abstract interfaces)
│   ├── interfaces.py       # Abstract storage interfaces
│   └── local_storage.py    # Local file-based implementation
├── retrieval/               # Retrieval layer
│   └── retrieval_manager.py
├── examples/                # Example scripts
└── data_engine.py          # Main orchestration class
```

### Component Details

#### 1. Core Schema (`core/`)

**DataRecord**: Unified data structure
- All data becomes a DataRecord
- Supports structured, numerical, categorical fields
- Optional embeddings and sentiment
- Rich metadata tracking

**BucketType**: Enum for 4 data buckets
**SourceType**: Enum for data formats

#### 2. Ingestion Layer (`ingestion/`)

**Base Class**: `IngestionBase`
- Abstract interface for all ingesters
- File validation
- Record generation

**Bucket Implementations**:
- `bucket1_online_datasets.py`: CSV from Kaggle/public datasets
- `bucket2_surveys_interviews.py`: CSV surveys + TXT interviews
- `bucket3_financial_data.py`: Financial/foot-traffic CSV
- `bucket4_scrapers/`: Scrapers (Google Reviews, Reddit, etc.)

#### 3. Normalization Layer

**Unified Schema**: All data → DataRecord
- CSV rows → structured_fields + numerical_fields + categorical_fields
- TXT files → chunked raw_text records
- Scraped content → brand-tagged raw_text records

#### 4. Enrichment Layer (`enrichment/`)

**Modular Pipelines**:
- `TextCleaner`: Remove URLs, normalize whitespace
- `SentimentAnalyzer`: Analyze sentiment (TODO: integrate models)
- Extensible: Add custom enrichment pipelines

#### 5. Indexing Layer (`indexing/`)

**IndexManager**: Orchestrates multi-indexing
- Coordinates storage, vector store, metadata store
- Batch indexing support
- Embedding integration

**Three Index Types**:
1. **Structured Index**: Metadata, filters, categories
2. **Semantic Index**: Vector embeddings (FAISS)
3. **Metadata Index**: Brand, time, bucket, client

#### 6. Storage Layer (`storage/`)

**Abstract Interfaces**:
- `StorageBackend`: Raw record storage
- `VectorStore`: Embedding storage
- `MetadataStore`: Metadata indexing

**Local Implementations**:
- `LocalStorageBackend`: JSON file storage
- `LocalVectorStore`: FAISS-based vectors
- `LocalMetadataStore`: JSON-based metadata index

**Swappable**: Can swap to PostgreSQL, Pinecone, S3, etc.

#### 7. Retrieval Layer (`retrieval/`)

**RetrievalManager**: Agent-ready APIs
- `query_by_text()`: Semantic similarity search
- `query_by_brand()`: Brand-based queries
- `query_by_bucket()`: Bucket-based queries
- `query_by_time_range()`: Time-based queries
- `hybrid_query()`: Combined semantic + filters

### Design Patterns

#### 1. Abstract Interfaces

Storage backends use abstract base classes, allowing easy swapping:

```python
# Can swap implementations without changing code
storage_backend = LocalStorageBackend(...)
# or
storage_backend = CloudStorageBackend(...)
```

#### 2. Modular Enrichment

Enrichment pipelines are optional and composable:

```python
# Apply only what you need
text_cleaner = TextCleaner()
sentiment_analyzer = SentimentAnalyzer()

# Chain enrichment
record = text_cleaner.enrich(record)
record = sentiment_analyzer.enrich(record)
```

#### 3. Unified Schema

All data becomes DataRecord, ensuring consistency:

```python
# CSV row → DataRecord
# TXT chunk → DataRecord
# Scraped content → DataRecord
# All queryable the same way
```

#### 4. Multi-Indexing

Three complementary indexes for different query types:

- **Structured**: Fast filtering by metadata
- **Semantic**: Similarity search by content
- **Metadata**: Quick lookups by brand/time/bucket

## Data Buckets

The system organizes data into 4 buckets:

### Bucket 1: Online Datasets
- **Source**: Kaggle, public datasets, research datasets
- **Format**: CSV ONLY
- **Examples**: Product reviews, food preference datasets, demographic tables
- **Characteristics**: Structured, column-driven, static or periodically updated

### Bucket 2: Internal Survey & Interview Data
- **Sources**: Team-uploaded CSV survey data, TXT files from qualitative interviews
- **CSV**: Likert scales, rankings, free-text answers
- **TXT**: Long-form interviews, transcripts
- **Characteristics**: Semi-structured, mixed quantitative + qualitative

### Bucket 3: Client Financial / Foot-Traffic Data
- **Sources**: Credit card aggregates, transaction summaries, foot traffic / mobility data
- **Format**: CSV
- **Characteristics**: Time-series heavy, sensitive metadata, client-scoped namespaces

### Bucket 4: Scraped Public Data (Automated)
- **Sources**: Google Reviews, Reddit, Twitter/X, Forums, Blog comments
- **Format**: Raw HTML → cleaned text → structured records
- **Characteristics**: Unstructured, high volume, sentiment-rich, brand-centric

## Core Concepts

### DataRecord

Every data point becomes a `DataRecord` with:

- `record_id`: Unique UUID
- `bucket_id`: Bucket type (1-4)
- `source_name`: Source identifier
- `source_type`: Format (csv, txt, scraped, json)
- `brand`: Brand name (if applicable)
- `timestamp`: Event time
- `ingestion_time`: When record was ingested
- `raw_text`: Text content
- `structured_fields`: Key-value pairs
- `numerical_fields`: Numerical values
- `categorical_fields`: Categorical values
- `sentiment`: Sentiment score (optional)
- `embedding`: Vector embedding (optional)
- `metadata`: Additional metadata
- `client_id`: Client identifier (for bucket 3)
- `chunk_index`: For chunked documents
- `parent_record_id`: For chunks, reference to parent

### Multi-Indexing

The system maintains three types of indexes:

1. **Structured Index**: Metadata, filters, categories
2. **Semantic Index**: Vector embeddings for similarity search
3. **Metadata Index**: Brand, time, bucket, client indexing

## Usage Examples

### Basic Usage

```python
from pathlib import Path
from Data_Engine.data_engine import DataEngine
from sentence_transformers import SentenceTransformer

# Initialize engine
engine = DataEngine(storage_dir=Path("./storage"))

# Set up embeddings (for semantic search)
encoder = SentenceTransformer('all-MiniLM-L6-v2')
engine.set_embedding_fn(lambda text: encoder.encode(text))

# Ingest online dataset (Bucket 1)
records = engine.ingest_online_dataset(
    file_path=Path("data/products.csv"),
    source_name="kaggle_food_reviews",
    text_columns=["description", "ingredients"],
    brand_column="brand"
)

# Index with embeddings
engine.index_records(records, generate_embeddings=True)

# Search
results = engine.search("juicy burger", top_k=10)
for record in results:
    print(record.structured_fields.get("name"))
```

### Ingest Survey Data

```python
# Ingest CSV survey
records = engine.ingest_survey(
    file_path=Path("data/survey.csv"),
    source_name="customer_survey_2024",
    brand_column="preferred_brand"
)

# Index
engine.index_records(records, generate_embeddings=True, enrich_text=True)
```

### Query by Brand

```python
# Get all records for a brand
mcd_records = engine.get_by_brand("McDonald's", limit=100)

# Filter by sentiment
positive_records = [
    r for r in mcd_records 
    if r.sentiment and r.sentiment > 0.5
]
```

### Hybrid Query

```python
# Semantic search with filters
results = engine.search(
    query="breakfast items",
    filters={
        "bucket_id": 1,
        "source_name": "mcdonalds_menu",
        "categorical_fields.Category": "Breakfast"
    },
    top_k=10
)
```

### Query Examples Script

For comprehensive query examples, run:

```bash
python Data_Engine/query_examples.py
```

This script demonstrates:
- Querying by brand, source, bucket
- Structured filtering (by category, numerical fields)
- Semantic search (if embeddings enabled)
- Hybrid queries (semantic + filters)
- Time-based queries
- Combining multiple queries

### Ingest Multiple Files

```python
files = [Path("data1.csv"), Path("data2.csv")]
all_records = []

for file in files:
    records = engine.ingest_online_dataset(
        file_path=file,
        source_name=f"dataset_{file.stem}"
    )
    all_records.extend(records)

engine.index_records(all_records, generate_embeddings=True)
```

### Query by Multiple Criteria

```python
# Get records matching multiple filters
results = engine.get_by_filters({
    "bucket_id": 1,
    "brand": "McDonald's",
    "categorical_fields.Category": "Burgers"
})
```

### Time-Based Queries

```python
from datetime import datetime, timedelta

start = datetime.now() - timedelta(days=30)
end = datetime.now()

recent_records = engine.get_by_time_range(start, end)
```

### Without Embeddings (Faster, Structured Only)

```python
# Index without embeddings (faster, but no semantic search)
engine.index_records(records, generate_embeddings=False)

# Still can query by filters
results = engine.get_by_brand("McDonald's")
results = engine.get_by_filters({"bucket_id": 1})
```

### Using with Your Existing Data

#### Quick Method: Use the Ingest Script

The easiest way to ingest all Phase 1 menu data:

```bash
# From Consumer_Engine directory
python Data_Engine/ingest_phase1_data.py
```

This script will:
- Find all CSV files in `Phase_1_Taste_Embedding_Model/data/raw/`
- Ingest them into the Data Engine
- Index them with optional embeddings
- Show you a summary

#### Manual Method: Ingest Individual Files

```python
from pathlib import Path
from Data_Engine.data_engine import DataEngine
from sentence_transformers import SentenceTransformer

# Initialize
engine = DataEngine(storage_dir=Path("./storage"))
encoder = SentenceTransformer('all-MiniLM-L6-v2')
engine.set_embedding_fn(lambda text: encoder.encode(text))

# Ingest McDonald's CSV
mcd_file = Path("../Phase_1_Taste_Embedding_Model/data/raw/mcdonalds.csv")
if mcd_file.exists():
    records = engine.ingest_online_dataset(
        file_path=mcd_file,
        source_name="mcdonalds_menu",
        text_columns=["Item", "Category"],
        brand_column="Item"
    )
    
    # Index
    engine.index_records(records, generate_embeddings=True)
    
    # Search
    results = engine.search("burger", top_k=5)
    for r in results:
        print(r.structured_fields.get("Item"))
```

#### Ingest Multiple Files

```python
from pathlib import Path
from Data_Engine.data_engine import DataEngine

engine = DataEngine(storage_dir=Path("./storage"))

# Path to Phase 1 data
data_dir = Path("../Phase_1_Taste_Embedding_Model/data/raw")

# List of files to ingest
files_to_ingest = [
    ("mcdonalds.csv", "mcdonalds_menu", ["Item", "Category"], "Item"),
    ("burger-king-menu.csv", "burger_king_menu", ["ITEM", "CATEGORY"], "ITEM"),
    ("wendys-menu.csv", "wendys_menu", ["Item", "Category"], "Item"),
]

all_records = []

for filename, source_name, text_cols, brand_col in files_to_ingest:
    file_path = data_dir / filename
    if file_path.exists():
        records = engine.ingest_online_dataset(
            file_path=file_path,
            source_name=source_name,
            text_columns=text_cols,
            brand_column=brand_col
        )
        all_records.extend(list(records))

# Index all at once
engine.index_records(all_records, generate_embeddings=True)
```

## Advanced Usage

### Custom Ingestion

```python
from Data_Engine.ingestion.bucket1_online_datasets import OnlineDatasetsIngester

ingester = OnlineDatasetsIngester(source_name="my_dataset")
records = list(ingester.ingest(
    Path("data.csv"),
    text_columns=["description"],
    brand_column="brand"
))
```

### Custom Enrichment

```python
from Data_Engine.enrichment.base import EnrichmentPipeline
from Data_Engine.core.schema import DataRecord

class CustomEnrichment(EnrichmentPipeline):
    def enrich(self, record: DataRecord) -> DataRecord:
        # Your enrichment logic
        record.metadata['custom_field'] = 'value'
        return record

# Use in pipeline
enrichment = CustomEnrichment()
enriched = enrichment.enrich(record)
```

### Direct Index Management

```python
from Data_Engine.indexing.index_manager import IndexManager
import numpy as np

index_manager = IndexManager(storage_dir=Path("./storage"))

# Index with embeddings
embeddings = np.array([...])  # Shape: [n_records, embedding_dim]
index_manager.index_batch(records, embeddings)
```

### Custom Storage Backend

```python
from Data_Engine.storage.interfaces import StorageBackend

class CloudStorageBackend(StorageBackend):
    def save_record(self, record):
        # Upload to S3, etc.
        pass
    # ... implement other methods

# Use custom backend
index_manager = IndexManager(
    storage_dir=Path("./storage"),
    storage_backend=CloudStorageBackend()
)
```

### Integration with Phase 1 Embeddings

You can use the Phase 1 taste embedding model:

```python
from Phase_1_Taste_Embedding_Model.text_encoder_simple import SentenceTransformerWrapper

# Load Phase 1 encoder
encoder = SentenceTransformerWrapper('all-MiniLM-L6-v2')

# Use with Data Engine
engine.set_embedding_fn(lambda text: encoder.encode(text))
```

## API Reference

### DataEngine

Main orchestration class.

**Methods:**
- `ingest_online_dataset()`: Ingest Bucket 1 data
- `ingest_survey()`: Ingest Bucket 2 data
- `ingest_financial_data()`: Ingest Bucket 3 data
- `index_records()`: Index records with optional enrichment
- `search()`: Semantic search
- `get_by_brand()`: Query by brand
- `get_by_bucket()`: Query by bucket
- `get_by_time_range()`: Query by time range
- `get_by_filters()`: Query by arbitrary filters
- `set_embedding_fn()`: Set embedding function for semantic search

### RetrievalManager

Low-level retrieval APIs.

**Methods:**
- `query_by_text()`: Semantic similarity search
- `query_by_brand()`: Brand-based query
- `query_by_bucket()`: Bucket-based query
- `query_by_time_range()`: Time-based query
- `hybrid_query()`: Combined semantic + filter query
- `query_by_filters()`: Query by arbitrary filters

### IndexManager

Index management APIs.

**Methods:**
- `index_record()`: Index a single record
- `index_batch()`: Index multiple records in batch
- `get_record()`: Get a record by ID
- `delete_record()`: Delete a record from all indexes

## Running Examples

### Quick Start Workflow

```bash
# 1. First, ingest your data
python Data_Engine/ingest_phase1_data.py

# 2. Then, learn how to query it
python Data_Engine/query_examples.py
```

### Option 1: Run from Consumer_Engine directory (Recommended)

```bash
# Navigate to Consumer_Engine
cd /Users/rohitganti/Desktop/Consumer_Engine

# Ingest data
python Data_Engine/ingest_phase1_data.py

# Query examples
python Data_Engine/query_examples.py

# Other examples
python Data_Engine/examples/quick_start_example.py
python Data_Engine/examples/use_with_existing_data.py
```

### Option 2: Run from Data_Engine directory

```bash
# Navigate to Data_Engine
cd Data_Engine

# Run examples
python examples/quick_start_example.py
python examples/use_with_existing_data.py
```

### Example Scripts

1. **`ingest_phase1_data.py`**: **Quick script to ingest all Phase 1 menu data**
   - Automatically finds CSV files in Phase 1 data folder
   - Ingests and indexes all menu data
   - Run with: `python Data_Engine/ingest_phase1_data.py`

2. **`query_examples.py`**: **Comprehensive query examples**
   - Shows all query methods: brand, source, filters, semantic search
   - Demonstrates hybrid queries and time-based queries
   - Run with: `python Data_Engine/query_examples.py`
   - **Use this to learn how to query your data!**

3. **`quick_start_example.py`**: Complete example with sample data
   - Data ingestion
   - Indexing with/without embeddings
   - Semantic search
   - Structured queries

4. **`use_with_existing_data.py`**: Uses your existing menu data from Phase 1
   - Ingesting multiple CSV files
   - Indexing menu items
   - Querying by brand, source, etc.

5. **`example_bucket1.py`**: Bucket 1 (Online Datasets) specific example

6. **`example_bucket2.py`**: Bucket 2 (Surveys & Interviews) specific example

7. **`example_bucket3.py`**: Bucket 3 (Financial Data) specific example

8. **`example_semantic_search.py`**: Semantic search focused example

### Import in Your Own Scripts

#### If running from Consumer_Engine directory:

```python
from Data_Engine.data_engine import DataEngine
```

#### If running from Data_Engine directory:

```python
# Add parent to path first
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Data_Engine.data_engine import DataEngine
```

## Troubleshooting

### FAISS Import Error

If you see `ModuleNotFoundError: No module named 'faiss'`:

1. Install FAISS:
   ```bash
   pip install faiss-cpu
   ```

2. Or use the engine without embeddings (see Installation Options above)

### Missing sentence-transformers

If you see `ModuleNotFoundError: No module named 'sentence_transformers'`:
- Install: `pip install sentence-transformers`
- Or run examples without semantic search (they'll skip those features)

### Missing FAISS

If you see FAISS-related errors:
- Install: `pip install faiss-cpu`
- Or use `generate_embeddings=False` when indexing

### Import Errors

If you see `ImportError: attempted relative import beyond top-level package`:

1. Make sure you're running from the correct directory
2. Check that `Data_Engine` is a package (has `__init__.py`)
3. Try running from `Consumer_Engine` directory instead

### Encoding Errors

CSV files with non-UTF-8 encoding are automatically handled. The system tries multiple encodings:
- UTF-8 (default)
- latin-1
- iso-8859-1
- cp1252

### Validation Errors

If you see "Invalid record" errors, check:
- Record has a `source_name`
- Record has `bucket_id` between 1-4
- Record has at least some data (text, structured, numerical, or categorical fields)

## Future Enhancements

### High Priority

#### Sentiment Analysis Integration
- [ ] Integrate TextBlob for basic sentiment analysis
- [ ] Integrate VADER for social media sentiment
- [ ] Add transformers-based sentiment models (e.g., roberta-base-sentiment)
- [ ] Create sentiment enrichment pipeline that works with all buckets
- [ ] Add sentiment filtering to retrieval APIs

#### Scraper Implementations
- [ ] Google Reviews scraper using Google Places API
- [ ] Reddit scraper using PRAW (Python Reddit API Wrapper)
- [ ] Twitter/X scraper (API or web scraping with rate limiting)
- [ ] Forum/blog comment scrapers
- [ ] Rate limiting and legal compliance for all scrapers

#### Embedding Integration
- [ ] Integrate Phase 1 taste embedding model
- [ ] Support multiple embedding models (sentence-transformers, OpenAI, custom)
- [ ] Batch embedding generation optimization
- [ ] Embedding caching for repeated queries

### Medium Priority

#### Storage Backends
- [ ] PostgreSQL backend for structured data
- [ ] MongoDB backend for flexible schemas
- [ ] S3/cloud storage backend
- [ ] Pinecone integration for vector store
- [ ] Weaviate integration for vector store

#### Enrichment Pipelines
- [ ] Topic clustering (LDA, BERTopic)
- [ ] Brand/entity extraction (spaCy NER)
- [ ] Named entity recognition
- [ ] Text summarization for long documents
- [ ] Language detection

#### Performance Optimizations
- [ ] Batch processing for large datasets
- [ ] Parallel ingestion
- [ ] Incremental indexing
- [ ] Index compression
- [ ] Query result caching

#### Monitoring & Logging
- [ ] Structured logging
- [ ] Ingestion metrics
- [ ] Query performance metrics
- [ ] Index health monitoring
- [ ] Error tracking and alerting

### Low Priority / Future

#### LangGraph Integration
- [ ] LangGraph agent that uses Data Engine
- [ ] Multi-agent query orchestration
- [ ] Agent memory using Data Engine

#### RAG Pipeline
- [ ] RAG pipeline using Data Engine as knowledge base
- [ ] Context retrieval for LLM prompts
- [ ] Citation tracking

#### Advanced Features
- [ ] Data versioning
- [ ] Data lineage tracking
- [ ] Data quality checks
- [ ] Automated schema inference
- [ ] Data deduplication

#### UI/Dashboard
- [ ] Web dashboard for data exploration
- [ ] Query interface
- [ ] Data visualization
- [ ] Ingestion monitoring dashboard

### Integration Points

#### Phase 1: Taste Embedding Model
- [x] Basic integration structure
- [ ] Full integration with pre-trained models
- [ ] Use Phase 1 embeddings for product-related queries

#### Phase 2: Behavioral Dynamic Engine
- [ ] Integration point for behavioral data ingestion
- [ ] Time-series data support
- [ ] Behavioral pattern indexing

#### Phase 3: Large Population Model
- [ ] Population-level data aggregation
- [ ] Statistical query support
- [ ] Cohort analysis support

### Notes

- All scrapers must respect rate limits and terms of service
- Sentiment analysis should be pluggable (multiple models)
- Storage backends should be swappable without code changes
- All APIs should be async-ready for future async support

## Contributing

When adding new features:

1. Follow the existing architecture patterns
2. Use abstract interfaces for storage/vector stores
3. Add comprehensive docstrings
4. Include example usage
5. Update this README

### Extension Points

#### Adding a New Bucket

1. Create new ingester inheriting from `IngestionBase`
2. Implement `validate_file()` and `ingest()`
3. Add to `DataEngine` main class
4. Update documentation

#### Adding a New Storage Backend

1. Implement interface (`StorageBackend`, `VectorStore`, or `MetadataStore`)
2. Pass to `IndexManager` constructor
3. No other code changes needed

#### Adding a New Enrichment Pipeline

1. Create class inheriting from `EnrichmentPipeline`
2. Implement `enrich()` method
3. Use in `DataEngine.index_records()` or directly

#### Adding a New Scraper

1. Create scraper inheriting from `BaseScraper`
2. Implement `scrape()` method
3. Add to `bucket4_scrapers/`

## Design Principles

1. **Modularity**: Each layer is independent and swappable
2. **Extensibility**: Easy to add new buckets, scrapers, or enrichment pipelines
3. **Production-ready**: Error handling, logging, validation
4. **Agent-ready**: APIs designed for RAG and multi-agent systems
5. **Future-proof**: Designed for LangGraph, RAG, and evolving use cases

## License

Part of the Consumer Engine project.
