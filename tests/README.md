# BSTI Test Suite

This directory contains all the tests for the BSTI project. The tests are organized as follows:

## Directory Structure

- `tests/` - Contains all test files
  - `test_nmb.py` - Tests for the Nessus Management Buddy (NMB) functionality
  - `test_module_system.py` - Tests for the BSTI module system
  - `test_home_tab.py` - Tests for the Home tab UI component
  - `test_module_editor_tab.py` - Tests for the Module Editor tab UI component
  - `test_view_logs_tab.py` - Tests for the View Logs tab UI component
  - `test_plugin_manager.py` - Tests for the Plugin Manager functionality
  - `run_tab_tests.py` - Script to run all UI component tests
  - `run_nmb_tests.py` - Script to run all NMB tests
  - `run_all_tests.py` - Script to run all tests in the BSTI project
  - `bsti_test.py` - General BSTI functionality tests

## Running Tests

You can run the tests using pytest:

```bash
# Run all tests
python -m pytest

# Run a specific test file
python -m pytest tests/test_nmb.py

# Run tests with verbose output
python -m pytest -v tests/test_nmb.py

# Run tests with coverage report
python -m pytest --cov=BSTI tests/
```

Alternatively, you can use the run scripts:

```bash
# Run all tests
./tests/run_all_tests.py

# Run all tests with verbose output
./tests/run_all_tests.py -v

# Run all tests with HTML coverage report
./tests/run_all_tests.py --html

# Run specific test components
./tests/run_all_tests.py --skip-ui  # Skip UI tests
./tests/run_all_tests.py --skip-nmb  # Skip NMB tests
./tests/run_all_tests.py --skip-module  # Skip module system tests

# Run UI component tests
./tests/run_tab_tests.py

# Run NMB tests
./tests/run_nmb_tests.py
```

## Adding New Tests

When adding new tests:

1. Place the test file in the `tests/` directory
2. Use the naming convention `test_*.py` for test files
3. Make sure to use proper imports that reference modules from the project root
4. Update this README if you add a new test category 