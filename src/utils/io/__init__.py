"""
IO utilities for CityPulse.

This package contains utilities for input/output operations, including data versioning,
data catalog, metadata tracking, and file management.
"""

from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

# Import key components for easier access
from src.utils.io.data_versioning import (
    DataVersioningSystem,
    DatasetVersion,
    VersionedDataset,
    get_versioning_system
)

from src.utils.io.data_catalog import (
    DataCatalog,
    DatasetEntry,
    DatasetSchema,
    get_catalog
)

from src.utils.io.metadata_manager import get_metadata_manager, MetadataEnhancer, MetadataSchema

__all__ = [
    'DataVersioningSystem',
    'DatasetVersion',
    'VersionedDataset',
    'get_versioning_system',
    'DataCatalog',
    'DatasetEntry',
    'DatasetSchema',
    'get_catalog',
    'get_metadata_manager',
    'MetadataEnhancer',
    'MetadataSchema'
]