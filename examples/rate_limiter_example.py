#!/usr/bin/env python3
"""
Example script demonstrating how to use rate limiting and retry mechanisms.

This script shows how to use the rate limiter, retry decorator, and
rate-limited client for API calls.
"""

import sys
import time
import random
import asyncio
import argparse
import requests
from pathlib import Path
from typing import Dict, Any, List, Optional

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_collection.rate_limiter import (
    RateLimiter,
    ExponentialBackoff,
    with_retry,
    ConcurrencyLimiter,
    RateLimitedClient,
    create_rate_limiter,
    create_retry_decorator,
    create_rate_limited_client
)
from src.utils.logging import get_module_logger

logger = get_module_logger(__name__)


def simulate_api_call(success_rate: float = 0.7, max_delay: float = 0.5) -> Dict[str, Any]:
    """
    Simulate an API call with random success/failure and delay.
    
    Args:
        success_rate: Probability of success (0.0 to 1.0)
        max_delay: Maximum delay in seconds
        
    Returns:
        Response data
        
    Raises:
        Exception: If the simulated call fails
    """
    # Simulate network delay
    delay = random.random() * max_delay
    time.sleep(delay)
    
    # Simulate success/failure
    if random.random() > success_rate:
        error_type = random.choice([
            "ConnectionError",
            "Timeout",
            "ServerError"
        ])
        raise Exception(f"Simulated {error_type}")
    
    # Return simulated data
    return {
        "id": random.randint(1, 1000),
        "value": random.random(),
        "timestamp": time.time(),
        "delay": delay
    }


def demonstrate_rate_limiter(rate: float, capacity: int, num_calls: int) -> None:
    """
    Demonstrate the rate limiter.
    
    Args:
        rate: Rate limit in calls per second
        capacity: Burst capacity
        num_calls: Number of calls to make
    """
    logger.info(f"Demonstrating rate limiter (rate={rate} req/s, capacity={capacity})")
    
    # Create rate limiter
    rate_limiter = create_rate_limiter(rate, capacity)
    
    # Make calls with rate limiting
    start_time = time.time()
    
    for i in range(num_calls):
        call_start = time.time()
        rate_limiter.acquire()
        call_end = time.time()
        
        logger.info(f"Call {i+1}/{num_calls} - waited {call_end - call_start:.3f}s")
    
    total_time = time.time() - start_time
    expected_time = num_calls / rate
    
    logger.info(f"Made {num_calls} calls in {total_time:.2f}s")
    logger.info(f"Expected minimum time: {expected_time:.2f}s")
    logger.info(f"Effective rate: {num_calls / total_time:.2f} req/s")


def demonstrate_retry_mechanism(max_retries: int, success_rate: float, num_calls: int) -> None:
    """
    Demonstrate the retry mechanism.
    
    Args:
        max_retries: Maximum number of retries
        success_rate: Probability of success for each call
        num_calls: Number of calls to make
    """
    logger.info(f"Demonstrating retry mechanism (max_retries={max_retries}, success_rate={success_rate})")
    
    # Create retry decorator
    retry_decorator = create_retry_decorator(
        max_retries=max_retries,
        base_delay=0.1,
        max_delay=1.0,
        jitter=True
    )
    
    # Apply retry decorator to our function
    @retry_decorator
    def api_call() -> Dict[str, Any]:
        return simulate_api_call(success_rate)
    
    # Make calls with retry
    successes = 0
    failures = 0
    
    for i in range(num_calls):
        try:
            start_time = time.time()
            result = api_call()
            elapsed = time.time() - start_time
            
            logger.info(f"Call {i+1}/{num_calls} succeeded in {elapsed:.2f}s")
            successes += 1
        except Exception as e:
            logger.error(f"Call {i+1}/{num_calls} failed: {str(e)}")
            failures += 1
    
    logger.info(f"Results: {successes} successes, {failures} failures")


def demonstrate_rate_limited_client(
    rate: float,
    capacity: int,
    max_retries: int,
    max_concurrency: int,
    success_rate: float,
    num_items: int
) -> None:
    """
    Demonstrate the rate-limited client.
    
    Args:
        rate: Rate limit in calls per second
        capacity: Burst capacity
        max_retries: Maximum number of retries
        max_concurrency: Maximum concurrency
        success_rate: Probability of success for each call
        num_items: Number of items to process
    """
    logger.info(
        f"Demonstrating rate-limited client "
        f"(rate={rate} req/s, capacity={capacity}, "
        f"max_retries={max_retries}, max_concurrency={max_concurrency})"
    )
    
    # Create rate-limited client
    client = create_rate_limited_client(
        rate=rate,
        capacity=capacity,
        max_retries=max_retries,
        max_concurrency=max_concurrency
    )
    
    # Create items to process
    items = list(range(num_items))
    
    # Define processing function
    def process_item(item: int) -> Dict[str, Any]:
        result = simulate_api_call(success_rate)
        result["item"] = item
        return result
    
    # Process items in batch
    logger.info(f"Processing {num_items} items in batch")
    start_time = time.time()
    results = client.batch_call(process_item, items)
    total_time = time.time() - start_time
    
    # Count successes and failures
    successes = sum(1 for _, result in results if not isinstance(result, Exception))
    failures = sum(1 for _, result in results if isinstance(result, Exception))
    
    logger.info(f"Batch processing completed in {total_time:.2f}s")
    logger.info(f"Results: {successes} successes, {failures} failures")
    logger.info(f"Effective rate: {num_items / total_time:.2f} items/s")


