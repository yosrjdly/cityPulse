"""
Base collector module for CityPulse data collection framework.

This module provides the foundation for all data collectors in the system,
defining a common interface and shared functionality.
"""

import os
import time
import logging
import abc
from datetime import datetime
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path

from src.utils.logging import get_module_logger
from src.utils.io.metadata_manager import get_metadata_manager
from src.utils.validation.data_validator import get_data_validator

logger = get_module_logger(__name__)


class BaseCollector(abc.ABC):
    """
    Abstract base class for all data collectors in the CityPulse system.
    
    This class defines the common interface and shared functionality for all
    collectors, ensuring consistent behavior across the system.
    
    Attributes:
        name (str): Name of the collector
        description (str): Description of the collector
        source_name (str): Name of the data source
        source_url (str): URL of the data source
        source_attribution (str): Attribution text for the data source
        source_license (str): License information for the data source
        data_dir (Path): Directory where collected data will be stored
        metadata (Dict[str, Any]): Metadata for the collector
        last_collection_time (Optional[datetime]): Time of the last collection
        last_collection_status (Optional[str]): Status of the last collection
    """
    
    def __init__(
        self,
        name: str,
        description: str,
        source_name: str,
        source_url: str,
        source_attribution: str,
        source_license: str,
        data_dir: Optional[Union[str, Path]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a new collector.
        
        Args:
            name: Name of the collector
            description: Description of the collector
            source_name: Name of the data source
            source_url: URL of the data source
            source_attribution: Attribution text for the data source
            source_license: License information for the data source
            data_dir: Directory where collected data will be stored
            metadata: Additional metadata for the collector
        """
        self.name = name
        self.description = description
        self.source_name = source_name
        self.source_url = source_url
        self.source_attribution = source_attribution
        self.source_license = source_license
        
        # Set up data directory
        if data_dir is None:
            self.data_dir = Path(os.environ.get(
                "CITYPULSE_DATA_DIR", 
                str(Path(__file__).parent.parent.parent / "data")
            )) / "collected" / self.name
        else:
            self.data_dir = Path(data_dir)
        
        # Create data directory if it doesn't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize metadata
        self.metadata = metadata or {}
        self.metadata.update({
            "collector_name": self.name,
            "collector_description": self.description,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "source_attribution": self.source_attribution,
            "source_license": self.source_license
        })
        
        # Initialize collection tracking
        self.last_collection_time = None
        self.last_collection_status = None
        
        # Get metadata manager and data validator
        self.metadata_manager = get_metadata_manager()
        self.data_validator = get_data_validator()
        
        logger.info(f"Initialized collector: {self.name}")
    
    @abc.abstractmethod
    def collect(self, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """
        Collect data from the source.
        
        This method must be implemented by all concrete collector classes.
        
        Args:
            **kwargs: Additional parameters for the collection process
            
        Returns:
            Tuple containing:
                - Boolean indicating success or failure
                - Dictionary with collected data or error information
        """
        pass
    
    def validate(self, data: Any, rule_ids: Optional[List[str]] = None) -> bool:
        """
        Validate collected data using the data validation framework.
        
        Args:
            data: Data to validate
            rule_ids: List of validation rule IDs to apply
            
        Returns:
            Boolean indicating whether the data is valid
        """
        logger.info(f"Validating data for collector: {self.name}")
        report = self.data_validator.validate(
            data, 
            rule_ids=rule_ids, 
            dataset_name=f"{self.name}_collection"
        )
        
        if not report.is_valid:
            logger.error(
                f"Validation failed for collector {self.name} with "
                f"{report.error_count} errors, {report.warning_count} warnings"
            )
            
            # Log the first few errors
            for i, result in enumerate(report.results):
                if not result.is_valid and result.level.value == 'error':
                    logger.error(f"Error {i+1}: {result.message}")
                    if i >= 2:  # Only log the first 3 errors
                        break
        
        return report.is_valid
    
    def save_data(self, data: Any, filename: str, metadata: Optional[Dict[str, Any]] = None) -> Path:
        """
        Save collected data to disk with metadata.
        
        Args:
            data: Data to save
            filename: Name of the file to save
            metadata: Additional metadata to save with the data
            
        Returns:
            Path to the saved file
        """
        # Create timestamp-based directory
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_dir = self.data_dir / timestamp
        save_dir.mkdir(parents=True, exist_ok=True)
        
        # Save data
        file_path = save_dir / filename
        
        # Determine file type and save accordingly
        if hasattr(data, 'to_csv') and callable(data.to_csv):
            # Handle pandas DataFrame or similar
            data.to_csv(file_path, index=False)
        elif hasattr(data, 'to_file') and callable(data.to_file):
            # Handle GeoPandas GeoDataFrame or similar
            data.to_file(file_path)
        elif isinstance(data, (dict, list)):
            # Handle JSON-serializable data
            import json
            with open(file_path, 'w') as f:
                json.dump(data, f, indent=2)
        else:
            # Handle other types as string
            with open(file_path, 'w') as f:
                f.write(str(data))
        
        # Save metadata
        combined_metadata = {
            "collection_time": timestamp,
            "collector_name": self.name,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "source_attribution": self.source_attribution,
            "source_license": self.source_license,
            "file_path": str(file_path),
            "file_size": os.path.getsize(file_path)
        }
        
        if metadata:
            combined_metadata.update(metadata)
        
        # Extract additional metadata from data
        extracted_metadata = self.metadata_manager.extract_metadata(data)
        combined_metadata.update(extracted_metadata)
        
        # Save metadata to file
        metadata_path = save_dir / f"{filename}.metadata.json"
        import json
        with open(metadata_path, 'w') as f:
            json.dump(combined_metadata, f, indent=2)
        
        logger.info(f"Saved data to {file_path} with metadata at {metadata_path}")
        return file_path
    
    def run(self, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """
        Run the collector with timing and logging.
        
        Args:
            **kwargs: Additional parameters for the collection process
            
        Returns:
            Tuple containing:
                - Boolean indicating success or failure
                - Dictionary with results or error information
        """
        logger.info(f"Running collector: {self.name}")
        start_time = time.time()
        self.last_collection_time = datetime.now()
        
        try:
            success, result = self.collect(**kwargs)
            self.last_collection_status = "success" if success else "failure"
            
            end_time = time.time()
            duration = end_time - start_time
            
            logger.info(
                f"Collector {self.name} completed in {duration:.2f} seconds "
                f"with status: {self.last_collection_status}"
            )
            
            # Add timing information to result
            if isinstance(result, dict):
                result["collection_time"] = self.last_collection_time.isoformat()
                result["collection_duration"] = duration
                result["collection_status"] = self.last_collection_status
            
            return success, result
            
        except Exception as e:
            self.last_collection_status = "error"
            error_msg = f"Error in collector {self.name}: {str(e)}"
            logger.exception(error_msg)
            
            end_time = time.time()
            duration = end_time - start_time
            
            return False, {
                "error": error_msg,
                "collection_time": self.last_collection_time.isoformat(),
                "collection_duration": duration,
                "collection_status": self.last_collection_status
            }
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get the current status of the collector.
        
        Returns:
            Dictionary with status information
        """
        return {
            "name": self.name,
            "description": self.description,
            "source_name": self.source_name,
            "source_url": self.source_url,
            "last_collection_time": self.last_collection_time.isoformat() 
                if self.last_collection_time else None,
            "last_collection_status": self.last_collection_status
        } 