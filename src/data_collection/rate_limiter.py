"""
Rate limiting and retry mechanisms for CityPulse data collection.

This module provides utilities for rate limiting API calls and implementing
retry mechanisms with exponential backoff.
"""

import time
import random
import functools
import threading
from typing import Dict, Any, Callable, Optional, TypeVar, List, Tuple, Union
from datetime import datetime, timedelta
import asyncio
import concurrent.futures

from src.utils.logging import get_module_logger

logger = get_module_logger(__name__)

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')


class RateLimiter:
    """
    Rate limiter for API calls.
    
    This class implements a token bucket algorithm for rate limiting.
    It allows for bursts of requests up to a maximum capacity,
    while maintaining a long-term average rate.
    
    Attributes:
        rate (float): Rate at which tokens are added to the bucket (tokens per second)
        capacity (int): Maximum number of tokens the bucket can hold
        tokens (float): Current number of tokens in the bucket
        last_refill (datetime): Time of the last token refill
        lock (threading.RLock): Lock for thread safety
    """
    
    def __init__(self, rate: float, capacity: int = 1):
        """
        Initialize a rate limiter.
        
        Args:
            rate: Rate at which tokens are added to the bucket (tokens per second)
            capacity: Maximum number of tokens the bucket can hold
        """
        self.rate = rate
        self.capacity = capacity
        self.tokens = capacity
        self.last_refill = datetime.now()
        self.lock = threading.RLock()
        
        logger.info(f"Initialized rate limiter with rate={rate} req/s, capacity={capacity}")
    
    def _refill(self) -> None:
        """Refill the token bucket based on elapsed time."""
        now = datetime.now()
        elapsed = (now - self.last_refill).total_seconds()
        
        # Calculate new tokens to add
        new_tokens = elapsed * self.rate
        
        # Update tokens and last refill time
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now
    
    def acquire(self, tokens: int = 1, block: bool = True) -> bool:
        """
        Acquire tokens from the bucket.
        
        Args:
            tokens: Number of tokens to acquire
            block: Whether to block until tokens are available
            
        Returns:
            True if tokens were acquired, False otherwise
        """
        if tokens > self.capacity:
            logger.warning(
                f"Requested tokens ({tokens}) exceed capacity ({self.capacity}). "
                f"This call will never succeed."
            )
            return False
        
        with self.lock:
            self._refill()
            
            # If we have enough tokens, consume them and return
            if self.tokens >= tokens:
                self.tokens -= tokens
                return True
            
            # If not blocking, return False
            if not block:
                return False
            
            # Calculate how long to wait for enough tokens
            deficit = tokens - self.tokens
            wait_time = deficit / self.rate
            
            logger.debug(f"Rate limit reached. Waiting {wait_time:.2f}s for more tokens")
            
            # Sleep and try again
            time.sleep(wait_time)
            return self.acquire(tokens, block)
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator for rate-limited functions.
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            self.acquire()
            return func(*args, **kwargs)
        
        return wrapper


