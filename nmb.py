#!/usr/bin/env python3
# BSTI Nessus Management Buddy (NMB)
# Author: Connor Fancy
# Version: 1.2

import argparse
import sys
import signal
import os
import pretty_errors
from scripts.nessus import Nessus
from scripts.creator import GenConfig
from scripts.lackey import Lackey
from scripts.logging_config import log

# Import core BSTI Nessus modules for enhanced functionality
from bsti_nessus.utils.credentials import CredentialManager
from bsti_nessus.utils.config_wizard import ConfigWizard
from bsti_nessus.utils.progress import ProgressTracker
from bsti_nessus.utils.parallel import ThreadPool, ProcessPool
from bsti_nessus.utils.logger import Logger
from bsti_nessus.utils.progress import ProgressTracker
from bsti_nessus.utils.credentials import CredentialManager
from scripts.nessus import Nessus
from scripts.creator import GenConfig
from scripts.drone_config import drone_config_manager

# Define chunk_items function since it's not available in any module
def chunk_items(items, chunk_size=10):
    """Split a list of items into chunks of specified size."""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]

# ================== Utility Functions ==================

class CredentialsCache:
    def __init__(self, username=None, password=None):
        self.username = username
        self.password = password
        self.credential_manager = None
        
        # Initialize the secure credential manager if credentials aren't provided
        if not (username and password):
            self.initialize_credential_manager()

    def initialize_credential_manager(self):
        """Initialize the secure credential manager for storing and retrieving credentials."""
        try:
            self.credential_manager = CredentialManager(service_name="bsti-nessus")
            stored_creds = self.credential_manager.get_credentials("nessus-drone")
            if stored_creds:
                self.username, self.password = stored_creds
                log.info("Using securely stored credentials")
        except Exception as e:
            log.warning(f"Failed to initialize secure credential manager: {str(e)}")

    def get_creds(self):
        """Get stored credentials, returns tuple of (username, password)."""
        return self.username, self.password
    
    def store_creds(self, username, password):
        """Securely store credentials for future use."""
        if self.credential_manager:
            try:
                self.credential_manager.store_credentials("nessus-drone", username, password)
                self.username = username
                self.password = password
                log.info("Credentials securely stored for future use")
                return True
            except Exception as e:
                log.error(f"Failed to store credentials: {str(e)}")
                return False
        return False

    def test_connection(self, drone_host):
        """Test connection to Nessus using stored credentials."""
        if not self.username or not self.password:
            log.error("No credentials available to test connection")
            return False
        
        # This is a placeholder - actual implementation would depend on how
        # your Nessus connection testing is implemented
        try:
            log.info(f"Testing connection to {drone_host} with username {self.username}")
            # Actual connection test would be here
            return True
        except Exception as e:
            log.error(f"Connection test failed: {str(e)}")
            return False

def find_policy_file(project_scope):
    """Find the appropriate Nessus policy file based on the project scope."""
    policies = {
        'core': "Default Good Model Nessus Vulnerability Policy.nessus",
        'nc': "Custom_Nessus_Policy-Pn_pAll_AllSSLTLS-Web-NoLocalCheck-NoDOS.nessus"
    }
    
    # If project_scope is 'custom', prompt the user for the path
    if project_scope == 'custom':
        custom_path = input("Please enter the path to your custom policy file: ").strip()
        return os.path.normpath(custom_path)
    
    policy_dir = os.path.join(os.getcwd(), "Nessus-policy")
    return os.path.normpath(os.path.join(policy_dir, policies.get(project_scope, "")))


def read_targets(targets_file_path):
    """Read target URLs from a file."""
    with open(targets_file_path, 'r') as targets_file:
        return [url.strip() for url in targets_file.readlines() if url.strip()]

