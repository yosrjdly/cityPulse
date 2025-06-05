#!/usr/bin/env python
"""
Example script demonstrating the metadata tracking system in CityPulse.

This script shows how to:
1. Create and manage metadata schemas
2. Generate metadata templates
3. Extract and enhance metadata from files
4. Validate metadata against schemas
5. Integrate with the data versioning system
"""

import os
import sys
import json
import pandas as pd
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.io.metadata_manager import (
    get_metadata_manager,
    MetadataEnhancer
)
from src.utils.io.data_versioning import get_versioning_system
from src.utils.logging import get_module_logger

# Initialize logger
logger = get_module_logger(__name__)

# Example data directory
EXAMPLE_DATA_DIR = Path(__file__).parent.parent / "data" / "examples"
EXAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)


def create_example_data():
    """Create example data files for demonstration."""
    # Create a CSV file
    df = pd.DataFrame({
        'id': range(1, 101),
        'name': [f'Item {i}' for i in range(1, 101)],
        'value': [i * 2.5 for i in range(1, 101)],
        'category': ['A' if i % 3 == 0 else 'B' if i % 3 == 1 else 'C' for i in range(1, 101)]
    })
    
    csv_path = EXAMPLE_DATA_DIR / "sample_data.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Created example CSV file: {csv_path}")
    
    return csv_path


def demonstrate_metadata_schemas():
    """Demonstrate creating and using metadata schemas."""
    logger.info("\n=== Demonstrating Metadata Schemas ===")
    
    # Get metadata manager
    metadata_manager = get_metadata_manager()
    
    # Get the default schema
    default_schema = metadata_manager.get_schema('default')
    logger.info(f"Default schema: {default_schema.name}")
    logger.info(f"Required fields: {default_schema.required_fields}")
    
    # Create a custom schema for tabular data
    tabular_fields = {
        'title': {'type': 'string', 'description': 'Dataset title'},
        'description': {'type': 'string', 'description': 'Dataset description'},
        'row_count': {'type': 'number', 'description': 'Number of rows'},
        'column_count': {'type': 'number', 'description': 'Number of columns'},
        'columns': {'type': 'array', 'description': 'List of column names'},
        'dtypes': {'type': 'object', 'description': 'Column data types'},
        'source': {'type': 'string', 'description': 'Data source'},
        'license': {'type': 'string', 'description': 'Data license'},
        'version': {'type': 'string', 'description': 'Dataset version'},
        'created_at': {'type': 'string', 'description': 'Creation timestamp'},
        'updated_at': {'type': 'string', 'description': 'Update timestamp'},
        'created_by': {'type': 'string', 'description': 'Creator'},
        'tags': {'type': 'array', 'description': 'Dataset tags'},
    }
    
    required_tabular_fields = {
        'title', 'description', 'row_count', 'column_count', 
        'columns', 'source', 'version', 'created_at'
    }
    
    tabular_schema = metadata_manager.create_schema(
        name='tabular',
        description='Schema for tabular datasets',
        fields=tabular_fields,
        required_fields=required_tabular_fields
    )
    
    logger.info(f"Created tabular schema with {len(tabular_schema.fields)} fields")
    logger.info(f"Required fields: {tabular_schema.required_fields}")
    
    # Generate a metadata template
    template = metadata_manager.generate_metadata_template('tabular', include_optional=True)
    logger.info(f"Generated template with {len(template)} fields")
    
    return metadata_manager


def demonstrate_metadata_extraction(file_path, metadata_manager):
    """Demonstrate extracting and enhancing metadata from files."""
    logger.info("\n=== Demonstrating Metadata Extraction ===")
    
    # Extract basic metadata
    basic_metadata = metadata_manager.extract_metadata_from_file(file_path)
    logger.info(f"Extracted basic metadata with {len(basic_metadata)} fields")
    
    # Enhance metadata for tabular data
    enhanced_metadata = MetadataEnhancer.enhance_tabular_metadata(file_path, basic_metadata)
    logger.info(f"Enhanced metadata with {len(enhanced_metadata)} fields")
    
    # Add some custom metadata
    enhanced_metadata.update({
        'tags': ['example', 'demo', 'tabular'],
        'domain': 'demonstration',
        'purpose': 'Showing metadata capabilities',
        'quality': 'high'
    })
    
    # Categorize metadata
    categorized = metadata_manager.categorize_metadata(enhanced_metadata)
    logger.info(f"Categorized metadata into {len(categorized)} categories")
    
    for category, fields in categorized.items():
        logger.info(f"  {category}: {len(fields)} fields")
    
    return enhanced_metadata


def demonstrate_metadata_validation(metadata, metadata_manager):
    """Demonstrate validating metadata against schemas."""
    logger.info("\n=== Demonstrating Metadata Validation ===")
    
    # Validate against default schema
    is_valid_default, errors_default = metadata_manager.validate_metadata(metadata, 'default')
    logger.info(f"Validation against default schema: {'Valid' if is_valid_default else 'Invalid'}")
    if not is_valid_default:
        logger.info(f"Errors: {errors_default}")
    
    # Validate against tabular schema
    is_valid_tabular, errors_tabular = metadata_manager.validate_metadata(metadata, 'tabular')
    logger.info(f"Validation against tabular schema: {'Valid' if is_valid_tabular else 'Invalid'}")
    if not is_valid_tabular:
        logger.info(f"Errors: {errors_tabular}")
    
    return is_valid_tabular


def demonstrate_integration_with_versioning(file_path, metadata):
    """Demonstrate integration with the data versioning system."""
    logger.info("\n=== Demonstrating Integration with Versioning ===")
    
    # Get versioning system
    versioning_system = get_versioning_system()
    
    # Register dataset with metadata
    version = versioning_system.register_dataset(
        dataset_name="example_dataset",
        file_path=str(file_path),
        metadata=metadata
    )
    
    logger.info(f"Registered dataset with version ID: {version.version_id}")
    logger.info(f"Metadata fields in version: {len(version.metadata)}")
    
    # Update metadata
    versioning_system.update_metadata(
        version_id=version.version_id,
        metadata={'quality_checked': True, 'quality_score': 0.95}
    )
    
    # Get updated version
    updated_version = versioning_system.get_version(version.version_id)
    logger.info(f"Updated metadata fields: {len(updated_version.metadata)}")
    
    return updated_version


def main():
    """Run the metadata example."""
    logger.info("Starting metadata example")
    
    # Create example data
    file_path = create_example_data()
    
    # Demonstrate metadata schemas
    metadata_manager = demonstrate_metadata_schemas()
    
    # Demonstrate metadata extraction
    metadata = demonstrate_metadata_extraction(file_path, metadata_manager)
    
    # Demonstrate metadata validation
    is_valid = demonstrate_metadata_validation(metadata, metadata_manager)
    
    # Demonstrate integration with versioning
    if is_valid:
        version = demonstrate_integration_with_versioning(file_path, metadata)
    
    logger.info("Metadata example completed")


if __name__ == "__main__":
    main() 