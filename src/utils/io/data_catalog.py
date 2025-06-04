"""
Data catalog module for CityPulse.

This module provides utilities for cataloging, discovering, and managing datasets
across the project, including metadata, schema information, and access patterns.
"""

import os
import sys
import json
import yaml
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Set
from dataclasses import dataclass, field, asdict
import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logging import get_module_logger
from src.utils.io.data_versioning import get_versioning_system, DatasetVersion
from config.settings import DATA_DIR, RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR, EXTERNAL_DATA_DIR

# Initialize logger
logger = get_module_logger(__name__)


@dataclass
class DatasetSchema:
    """Class representing a dataset schema."""
    
    columns: List[Dict[str, Any]]
    primary_key: Optional[List[str]] = None
    foreign_keys: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetSchema':
        """Create from dictionary representation."""
        return cls(**data)
    
    @classmethod
    def from_dataframe(cls, df: pd.DataFrame, primary_key: Optional[List[str]] = None) -> 'DatasetSchema':
        """Create schema from pandas DataFrame.
        
        Args:
            df: DataFrame to extract schema from
            primary_key: List of column names forming the primary key
            
        Returns:
            DatasetSchema object
        """
        columns = []
        for col_name, dtype in df.dtypes.items():
            # Get basic statistics for the column
            stats = {}
            try:
                if pd.api.types.is_numeric_dtype(dtype):
                    stats = {
                        "min": float(df[col_name].min()),
                        "max": float(df[col_name].max()),
                        "mean": float(df[col_name].mean()),
                        "null_count": int(df[col_name].isna().sum())
                    }
                elif pd.api.types.is_string_dtype(dtype):
                    stats = {
                        "unique_count": int(df[col_name].nunique()),
                        "null_count": int(df[col_name].isna().sum()),
                        "max_length": int(df[col_name].str.len().max() if not df[col_name].empty else 0)
                    }
                else:
                    stats = {
                        "unique_count": int(df[col_name].nunique()),
                        "null_count": int(df[col_name].isna().sum())
                    }
            except Exception as e:
                logger.warning(f"Error computing statistics for column {col_name}: {e}")
                stats = {"null_count": int(df[col_name].isna().sum())}
                
            columns.append({
                "name": str(col_name),
                "type": str(dtype),
                "stats": stats
            })
        
        return cls(columns=columns, primary_key=primary_key)


@dataclass
class DatasetEntry:
    """Class representing an entry in the data catalog."""
    
    dataset_id: str
    name: str
    description: str
    file_path: str
    format: str  # csv, parquet, json, etc.
    category: str  # raw, processed, external, etc.
    tags: List[str] = field(default_factory=list)
    schema: Optional[DatasetSchema] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    version_id: Optional[str] = None
    created_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.datetime.now().isoformat())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = asdict(self)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetEntry':
        """Create from dictionary representation."""
        # Handle schema conversion
        schema_data = data.pop("schema", None)
        if schema_data:
            schema = DatasetSchema.from_dict(schema_data)
        else:
            schema = None
            
        return cls(schema=schema, **data)


