# Collector Architecture

This document describes the modular collector architecture for the CityPulse data collection framework.

## Overview

The collector architecture provides a standardized way to collect data from various sources, with built-in support for:

- Metadata tracking
- Data validation
- Error handling
- Logging and monitoring
- Source attribution
- Data storage

The architecture is designed to be modular and extensible, allowing for easy addition of new data sources.

## Core Components

### BaseCollector

The `BaseCollector` abstract base class defines the common interface and shared functionality for all collectors. It provides:

- A standardized initialization process
- Abstract methods that must be implemented by concrete collectors
- Utility methods for data validation, storage, and metadata management

### Collector Registry

The collector registry provides a centralized way to register and discover collectors. It allows:

- Registration of collectors by name
- Discovery of available collectors
- Creation of collector instances

### Rate Limiting and Retry

The rate limiting and retry mechanisms help prevent overloading data sources and handle transient errors. They provide:

- Configurable rate limits
- Automatic retries with exponential backoff
- Concurrent request management

### Source Attribution

The source attribution system ensures proper attribution of data sources, including:

- Source name and URL
- License information
- Attribution text

### Collection Monitoring

The collection monitoring system tracks the status and performance of collectors, including:

- Collection success/failure
- Collection timing
- Resource usage

## Class Structure

### BaseCollector

```python
class BaseCollector(abc.ABC):
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
        # Initialize collector
        
    @abc.abstractmethod
    def collect(self, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        # Collect data from source
        
    def validate(self, data: Any, rule_ids: Optional[List[str]] = None) -> bool:
        # Validate collected data
        
    def save_data(self, data: Any, filename: str, metadata: Optional[Dict[str, Any]] = None) -> Path:
        # Save data to disk with metadata
        
    def run(self, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        # Run the collector with timing and logging
        
    def get_status(self) -> Dict[str, Any]:
        # Get collector status
```

## Implementation Guide

### Creating a New Collector

To create a new collector, follow these steps:

1. Create a new Python module in the appropriate directory (e.g., `src/data_collection/osm/`)
2. Import the `BaseCollector` class
3. Create a new class that inherits from `BaseCollector`
4. Implement the required `collect` method
5. Override other methods as needed

Example:

```python
from src.data_collection.base_collector import BaseCollector

class MyCollector(BaseCollector):
    def __init__(self, api_key: str, **kwargs):
        super().__init__(
            name="my_collector",
            description="My custom collector",
            source_name="My Data Source",
            source_url="https://example.com/api",
            source_attribution="Example Data Provider",
            source_license="CC-BY-4.0",
            **kwargs
        )
        self.api_key = api_key
        
    def collect(self, **kwargs) -> Tuple[bool, Dict[str, Any]]:
        # Implement data collection logic
        # ...
        return True, {"data": collected_data}
```

### Using the Collector

To use a collector, follow these steps:

1. Import the collector class or factory function
2. Create an instance of the collector
3. Call the `run` method with appropriate parameters
4. Handle the result

Example:

```python
from src.data_collection.my_collector import MyCollector

# Create collector
collector = MyCollector(api_key="my_api_key")

# Run collector
success, result = collector.run(param1="value1", param2="value2")

# Handle result
if success:
    print(f"Collection successful! Collected {len(result['data'])} items")
else:
    print(f"Collection failed: {result['error']}")
```

## Best Practices

### Error Handling

- Always catch and handle exceptions in the `collect` method
- Return meaningful error messages
- Log errors at appropriate levels

### Resource Management

- Be mindful of memory usage when processing large datasets
- Use streaming or chunking for large data transfers
- Close resources (files, connections) properly

### Metadata

- Include comprehensive metadata with collected data
- Document the structure and meaning of the data
- Track data lineage

### Validation

- Validate data as early as possible
- Define appropriate validation rules
- Handle validation failures gracefully

## Example Implementations

### Example Collector

The `ExampleCollector` class demonstrates a simple implementation that fetches data from a JSON API:

```python
from src.data_collection.base_collector import BaseCollector

class ExampleCollector(BaseCollector):
    def __init__(self, api_url: str, api_key: Optional[str] = None, **kwargs):
        super().__init__(
            name="example_collector",
            description="Example collector that fetches data from a JSON API",
            source_name="Example API",
            source_url=api_url,
            source_attribution="Example API Provider",
            source_license="CC-BY-4.0",
            **kwargs
        )
        self.api_url = api_url
        self.api_key = api_key
    
    def collect(self, endpoint: str = "posts", **kwargs) -> Tuple[bool, Dict[str, Any]]:
        url = f"{self.api_url}/{endpoint}"
        headers = {}
        
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        
        try:
            response = requests.get(url, headers=headers, params=kwargs)
            response.raise_for_status()
            
            data = response.json()
            
            # Validate and save data
            # ...
            
            return True, {"data": data}
            
        except Exception as e:
            return False, {"error": str(e)}
```

## Integration with Other Components

### Data Validation Framework

Collectors use the data validation framework to ensure data quality:

```python
from src.utils.validation.data_validator import get_data_validator

validator = get_data_validator()
report = validator.validate(data, rule_ids=["not_null", "schema_valid"])
```

### Metadata Manager

Collectors use the metadata manager to track metadata:

```python
from src.utils.io.metadata_manager import get_metadata_manager

metadata_manager = get_metadata_manager()
metadata = metadata_manager.extract_metadata(data)
```

### Data Versioning

Collectors can integrate with the data versioning system:

```python
from src.utils.io.data_versioning import get_version_manager

version_manager = get_version_manager()
version_id = version_manager.create_version(data, metadata)
```

## Future Enhancements

- Parallel collection from multiple sources
- Scheduled collection with cron-like syntax
- Incremental collection with change detection
- Collector pipelines for multi-step collection processes 