"""
IO utilities for CityPulse.

This package contains utilities for input/output operations, including data versioning,
metadata tracking, and file management.
"""

from pathlib import Path
import sys

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent)) 