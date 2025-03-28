#!/usr/bin/env python3
"""
BSTI Drone Setup Tool

This script provides a simple command-line interface for setting up
drone connections for the BSTI tool.
"""

import sys
import os
import argparse
import traceback
from scripts.drone_config import drone_config_manager
from scripts.logging_config import log

def print_header():
    """Print the script header."""
    print("\n" + "=" * 40)
    print("   BSTI Drone Connection Setup Tool")
    print("=" * 40 + "\n")
    print("This tool helps you set up and manage drone connections for BSTI.")
    print("Drone connections are saved and can be used with the '-d' option in nmb.py.\n")

def run_wizard():
    """Run the interactive drone setup wizard."""
    print_header()
    print("Starting drone setup wizard...\n")
    
    result = drone_config_manager.interactive_setup()
    
    if result:
        print("\nWizard completed successfully!")
        print(f"You can now use this drone with: python nmb.py -d {result['name']} -m test-connection")
    else:
        print("\nWizard was cancelled or failed.")
        print("For troubleshooting, run: python setup_drone.py --troubleshoot")

def list_drones():
    """List all configured drones."""
    print_header()
    
    drone_names = drone_config_manager.get_drone_names()
    
    if not drone_names:
        print("No drone configurations found.")
        print("Run 'python setup_drone.py --wizard' to create one.")
        return
    
    print(f"Found {len(drone_names)} configured drones:")
    print("-" * 60)
    print(f"{'NAME':<15} {'HOSTNAME':<20} {'USERNAME':<15} {'PASSWORD SAVED':<15}")
    print("-" * 60)
    
    for name in drone_names:
        config = drone_config_manager.get_drone(name)
        password_saved = "Yes" if "password" in config else "No"
        print(f"{name:<15} {config['hostname']:<20} {config['username']:<15} {password_saved:<15}")
    
    print("\nUse these drones with: python nmb.py -d DRONE_NAME ...")

def test_drone(name):
    """Test connection to a configured drone."""
    print_header()
    
    config = drone_config_manager.get_drone(name)
    
    if not config:
        print(f"Error: No configuration found for drone '{name}'.")
        print("Run 'python setup_drone.py --list' to see available drones.")
        return False
    
    print(f"Testing connection to drone '{name}' ({config['hostname']})...")
    
    password = None
    if "password" not in config:
        import getpass
        password = getpass.getpass(f"Enter password for {config['hostname']}: ")
    
    success = drone_config_manager.test_connection(name=name, password=password)
    
    if success:
        print(f"\nSuccess! Connection to '{name}' ({config['hostname']}) is working.")
        return True
    else:
        print(f"\nFailed to connect to '{name}' ({config['hostname']}).")
        print("Please check your network connection and credentials.")
        return False

def delete_drone(name):
    """Delete a drone configuration."""
    print_header()
    
    config = drone_config_manager.get_drone(name)
    
    if not config:
        print(f"Error: No configuration found for drone '{name}'.")
        print("Run 'python setup_drone.py --list' to see available drones.")
        return
    
    confirm = input(f"Are you sure you want to delete drone '{name}' ({config['hostname']})? (y/n): ")
    
    if confirm.lower() != 'y':
        print("Operation cancelled.")
        return
    
    success = drone_config_manager.remove_drone(name)
    
    if success:
        print(f"Drone '{name}' was successfully deleted.")
    else:
        print(f"Failed to delete drone '{name}'.")
        print("For troubleshooting, run: python setup_drone.py --troubleshoot")

def add_drone_manually():
    """Add a drone manually, bypassing the wizard."""
    print_header()
    print("Add a drone configuration manually\n")
    
    name = input("Enter a name for this drone configuration: ").strip()
    if not name:
        print("Operation cancelled.")
        return
    
    hostname = input("Enter the hostname or IP address: ").strip()
    if not hostname:
        print("Operation cancelled.")
        return
    
    username = input("Enter the username: ").strip()
    if not username:
        print("Operation cancelled.")
        return
    
    import getpass
    password = getpass.getpass("Enter the password: ").strip()
    if not password:
        print("Operation cancelled.")
        return
    
    save_password = input("Save password? (y/n): ").strip().lower() == 'y'
    
    # Add drone directly, bypassing connection test
    print("Adding drone configuration without testing connection...")
    success = drone_config_manager.add_drone(name, hostname, username, password, save_password)
    
    if success:
        print(f"Drone configuration '{name}' was successfully added.")
        print(f"You can test the connection with: python setup_drone.py --test {name}")
    else:
        print(f"Failed to add drone configuration '{name}'.")
        print("For troubleshooting, run: python setup_drone.py --troubleshoot")