def process_targets_in_parallel(targets, process_func, max_workers=4, use_processes=False):
    """Process a list of targets in parallel using either threads or processes."""
    pool_class = ProcessPool if use_processes else ThreadPool
    
    # Create progress tracker for the operation
    progress = ProgressTracker(
        total=len(targets),
        desc="Processing targets",
        unit="targets"
    )
    
    # Process the targets in parallel with progress reporting
    with pool_class(max_workers=max_workers) as pool:
        # Chunk the targets into batches for better performance
        chunked_targets = chunk_items(targets, chunk_size=10)
        
        # Define a wrapper function that updates progress
        def process_chunk(chunk):
            results = []
            for item in chunk:
                result = process_func(item)
                progress.update(1)
                results.append(result)
            return results
        
        # Submit all chunks to the pool
        futures = [pool.submit(process_chunk, chunk) for chunk in chunked_targets]
        
        # Collect all results
        all_results = []
        for future in futures:
            try:
                results = future.result()
                all_results.extend(results)
            except Exception as e:
                progress.error()
                log.error(f"Error processing targets: {str(e)}")
        
        progress.finish()
        return all_results

def read_credentials(username_file_path, password_file_path):
    """Read username and password credentials from files."""
    try:
        if not username_file_path:
            return None, None
        with open(username_file_path, 'r') as username_file, open(password_file_path, 'r') as password_file:
            usernames = [u.strip() for u in username_file.read().split('\n') if u.strip()]
            passwords = [p.strip() for p in password_file.read().split('\n') if p.strip()]
            return usernames, passwords
    except Exception as e:
        log.warning(f"Scan will be executed without credentials due to: {str(e)}")
        return None, None

def determine_execution_mode(args):
    """Determine whether to run locally or on the drone."""
    # Return True if we want to run locally, False if we want to run on the drone
    # For internal mode, explicitly use drone unless --local is passed
    is_local = args.local is True
    log.info(f"Execution mode: {'LOCAL' if is_local else 'DRONE'}")
    return is_local

def signal_handler(signal, frame):
    """Handle Ctrl+C graceful exit."""
    print()
    log.warning("Ctrl+C detected. Exiting...")
    sys.exit(0)

def run_config_wizard(args, creds_cache):
    """Run the interactive configuration wizard."""
    log.info("Starting configuration wizard...")
    
    # Determine config path
    config_path = os.path.join(os.getcwd(), "NMB_config.json")
    
    # Create a progress tracker for the wizard
    progress = ProgressTracker(
        total=5,  # Approximate number of steps
        description="Configuration wizard",
        unit="steps"
    )
    
    # Initialize wizard with more specific parameters
    wizard = ConfigWizard(config_path=config_path)
    progress.update(1, info="Collecting configuration options")
    
    # Run the wizard
    config = wizard.run_wizard()
    progress.update(3, info="Processing configuration")
    
    if config:
        # Store credentials if provided
        if config.get('username') and config.get('password'):
            progress.update(4, info="Storing credentials")
            creds_cache.store_creds(config['username'], config['password'])
        
        # Update args with new configuration values
        for key, value in config.items():
            if hasattr(args, key) and value:
                setattr(args, key, value)
        
        progress.close()
        log.success("Configuration completed successfully")
        
        # Test connection if we have drone and credentials
        if hasattr(args, 'drone') and args.drone and config.get('username') and config.get('password'):
            if creds_cache.test_connection(args.drone):
                log.success(f"Successfully connected to {args.drone}")
            else:
                log.warning(f"Could not connect to {args.drone}. Please check your credentials and connection.")
        
        return True
    
    progress.close(success=False)
    log.error("Configuration wizard was cancelled or failed")
    return False


# ================== Mode Handlers ==================

