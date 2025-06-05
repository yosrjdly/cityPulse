"""
Metadata management module for CityPulse.

This module provides utilities for tracking, validating, and managing metadata
for datasets throughout the data processing pipeline.
"""

import os
import sys
import json
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Set, Tuple
from dataclasses import dataclass, field, asdict
import uuid
import re

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logging import get_module_logger
from config.settings import DATA_DIR

# Initialize logger
logger = get_module_logger(__name__)

# Standard metadata fields that should be present in all datasets
STANDARD_METADATA_FIELDS = {
    'title': str,
    'description': str,
    'created_at': str,
    'updated_at': str,
    'created_by': str,
    'source': str,
    'license': str,
    'version': str,
}

# Metadata categories for organization
METADATA_CATEGORIES = {
    'basic': ['title', 'description', 'created_at', 'updated_at', 'created_by'],
    'provenance': ['source', 'license', 'version', 'source_url', 'collection_date'],
    'technical': ['format', 'encoding', 'schema', 'row_count', 'column_count', 'file_size'],
    'spatial': ['spatial_coverage', 'spatial_resolution', 'crs', 'bbox'],
    'temporal': ['temporal_coverage', 'temporal_resolution', 'time_period', 'frequency'],
    'quality': ['completeness', 'accuracy', 'consistency', 'validation_results'],
    'domain': ['domain_tags', 'keywords', 'category', 'subcategory'],
    'usage': ['access_rights', 'usage_notes', 'limitations', 'citation'],
}


