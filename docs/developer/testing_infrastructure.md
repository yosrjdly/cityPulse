# Testing Infrastructure

This document describes the testing infrastructure for the CityPulse project, including the testing framework, test organization, and best practices for writing tests.

## Overview

CityPulse uses pytest as its testing framework, with a comprehensive set of fixtures, markers, and configuration to make testing easy and effective. The testing infrastructure is designed to support:

- **Unit testing**: Testing individual components in isolation
- **Integration testing**: Testing multiple components working together
- **Data validation testing**: Testing with real or synthetic data
- **Performance testing**: Testing the performance characteristics of the system

## Test Organization

Tests are organized into the following directories:

- `tests/unit/`: Unit tests for individual components
- `tests/integration/`: Integration tests for multiple components working together
- `tests/data/`: Test data files used by tests

## Test Configuration

The pytest configuration is defined in `pytest.ini` at the project root. This includes:

- Test discovery patterns
- Display settings
- Warning filters
- Custom markers

## Test Fixtures

Common test fixtures are defined in `tests/conftest.py`. These fixtures provide reusable components for tests, such as:

### Basic Fixtures

- `project_root`: Returns the project root directory
- `temp_dir`: Creates a temporary directory for test files
- `capture_logs`: Captures logs during a test

### Data Fixtures

- `sample_dataframe`: Creates a sample pandas DataFrame
- `sample_geodataframe`: Creates a sample GeoPandas GeoDataFrame
- `sample_json`: Creates a sample JSON object
- `test_data_dir`: Returns the test data directory

## Test Markers

Custom markers are used to categorize tests:

- `unit`: Unit tests that test a single component in isolation
- `integration`: Tests that verify multiple components working together
- `slow`: Tests that take a long time to run (skipped by default)
- `data`: Tests that require specific data files (skipped by default)
- `performance`: Tests that measure performance metrics

## Running Tests

### Basic Usage

To run all tests:

```bash
pytest
```

To run a specific test file:

```bash
pytest tests/unit/test_data_validator.py
```

To run a specific test:

```bash
pytest tests/unit/test_data_validator.py::TestValidationRule::test_validation_rule_creation
```

### Running Tests by Category

Tests can be run by category using markers:

```bash
pytest -m unit  # Run unit tests
pytest -m integration  # Run integration tests
```

### Special Test Categories

Some tests have special requirements and are skipped by default:

```bash
pytest --runslow  # Run tests marked as slow
pytest --rundata  # Run tests that require data files
```

## Test Coverage

To run tests with coverage reporting:

```bash
pytest --cov=src
```

For HTML coverage reports:

```bash
pytest --cov=src --cov-report=html
```

The coverage report will be generated in the `htmlcov/` directory.

## Best Practices for Writing Tests

### General Guidelines

1. **Test one thing per test**: Each test should focus on testing a single aspect of the code
2. **Use descriptive test names**: Test names should describe what is being tested
3. **Use fixtures for common setup**: Use fixtures for common setup code
4. **Clean up after tests**: Use fixtures to clean up resources after tests
5. **Use appropriate assertions**: Use the most specific assertion for the situation

### Unit Test Guidelines

1. **Test in isolation**: Mock or patch external dependencies
2. **Test edge cases**: Test boundary conditions and error cases
3. **Test public interfaces**: Focus on testing the public API of a component
4. **Keep tests fast**: Unit tests should run quickly

### Integration Test Guidelines

1. **Test component interactions**: Focus on how components work together
2. **Use real dependencies when possible**: Minimize mocking for integration tests
3. **Test end-to-end workflows**: Test complete workflows from input to output

### Data Test Guidelines

1. **Use representative data**: Test with data that represents real-world scenarios
2. **Test with edge cases**: Test with boundary conditions and unusual data
3. **Test data validation**: Verify that data validation works correctly

### Performance Test Guidelines

1. **Establish baselines**: Measure and record baseline performance
2. **Test with realistic loads**: Test with realistic data volumes and concurrency
3. **Isolate performance tests**: Run performance tests separately from other tests

## Test Driven Development

The CityPulse project encourages test-driven development (TDD) for new features:

1. **Write tests first**: Write tests that define the expected behavior
2. **Run tests to see them fail**: Verify that the tests fail as expected
3. **Implement the feature**: Write code to make the tests pass
4. **Refactor**: Clean up the code while keeping the tests passing

## Continuous Integration

Tests are automatically run in CI when changes are pushed to the repository. All tests must pass before changes can be merged.

## Adding New Tests

When adding new components to the system, corresponding tests should be added:

1. **Unit tests** for the component in `tests/unit/`
2. **Integration tests** for how the component interacts with other components in `tests/integration/`
3. **Test data** in `tests/data/` if needed

## Test Documentation

Tests serve as documentation for how components should behave. When writing tests:

1. **Use descriptive docstrings**: Describe what the test is checking
2. **Use clear assertions**: Make it obvious what is being verified
3. **Comment complex test logic**: Explain any complex test setup or assertions 