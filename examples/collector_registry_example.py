#!/usr/bin/env python3
"""
Example script demonstrating how to use the collector registry.

This script shows how to register collectors, discover collectors,
and create collector instances using the registry.
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.data_collection.collector_registry import (
    get_collector_registry,
    register_collector,
    register_factory,
    create_collector,
    list_collectors,
    discover_collectors
)
from src.data_collection.example_collector import ExampleCollector, get_example_collector
from src.utils.logging import get_module_logger

logger = get_module_logger(__name__)


def register_collectors_manually():
    """Register collectors manually."""
    logger.info("Registering collectors manually")
    
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


def print_collector_list():
    """Print the list of registered collectors."""
    collectors = list_collectors()
    
    logger.info(f"Found {len(collectors)} registered collectors:")
    
    for i, collector_info in enumerate(collectors):
        logger.info(f"Collector {i+1}: {collector_info['name']}")
        for key, value in collector_info.items():
            if key != 'name':
                logger.info(f"  {key}: {value}")


def main():
    """Run the collector registry example."""
    parser = argparse.ArgumentParser(description="Demonstrate the collector registry")
    parser.add_argument(
        "--discover",
        action="store_true",
        help="Discover collectors automatically"
    )
    parser.add_argument(
        "--package",
        default="src.data_collection",
        help="Package to search for collectors"
    )
    parser.add_argument(
        "--collector",
        default="example",
        help="Name of the collector to create"
    )
    parser.add_argument(
        "--endpoint",
        default="posts",
        help="API endpoint for the example collector"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=5,
        help="Maximum number of items to collect"
    )
    
    args = parser.parse_args()
    
    # Get the collector registry
    registry = get_collector_registry()
    
    # Register collectors
    if args.discover:
        logger.info(f"Discovering collectors in package: {args.package}")
        count = discover_collectors(args.package)
        logger.info(f"Discovered {count} collectors")
    else:
        register_collectors_manually()
    
    # Print the list of registered collectors
    print_collector_list()
    
    # Create and run a collector
    try:
        logger.info(f"Creating collector: {args.collector}")
        collector = create_collector(
            args.collector,
            api_url="https://jsonplaceholder.typicode.com"
        )
        
        logger.info(f"Running collector: {args.collector}")
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
        
    except KeyError as e:
        logger.error(f"Collector not found: {str(e)}")
    except Exception as e:
        logger.exception(f"Error creating or running collector: {str(e)}")


if __name__ == "__main__":
    main() 