async def demonstrate_async_client(
    rate: float,
    capacity: int,
    max_retries: int,
    max_concurrency: int,
    success_rate: float,
    num_items: int
) -> None:
    """
    Demonstrate the async capabilities of the rate-limited client.
    
    Args:
        rate: Rate limit in calls per second
        capacity: Burst capacity
        max_retries: Maximum number of retries
        max_concurrency: Maximum concurrency
        success_rate: Probability of success for each call
        num_items: Number of items to process
    """
    logger.info(
        f"Demonstrating async rate-limited client "
        f"(rate={rate} req/s, capacity={capacity}, "
        f"max_retries={max_retries}, max_concurrency={max_concurrency})"
    )
    
    # Create rate-limited client
    client = create_rate_limited_client(
        rate=rate,
        capacity=capacity,
        max_retries=max_retries,
        max_concurrency=max_concurrency
    )
    
    # Create items to process
    items = list(range(num_items))
    
    # Define async processing function
    async def process_item_async(item: int) -> Dict[str, Any]:
        # Use asyncio.to_thread to run CPU-bound or blocking code
        result = await asyncio.to_thread(simulate_api_call, success_rate)
        result["item"] = item
        return result
    
    # Process items in batch asynchronously
    logger.info(f"Processing {num_items} items asynchronously")
    start_time = time.time()
    results = await client.batch_call_async(process_item_async, items)
    total_time = time.time() - start_time
    
    # Count successes and failures
    successes = sum(1 for _, result in results if not isinstance(result, Exception))
    failures = sum(1 for _, result in results if isinstance(result, Exception))
    
    logger.info(f"Async batch processing completed in {total_time:.2f}s")
    logger.info(f"Results: {successes} successes, {failures} failures")
    logger.info(f"Effective rate: {num_items / total_time:.2f} items/s")


def demonstrate_real_api_call(url: str, num_calls: int, rate: float) -> None:
    """
    Demonstrate rate limiting with a real API.
    
    Args:
        url: URL to call
        num_calls: Number of calls to make
        rate: Rate limit in calls per second
    """
    logger.info(f"Demonstrating real API calls to {url} (rate={rate} req/s)")
    
    # Create rate-limited client
    client = create_rate_limited_client(
        rate=rate,
        capacity=1,
        max_retries=3,
        max_concurrency=5,
        retryable_exceptions=[
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.HTTPError
        ]
    )
    
    # Define API call function
    def call_api(params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    
    # Make API calls
    start_time = time.time()
    
    for i in range(num_calls):
        try:
            result = client.call_api(call_api, {"i": i})
            logger.info(f"Call {i+1}/{num_calls} succeeded")
        except Exception as e:
            logger.error(f"Call {i+1}/{num_calls} failed: {str(e)}")
    
    total_time = time.time() - start_time
    
    logger.info(f"Made {num_calls} API calls in {total_time:.2f}s")
    logger.info(f"Effective rate: {num_calls / total_time:.2f} req/s")


async def main_async():
    """Run the async demonstration."""
    parser = argparse.ArgumentParser(description="Demonstrate async rate limiting and retry")
    parser.add_argument(
        "--rate",
        type=float,
        default=5.0,
        help="Rate limit in requests per second"
    )
    parser.add_argument(
        "--capacity",
        type=int,
        default=2,
        help="Burst capacity"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retries"
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=5,
        help="Maximum concurrency"
    )
    parser.add_argument(
        "--success-rate",
        type=float,
        default=0.7,
        help="Probability of success for simulated calls"
    )
    parser.add_argument(
        "--num-items",
        type=int,
        default=20,
        help="Number of items to process"
    )
    
    args = parser.parse_args()
    
    await demonstrate_async_client(
        rate=args.rate,
        capacity=args.capacity,
        max_retries=args.max_retries,
        max_concurrency=args.max_concurrency,
        success_rate=args.success_rate,
        num_items=args.num_items
    )


def main():
    """Run the demonstration."""
    parser = argparse.ArgumentParser(description="Demonstrate rate limiting and retry")
    parser.add_argument(
        "--demo",
        choices=["rate-limiter", "retry", "client", "real-api", "async"],
        default="rate-limiter",
        help="Which demonstration to run"
    )
    parser.add_argument(
        "--rate",
        type=float,
        default=5.0,
        help="Rate limit in requests per second"
    )
    parser.add_argument(
        "--capacity",
        type=int,
        default=2,
        help="Burst capacity"
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="Maximum number of retries"
    )
    parser.add_argument(
        "--max-concurrency",
        type=int,
        default=5,
        help="Maximum concurrency"
    )
    parser.add_argument(
        "--success-rate",
        type=float,
        default=0.7,
        help="Probability of success for simulated calls"
    )
    parser.add_argument(
        "--num-calls",
        type=int,
        default=10,
        help="Number of calls to make"
    )
    parser.add_argument(
        "--url",
        default="https://jsonplaceholder.typicode.com/posts/1",
        help="URL for real API calls"
    )
    
    args = parser.parse_args()
    
    if args.demo == "rate-limiter":
        demonstrate_rate_limiter(
            rate=args.rate,
            capacity=args.capacity,
            num_calls=args.num_calls
        )
    elif args.demo == "retry":
        demonstrate_retry_mechanism(
            max_retries=args.max_retries,
            success_rate=args.success_rate,
            num_calls=args.num_calls
        )
    elif args.demo == "client":
        demonstrate_rate_limited_client(
            rate=args.rate,
            capacity=args.capacity,
            max_retries=args.max_retries,
            max_concurrency=args.max_concurrency,
            success_rate=args.success_rate,
            num_items=args.num_calls
        )
    elif args.demo == "real-api":
        demonstrate_real_api_call(
            url=args.url,
            num_calls=args.num_calls,
            rate=args.rate
        )
    elif args.demo == "async":
        asyncio.run(main_async())


if __name__ == "__main__":
    main() 