class DataCatalog:
    """Class for managing a catalog of datasets."""
    
    def __init__(
        self,
        catalog_dir: Optional[str] = None,
        auto_create_dirs: bool = True
    ):
        """Initialize the data catalog.
        
        Args:
            catalog_dir: Directory to store catalog information
            auto_create_dirs: Whether to automatically create directories
        """
        self.catalog_dir = Path(catalog_dir) if catalog_dir else Path(DATA_DIR) / 'catalog'
        self.catalog_file = self.catalog_dir / 'catalog.json'
        
        # Create catalog directory if it doesn't exist
        if auto_create_dirs and not self.catalog_dir.exists():
            self.catalog_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created catalog directory: {self.catalog_dir}")
        
        # Dictionary to store catalog entries
        self._entries: Dict[str, DatasetEntry] = {}
        
        # Load existing catalog
        self._load_catalog()
    
    def _load_catalog(self):
        """Load existing catalog from disk."""
        if not self.catalog_file.exists():
            logger.info(f"Catalog file does not exist: {self.catalog_file}")
            return
        
        try:
            with open(self.catalog_file, 'r') as f:
                catalog_data = json.load(f)
            
            for entry_data in catalog_data.get("entries", []):
                try:
                    entry = DatasetEntry.from_dict(entry_data)
                    self._entries[entry.dataset_id] = entry
                except Exception as e:
                    logger.error(f"Error loading catalog entry: {e}")
                    
            logger.info(f"Loaded {len(self._entries)} entries from catalog")
            
        except Exception as e:
            logger.error(f"Error loading catalog: {e}")
    
    def _save_catalog(self):
        """Save catalog to disk."""
        try:
            catalog_data = {
                "version": "1.0",
                "updated_at": datetime.datetime.now().isoformat(),
                "entries": [entry.to_dict() for entry in self._entries.values()]
            }
            
            with open(self.catalog_file, 'w') as f:
                json.dump(catalog_data, f, indent=2)
                
            logger.info(f"Saved catalog with {len(self._entries)} entries")
            
        except Exception as e:
            logger.error(f"Error saving catalog: {e}")
    
    def add_entry(self, entry: DatasetEntry) -> bool:
        """Add an entry to the catalog.
        
        Args:
            entry: DatasetEntry to add
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Update timestamps
            entry.updated_at = datetime.datetime.now().isoformat()
            
            # Add to catalog
            self._entries[entry.dataset_id] = entry
            
            # Save catalog
            self._save_catalog()
            
            logger.info(f"Added entry to catalog: {entry.name} ({entry.dataset_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error adding entry to catalog: {e}")
            return False
    
    def get_entry(self, dataset_id: str) -> Optional[DatasetEntry]:
        """Get an entry from the catalog.
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            DatasetEntry or None if not found
        """
        return self._entries.get(dataset_id)
    
    def list_entries(
        self,
        category: Optional[str] = None,
        tags: Optional[List[str]] = None,
        format: Optional[str] = None
    ) -> List[DatasetEntry]:
        """List entries in the catalog, optionally filtered.
        
        Args:
            category: Filter by category
            tags: Filter by tags (must have all tags)
            format: Filter by format
            
        Returns:
            List of DatasetEntry objects
        """
        entries = list(self._entries.values())
        
        # Apply filters
        if category:
            entries = [e for e in entries if e.category == category]
        
        if tags:
            entries = [e for e in entries if all(tag in e.tags for tag in tags)]
        
        if format:
            entries = [e for e in entries if e.format == format]
        
        return entries
    
    def search_entries(self, query: str) -> List[DatasetEntry]:
        """Search for entries in the catalog.
        
        Args:
            query: Search query
            
        Returns:
            List of matching DatasetEntry objects
        """
        query = query.lower()
        results = []
        
        for entry in self._entries.values():
            # Search in name, description, and tags
            if (query in entry.name.lower() or
                query in entry.description.lower() or
                any(query in tag.lower() for tag in entry.tags)):
                results.append(entry)
        
        return results
    
    def update_entry(self, dataset_id: str, updates: Dict[str, Any]) -> bool:
        """Update an existing entry in the catalog.
        
        Args:
            dataset_id: ID of the dataset to update
            updates: Dictionary of updates to apply
            
        Returns:
            True if successful, False otherwise
        """
        if dataset_id not in self._entries:
            logger.warning(f"Entry not found: {dataset_id}")
            return False
        
        try:
            entry = self._entries[dataset_id]
            
            # Update fields
            for key, value in updates.items():
                if hasattr(entry, key):
                    setattr(entry, key, value)
            
            # Update timestamp
            entry.updated_at = datetime.datetime.now().isoformat()
            
            # Save catalog
            self._save_catalog()
            
            logger.info(f"Updated entry in catalog: {entry.name} ({entry.dataset_id})")
            return True
            
        except Exception as e:
            logger.error(f"Error updating entry in catalog: {e}")
            return False
    
    def delete_entry(self, dataset_id: str) -> bool:
        """Delete an entry from the catalog.
        
        Args:
            dataset_id: ID of the dataset to delete
            
        Returns:
            True if successful, False otherwise
        """
        if dataset_id not in self._entries:
            logger.warning(f"Entry not found: {dataset_id}")
            return False
        
        try:
            # Remove from catalog
            del self._entries[dataset_id]
            
            # Save catalog
            self._save_catalog()
            
            logger.info(f"Deleted entry from catalog: {dataset_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting entry from catalog: {e}")
            return False
    
    def register_dataset(
        self,
        name: str,
        description: str,
        file_path: str,
        format: str,
        category: str,
        tags: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        infer_schema: bool = True,
        primary_key: Optional[List[str]] = None,
        register_version: bool = True
    ) -> Optional[str]:
        """Register a new dataset in the catalog.
        
        Args:
            name: Name of the dataset
            description: Description of the dataset
            file_path: Path to the dataset file
            format: Format of the dataset (csv, parquet, json, etc.)
            category: Category of the dataset (raw, processed, external, etc.)
            tags: List of tags for the dataset
            metadata: Additional metadata
            infer_schema: Whether to infer schema from the dataset
            primary_key: List of column names forming the primary key
            register_version: Whether to register with the versioning system
            
        Returns:
            Dataset ID if successful, None otherwise
        """
        try:
            # Ensure file exists
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"Dataset file not found: {file_path}")
            
            # Generate dataset ID
            dataset_id = f"{name.lower().replace(' ', '_')}_{datetime.datetime.now().strftime('%Y%m%d%H%M%S')}"
            
            # Infer schema if requested
            schema = None
            if infer_schema:
                try:
                    if format.lower() == 'csv':
                        df = pd.read_csv(file_path)
                    elif format.lower() == 'parquet':
                        df = pd.read_parquet(file_path)
                    elif format.lower() == 'json':
                        df = pd.read_json(file_path)
                    else:
                        logger.warning(f"Schema inference not supported for format: {format}")
                        df = None
                    
                    if df is not None:
                        schema = DatasetSchema.from_dataframe(df, primary_key)
                        
                except Exception as e:
                    logger.error(f"Error inferring schema: {e}")
            
            # Register with versioning system if requested
            version_id = None
            if register_version:
                try:
                    versioning = get_versioning_system()
                    version = versioning.register_dataset(
                        dataset_name=name,
                        file_path=file_path,
                        metadata=metadata or {}
                    )
                    version_id = version.version_id
                    
                except Exception as e:
                    logger.error(f"Error registering with versioning system: {e}")
            
            # Create entry
            entry = DatasetEntry(
                dataset_id=dataset_id,
                name=name,
                description=description,
                file_path=file_path,
                format=format,
                category=category,
                tags=tags or [],
                schema=schema,
                metadata=metadata or {},
                version_id=version_id
            )
            
            # Add to catalog
            if self.add_entry(entry):
                return dataset_id
            else:
                return None
                
        except Exception as e:
            logger.error(f"Error registering dataset: {e}")
            return None
    
    def export_catalog(self, output_format: str = 'json', output_path: Optional[str] = None) -> Optional[str]:
        """Export the catalog to a file.
        
        Args:
            output_format: Format to export (json, yaml, csv)
            output_path: Path to save the export
            
        Returns:
            Path to the exported file or None if failed
        """
        if not output_path:
            output_path = self.catalog_dir / f"catalog_export.{output_format}"
        
        try:
            if output_format.lower() == 'json':
                catalog_data = {
                    "version": "1.0",
                    "exported_at": datetime.datetime.now().isoformat(),
                    "entries": [entry.to_dict() for entry in self._entries.values()]
                }
                
                with open(output_path, 'w') as f:
                    json.dump(catalog_data, f, indent=2)
                    
            elif output_format.lower() == 'yaml':
                catalog_data = {
                    "version": "1.0",
                    "exported_at": datetime.datetime.now().isoformat(),
                    "entries": [entry.to_dict() for entry in self._entries.values()]
                }
                
                with open(output_path, 'w') as f:
                    yaml.dump(catalog_data, f)
                    
            elif output_format.lower() == 'csv':
                # Create a flattened version for CSV
                rows = []
                for entry in self._entries.values():
                    row = {
                        "dataset_id": entry.dataset_id,
                        "name": entry.name,
                        "description": entry.description,
                        "file_path": entry.file_path,
                        "format": entry.format,
                        "category": entry.category,
                        "tags": ",".join(entry.tags),
                        "version_id": entry.version_id or "",
                        "created_at": entry.created_at,
                        "updated_at": entry.updated_at
                    }
                    rows.append(row)
                
                df = pd.DataFrame(rows)
                df.to_csv(output_path, index=False)
                
            else:
                logger.error(f"Unsupported export format: {output_format}")
                return None
                
            logger.info(f"Exported catalog to {output_path}")
            return str(output_path)
            
        except Exception as e:
            logger.error(f"Error exporting catalog: {e}")
            return None
    
    def import_catalog(self, input_path: str, merge: bool = True) -> bool:
        """Import a catalog from a file.
        
        Args:
            input_path: Path to the file to import
            merge: Whether to merge with existing catalog
            
        Returns:
            True if successful, False otherwise
        """
        try:
            # Determine format from file extension
            format = os.path.splitext(input_path)[1].lower().replace('.', '')
            
            if format == 'json':
                with open(input_path, 'r') as f:
                    catalog_data = json.load(f)
                    
            elif format == 'yaml' or format == 'yml':
                with open(input_path, 'r') as f:
                    catalog_data = yaml.safe_load(f)
                    
            else:
                logger.error(f"Unsupported import format: {format}")
                return False
            
            # Process entries
            entries = {}
            for entry_data in catalog_data.get("entries", []):
                try:
                    entry = DatasetEntry.from_dict(entry_data)
                    entries[entry.dataset_id] = entry
                except Exception as e:
                    logger.error(f"Error loading catalog entry: {e}")
            
            # Merge or replace
            if merge:
                self._entries.update(entries)
            else:
                self._entries = entries
            
            # Save catalog
            self._save_catalog()
            
            logger.info(f"Imported {len(entries)} entries from {input_path}")
            return True
            
        except Exception as e:
            logger.error(f"Error importing catalog: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the catalog.
        
        Returns:
            Dictionary with statistics
        """
        categories = {}
        formats = {}
        tags = {}
        
        for entry in self._entries.values():
            # Count by category
            categories[entry.category] = categories.get(entry.category, 0) + 1
            
            # Count by format
            formats[entry.format] = formats.get(entry.format, 0) + 1
            
            # Count by tag
            for tag in entry.tags:
                tags[tag] = tags.get(tag, 0) + 1
        
        return {
            "total_entries": len(self._entries),
            "categories": categories,
            "formats": formats,
            "tags": tags,
            "with_schema": sum(1 for e in self._entries.values() if e.schema is not None),
            "with_version": sum(1 for e in self._entries.values() if e.version_id is not None)
        }


def get_catalog() -> DataCatalog:
    """Get a singleton instance of the data catalog.
    
    Returns:
        DataCatalog instance
    """
    if not hasattr(get_catalog, "_instance"):
        get_catalog._instance = DataCatalog()
    
    return get_catalog._instance


# Example usage
if __name__ == "__main__":
    # Create catalog
    catalog = DataCatalog()
    
    # Register a dataset
    dataset_id = catalog.register_dataset(
        name="Example Dataset",
        description="An example dataset for demonstration",
        file_path="data/raw/example.csv",
        format="csv",
        category="raw",
        tags=["example", "demo"],
        metadata={"source": "synthetic", "rows": 1000}
    )
    
    print(f"Registered dataset: {dataset_id}")
    
    # List entries
    entries = catalog.list_entries(category="raw")
    print(f"Found {len(entries)} raw datasets")
    
    # Get statistics
    stats = catalog.get_statistics()
    print(f"Catalog statistics: {stats}")
    
    # Export catalog
    export_path = catalog.export_catalog(output_format="json")
    print(f"Exported catalog to: {export_path}") 