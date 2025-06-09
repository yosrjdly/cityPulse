# Rate Limiting and Retry Mechanisms

This document describes the rate limiting and retry mechanisms for the CityPulse data collection framework.

## Overview

The rate limiting and retry module provides utilities for:

- Limiting the rate of API calls to prevent overwhelming external services
- Implementing retry strategies with exponential backoff for handling transient failures
- Managing concurrency to optimize resource usage
- Batch processing with rate limiting and retries

These mechanisms are essential for reliable data collection from external APIs, which often have rate limits and may experience temporary failures.

## Core Components

### RateLimiter Class

The `RateLimiter` class implements a token bucket algorithm for rate limiting:

- **Token Bucket Algorithm**: Allows for bursts of requests up to a maximum capacity while maintaining a long-term average rate
- **Thread Safety**: Uses locks to ensure thread safety
- **Blocking and Non-Blocking Modes**: Can either block until tokens are available or return immediately
- **Decorator Support**: Can be used as a decorator for rate-limited functions

```python
# Create a rate limiter with 5 requests per second and burst capacity of 10
rate_limiter = RateLimiter(rate=5.0, capacity=10)

# Use as a function
rate_limiter.acquire()  # Blocks until a token is available

# Use as a decorator
@rate_limiter
def call_api():
    # This function will be rate-limited
    pass
```

### Retry Strategies

The module provides a flexible retry system with customizable strategies:

- **RetryStrategy Base Class**: Abstract base class for implementing retry strategies
- **ExponentialBackoff Strategy**: Implements exponential backoff with optional jitter
- **with_retry Decorator**: Decorator for retrying functions on failure

```python
# Create a retry decorator with exponential backoff
retry_decorator = create_retry_decorator(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0,
    jitter=True,
    retryable_exceptions=[ConnectionError, TimeoutError]
)

# Apply the decorator to a function
@retry_decorator
def call_api():
    # This function will be retried on failure
    pass
```

### ConcurrencyLimiter Class

The `ConcurrencyLimiter` class limits the number of concurrent operations:

- **Semaphore-Based Limiting**: Uses semaphores to limit concurrency
- **Decorator Support**: Can be used as a decorator for concurrency-limited functions
- **Async Support**: Provides async-compatible methods for limiting concurrency in async code

```python
# Create a concurrency limiter with maximum 5 concurrent operations
concurrency_limiter = ConcurrencyLimiter(max_concurrency=5)

# Use as a decorator
@concurrency_limiter
def call_api():
    # This function will be concurrency-limited
    pass
```

### RateLimitedClient Class

The `RateLimitedClient` class combines rate limiting, retry, and concurrency management:

- **Combined Functionality**: Integrates rate limiting, retry, and concurrency limiting
- **API Call Wrapper**: Provides a simple interface for making API calls with all protections
- **Batch Processing**: Supports processing batches of items with all protections
- **Async Support**: Provides async-compatible methods for async code

```python
# Create a rate-limited client
client = create_rate_limited_client(
    rate=5.0,
    capacity=10,
    max_retries=3,
    max_concurrency=5
)

# Make an API call
result = client.call_api(requests.get, "https://api.example.com/data")

# Process a batch of items
results = client.batch_call(process_item, items)
```

## Usage Patterns

### Basic Rate Limiting

For simple rate limiting of API calls:

```python
from src.data_collection.rate_limiter import create_rate_limiter

# Create a rate limiter with 5 requests per second
rate_limiter = create_rate_limiter(rate=5.0)

# Use the rate limiter
for item in items:
    rate_limiter.acquire()
    process_item(item)
```

### Retry with Exponential Backoff

For retrying operations that may fail transiently:

```python
from src.data_collection.rate_limiter import create_retry_decorator

# Create a retry decorator
retry_decorator = create_retry_decorator(
    max_retries=3,
    base_delay=1.0,
    max_delay=60.0,
    retryable_exceptions=[ConnectionError, TimeoutError]
)

# Apply the decorator
@retry_decorator
def fetch_data(url):
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()
```

### Combined Rate Limiting and Retry

For comprehensive protection when calling external APIs:

```python
from src.data_collection.rate_limiter import create_rate_limited_client

# Create a rate-limited client
client = create_rate_limited_client(
    rate=5.0,
    capacity=10,
    max_retries=3,
    max_concurrency=5,
    retryable_exceptions=[ConnectionError, TimeoutError, HTTPError]
)

# Define the API call function
def call_api(params):
    response = requests.get("https://api.example.com/data", params=params)
    response.raise_for_status()
    return response.json()

# Make API calls with protection
for params in parameter_list:
    try:
        result = client.call_api(call_api, params)
        process_result(result)
    except Exception as e:
        handle_error(e)
```

### Batch Processing

For efficiently processing many items with rate limiting and retry:

