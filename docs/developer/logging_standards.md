# Logging Standards for CityPulse

This document outlines the logging standards for the CityPulse project to ensure consistent, useful logs across all components.

## Logging Levels

CityPulse uses the following logging levels:

| Level | When to Use |
|-------|-------------|
| DEBUG | Detailed information, typically useful only for diagnosing problems |
| INFO | Confirmation that things are working as expected |
| WARNING | Indication that something unexpected happened, or may happen in the near future (e.g., disk space low) |
| ERROR | Due to a more serious problem, the software has not been able to perform some function |
| CRITICAL | A serious error, indicating that the program itself may be unable to continue running |

## Logging Format

All logs should follow this format:

```
%(asctime)s - %(name)s - %(levelname)s - %(message)s
```

Example:
```
2023-07-15 14:32:45,123 - citypulse.data_collection.osm - INFO - Downloaded 1250 POIs for Tunis
```

## Logger Naming Convention

Loggers should be named using the module's full path:

```python
# In src/data_collection/osm/poi_collector.py
logger = logging.getLogger("citypulse.data_collection.osm.poi_collector")
```

## Contextual Information

Include relevant contextual information in log messages:

1. **Resource IDs**: Include IDs of resources being processed
2. **Quantities**: Include counts, sizes, durations
3. **Operation Status**: Success/failure and relevant details

Example:
```python
logger.info(f"Downloaded {len(pois)} POIs for {area_name} in {duration:.2f} seconds")
```

## Log File Management

Logs are stored in the `logs/` directory with the following conventions:

1. **Main Application Log**: `citypulse_YYYYMMDD_HHMMSS.log`
2. **Component Logs**: `component_name_YYYYMMDD_HHMMSS.log`

Log rotation is configured to:
- Create a new log file daily
- Compress logs older than 7 days
- Delete logs older than 30 days

## Performance Considerations

1. **Avoid Expensive Operations**: Use lazy evaluation for expensive operations
   ```python
   # Good
   if logger.isEnabledFor(logging.DEBUG):
       logger.debug(f"Complex calculation result: {expensive_function()}")
   ```

2. **Batch Logging**: For high-volume operations, consider batching logs

3. **Sampling**: For very high-frequency events, consider sampling logs

## Sensitive Information

Never log:
- API keys or credentials
- Personal identifiable information (PII)
- Database connection strings

Use the following pattern to mask sensitive information:
```python
logger.info(f"Connecting to database {mask_connection_string(conn_string)}")
```

## Exception Logging

When logging exceptions, always include the traceback:

```python
try:
    # Some operation
except Exception as e:
    logger.error(f"Failed to process {resource_id}", exc_info=True)
```

## Integration with Monitoring

Critical and error logs should trigger alerts in the monitoring system. Configure your logger to integrate with the monitoring system:

```python
# Example integration with monitoring system
handler = MonitoringHandler()
handler.setLevel(logging.ERROR)
logger.addHandler(handler)
```

## Implementation Example

```python
import logging
import time
from pathlib import Path

from config.settings import LOG_DIR, LOG_LEVEL, LOG_FORMAT

def setup_logger(name, log_file=None):
    """Set up a logger with the project standards."""
    logger = logging.getLogger(name)
    
    # Set level from configuration
    level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Create handlers
    handlers = []
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter(LOG_FORMAT))
    handlers.append(console_handler)
    
    # File handler (if specified)
    if log_file:
        log_path = Path(LOG_DIR) / log_file
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(logging.Formatter(LOG_FORMAT))
        handlers.append(file_handler)
    
    # Add handlers to logger
    for handler in handlers:
        logger.addHandler(handler)
    
    return logger

# Usage example
if __name__ == "__main__":
    # Create logger for a module
    module_logger = setup_logger(
        "citypulse.data_collection.osm",
        f"osm_collection_{time.strftime('%Y%m%d_%H%M%S')}.log"
    )
    
    # Log messages
    module_logger.debug("Starting OSM data collection")
    module_logger.info("Downloaded 1250 POIs for Tunis")
    module_logger.warning("Rate limit approaching, slowing down requests")
    
    try:
        # Simulate an error
        raise ValueError("Invalid parameter")
    except Exception as e:
        module_logger.error("Failed to process data", exc_info=True)
```

## Testing Logging

When testing logging, verify:

1. Log messages are correctly formatted
2. Appropriate levels are used
3. Contextual information is included
4. Sensitive information is masked
5. Log rotation works correctly

Example test:
```python
def test_logger_formatting(caplog):
    logger = setup_logger("test.logger")
    logger.info("Test message with %s", "parameter")
    
    assert "test.logger" in caplog.text
    assert "INFO" in caplog.text
    assert "Test message with parameter" in caplog.text
``` 