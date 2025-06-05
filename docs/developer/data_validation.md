# Data Validation Framework

The CityPulse data validation framework provides a comprehensive system for validating data against rules and constraints, ensuring data quality throughout the data processing pipeline.

## Overview

Data validation is a critical part of any data processing pipeline, helping to ensure that data meets quality standards and is fit for purpose. The CityPulse data validation framework provides:

- **Rule-based validation**: Define and apply validation rules to data
- **Multi-level severity**: Categorize validation issues by severity (error, warning, info)
- **Comprehensive reporting**: Generate detailed validation reports
- **Extensibility**: Easily add custom validation rules
- **Integration**: Seamlessly integrate with other CityPulse components

## Key Components

### ValidationLevel

The `ValidationLevel` enum defines the severity levels for validation rules:

- **ERROR**: Must be fixed, data is invalid
- **WARNING**: Should be fixed, but data can still be used
- **INFO**: Informational only, no action required

### ValidationResult

The `ValidationResult` class represents the result of a validation check:

- **rule_id**: Identifier for the validation rule
- **is_valid**: Whether the data passed the validation
- **level**: Severity level of the validation rule
- **message**: Description of the validation result
- **context**: Additional context about the validation result

### ValidationRule

The `ValidationRule` class defines a validation rule:

- **rule_id**: Unique identifier for the rule
- **description**: Description of what the rule checks
- **level**: Severity level of the rule
- **validator**: Function that performs the validation
- **params**: Parameters for the validator function

### ValidationReport

The `ValidationReport` class represents a validation report:

- **dataset_name**: Name of the validated dataset
- **timestamp**: When the validation was performed
- **results**: List of validation results
- **metadata**: Additional metadata about the validation

### DataValidator

The `DataValidator` class is the main interface for validating data:

- **register_rule**: Register a validation rule
- **get_rule**: Get a validation rule by ID
- **validate**: Validate data against rules

## Built-in Validators

The framework includes a variety of built-in validators for common validation tasks:

### Basic Validators

- **validate_not_null**: Validate that data is not None
- **validate_not_empty**: Validate that data is not empty
- **validate_in_range**: Validate that a numeric value is within a specified range
- **validate_regex_match**: Validate that a string matches a regex pattern

### DataFrame Validators

- **validate_df_columns**: Validate that a DataFrame has the required columns
- **validate_df_no_nulls**: Validate that a DataFrame has no null values
- **validate_df_unique_values**: Validate that specified columns have unique values
- **validate_df_value_counts**: Validate that a column only contains allowed values

### Geospatial Validators

- **validate_geospatial_crs**: Validate that a GeoDataFrame has the expected CRS
- **validate_geospatial_bounds**: Validate that geometries are within specified bounds
- **validate_geospatial_types**: Validate that only allowed geometry types are present

### Schema Validators

- **validate_against_schema**: Validate that data conforms to a JSON schema
- **validate_against_metadata_schema**: Validate that data conforms to a metadata schema

## Usage Examples

### Creating and Registering Rules

```python
from src.utils.validation import get_data_validator, ValidationLevel, ValidationRule
from src.utils.validation.data_validator import validate_not_null

# Get the data validator
validator = get_data_validator()

# Register a validation rule
validator.register_rule(ValidationRule(
    rule_id='not_null',
    description='Data should not be null',
    level=ValidationLevel.ERROR,
    validator=validate_not_null
))
```

### Validating Data

```python
from src.utils.validation import get_data_validator

# Get the data validator
validator = get_data_validator()

# Validate some data
report = validator.validate(data, dataset_name="my_dataset")

# Check if the data is valid
if report.is_valid:
    print("Data is valid!")
else:
    print(f"Data is invalid: {report.error_count} errors found")
```

### Creating Custom Validators

```python
from typing import Tuple, Dict, Any

def validate_custom_rule(data: Any, threshold: float = 0.5, **kwargs) -> Tuple[bool, str, Dict[str, Any]]:
    """Custom validation rule.
    
    Args:
        data: Data to validate
        threshold: Validation threshold
        
    Returns:
        Tuple of (is_valid, message, context)
    """
    # Implement your validation logic here
    is_valid = some_condition(data, threshold)
    
    if is_valid:
        message = "Data passes custom validation"
    else:
        message = "Data fails custom validation"
    
    context = {
        'threshold': threshold,
        'some_metric': calculate_metric(data)
    }
    
    return is_valid, message, context
```

### Working with Validation Reports

```python
from src.utils.validation import get_data_validator

# Get the data validator
validator = get_data_validator()

# Validate some data
report = validator.validate(data, dataset_name="my_dataset")

# Print validation results
print(f"Validation result: {'VALID' if report.is_valid else 'INVALID'}")
print(f"Error count: {report.error_count}")
print(f"Warning count: {report.warning_count}")
print(f"Info count: {report.info_count}")

# Save the report to a file
report.save("validation_report.json")

# Load a report from a file
loaded_report = ValidationReport.load("validation_report.json")

# Convert the report to a DataFrame for analysis
df_report = report.to_dataframe()
```

## Best Practices

1. **Define clear validation rules**: Each rule should check one specific aspect of data quality
2. **Use appropriate severity levels**: Reserve ERROR level for critical issues that must be fixed
3. **Provide context in validation results**: Include relevant information to help diagnose and fix issues
4. **Validate early and often**: Catch data quality issues as early as possible in the pipeline
5. **Create custom validators for domain-specific checks**: Extend the framework with validators for your specific needs

## Implementation Details

### File Structure

- `src/utils/validation/data_validator.py`: Main implementation of the data validation framework
- `src/utils/validation/__init__.py`: Exports key components of the framework

### Dependencies

The data validation framework depends on:

- `src.utils.logging`: For logging
- `src.utils.io.metadata_manager`: For metadata schema validation

## Future Enhancements

1. **Rule groups**: Group related validation rules for easier management
2. **Conditional validation**: Apply rules conditionally based on data characteristics
3. **Performance optimization**: Improve validation performance for large datasets
4. **UI integration**: Create a user interface for viewing validation reports
5. **Auto-correction**: Add capabilities to automatically fix common validation issues 