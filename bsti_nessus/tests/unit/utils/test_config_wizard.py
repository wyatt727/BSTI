"""
Unit tests for the configuration wizard module
"""
import os
import json
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from bsti_nessus.utils.config_wizard import ConfigWizard


@pytest.fixture
def temp_config_file():
    """Create a temporary config file for testing"""
    with tempfile.NamedTemporaryFile(delete=False, suffix='.json') as temp_file:
        # Write empty JSON object to the file
        temp_file.write(b'{}')
        temp_file_path = temp_file.name
    
    yield temp_file_path
    
    # Cleanup after test
    if os.path.exists(temp_file_path):
        os.remove(temp_file_path)


@pytest.fixture
def wizard(temp_config_file):
    """Create a ConfigWizard instance for testing"""
    mock_logger = MagicMock()
    return ConfigWizard(temp_config_file, logger=mock_logger)


def test_init_with_existing_config(temp_config_file):
    """Test initialization with an existing config file"""
    # Create a sample config file
    sample_config = {
        "plextrac": {
            "instances": {
                "test": {
                    "url": "https://test.plextrac.com",
                    "verify_ssl": True
                }
            }
        },
        "nessus": {
            "csv_format": {
                "required_fields": ["Test Field"]
            }
        }
    }
    
    with open(temp_config_file, 'w') as f:
        json.dump(sample_config, f)
    
    mock_logger = MagicMock()
    wizard = ConfigWizard(temp_config_file, logger=mock_logger)
    
    # Check that the config was loaded
    assert wizard.config == sample_config
    mock_logger.info.assert_called_once()


def test_init_with_invalid_config(temp_config_file):
    """Test initialization with an invalid config file"""
    # Write invalid JSON to the file
    with open(temp_config_file, 'w') as f:
        f.write("This is not valid JSON")
    
    mock_logger = MagicMock()
    wizard = ConfigWizard(temp_config_file, logger=mock_logger)
    
    # Check that the config is empty and an error was logged
    assert wizard.config == {}
    mock_logger.error.assert_called_once()


@patch('sys.stdout')
@patch('sys.stdin')
def test_get_input(mock_stdin, mock_stdout, wizard):
    """Test the _get_input method"""
    # Test with no default value
    mock_stdin.readline.return_value = "test input\n"
    result = wizard._get_input("Test prompt")
    assert result == "test input"
    mock_stdout.write.assert_called_with("Test prompt: ")
    
    # Test with default value
    mock_stdin.readline.return_value = "\n"  # User just presses Enter
    result = wizard._get_input("Test prompt", default="default value")
    assert result == "default value"
    mock_stdout.write.assert_called_with("Test prompt [default value]: ")
    
    # Test with validation
    mock_stdin.readline.side_effect = ["invalid", "valid\n"]
    validator = lambda x: x == "valid"
    result = wizard._get_input("Test prompt", validator=validator)
    assert result == "valid"
    assert mock_stdin.readline.call_count == 2


@patch('sys.stdout')
@patch('sys.stdin')
def test_get_boolean_input(mock_stdin, mock_stdout, wizard):
    """Test the _get_boolean_input method"""
    # Test with yes input
    mock_stdin.readline.return_value = "y\n"
    result = wizard._get_boolean_input("Test prompt")
    assert result is True
    
    # Test with no input
    mock_stdin.readline.return_value = "n\n"
    result = wizard._get_boolean_input("Test prompt")
    assert result is False
    
    # Test with invalid then valid input
    mock_stdin.readline.side_effect = ["invalid\n", "yes\n"]
    result = wizard._get_boolean_input("Test prompt")
    assert result is True
    
    # Test with default and empty input
    mock_stdin.readline.return_value = "\n"
    result = wizard._get_boolean_input("Test prompt", default=True)
    assert result is True


def test_validate_url(wizard):
    """Test the URL validator"""
    assert wizard._validate_url("https://example.com") is True
    assert wizard._validate_url("http://example.com") is True
    assert wizard._validate_url("example.com") is False
    assert wizard._validate_url("ftp://example.com") is False


