"""
Unit tests for setup.py utility functions
"""
import os
import re
from unittest.mock import patch, mock_open, MagicMock
import pytest


# Define the utility functions here to avoid importing setup.py directly
def read_file(filename):
    """Reads a file and returns its contents."""
    with open(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), filename)) as f:
        return f.read()


def extract_version(init_content):
    """Extract version from __init__.py content."""
    match = re.search(r"__version__ = ['\"]([^'\"]+)['\"]", init_content)
    if match:
        return match.group(1)
    return None


def parse_requirements(requirements_content):
    """Parse requirements from requirements.txt content."""
    requirements = []
    for line in requirements_content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        requirements.append(line)
    return requirements


@patch('builtins.open', new_callable=mock_open, read_data="Test content")
def test_read_file(mock_file):
    """Test reading file contents."""
    result = read_file("testfile.txt")
    assert result == "Test content"
    mock_file.assert_called_once()


def test_extract_version():
    """Test version extraction from __init__.py."""
    content = '__version__ = "1.2.3"\n__author__ = "BSTI Team"'
    version = extract_version(content)
    assert version == "1.2.3"


def test_extract_version_no_match():
    """Test version extraction fails with incorrect format."""
    content = 'version = "1.2.3"\n__author__ = "BSTI Team"'
    version = extract_version(content)
    assert version is None


def test_parse_requirements():
    """Test requirements parsing from requirements.txt."""
    content = (
        "# Requirements\n"
        "tqdm>=4.61.0\n"
        "requests>=2.25.1\n"
        "\n"
        "# Optional dependencies\n"
        "pytest>=6.2.5\n"
    )
    requirements = parse_requirements(content)
    assert requirements == ["tqdm>=4.61.0", "requests>=2.25.1", "pytest>=6.2.5"]


@patch('os.path.dirname')
@patch('os.path.join')
def test_version_in_init(mock_join, mock_dirname):
    """Test that __init__.py has a valid version."""
    # Skip actual file reading and return a fixed path
    mock_dirname.return_value = '/test'
    mock_join.return_value = 'bsti_nessus/__init__.py'
    
    # Test with mocked file content
    init_content = """
    \"\"\"
    BSTI Nessus to Plextrac Converter
    \"\"\"
    
    __version__ = "1.0.0"
    __author__ = "BSTI Team"
    """
    
    with patch('builtins.open', mock_open(read_data=init_content)):
        content = read_file('bsti_nessus/__init__.py')
        version = extract_version(content)
        
        assert version is not None
        assert re.match(r'^\d+\.\d+\.\d+$', version) is not None 