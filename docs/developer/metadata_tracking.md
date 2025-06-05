# Metadata Tracking System

The CityPulse metadata tracking system provides a comprehensive framework for managing, validating, and tracking metadata associated with datasets throughout the data processing pipeline.

## Overview

Metadata is critical for understanding, discovering, and properly using datasets. The metadata tracking system in CityPulse provides:

- **Schema-based validation**: Define and enforce metadata schemas for different types of data
- **Automatic extraction**: Extract basic metadata from files automatically
- **Enhanced metadata**: Add domain-specific metadata for different data types (tabular, geospatial, etc.)
- **Categorization**: Organize metadata into logical categories
- **Integration**: Seamless integration with the data versioning system

## Key Components

### MetadataSchema

The `MetadataSchema` class defines the structure and validation rules for metadata:

- **Fields**: Defines the expected fields and their properties
- **Required fields**: Specifies which fields must be present
- **Validation**: Validates metadata against the schema rules

### MetadataManager

The `MetadataManager` class is the main interface for working with metadata:

- **Schema management**: Create, retrieve, and manage metadata schemas
- **Validation**: Validate metadata against schemas
- **Template generation**: Generate metadata templates based on schemas
- **Extraction**: Extract basic metadata from files
- **Categorization**: Organize metadata into logical categories

### MetadataEnhancer

The `MetadataEnhancer` class provides utilities for enriching metadata with additional information:

- **Tabular data**: Extract row counts, column information, data types, etc.
- **Geospatial data**: Extract bounds, feature counts, geometry types, etc.
- **Image data**: Extract dimensions, format, EXIF data, etc.

## Standard Metadata Fields

The system defines a set of standard metadata fields that should be present in all datasets:

| Field | Description | Type |
|-------|-------------|------|
| title | Dataset title | string |
| description | Dataset description | string |
| created_at | Creation timestamp | string (ISO format) |
| updated_at | Update timestamp | string (ISO format) |
| created_by | Creator | string |
| source | Data source | string |
| license | Data license | string |
| version | Dataset version | string |

## Metadata Categories

Metadata is organized into the following categories:

| Category | Description | Example Fields |
|----------|-------------|----------------|
| basic | Basic dataset information | title, description, created_at |
| provenance | Origin and lineage | source, license, version |
| technical | Technical characteristics | format, encoding, schema |
| spatial | Geospatial properties | spatial_coverage, crs, bbox |
| temporal | Time-related properties | temporal_coverage, frequency |
| quality | Data quality metrics | completeness, accuracy |
| domain | Domain-specific tags | domain_tags, keywords |
| usage | Usage information | access_rights, limitations |

## Usage Examples

### Creating a Metadata Schema

```python
from src.utils.io.metadata_manager import get_metadata_manager

# Get metadata manager
metadata_manager = get_metadata_manager()

# Define fields for a custom schema
fields = {
    'title': {'type': 'string', 'description': 'Dataset title'},
    'description': {'type': 'string', 'description': 'Dataset description'},
    'row_count': {'type': 'number', 'description': 'Number of rows'},
    # ... more fields
}

# Define required fields
required_fields = {'title', 'description', 'row_count'}

# Create the schema
schema = metadata_manager.create_schema(
    name='my_schema',
    description='My custom schema',
    fields=fields,
    required_fields=required_fields
)
```

### Extracting and Enhancing Metadata

```python
from src.utils.io.metadata_manager import get_metadata_manager, MetadataEnhancer

# Get metadata manager
metadata_manager = get_metadata_manager()

# Extract basic metadata
basic_metadata = metadata_manager.extract_metadata_from_file('path/to/file.csv')

# Enhance for tabular data
enhanced_metadata = MetadataEnhancer.enhance_tabular_metadata('path/to/file.csv', basic_metadata)

# Add custom metadata
enhanced_metadata.update({
    'tags': ['example', 'demo'],
    'quality': 'high'
})
```

### Validating Metadata

```python
from src.utils.io.metadata_manager import get_metadata_manager

# Get metadata manager
metadata_manager = get_metadata_manager()

# Validate metadata against a schema
is_valid, errors = metadata_manager.validate_metadata(metadata, 'my_schema')

if not is_valid:
    print(f"Validation errors: {errors}")
```

### Integration with Data Versioning

```python
from src.utils.io.metadata_manager import get_metadata_manager
from src.utils.io.data_versioning import get_versioning_system

# Get metadata and versioning systems
metadata_manager = get_metadata_manager()
versioning_system = get_versioning_system()

# Extract and enhance metadata
metadata = metadata_manager.extract_metadata_from_file('path/to/file.csv')
enhanced_metadata = MetadataEnhancer.enhance_tabular_metadata('path/to/file.csv', metadata)

# Register dataset with metadata
version = versioning_system.register_dataset(
    dataset_name="my_dataset",
    file_path="path/to/file.csv",
    metadata=enhanced_metadata
)
```

## Best Practices

1. **Define domain-specific schemas**: Create schemas for different types of data (tabular, geospatial, etc.)
2. **Automate metadata extraction**: Use the enhancers to automatically extract metadata when possible
3. **Validate early and often**: Validate metadata as early as possible in the data pipeline
4. **Use categorization**: Organize metadata into categories for better readability
5. **Integrate with versioning**: Always associate metadata with dataset versions

## Implementation Details

### File Structure

- `src/utils/io/metadata_manager.py`: Main implementation of the metadata tracking system
- `data/.schemas/`: Directory for storing metadata schemas

### Dependencies

The metadata tracking system depends on:

- `src.utils.logging`: For logging
- `config.settings`: For configuration settings

## Future Enhancements

1. **Additional enhancers**: Add support for more file types and data formats
2. **Search capabilities**: Implement metadata-based dataset search
3. **UI integration**: Create a user interface for browsing and editing metadata
4. **Export/import**: Add support for exporting and importing metadata in standard formats (e.g., Dublin Core, DCAT)
5. **Versioned schemas**: Add versioning for metadata schemas 