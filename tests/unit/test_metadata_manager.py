"""
Unit tests for the metadata manager.
"""

import os
import sys
import json
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent.parent))

from src.utils.io.metadata_manager import (
    get_metadata_manager,
    MetadataManager,
    MetadataSchema,
    MetadataEnhancer
)


class TestMetadataSchema:
    """Tests for MetadataSchema class."""
    
    def test_metadata_schema_creation(self):
        """Test creating a MetadataSchema."""
        schema = MetadataSchema(
            name='test_schema',
            schema={
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'name': {'type': 'string'},
                    'value': {'type': 'number'}
                },
                'required': ['id', 'name']
            },
            description='Test schema'
        )
        
        assert schema.name == 'test_schema'
        assert schema.schema['type'] == 'object'
        assert 'id' in schema.schema['properties']
        assert schema.description == 'Test schema'
    
    def test_metadata_schema_validate(self):
        """Test validating metadata against a schema."""
        schema = MetadataSchema(
            name='test_schema',
            schema={
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'name': {'type': 'string'},
                    'value': {'type': 'number'}
                },
                'required': ['id', 'name']
            },
            description='Test schema'
        )
        
        # Valid metadata
        valid_metadata = {
            'id': '123',
            'name': 'Test',
            'value': 42
        }
        
        is_valid, errors = schema.validate(valid_metadata)
        assert is_valid is True
        assert len(errors) == 0
        
        # Invalid metadata (missing required field)
        invalid_metadata = {
            'id': '123',
            'value': 42
        }
        
        is_valid, errors = schema.validate(invalid_metadata)
        assert is_valid is False
        assert len(errors) > 0
        assert any('name' in error for error in errors)
        
        # Invalid metadata (wrong type)
        invalid_metadata = {
            'id': '123',
            'name': 'Test',
            'value': 'not a number'
        }
        
        is_valid, errors = schema.validate(invalid_metadata)
        assert is_valid is False
        assert len(errors) > 0
        assert any('value' in error for error in errors)


class TestMetadataEnhancer:
    """Tests for MetadataEnhancer class."""
    
    def test_metadata_enhancer_creation(self):
        """Test creating a MetadataEnhancer."""
        def dummy_enhancer(data, metadata):
            metadata['enhanced'] = True
            return metadata
        
        enhancer = MetadataEnhancer(
            name='test_enhancer',
            enhancer_func=dummy_enhancer,
            description='Test enhancer'
        )
        
        assert enhancer.name == 'test_enhancer'
        assert enhancer.enhancer_func is dummy_enhancer
        assert enhancer.description == 'Test enhancer'
    
    def test_metadata_enhancer_enhance(self):
        """Test enhancing metadata."""
        def dummy_enhancer(data, metadata):
            metadata['enhanced'] = True
            metadata['data_type'] = str(type(data).__name__)
            return metadata
        
        enhancer = MetadataEnhancer(
            name='test_enhancer',
            enhancer_func=dummy_enhancer,
            description='Test enhancer'
        )
        
        data = [1, 2, 3]
        metadata = {'original': True}
        
        enhanced = enhancer.enhance(data, metadata)
        assert enhanced['original'] is True
        assert enhanced['enhanced'] is True
        assert enhanced['data_type'] == 'list'