def handle_mode(args, mode, required_args, handler_info):
    """Handle the execution of different modes."""
    if getattr(args, 'local', False) and "drone" in required_args:
        required_args.remove("drone")
    
    missing_args = [arg for arg in required_args if not getattr(args, arg)]
    if missing_args:
        log.error(f"Missing required arguments for {mode} mode: {', '.join(missing_args)}")
        sys.exit(1)
    
    # Determine number of steps for progress tracking
    if 'handler_class' in handler_info:
        num_steps = 1
    else:
        num_steps = len(handler_info['handler_classes_with_args_providers'])
    
    # Setup progress tracking for this operation with more informative description
    progress_tracker = ProgressTracker(
        total=num_steps, 
        desc=f"Running {mode.upper()} operation",
        unit="steps"
    )
    
    # Handle modes that use the old structure
    if 'handler_class' in handler_info:
        handler_classes_with_args_providers = [(handler_info['handler_class'], handler_info['handler_args_providers'])]
    else:
        handler_classes_with_args_providers = handler_info['handler_classes_with_args_providers']
    
    # Determine if we should use parallel processing
    use_parallel = getattr(args, 'parallel', False)
    
    try:
        progress_tracker.start()
        for i, (handler_class, handler_args_providers) in enumerate(handler_classes_with_args_providers):
            handler_args = []
            handler_kwargs = {}
            for provider in handler_args_providers:
                result = provider(args)
                if isinstance(result, tuple):
                    handler_args.extend(result)
                elif isinstance(result, dict):
                    handler_kwargs.update(result)
                else:
                    handler_args.append(result)
            
            # Add parallel processing flag if needed
            if use_parallel:
                handler_kwargs['parallel'] = True
            
            progress_tracker.update(i + 1, desc=f"Running {handler_class.__name__}")
            
            # Create instance and run
            handler = handler_class(*handler_args, **handler_kwargs)
            
            # If the class has a run method, call it
            if hasattr(handler, 'run'):
                handler.run()
        
        progress_tracker.finish()
        log.success(f"{mode.upper()} operation completed successfully")

    except Exception as e:
        progress_tracker.error()
        log.error(f"An error occurred during {mode} execution: {str(e)}")
        import traceback
        log.debug(traceback.format_exc())