class RetryStrategy:
    """
    Base class for retry strategies.
    
    A retry strategy determines if and when to retry a failed operation.
    """
    
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """
        Determine if the operation should be retried.
        
        Args:
            attempt: Current attempt number (0-based)
            exception: Exception that caused the failure
            
        Returns:
            True if the operation should be retried, False otherwise
        """
        raise NotImplementedError("Subclasses must implement should_retry")
    
    def get_delay(self, attempt: int) -> float:
        """
        Get the delay before the next retry.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        raise NotImplementedError("Subclasses must implement get_delay")


class ExponentialBackoff(RetryStrategy):
    """
    Exponential backoff retry strategy.
    
    This strategy retries with exponentially increasing delays,
    optionally with jitter to avoid thundering herd problems.
    
    Attributes:
        max_retries (int): Maximum number of retries
        base_delay (float): Base delay in seconds
        max_delay (float): Maximum delay in seconds
        jitter (bool): Whether to add jitter to the delay
        retryable_exceptions (List[type]): List of exception types that should trigger a retry
    """
    
    def __init__(
        self,
        max_retries: int = 3,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        retryable_exceptions: Optional[List[type]] = None
    ):
        """
        Initialize an exponential backoff strategy.
        
        Args:
            max_retries: Maximum number of retries
            base_delay: Base delay in seconds
            max_delay: Maximum delay in seconds
            jitter: Whether to add jitter to the delay
            retryable_exceptions: List of exception types that should trigger a retry
                                  (defaults to all exceptions)
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.retryable_exceptions = retryable_exceptions or [Exception]
    
    def should_retry(self, attempt: int, exception: Exception) -> bool:
        """
        Determine if the operation should be retried.
        
        Args:
            attempt: Current attempt number (0-based)
            exception: Exception that caused the failure
            
        Returns:
            True if the operation should be retried, False otherwise
        """
        # Check if we've exceeded the maximum number of retries
        if attempt >= self.max_retries:
            return False
        
        # Check if the exception is retryable
        return any(isinstance(exception, exc_type) for exc_type in self.retryable_exceptions)
    
    def get_delay(self, attempt: int) -> float:
        """
        Get the delay before the next retry.
        
        Args:
            attempt: Current attempt number (0-based)
            
        Returns:
            Delay in seconds
        """
        # Calculate exponential delay: base_delay * 2^attempt
        delay = self.base_delay * (2 ** attempt)
        
        # Apply maximum delay
        delay = min(delay, self.max_delay)
        
        # Add jitter if enabled
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay


