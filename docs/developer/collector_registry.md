# Collector Registry

This document describes the collector registry system for the CityPulse data collection framework.

## Overview

The collector registry provides a centralized way to register, discover, and instantiate data collectors in the CityPulse system. It allows for:

- Registration of collector classes and factory functions
- Dynamic discovery of collectors from packages
- Creation of collector instances by name
- Metadata management for collectors

## Core Components

### CollectorRegistry Class

The `CollectorRegistry` class is the main component of the registry system. It provides methods for:

- Registering collector classes and factory functions
- Retrieving collector classes and factory functions
- Creating collector instances
- Listing registered collectors
- Discovering collectors from packages

### Registry Functions

The module provides several convenience functions that operate on a global registry instance:

- `get_collector_registry()`: Get the singleton registry instance
- `register_collector()`: Register a collector class
- `register_factory()`: Register a factory function
- `create_collector()`: Create a collector instance by name
- `list_collectors()`: List all registered collectors
- `discover_collectors()`: Discover collectors from a package

## Usage

### Registering Collectors Manually

You can register collector classes and factory functions manually:

```python
from src.data_collection.collector_registry import register_collector, register_factory
from src.data_collection.example_collector import ExampleCollector, get_example_collector

# Register a collector class
register_collector(
    ExampleCollector,
    name="example",
    metadata={
        "category": "example",
        "description": "Example collector for demonstration purposes",
        "version": "1.0.0"
    }
)

# Register a factory function
register_factory(
    get_example_collector,
    name="example_factory",
    metadata={
        "category": "example",
        "description": "Factory function for creating example collectors",
        "version": "1.0.0"
    }
)
```

### Discovering Collectors Automatically

You can discover collectors from a package:

```python
from src.data_collection.collector_registry import discover_collectors

# Discover collectors from the data_collection package
count = discover_collectors("src.data_collection")
print(f"Discovered {count} collectors")
```

The discovery process will:

1. Search the package for classes that inherit from `BaseCollector`
2. Search the package for factory functions that return `BaseCollector` instances
3. Register all found collectors and factories

### Creating Collector Instances

You can create collector instances by name:

```python
from src.data_collection.collector_registry import create_collector

# Create a collector instance
collector = create_collector(
    "example",
    api_url="https://jsonplaceholder.typicode.com"
)

# Run the collector
success, result = collector.run(endpoint="posts", _limit=10)
```

The `create_collector()` function will:

1. Try to use a registered factory function with the given name
2. If no factory is found, try to instantiate a registered collector class with the given name
3. Raise a `KeyError` if no collector or factory is found with the given name

### Listing Registered Collectors

You can list all registered collectors:

```python
from src.data_collection.collector_registry import list_collectors

# List all registered collectors
collectors = list_collectors()

for collector_info in collectors:
    print(f"Collector: {collector_info['name']}")
    print(f"  Type: {collector_info['type']}")
    print(f"  Module: {collector_info['module']}")
    if 'description' in collector_info:
        print(f"  Description: {collector_info['description']}")
```

## Collector Discovery Rules

The collector discovery process follows these rules:

1. **Collector Classes**: A class is registered as a collector if:
   - It inherits from `BaseCollector`
   - It is not the `BaseCollector` class itself

2. **Factory Functions**: A function is registered as a factory if:
   - Its name starts with `get_` and ends with `_collector`
   - Its return annotation is a subclass of `BaseCollector`

## Metadata Management

The registry maintains metadata for each registered collector or factory. This metadata can include:

- Description (automatically extracted from docstrings)
- Category
- Version
- Custom metadata specified during registration

## Best Practices

### Naming Conventions

- Collector classes should have descriptive names that end with `Collector`
- Factory functions should be named `get_X_collector` where `X` is the collector name
- Collector names in the registry should be lowercase and use underscores for spaces

### Registration

- Register collectors as early as possible, preferably during application startup
- Use factory functions for collectors that require complex initialization
- Include comprehensive metadata during registration

### Discovery

- Use discovery for large applications with many collectors
- Structure your packages to facilitate discovery
- Ensure all collectors have proper type annotations

## Example Implementation

### Example Collector Class

```python
from src.data_collection.base_collector import BaseCollector

class ExampleCollector(BaseCollector):
    def __init__(self, api_url, api_key=None, **kwargs):
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
    
    def collect(self, endpoint="posts", **kwargs):
        # Implementation...
```

### Example Factory Function

```python
def get_example_collector(
    api_url="https://jsonplaceholder.typicode.com",
    api_key=None,
    data_dir=None
) -> ExampleCollector:
    """
    Factory function to create an instance of ExampleCollector.
    """
    return ExampleCollector(
        api_url=api_url,
        api_key=api_key,
        data_dir=data_dir
    )
```

### Example Usage

```python
from src.data_collection.collector_registry import discover_collectors, create_collector

# Discover collectors
discover_collectors()

# Create and run a collector
collector = create_collector(
    "example",
    api_url="https://jsonplaceholder.typicode.com"
)
success, result = collector.run(endpoint="posts", _limit=5)
```

## Integration with Other Components

### Base Collector

The registry works closely with the `BaseCollector` class, which defines the common interface for all collectors.

### Data Validation Framework

Collectors created through the registry can use the data validation framework to validate collected data.

### Metadata Manager

Collectors created through the registry can use the metadata manager to track metadata for collected data.

## Future Enhancements

- Support for collector categories and tags
- Dependency management between collectors
- Configuration management for collectors
- Collector lifecycle management (initialization, shutdown)
- Web-based collector registry browser 