class TestMetadataManager:
    """Tests for MetadataManager class."""
    
    def test_metadata_manager_creation(self):
        """Test creating a MetadataManager."""
        manager = MetadataManager()
        assert isinstance(manager, MetadataManager)
        assert hasattr(manager, '_schemas')
        assert hasattr(manager, '_enhancers')
    
    def test_register_schema(self):
        """Test registering a schema."""
        manager = MetadataManager()
        
        schema = MetadataSchema(
            name='test_schema',
            schema={'type': 'object'},
            description='Test schema'
        )
        
        manager.register_schema(schema)
        assert 'test_schema' in manager._schemas
        assert manager._schemas['test_schema'] is schema
        
        # Test registering a duplicate schema
        with pytest.raises(ValueError):
            manager.register_schema(schema)
    
    def test_get_schema(self):
        """Test getting a schema."""
        manager = MetadataManager()
        
        schema = MetadataSchema(
            name='test_schema',
            schema={'type': 'object'},
            description='Test schema'
        )
        
        manager.register_schema(schema)
        
        retrieved_schema = manager.get_schema('test_schema')
        assert retrieved_schema is schema
        
        # Test getting a non-existent schema
        assert manager.get_schema('non_existent') is None
    
    def test_register_enhancer(self):
        """Test registering an enhancer."""
        manager = MetadataManager()
        
        def dummy_enhancer(data, metadata):
            return metadata
        
        enhancer = MetadataEnhancer(
            name='test_enhancer',
            enhancer_func=dummy_enhancer,
            description='Test enhancer'
        )
        
        manager.register_enhancer(enhancer)
        assert 'test_enhancer' in manager._enhancers
        assert manager._enhancers['test_enhancer'] is enhancer
        
        # Test registering a duplicate enhancer
        with pytest.raises(ValueError):
            manager.register_enhancer(enhancer)
    
    def test_get_enhancer(self):
        """Test getting an enhancer."""
        manager = MetadataManager()
        
        def dummy_enhancer(data, metadata):
            return metadata
        
        enhancer = MetadataEnhancer(
            name='test_enhancer',
            enhancer_func=dummy_enhancer,
            description='Test enhancer'
        )
        
        manager.register_enhancer(enhancer)
        
        retrieved_enhancer = manager.get_enhancer('test_enhancer')
        assert retrieved_enhancer is enhancer
        
        # Test getting a non-existent enhancer
        assert manager.get_enhancer('non_existent') is None
    
    def test_validate_metadata(self):
        """Test validating metadata against a schema."""
        manager = MetadataManager()
        
        schema = MetadataSchema(
            name='test_schema',
            schema={
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'name': {'type': 'string'}
                },
                'required': ['id', 'name']
            },
            description='Test schema'
        )
        
        manager.register_schema(schema)
        
        # Valid metadata
        valid_metadata = {
            'id': '123',
            'name': 'Test'
        }
        
        is_valid, errors = manager.validate_metadata(valid_metadata, 'test_schema')
        assert is_valid is True
        assert len(errors) == 0
        
        # Invalid metadata
        invalid_metadata = {
            'id': '123'
        }
        
        is_valid, errors = manager.validate_metadata(invalid_metadata, 'test_schema')
        assert is_valid is False
        assert len(errors) > 0
        
        # Non-existent schema
        is_valid, errors = manager.validate_metadata(valid_metadata, 'non_existent')
        assert is_valid is False
        assert len(errors) > 0
        assert 'Schema not found' in errors[0]
    
    def test_enhance_metadata(self):
        """Test enhancing metadata."""
        manager = MetadataManager()
        
        def enhancer1(data, metadata):
            metadata['enhancer1'] = True
            return metadata
        
        def enhancer2(data, metadata):
            metadata['enhancer2'] = True
            return metadata
        
        manager.register_enhancer(MetadataEnhancer(
            name='enhancer1',
            enhancer_func=enhancer1,
            description='Enhancer 1'
        ))
        
        manager.register_enhancer(MetadataEnhancer(
            name='enhancer2',
            enhancer_func=enhancer2,
            description='Enhancer 2'
        ))
        
        # Enhance with specific enhancers
        data = {'test': 'data'}
        metadata = {'original': True}
        
        enhanced = manager.enhance_metadata(data, metadata, enhancers=['enhancer1'])
        assert enhanced['original'] is True
        assert enhanced['enhancer1'] is True
        assert 'enhancer2' not in enhanced
        
        # Enhance with all enhancers
        enhanced = manager.enhance_metadata(data, metadata)
        assert enhanced['original'] is True
        assert enhanced['enhancer1'] is True
        assert enhanced['enhancer2'] is True
        
        # Enhance with non-existent enhancer
        enhanced = manager.enhance_metadata(data, metadata, enhancers=['non_existent'])
        assert enhanced == metadata  # Should return original metadata unchanged
    
    def test_extract_metadata(self):
        """Test extracting metadata from data."""
        manager = MetadataManager()
        
        # Test with DataFrame
        df = pd.DataFrame({
            'id': range(10),
            'value': range(10, 20)
        })
        
        metadata = manager.extract_metadata(df)
        assert metadata['data_type'] == 'DataFrame'
        assert metadata['row_count'] == 10
        assert metadata['column_count'] == 2
        assert set(metadata['columns']) == {'id', 'value'}
        
        # Test with dict
        data_dict = {
            'key1': 'value1',
            'key2': 'value2',
            'nested': {
                'key3': 'value3'
            }
        }
        
        metadata = manager.extract_metadata(data_dict)
        assert metadata['data_type'] == 'dict'
        assert metadata['key_count'] == 3
        assert set(metadata['keys']) == {'key1', 'key2', 'nested'}
        
        # Test with list
        data_list = [1, 2, 3, 4, 5]
        
        metadata = manager.extract_metadata(data_list)
        assert metadata['data_type'] == 'list'
        assert metadata['length'] == 5
        
        # Test with string
        data_str = "test string"
        
        metadata = manager.extract_metadata(data_str)
        assert metadata['data_type'] == 'str'
        assert metadata['length'] == 11
    
    def test_get_metadata_manager(self):
        """Test get_metadata_manager function."""
        manager1 = get_metadata_manager()
        manager2 = get_metadata_manager()
        
        # Should return the same instance
        assert manager1 is manager2 