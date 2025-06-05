"""
Example collector implementation to demonstrate the BaseCollector usage.
"""

import os
import json
import requests
from typing import Dict, Any, Tuple, Optional, List
from pathlib import Path

from src.data_collection.base_collector import BaseCollector
from src.utils.logging import get_module_logger

logger = get_module_logger(__name__)


class ExampleCollector(BaseCollector):
    """
    Example collector that fetches data from a JSON API.
    
    This collector demonstrates how to implement a concrete collector
    using the BaseCollector abstract class.
    """
    
    def __init__(
        self,
        api_url: str,
        api_key: Optional[str] = None,
        data_dir: Optional[Path] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize the example collector.
        
        Args:
            api_url: URL of the API to collect data from
            api_key: API key for authentication (if required)
            data_dir: Directory to store collected data
            metadata: Additional metadata
        """
        super().__init__(
            name="example_collector",
            description="Example collector that fetches data from a JSON API",
            source_name="Example API",
            source_url=api_url,
            source_attribution="Example API Provider",
            source_license="CC-BY-4.0",
            data_dir=data_dir,
            metadata=metadata
        )
        
        self.api_url = api_url
        self.api_key = api_key
    
    def collect(self, endpoint: str = "posts", **kwargs) -> Tuple[bool, Dict[str, Any]]:
        """
        Collect data from the example API.
        
        Args:
            endpoint: API endpoint to fetch data from
            **kwargs: Additional parameters for the API request
            
        Returns:
            Tuple containing:
                - Boolean indicating success or failure
                - Dictionary with collected data or error information
        """
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        logger.info(f"Fetching data from {url}")
        
        try:
            response = requests.get(url, headers=headers, params=kwargs)
            response.raise_for_status()
            
            data = response.json()
            
            # Validate the collected data
            is_valid = self.validate(data)
            if not is_valid:
                return False, {
                    "error": "Data validation failed",
                    "data": data
                }
            
            # Save the data to disk
            filename = f"{endpoint}.json"
            file_path = self.save_data(
                data,
                filename,
                metadata={
                    "endpoint": endpoint,
                    "params": kwargs,
                    "response_time": response.elapsed.total_seconds(),
                    "response_status": response.status_code
                }
            )
            
            return True, {
                "data": data,
                "file_path": str(file_path),
                "record_count": len(data) if isinstance(data, list) else 1
            }
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Error fetching data from {url}: {str(e)}"
            logger.error(error_msg)
            return False, {"error": error_msg}
        
        except Exception as e:
            error_msg = f"Unexpected error in collection: {str(e)}"
            logger.exception(error_msg)
            return False, {"error": error_msg}


def get_example_collector(
    api_url: str = "https://jsonplaceholder.typicode.com",
    api_key: Optional[str] = None,
    data_dir: Optional[Path] = None
) -> ExampleCollector:
    """
    Factory function to create an instance of ExampleCollector.
    
    Args:
        api_url: URL of the API to collect data from
        api_key: API key for authentication (if required)
        data_dir: Directory to store collected data
        
    Returns:
        Instance of ExampleCollector
    """
    return ExampleCollector(
        api_url=api_url,
        api_key=api_key,
        data_dir=data_dir
    ) 