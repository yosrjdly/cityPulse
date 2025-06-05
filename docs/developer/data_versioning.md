# Data Versioning System

## Overview

The data versioning system provides a robust way to track datasets throughout their lifecycle in the CityPulse project. It enables version tracking, lineage tracking, and comparison between different versions of the same dataset.

## Key Features

- **Version Tracking**: Register and track different versions of datasets
- **Lineage Tracking**: Track relationships between datasets (parent-child)
- **Metadata Management**: Store and update metadata for each dataset version
- **Hash-based Verification**: Compute and store file hashes for integrity checking
- **Version Comparison**: Compare different versions of datasets
- **Derived Datasets**: Create and track derived datasets with clear lineage

## Core Components

### DatasetVersion

A dataclass representing a specific version of a dataset with the following attributes:

- `version_id`: Unique identifier for the version
- `dataset_name`: Name of the dataset
- `timestamp`: Creation timestamp
- `file_path`: Path to the dataset file
- `parent_versions`: List of parent version IDs
- `metadata`: Dictionary of metadata
- `hash_value`: Hash of the file contents

### DataVersioningSystem

The main class for managing dataset versions with the following key methods:

- `register_dataset()`: Register a new dataset version
- `get_version()`: Get a specific version by ID
- `get_dataset_versions()`: Get all versions of a dataset
- `get_latest_version()`: Get the latest version of a dataset
- `create_version_copy()`: Create a copy of a specific version
- `get_lineage()`: Get the complete lineage of a version
- `compare_versions()`: Compare two versions
- `delete_version()`: Delete a version
- `update_metadata()`: Update metadata for a version

### VersionedDataset

A higher-level class for working with versioned datasets:

- `register()`: Register the dataset with the versioning system
- `get_lineage()`: Get the lineage of the dataset
- `create_derived_dataset()`: Create a derived dataset

## Usage Examples

### Basic Usage

```python
from src.utils.io.data_versioning import DataVersioningSystem

# Initialize the versioning system
versioning = DataVersioningSystem()

# Register a dataset
version = versioning.register_dataset(
    dataset_name="example_dataset",
    file_path="data/raw/example.csv",
    metadata={"source": "example", "rows": 1000}
)

# Get the latest version of a dataset
latest = versioning.get_latest_version("example_dataset")
```

### Working with Derived Datasets

```python
from src.utils.io.data_versioning import VersionedDataset

# Create a versioned dataset
raw_dataset = VersionedDataset(
    dataset_name="raw_data",
    file_path="data/raw/data.csv",
    metadata={"source": "example", "rows": 1000}
)
raw_version_id = raw_dataset.register()

# Create a derived dataset
processed_dataset = raw_dataset.create_derived_dataset(
    new_file_path="data/processed/processed_data.csv",
    derived_name="processed_data",
    additional_metadata={"transformation": "normalization"}
)
processed_version_id = processed_dataset.register()

# Get lineage
lineage = processed_dataset.get_lineage()
```

### Comparing Versions

```python
# Compare two versions
comparison = versioning.compare_versions(version_id1, version_id2)
print(f"Same dataset: {comparison['same_dataset']}")
print(f"Time difference: {comparison['time_difference']}")
print(f"Same hash: {comparison['same_hash']}")
```

## Implementation Details

### Version Storage

Dataset version information is stored as JSON files in the `.versions` directory inside the data directory. Each version is stored in a separate file named with the version ID.

### File Hashing

File hashes are computed using the SHA-256 algorithm by default. The hash is computed by reading the file in chunks to support large files.

### Lineage Tracking

Lineage is tracked through parent-child relationships. Each dataset version can have multiple parent versions, allowing for complex derivation trees.

## Best Practices

1. **Always register raw datasets**: Register datasets as soon as they are created or imported
2. **Use meaningful metadata**: Include relevant information like source, row count, and description
3. **Create derived datasets properly**: Use the `create_derived_dataset()` method to maintain lineage
4. **Check dataset integrity**: Use hash values to verify dataset integrity
5. **Use version IDs in filenames**: When creating copies, include version IDs in filenames

## Performance Considerations

- **File hashing** can be slow for large files. Set `compute_hash=False` when registering large datasets if performance is a concern.
- The versioning system **caches version information** in memory to improve performance.
- **Version lookups** are fast as they use an in-memory cache.

## Error Handling

The versioning system includes comprehensive error handling:

- File not found errors when registering datasets
- Version not found errors when retrieving versions
- Error handling for file operations
- Logging of all errors and warnings

## Future Enhancements

1. Database backend for version storage
2. Support for distributed version tracking
3. Integration with external version control systems
4. Advanced diff operations between dataset versions
5. Automatic version pruning for storage management 