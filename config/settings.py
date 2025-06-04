"""
Project-wide settings for CityPulse.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
INTERIM_DATA_DIR = DATA_DIR / "interim"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
EXTERNAL_DATA_DIR = DATA_DIR / "external"
RESULTS_DIR = PROJECT_ROOT / "results"
LOG_DIR = PROJECT_ROOT / "logs"

# Ensure directories exist
for directory in [RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR, 
                 EXTERNAL_DATA_DIR, RESULTS_DIR, LOG_DIR]:
    directory.mkdir(exist_ok=True, parents=True)

# API Keys (from environment variables)
OSM_USER_AGENT = os.getenv("OSM_USER_AGENT", "CityPulse/1.0")
WORLDBANK_API_KEY = os.getenv("WORLDBANK_API_KEY", "")

# Logging configuration
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Database configuration
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "citypulse")
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# Analysis parameters
BUFFER_DISTANCE = 500  # meters
ISOCHRONE_CUTOFFS = [5, 10, 15, 20]  # minutes
ACCESSIBILITY_THRESHOLD = 15  # minutes
