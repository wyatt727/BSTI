import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock

from bsti_nessus.utils.config_wizard import ConfigWizard
from bsti_nessus.utils.logger import CustomLogger


@pytest.fixture
def temp_config_file():
    """Fixture that creates a temporary configuration file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        temp_file.write(b'{}')  # Empty JSON object
        file_path = temp_file.name
    
    yield file_path
    
    # Clean up
    if os.path.exists(file_path):
        os.remove(file_path)


@pytest.fixture
def mock_input():
    """Fixture that mocks the input function to simulate user responses."""
    with patch('builtins.input') as mock_input:
        # Configure the mock to return different values for different prompts
        mock_input.side_effect = [
            # Plextrac instance configuration
            'y',  # Yes to configure Plextrac instances
            'dev',  # Instance name
            'https://dev.plextrac.com',  # Instance URL
            'y',  # Yes to verify SSL
            'n',  # No to configure another instance
            
            # Nessus parser configuration
            'y',  # Yes to configure Nessus parser
            'Plugin ID,Name,Risk,Description,Solution,See Also',  # CSV format
            'y',  # Yes to configure plugin categorization
            'network',  # Category name
            'Network Vulnerabilities',  # Display name
            'Vulnerabilities related to network configurations',  # Description
            '10180,10287,10386',  # Plugin IDs
            'n',  # No to add another category
            
            # Output configuration
            'y',  # Yes to configure output settings
            'plextrac_output',  # Output directory
            'screenshots',  # Screenshot directory
            
            # General settings
            'y',  # Yes to configure general settings
            '10',  # Default timeout
            '4',  # Default thread count
            'info',  # Default log level
        ]
        yield mock_input


@pytest.mark.integration
def test_config_wizard_full_workflow(temp_config_file, mock_input):
    """Test the full configuration wizard workflow."""
    # Create a mock logger
    mock_logger = MagicMock(spec=CustomLogger)
    
    # Initialize the ConfigWizard with our test config file and logger
    wizard = ConfigWizard(temp_config_file, mock_logger)
    
    # Run the wizard
    with patch('os.path.exists', return_value=True):  # Make directory checks pass
        with patch('os.makedirs'):  # Mock directory creation
            # Mock sys.stdin.readline to avoid OSError during tests
            with patch('sys.stdin.readline', side_effect=mock_input.side_effect):
                config = wizard.run_wizard()
    
    # Verify the generated configuration
    assert 'plextrac' in config
    assert 'instances' in config['plextrac']
    assert 'dev' in config['plextrac']['instances']
    assert config['plextrac']['instances']['dev']['url'] == 'https://dev.plextrac.com'
    assert config['plextrac']['instances']['dev']['verify_ssl'] == True
    
    assert 'nessus' in config
    assert 'csv_format' in config['nessus']
    assert 'categories' in config['nessus']
    assert 'network' in config['nessus']['categories']
    
    assert 'output' in config
    assert config['output']['directory'] == 'plextrac_output'
    assert config['output']['screenshots'] == 'screenshots'
    
    assert 'general' in config
    assert config['general']['timeout'] == 10
    assert config['general']['threads'] == 4
    assert config['general']['log_level'] == 'info'
    
    # Verify the configuration was saved
    mock_logger.info.assert_any_call("Configuration saved successfully")


@pytest.mark.integration
def test_config_wizard_validation():
    """Test configuration wizard validation functionality."""
    # Create a mock logger
    mock_logger = MagicMock(spec=CustomLogger)
    
    # Use a non-existent file path
    with tempfile.NamedTemporaryFile(suffix='.json') as temp_file:
        file_path = temp_file.name
    
    # Initialize the ConfigWizard with our non-existent config file
    wizard = ConfigWizard(file_path, mock_logger)
    
    # Test validation methods
    assert wizard.validate_url("https://valid-url.com") is True
    assert wizard.validate_url("not-a-valid-url") is False
    
    assert wizard.validate_integer("10") == 10
    assert wizard.validate_integer("-5") is None
    assert wizard.validate_integer("not-a-number") is None
    
    assert wizard.validate_log_level("debug") == "debug"
    assert wizard.validate_log_level("warning") == "warning"
    assert wizard.validate_log_level("invalid") is None


@pytest.mark.integration
def test_config_wizard_template_config():
    """Test the configuration wizard template functionality."""
    # Create a mock logger
    mock_logger = MagicMock(spec=CustomLogger)
    
    # Create a temporary config file
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as temp_file:
        temp_file.write(b'{}')  # Empty JSON object
        file_path = temp_file.name
    
    try:
        # Initialize the ConfigWizard
        wizard = ConfigWizard(file_path, mock_logger)
        
        # Use a predefined template for testing
        with patch.object(wizard, 'ask_template_choice', return_value='default'):
            with patch.object(wizard, 'load_template', return_value={
                'plextrac': {
                    'instances': {
                        'default': {
                            'url': 'https://default.plextrac.com',
                            'verify_ssl': True
                        }
                    }
                },
                'nessus': {
                    'csv_format': {
                        'required_fields': ['Plugin ID', 'Name', 'Risk', 'Description']
                    }
                }
            }):
                # Mock sys.stdin.readline to avoid OSError during tests
                with patch('sys.stdin.readline', return_value='y'):
                    # Run the wizard in template mode
                    with patch('builtins.input', return_value='y'):  # Confirm template usage
                        config = wizard.apply_template('default')
        
        # Verify the template was applied correctly
        assert 'plextrac' in config
        assert 'instances' in config['plextrac']
        assert 'default' in config['plextrac']['instances']
        assert config['plextrac']['instances']['default']['url'] == 'https://default.plextrac.com'
        
        assert 'nessus' in config
        assert 'csv_format' in config['nessus']
        assert 'required_fields' in config['nessus']['csv_format']
        
    finally:
        # Clean up
        if os.path.exists(file_path):
            os.remove(file_path) 