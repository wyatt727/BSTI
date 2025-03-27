"""
Command-line interface for the BSTI Nessus to Plextrac converter.
"""
import argparse
import sys
import os
from typing import Any

from ..utils.logger import log, setup_logging
from ..utils.config_manager import ConfigManager
from ..utils.config_wizard import ConfigWizard
from .engine import NessusEngine


def parse_arguments() -> Any:
    """
    Parse command-line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="BSTI Nessus to Plextrac Converter",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  # Run the configuration wizard for interactive setup:
  python bsti_nessus_converter.py --config-wizard
  
  # Convert and upload Nessus findings:
  python bsti_nessus_converter.py -u johndoe -p password123 -d ./nessus_files -t dev
  
  # Include screenshot uploads:
  python bsti_nessus_converter.py -u johndoe -p password123 -d ./nessus_files -t dev --screenshots --screenshot-dir ./screenshots
  
  # Use stored credentials:
  python bsti_nessus_converter.py --use-stored-credentials -d ./nessus_files -t dev
        """
    )
    
    # Configuration options
    config_group = parser.add_argument_group("Configuration Options")
    config_group.add_argument("--config", "-c", default="config/config.json", 
                            help="Path to configuration file (default: config/config.json)")
    config_group.add_argument("--config-wizard", action="store_true", 
                             help="Run the configuration wizard to set up or update the configuration")
    
    # Credential management options
    credential_group = parser.add_argument_group("Credential Management")
    credential_group.add_argument("--use-stored-credentials", action="store_true",
                                help="Use stored credentials for the specified Plextrac instance")
    credential_group.add_argument("--store-credentials", action="store_true",
                                help="Store credentials after successful authentication")
    
    # Required arguments - not required if running the config wizard
    required_args = parser.add_argument_group("Required Arguments (not needed with --config-wizard)")
    required_args.add_argument("-u", "--username", help="Username for Plextrac authentication")
    required_args.add_argument("-p", "--password", help="Password for Plextrac authentication")
    required_args.add_argument("-d", "--directory", help="Directory containing Nessus CSV files")
    required_args.add_argument("-t", "--target-plextrac", dest="target_plextrac", 
                              help="Target Plextrac instance (e.g., 'dev', 'prod')")
    
    # Optional arguments
    optional_args = parser.add_argument_group("Optional Arguments")
    optional_args.add_argument("-s", "--scope", 
                             choices=["internal", "external", "web", "surveillance", "mobile"], 
                             default="internal", 
                             help="Scope of the findings (default: internal)")
    optional_args.add_argument("--screenshot-dir", dest="screenshot_dir", 
                              help="Directory containing screenshots to upload")
    optional_args.add_argument("--client", help="Client name for the report")
    optional_args.add_argument("--report", help="Report name for the findings")
    optional_args.add_argument("--screenshots", action="store_true", 
                              help="Upload screenshots if available")
    optional_args.add_argument("--cleanup", action="store_true", 
                              help="Clean up temporary files after processing")
    optional_args.add_argument("--non-core", dest="non_core", action="store_true", 
                              help="Update non-core fields in Plextrac")
    optional_args.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2], default=1, 
                              help="Verbosity level (0=WARNING, 1=INFO, 2=DEBUG)")
    
    args = parser.parse_args()
    
    # Validate required arguments if not running config wizard
    if not args.config_wizard:
        if not (args.username and args.password) and not args.use_stored_credentials:
            parser.error("Either provide --username and --password or use --use-stored-credentials")
        if not args.directory:
            parser.error("--directory is required when not using --config-wizard")
        if not args.target_plextrac:
            parser.error("--target-plextrac is required when not using --config-wizard")
    
    return args


