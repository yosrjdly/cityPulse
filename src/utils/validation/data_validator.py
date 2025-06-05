"""
Data validation framework for CityPulse.

This module provides utilities for validating data against rules and constraints,
ensuring data quality throughout the data processing pipeline.
"""

import os
import sys
import json
import re
import datetime
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Union, Any, Tuple, Set, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.utils.logging import get_module_logger
from src.utils.io.metadata_manager import get_metadata_manager

# Initialize logger
logger = get_module_logger(__name__)


class ValidationLevel(Enum):
    """Validation severity levels."""
    ERROR = 'error'  # Must be fixed, data is invalid
    WARNING = 'warning'  # Should be fixed, but data can still be used
    INFO = 'info'  # Informational only, no action required


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for handling non-serializable objects."""
    
    def default(self, obj):
        """Handle non-serializable objects."""
        if isinstance(obj, np.integer):
            return int(obj)
        elif isinstance(obj, np.floating):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (set, frozenset)):
            return list(obj)
        elif isinstance(obj, ValidationLevel):
            return obj.value
        elif isinstance(obj, pd.Series):
            return obj.to_dict()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient='records')
        elif isinstance(obj, Path):
            return str(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.isoformat()
        elif isinstance(obj, datetime.date):
            return obj.isoformat()
        elif isinstance(obj, (bool, int, float, str, type(None))):
            return obj
        elif hasattr(obj, 'to_dict') and callable(getattr(obj, 'to_dict')):
            return obj.to_dict()
        elif hasattr(obj, '__dict__'):
            return {k: v for k, v in obj.__dict__.items() if not k.startswith('_')}
        return str(obj)  # Fallback to string representation


@dataclass
class ValidationResult:
    """Class representing the result of a validation check."""
    
    rule_id: str
    is_valid: bool
    level: ValidationLevel
    message: str
    context: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        result = asdict(self)
        result['level'] = self.level.value
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationResult':
        """Create from dictionary representation."""
        if 'level' in data and isinstance(data['level'], str):
            data['level'] = ValidationLevel(data['level'])
        return cls(**data)


@dataclass
class ValidationRule:
    """Class representing a validation rule."""
    
    rule_id: str
    description: str
    level: ValidationLevel
    validator: Callable
    params: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self, data: Any) -> ValidationResult:
        """Apply the validation rule to the data.
        
        Args:
            data: Data to validate
            
        Returns:
            ValidationResult object
        """
        try:
            is_valid, message, context = self.validator(data, **self.params)
            
            return ValidationResult(
                rule_id=self.rule_id,
                is_valid=is_valid,
                level=self.level,
                message=message or self.description,
                context=context or {}
            )
        except Exception as e:
            logger.error(f"Error applying validation rule {self.rule_id}: {e}")
            return ValidationResult(
                rule_id=self.rule_id,
                is_valid=False,
                level=ValidationLevel.ERROR,
                message=f"Validation rule failed with error: {str(e)}",
                context={'error': str(e)}
            )


@dataclass
class ValidationReport:
    """Class representing a validation report."""
    
    dataset_name: str
    timestamp: str
    results: List[ValidationResult] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    @property
    def is_valid(self) -> bool:
        """Check if all validation rules passed."""
        return all(result.is_valid for result in self.results)
    
    @property
    def error_count(self) -> int:
        """Count of error-level validation failures."""
        return sum(1 for result in self.results 
                  if not result.is_valid and result.level == ValidationLevel.ERROR)
    
    @property
    def warning_count(self) -> int:
        """Count of warning-level validation failures."""
        return sum(1 for result in self.results 
                  if not result.is_valid and result.level == ValidationLevel.WARNING)
    
    @property
    def info_count(self) -> int:
        """Count of info-level validation failures."""
        return sum(1 for result in self.results 
                  if not result.is_valid and result.level == ValidationLevel.INFO)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            'dataset_name': self.dataset_name,
            'timestamp': self.timestamp,
            'is_valid': self.is_valid,
            'error_count': self.error_count,
            'warning_count': self.warning_count,
            'info_count': self.info_count,
            'results': [result.to_dict() for result in self.results],
            'metadata': self.metadata
        }
    
    def to_dataframe(self) -> pd.DataFrame:
        """Convert results to a pandas DataFrame."""
        data = []
        for result in self.results:
            row = {
                'rule_id': result.rule_id,
                'is_valid': result.is_valid,
                'level': result.level.value,
                'message': result.message
            }
            # Add context as flattened columns
            for key, value in result.context.items():
                row[f'context_{key}'] = str(value)
            data.append(row)
        
        return pd.DataFrame(data)
    
    def save(self, file_path: str) -> None:
        """Save the validation report to a file.
        
        Args:
            file_path: Path to save the report
        """
        with open(file_path, 'w') as f:
            json.dump(self.to_dict(), f, indent=2, cls=JSONEncoder)
        
        logger.info(f"Saved validation report to {file_path}")
    
    @classmethod
    def load(cls, file_path: str) -> 'ValidationReport':
        """Load a validation report from a file.
        
        Args:
            file_path: Path to the report file
            
        Returns:
            ValidationReport object
        """
        with open(file_path, 'r') as f:
            data = json.load(f)
        
        results = [ValidationResult.from_dict(result) for result in data.pop('results', [])]
        
        # Remove computed properties from the data
        for key in ['is_valid', 'error_count', 'warning_count', 'info_count']:
            data.pop(key, None)
        
        return cls(results=results, **data)


class DataValidator:
    """System for validating data against rules."""
    
    def __init__(self):
        """Initialize the data validator."""
        # Dictionary to store validation rules by rule_id
        self._rules: Dict[str, ValidationRule] = {}
    
    def register_rule(self, rule: ValidationRule) -> None:
        """Register a validation rule.
        
        Args:
            rule: ValidationRule to register
        """
        if rule.rule_id in self._rules:
            logger.warning(f"Overwriting existing rule with ID: {rule.rule_id}")
        
        self._rules[rule.rule_id] = rule
        logger.debug(f"Registered validation rule: {rule.rule_id}")
    
    def get_rule(self, rule_id: str) -> Optional[ValidationRule]:
        """Get a validation rule by ID.
        
        Args:
            rule_id: ID of the rule to retrieve
            
        Returns:
            ValidationRule object or None if not found
        """
        return self._rules.get(rule_id)
    
    def validate(
        self,
        data: Any,
        rule_ids: Optional[List[str]] = None,
        dataset_name: str = "unnamed_dataset"
    ) -> ValidationReport:
        """Validate data against rules.
        
        Args:
            data: Data to validate
            rule_ids: List of rule IDs to apply (if None, apply all rules)
            dataset_name: Name of the dataset being validated
            
        Returns:
            ValidationReport object
        """
        results = []
        
        # Determine which rules to apply
        rules_to_apply = []
        if rule_ids is not None:
            for rule_id in rule_ids:
                rule = self.get_rule(rule_id)
                if rule:
                    rules_to_apply.append(rule)
                else:
                    logger.warning(f"Rule not found: {rule_id}")
        else:
            rules_to_apply = list(self._rules.values())
        
        # Apply each rule
        for rule in rules_to_apply:
            result = rule.validate(data)
            results.append(result)
            
            # Log the result
            if result.is_valid:
                logger.debug(f"Rule {rule.rule_id} passed")
            else:
                log_method = logger.error if result.level == ValidationLevel.ERROR else \
                            logger.warning if result.level == ValidationLevel.WARNING else \
                            logger.info
                log_method(f"Rule {rule.rule_id} failed: {result.message}")
        
        # Create and return the report
        timestamp = datetime.datetime.now().isoformat()
        return ValidationReport(
            dataset_name=dataset_name,
            timestamp=timestamp,
            results=results,
            metadata={
                'rule_count': len(rules_to_apply),
                'applied_rules': [rule.rule_id for rule in rules_to_apply]
            }
        )


# Singleton instance
_data_validator = None


def get_data_validator() -> DataValidator:
    """Get or create a data validator instance.
    
    Returns:
        DataValidator instance
    """
    global _data_validator
    if _data_validator is None:
        _data_validator = DataValidator()
    return _data_validator


# Common validation functions

def validate_not_null(data: Any, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that data is not None.
    
    Args:
        data: Data to validate
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    is_valid = data is not None
    message = "Data is not None" if is_valid else "Data is None"
    return is_valid, message, {}


def validate_not_empty(data: Any, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that data is not empty.
    
    Args:
        data: Data to validate
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    if data is None:
        return False, "Data is None", {}
    
    try:
        is_valid = len(data) > 0
        message = "Data is not empty" if is_valid else "Data is empty"
        context = {'length': len(data) if hasattr(data, '__len__') else 0}
        return is_valid, message, context
    except TypeError:
        # Object doesn't support len()
        return True, "Data is not a collection", {}


def validate_in_range(data: Union[int, float], min_value: Optional[float] = None, 
                     max_value: Optional[float] = None, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that a numeric value is within a specified range.
    
    Args:
        data: Numeric value to validate
        min_value: Minimum allowed value (inclusive)
        max_value: Maximum allowed value (inclusive)
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    if not isinstance(data, (int, float)):
        return False, f"Expected numeric value, got {type(data).__name__}", {'type': type(data).__name__}
    
    context = {'value': data}
    
    if min_value is not None and max_value is not None:
        is_valid = min_value <= data <= max_value
        message = f"Value {data} is within range [{min_value}, {max_value}]" if is_valid else \
                 f"Value {data} is outside range [{min_value}, {max_value}]"
        context.update({'min_value': min_value, 'max_value': max_value})
    elif min_value is not None:
        is_valid = data >= min_value
        message = f"Value {data} is >= {min_value}" if is_valid else \
                 f"Value {data} is < {min_value}"
        context.update({'min_value': min_value})
    elif max_value is not None:
        is_valid = data <= max_value
        message = f"Value {data} is <= {max_value}" if is_valid else \
                 f"Value {data} is > {max_value}"
        context.update({'max_value': max_value})
    else:
        is_valid = True
        message = "No range constraints specified"
    
    return is_valid, message, context


def validate_regex_match(data: str, pattern: str, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that a string matches a regex pattern.
    
    Args:
        data: String to validate
        pattern: Regex pattern to match
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    if not isinstance(data, str):
        return False, f"Expected string, got {type(data).__name__}", {'type': type(data).__name__}
    
    try:
        is_valid = bool(re.match(pattern, data))
        message = f"String matches pattern '{pattern}'" if is_valid else \
                 f"String does not match pattern '{pattern}'"
        return is_valid, message, {'pattern': pattern, 'value': data}
    except re.error as e:
        return False, f"Invalid regex pattern: {str(e)}", {'pattern': pattern, 'error': str(e)}


# DataFrame validation functions

def validate_df_columns(df: pd.DataFrame, required_columns: List[str], 
                       allow_extra: bool = True, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that a DataFrame has the required columns.
    
    Args:
        df: DataFrame to validate
        required_columns: List of column names that must be present
        allow_extra: Whether to allow extra columns
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    if not isinstance(df, pd.DataFrame):
        return False, f"Expected DataFrame, got {type(df).__name__}", {'type': type(df).__name__}
    
    # Check for missing columns
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    # Check for extra columns
    extra_columns = [col for col in df.columns if col not in required_columns] if not allow_extra else []
    
    is_valid = len(missing_columns) == 0 and len(extra_columns) == 0
    
    context = {
        'required_columns': required_columns,
        'actual_columns': list(df.columns),
        'missing_columns': missing_columns,
        'extra_columns': extra_columns
    }
    
    if is_valid:
        message = "DataFrame has all required columns"
    else:
        messages = []
        if missing_columns:
            messages.append(f"Missing columns: {missing_columns}")
        if extra_columns:
            messages.append(f"Extra columns not allowed: {extra_columns}")
        message = ". ".join(messages)
    
    return is_valid, message, context


def validate_df_no_nulls(df: pd.DataFrame, columns: Optional[List[str]] = None, 
                        threshold: float = 0.0, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that a DataFrame has no null values.
    
    Args:
        df: DataFrame to validate
        columns: List of columns to check (if None, check all columns)
        threshold: Maximum allowed percentage of nulls (0.0 means no nulls allowed)
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    if not isinstance(df, pd.DataFrame):
        return False, f"Expected DataFrame, got {type(df).__name__}", {'type': type(df).__name__}
    
    # Determine which columns to check
    columns_to_check = columns if columns is not None else df.columns
    
    # Calculate null counts and percentages
    null_counts = {}
    null_percentages = {}
    total_rows = len(df)
    
    for col in columns_to_check:
        if col in df.columns:
            null_count = df[col].isna().sum()
            null_percentage = null_count / total_rows if total_rows > 0 else 0.0
            null_counts[col] = int(null_count)
            null_percentages[col] = float(null_percentage)
    
    # Check if any column exceeds the threshold
    invalid_columns = {col: pct for col, pct in null_percentages.items() if pct > threshold}
    is_valid = len(invalid_columns) == 0
    
    context = {
        'null_counts': null_counts,
        'null_percentages': null_percentages,
        'threshold': threshold,
        'total_rows': total_rows
    }
    
    if is_valid:
        message = f"No columns exceed null threshold of {threshold:.1%}"
    else:
        message = f"Columns exceeding null threshold of {threshold:.1%}: " + \
                 ", ".join(f"{col} ({pct:.1%})" for col, pct in invalid_columns.items())
    
    return is_valid, message, context


def validate_df_unique_values(df: pd.DataFrame, columns: List[str], **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that specified columns in a DataFrame have unique values.
    
    Args:
        df: DataFrame to validate
        columns: List of columns that should have unique values
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    if not isinstance(df, pd.DataFrame):
        return False, f"Expected DataFrame, got {type(df).__name__}", {'type': type(df).__name__}
    
    # Check which columns exist in the DataFrame
    existing_columns = [col for col in columns if col in df.columns]
    missing_columns = [col for col in columns if col not in df.columns]
    
    # Check for duplicate values
    duplicate_counts = {}
    for col in existing_columns:
        duplicate_count = len(df) - df[col].nunique()
        if duplicate_count > 0:
            duplicate_counts[col] = duplicate_count
    
    is_valid = len(duplicate_counts) == 0 and len(missing_columns) == 0
    
    context = {
        'duplicate_counts': duplicate_counts,
        'missing_columns': missing_columns
    }
    
    if is_valid:
        message = "All specified columns have unique values"
    else:
        messages = []
        if duplicate_counts:
            messages.append("Columns with duplicate values: " + 
                          ", ".join(f"{col} ({count})" for col, count in duplicate_counts.items()))
        if missing_columns:
            messages.append(f"Columns not found in DataFrame: {missing_columns}")
        message = ". ".join(messages)
    
    return is_valid, message, context


def validate_df_value_counts(df: pd.DataFrame, column: str, allowed_values: List[Any], 
                            allow_other: bool = False, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that a column in a DataFrame only contains allowed values.
    
    Args:
        df: DataFrame to validate
        column: Column to check
        allowed_values: List of allowed values
        allow_other: Whether to allow values not in the allowed list
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    if not isinstance(df, pd.DataFrame):
        return False, f"Expected DataFrame, got {type(df).__name__}", {'type': type(df).__name__}
    
    if column not in df.columns:
        return False, f"Column '{column}' not found in DataFrame", {'missing_column': column}
    
    # Get value counts
    value_counts = df[column].value_counts().to_dict()
    
    # Check for disallowed values
    disallowed_values = {}
    if not allow_other:
        for value, count in value_counts.items():
            if value not in allowed_values and not (pd.isna(value) and None in allowed_values):
                disallowed_values[str(value)] = count
    
    is_valid = len(disallowed_values) == 0
    
    context = {
        'allowed_values': [str(val) for val in allowed_values],
        'actual_values': [str(val) for val in value_counts.keys()],
        'disallowed_values': disallowed_values
    }
    
    if is_valid:
        message = f"Column '{column}' contains only allowed values"
    else:
        message = f"Column '{column}' contains disallowed values: " + \
                 ", ".join(f"{val} ({count})" for val, count in disallowed_values.items())
    
    return is_valid, message, context


# Geospatial validation functions

def validate_geospatial_crs(gdf, expected_crs: str, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that a GeoDataFrame has the expected coordinate reference system.
    
    Args:
        gdf: GeoDataFrame to validate
        expected_crs: Expected CRS string
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    try:
        import geopandas as gpd
        
        if not isinstance(gdf, gpd.GeoDataFrame):
            return False, f"Expected GeoDataFrame, got {type(gdf).__name__}", {'type': type(gdf).__name__}
        
        if gdf.crs is None:
            return False, "GeoDataFrame has no CRS defined", {'actual_crs': None}
        
        # Convert CRS to string for comparison
        actual_crs_str = str(gdf.crs)
        is_valid = actual_crs_str == expected_crs
        
        context = {
            'expected_crs': expected_crs,
            'actual_crs': actual_crs_str
        }
        
        if is_valid:
            message = f"GeoDataFrame has expected CRS: {expected_crs}"
        else:
            message = f"GeoDataFrame has unexpected CRS: {actual_crs_str}, expected: {expected_crs}"
        
        return is_valid, message, context
    
    except ImportError:
        return False, "geopandas not available for validation", {'error': 'ImportError'}


def validate_geospatial_bounds(gdf, min_x: float, min_y: float, max_x: float, max_y: float, 
                              **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that a GeoDataFrame's geometries are within specified bounds.
    
    Args:
        gdf: GeoDataFrame to validate
        min_x: Minimum x-coordinate
        min_y: Minimum y-coordinate
        max_x: Maximum x-coordinate
        max_y: Maximum y-coordinate
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    try:
        import geopandas as gpd
        
        if not isinstance(gdf, gpd.GeoDataFrame):
            return False, f"Expected GeoDataFrame, got {type(gdf).__name__}", {'type': type(gdf).__name__}
        
        if 'geometry' not in gdf.columns:
            return False, "GeoDataFrame has no geometry column", {}
        
        # Get the bounds of the GeoDataFrame
        bounds = gdf.total_bounds
        actual_min_x, actual_min_y, actual_max_x, actual_max_y = bounds
        
        # Check if the bounds are within the specified range
        is_valid = (
            actual_min_x >= min_x and
            actual_min_y >= min_y and
            actual_max_x <= max_x and
            actual_max_y <= max_y
        )
        
        context = {
            'expected_bounds': {
                'min_x': min_x,
                'min_y': min_y,
                'max_x': max_x,
                'max_y': max_y
            },
            'actual_bounds': {
                'min_x': float(actual_min_x),
                'min_y': float(actual_min_y),
                'max_x': float(actual_max_x),
                'max_y': float(actual_max_y)
            }
        }
        
        if is_valid:
            message = "GeoDataFrame is within specified bounds"
        else:
            message = "GeoDataFrame exceeds specified bounds"
        
        return is_valid, message, context
    
    except ImportError:
        return False, "geopandas not available for validation", {'error': 'ImportError'}


def validate_geospatial_types(gdf, allowed_types: List[str], **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that a GeoDataFrame only contains allowed geometry types.
    
    Args:
        gdf: GeoDataFrame to validate
        allowed_types: List of allowed geometry types
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    try:
        import geopandas as gpd
        
        if not isinstance(gdf, gpd.GeoDataFrame):
            return False, f"Expected GeoDataFrame, got {type(gdf).__name__}", {'type': type(gdf).__name__}
        
        if 'geometry' not in gdf.columns:
            return False, "GeoDataFrame has no geometry column", {}
        
        # Get the unique geometry types
        geom_types = gdf.geometry.type.unique().tolist()
        
        # Check if all geometry types are allowed
        disallowed_types = [gt for gt in geom_types if gt not in allowed_types]
        is_valid = len(disallowed_types) == 0
        
        context = {
            'allowed_types': allowed_types,
            'actual_types': geom_types,
            'disallowed_types': disallowed_types
        }
        
        if is_valid:
            message = "GeoDataFrame contains only allowed geometry types"
        else:
            message = f"GeoDataFrame contains disallowed geometry types: {disallowed_types}"
        
        return is_valid, message, context
    
    except ImportError:
        return False, "geopandas not available for validation", {'error': 'ImportError'}


# Schema validation functions

def validate_against_schema(data: Dict[str, Any], schema: Dict[str, Any], 
                           **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that data conforms to a JSON schema.
    
    Args:
        data: Data to validate
        schema: JSON schema
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    try:
        from jsonschema import validate, ValidationError
        
        try:
            validate(instance=data, schema=schema)
            return True, "Data conforms to schema", {}
        except ValidationError as e:
            return False, f"Schema validation error: {e.message}", {
                'path': list(e.path),
                'schema_path': list(e.schema_path),
                'message': e.message
            }
    except ImportError:
        return False, "jsonschema not available for validation", {'error': 'ImportError'}


def validate_against_metadata_schema(data: Dict[str, Any], schema_name: str, 
                                   **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Validate that data conforms to a metadata schema.
    
    Args:
        data: Data to validate
        schema_name: Name of the metadata schema
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    metadata_manager = get_metadata_manager()
    is_valid, errors = metadata_manager.validate_metadata(data, schema_name)
    
    if is_valid:
        message = f"Data conforms to metadata schema '{schema_name}'"
        context = {}
    else:
        message = f"Metadata schema validation errors: {', '.join(errors)}"
        context = {'errors': errors}
    
    return is_valid, message, context 