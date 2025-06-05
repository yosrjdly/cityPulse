"""
Common test fixtures and utilities for CityPulse tests.

This file contains pytest fixtures that can be used across all tests.
"""

import os
import sys
import json
import shutil
import tempfile
import datetime
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.logging import get_module_logger

# Initialize logger
logger = get_module_logger(__name__)


@pytest.fixture(scope="session")
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


@pytest.fixture(scope="function")
def temp_dir():
    """Create a temporary directory for test files.
    
    The directory is automatically cleaned up after the test.
    """
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def sample_dataframe():
    """Create a sample DataFrame for testing."""
    return pd.DataFrame({
        'id': list(range(1, 101)),
        'name': [f'Item {i}' for i in range(1, 101)],
        'value': [i * 2.5 for i in range(1, 101)],
        'category': ['A' if i % 3 == 0 else 'B' if i % 3 == 1 else 'C' for i in range(1, 101)]
    })


@pytest.fixture(scope="function")
def sample_geodataframe():
    """Create a sample GeoDataFrame for testing."""
    try:
        import geopandas as gpd
        from shapely.geometry import Point
        
        df = pd.DataFrame({
            'id': list(range(1, 101)),
            'name': [f'Point {i}' for i in range(1, 101)],
            'value': [i * 1.5 for i in range(1, 101)],
            'geometry': [Point(i * 0.1, i * 0.1) for i in range(1, 101)]
        })
        
        return gpd.GeoDataFrame(df, geometry='geometry', crs='EPSG:4326')
    except ImportError:
        pytest.skip("geopandas not installed")


@pytest.fixture(scope="function")
def sample_json():
    """Create a sample JSON object for testing."""
    return {
        "id": "test123",
        "name": "Test Object",
        "properties": {
            "created": datetime.datetime.now().isoformat(),
            "version": "1.0.0",
            "tags": ["test", "sample", "json"]
        },
        "values": [1, 2, 3, 4, 5],
        "active": True
    }


@pytest.fixture(scope="session")
def test_data_dir(project_root):
    """Return the test data directory."""
    data_dir = project_root / "tests" / "data"
    data_dir.mkdir(exist_ok=True, parents=True)
    return data_dir


@pytest.fixture(scope="function")
def capture_logs():
    """Fixture to capture logs during a test."""
    import logging
    
    class LogCapture:
        def __init__(self):
            self.records = []
            self.handler = None
            
        def __enter__(self):
            self.handler = logging.StreamHandler(self)
            self.handler.setLevel(logging.DEBUG)
            logging.getLogger().addHandler(self.handler)
            return self
            
        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.handler:
                logging.getLogger().removeHandler(self.handler)
                
        def write(self, msg):
            self.records.append(msg)
            
        def flush(self):
            pass
            
        def get_logs(self):
            return "".join(self.records)
    
    return LogCapture()


def pytest_addoption(parser):
    """Add command-line options to pytest."""
    parser.addoption(
        "--runslow", action="store_true", default=False, help="run slow tests"
    )
    parser.addoption(
        "--rundata", action="store_true", default=False, help="run tests that require data files"
    )


def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line("markers", "slow: mark test as slow to run")
    config.addinivalue_line("markers", "data: mark test as requiring data files")
    config.addinivalue_line("markers", "integration: mark test as an integration test")
    config.addinivalue_line("markers", "unit: mark test as a unit test")
    config.addinivalue_line("markers", "performance: mark test as a performance test")


def pytest_collection_modifyitems(config, items):
    """Skip tests based on command-line options."""
    skip_slow = pytest.mark.skip(reason="need --runslow option to run")
    skip_data = pytest.mark.skip(reason="need --rundata option to run")
    
    for item in items:
        if "slow" in item.keywords and not config.getoption("--runslow"):
            item.add_marker(skip_slow)
        if "data" in item.keywords and not config.getoption("--rundata"):
            item.add_marker(skip_data) 