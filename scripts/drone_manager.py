#!/usr/bin/env python3
import argparse
import sys
import os
import getpass
from scripts.drone_config import drone_config_manager
from scripts.logging_config import log

def setup_argparse():
    """Set up the argument parser for the drone manager."""
    parser = argparse.ArgumentParser(
        description="BSTI Drone Connection Manager",
        formatter_class=argparse.RawTextHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Command to execute")
    
    # List command
    list_parser = subparsers.add_parser("list", help="List all drone configurations")
    
    # Add command
    add_parser = subparsers.add_parser("add", help="Add a new drone configuration")
    add_parser.add_argument("name", help="Name for the drone configuration")
    add_parser.add_argument("hostname", help="Hostname or IP address of the drone")
    add_parser.add_argument("username", help="Username for the drone")
    add_parser.add_argument("--password", help="Password for the drone (will prompt if not provided)")
    add_parser.add_argument("--save-password", action="store_true", 
                           help="Save password (WARNING: stored in plain text)")
    
    # Remove command
    remove_parser = subparsers.add_parser("remove", help="Remove a drone configuration")
    remove_parser.add_argument("name", help="Name of the drone configuration to remove")
    
    # Test command
    test_parser = subparsers.add_parser("test", help="Test connection to a drone")
    test_parser.add_argument("name", help="Name of the drone configuration to test")
    test_parser.add_argument("--password", help="Password for the drone (will prompt if not saved)")
    
    # Wizard command
    wizard_parser = subparsers.add_parser("wizard", help="Interactive setup wizard")
    
    return parser

def handle_list(args):
    """Handle the list command."""
    drone_names = drone_config_manager.get_drone_names()
    
    if not drone_names:
        print("No drone configurations found.")
        return
    
    print("\nAvailable Drone Configurations:")
    print("==============================")
    
    for name in drone_names:
        config = drone_config_manager.get_drone(name)
        password_saved = "Yes" if "password" in config else "No"
        print(f"Name: {name}")
        print(f"  Hostname: {config['hostname']}")
        print(f"  Username: {config['username']}")
        print(f"  Password Saved: {password_saved}")
        print()

def handle_add(args):
    """Handle the add command."""
    password = args.password
    
    # Prompt for password if not provided
    if not password:
        password = getpass.getpass(f"Enter password for {args.hostname}: ")
    
    success = drone_config_manager.add_drone(
        args.name, args.hostname, args.username, 
        password, args.save_password
    )
    
    if success:
        print(f"Drone configuration '{args.name}' added successfully.")
    else:
        print("Failed to add drone configuration.")

def handle_remove(args):
    """Handle the remove command."""
    success = drone_config_manager.remove_drone(args.name)
    
    if success:
        print(f"Drone configuration '{args.name}' removed successfully.")
    else:
        print(f"Failed to remove drone configuration '{args.name}'.")

def handle_test(args):
    """Handle the test command."""
    config = drone_config_manager.get_drone(args.name)
    
    if not config:
        print(f"No configuration found for drone '{args.name}'.")
        return
    
    password = args.password
    
    # If password not provided and not saved, prompt for it
    if not password and "password" not in config:
        password = getpass.getpass(f"Enter password for {config['hostname']}: ")
    
    success = drone_config_manager.test_connection(
        name=args.name, password=password
    )
    
    if success:
        print(f"Successfully connected to drone '{args.name}'.")
    else:
        print(f"Failed to connect to drone '{args.name}'.")

def handle_wizard(args):
    """Handle the wizard command."""
    result = drone_config_manager.interactive_setup()
    
    if result:
        print(f"\nDrone configuration '{result['name']}' set up successfully.")
    else:
        print("\nDrone setup was cancelled or failed.")

def main():
    """Main function for the drone manager."""
    parser = setup_argparse()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    # Execute the appropriate command handler
    if args.command == "list":
        handle_list(args)
    elif args.command == "add":
        handle_add(args)
    elif args.command == "remove":
        handle_remove(args)
    elif args.command == "test":
        handle_test(args)
    elif args.command == "wizard":
        handle_wizard(args)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nOperation cancelled.")
        sys.exit(1)
    except Exception as e:
        log.error(f"Error: {str(e)}")
        sys.exit(1) 