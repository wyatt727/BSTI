"""
Configuration Wizard for BSTI Nessus to Plextrac Converter

This module provides an interactive wizard to help users create and validate
their configuration for the BSTI Nessus to Plextrac Converter.
"""
import os
import json
import getpass
import sys
from typing import Dict, Any, List, Optional, Tuple

from bsti_nessus.utils.logger import Logger


class ConfigWizard:
    """Interactive configuration wizard for setting up the BSTI Nessus to Plextrac Converter"""

    def __init__(self, config_path: str, logger: Optional[Logger] = None):
        """
        Initialize the configuration wizard
        
        Args:
            config_path: Path to the configuration file to create or update
            logger: Optional logger instance
        """
        self.config_path = config_path
        self.logger = logger or Logger("config_wizard")
        self.config = {}
        
        # Load existing configuration if available
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r') as f:
                    self.config = json.load(f)
                self.logger.info(f"Loaded existing configuration from {config_path}")
            except (json.JSONDecodeError, IOError) as e:
                self.logger.error(f"Failed to load existing configuration: {str(e)}")
                self.config = {}
    
    def _get_input(self, prompt: str, default: str = None, 
                   validator=None, password: bool = False) -> str:
        """
        Get user input with optional validation and default value
        
        Args:
            prompt: The prompt to display to the user
            default: Optional default value
            validator: Optional function to validate input
            password: Whether to hide input (for passwords)
            
        Returns:
            The validated user input
        """
        while True:
            display_prompt = f"{prompt} [{default}]: " if default else f"{prompt}: "
            
            if password:
                value = getpass.getpass(display_prompt)
            else:
                sys.stdout.write(display_prompt)
                sys.stdout.flush()
                value = sys.stdin.readline().strip()
            
            if not value and default:
                value = default
                
            if not value:
                self.logger.warning("Value cannot be empty")
                continue
                
            if validator and not validator(value):
                continue
                
            return value
    
    def _get_boolean_input(self, prompt: str, default: bool = None) -> bool:
        """
        Get boolean input from user
        
        Args:
            prompt: The prompt to display to the user
            default: Optional default value
            
        Returns:
            Boolean value from user input
        """
        default_str = "y" if default else "n" if default is not None else None
        while True:
            display_prompt = f"{prompt} (y/n) [{default_str}]: " if default_str else f"{prompt} (y/n): "
            sys.stdout.write(display_prompt)
            sys.stdout.flush()
            value = sys.stdin.readline().strip().lower()
            
            if not value and default_str:
                return default
                
            if value in ("y", "yes", "true", "1"):
                return True
            elif value in ("n", "no", "false", "0"):
                return False
            else:
                self.logger.warning("Please enter 'y' or 'n'")
    
    def _validate_url(self, url: str) -> bool:
        """
        Validate URL format
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        if not url.startswith(("http://", "https://")):
            self.logger.warning("URL must start with http:// or https://")
            return False
        return True
    
    def _configure_plextrac_instances(self) -> Dict[str, Dict[str, Any]]:
        """
        Configure Plextrac instances
        
        Returns:
            Dictionary of configured Plextrac instances
        """
        instances = {}
        existing_instances = self.config.get("plextrac", {}).get("instances", {})
        
        if existing_instances:
            self.logger.info(f"Found {len(existing_instances)} existing Plextrac instance(s)")
            for name, config in existing_instances.items():
                keep = self._get_boolean_input(f"Keep instance '{name}' ({config.get('url')})?", True)
                if keep:
                    instances[name] = config
        
        add_more = self._get_boolean_input("Add a new Plextrac instance?", 
                                           not bool(instances))
        
        while add_more:
            name = self._get_input("Instance name (e.g., 'dev', 'prod')")
            
            if name in instances:
                self.logger.warning(f"Instance '{name}' already exists")
                continue
            
            url = self._get_input("Instance URL (e.g., https://your-instance.plextrac.com)", 
                                  validator=self._validate_url)
            
            verify_ssl = self._get_boolean_input("Verify SSL certificates?", True)
            
            instances[name] = {
                "url": url,
                "verify_ssl": verify_ssl
            }
            
            add_more = self._get_boolean_input("Add another Plextrac instance?", False)
        
        return instances
    
    def _configure_nessus_settings(self) -> Dict[str, Any]:
        """
        Configure Nessus parser settings
        
        Returns:
            Dictionary of Nessus settings
        """
        existing_settings = self.config.get("nessus", {})
        
        settings = {
            "csv_format": {
                "required_fields": existing_settings.get("csv_format", {}).get(
                    "required_fields", 
                    ["Plugin ID", "Name", "Risk", "Description"]
                ),
                "optional_fields": existing_settings.get("csv_format", {}).get(
                    "optional_fields", 
                    ["Solution", "See Also"]
                )
            }
        }
        
        customize = self._get_boolean_input("Customize Nessus CSV field settings?", False)
        if customize:
            # Required fields
            self.logger.info("Configure required fields (comma-separated list)")
            required_str = self._get_input(
                "Required fields", 
                default=", ".join(settings["csv_format"]["required_fields"])
            )
            settings["csv_format"]["required_fields"] = [
                field.strip() for field in required_str.split(",") if field.strip()
            ]
            
            # Optional fields
            self.logger.info("Configure optional fields (comma-separated list)")
            optional_str = self._get_input(
                "Optional fields", 
                default=", ".join(settings["csv_format"]["optional_fields"])
            )
            settings["csv_format"]["optional_fields"] = [
                field.strip() for field in optional_str.split(",") if field.strip()
            ]
        
        return settings
    
    def _configure_general_settings(self) -> Dict[str, Any]:
        """
        Configure general application settings
        
        Returns:
            Dictionary of general settings
        """
        existing_settings = self.config.get("general", {})
        
        settings = {
            "tmp_dir": existing_settings.get("tmp_dir", "/tmp/bsti_nessus"),
            "cleanup_tmp": existing_settings.get("cleanup_tmp", True),
            "log_level": existing_settings.get("log_level", "INFO")
        }
        
        customize = self._get_boolean_input("Customize general settings?", False)
        if customize:
            settings["tmp_dir"] = self._get_input(
                "Temporary directory path", 
                default=settings["tmp_dir"]
            )
            
            settings["cleanup_tmp"] = self._get_boolean_input(
                "Clean up temporary files after processing?", 
                default=settings["cleanup_tmp"]
            )
            
            log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
            while True:
                log_level = self._get_input(
                    f"Log level ({', '.join(log_levels)})", 
                    default=settings["log_level"]
                ).upper()
                
                if log_level in log_levels:
                    settings["log_level"] = log_level
                    break
                else:
                    self.logger.warning(f"Invalid log level. Choose from: {', '.join(log_levels)}")
        
        return settings
    
    def _test_configuration(self) -> Tuple[bool, str]:
        """
        Test the current configuration
        
        Returns:
            Tuple of (success, message)
        """
        # Validate plextrac instances
        if not self.config.get("plextrac", {}).get("instances"):
            return False, "No Plextrac instances configured"
        
        # Validate nessus settings
        nessus_settings = self.config.get("nessus", {}).get("csv_format", {})
        if not nessus_settings.get("required_fields"):
            return False, "No required Nessus CSV fields configured"
        
        # TODO: Implement actual API connection test if desired
        
        return True, "Configuration looks valid"
    
    def run_wizard(self) -> Dict[str, Any]:
        """
        Run the configuration wizard
        
        Returns:
            The final configuration dictionary
        """
        self.logger.info("Starting BSTI Nessus to Plextrac Converter Configuration Wizard")
        
        # Configure Plextrac instances
        self.logger.info("Step 1: Configure Plextrac Instances")
        instances = self._configure_plextrac_instances()
        if not instances:
            self.logger.error("At least one Plextrac instance is required")
            return self.config
        
        self.config["plextrac"] = {
            "instances": instances
        }
        
        # Configure Nessus settings
        self.logger.info("Step 2: Configure Nessus Parser Settings")
        self.config["nessus"] = self._configure_nessus_settings()
        
        # Configure general settings
        self.logger.info("Step 3: Configure General Settings")
        self.config["general"] = self._configure_general_settings()
        
        # Test configuration
        self.logger.info("Testing configuration...")
        success, message = self._test_configuration()
        if success:
            self.logger.info(f"Configuration test passed: {message}")
        else:
            self.logger.warning(f"Configuration test failed: {message}")
            if not self._get_boolean_input("Continue anyway?", False):
                return self.config
        
        # Save configuration
        save = self._get_boolean_input("Save configuration?", True)
        if save:
            try:
                os.makedirs(os.path.dirname(os.path.abspath(self.config_path)), exist_ok=True)
                with open(self.config_path, 'w') as f:
                    json.dump(self.config, f, indent=4)
                self.logger.info(f"Configuration saved to {self.config_path}")
            except IOError as e:
                self.logger.error(f"Failed to save configuration: {str(e)}")
        
        return self.config


def main():
    """Entry point when running the wizard directly"""
    import argparse
    
    parser = argparse.ArgumentParser(description="BSTI Nessus to Plextrac Converter Configuration Wizard")
    parser.add_argument("--config", "-c", default="config/config.json", 
                        help="Path to configuration file")
    parser.add_argument("--verbose", "-v", action="store_true", 
                        help="Enable verbose logging")
    
    args = parser.parse_args()
    
    logger = Logger("config_wizard", level="DEBUG" if args.verbose else "INFO")
    wizard = ConfigWizard(args.config, logger)
    config = wizard.run_wizard()
    
    return 0


if __name__ == "__main__":
    sys.exit(main()) 