def validate_arguments(args: Any) -> bool:
    """
    Validate command-line arguments.
    
    Args:
        args (argparse.Namespace): Parsed arguments.
        
    Returns:
        bool: True if arguments are valid, False otherwise.
    """
    # Skip validation for config wizard mode
    if args.config_wizard:
        return True
        
    valid = True
    
    # Check if directory exists
    if not os.path.isdir(args.directory):
        log.error(f"Directory not found: {args.directory}")
        valid = False
    
    # Check if screenshot directory exists if specified
    if args.screenshot_dir and not os.path.isdir(args.screenshot_dir):
        log.error(f"Screenshot directory not found: {args.screenshot_dir}")
        valid = False
    
    return valid


def print_banner():
    """Print the application banner."""
    banner = """
 ____   _____ _______ _____   _   _                          
|  _ \ / ____|__   __|_   _| | \ | |                         
| |_) | (___    | |    | |   |  \| | ___  ___ ___ _   _ ___ 
|  _ < \___ \   | |    | |   | . ` |/ _ \/ __/ __| | | / __|
| |_) |____) |  | |   _| |_  | |\  |  __/\__ \__ \ |_| \__ \\
|____/|_____/   |_|  |_____| |_| \_|\___||___/___/\__,_|___/
                                                             
 _____                          _                            
/ ____|                        | |                           
| |     ___  _ ____   _____ _ __| |_ ___ _ __                
| |    / _ \| '_ \ \ / / _ \ '__| __/ _ \ '__|               
| |___| (_) | | | \ V /  __/ |  | ||  __/ |                  
 \_____\___/|_| |_|\_/ \___|_|   \__\___|_|                  
"""
    print(banner)
    print("BSTI Nessus to Plextrac Converter")
    print("----------------------------------")
    print("Features:")
    print(" - Interactive configuration wizard (--config-wizard)")
    print(" - Secure credential management (--use-stored-credentials, --store-credentials)")
    print(" - Nessus CSV to Plextrac conversion")
    print(" - Screenshot upload and management")
    print(" - Smart finding categorization")
    print("")
    print("Use --help for more information")
    print("----------------------------------")


def run_config_wizard(args: Any):
    """
    Run the configuration wizard.
    
    Args:
        args (argparse.Namespace): Parsed arguments.
    """
    # Set up logging first
    setup_logging(args.verbosity)
    
    log.info("Starting configuration wizard...")
    
    # Create the wizard
    wizard = ConfigWizard(args.config)
    
    # Run the wizard
    wizard.run_wizard()
    
    log.info(f"Configuration wizard completed. Config saved to {args.config}")
    log.info("You can now run the converter with your configured settings.")


def main():
    """
    Main entry point for the application.
    """
    try:
        # Parse command-line arguments
        args = parse_arguments()
        
        # Set up logging
        setup_logging(args.verbosity)
        
        # Print banner
        print_banner()
        
        # Run configuration wizard if requested
        if args.config_wizard:
            run_config_wizard(args)
            return
        
        # Validate arguments
        if not validate_arguments(args):
            sys.exit(1)
        
        # Handle stored credentials if requested
        if args.use_stored_credentials:
            from ..utils.credentials import CredentialManager
            cred_manager = CredentialManager()
            username, password = cred_manager.get_credentials(args.target_plextrac)
            
            if not username or not password:
                log.error(f"No stored credentials found for {args.target_plextrac}")
                sys.exit(1)
                
            log.info(f"Using stored credentials for {args.target_plextrac}")
            args.username = username
            args.password = password
        
        # Create and run the engine
        engine = NessusEngine(args)
        result = engine.run()
        
        # Store credentials if requested
        if args.store_credentials:
            from ..utils.credentials import CredentialManager
            cred_manager = CredentialManager()
            if cred_manager.store_credentials(args.username, args.password, args.target_plextrac):
                log.info(f"Credentials for {args.target_plextrac} stored successfully")
            else:
                log.warning(f"Failed to store credentials for {args.target_plextrac}")
        
        return result
        
    except KeyboardInterrupt:
        log.warning("Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        log.error(f"Unexpected error: {str(e)}")
        import traceback
        log.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main() 