# === Main Execution ===
def main():
    """Main function to handle application flow."""
    signal.signal(signal.SIGINT, signal_handler)
    args = parse_arguments()
    
    # Display mode banner to provide context
    if hasattr(args, 'mode') and args.mode:
        log.info(f"Running in {args.mode.upper()} mode")
    
    # Handle config wizard if requested
    if hasattr(args, 'config_wizard') and args.config_wizard:
        creds_cache = CredentialsCache()
        if run_config_wizard(args, creds_cache):
            log.info("Configuration wizard completed successfully")
        else:
            log.error("Configuration wizard was cancelled or failed")
            return
    
    # Process drone argument - check if it's a saved configuration
    if hasattr(args, 'drone') and args.drone:
        # If using a saved drone configuration
        config = drone_config_manager.get_drone(args.drone)
        if config:
            log.info(f"Using saved drone configuration: {args.drone}")
            # If we have a saved drone config, use those details
            args.drone = config['hostname']
            
            # Only overwrite username/password if they weren't provided explicitly
            if not args.username:
                args.username = config['username']
            
            # We'll handle password later when creating the creds_cache
    
    # Initialize credentials cache with provided or saved credentials
    creds_cache = CredentialsCache(username=args.username, password=args.password)
    
    # If we have a saved drone config with password and no explicit password provided
    if (hasattr(args, 'drone') and 
        drone_config_manager.get_drone(args.drone) and 
        'password' in drone_config_manager.get_drone(args.drone) and
        not args.password):
        # Use the saved password
        config = drone_config_manager.get_drone(args.drone)
        creds_cache.username = args.username or config['username']
        creds_cache.password = config['password']
    
    # Define mode handlers
    mode_handlers = {
        "deploy": {
            "required_args": ["client", "project_type", "drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                      lambda _: creds_cache.get_creds(),
                                      lambda args: args.mode,
                                      lambda args: args.client, 
                                      lambda args: find_policy_file(args.project_type), 
                                      lambda args: args.targets_file, 
                                      lambda args: args.exclude_file,
                                      lambda args: args.discovery]
        },
        "create": {
            "required_args": ["client", "project_type", "drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                      lambda _: creds_cache.get_creds(),
                                      lambda args: args.mode,
                                      lambda args: args.client, 
                                      lambda args: find_policy_file(args.project_type), 
                                      lambda args: args.targets_file, 
                                      lambda args: args.exclude_file]
        },
        "launch": {
            "required_args": ["client", "drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                      lambda _: creds_cache.get_creds(),
                                      lambda args: args.mode,
                                      lambda args: args.client]
        },
        "pause": {
            "required_args": ["client", "drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                      lambda _: creds_cache.get_creds(),
                                      lambda args: args.mode,
                                      lambda args: args.client]
        },
        "resume": {
            "required_args": ["client", "drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                       lambda _: creds_cache.get_creds(),
                                       lambda _: args.mode,
                                       lambda args: args.client]
        },
        "monitor": {
            "required_args": ["client", "drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                       lambda _: creds_cache.get_creds(),
                                       lambda _: args.mode,
                                       lambda args: args.client]
        },
        "regen": {
            "required_args": [],
            "handler_class": GenConfig,
            "handler_args_providers": [lambda _: {"regen": True}]
        },
        "export": {
            "required_args": ["client", "drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone, 
                                       lambda _: creds_cache.get_creds(),
                                       lambda _: args.mode,
                                       lambda args: args.client]
        },
        "test-connection": {
            "required_args": ["drone"],
            "handler_class": Nessus,
            "handler_args_providers": [lambda args: args.drone,
                                       lambda _: creds_cache.get_creds(),
                                       lambda _: "test-connection"]
        }
    }
    
    # == Mode Execution Logic ==
    
    # If mode is provided, get the right handler
    if hasattr(args, 'mode') and args.mode:
        if args.mode == "external" or args.mode == "internal":
            args.client = args.client or args.project_type
            args.external = args.mode == "external"
            log.info(f"Running in {'external' if args.external else 'internal'} mode")
            
            if determine_execution_mode(args):
                is_local = True
                log.info("Executing tools locally")
                Tools(args, run_locally=is_local)
            else:
                log.info(f"Using drone {args.drone} for execution")
                try:
                    Nessus(args.drone, *creds_cache.get_creds())
                except Exception as e:
                    log.error(f"Error connecting to drone: {str(e)}")
                    log.error("Please check your credentials and connection")
                    sys.exit(1)
        elif args.mode == "test-connection":
            # Test connection to drone
            if not args.drone:
                log.error("Please specify a drone with -d/--drone")
                sys.exit(1)
                
            # If it's a saved configuration, use that
            config = drone_config_manager.get_drone(args.drone)
            if config:
                success = drone_config_manager.test_connection(name=args.drone)
                if success:
                    log.success(f"Successfully connected to {args.drone}")
                else:
                    log.error(f"Failed to connect to {args.drone}")
                sys.exit(0 if success else 1)
            
            # Otherwise test with provided credentials
            username, password = creds_cache.get_creds()
            if not username or not password:
                log.error("Username and password are required for connection test")
                
                # Try to get from the drone config if available
                config = drone_config_manager.get_drone(args.drone)
                if config and "username" in config:
                    username = config["username"]
                    if "password" in config:
                        password = config["password"]
                        log.info(f"Using credentials from drone configuration {args.drone}")
                    else:
                        import getpass
                        password = getpass.getpass(f"Enter password for {config['hostname']}: ")
                else:
                    sys.exit(1)
            
            success = False
            try:
                # Use Nessus class to test the connection
                Nessus(args.drone, username, password, mode="test-connection")
                success = True
                log.success(f"Successfully connected to {args.drone}")
            except Exception as e:
                log.error(f"Failed to connect to {args.drone}: {str(e)}")
            
            # If --store-credentials was specified, store them
            if success and hasattr(args, 'store_credentials') and args.store_credentials:
                if creds_cache.store_creds(username, password):
                    log.success("Credentials stored successfully")
                    
                    # Also save to the drone configuration if requested
                    save_to_config = input("Save to drone configurations? (y/n): ").strip().lower() == 'y'
                    if save_to_config:
                        name = input("Enter name for this drone configuration: ").strip()
                        if name:
                            save_password = input("Save password? (y/n): ").strip().lower() == 'y'
                            drone_config_manager.add_drone(name, args.drone, username, 
                                                       password if save_password else None, 
                                                       save_password)
                            log.success(f"Drone configuration saved as '{name}'")
                
            sys.exit(0 if success else 1)
        else:
            # Handle other modes from the mode_handlers dictionary
            handler_info = mode_handlers.get(args.mode)
            if handler_info:
                handle_mode(args, args.mode, handler_info["required_args"], handler_info)
            else:
                log.error(f"Unknown mode: {args.mode}")
                sys.exit(1)
    else:
        log.warning("No mode specified. Run with -h/--help for usage information.")