def with_retry(
    retry_strategy: Optional[RetryStrategy] = None,
    on_retry: Optional[Callable[[int, Exception], None]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Decorator for functions that should be retried on failure.
    
    Args:
        retry_strategy: Strategy for determining if and when to retry
        on_retry: Callback function to call when a retry occurs
        
    Returns:
        Decorated function
    """
    # Use default retry strategy if none is provided
    if retry_strategy is None:
        retry_strategy = ExponentialBackoff()
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            attempt = 0
            
            while True:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    attempt += 1
                    
                    if not retry_strategy.should_retry(attempt - 1, e):
                        logger.warning(
                            f"Failed after {attempt} attempts. Last error: {str(e)}"
                        )
                        raise
                    
                    delay = retry_strategy.get_delay(attempt - 1)
                    
                    logger.info(
                        f"Attempt {attempt} failed with error: {str(e)}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    
                    if on_retry:
                        on_retry(attempt, e)
                    
                    time.sleep(delay)
        
        return wrapper
    
    return decorator


class ConcurrencyLimiter:
    """
    Limiter for concurrent operations.
    
    This class limits the number of concurrent operations
    that can be performed at once.
    
    Attributes:
        max_concurrency (int): Maximum number of concurrent operations
        semaphore (threading.Semaphore): Semaphore for limiting concurrency
        async_semaphore (asyncio.Semaphore): Semaphore for limiting async concurrency
    """
    
    def __init__(self, max_concurrency: int = 5):
        """
        Initialize a concurrency limiter.
        
        Args:
            max_concurrency: Maximum number of concurrent operations
        """
        self.max_concurrency = max_concurrency
        self.semaphore = threading.Semaphore(max_concurrency)
        self.async_semaphore = None  # Created on demand
        
        logger.info(f"Initialized concurrency limiter with max_concurrency={max_concurrency}")
    
    def __call__(self, func: Callable[..., T]) -> Callable[..., T]:
        """
        Decorator for concurrency-limited functions.
        
        Args:
            func: Function to decorate
            
        Returns:
            Decorated function
        """
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            with self.semaphore:
                return func(*args, **kwargs)
        
        return wrapper
    
    def get_async_semaphore(self) -> asyncio.Semaphore:
        """
        Get the async semaphore for this limiter.
        
        Returns:
            Async semaphore
        """
        if self.async_semaphore is None:
            self.async_semaphore = asyncio.Semaphore(self.max_concurrency)
        return self.async_semaphore
    
    async def async_limited(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Run a function with async concurrency limiting.
        
        Args:
            func: Function to run
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function
        """
        semaphore = self.get_async_semaphore()
        async with semaphore:
            if asyncio.iscoroutinefunction(func):
                return await func(*args, **kwargs)
            else:
                return await asyncio.to_thread(func, *args, **kwargs)


class RateLimitedClient:
    """
    Base class for rate-limited API clients.
    
    This class provides rate limiting and retry capabilities
    for API clients.
    
    Attributes:
        rate_limiter (RateLimiter): Rate limiter for API calls
        retry_strategy (RetryStrategy): Strategy for retrying failed calls
        concurrency_limiter (ConcurrencyLimiter): Limiter for concurrent operations
    """
    
    def __init__(
        self,
        rate: float = 1.0,
        capacity: int = 1,
        max_retries: int = 3,
        max_concurrency: int = 5,
        retryable_exceptions: Optional[List[type]] = None
    ):
        """
        Initialize a rate-limited client.
        
        Args:
            rate: Rate at which API calls can be made (calls per second)
            capacity: Maximum burst capacity for API calls
            max_retries: Maximum number of retries for failed calls
            max_concurrency: Maximum number of concurrent operations
            retryable_exceptions: List of exception types that should trigger a retry
        """
        self.rate_limiter = RateLimiter(rate, capacity)
        self.retry_strategy = ExponentialBackoff(
            max_retries=max_retries,
            retryable_exceptions=retryable_exceptions
        )
        self.concurrency_limiter = ConcurrencyLimiter(max_concurrency)
        
        logger.info(
            f"Initialized rate-limited client with rate={rate} req/s, "
            f"capacity={capacity}, max_retries={max_retries}, "
            f"max_concurrency={max_concurrency}"
        )
    
    def call_api(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """
        Call an API function with rate limiting and retry.
        
        Args:
            func: Function to call
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function
        """
        # Define the retry callback
        def on_retry(attempt: int, exception: Exception) -> None:
            logger.info(
                f"API call failed (attempt {attempt}): {str(exception)}"
            )
        
        # Apply rate limiting, retry, and concurrency limiting
        @self.concurrency_limiter
        @with_retry(self.retry_strategy, on_retry)
        @self.rate_limiter
        def wrapped_func(*inner_args: Any, **inner_kwargs: Any) -> T:
            return func(*inner_args, **inner_kwargs)
        
        return wrapped_func(*args, **kwargs)
    
    async def call_api_async(
        self, 
        func: Callable[..., T], 
        *args: Any, 
        **kwargs: Any
    ) -> T:
        """
        Call an API function asynchronously with rate limiting and retry.
        
        Args:
            func: Function to call
            *args: Arguments to pass to the function
            **kwargs: Keyword arguments to pass to the function
            
        Returns:
            Result of the function
        """
        # Define the async retry function
        async def async_retry(
            func: Callable[..., T], 
            *args: Any, 
            **kwargs: Any
        ) -> T:
            attempt = 0
            
            while True:
                try:
                    # Acquire rate limit token
                    await asyncio.to_thread(self.rate_limiter.acquire)
                    
                    # Call the function
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return await asyncio.to_thread(func, *args, **kwargs)
                        
                except Exception as e:
                    attempt += 1
                    
                    if not self.retry_strategy.should_retry(attempt - 1, e):
                        logger.warning(
                            f"Failed after {attempt} attempts. Last error: {str(e)}"
                        )
                        raise
                    
                    delay = self.retry_strategy.get_delay(attempt - 1)
                    
                    logger.info(
                        f"Async attempt {attempt} failed with error: {str(e)}. "
                        f"Retrying in {delay:.2f}s"
                    )
                    
                    await asyncio.sleep(delay)
        
        # Apply concurrency limiting
        return await self.concurrency_limiter.async_limited(async_retry, func, *args, **kwargs)
    
    def batch_call(
        self, 
        func: Callable[[Any], T], 
        items: List[Any], 
        max_workers: Optional[int] = None
    ) -> List[Tuple[Any, Union[T, Exception]]]:
        """
        Call an API function for a batch of items with rate limiting and retry.
        
        Args:
            func: Function to call for each item
            items: List of items to process
            max_workers: Maximum number of worker threads
            
        Returns:
            List of tuples containing the input item and either the result or an exception
        """
        if max_workers is None:
            max_workers = min(self.concurrency_limiter.max_concurrency, 10)
        
        results = []
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all tasks
            future_to_item = {
                executor.submit(self.call_api, func, item): item for item in items
            }
            
            # Process results as they complete
            for future in concurrent.futures.as_completed(future_to_item):
                item = future_to_item[future]
                try:
                    result = future.result()
                    results.append((item, result))
                except Exception as e:
                    results.append((item, e))
                    logger.error(f"Batch item failed: {str(e)}")
        
        return results
    
    async def batch_call_async(
        self, 
        func: Callable[[Any], T], 
        items: List[Any],
        max_concurrency: Optional[int] = None
    ) -> List[Tuple[Any, Union[T, Exception]]]:
        """
        Call an API function asynchronously for a batch of items.
        
        Args:
            func: Function to call for each item
            items: List of items to process
            max_concurrency: Maximum number of concurrent tasks
            
        Returns:
            List of tuples containing the input item and either the result or an exception
        """
        if max_concurrency is None:
            max_concurrency = self.concurrency_limiter.max_concurrency
        
        results = []
        semaphore = asyncio.Semaphore(max_concurrency)
        
        async def process_item(item: Any) -> Tuple[Any, Union[T, Exception]]:
            async with semaphore:
                try:
                    result = await self.call_api_async(func, item)
                    return item, result
                except Exception as e:
                    logger.error(f"Async batch item failed: {str(e)}")
                    return item, e
        
        # Create tasks for all items
        tasks = [process_item(item) for item in items]
        
        # Wait for all tasks to complete
        for completed_task in asyncio.as_completed(tasks):
            result = await completed_task
            results.append(result)
        
        return results


# Convenience functions for creating rate limiters and retry decorators

def create_rate_limiter(rate: float, capacity: int = 1) -> RateLimiter:
    """
    Create a rate limiter.
    
    Args:
        rate: Rate at which tokens are added to the bucket (tokens per second)
        capacity: Maximum number of tokens the bucket can hold
        
    Returns:
        Rate limiter instance
    """
    return RateLimiter(rate, capacity)


def create_retry_decorator(
    max_retries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    jitter: bool = True,
    retryable_exceptions: Optional[List[type]] = None
) -> Callable[[Callable[..., T]], Callable[..., T]]:
    """
    Create a retry decorator.
    
    Args:
        max_retries: Maximum number of retries
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        jitter: Whether to add jitter to the delay
        retryable_exceptions: List of exception types that should trigger a retry
        
    Returns:
        Retry decorator
    """
    strategy = ExponentialBackoff(
        max_retries=max_retries,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter,
        retryable_exceptions=retryable_exceptions
    )
    
    return with_retry(strategy)


def create_rate_limited_client(
    rate: float = 1.0,
    capacity: int = 1,
    max_retries: int = 3,
    max_concurrency: int = 5,
    retryable_exceptions: Optional[List[type]] = None
) -> RateLimitedClient:
    """
    Create a rate-limited client.
    
    Args:
        rate: Rate at which API calls can be made (calls per second)
        capacity: Maximum burst capacity for API calls
        max_retries: Maximum number of retries for failed calls
        max_concurrency: Maximum number of concurrent operations
        retryable_exceptions: List of exception types that should trigger a retry
        
    Returns:
        Rate-limited client instance
    """
    return RateLimitedClient(
        rate=rate,
        capacity=capacity,
        max_retries=max_retries,
        max_concurrency=max_concurrency,
        retryable_exceptions=retryable_exceptions
    ) 