@patch.object(ConfigWizard, '_get_boolean_input')
@patch.object(ConfigWizard, '_get_input')
def test_configure_plextrac_instances(mock_get_input, mock_get_boolean, wizard):
    """Test the Plextrac instance configuration"""
    # Mock user inputs
    mock_get_boolean.side_effect = [True, False]  # Add instance, don't add another
    mock_get_input.side_effect = ["prod", "https://prod.plextrac.com"]
    
    # Run the method
    instances = wizard._configure_plextrac_instances()
    
    # Check the result
    assert "prod" in instances
    assert instances["prod"]["url"] == "https://prod.plextrac.com"
    assert instances["prod"]["verify_ssl"] is True  # Default is True
    
    # Test with existing instances
    wizard.config = {
        "plextrac": {
            "instances": {
                "existing": {
                    "url": "https://existing.plextrac.com",
                    "verify_ssl": False
                }
            }
        }
    }
    
    # Mock user inputs - keep existing, add new
    mock_get_boolean.side_effect = [True, True, False]  # Keep existing, add new, don't add another
    mock_get_input.side_effect = ["new", "https://new.plextrac.com"]
    
    # Run the method again
    instances = wizard._configure_plextrac_instances()
    
    # Check the result includes both instances
    assert len(instances) == 2
    assert "existing" in instances
    assert "new" in instances


@patch.object(ConfigWizard, '_get_boolean_input')
@patch.object(ConfigWizard, '_get_input')
def test_configure_nessus_settings(mock_get_input, mock_get_boolean, wizard):
    """Test the Nessus settings configuration"""
    # Test with default settings (no customization)
    mock_get_boolean.return_value = False
    
    settings = wizard._configure_nessus_settings()
    assert "csv_format" in settings
    assert "required_fields" in settings["csv_format"]
    assert "Plugin ID" in settings["csv_format"]["required_fields"]
    
    # Test with customization
    mock_get_boolean.return_value = True
    mock_get_input.side_effect = [
        "Field1, Field2, Field3",  # Required fields
        "OptField1, OptField2"     # Optional fields
    ]
    
    settings = wizard._configure_nessus_settings()
    assert settings["csv_format"]["required_fields"] == ["Field1", "Field2", "Field3"]
    assert settings["csv_format"]["optional_fields"] == ["OptField1", "OptField2"]


@patch.object(ConfigWizard, '_configure_plextrac_instances')
@patch.object(ConfigWizard, '_configure_nessus_settings')
@patch.object(ConfigWizard, '_configure_general_settings')
@patch.object(ConfigWizard, '_test_configuration')
@patch.object(ConfigWizard, '_get_boolean_input')
def test_run_wizard(
    mock_get_boolean, mock_test_config, mock_gen_settings, 
    mock_nessus_settings, mock_plextrac_instances, wizard, temp_config_file
):
    """Test the main wizard workflow"""
    # Setup mocks
    mock_plextrac_instances.return_value = {
        "test": {"url": "https://test.plextrac.com", "verify_ssl": True}
    }
    mock_nessus_settings.return_value = {
        "csv_format": {
            "required_fields": ["Field1", "Field2"],
            "optional_fields": ["OptField1"]
        }
    }
    mock_gen_settings.return_value = {
        "tmp_dir": "/tmp/test",
        "cleanup_tmp": True
    }
    mock_test_config.return_value = (True, "Configuration looks valid")
    mock_get_boolean.return_value = True  # Save config
    
    # Run the wizard
    config = wizard.run_wizard()
    
    # Check the result
    assert "plextrac" in config
    assert "nessus" in config
    assert "general" in config
    
    # Verify the config was saved to disk
    with open(temp_config_file, 'r') as f:
        saved_config = json.load(f)
    
    assert saved_config == config
    
    # Test with failed validation
    mock_test_config.return_value = (False, "Configuration invalid")
    mock_get_boolean.side_effect = [False, True]  # Don't continue, save config
    
    config = wizard.run_wizard()
    assert config == wizard.config  # Should return current config without changes


@patch('bsti_nessus.utils.config_wizard.Logger')
@patch('argparse.ArgumentParser.parse_args')
@patch.object(ConfigWizard, 'run_wizard')
def test_main(mock_run_wizard, mock_parse_args, mock_logger):
    """Test the main function"""
    # Setup mocks
    mock_args = MagicMock()
    mock_args.config = "test_config.json"
    mock_args.verbose = True
    mock_parse_args.return_value = mock_args
    
    # Call main
    from bsti_nessus.utils.config_wizard import main
    result = main()
    
    # Check result
    assert result == 0
    mock_run_wizard.assert_called_once()
    mock_logger.assert_called_with("config_wizard", level="DEBUG") 