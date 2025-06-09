"""
Data versioning module for CityPulse.

This module provides utilities for versioning datasets, tracking changes, and managing
data lineage throughout the data processing pipeline.
"""

import os
import sys
import json
import hashlib
import datetime
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, Set
from dataclasses import dataclass, field, asdict
import uuid

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logging import get_module_logger
from config.settings import DATA_DIR, RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR

# Initialize logger
logger = get_module_logger(__name__)


@dataclass
class DatasetVersion:
    """Class representing a version of a dataset."""
    
    version_id: str
    dataset_name: str
    timestamp: str
    file_path: str
    parent_versions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    hash_value: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DatasetVersion':
        """Create from dictionary representation."""
        return cls(**data)


class DataVersioningSystem:
    """System for managing dataset versions and lineage."""
    
    def __init__(
        self,
        version_dir: Optional[str] = None,
        hash_algorithm: str = 'sha256',
        auto_create_dirs: bool = True
    ):
        """Initialize the data versioning system.
        
        Args:
            version_dir: Directory to store version information
            hash_algorithm: Algorithm to use for file hashing
            auto_create_dirs: Whether to automatically create directories
        """
        self.version_dir = Path(version_dir) if version_dir else Path(DATA_DIR) / '.versions'
        self.hash_algorithm = hash_algorithm
        
        # Create version directory if it doesn't exist
        if auto_create_dirs and not self.version_dir.exists():
            self.version_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created version directory: {self.version_dir}")
        
        # Dictionary to cache loaded versions
        self._version_cache: Dict[str, DatasetVersion] = {}
        
        # Load existing versions
        self._load_versions()
    
    def _load_versions(self):
        """Load existing versions from disk."""
        if not self.version_dir.exists():
            logger.warning(f"Version directory does not exist: {self.version_dir}")
            return
        
        for version_file in self.version_dir.glob('*.json'):
            try:
                with open(version_file, 'r') as f:
                    version_data = json.load(f)
                
                version = DatasetVersion.from_dict(version_data)
                self._version_cache[version.version_id] = version
                
            except Exception as e:
                logger.error(f"Error loading version file {version_file}: {e}")
    
    def _save_version(self, version: DatasetVersion):
        """Save version information to disk.
        
        Args:
            version: Dataset version to save
        """
        version_path = self.version_dir / f"{version.version_id}.json"
        
        with open(version_path, 'w') as f:
            json.dump(version.to_dict(), f, indent=2)
        
        logger.debug(f"Saved version information to {version_path}")
    
    def _compute_file_hash(self, file_path: str) -> str:
        """Compute hash of a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Hash value as a hexadecimal string
        """
        hash_obj = hashlib.new(self.hash_algorithm)
        
        with open(file_path, 'rb') as f:
            # Read in chunks to handle large files
            for chunk in iter(lambda: f.read(4096), b''):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
    
    def register_dataset(
        self,
        dataset_name: str,
        file_path: str,
        parent_versions: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
        compute_hash: bool = True
    ) -> DatasetVersion:
        """Register a new dataset version.
        
        Args:
            dataset_name: Name of the dataset
            file_path: Path to the dataset file
            parent_versions: List of parent version IDs
            metadata: Additional metadata
            compute_hash: Whether to compute file hash
            
        Returns:
            Created DatasetVersion object
        """
        # Ensure file exists
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        # Generate version ID
        version_id = str(uuid.uuid4())
        
        # Get current timestamp
        timestamp = datetime.datetime.now().isoformat()
        
        # Compute hash if requested
        hash_value = ""
        if compute_hash:
            try:
                hash_value = self._compute_file_hash(file_path)
                logger.debug(f"Computed hash for {file_path}: {hash_value}")
            except Exception as e:
                logger.error(f"Error computing hash for {file_path}: {e}")
        
        # Create version object
        version = DatasetVersion(
            version_id=version_id,
            dataset_name=dataset_name,
            timestamp=timestamp,
            file_path=file_path,
            parent_versions=parent_versions or [],
            metadata=metadata or {},
            hash_value=hash_value
        )
        
        # Save to cache and disk
        self._version_cache[version_id] = version
        self._save_version(version)
        
        logger.info(f"Registered new version of dataset '{dataset_name}': {version_id}")
        
        return version
    
    def get_version(self, version_id: str) -> Optional[DatasetVersion]:
        """Get a specific dataset version.
        
        Args:
            version_id: ID of the version to retrieve
            
        Returns:
            DatasetVersion object or None if not found
        """
        # Check cache first
        if version_id in self._version_cache:
            return self._version_cache[version_id]
        
        # Try to load from disk
        version_path = self.version_dir / f"{version_id}.json"
        if not version_path.exists():
            logger.warning(f"Version not found: {version_id}")
            return None
        
        try:
            with open(version_path, 'r') as f:
                version_data = json.load(f)
            
            version = DatasetVersion.from_dict(version_data)
            self._version_cache[version_id] = version
            return version
            
        except Exception as e:
            logger.error(f"Error loading version {version_id}: {e}")
            return None
    
    def get_dataset_versions(self, dataset_name: str) -> List[DatasetVersion]:
        """Get all versions of a specific dataset.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            List of DatasetVersion objects
        """
        return [v for v in self._version_cache.values() if v.dataset_name == dataset_name]
    
    def get_latest_version(self, dataset_name: str) -> Optional[DatasetVersion]:
        """Get the latest version of a dataset.
        
        Args:
            dataset_name: Name of the dataset
            
        Returns:
            Latest DatasetVersion or None if not found
        """
        versions = self.get_dataset_versions(dataset_name)
        
        if not versions:
            logger.warning(f"No versions found for dataset: {dataset_name}")
            return None
        
        # Sort by timestamp (newest first)
        versions.sort(key=lambda v: v.timestamp, reverse=True)
        return versions[0]
    
    def create_version_copy(
        self,
        version_id: str,
        target_dir: str,
        new_name: Optional[str] = None
    ) -> Optional[str]:
        """Create a copy of a specific dataset version.
        
        Args:
            version_id: ID of the version to copy
            target_dir: Directory to copy to
            new_name: New name for the copied file
            
        Returns:
            Path to the copied file or None if failed
        """
        version = self.get_version(version_id)
        if not version:
            logger.error(f"Version not found: {version_id}")
            return None
        
        source_path = version.file_path
        if not os.path.exists(source_path):
            logger.error(f"Source file not found: {source_path}")
            return None
        
        # Create target directory if it doesn't exist
        os.makedirs(target_dir, exist_ok=True)
        
        # Determine target filename
        if new_name:
            target_filename = new_name
        else:
            # Use original filename with version ID
            original_name = os.path.basename(source_path)
            name_parts = os.path.splitext(original_name)
            target_filename = f"{name_parts[0]}_{version_id[:8]}{name_parts[1]}"
        
        target_path = os.path.join(target_dir, target_filename)
        
        # Copy the file
        try:
            shutil.copy2(source_path, target_path)
            logger.info(f"Created copy of version {version_id} at {target_path}")
            return target_path
        except Exception as e:
            logger.error(f"Error creating version copy: {e}")
            return None
    
    def get_lineage(self, version_id: str) -> List[DatasetVersion]:
        """Get the complete lineage of a dataset version.
        
        Args:
            version_id: ID of the version
            
        Returns:
            List of ancestor DatasetVersion objects
        """
        version = self.get_version(version_id)
        if not version:
            logger.warning(f"Version not found: {version_id}")
            return []
        
        # Use set to avoid duplicates
        lineage_ids: Set[str] = set()
        to_process = version.parent_versions.copy()
        
        while to_process:
            current_id = to_process.pop(0)
            if current_id in lineage_ids:
                continue
                
            lineage_ids.add(current_id)
            
            parent = self.get_version(current_id)
            if parent:
                # Add parent's parents to processing queue
                to_process.extend([p for p in parent.parent_versions if p not in lineage_ids])
        
        # Convert IDs to actual version objects
        return [self.get_version(vid) for vid in lineage_ids if self.get_version(vid)]
    
    def compare_versions(
        self,
        version_id1: str,
        version_id2: str
    ) -> Dict[str, Any]:
        """Compare two dataset versions.
        
        Args:
            version_id1: ID of first version
            version_id2: ID of second version
            
        Returns:
            Dictionary with comparison results
        """
        v1 = self.get_version(version_id1)
        v2 = self.get_version(version_id2)
        
        if not v1 or not v2:
            missing = []
            if not v1:
                missing.append(version_id1)
            if not v2:
                missing.append(version_id2)
            logger.error(f"Versions not found: {', '.join(missing)}")
            return {"error": f"Versions not found: {', '.join(missing)}"}
        
        # Compare metadata keys
        v1_keys = set(v1.metadata.keys())
        v2_keys = set(v2.metadata.keys())
        
        # Get lineage IDs for comparison
        lineage1_ids = set(v.version_id for v in self.get_lineage(version_id1))
        lineage2_ids = set(v.version_id for v in self.get_lineage(version_id2))
        common_lineage_ids = lineage1_ids.intersection(lineage2_ids)
        
        return {
            "same_dataset": v1.dataset_name == v2.dataset_name,
            "time_difference": self._parse_timestamp_diff(v1.timestamp, v2.timestamp),
            "common_metadata_keys": list(v1_keys.intersection(v2_keys)),
            "v1_only_metadata": list(v1_keys - v2_keys),
            "v2_only_metadata": list(v2_keys - v1_keys),
            "same_hash": v1.hash_value == v2.hash_value if v1.hash_value and v2.hash_value else "Unknown",
            "common_lineage": list(common_lineage_ids)
        }
    
    def _parse_timestamp_diff(self, ts1: str, ts2: str) -> str:
        """Calculate the difference between two ISO timestamps.
        
        Args:
            ts1: First timestamp
            ts2: Second timestamp
            
        Returns:
            String describing the time difference
        """
        try:
            dt1 = datetime.datetime.fromisoformat(ts1)
            dt2 = datetime.datetime.fromisoformat(ts2)
            
            diff = abs(dt1 - dt2)
            
            if diff.days > 0:
                return f"{diff.days} days, {diff.seconds // 3600} hours"
            elif diff.seconds // 3600 > 0:
                return f"{diff.seconds // 3600} hours, {(diff.seconds % 3600) // 60} minutes"
            else:
                return f"{(diff.seconds % 3600) // 60} minutes, {diff.seconds % 60} seconds"
            
        except Exception as e:
            logger.error(f"Error parsing timestamps: {e}")
            return "Unknown"
    
    def delete_version(self, version_id: str, delete_file: bool = False) -> bool:
        """Delete a dataset version.
        
        Args:
            version_id: ID of the version to delete
            delete_file: Whether to also delete the dataset file
            
        Returns:
            True if successful, False otherwise
        """
        version = self.get_version(version_id)
        if not version:
            logger.warning(f"Version not found: {version_id}")
            return False
        
        # Delete the version file
        version_path = self.version_dir / f"{version_id}.json"
        if version_path.exists():
            try:
                version_path.unlink()
                logger.info(f"Deleted version file: {version_path}")
            except Exception as e:
                logger.error(f"Error deleting version file: {e}")
                return False
        
        # Delete the dataset file if requested
        if delete_file and os.path.exists(version.file_path):
            try:
                os.remove(version.file_path)
                logger.info(f"Deleted dataset file: {version.file_path}")
            except Exception as e:
                logger.error(f"Error deleting dataset file: {e}")
                # Continue with deletion of version info
        
        # Remove from cache
        if version_id in self._version_cache:
            del self._version_cache[version_id]
        
        return True
    
    def update_metadata(
        self,
        version_id: str,
        metadata: Dict[str, Any],
        overwrite: bool = False
    ) -> bool:
        """Update metadata for a dataset version.
        
        Args:
            version_id: ID of the version
            metadata: New metadata to add
            overwrite: Whether to overwrite existing metadata
            
        Returns:
            True if successful, False otherwise
        """
        version = self.get_version(version_id)
        if not version:
            logger.warning(f"Version not found: {version_id}")
            return False
        
        if overwrite:
            version.metadata = metadata.copy()
        else:
            # Update existing metadata
            version.metadata.update(metadata)
        
        # Save updated version
        self._save_version(version)
        logger.info(f"Updated metadata for version {version_id}")
        
        return True


