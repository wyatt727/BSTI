import os
import json
import getpass
from scripts.logging_config import log

class DroneConfigManager:
    """
    Manages drone connection configurations including host/IP, username and password.
    
    This class provides functionality to:
    - Store drone configurations in a JSON file
    - Retrieve drone configurations
    - Test drone connections
    - Create preset profiles for quick connection
    """
    
    def __init__(self, config_file=None):
        """
        Initialize the drone configuration manager.
        
        Args:
            config_file: Path to the drone configuration file (optional)
        """
        # Determine home directory safely
        home_dir = os.path.expanduser("~")
        if not os.path.exists(home_dir):
            home_dir = os.getcwd()
            log.warning(f"Home directory not found, using current directory: {home_dir}")
            
        self.config_dir = os.path.join(home_dir, ".bsti")
        self.config_file = config_file or os.path.join(self.config_dir, "drone_config.json")
        self.configs = {}
        self._load_configs()
    
    def _ensure_config_dir_exists(self):
        """Ensure the configuration directory exists and is writable."""
        try:
            if not os.path.exists(self.config_dir):
                os.makedirs(self.config_dir, exist_ok=True)
                log.info(f"Created configuration directory: {self.config_dir}")
            
            # Verify the directory is writable by creating a test file
            test_file = os.path.join(self.config_dir, ".test_write")
            try:
                with open(test_file, 'w') as f:
                    f.write("test")
                os.remove(test_file)
                return True
            except Exception as e:
                log.error(f"Configuration directory is not writable: {self.config_dir}")
                log.error(f"Error: {str(e)}")
                return False
        except Exception as e:
            log.error(f"Failed to create configuration directory: {self.config_dir}")
            log.error(f"Error: {str(e)}")
            return False
    
    def _load_configs(self):
        """Load drone configurations from the config file."""
        # Ensure directory exists first
        self._ensure_config_dir_exists()
        
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r') as f:
                    self.configs = json.load(f)
                log.info(f"Loaded {len(self.configs)} drone configurations from {self.config_file}")
            except json.JSONDecodeError as e:
                log.error(f"Invalid JSON in configuration file: {str(e)}")
                # Backup the corrupted file
                backup_file = f"{self.config_file}.bak"
                try:
                    import shutil
                    shutil.copy(self.config_file, backup_file)
                    log.info(f"Backed up corrupted configuration to {backup_file}")
                except Exception as be:
                    log.error(f"Failed to backup corrupted configuration: {str(be)}")
                self.configs = {}
            except Exception as e:
                log.error(f"Error loading drone configurations: {str(e)}")
                self.configs = {}
    
    def _save_configs(self):
        """Save drone configurations to the config file."""
        # First ensure the directory exists and is writable
        if not self._ensure_config_dir_exists():
            log.error("Cannot save configuration: directory issues")
            return False
            
        try:
            with open(self.config_file, 'w') as f:
                json.dump(self.configs, f, indent=4)
            log.info(f"Saved {len(self.configs)} drone configurations to {self.config_file}")
            
            # Verify the file was actually created
            if os.path.exists(self.config_file):
                return True
            else:
                log.error(f"Configuration file was not created: {self.config_file}")
                return False
        except PermissionError as e:
            log.error(f"Permission error saving configuration: {str(e)}")
            log.error(f"Please check permissions for: {self.config_file}")
            return False
        except IOError as e:
            log.error(f"IO error saving configuration: {str(e)}")
            return False
        except Exception as e:
            log.error(f"Unexpected error saving drone configurations: {str(e)}")
            log.error(f"Config file path: {self.config_file}")
            import traceback
            log.debug(traceback.format_exc())
            return False
    
    def add_drone(self, name, hostname, username, password=None, save_password=False):
        """
        Add a new drone configuration or update an existing one.
        
        Args:
            name: A friendly name for the drone
            hostname: The hostname or IP address of the drone
            username: The username for the drone
            password: The password for the drone (optional)
            save_password: Whether to save the password (default: False)
            
        Returns:
            bool: True if the drone was added successfully, False otherwise
        """
        log.info(f"Adding drone configuration: {name}")
        
        # Validate inputs
        if not name or not hostname or not username:
            log.error("Missing required parameters (name, hostname, username)")
            return False
            
        # Create the configuration
        try:
            self.configs[name] = {
                "hostname": hostname,
                "username": username
            }
            
            if save_password and password:
                self.configs[name]["password"] = password
                
            # Save the configuration
            success = self._save_configs()
            if success:
                log.info(f"Successfully added drone: {name}")
                return True
            else:
                log.error(f"Failed to save configuration for drone: {name}")
                return False
        except Exception as e:
            log.error(f"Error adding drone {name}: {str(e)}")
            return False
    
    def remove_drone(self, name):
        """
        Remove a drone configuration.
        
        Args:
            name: The name of the drone to remove
            
        Returns:
            bool: True if the drone was removed successfully, False otherwise
        """
        if name in self.configs:
            del self.configs[name]
            return self._save_configs()
        return False
    
    def get_drone(self, name):
        """
        Get a drone configuration.
        
        Args:
            name: The name of the drone to get
            
        Returns:
            dict: The drone configuration or None if not found
        """
        return self.configs.get(name, None)
    
    def get_drone_names(self):
        """
        Get a list of all drone names.
        
        Returns:
            list: A list of drone names
        """
        return list(self.configs.keys())
    
    def test_connection(self, name=None, hostname=None, username=None, password=None):
        """
        Test a connection to a drone.
        
        Args:
            name: The name of the drone to test (optional)
            hostname: The hostname or IP address of the drone (optional)
            username: The username for the drone (optional)
            password: The password for the drone (optional)
            
        If name is provided, the other parameters are ignored and
        the configuration for that name is used.
        
        Returns:
            bool: True if the connection was successful, False otherwise
        """
        from scripts.drone import Drone
        
        try:
            # Use configuration if name is provided
            if name and name in self.configs:
                config = self.configs[name]
                hostname = config["hostname"]
                username = config["username"]
                password = config.get("password", password)
                
            # Validate parameters
            if not (hostname and username and password):
                log.error("Missing required connection parameters")
                return False
                
            # Test connection
            log.info(f"Testing connection to {hostname}")
            drone = Drone(hostname, username, password)
            # A simple command to test the connection
            result = drone.execute("echo 'Connection successful'")
            
            if "Connection successful" in result:
                log.success(f"Successfully connected to {hostname}")
                return True
            else:
                log.error(f"Failed to connect to {hostname}")
                return False
                
        except Exception as e:
            log.error(f"Error testing connection: {str(e)}")
            return False

    def interactive_setup(self):
        """
        Run an interactive setup wizard to configure a drone.
        
        Returns:
            dict: The configured drone or None if cancelled
        """
        try:
            print("\nDrone Connection Setup Wizard")
            print("============================\n")
            
            name = input("Enter a name for this drone configuration: ").strip()
            if not name:
                print("Setup cancelled")
                return None
                
            hostname = input("Enter the hostname or IP address: ").strip()
            if not hostname:
                print("Setup cancelled")
                return None
                
            username = input("Enter the username: ").strip()
            if not username:
                print("Setup cancelled")
                return None
                
            password = getpass.getpass("Enter the password: ").strip()
            if not password:
                print("Setup cancelled")
                return None
                
            save_password = input("Save password? (y/n): ").strip().lower() == 'y'
            
            # Test connection
            print("Testing connection...")
            if self.test_connection(hostname=hostname, username=username, password=password):
                # Add configuration
                success = self.add_drone(name, hostname, username, password, save_password)
                if success:
                    print(f"Drone configuration '{name}' saved successfully")
                    return {
                        "name": name,
                        "hostname": hostname,
                        "username": username,
                        "password": password
                    }
                else:
                    print("Failed to save drone configuration. Check permissions and try again.")
                    return None
            else:
                print("Connection test failed. Configuration not saved.")
                retry = input("Retry? (y/n): ").strip().lower() == 'y'
                if retry:
                    return self.interactive_setup()
                return None
                
        except KeyboardInterrupt:
            print("\nSetup cancelled")
            return None
        except Exception as e:
            print(f"Error during setup: {str(e)}")
            return None

# Create a singleton instance
drone_config_manager = DroneConfigManager() 