# === Argument Parsing ===
def parse_arguments():
    """Parse command line arguments."""
    signal.signal(signal.SIGINT, signal_handler)
    parser = argparse.ArgumentParser(
        usage = "nmb.py [OPTIONS]",
        formatter_class = argparse.RawTextHelpFormatter,
        epilog = "Example:\n" \
                 "nmb.py -d storm -c myclient -m deploy -s core -u bstg -p password --csv-file path/to/csv\n" \
    )
    parser.add_argument("-m", "--mode", required=False, 
        choices=["deploy", "create", "launch", "pause", "resume", "monitor", 
                 "export", "external", "internal", "regen", "test-connection"], 
        help="choose mode to run Nessus:\n" \
        "deploy: update settings, upload policy file, upload targets file, launch scan, monitor scan, export results, analyze results\n" \
        "create: update settings, upload policy file, upload targets files\n" \
        "launch: launch scan, export results, analyze results\n" \
        "pause: pause scan\n" \
        "resume: resume scan, export results, analyze results\n" \
        "monitor: monitor scan\n" \
        "export: export scan results, analyze results\n" \
        "external: perform nmap scans, manual finding verification, generate external report, take screenshots\n" \
        "internal: perform nmap scans, manual finding verification, generate internal report, take screenshots\n" \
        "regen: Regenerates 'NMB_config.json'\n" \
        "test-connection: Test connection to Nessus drone with credentials"
    )

    # UTIL
    parser.add_argument("-u", "--username", required=False, help="Username for the drone")
    parser.add_argument("-p", "--password", required=False, help="Password for the drone")
    parser.add_argument("--targets-file", required=False, help="Path to the txt file")
    parser.add_argument("--csv-file", required=False, help="Path to the csv file")
    parser.add_argument("--config-wizard", action="store_true", help="Launch the configuration wizard")
    parser.add_argument("--store-credentials", action="store_true", help="Securely store provided credentials for future use")
    parser.add_argument("--use-drone-config", action="store_true", 
                      help="Use a saved drone configuration (name specified with -d/--drone)")

    # INTERNAL/EXTERNAL
    parser.add_argument("-d", "--drone", required=False, 
                      help="drone name or IP (can be a saved configuration name)")
    parser.add_argument("-c", "--client-name", dest="client", required=False, help="client name or project name (used to name the scan and output files)")
    parser.add_argument("-s", "--scope", dest="project_type", required=False, choices=["core", "nc", "custom"], help="Specify if core, custom or non-core policy file")
    parser.add_argument("-e", "--exclude-file", dest="exclude_file", required=False, help="exclude targets file", type=argparse.FileType('r'))
    parser.add_argument("-ex", "--external", dest="external", required=False, action="store_const", const=True, help="Enable external mode")
    parser.add_argument("-l", "--local", dest="local", required=False, action="store_const", const=True, help="run manual checks on your local machine instead of over ssh")
    parser.add_argument("--discovery", dest="discovery", required=False, action="store_const", const=True, help="Enable discovery scan prior to running nessus.")
    
    # Parallel Processing Options
    parser.add_argument("--parallel", action="store_true", help="Enable parallel processing for faster execution")
    parser.add_argument("--workers", type=int, default=4, help="Number of parallel workers to use (default: 4)")
    parser.add_argument("--use-processes", action="store_true", help="Use processes instead of threads for parallelization (better for CPU-intensive tasks)")
    
    # Logging Options
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")
    parser.add_argument("--quiet", action="store_true", help="Suppress all but error messages")
    
    # Drone config management
    parser.add_argument("--drone-config", dest="drone_config_cmd", required=False,
                      choices=["list", "add", "remove", "test", "wizard"],
                      help="Manage drone configurations")
    parser.add_argument("--drone-name", required=False, help="Name for a drone configuration (used with --drone-config)")
    parser.add_argument("--drone-hostname", required=False, help="Hostname/IP for a drone configuration (used with --drone-config add)")
    parser.add_argument("--save-drone-password", action="store_true", help="Save drone password in configuration")

    args = parser.parse_args()
    
    # Configure logging based on verbosity settings
    if args.verbose:
        log.set_level("DEBUG")
    elif args.quiet:
        log.set_level("ERROR")
    
    # Handle drone config management commands
    if args.drone_config_cmd:
        handle_drone_config_command(args)
        sys.exit(0)
    
    # Store credentials if requested
    if args.store_credentials and args.username and args.password:
        creds_cache = CredentialsCache()
        creds_cache.store_creds(args.username, args.password)
    
    return args