```python
from src.data_collection.rate_limiter import create_rate_limited_client

# Create a rate-limited client
client = create_rate_limited_client(
    rate=5.0,
    capacity=10,
    max_retries=3,
    max_concurrency=5
)

# Define the processing function
def process_item(item):
    # Process a single item
    return result

# Process items in batch
results = client.batch_call(process_item, items)

# Process results
for item, result in results:
    if isinstance(result, Exception):
        handle_error(item, result)
    else:
        handle_success(item, result)
```

### Asynchronous Processing

For asynchronous processing with rate limiting and retry:

```python
import asyncio
from src.data_collection.rate_limiter import create_rate_limited_client

# Create a rate-limited client
client = create_rate_limited_client(
    rate=5.0,
    capacity=10,
    max_retries=3,
    max_concurrency=5
)

# Define the async processing function
async def process_item_async(item):
    # Process a single item asynchronously
    return result

# Process items in batch asynchronously
async def process_batch():
    results = await client.batch_call_async(process_item_async, items)
    return results

# Run the async batch processing
results = asyncio.run(process_batch())
```

## Integration with Collectors

The rate limiting and retry mechanisms integrate seamlessly with the collector architecture:

### In BaseCollector Subclasses

```python
from src.data_collection.base_collector import BaseCollector
from src.data_collection.rate_limiter import create_rate_limited_client

class APICollector(BaseCollector):
    def __init__(self, api_url, rate=5.0, **kwargs):
        super().__init__(name="api_collector", **kwargs)
        self.api_url = api_url
        self.client = create_rate_limited_client(
            rate=rate,
            retryable_exceptions=[ConnectionError, TimeoutError, HTTPError]
        )
    
    def collect(self, endpoint, **kwargs):
        # Define the API call function
        def call_api(params):
            url = f"{self.api_url}/{endpoint}"
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        
        # Make the API call with rate limiting and retry
        return self.client.call_api(call_api, kwargs)
```

### With Collector Registry

```python
from src.data_collection.collector_registry import create_collector
from src.data_collection.rate_limiter import create_rate_limited_client

# Create a collector with rate limiting
collector = create_collector("APICollector", api_url="https://api.example.com")

# Create a rate-limited client for batch processing
client = create_rate_limited_client(rate=5.0)

# Process multiple endpoints with rate limiting
endpoints = ["users", "posts", "comments"]
results = client.batch_call(collector.collect, endpoints)
```

## Best Practices

### Rate Limiting

- **Respect API Limits**: Always set rate limits according to the API provider's documentation
- **Add Buffer**: Set rate limits slightly below the maximum allowed to account for timing variations
- **Monitor Usage**: Log rate limit usage to detect when you're approaching limits

### Retry Strategies

- **Identify Retryable Errors**: Only retry errors that are likely to be transient
- **Set Reasonable Limits**: Don't retry too many times or with too long delays
- **Use Jitter**: Add randomness to retry delays to prevent thundering herd problems

### Concurrency

- **Match System Capabilities**: Set concurrency limits based on your system's capabilities
- **Consider API Limits**: Some APIs limit concurrent connections as well as request rates
- **Monitor Performance**: Adjust concurrency limits based on observed performance

### Error Handling

- **Log All Failures**: Log both transient failures and permanent failures
- **Track Success Rates**: Monitor the success rate of API calls to detect issues
- **Implement Circuit Breakers**: Stop making requests if failure rates are too high

## Example Implementation

### Rate-Limited API Client

```python
from src.data_collection.rate_limiter import RateLimitedClient
import requests

class WeatherAPIClient:
    def __init__(self, api_key):
        self.api_key = api_key
        self.base_url = "https://api.weatherservice.com/v1"
        
        # Create rate-limited client with appropriate limits
        self.client = RateLimitedClient(
            rate=10.0,  # 10 requests per second
            capacity=20,  # Allow bursts up to 20 requests
            max_retries=3,
            max_concurrency=5,
            retryable_exceptions=[
                requests.exceptions.ConnectionError,
                requests.exceptions.Timeout,
                requests.exceptions.HTTPError
            ]
        )
    
    def get_current_weather(self, city):
        """Get current weather for a city."""
        def call_api():
            url = f"{self.base_url}/current"
            params = {"city": city, "apikey": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        return self.client.call_api(call_api)
    
    def get_forecast(self, city, days=5):
        """Get weather forecast for a city."""
        def call_api():
            url = f"{self.base_url}/forecast"
            params = {"city": city, "days": days, "apikey": self.api_key}
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            return response.json()
        
        return self.client.call_api(call_api)
    
    def get_weather_for_cities(self, cities):
        """Get current weather for multiple cities."""
        return self.client.batch_call(self.get_current_weather, cities)
```

## Future Enhancements

- **Adaptive Rate Limiting**: Dynamically adjust rate limits based on API responses
- **Circuit Breaker Pattern**: Implement circuit breakers to prevent cascading failures
- **Rate Limit Headers**: Parse and respect rate limit headers from API responses
- **Priority Queuing**: Implement priority queues for rate-limited requests
- **Distributed Rate Limiting**: Support for distributed rate limiting across multiple instances 