#!/usr/bin/env python3
"""
Example script demonstrating the data catalog system.

This script shows how to use the data catalog system to manage and discover datasets.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.io.data_catalog import DataCatalog, DatasetEntry, DatasetSchema
from src.utils.io.data_versioning import get_versioning_system
from config.settings import RAW_DATA_DIR, PROCESSED_DATA_DIR
from src.utils.logging import get_module_logger

# Initialize logger
logger = get_module_logger(__name__)


def create_sample_dataset(file_path, rows=100, columns=5):
    """Create a sample dataset for demonstration purposes.
    
    Args:
        file_path: Path to save the dataset
        rows: Number of rows
        columns: Number of columns
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # Create random data
    data = np.random.rand(rows, columns)
    column_names = [f"feature_{i}" for i in range(columns)]
    
    # Create DataFrame
    df = pd.DataFrame(data, columns=column_names)
    
    # Save to CSV
    df.to_csv(file_path, index=False)
    logger.info(f"Created sample dataset with {rows} rows and {columns} columns at {file_path}")
    
    return df


def main():
    """Run the data catalog example."""
    # Initialize catalog
    catalog = DataCatalog()
    logger.info("Initialized data catalog")
    
    # Create and register raw datasets
    raw_path1 = os.path.join(RAW_DATA_DIR, "sample_data1.csv")
    create_sample_dataset(raw_path1, rows=100, columns=5)
    
    dataset_id1 = catalog.register_dataset(
        name="Sample Dataset 1",
        description="First sample dataset for demonstration",
        file_path=raw_path1,
        format="csv",
        category="raw",
        tags=["sample", "demo", "small"],
        metadata={
            "source": "synthetic",
            "rows": 100,
            "columns": 5,
            "description": "Small sample dataset"
        },
        infer_schema=True
    )
    logger.info(f"Registered first dataset with ID: {dataset_id1}")
    
    # Create and register a second dataset
    raw_path2 = os.path.join(RAW_DATA_DIR, "sample_data2.csv")
    create_sample_dataset(raw_path2, rows=1000, columns=10)
    
    dataset_id2 = catalog.register_dataset(
        name="Sample Dataset 2",
        description="Second sample dataset for demonstration",
        file_path=raw_path2,
        format="csv",
        category="raw",
        tags=["sample", "demo", "large"],
        metadata={
            "source": "synthetic",
            "rows": 1000,
            "columns": 10,
            "description": "Large sample dataset"
        },
        infer_schema=True
    )
    logger.info(f"Registered second dataset with ID: {dataset_id2}")
    
    # Create a processed dataset
    processed_path = os.path.join(PROCESSED_DATA_DIR, "processed_data.csv")
    
    # Read raw data, perform simple processing, and save
    df = pd.read_csv(raw_path1)
    df_processed = df.copy()
    
    # Normalize columns
    for col in df_processed.columns:
        if df_processed[col].dtype == np.float64:
            df_processed[col] = (df_processed[col] - df_processed[col].mean()) / df_processed[col].std()
    
    # Add a new column
    df_processed['processed'] = True
    
    # Save processed data
    os.makedirs(os.path.dirname(processed_path), exist_ok=True)
    df_processed.to_csv(processed_path, index=False)
    
    # Get the raw dataset entry
    raw_entry = catalog.get_entry(dataset_id1)
    
    # Register the processed dataset with lineage to raw dataset
    dataset_id3 = catalog.register_dataset(
        name="Processed Dataset",
        description="Processed version of Sample Dataset 1",
        file_path=processed_path,
        format="csv",
        category="processed",
        tags=["processed", "normalized"],
        metadata={
            "source_dataset": dataset_id1,
            "processing_type": "normalization",
            "columns_added": ["processed"]
        },
        infer_schema=True,
        register_version=True
    )
    logger.info(f"Registered processed dataset with ID: {dataset_id3}")
    
    # List all datasets
    all_entries = catalog.list_entries()
    logger.info(f"Total datasets in catalog: {len(all_entries)}")
    
    # List raw datasets
    raw_entries = catalog.list_entries(category="raw")
    logger.info(f"Raw datasets in catalog: {len(raw_entries)}")
    for entry in raw_entries:
        logger.info(f"  - {entry.name} ({entry.dataset_id}): {entry.description}")
    
    # Search for datasets
    search_results = catalog.search_entries("sample")
    logger.info(f"Search results for 'sample': {len(search_results)}")
    
    # Filter by tags
    tagged_entries = catalog.list_entries(tags=["demo"])
    logger.info(f"Datasets with tag 'demo': {len(tagged_entries)}")
    
    # Get catalog statistics
    stats = catalog.get_statistics()
    logger.info("Catalog statistics:")
    logger.info(f"  Total entries: {stats['total_entries']}")
    logger.info(f"  Categories: {stats['categories']}")
    logger.info(f"  Formats: {stats['formats']}")
    logger.info(f"  Tags: {stats['tags']}")
    logger.info(f"  With schema: {stats['with_schema']}")
    logger.info(f"  With version: {stats['with_version']}")
    
    # Export catalog to different formats
    json_path = catalog.export_catalog(output_format="json")
    logger.info(f"Exported catalog to JSON: {json_path}")
    
    csv_path = catalog.export_catalog(output_format="csv")
    logger.info(f"Exported catalog to CSV: {csv_path}")
    
    # Update an entry
    catalog.update_entry(dataset_id1, {
        "description": "Updated description for Sample Dataset 1",
        "tags": ["sample", "demo", "small", "updated"]
    })
    logger.info("Updated dataset entry")
    
    # Verify the update
    updated_entry = catalog.get_entry(dataset_id1)
    logger.info(f"Updated description: {updated_entry.description}")
    logger.info(f"Updated tags: {updated_entry.tags}")
    
    logger.info("Data catalog example completed successfully")


if __name__ == "__main__":
    main() 