def run_troubleshoot():
    """Run troubleshooting diagnostics."""
    print_header()
    print("Drone Configuration Troubleshooting\n")
    
    # Check configuration directory
    config_dir = drone_config_manager.config_dir
    config_file = drone_config_manager.config_file
    
    print(f"Configuration directory: {config_dir}")
    print(f"Configuration file: {config_file}")
    
    # Directory existence
    print(f"\nChecking configuration directory...")
    if os.path.exists(config_dir):
        print(f"✓ Directory exists: {config_dir}")
    else:
        print(f"✗ Directory does not exist: {config_dir}")
        print(f"  Attempting to create...")
        try:
            os.makedirs(config_dir, exist_ok=True)
            print(f"✓ Successfully created directory: {config_dir}")
        except Exception as e:
            print(f"✗ Failed to create directory: {str(e)}")
    
    # Directory permissions
    if os.path.exists(config_dir):
        print(f"\nChecking directory permissions...")
        test_file = os.path.join(config_dir, ".test_write")
        try:
            with open(test_file, 'w') as f:
                f.write("test")
            os.remove(test_file)
            print(f"✓ Directory is writable: {config_dir}")
        except Exception as e:
            print(f"✗ Directory is not writable: {str(e)}")
            print(f"  Please check permissions for: {config_dir}")
    
    # Configuration file
    print(f"\nChecking configuration file...")
    if os.path.exists(config_file):
        print(f"✓ Configuration file exists: {config_file}")
        try:
            with open(config_file, 'r') as f:
                import json
                configs = json.load(f)
                print(f"✓ Configuration file is valid JSON")
                print(f"  Contains {len(configs)} drone configurations")
        except json.JSONDecodeError as e:
            print(f"✗ Configuration file contains invalid JSON: {str(e)}")
            print(f"  You may need to delete or fix the file: {config_file}")
        except Exception as e:
            print(f"✗ Error reading configuration file: {str(e)}")
    else:
        print(f"✗ Configuration file does not exist: {config_file}")
        print(f"  This is normal if you haven't added any drones yet")
        print(f"  Attempting to create an empty configuration file...")
        try:
            with open(config_file, 'w') as f:
                f.write("{}")
            print(f"✓ Successfully created empty configuration file: {config_file}")
        except Exception as e:
            print(f"✗ Failed to create configuration file: {str(e)}")
    
    # Testing adding a dummy configuration
    print(f"\nTesting configuration save functionality...")
    test_name = "_test_drone_"
    success = drone_config_manager.add_drone(test_name, "127.0.0.1", "test_user")
    if success:
        print(f"✓ Successfully added test configuration")
        drone_config_manager.remove_drone(test_name)
        print(f"✓ Successfully removed test configuration")
    else:
        print(f"✗ Failed to add test configuration")
        print(f"  This indicates a problem with saving configurations")
    
    # Summary
    print("\nTroubleshooting Summary:")
    print("1. If directory issues were reported, fix permissions or create the directory manually")
    print("2. If file issues were reported, check if the file is corrupted or has wrong permissions")
    print("3. If the test configuration failed, there may be a deeper issue with the code or system")
    print("\nYou can try adding a drone manually with: python setup_drone.py --add-manual")

def setup_argparse():
    """Set up the argument parser."""
    parser = argparse.ArgumentParser(
        description="BSTI Drone Connection Setup Tool",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--wizard", action="store_true", help="Run the drone setup wizard")
    group.add_argument("--list", action="store_true", help="List all configured drones")
    group.add_argument("--test", metavar="DRONE_NAME", help="Test connection to a drone")
    group.add_argument("--delete", metavar="DRONE_NAME", help="Delete a drone configuration")
    group.add_argument("--add-manual", action="store_true", help="Add a drone manually (bypass connection test)")
    group.add_argument("--troubleshoot", action="store_true", help="Run troubleshooting diagnostics")
    
    # Global options
    parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
    
    return parser

def main():
    """Main function."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    # Configure verbose logging if requested
    if args.verbose:
        import logging
        log.set_level(logging.DEBUG)
        print("Verbose logging enabled")
    
    try:
        if args.wizard:
            run_wizard()
        elif args.list:
            list_drones()
        elif args.test:
            test_drone(args.test)
        elif args.delete:
            delete_drone(args.delete)
        elif args.add_manual:
            add_drone_manually()
        elif args.troubleshoot:
            run_troubleshoot()
    except Exception as e:
        print(f"\nError: {str(e)}")
        if args.verbose:
            print("\nStack trace:")
            traceback.print_exc()
        print("\nFor troubleshooting, run: python setup_drone.py --troubleshoot")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {str(e)}")
        sys.exit(1) 