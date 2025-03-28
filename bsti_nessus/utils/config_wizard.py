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
    
    def validate_url(self, url: str) -> bool:
        """
        Public wrapper for _validate_url
        
        Args:
            url: URL to validate
            
        Returns:
            True if URL is valid, False otherwise
        """
        return self._validate_url(url)
    
    def validate_integer(self, value: str) -> Optional[int]:
        """
        Validate and convert a string to an integer
        
        Args:
            value: String value to convert
            
        Returns:
            Integer value or None if invalid
        """
        try:
            int_value = int(value)
            if int_value >= 0:
                return int_value
            self.logger.warning("Value must be a positive integer")
            return None
        except ValueError:
            self.logger.warning("Value must be a valid integer")
            return None
            
    def validate_log_level(self, level: str) -> Optional[str]:
        """
        Validate log level
        
        Args:
            level: Log level to validate
            
        Returns:
            Valid log level or None if invalid
        """
        valid_levels = ["debug", "info", "warning", "error", "critical"]
        level = level.lower()
        if level in valid_levels:
            return level
        self.logger.warning(f"Log level must be one of: {', '.join(valid_levels)}")
        return None
    
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
            },
            "categories": existing_settings.get("categories", {})
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
        
        # Configure plugin categories
        configure_categories = self._get_boolean_input("Configure Nessus plugin categorization?", False)
        if configure_categories:
            self.logger.info("Plugin categories help organize findings by type")
            
            # Allow updating existing categories
            if settings["categories"]:
                self.logger.info(f"Found {len(settings['categories'])} existing categories")
                for category_id, category_info in list(settings["categories"].items()):
                    keep = self._get_boolean_input(
                        f"Keep category '{category_id}' ({category_info.get('display_name')})?", 
                        True
                    )
                    if not keep:
                        del settings["categories"][category_id]
            
            # Add new categories
            add_more = self._get_boolean_input("Add a new plugin category?", not bool(settings["categories"]))
            while add_more:
                category_id = self._get_input("Category ID (e.g., 'network', 'webapp')")
                
                if category_id in settings["categories"]:
                    self.logger.warning(f"Category '{category_id}' already exists")
                    continue
                
                display_name = self._get_input(f"Display name for '{category_id}'")
                description = self._get_input(f"Description for '{category_id}'", default="")
                
                plugin_ids_str = self._get_input(
                    f"Plugin IDs for '{category_id}' (comma-separated list)",
                    default=""
                )
                
                plugin_ids = []
                if plugin_ids_str:
                    try:
                        plugin_ids = [
                            int(pid.strip()) for pid in plugin_ids_str.split(",") 
                            if pid.strip().isdigit()
                        ]
                    except ValueError:
                        self.logger.warning("Invalid plugin ID format, should be integers")
                
                settings["categories"][category_id] = {
                    "display_name": display_name,
                    "description": description,
                    "plugin_ids": plugin_ids
                }
                
                add_more = self._get_boolean_input("Add another plugin category?", False)
        
        return settings
    
    def _configure_general_settings(self) -> Dict[str, Any]:
        """
        Configure general settings
        
        Returns:
            Dictionary of general settings
        """
        existing_settings = self.config.get("general", {})
        
        settings = {
            "timeout": existing_settings.get("timeout", 30),
            "threads": existing_settings.get("threads", 4),
            "log_level": existing_settings.get("log_level", "info")
        }
        
        customize = self._get_boolean_input("Customize general settings?", False)
        if customize:
            # Default timeout
            timeout = self._get_input(
                "Default timeout (seconds)",
                default=str(settings["timeout"]),
                validator=lambda x: self.validate_integer(x) is not None
            )
            settings["timeout"] = self.validate_integer(timeout)
            
            # Default thread count
            threads = self._get_input(
                "Default thread count",
                default=str(settings["threads"]),
                validator=lambda x: self.validate_integer(x) is not None
            )
            settings["threads"] = self.validate_integer(threads)
            
            # Default log level
            log_level = self._get_input(
                "Default log level (debug, info, warning, error, critical)",
                default=settings["log_level"],
                validator=lambda x: self.validate_log_level(x) is not None
            )
            settings["log_level"] = self.validate_log_level(log_level)
        
        return settings
    
    def ask_template_choice(self) -> str:
        """
        Ask the user to select a configuration template
        
        Returns:
            Name of the selected template
        """
        templates = self._get_available_templates()
        
        if not templates:
            self.logger.warning("No templates available")
            return None
        
        self.logger.info("Available templates:")
        for i, template in enumerate(templates, 1):
            self.logger.info(f"{i}. {template}")
        
        while True:
            choice = self._get_input("Select a template (number or name)")
            
            # Try to interpret as a number
            try:
                index = int(choice) - 1
                if 0 <= index < len(templates):
                    return templates[index]
            except ValueError:
                # Not a number, try as a name
                if choice in templates:
                    return choice
            
            self.logger.warning("Invalid template choice")

    def _get_available_templates(self) -> List[str]:
        """
        Get list of available configuration templates
        
        Returns:
            List of template names
        """
        # In a real implementation, this would scan a templates directory
        # For now, return a hardcoded list of available templates
        return ["default", "enterprise", "minimal"]

    def load_template(self, template_name: str) -> Dict[str, Any]:
        """
        Load a configuration template
        
        Args:
            template_name: Name of the template to load
            
        Returns:
            Template configuration dictionary
        """
        # In a real implementation, this would load from a file
        # For now, return hardcoded templates
        
        if template_name == "default":
            return {
                "plextrac": {
                    "instances": {
                        "default": {
                            "url": "https://default.plextrac.com",
                            "verify_ssl": True
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
                            "display_name": "Network Vulnerabilities",
                            "description": "Vulnerabilities related to network configurations and services",
                            "plugin_ids": [10180, 10287, 10386]
                        },
                        "webapp": {
                            "display_name": "Web Application Vulnerabilities",
                            "description": "Vulnerabilities found in web applications",
                            "plugin_ids": [11219, 12345, 67890]
                        }
                    }
                },
                "output": {
                    "directory": "plextrac_output",
                    "screenshots": "screenshots"
                },
                "general": {
                    "timeout": 30,
                    "threads": 4,
                    "log_level": "info"
                }
            }
        elif template_name == "enterprise":
            return {
                "plextrac": {
                    "instances": {
                        "prod": {
                            "url": "https://enterprise.plextrac.com",
                            "verify_ssl": True
                        },
                        "dev": {
                            "url": "https://dev.enterprise.plextrac.com",
                            "verify_ssl": True
                        }
                    }
                },
                "nessus": {
                    "csv_format": {
                        "required_fields": ["Plugin ID", "Name", "Risk", "Description", "Solution", "See Also"],
                        "optional_fields": ["CVSS Base Score", "CVSS Temporal Score", "References"]
                    },
                    "categories": {
                        "network": {
                            "display_name": "Network Infrastructure",
                            "description": "Network device and service vulnerabilities",
                            "plugin_ids": [10180, 10287, 10386, 15435, 18932]
                        },
                        "webapp": {
                            "display_name": "Web Applications",
                            "description": "Web application security issues",
                            "plugin_ids": [11219, 12345, 67890]
                        },
                        "database": {
                            "display_name": "Database Systems",
                            "description": "Database security configurations and vulnerabilities",
                            "plugin_ids": [20835, 23485, 26271]
                        },
                        "compliance": {
                            "display_name": "Compliance Issues",
                            "description": "Regulatory compliance violations",
                            "plugin_ids": [30562, 32764, 38456]
                        }
                    }
                },
                "output": {
                    "directory": "enterprise_output",
                    "screenshots": "enterprise_screenshots"
                },
                "general": {
                    "timeout": 60,
                    "threads": 8,
                    "log_level": "info"
                }
            }
        elif template_name == "minimal":
            return {
                "plextrac": {
                    "instances": {
                        "minimal": {
                            "url": "https://minimal.plextrac.com",
                            "verify_ssl": True
                        }
                    }
                },
                "nessus": {
                    "csv_format": {
                        "required_fields": ["Plugin ID", "Name", "Risk"],
                        "optional_fields": []
                    },
                    "categories": {
                        "general": {
                            "display_name": "General Findings",
                            "description": "All types of findings",
                            "plugin_ids": []
                        }
                    }
                },
                "output": {
                    "directory": "output",
                    "screenshots": "screenshots"
                },
                "general": {
                    "timeout": 30,
                    "threads": 2,
                    "log_level": "warning"
                }
            }
        else:
            self.logger.warning(f"Unknown template: {template_name}")
            return {}

    def apply_template(self, template_name: str) -> Dict[str, Any]:
        """
        Apply a configuration template
        
        Args:
            template_name: Name of the template to apply
            
        Returns:
            Updated configuration dictionary
        """
        template = self.load_template(template_name)
        
        if not template:
            self.logger.warning("Failed to load template")
            return self.config
        
        # Confirm template application
        use_template = self._get_boolean_input(
            f"Use the '{template_name}' template as a starting point?", True
        )
        
        if use_template:
            self.config = template
            self.logger.info(f"Applied '{template_name}' template")
            
            # Save the configuration
            self._save_configuration()
        
        return self.config

    def _save_configuration(self) -> bool:
        """
        Save the configuration to the specified file
        
        Returns:
            True if successful, False otherwise
        """
        try:
            config_dir = os.path.dirname(self.config_path)
            if config_dir and not os.path.exists(config_dir):
                os.makedirs(config_dir, exist_ok=True)
            
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=4)
            
            self.logger.info("Configuration saved successfully")
            return True
        except (IOError, OSError) as e:
            self.logger.error(f"Failed to save configuration: {str(e)}")
            return False
    
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
        
        # Validate nessus categories
        if "categories" not in self.config.get("nessus", {}):
            self.logger.warning("No Nessus categories configured. It's recommended to configure at least one category.")
        
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