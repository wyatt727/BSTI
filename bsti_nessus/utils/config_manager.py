"""
Configuration manager for the BSTI Nessus to Plextrac converter.
"""
import json
import os
from typing import Any, Dict, Optional
from pathlib import Path

class ConfigManager:
    """
    Configuration manager that loads and provides access to configuration settings.
    """
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_path (str, optional): Path to the main configuration file.
                If not provided, will look for config.json in the config directory.
        """
        self._config: Dict[str, Any] = {}
        self._plugin_defs: Dict[str, Any] = {}
        
        if not config_path:
            # Get the directory where this module is located
            module_dir = Path(__file__).parent.parent
            config_path = os.path.join(module_dir, 'config', 'config.json')
        
        self.load_config(config_path)
        
        # Load plugin definitions
        plugin_defs_path = self.get('plugin_categories')
        if plugin_defs_path:
            # Check if it's an absolute path or relative
            if not os.path.isabs(plugin_defs_path):
                # If relative, join with the config directory
                plugin_defs_path = os.path.join(os.path.dirname(config_path), plugin_defs_path)
            
            self.load_plugin_definitions(plugin_defs_path)
    
    def load_config(self, config_path: str):
        """
        Load configuration from a JSON file.
        
        Args:
            config_path (str): Path to the configuration file.
            
        Raises:
            FileNotFoundError: If the configuration file is not found.
            json.JSONDecodeError: If the configuration file is not valid JSON.
        """
        try:
            with open(config_path, 'r') as f:
                self._config = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        except json.JSONDecodeError:
            raise ValueError(f"Invalid JSON in configuration file: {config_path}")
    
    def load_plugin_definitions(self, plugin_defs_path: str):
        """
        Load plugin definitions from a JSON file.
        
        Args:
            plugin_defs_path (str): Path to the plugin definitions file.
            
        Raises:
            FileNotFoundError: If the plugin definitions file is not found.
            json.JSONDecodeError: If the plugin definitions file is not valid JSON.
        """
        try:
            with open(plugin_defs_path, 'r') as f:
                self._plugin_defs = json.load(f)
        except FileNotFoundError:
            # Not a critical error, just log a warning
            from .logger import log
            log.warning(f"Plugin definitions file not found: {plugin_defs_path}")
        except json.JSONDecodeError:
            from .logger import log
            log.error(f"Invalid JSON in plugin definitions file: {plugin_defs_path}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value.
        
        Args:
            key (str): The configuration key, can be nested using dot notation (e.g., 'api.plextrac.base_url').
            default (any, optional): Default value to return if the key is not found.
            
        Returns:
            The configuration value or the default if not found.
        """
        # Handle nested keys with dot notation
        if '.' in key:
            parts = key.split('.')
            current = self._config
            
            for part in parts:
                if isinstance(current, dict) and part in current:
                    current = current[part]
                else:
                    return default
            
            return current
        
        return self._config.get(key, default)
    
    def get_plugin_categories(self) -> Dict[str, str]:
        """
        Build a mapping of plugin categories from the configuration.
        
        Returns:
            Dictionary mapping plugin IDs to their respective categories.
        """
        categories = {}
        plugins = self._plugin_defs.get('plugins', {})
        
        for category, details in plugins.items():
            for plugin_id in details.get('ids', []):
                categories[plugin_id] = category
        
        return categories
    
    def get_plugin_details(self, category: str) -> Dict[str, Any]:
        """
        Get details for a plugin category.
        
        Args:
            category (str): The plugin category.
            
        Returns:
            A dictionary with the plugin category details or an empty dictionary if not found.
        """
        return self._plugin_defs.get('plugins', {}).get(category, {})

    def load_client_config(self, client_name: str) -> bool:
        """
        Load client-specific configuration.
        
        Args:
            client_name (str): Name of the client.
            
        Returns:
            bool: True if client config was loaded, False otherwise.
        """
        if not client_name:
            return False
        
        # Get the module directory
        module_dir = Path(__file__).parent.parent
        client_config_dir = os.path.join(module_dir, 'config', 'clients')
        
        # Check if client directory exists
        if not os.path.exists(client_config_dir):
            os.makedirs(client_config_dir, exist_ok=True)
            return False
        
        # Check if client config exists
        client_config_path = os.path.join(client_config_dir, f"{client_name.lower()}.json")
        if not os.path.exists(client_config_path):
            return False
        
        try:
            with open(client_config_path, 'r') as file:
                client_config = json.load(file)
                
            # Merge client config with current config (client config takes precedence)
            self._merge_configs(self._config, client_config)
            return True
        except Exception as e:
            print(f"Error loading client config: {str(e)}")
            return False

    def _merge_configs(self, base_config: Dict[str, Any], override_config: Dict[str, Any]):
        """
        Recursively merge two configurations.
        
        Args:
            base_config (dict): Base configuration to be updated.
            override_config (dict): Configuration with overrides.
        """
        for key, value in override_config.items():
            if isinstance(value, dict) and key in base_config and isinstance(base_config[key], dict):
                # If both values are dictionaries, merge them recursively
                self._merge_configs(base_config[key], value)
            else:
                # Otherwise override the value
                base_config[key] = value

    def get_client_specific_field(self, client_name: str, field_path: str, default=None) -> Any:
        """
        Get a client-specific field value.
        
        Args:
            client_name (str): Name of the client.
            field_path (str): Path to the field in dot notation.
            default: Default value to return if the field is not found.
            
        Returns:
            Any: The field value or default.
        """
        # First try to get from client-specific config
        if client_name:
            # Make a backup of the current config
            config_backup = self._config.copy()
            
            # Load client config
            client_loaded = self.load_client_config(client_name)
            
            if client_loaded:
                # Get the value
                result = self.get(field_path, default)
                
                # Restore original config
                self._config = config_backup
                
                return result
        
        # Fall back to regular config
        return self.get(field_path, default) 