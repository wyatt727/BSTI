# BSTI Nessus Test Infrastructure

This directory contains tests for the BSTI Nessus to Plextrac converter. The tests are organized into unit tests and integration tests.

## Test Structure

The tests are organized as follows:

```
tests/
├── __init__.py
├── unit/
│   ├── __init__.py
│   ├── test_*.py
│   └── ...
├── integration/
│   ├── __init__.py
│   ├── test_*.py
│   └── ...
└── ...
```

## Running Tests

### Running All Tests

To run all tests, use the following command from the project root:

```bash
pytest
```

### Running Tests with Coverage

To run tests with coverage reporting, use the provided script:

```bash
./scripts/run_tests_with_coverage.py
```

This will run all tests and generate coverage reports in HTML and terminal output formats.

### Running Specific Test Types

To run only unit tests:

```bash
pytest -m unit
# or
./scripts/run_tests_with_coverage.py --unit-only
```

To run only integration tests:

```bash
pytest -m integration
# or
./scripts/run_tests_with_coverage.py --integration-only
```

### Running Specific Test Files

To run a specific test file:

```bash
pytest bsti_nessus/tests/unit/test_file.py
# or
./scripts/run_tests_with_coverage.py bsti_nessus/tests/unit/test_file.py
```

## Test Markers

The following markers are used to categorize tests:

* `unit`: Unit tests
* `integration`: Integration tests
* `slow`: Tests that take a long time to run
* `plextrac`: Tests that require Plextrac API access
* `nessus`: Tests that require Nessus files

To run tests with a specific marker, use the `-m` option:

```bash
pytest -m "marker_name"
```

## Coverage Reporting

Code coverage reports are generated when running tests with coverage:

```bash
pytest --cov=bsti_nessus --cov-report=term --cov-report=html
# or
./scripts/run_tests_with_coverage.py
```

This will generate:
* Terminal output showing coverage statistics
* HTML reports in the `coverage_html_report` directory

## Continuous Integration

The test infrastructure is set up for use in continuous integration. The tests can be run with XML coverage reporting for CI tools:

```bash
./scripts/run_tests_with_coverage.py --xml
```

This will generate:
* XML coverage report in `coverage.xml`

## Writing Tests

### Unit Tests

Unit tests should test individual components in isolation. They should be:
* Fast
* Independent
* Focused on a single unit of functionality

Example unit test:

```python
import pytest
from bsti_nessus.utils.module import function

@pytest.mark.unit
def test_function():
    # Arrange
    input_data = ...
    
    # Act
    result = function(input_data)
    
    # Assert
    assert result == expected_result
```

### Integration Tests

Integration tests should test the interaction between multiple components. They should:
* Test workflows that span multiple units
* Verify that components work together
* Mock external dependencies

Example integration test:

```python
import pytest
from unittest.mock import patch, MagicMock
from bsti_nessus.core.component_a import ComponentA
from bsti_nessus.core.component_b import ComponentB

@pytest.mark.integration
def test_workflow():
    # Arrange
    component_a = ComponentA()
    component_b = ComponentB()
    
    # Act
    with patch('some_external_dependency', MagicMock(return_value=...)):
        result = component_a.do_something_with(component_b)
    
    # Assert
    assert result == expected_result
```

### Test Fixtures

Reusable test fixtures are defined in each test module. Common fixtures are defined in `conftest.py` files.

Example fixture:

```python
@pytest.fixture
def sample_data():
    """Fixture that provides sample data for tests."""
    data = {
        "key": "value",
        ...
    }
    return data
```

## Test Dependencies

The test infrastructure depends on the following packages:

* pytest
* pytest-cov
* pytest-mock

These dependencies are included in the project's development requirements. 