@dataclass
class MetadataSchema:
    """Class representing a metadata schema with field definitions."""
    
    name: str
    description: str
    fields: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    required_fields: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = asdict(self)
        # Convert set to list for JSON serialization
        result['required_fields'] = list(self.required_fields)
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'MetadataSchema':
        """Create from dictionary representation."""
        # Convert list back to set
        if 'required_fields' in data and isinstance(data['required_fields'], list):
            data['required_fields'] = set(data['required_fields'])
        return cls(**data)
    
    def validate(self, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """Validate metadata against this schema.
        
        Args:
            metadata: Metadata to validate
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []
        
        # Check required fields
        for field in self.required_fields:
            if field not in metadata:
                errors.append(f"Missing required field: {field}")
        
        # Check field types
        for field, value in metadata.items():
            if field in self.fields:
                field_def = self.fields[field]
                expected_type = field_def.get('type')
                
                # Skip type checking if no type defined
                if not expected_type:
                    continue
                
                # Handle different type specifications
                if expected_type == 'string' and not isinstance(value, str):
                    errors.append(f"Field '{field}' should be a string")
                elif expected_type == 'number' and not isinstance(value, (int, float)):
                    errors.append(f"Field '{field}' should be a number")
                elif expected_type == 'boolean' and not isinstance(value, bool):
                    errors.append(f"Field '{field}' should be a boolean")
                elif expected_type == 'array' and not isinstance(value, list):
                    errors.append(f"Field '{field}' should be an array")
                elif expected_type == 'object' and not isinstance(value, dict):
                    errors.append(f"Field '{field}' should be an object")
                
                # Check pattern if defined
                if 'pattern' in field_def and isinstance(value, str):
                    pattern = field_def['pattern']
                    if not re.match(pattern, value):
                        errors.append(f"Field '{field}' does not match pattern: {pattern}")
                
                # Check enum if defined
                if 'enum' in field_def and value not in field_def['enum']:
                    errors.append(f"Field '{field}' must be one of: {', '.join(str(v) for v in field_def['enum'])}")
        
        return len(errors) == 0, errors


class MetadataManager:
    """System for managing dataset metadata."""
    
    def __init__(
        self,
        schema_dir: Optional[str] = None,
        auto_create_dirs: bool = True
    ):
        """Initialize the metadata manager.
        
        Args:
            schema_dir: Directory to store metadata schemas
            auto_create_dirs: Whether to automatically create directories
        """
        self.schema_dir = Path(schema_dir) if schema_dir else Path(DATA_DIR) / '.schemas'
        
        # Create schema directory if it doesn't exist
        if auto_create_dirs and not self.schema_dir.exists():
            self.schema_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created schema directory: {self.schema_dir}")
        
        # Dictionary to cache loaded schemas
        self._schema_cache: Dict[str, MetadataSchema] = {}
        
        # Load existing schemas
        self._load_schemas()
        
        # Create default schema if it doesn't exist
        if 'default' not in self._schema_cache:
            self._create_default_schema()
    
    def _load_schemas(self):
        """Load existing schemas from disk."""
        if not self.schema_dir.exists():
            logger.warning(f"Schema directory does not exist: {self.schema_dir}")
            return
        
        for schema_file in self.schema_dir.glob('*.json'):
            try:
                with open(schema_file, 'r') as f:
                    schema_data = json.load(f)
                
                schema = MetadataSchema.from_dict(schema_data)
                self._schema_cache[schema.name] = schema
                
            except Exception as e:
                logger.error(f"Error loading schema file {schema_file}: {e}")
    
    def _save_schema(self, schema: MetadataSchema):
        """Save schema to disk.
        
        Args:
            schema: Metadata schema to save
        """
        schema_path = self.schema_dir / f"{schema.name}.json"
        
        with open(schema_path, 'w') as f:
            json.dump(schema.to_dict(), f, indent=2)
        
        logger.debug(f"Saved schema to {schema_path}")
    
    def _create_default_schema(self):
        """Create and save the default metadata schema."""
        fields = {}
        required_fields = set()
        
        # Add standard fields
        for field_name, field_type in STANDARD_METADATA_FIELDS.items():
            fields[field_name] = {
                'type': 'string' if field_type == str else 'number' if field_type in (int, float) else 'boolean',
                'description': f"Standard {field_name} field"
            }
            required_fields.add(field_name)
        
        # Create schema
        schema = MetadataSchema(
            name='default',
            description='Default metadata schema with standard fields',
            fields=fields,
            required_fields=required_fields
        )
        
        # Save to cache and disk
        self._schema_cache['default'] = schema
        self._save_schema(schema)
        
        logger.info("Created default metadata schema")
    
    def get_schema(self, schema_name: str = 'default') -> Optional[MetadataSchema]:
        """Get a metadata schema by name.
        
        Args:
            schema_name: Name of the schema
            
        Returns:
            MetadataSchema object or None if not found
        """
        # Check cache first
        if schema_name in self._schema_cache:
            return self._schema_cache[schema_name]
        
        # Try to load from disk
        schema_path = self.schema_dir / f"{schema_name}.json"
        if not schema_path.exists():
            logger.warning(f"Schema not found: {schema_name}")
            return None
        
        try:
            with open(schema_path, 'r') as f:
                schema_data = json.load(f)
            
            schema = MetadataSchema.from_dict(schema_data)
            self._schema_cache[schema_name] = schema
            return schema
            
        except Exception as e:
            logger.error(f"Error loading schema {schema_name}: {e}")
            return None
    
    def create_schema(
        self,
        name: str,
        description: str,
        fields: Dict[str, Dict[str, Any]],
        required_fields: Optional[Set[str]] = None
    ) -> MetadataSchema:
        """Create a new metadata schema.
        
        Args:
            name: Schema name
            description: Schema description
            fields: Dictionary of field definitions
            required_fields: Set of required field names
            
        Returns:
            Created MetadataSchema object
        """
        if name in self._schema_cache:
            logger.warning(f"Schema already exists: {name}")
            return self._schema_cache[name]
        
        schema = MetadataSchema(
            name=name,
            description=description,
            fields=fields,
            required_fields=required_fields or set()
        )
        
        # Save to cache and disk
        self._schema_cache[name] = schema
        self._save_schema(schema)
        
        logger.info(f"Created new metadata schema: {name}")
        
        return schema
    
    def validate_metadata(
        self,
        metadata: Dict[str, Any],
        schema_name: str = 'default'
    ) -> Tuple[bool, List[str]]:
        """Validate metadata against a schema.
        
        Args:
            metadata: Metadata to validate
            schema_name: Name of the schema to validate against
            
        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        schema = self.get_schema(schema_name)
        if not schema:
            return False, [f"Schema not found: {schema_name}"]
        
        return schema.validate(metadata)
    
    def generate_metadata_template(
        self,
        schema_name: str = 'default',
        include_optional: bool = False
    ) -> Dict[str, Any]:
        """Generate a metadata template based on a schema.
        
        Args:
            schema_name: Name of the schema
            include_optional: Whether to include optional fields
            
        Returns:
            Template metadata dictionary
        """
        schema = self.get_schema(schema_name)
        if not schema:
            logger.warning(f"Schema not found: {schema_name}")
            return {}
        
        template = {}
        
        # Add required fields
        for field in schema.required_fields:
            if field in schema.fields:
                field_def = schema.fields[field]
                template[field] = self._get_default_value(field_def)
        
        # Add optional fields if requested
        if include_optional:
            for field, field_def in schema.fields.items():
                if field not in template:
                    template[field] = self._get_default_value(field_def)
        
        return template
    
    def _get_default_value(self, field_def: Dict[str, Any]) -> Any:
        """Get a default value for a field based on its definition.
        
        Args:
            field_def: Field definition
            
        Returns:
            Default value
        """
        field_type = field_def.get('type', 'string')
        
        if 'default' in field_def:
            return field_def['default']
        
        if field_type == 'string':
            return ""
        elif field_type == 'number':
            return 0
        elif field_type == 'boolean':
            return False
        elif field_type == 'array':
            return []
        elif field_type == 'object':
            return {}
        else:
            return None
    
    def extract_metadata_from_file(self, file_path: str) -> Dict[str, Any]:
        """Extract basic metadata from a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary of extracted metadata
        """
        path = Path(file_path)
        
        if not path.exists():
            logger.warning(f"File not found: {file_path}")
            return {}
        
        metadata = {
            'title': path.stem,
            'description': f"Data from {path.name}",
            'created_at': datetime.datetime.fromtimestamp(path.stat().st_ctime).isoformat(),
            'updated_at': datetime.datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            'created_by': 'system',
            'source': 'file',
            'license': 'unknown',
            'version': '1.0',
            'format': path.suffix.lstrip('.'),
            'file_size': path.stat().st_size
        }
        
        return metadata
    
    def categorize_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
        """Organize metadata into categories.
        
        Args:
            metadata: Flat metadata dictionary
            
        Returns:
            Dictionary with metadata organized by category
        """
        categorized = {category: {} for category in METADATA_CATEGORIES}
        categorized['other'] = {}
        
        # Place each metadata field in its category
        for key, value in metadata.items():
            placed = False
            for category, fields in METADATA_CATEGORIES.items():
                if key in fields:
                    categorized[category][key] = value
                    placed = True
                    break
            
            if not placed:
                categorized['other'][key] = value
        
        # Remove empty categories
        return {k: v for k, v in categorized.items() if v}
    
    def flatten_metadata(self, categorized_metadata: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """Flatten categorized metadata back to a flat dictionary.
        
        Args:
            categorized_metadata: Metadata organized by category
            
        Returns:
            Flat metadata dictionary
        """
        flattened = {}
        
        for category, fields in categorized_metadata.items():
            flattened.update(fields)
        
        return flattened


def get_metadata_manager() -> MetadataManager:
    """Get or create a metadata manager instance.
    
    Returns:
        MetadataManager instance
    """
    return MetadataManager()


class MetadataEnhancer:
    """Utility for enhancing metadata with additional information."""
    
    @staticmethod
    def enhance_tabular_metadata(file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata for tabular data files.
        
        Args:
            file_path: Path to the tabular data file
            metadata: Existing metadata
            
        Returns:
            Enhanced metadata
        """
        import pandas as pd
        
        try:
            # Convert to string if it's a Path object
            file_path_str = str(file_path)
            
            # Determine file type and read accordingly
            if file_path_str.endswith('.csv'):
                df = pd.read_csv(file_path_str)
            elif file_path_str.endswith(('.xls', '.xlsx')):
                df = pd.read_excel(file_path_str)
            elif file_path_str.endswith('.parquet'):
                df = pd.read_parquet(file_path_str)
            else:
                logger.warning(f"Unsupported tabular file format: {file_path_str}")
                return metadata
            
            # Add tabular-specific metadata
            metadata.update({
                'row_count': len(df),
                'column_count': len(df.columns),
                'columns': list(df.columns),
                'dtypes': {col: str(dtype) for col, dtype in df.dtypes.items()},
                'missing_values': {col: int(df[col].isna().sum()) for col in df.columns},
                'completeness': 1 - (df.isna().sum().sum() / (len(df) * len(df.columns)))
            })
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error enhancing tabular metadata for {file_path}: {e}")
            return metadata
    
    @staticmethod
    def enhance_geospatial_metadata(file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata for geospatial data files.
        
        Args:
            file_path: Path to the geospatial data file
            metadata: Existing metadata
            
        Returns:
            Enhanced metadata
        """
        try:
            import geopandas as gpd
            
            # Convert to string if it's a Path object
            file_path_str = str(file_path)
            
            # Read the geospatial file
            gdf = gpd.read_file(file_path_str)
            
            # Add geospatial-specific metadata
            bounds = gdf.total_bounds
            metadata.update({
                'feature_count': len(gdf),
                'geometry_types': list(gdf.geometry.type.unique()),
                'crs': str(gdf.crs),
                'bbox': {
                    'minx': float(bounds[0]),
                    'miny': float(bounds[1]),
                    'maxx': float(bounds[2]),
                    'maxy': float(bounds[3])
                },
                'spatial_coverage': f"{bounds[0]},{bounds[1]},{bounds[2]},{bounds[3]}",
                'attributes': list(gdf.columns),
            })
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error enhancing geospatial metadata for {file_path}: {e}")
            return metadata
    
    @staticmethod
    def enhance_image_metadata(file_path: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance metadata for image files.
        
        Args:
            file_path: Path to the image file
            metadata: Existing metadata
            
        Returns:
            Enhanced metadata
        """
        try:
            from PIL import Image
            import PIL.ExifTags
            
            # Convert to string if it's a Path object
            file_path_str = str(file_path)
            
            # Open the image
            img = Image.open(file_path_str)
            
            # Add image-specific metadata
            metadata.update({
                'width': img.width,
                'height': img.height,
                'format': img.format,
                'mode': img.mode,
                'dpi': img.info.get('dpi', None)
            })
            
            # Extract EXIF data if available
            if hasattr(img, '_getexif') and img._getexif():
                exif = {
                    PIL.ExifTags.TAGS[k]: v
                    for k, v in img._getexif().items()
                    if k in PIL.ExifTags.TAGS
                }
                
                # Add selected EXIF data
                metadata['exif'] = {
                    k: str(v) for k, v in exif.items()
                    if k in ('DateTimeOriginal', 'Make', 'Model', 'GPSInfo')
                }
            
            return metadata
            
        except Exception as e:
            logger.error(f"Error enhancing image metadata for {file_path}: {e}")
            return metadata 