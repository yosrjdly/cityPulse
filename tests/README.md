# CityPulse Testing Framework

This directory contains the automated testing infrastructure for the CityPulse project.

## Directory Structure

- `unit/`: Unit tests for individual components
- `integration/`: Integration tests for multiple components working together
- `data/`: Test data files used by tests

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

### Test Categories

Tests are categorized using markers. To run tests with a specific marker:

```bash
pytest -m unit  # Run unit tests
pytest -m integration  # Run integration tests
pytest -m slow  # Run slow tests (requires --runslow flag)
pytest -m data  # Run tests that require data files (requires --rundata flag)
```

### Special Test Categories

Some tests have special requirements:

```bash
pytest --runslow  # Run tests marked as slow
pytest --rundata  # Run tests that require data files
```

## Test Fixtures

Common test fixtures are defined in `tests/conftest.py`. These include:

- `project_root`: Returns the project root directory
- `temp_dir`: Creates a temporary directory for test files
- `sample_dataframe`: Creates a sample pandas DataFrame
- `sample_geodataframe`: Creates a sample GeoPandas GeoDataFrame
- `sample_json`: Creates a sample JSON object
- `test_data_dir`: Returns the test data directory
- `capture_logs`: Captures logs during a test

## Writing Tests

### Test Organization

Tests should be organized by component and test type:

- Unit tests go in `tests/unit/`
- Integration tests go in `tests/integration/`

### Test File Naming

Test files should be named `test_*.py`. For example, `test_data_validator.py`.

### Test Class and Function Naming

- Test classes should be named `Test*`
- Test functions should be named `test_*`

### Using Markers

To mark a test, use the `@pytest.mark` decorator:

```python
import pytest

@pytest.mark.unit
def test_something():
    # Test code here
    pass

@pytest.mark.slow
def test_something_slow():
    # Slow test code here
    pass
```

### Using Fixtures

To use a fixture, add it as a parameter to your test function:

```python
def test_with_fixture(temp_dir):
    # temp_dir is a Path object pointing to a temporary directory
    file_path = temp_dir / "test.txt"
    with open(file_path, "w") as f:
        f.write("test")
    
    assert file_path.exists()
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

## Continuous Integration

Tests are automatically run in CI when changes are pushed to the repository. All tests must pass before changes can be merged. 