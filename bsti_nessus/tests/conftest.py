"""
Common pytest fixtures and configuration for the BSTI Nessus tests.
"""
import os
import tempfile
import pytest
from unittest.mock import MagicMock

from bsti_nessus.utils.logger import log, CustomLogger
from bsti_nessus.utils.config_manager import ConfigManager


@pytest.fixture
def mock_logger():
    """Fixture that provides a mock logger."""
    return MagicMock(spec=CustomLogger)


@pytest.fixture
def temp_dir():
    """
    Fixture that creates a temporary directory for test files.
    
    The directory will be automatically removed after the test.
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


@pytest.fixture
def temp_config_file():
    """
    Fixture that creates a temporary configuration file for testing.
    
    The file will be automatically removed after the test.
    """
    sample_config = {
        "plextrac": {
            "instances": {
                "test": {
                    "url": "https://test-instance.plextrac.com",
                    "verify_ssl": False
                }
            }
        },
        "nessus": {
            "csv_format": {
                "required_fields": ["Plugin ID", "Name", "Risk", "Description"],
                "optional_fields": ["Solution", "See Also"]
            },
            "categories": {
                "network": {
                    "writeup_name": "Network Vulnerabilities",
                    "description": "Vulnerabilities related to network configurations",
                    "ids": ["10180", "10287", "10386"]
                }
            }
        },
        "output": {
            "directory": "plextrac_output",
            "screenshots": "screenshots"
        },
        "general": {
            "timeout": 10,
            "threads": 4,
            "log_level": "info"
        }
    }
    
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        import json
        temp_file.write(json.dumps(sample_config).encode('utf-8'))
        file_path = temp_file.name
    
    yield file_path
    
    # Clean up
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def config_manager(temp_config_file):
    """
    Fixture that provides a ConfigManager with a sample configuration.
    """
    return ConfigManager(temp_config_file)


@pytest.fixture
def sample_nessus_csv():
    """
    Fixture that creates a sample Nessus CSV file for testing.
    
    The file will be automatically removed after the test.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as temp_file:
        # Write a header and some sample findings
        temp_file.write("Plugin ID,Name,Risk,Description,Solution,See Also\n")
        temp_file.write("12345,Test Vulnerability,High,This is a test vulnerability description,Patch the system,https://example.com\n")
        temp_file.write("67890,Another Vulnerability,Medium,Another description,Update firmware,https://example.com/update\n")
        file_path = temp_file.name

    yield file_path
    
    # Clean up
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def file_path():
    """
    Fixture that creates a simple temporary text file for testing file processing.
    
    The file will be automatically removed after the test.
    """
    with tempfile.NamedTemporaryFile(mode="w", suffix=".txt", delete=False) as temp_file:
        temp_file.write("This is a test file content.\n")
        temp_file.write("It has multiple lines.\n")
        temp_file.write("Used for testing file processing functions.\n")
        file_path = temp_file.name

    yield file_path
    
    # Clean up
    if os.path.exists(file_path):
        os.remove(file_path) 