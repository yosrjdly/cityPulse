"""
Unit tests for the data validation framework.
"""

import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.validation.data_validator import (
    get_data_validator,
    ValidationLevel,
    ValidationRule,
    ValidationResult,
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


class TestValidationLevel:
    """Tests for ValidationLevel enum."""
    
    def test_validation_level_values(self):
        """Test that ValidationLevel has the expected values."""
        assert ValidationLevel.ERROR.value == 'error'
        assert ValidationLevel.WARNING.value == 'warning'
        assert ValidationLevel.INFO.value == 'info'


class TestValidationResult:
    """Tests for ValidationResult class."""
    
    def test_validation_result_creation(self):
        """Test creating a ValidationResult."""
        result = ValidationResult(
            rule_id='test_rule',
            is_valid=True,
            level=ValidationLevel.INFO,
            message='Test message',
            context={'key': 'value'}
        )
        
        assert result.rule_id == 'test_rule'
        assert result.is_valid is True
        assert result.level == ValidationLevel.INFO
        assert result.message == 'Test message'
        assert result.context == {'key': 'value'}
    
    def test_validation_result_to_dict(self):
        """Test converting ValidationResult to dictionary."""
        result = ValidationResult(
            rule_id='test_rule',
            is_valid=True,
            level=ValidationLevel.INFO,
            message='Test message',
            context={'key': 'value'}
        )
        
        result_dict = result.to_dict()
        assert result_dict['rule_id'] == 'test_rule'
        assert result_dict['is_valid'] is True
        assert result_dict['level'] == 'info'  # Should be string value
        assert result_dict['message'] == 'Test message'
        assert result_dict['context'] == {'key': 'value'}
    
    def test_validation_result_from_dict(self):
        """Test creating ValidationResult from dictionary."""
        result_dict = {
            'rule_id': 'test_rule',
            'is_valid': True,
            'level': 'warning',
            'message': 'Test message',
            'context': {'key': 'value'}
        }
        
        result = ValidationResult.from_dict(result_dict)
        assert result.rule_id == 'test_rule'
        assert result.is_valid is True
        assert result.level == ValidationLevel.WARNING
        assert result.message == 'Test message'
        assert result.context == {'key': 'value'}


class TestValidationRule:
    """Tests for ValidationRule class."""
    
    def test_validation_rule_creation(self):
        """Test creating a ValidationRule."""
        def dummy_validator(data, **kwargs):
            return True, "Valid", {"data": data}
        
        rule = ValidationRule(
            rule_id='test_rule',
            description='Test description',
            level=ValidationLevel.ERROR,
            validator=dummy_validator,
            params={'param1': 'value1'}
        )
        
        assert rule.rule_id == 'test_rule'
        assert rule.description == 'Test description'
        assert rule.level == ValidationLevel.ERROR
        assert rule.validator is dummy_validator
        assert rule.params == {'param1': 'value1'}
    
    def test_validation_rule_validate(self):
        """Test applying a ValidationRule to data."""
        def dummy_validator(data, param1=None, **kwargs):
            is_valid = data is not None
            message = "Data is valid" if is_valid else "Data is invalid"
            context = {"data": str(data), "param1": param1}
            return is_valid, message, context
        
        rule = ValidationRule(
            rule_id='test_rule',
            description='Test description',
            level=ValidationLevel.ERROR,
            validator=dummy_validator,
            params={'param1': 'value1'}
        )
        
        result = rule.validate("test_data")
        assert result.is_valid is True
        assert result.rule_id == 'test_rule'
        assert result.level == ValidationLevel.ERROR
        assert "valid" in result.message.lower()
        assert result.context['param1'] == 'value1'
        
        result = rule.validate(None)
        assert result.is_valid is False
        assert "invalid" in result.message.lower()
    
    def test_validation_rule_exception_handling(self):
        """Test that ValidationRule handles exceptions in the validator."""
        def failing_validator(data, **kwargs):
            raise ValueError("Test error")
        
        rule = ValidationRule(
            rule_id='failing_rule',
            description='Rule that fails',
            level=ValidationLevel.WARNING,
            validator=failing_validator
        )
        
        result = rule.validate("test_data")
        assert result.is_valid is False
        assert result.level == ValidationLevel.ERROR  # Errors are always ERROR level
        assert "failed with error" in result.message
        assert "Test error" in result.context['error']


class TestValidationReport:
    """Tests for ValidationReport class."""
    
    def test_validation_report_creation(self):
        """Test creating a ValidationReport."""
        report = ValidationReport(
            dataset_name="test_dataset",
            timestamp="2023-01-01T00:00:00",
            results=[],
            metadata={"key": "value"}
        )
        
        assert report.dataset_name == "test_dataset"
        assert report.timestamp == "2023-01-01T00:00:00"
        assert report.results == []
        assert report.metadata == {"key": "value"}
    
    def test_validation_report_is_valid(self):
        """Test the is_valid property of ValidationReport."""
        valid_result = ValidationResult(
            rule_id='valid_rule',
            is_valid=True,
            level=ValidationLevel.INFO,
            message='Valid',
            context={}
        )
        
        invalid_result = ValidationResult(
            rule_id='invalid_rule',
            is_valid=False,
            level=ValidationLevel.ERROR,
            message='Invalid',
            context={}
        )
        
        # Report with only valid results
        report = ValidationReport(
            dataset_name="test_dataset",
            timestamp="2023-01-01T00:00:00",
            results=[valid_result, valid_result],
            metadata={}
        )
        assert report.is_valid is True
        
        # Report with mixed results
        report = ValidationReport(
            dataset_name="test_dataset",
            timestamp="2023-01-01T00:00:00",
            results=[valid_result, invalid_result],
            metadata={}
        )
        assert report.is_valid is False
        
        # Report with only invalid results
        report = ValidationReport(
            dataset_name="test_dataset",
            timestamp="2023-01-01T00:00:00",
            results=[invalid_result, invalid_result],
            metadata={}
        )
        assert report.is_valid is False
    
    def test_validation_report_count_properties(self):
        """Test the error_count, warning_count, and info_count properties."""
        error_result = ValidationResult(
            rule_id='error_rule',
            is_valid=False,
            level=ValidationLevel.ERROR,
            message='Error',
            context={}
        )
        
        warning_result = ValidationResult(
            rule_id='warning_rule',
            is_valid=False,
            level=ValidationLevel.WARNING,
            message='Warning',
            context={}
        )
        
        info_result = ValidationResult(
            rule_id='info_rule',
            is_valid=False,
            level=ValidationLevel.INFO,
            message='Info',
            context={}
        )
        
        valid_result = ValidationResult(
            rule_id='valid_rule',
            is_valid=True,
            level=ValidationLevel.ERROR,  # Level doesn't matter if is_valid is True
            message='Valid',
            context={}
        )
        
        report = ValidationReport(
            dataset_name="test_dataset",
            timestamp="2023-01-01T00:00:00",
            results=[
                error_result, error_result,
                warning_result, warning_result, warning_result,
                info_result,
                valid_result
            ],
            metadata={}
        )
        
        assert report.error_count == 2
        assert report.warning_count == 3
        assert report.info_count == 1
    
    def test_validation_report_to_dict(self):
        """Test converting ValidationReport to dictionary."""
        result = ValidationResult(
            rule_id='test_rule',
            is_valid=True,
            level=ValidationLevel.INFO,
            message='Test message',
            context={}
        )
        
        report = ValidationReport(
            dataset_name="test_dataset",
            timestamp="2023-01-01T00:00:00",
            results=[result],
            metadata={"key": "value"}
        )
        
        report_dict = report.to_dict()
        assert report_dict['dataset_name'] == "test_dataset"
        assert report_dict['timestamp'] == "2023-01-01T00:00:00"
        assert report_dict['is_valid'] is True
        assert report_dict['error_count'] == 0
        assert report_dict['warning_count'] == 0
        assert report_dict['info_count'] == 0
        assert len(report_dict['results']) == 1
        assert report_dict['metadata'] == {"key": "value"}
    
    def test_validation_report_to_dataframe(self, temp_dir):
        """Test converting ValidationReport to DataFrame."""
        result1 = ValidationResult(
            rule_id='rule1',
            is_valid=True,
            level=ValidationLevel.INFO,
            message='Message 1',
            context={"key1": "value1"}
        )
        
        result2 = ValidationResult(
            rule_id='rule2',
            is_valid=False,
            level=ValidationLevel.ERROR,
            message='Message 2',
            context={"key2": "value2", "key3": "value3"}
        )
        
        report = ValidationReport(
            dataset_name="test_dataset",
            timestamp="2023-01-01T00:00:00",
            results=[result1, result2],
            metadata={}
        )
        
        df = report.to_dataframe()
        assert len(df) == 2
        assert 'rule_id' in df.columns
        assert 'is_valid' in df.columns
        assert 'level' in df.columns
        assert 'message' in df.columns
        assert 'context_key1' in df.columns
        assert 'context_key2' in df.columns
        assert 'context_key3' in df.columns
        
        # Check values - using == instead of 'is' for numpy boolean comparison
        assert df.loc[0, 'rule_id'] == 'rule1'
        assert df.loc[0, 'is_valid'] == True
        assert df.loc[0, 'level'] == 'info'
        assert df.loc[0, 'context_key1'] == 'value1'
        
        assert df.loc[1, 'rule_id'] == 'rule2'
        assert df.loc[1, 'is_valid'] == False
        assert df.loc[1, 'level'] == 'error'
        assert df.loc[1, 'context_key2'] == 'value2'
        assert df.loc[1, 'context_key3'] == 'value3'
    
    def test_validation_report_save_load(self, temp_dir):
        """Test saving and loading ValidationReport."""
        result = ValidationResult(
            rule_id='test_rule',
            is_valid=True,
            level=ValidationLevel.INFO,
            message='Test message',
            context={"key": "value"}
        )
        
        report = ValidationReport(
            dataset_name="test_dataset",
            timestamp="2023-01-01T00:00:00",
            results=[result],
            metadata={"meta_key": "meta_value"}
        )
        
        # Save the report
        report_path = temp_dir / "test_report.json"
        report.save(str(report_path))
        
        # Check that the file exists
        assert report_path.exists()
        
        # Load the report
        loaded_report = ValidationReport.load(str(report_path))
        
        # Check that the loaded report matches the original
        assert loaded_report.dataset_name == report.dataset_name
        assert loaded_report.timestamp == report.timestamp
        assert len(loaded_report.results) == len(report.results)
        assert loaded_report.results[0].rule_id == report.results[0].rule_id
        assert loaded_report.results[0].is_valid == report.results[0].is_valid
        assert loaded_report.results[0].level == report.results[0].level
        assert loaded_report.results[0].message == report.results[0].message
        assert loaded_report.metadata == report.metadata


class TestDataValidator:
    """Tests for DataValidator class."""
    
    def test_register_and_get_rule(self):
        """Test registering and retrieving rules."""
        validator = get_data_validator()
        
        # Clear existing rules for test
        validator._rules = {}
        
        rule = ValidationRule(
            rule_id='test_rule',
            description='Test description',
            level=ValidationLevel.ERROR,
            validator=validate_not_null
        )
        
        validator.register_rule(rule)
        assert 'test_rule' in validator._rules
        
        retrieved_rule = validator.get_rule('test_rule')
        assert retrieved_rule is rule
        
        # Test getting a non-existent rule
        assert validator.get_rule('non_existent_rule') is None
    
    def test_validate(self, sample_dataframe):
        """Test validating data with rules."""
        validator = get_data_validator()
        
        # Clear existing rules for test
        validator._rules = {}
        
        # Register some rules
        validator.register_rule(ValidationRule(
            rule_id='not_null',
            description='Data should not be null',
            level=ValidationLevel.ERROR,
            validator=validate_not_null
        ))
        
        validator.register_rule(ValidationRule(
            rule_id='df_columns',
            description='DataFrame should have required columns',
            level=ValidationLevel.ERROR,
            validator=validate_df_columns,
            params={'required_columns': ['id', 'name', 'value']}
        ))
        
        # Validate with all rules
        report = validator.validate(sample_dataframe, dataset_name="test_dataset")
        assert report.is_valid is True
        assert len(report.results) == 2
        
        # Validate with specific rules
        report = validator.validate(sample_dataframe, rule_ids=['not_null'], dataset_name="test_dataset")
        assert report.is_valid is True
        assert len(report.results) == 1
        assert report.results[0].rule_id == 'not_null'
        
        # Validate with non-existent rules
        report = validator.validate(sample_dataframe, rule_ids=['non_existent'], dataset_name="test_dataset")
        assert report.is_valid is True
        assert len(report.results) == 0


class TestBuiltinValidators:
    """Tests for built-in validator functions."""
    
    def test_validate_not_null(self):
        """Test validate_not_null function."""
        is_valid, message, context = validate_not_null("data")
        assert is_valid is True
        assert "not None" in message
        
        is_valid, message, context = validate_not_null(None)
        assert is_valid is False
        assert "is None" in message
    
    def test_validate_not_empty(self):
        """Test validate_not_empty function."""
        is_valid, message, context = validate_not_empty([1, 2, 3])
        assert is_valid is True
        assert "not empty" in message
        assert context['length'] == 3
        
        is_valid, message, context = validate_not_empty([])
        assert is_valid is False
        assert "empty" in message
        assert context['length'] == 0
        
        is_valid, message, context = validate_not_empty(None)
        assert is_valid is False
        assert "None" in message
        
        # Test with object that doesn't support len()
        is_valid, message, context = validate_not_empty(123)
        assert is_valid is True
        assert "not a collection" in message
    
    def test_validate_in_range(self):
        """Test validate_in_range function."""
        # Test with min and max
        is_valid, message, context = validate_in_range(5, min_value=0, max_value=10)
        assert is_valid is True
        assert "within range" in message
        
        is_valid, message, context = validate_in_range(15, min_value=0, max_value=10)
        assert is_valid is False
        assert "outside range" in message
        
        # Test with only min
        is_valid, message, context = validate_in_range(5, min_value=0)
        assert is_valid is True
        assert ">=" in message
        
        is_valid, message, context = validate_in_range(-5, min_value=0)
        assert is_valid is False
        assert "<" in message
        
        # Test with only max
        is_valid, message, context = validate_in_range(5, max_value=10)
        assert is_valid is True
        assert "<=" in message
        
        is_valid, message, context = validate_in_range(15, max_value=10)
        assert is_valid is False
        assert ">" in message
        
        # Test with non-numeric value
        is_valid, message, context = validate_in_range("not a number", min_value=0, max_value=10)
        assert is_valid is False
        assert "Expected numeric value" in message
    
    def test_validate_regex_match(self):
        """Test validate_regex_match function."""
        is_valid, message, context = validate_regex_match("abc123", pattern=r"^[a-z]+\d+$")
        assert is_valid is True
        assert "matches pattern" in message
        
        is_valid, message, context = validate_regex_match("123abc", pattern=r"^[a-z]+\d+$")
        assert is_valid is False
        assert "does not match pattern" in message
        
        # Test with non-string value
        is_valid, message, context = validate_regex_match(123, pattern=r"^[a-z]+\d+$")
        assert is_valid is False
        assert "Expected string" in message
        
        # Test with invalid regex pattern
        is_valid, message, context = validate_regex_match("abc", pattern=r"[")
        assert is_valid is False
        assert "Invalid regex pattern" in message
    
    def test_validate_df_columns(self, sample_dataframe):
        """Test validate_df_columns function."""
        # Test with all required columns present
        is_valid, message, context = validate_df_columns(
            sample_dataframe, 
            required_columns=['id', 'name', 'value']
        )
        assert is_valid is True
        assert "has all required columns" in message
        
        # Test with missing columns
        is_valid, message, context = validate_df_columns(
            sample_dataframe, 
            required_columns=['id', 'name', 'missing_column']
        )
        assert is_valid is False
        assert "Missing columns" in message
        assert 'missing_column' in context['missing_columns']
        
        # Test with extra columns not allowed
        is_valid, message, context = validate_df_columns(
            sample_dataframe, 
            required_columns=['id', 'name'], 
            allow_extra=False
        )
        assert is_valid is False
        assert "Extra columns not allowed" in message
        assert 'value' in context['extra_columns']
        assert 'category' in context['extra_columns']
        
        # Test with non-DataFrame input
        is_valid, message, context = validate_df_columns(
            "not a dataframe", 
            required_columns=['id']
        )
        assert is_valid is False
        assert "Expected DataFrame" in message
    
    def test_validate_df_no_nulls(self, sample_dataframe):
        """Test validate_df_no_nulls function."""
        # Test with no nulls
        is_valid, message, context = validate_df_no_nulls(sample_dataframe)
        assert is_valid is True
        assert "No columns exceed null threshold" in message
        
        # Add some nulls
        df_with_nulls = sample_dataframe.copy()
        df_with_nulls.loc[0:4, 'name'] = None  # 5% nulls
        
        # Test with nulls and default threshold (0.0)
        is_valid, message, context = validate_df_no_nulls(df_with_nulls)
        assert is_valid is False
        assert "Columns exceeding null threshold" in message
        assert 'name' in message
        
        # Test with nulls and custom threshold
        is_valid, message, context = validate_df_no_nulls(df_with_nulls, threshold=0.1)
        assert is_valid is True
        assert "No columns exceed null threshold" in message
        
        # Test with specific columns
        is_valid, message, context = validate_df_no_nulls(df_with_nulls, columns=['id', 'value'])
        assert is_valid is True
        assert "No columns exceed null threshold" in message
        
        # Test with non-DataFrame input
        is_valid, message, context = validate_df_no_nulls("not a dataframe")
        assert is_valid is False
        assert "Expected DataFrame" in message
    
    def test_validate_df_unique_values(self, sample_dataframe):
        """Test validate_df_unique_values function."""
        # Test with unique values
        is_valid, message, context = validate_df_unique_values(sample_dataframe, columns=['id'])
        assert is_valid is True
        assert "have unique values" in message
        
        # Add some duplicates
        df_with_duplicates = sample_dataframe.copy()
        df_with_duplicates.loc[10, 'id'] = df_with_duplicates.loc[0, 'id']
        df_with_duplicates.loc[20, 'id'] = df_with_duplicates.loc[0, 'id']
        
        # Test with duplicates
        is_valid, message, context = validate_df_unique_values(df_with_duplicates, columns=['id'])
        assert is_valid is False
        assert "Columns with duplicate values" in message
        assert 'id' in message
        
        # Test with missing columns
        is_valid, message, context = validate_df_unique_values(sample_dataframe, columns=['id', 'missing_column'])
        assert is_valid is False
        assert "Columns not found in DataFrame" in message
        assert 'missing_column' in context['missing_columns']
        
        # Test with non-DataFrame input
        is_valid, message, context = validate_df_unique_values("not a dataframe", columns=['id'])
        assert is_valid is False
        assert "Expected DataFrame" in message
    
    def test_validate_df_value_counts(self, sample_dataframe):
        """Test validate_df_value_counts function."""
        # Test with allowed values
        is_valid, message, context = validate_df_value_counts(
            sample_dataframe, 
            column='category', 
            allowed_values=['A', 'B', 'C']
        )
        assert is_valid is True
        assert "contains only allowed values" in message
        
        # Add a disallowed value
        df_with_disallowed = sample_dataframe.copy()
        df_with_disallowed.loc[0, 'category'] = 'D'
        
        # Test with disallowed values
        is_valid, message, context = validate_df_value_counts(
            df_with_disallowed, 
            column='category', 
            allowed_values=['A', 'B', 'C']
        )
        assert is_valid is False
        assert "contains disallowed values" in message
        assert 'D' in message
        
        # Test with allow_other=True
        is_valid, message, context = validate_df_value_counts(
            df_with_disallowed, 
            column='category', 
            allowed_values=['A', 'B', 'C'],
            allow_other=True
        )
        assert is_valid is True
        assert "contains only allowed values" in message
        
        # Test with missing column
        is_valid, message, context = validate_df_value_counts(
            sample_dataframe, 
            column='missing_column', 
            allowed_values=['A']
        )
        assert is_valid is False
        assert "not found in DataFrame" in message
        
        # Test with non-DataFrame input
        is_valid, message, context = validate_df_value_counts(
            "not a dataframe", 
            column='category', 
            allowed_values=['A']
        )
        assert is_valid is False
        assert "Expected DataFrame" in message 