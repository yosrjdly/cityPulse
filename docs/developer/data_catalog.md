# Data Catalog System

## Overview

The data catalog system provides a centralized registry for tracking, discovering, and managing datasets throughout the CityPulse project. It enables dataset registration, schema inference, metadata management, and advanced search capabilities.

## Key Features

- **Dataset Registration**: Register datasets with rich metadata and automatic schema inference
- **Schema Management**: Track column types, statistics, and relationships
- **Search & Discovery**: Find datasets by name, description, tags, or category
- **Metadata Management**: Store and update arbitrary metadata for each dataset
- **Export & Import**: Export and import catalog data in multiple formats
- **Integration with Versioning**: Connect with the data versioning system for complete lineage tracking

## Core Components

### DatasetSchema

A dataclass representing a dataset's schema with the following attributes:

- `columns`: List of column definitions with name, type, and statistics
- `primary_key`: Optional list of column names forming the primary key
- `foreign_keys`: List of foreign key relationships

### DatasetEntry

A dataclass representing an entry in the data catalog with the following attributes:

- `dataset_id`: Unique identifier for the dataset
- `name`: Human-readable name
- `description`: Detailed description
- `file_path`: Path to the dataset file
- `format`: File format (csv, parquet, json, etc.)
- `category`: Dataset category (raw, processed, external, etc.)
- `tags`: List of tags for categorization
- `schema`: Optional DatasetSchema object
- `metadata`: Dictionary of additional metadata
- `version_id`: Optional reference to version in the versioning system
- `created_at`: Creation timestamp
- `updated_at`: Last update timestamp

### DataCatalog

The main class for managing the dataset catalog with the following key methods:

- `register_dataset()`: Register a new dataset with automatic schema inference
- `get_entry()`: Get a specific entry by ID
- `list_entries()`: List entries with optional filtering
- `search_entries()`: Search for entries by text query
- `update_entry()`: Update an existing entry
- `delete_entry()`: Delete an entry
- `export_catalog()`: Export catalog to JSON, YAML, or CSV
- `import_catalog()`: Import catalog from external file
- `get_statistics()`: Get statistics about the catalog

## Usage Examples

### Basic Usage

```python
from src.utils.io.data_catalog import DataCatalog

# Initialize the catalog
catalog = DataCatalog()

# Register a dataset
dataset_id = catalog.register_dataset(
    name="Example Dataset",
    description="An example dataset for demonstration",
    file_path="data/raw/example.csv",
    format="csv",
    category="raw",
    tags=["example", "demo"],
    metadata={"source": "synthetic", "rows": 1000},
    infer_schema=True
)

# Get an entry
entry = catalog.get_entry(dataset_id)
print(f"Dataset name: {entry.name}")
print(f"Dataset path: {entry.file_path}")
```

### Searching and Filtering

```python
# List all raw datasets
raw_datasets = catalog.list_entries(category="raw")

# Search by text
search_results = catalog.search_entries("population")

# Filter by tags
tagged_entries = catalog.list_entries(tags=["census", "demographics"])

# Filter by format
csv_entries = catalog.list_entries(format="csv")
```

### Working with Schema

```python
# Get schema for a dataset
entry = catalog.get_entry(dataset_id)
schema = entry.schema

if schema:
    print(f"Number of columns: {len(schema.columns)}")
    
    # Print column information
    for column in schema.columns:
        print(f"Column: {column['name']}, Type: {column['type']}")
        print(f"Statistics: {column['stats']}")
```

### Exporting and Importing

```python
# Export catalog to JSON
json_path = catalog.export_catalog(output_format="json")

# Export catalog to CSV
csv_path = catalog.export_catalog(output_format="csv")

# Import catalog from file
catalog.import_catalog("path/to/catalog.json", merge=True)
```

## Implementation Details

### Catalog Storage

The catalog is stored as a JSON file in the `data/catalog` directory. Each entry is serialized to JSON format with special handling for the schema information.

### Schema Inference

When registering a dataset with `infer_schema=True`, the system will:

1. Read the dataset file based on its format (CSV, Parquet, JSON)
2. Extract column names and types
3. Compute basic statistics for each column
4. Create a DatasetSchema object with this information

### Integration with Versioning

The data catalog can integrate with the data versioning system by:

1. Registering datasets with the versioning system when `register_version=True`
2. Storing the version ID in the catalog entry
3. Allowing retrieval of version information through the versioning system

## Best Practices

1. **Always register datasets**: Register datasets as soon as they are created or imported
2. **Use meaningful tags**: Add relevant tags to make datasets discoverable
3. **Provide rich descriptions**: Include detailed descriptions to help users understand the dataset
4. **Keep metadata updated**: Update metadata when datasets change
5. **Use categories consistently**: Stick to a consistent set of categories (raw, processed, external, etc.)

## Performance Considerations

- **Schema inference** can be slow for large files. Set `infer_schema=False` when registering large datasets if performance is a concern.
- The catalog is loaded into memory on initialization, so it's efficient for lookups.
- For very large catalogs, consider using the export/import functionality to work with subsets.

## Error Handling

The catalog system includes comprehensive error handling:

- File not found errors when registering datasets
- Schema inference errors
- Serialization/deserialization errors
- Logging of all errors and warnings

## Future Enhancements

1. Database backend for catalog storage
2. Advanced search capabilities with full-text indexing
3. Data quality metrics integration
4. Schema evolution tracking
5. Access control and permissions 