def handle_drone_config_command(args):
    """Handle drone configuration management commands."""
    if args.drone_config_cmd == "list":
        # List drone configurations
        drone_names = drone_config_manager.get_drone_names()
        if not drone_names:
            log.info("No drone configurations found.")
            return
        
        log.info(f"Found {len(drone_names)} drone configurations:")
        for name in drone_names:
            config = drone_config_manager.get_drone(name)
            password_saved = "Yes" if "password" in config else "No"
            log.info(f"  {name}: {config['hostname']} (User: {config['username']}, Password saved: {password_saved})")
    
    elif args.drone_config_cmd == "add":
        # Add a drone configuration
        if not (args.drone_name and args.drone_hostname and args.username):
            log.error("Missing required arguments for adding a drone configuration.")
            log.info("Usage: --drone-config add --drone-name NAME --drone-hostname HOSTNAME --username USERNAME [--password PASSWORD] [--save-drone-password]")
            return
        
        password = args.password
        if not password:
            import getpass
            password = getpass.getpass(f"Enter password for {args.drone_hostname}: ")
        
        # Test connection first
        log.info(f"Testing connection to {args.drone_hostname}...")
        success = drone_config_manager.test_connection(
            hostname=args.drone_hostname, 
            username=args.username, 
            password=password
        )
        
        if success:
            # Add the configuration
            drone_config_manager.add_drone(
                args.drone_name, 
                args.drone_hostname, 
                args.username, 
                password,
                args.save_drone_password
            )
            log.success(f"Drone configuration '{args.drone_name}' added successfully.")
        else:
            log.error(f"Connection test failed. Configuration not added.")
    
    elif args.drone_config_cmd == "remove":
        # Remove a drone configuration
        if not args.drone_name:
            log.error("Missing drone name for removal.")
            log.info("Usage: --drone-config remove --drone-name NAME")
            return
        
        success = drone_config_manager.remove_drone(args.drone_name)
        if success:
            log.success(f"Drone configuration '{args.drone_name}' removed successfully.")
        else:
            log.error(f"Failed to remove drone configuration '{args.drone_name}'.")
    
    elif args.drone_config_cmd == "test":
        # Test a drone configuration
        if not args.drone_name:
            log.error("Missing drone name for testing.")
            log.info("Usage: --drone-config test --drone-name NAME [--password PASSWORD]")
            return
        
        config = drone_config_manager.get_drone(args.drone_name)
        if not config:
            log.error(f"No configuration found for drone '{args.drone_name}'.")
            return
        
        password = args.password
        if not password and "password" not in config:
            import getpass
            password = getpass.getpass(f"Enter password for {config['hostname']}: ")
        
        success = drone_config_manager.test_connection(
            name=args.drone_name, 
            password=password
        )
        
        if success:
            log.success(f"Successfully connected to drone '{args.drone_name}'.")
        else:
            log.error(f"Failed to connect to drone '{args.drone_name}'.")
    
    elif args.drone_config_cmd == "wizard":
        # Run the configuration wizard
        result = drone_config_manager.interactive_setup()
        if result:
            log.success(f"Drone configuration '{result['name']}' set up successfully.")
        else:
            log.error("Drone setup was cancelled or failed.")
    
if __name__ == '__main__':
    log.info("---------------Welcome to NMB----------------")
    log.info("BSTI Nessus Management Buddy v1.2")
    main()
