#!/usr/bin/env python3
"""
Example script demonstrating how to use the data collection framework.

This script shows how to instantiate and use a collector to fetch data
from an external source.
"""

import os
import sys
import json
import argparse
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_collection.example_collector import get_example_collector
from src.utils.logging import get_module_logger

logger = get_module_logger(__name__)


def main():
    """Run the example collector."""
    parser = argparse.ArgumentParser(description="Run the example collector")
    parser.add_argument(
        "--endpoint",
        default="posts",
        help="API endpoint to collect data from (posts, users, comments, etc.)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=10,
        help="Maximum number of items to collect"
    )
    parser.add_argument(
        "--api-url",
        default="https://jsonplaceholder.typicode.com",
        help="URL of the API to collect data from"
    )
    parser.add_argument(
        "--api-key",
        help="API key for authentication (if required)"
    )
    parser.add_argument(
        "--output-dir",
        help="Directory to store collected data"
    )
    
    args = parser.parse_args()
    
    logger.info(f"Starting example collector with endpoint: {args.endpoint}")
    
    # Create the collector
    collector = get_example_collector(
        api_url=args.api_url,
        api_key=args.api_key,
        data_dir=args.output_dir
    )
    
    # Run the collector
    success, result = collector.run(
        endpoint=args.endpoint,
        _limit=args.limit
    )
    
    if success:
        logger.info(f"Collection successful!")
        logger.info(f"Collected {result.get('record_count', 0)} records")
        logger.info(f"Data saved to {result.get('file_path')}")
        
        # Print sample of the collected data
        if 'data' in result and isinstance(result['data'], list) and result['data']:
            sample = result['data'][0] if len(result['data']) > 0 else {}
            logger.info(f"Sample data: {json.dumps(sample, indent=2)}")
    else:
        logger.error(f"Collection failed: {result.get('error', 'Unknown error')}")
    
    # Get collector status
    status = collector.get_status()
    logger.info(f"Collector status: {json.dumps(status, indent=2)}")


if __name__ == "__main__":
    main() 