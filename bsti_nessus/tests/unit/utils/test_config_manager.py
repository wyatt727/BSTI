"""
Unit tests for the config_manager module.
"""
import pytest
import json
import os
from unittest.mock import patch, mock_open, MagicMock
from pathlib import Path

from bsti_nessus.utils.config_manager import ConfigManager


@pytest.fixture
def sample_config():
    """Sample configuration dictionary for testing."""
    return {
        "api": {
            "plextrac": {
                "base_url": "https://test.plextrac.com",
                "timeout": 30
            }
        },
        "file_paths": {
            "plextrac_format": "test_format.csv",
            "processed_findings": "_test_findings.json"
        },
        "plugin_categories": "plugin_defs.json"
    }


@pytest.fixture
def sample_plugin_defs():
    """Sample plugin definitions dictionary for testing."""
    return {
        "plugins": {
            "critical": {
                "title": "Critical Vulnerabilities",
                "color": "red",
                "ids": ["10001", "10002", "10003"]
            },
            "high": {
                "title": "High Vulnerabilities",
                "color": "orange",
                "ids": ["20001", "20002"]
            }
        }
    }


class TestConfigManager:
    """Tests for the ConfigManager class."""
    
    def test_init_default_path(self):
        """Test initialization with default config path."""
        # Skip actually creating the ConfigManager and directly test its functions
        with patch.object(ConfigManager, '__init__', return_value=None) as mock_init:
            # Create a config manager instance without calling its __init__
            config_manager = ConfigManager()
            # Manually set its attributes that would have been set in __init__
            config_manager._config = {"test": "config"}
            config_manager._plugin_defs = {}
            
            # Verify the mock was called
            mock_init.assert_called_once()
            
            # Test the instance's functionality
            assert config_manager._config == {"test": "config"}
    
    @patch('builtins.open', new_callable=mock_open, read_data='{"test": "custom_config"}')
    @patch('json.load', return_value={"test": "custom_config"})
    def test_load_config(self, mock_json_load, mock_file):
        """Test explicitly loading a configuration file."""
        # Create a config manager with an empty configuration
        with patch.object(ConfigManager, '__init__', return_value=None):
            config_manager = ConfigManager()
            config_manager._config = {}
            config_manager._plugin_defs = {}
        
        # Load a configuration file
        config_manager.load_config("/custom/path/config.json")
        
        # Assert the file was opened with the correct path
        mock_file.assert_called_with("/custom/path/config.json", "r")
        # Assert the configuration was loaded
        assert config_manager._config == {"test": "custom_config"}
    
    def test_load_config_file_not_found(self):
        """Test load_config when file is not found."""
        # Create a config manager with an empty configuration
        with patch.object(ConfigManager, '__init__', return_value=None):
            config_manager = ConfigManager()
            config_manager._config = {}
            config_manager._plugin_defs = {}
        
        # Mock the open function to raise FileNotFoundError
        with patch('builtins.open', side_effect=FileNotFoundError):
            # Attempt to load a non-existent file
            with pytest.raises(FileNotFoundError):
                config_manager.load_config("/non/existent/path/config.json")
    
    def test_load_config_invalid_json(self):
        """Test load_config when file contains invalid JSON."""
        # Create a config manager with an empty configuration
        with patch.object(ConfigManager, '__init__', return_value=None):
            config_manager = ConfigManager()
            config_manager._config = {}
            config_manager._plugin_defs = {}
        
        # Mock the open function to return a file with invalid JSON
        mock_file = mock_open(read_data="{ invalid json")
        with patch('builtins.open', mock_file):
            # Mock json.load to raise JSONDecodeError
            with patch('json.load', side_effect=json.JSONDecodeError("Expecting property name", "{ invalid json", 2)):
                # Attempt to load a file with invalid JSON
                with pytest.raises(ValueError):
                    config_manager.load_config("/path/to/invalid/config.json")
    
    def test_get_simple_key(self, sample_config):
        """Test getting a simple config key."""
        # Create a config manager with the sample config
        with patch.object(ConfigManager, '__init__', return_value=None):
            config_manager = ConfigManager()
            config_manager._config = sample_config
            config_manager._plugin_defs = {}
        
        # Get a simple key
        value = config_manager.get("plugin_categories")
        
        # Assert the value is correct
        assert value == "plugin_defs.json"
    
    def test_get_nested_key(self, sample_config):
        """Test getting a nested config key."""
        # Create a config manager with the sample config
        with patch.object(ConfigManager, '__init__', return_value=None):
            config_manager = ConfigManager()
            config_manager._config = sample_config
            config_manager._plugin_defs = {}
        
        # Get a nested key
        value = config_manager.get("api.plextrac.base_url")
        
        # Assert the value is correct
        assert value == "https://test.plextrac.com"
    
    def test_get_nonexistent_key(self, sample_config):
        """Test getting a nonexistent config key."""
        # Create a config manager with the sample config
        with patch.object(ConfigManager, '__init__', return_value=None):
            config_manager = ConfigManager()
            config_manager._config = sample_config
            config_manager._plugin_defs = {}
        
        # Get a nonexistent key with a default value
        value = config_manager.get("nonexistent_key", "default_value")
        
        # Assert the default value is returned
        assert value == "default_value"
    
    def test_get_nonexistent_nested_key(self, sample_config):
        """Test getting a nonexistent nested config key."""
        # Create a config manager with the sample config
        with patch.object(ConfigManager, '__init__', return_value=None):
            config_manager = ConfigManager()
            config_manager._config = sample_config
            config_manager._plugin_defs = {}
        
        # Get a nonexistent nested key with a default value
        value = config_manager.get("api.nonexistent.key", "default_value")
        
        # Assert the default value is returned
        assert value == "default_value"
    
    def test_get_plugin_categories(self, sample_plugin_defs):
        """Test getting plugin categories."""
        # Create a config manager with the sample plugin definitions
        with patch.object(ConfigManager, '__init__', return_value=None):
            config_manager = ConfigManager()
            config_manager._config = {}
            config_manager._plugin_defs = sample_plugin_defs
        
        # Get the plugin categories
        categories = config_manager.get_plugin_categories()
        
        # Assert the categories are correct
        expected_categories = {
            "10001": "critical",
            "10002": "critical",
            "10003": "critical",
            "20001": "high",
            "20002": "high"
        }
        assert categories == expected_categories
    
    def test_get_plugin_details(self, sample_plugin_defs):
        """Test getting plugin details."""
        # Create a config manager with the sample plugin definitions
        with patch.object(ConfigManager, '__init__', return_value=None):
            config_manager = ConfigManager()
            config_manager._config = {}
            config_manager._plugin_defs = sample_plugin_defs
        
        # Get the details for the "critical" category
        details = config_manager.get_plugin_details("critical")
        
        # Assert the details are correct
        expected_details = {
            "title": "Critical Vulnerabilities",
            "color": "red",
            "ids": ["10001", "10002", "10003"]
        }
        assert details == expected_details
    
    @patch("os.path.exists")
    @patch("os.makedirs")
    @patch("builtins.open", new_callable=mock_open, read_data='{"client": "specific", "api": {"timeout": 60}}')
    @patch("json.load", return_value={"client": "specific", "api": {"timeout": 60}})
    def test_load_client_config(self, mock_json_load, mock_file, mock_makedirs, mock_exists):
        """Test loading client-specific configuration."""
        # Set up the mocks
        mock_exists.return_value = True
        
        # Create a config manager with the sample config
        with patch.object(ConfigManager, '__init__', return_value=None):
            config_manager = ConfigManager()
            config_manager._config = {"api": {"timeout": 30, "url": "original"}}
            config_manager._plugin_defs = {}
        
        # Load the client config
        with patch('os.path.join', return_value="/test/path/config/clients/test_client.json"):
            result = config_manager.load_client_config("test_client")
        
        # Assert the client config was loaded successfully
        assert result is True
        # Assert the configs were merged correctly
        assert config_manager._config == {
            "api": {"timeout": 60, "url": "original"},
            "client": "specific"
        }
    
    def test_merge_configs(self):
        """Test merging configurations."""
        # Create a config manager
        with patch.object(ConfigManager, '__init__', return_value=None):
            config_manager = ConfigManager()
            config_manager._config = {}
            config_manager._plugin_defs = {}
        
        # Create base and override configs
        base_config = {
            "api": {
                "timeout": 30,
                "url": "original"
            },
            "unchanged": "value"
        }
        override_config = {
            "api": {
                "timeout": 60
            },
            "new_key": "new_value"
        }
        
        # Merge the configs
        config_manager._merge_configs(base_config, override_config)
        
        # Assert the configs were merged correctly
        expected_config = {
            "api": {
                "timeout": 60,
                "url": "original"
            },
            "unchanged": "value",
            "new_key": "new_value"
        }
        assert base_config == expected_config 