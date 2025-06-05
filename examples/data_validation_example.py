#!/usr/bin/env python
"""
Example script demonstrating the data validation framework in CityPulse.

This script shows how to:
1. Create and register validation rules
2. Apply validation rules to different types of data
3. Generate and interpret validation reports
4. Save and load validation reports
"""

import os
import sys
import json
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

from src.utils.validation.data_validator import (
    get_data_validator,
    ValidationLevel,
    ValidationRule,
    ValidationReport,
    validate_not_null,
    validate_not_empty,
    validate_in_range,
    validate_regex_match,
    validate_df_columns,
    validate_df_no_nulls,
    validate_df_unique_values,
    validate_df_value_counts
)
from src.utils.logging import get_module_logger

# Initialize logger
logger = get_module_logger(__name__)

# Example data directory
EXAMPLE_DATA_DIR = Path(__file__).parent.parent / "data" / "examples"
EXAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)


def create_example_data():
    """Create example data files for demonstration."""
    # Create a CSV file with some validation issues
    df = pd.DataFrame({
        'id': list(range(1, 101)) + [None],  # One null ID
        'name': [f'Item {i}' for i in range(1, 101)] + ['Special Item'],
        'value': [i * 2.5 for i in range(1, 101)] + [1000],  # One outlier value
        'category': ['A' if i % 3 == 0 else 'B' if i % 3 == 1 else 'C' for i in range(1, 101)] + ['D']  # One invalid category
    })
    
    # Add some duplicate IDs
    df.loc[10, 'id'] = 5
    df.loc[20, 'id'] = 15
    
    # Add some null values
    df.loc[30, 'name'] = None
    df.loc[40, 'value'] = None
    
    csv_path = EXAMPLE_DATA_DIR / "validation_sample.csv"
    df.to_csv(csv_path, index=False)
    logger.info(f"Created example CSV file: {csv_path}")
    
    return csv_path, df


def register_validation_rules():
    """Register validation rules for the example."""
    logger.info("\n=== Registering Validation Rules ===")
    
    # Get the data validator
    validator = get_data_validator()
    
    # Register basic validation rules
    validator.register_rule(ValidationRule(
        rule_id='not_null',
        description='Data should not be null',
        level=ValidationLevel.ERROR,
        validator=validate_not_null
    ))
    
    validator.register_rule(ValidationRule(
        rule_id='not_empty',
        description='Data should not be empty',
        level=ValidationLevel.ERROR,
        validator=validate_not_empty
    ))
    
    # Register DataFrame-specific rules
    validator.register_rule(ValidationRule(
        rule_id='required_columns',
        description='DataFrame should have all required columns',
        level=ValidationLevel.ERROR,
        validator=validate_df_columns,
        params={'required_columns': ['id', 'name', 'value', 'category']}
    ))
    
    validator.register_rule(ValidationRule(
        rule_id='no_null_ids',
        description='ID column should not have null values',
        level=ValidationLevel.ERROR,
        validator=validate_df_no_nulls,
        params={'columns': ['id'], 'threshold': 0.0}
    ))
    
    validator.register_rule(ValidationRule(
        rule_id='unique_ids',
        description='ID column should have unique values',
        level=ValidationLevel.ERROR,
        validator=validate_df_unique_values,
        params={'columns': ['id']}
    ))
    
    validator.register_rule(ValidationRule(
        rule_id='valid_categories',
        description='Category column should only have allowed values',
        level=ValidationLevel.WARNING,
        validator=validate_df_value_counts,
        params={'column': 'category', 'allowed_values': ['A', 'B', 'C']}
    ))
    
    validator.register_rule(ValidationRule(
        rule_id='value_range',
        description='Value column should be within expected range',
        level=ValidationLevel.INFO,
        validator=lambda df, **kwargs: validate_in_range(
            df['value'].max(), min_value=None, max_value=250
        ),
        params={}
    ))
    
    logger.info(f"Registered {len(validator._rules)} validation rules")
    
    return validator


def validate_dataframe(validator, df):
    """Validate a DataFrame using the registered rules."""
    logger.info("\n=== Validating DataFrame ===")
    
    # Validate the DataFrame
    report = validator.validate(df, dataset_name="sample_dataset")
    
    # Print the validation results
    logger.info(f"Validation result: {'VALID' if report.is_valid else 'INVALID'}")
    logger.info(f"Error count: {report.error_count}")
    logger.info(f"Warning count: {report.warning_count}")
    logger.info(f"Info count: {report.info_count}")
    
    # Print details of failed validations
    for result in report.results:
        if not result.is_valid:
            level_str = result.level.value.upper()
            logger.info(f"[{level_str}] Rule '{result.rule_id}' failed: {result.message}")
    
    return report


def save_and_load_report(report):
    """Demonstrate saving and loading a validation report."""
    logger.info("\n=== Saving and Loading Report ===")
    
    # Save the report to a file
    report_path = EXAMPLE_DATA_DIR / "validation_report.json"
    report.save(report_path)
    
    # Load the report from the file
    loaded_report = ValidationReport.load(report_path)
    
    # Verify that the loaded report matches the original
    logger.info(f"Loaded report is valid: {'Yes' if loaded_report.is_valid == report.is_valid else 'No'}")
    logger.info(f"Loaded report error count: {loaded_report.error_count}")
    logger.info(f"Loaded report warning count: {loaded_report.warning_count}")
    logger.info(f"Loaded report info count: {loaded_report.info_count}")
    
    return loaded_report


def create_report_dataframe(report):
    """Create a DataFrame from the validation report."""
    logger.info("\n=== Creating Report DataFrame ===")
    
    # Convert the report to a DataFrame
    df_report = report.to_dataframe()
    
    # Save the DataFrame to a CSV file
    report_csv_path = EXAMPLE_DATA_DIR / "validation_report.csv"
    df_report.to_csv(report_csv_path, index=False)
    
    logger.info(f"Saved report DataFrame to {report_csv_path}")
    logger.info(f"Report DataFrame shape: {df_report.shape}")
    
    return df_report


def main():
    """Run the data validation example."""
    logger.info("Starting data validation example")
    
    # Create example data
    file_path, df = create_example_data()
    
    # Register validation rules
    validator = register_validation_rules()
    
    # Validate the DataFrame
    report = validate_dataframe(validator, df)
    
    # Save and load the report
    loaded_report = save_and_load_report(report)
    
    # Create a report DataFrame
    df_report = create_report_dataframe(loaded_report)
    
    logger.info("Data validation example completed")


if __name__ == "__main__":
    main() 