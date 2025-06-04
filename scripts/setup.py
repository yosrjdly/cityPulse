#!/usr/bin/env python
"""
Setup script for CityPulse project.
This script initializes the project structure and downloads required data.
"""
import os
import sys
import logging
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from config.settings import (
    RAW_DATA_DIR, INTERIM_DATA_DIR, PROCESSED_DATA_DIR, 
    EXTERNAL_DATA_DIR, LOG_DIR, RESULTS_DIR
)

def setup_logging():
    """Set up logging for the setup script."""
    log_file = LOG_DIR / "setup.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger("setup")

def create_directory_structure():
    """Create the directory structure if it doesn't exist."""
    logger.info("Creating directory structure...")
    
    directories = [
        RAW_DATA_DIR,
        INTERIM_DATA_DIR,
        PROCESSED_DATA_DIR,
        EXTERNAL_DATA_DIR,
        LOG_DIR,
        RESULTS_DIR / "figures",
        RESULTS_DIR / "tables",
        RESULTS_DIR / "reports"
    ]
    
    for directory in directories:
        directory.mkdir(exist_ok=True, parents=True)
        logger.info(f"Created directory: {directory}")
    
    logger.info("Directory structure created successfully.")

def create_readme_files():
    """Create README.md files in data directories."""
    logger.info("Creating README files in data directories...")
    
    readme_contents = {
        RAW_DATA_DIR: "# Raw Data\n\nThis directory contains raw data files downloaded from various sources.\nFiles in this directory should be treated as immutable.\n",
        INTERIM_DATA_DIR: "# Interim Data\n\nThis directory contains intermediate data that has been transformed but is not yet ready for analysis.\n",
        PROCESSED_DATA_DIR: "# Processed Data\n\nThis directory contains processed data ready for analysis.\n",
        EXTERNAL_DATA_DIR: "# External Data\n\nThis directory contains data from third-party sources.\n"
    }
    
    for directory, content in readme_contents.items():
        readme_path = directory / "README.md"
        if not readme_path.exists():
            with open(readme_path, "w") as f:
                f.write(content)
            logger.info(f"Created README file: {readme_path}")
    
    logger.info("README files created successfully.")

def main():
    """Main setup function."""
    logger.info("Starting CityPulse project setup...")
    
    create_directory_structure()
    create_readme_files()
    
    logger.info("CityPulse project setup completed successfully.")
    logger.info("Next steps:")
    logger.info("1. Configure your .env file with appropriate credentials")
    logger.info("2. Run data collection scripts to download required data")
    logger.info("3. Start your analysis!")

if __name__ == "__main__":
    logger = setup_logging()
    main()