def get_versioning_system() -> DataVersioningSystem:
    """Get a singleton instance of the data versioning system.
    
    Returns:
        DataVersioningSystem instance
    """
    if not hasattr(get_versioning_system, "_instance"):
        get_versioning_system._instance = DataVersioningSystem()
    
    return get_versioning_system._instance


@dataclass
class VersionedDataset:
    """Class for working with versioned datasets."""
    
    dataset_name: str
    file_path: str
    version_id: Optional[str] = None
    parent_versions: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    _versioning_system: Optional[DataVersioningSystem] = None
    
    def __post_init__(self):
        """Initialize after creation."""
        if self._versioning_system is None:
            self._versioning_system = get_versioning_system()
    
    def register(self) -> str:
        """Register this dataset with the versioning system.
        
        Returns:
            Version ID
        """
        version = self._versioning_system.register_dataset(
            dataset_name=self.dataset_name,
            file_path=self.file_path,
            parent_versions=self.parent_versions,
            metadata=self.metadata
        )
        
        self.version_id = version.version_id
        return self.version_id
    
    def get_lineage(self) -> List[DatasetVersion]:
        """Get the lineage of this dataset.
        
        Returns:
            List of ancestor versions
        """
        if not self.version_id:
            logger.warning("Dataset not registered yet")
            return []
        
        return self._versioning_system.get_lineage(self.version_id)
    
    def create_derived_dataset(
        self,
        new_file_path: str,
        derived_name: Optional[str] = None,
        additional_metadata: Optional[Dict[str, Any]] = None
    ) -> 'VersionedDataset':
        """Create a derived dataset from this one.
        
        Args:
            new_file_path: Path to the derived dataset file
            derived_name: Name for the derived dataset
            additional_metadata: Additional metadata
            
        Returns:
            New VersionedDataset object
        """
        if not self.version_id:
            logger.warning("Source dataset not registered yet")
            self.register()
        
        # Use original name with suffix if derived name not provided
        if not derived_name:
            derived_name = f"{self.dataset_name}_derived"
        
        # Combine metadata
        combined_metadata = self.metadata.copy()
        if additional_metadata:
            combined_metadata.update(additional_metadata)
        
        # Add derivation info
        combined_metadata["derived_from"] = self.version_id
        combined_metadata["derivation_time"] = datetime.datetime.now().isoformat()
        
        return VersionedDataset(
            dataset_name=derived_name,
            file_path=new_file_path,
            parent_versions=[self.version_id],
            metadata=combined_metadata,
            _versioning_system=self._versioning_system
        )


# Example usage
if __name__ == "__main__":
    # Create versioning system
    versioning = DataVersioningSystem()
    
    # Register a dataset
    version = versioning.register_dataset(
        dataset_name="example_dataset",
        file_path="data/raw/example.csv",
        metadata={"source": "example", "rows": 1000}
    )
    
    print(f"Registered version: {version.version_id}")
    
    # Get latest version
    latest = versioning.get_latest_version("example_dataset")
    if latest:
        print(f"Latest version: {latest.version_id}, timestamp: {latest.timestamp}")
    
    # Create a derived dataset
    derived = VersionedDataset(
        dataset_name="derived_dataset",
        file_path="data/processed/derived.csv",
        parent_versions=[version.version_id],
        metadata={"transformation": "example", "rows": 500}
    )
    
    derived_id = derived.register()
    print(f"Registered derived dataset: {derived_id}")
    
    # Get lineage
    lineage = versioning.get_lineage(derived_id)
    print(f"Lineage: {[v.version_id for v in lineage]}") 