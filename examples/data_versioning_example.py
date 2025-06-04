#!/usr/bin/env python3
"""
Example script demonstrating the data versioning system.

This script shows how to use the data versioning system to track dataset versions
and their relationships.
"""

import os
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.io.data_versioning import DataVersioningSystem, VersionedDataset
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


def transform_dataset(input_path, output_path):
    """Apply a simple transformation to a dataset.
    
    Args:
        input_path: Path to input dataset
        output_path: Path to save transformed dataset
    """
    # Create directory if it doesn't exist
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    
    # Read input dataset
    df = pd.read_csv(input_path)
    
    # Apply transformation (normalize each column)
    for column in df.columns:
        if df[column].dtype == np.float64 or df[column].dtype == np.int64:
            df[column] = (df[column] - df[column].mean()) / df[column].std()
    
    # Add a new column
    df['transformed'] = True
    
    # Save to CSV
    df.to_csv(output_path, index=False)
    logger.info(f"Transformed dataset saved to {output_path}")
    
    return df


def main():
    """Run the data versioning example."""
    # Initialize versioning system
    versioning = DataVersioningSystem()
    logger.info("Initialized data versioning system")
    
    # Create and register raw dataset
    raw_path = os.path.join(RAW_DATA_DIR, "sample_data.csv")
    create_sample_dataset(raw_path, rows=100, columns=5)
    
    raw_dataset = VersionedDataset(
        dataset_name="sample_data",
        file_path=raw_path,
        metadata={
            "source": "synthetic",
            "rows": 100,
            "columns": 5,
            "description": "Sample dataset for demonstration"
        }
    )
    
    raw_version_id = raw_dataset.register()
    logger.info(f"Registered raw dataset with version ID: {raw_version_id}")
    
    # Transform and register processed dataset
    processed_path = os.path.join(PROCESSED_DATA_DIR, "normalized_data.csv")
    transform_dataset(raw_path, processed_path)
    
    # Create derived dataset
    processed_dataset = raw_dataset.create_derived_dataset(
        new_file_path=processed_path,
        derived_name="normalized_data",
        additional_metadata={
            "transformation": "normalization",
            "columns_added": ["transformed"]
        }
    )
    
    processed_version_id = processed_dataset.register()
    logger.info(f"Registered processed dataset with version ID: {processed_version_id}")
    
    # Get lineage of processed dataset
    lineage = versioning.get_lineage(processed_version_id)
    logger.info(f"Lineage of processed dataset: {[v.dataset_name for v in lineage]}")
    
    # Compare versions
    comparison = versioning.compare_versions(raw_version_id, processed_version_id)
    logger.info("Comparison of raw and processed datasets:")
    for key, value in comparison.items():
        logger.info(f"  {key}: {value}")
    
    # Create another version with different parameters
    raw_path2 = os.path.join(RAW_DATA_DIR, "sample_data_v2.csv")
    create_sample_dataset(raw_path2, rows=200, columns=8)
    
    raw_dataset2 = VersionedDataset(
        dataset_name="sample_data",  # Same name, different version
        file_path=raw_path2,
        metadata={
            "source": "synthetic",
            "rows": 200,
            "columns": 8,
            "description": "Larger sample dataset"
        }
    )
    
    raw_version_id2 = raw_dataset2.register()
    logger.info(f"Registered second raw dataset with version ID: {raw_version_id2}")
    
    # Get all versions of the dataset
    all_versions = versioning.get_dataset_versions("sample_data")
    logger.info(f"All versions of 'sample_data': {len(all_versions)}")
    for v in all_versions:
        logger.info(f"  {v.version_id}: {v.timestamp}, {v.metadata.get('rows')} rows")
    
    # Get latest version
    latest = versioning.get_latest_version("sample_data")
    logger.info(f"Latest version of 'sample_data': {latest.version_id}, {latest.timestamp}")
    
    logger.info("Data versioning example completed successfully")


if __name__ == "__main__":
    main() 