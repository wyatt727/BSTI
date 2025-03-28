#!/usr/bin/env python3
"""
BSTI Installation Verification Script

Original BSTI implementation by Connor Fancy.
This script is part of the refactored version of BSTI.

This script performs a series of checks to verify that the BSTI toolset
is correctly installed and all dependencies are available.
"""

import sys
import os
import platform
import importlib
import subprocess
from importlib.util import find_spec
import json

# ANSI color codes for output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(text):
    """Print a formatted header."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}=== {text} ==={Colors.ENDC}\n")

def print_success(text):
    """Print a success message."""
    print(f"{Colors.GREEN}✓ {text}{Colors.ENDC}")

def print_warning(text):
    """Print a warning message."""
    print(f"{Colors.YELLOW}⚠ {text}{Colors.ENDC}")

def print_error(text):
    """Print an error message."""
    print(f"{Colors.RED}✗ {text}{Colors.ENDC}")

def check_python_version():
    """Check if Python version is 3.8+."""
    print_header("Checking Python Version")
    
    version = sys.version_info
    if version.major < 3 or (version.major == 3 and version.minor < 8):
        print_error(f"Python version {version.major}.{version.minor}.{version.micro} detected.")
        print_error("BSTI requires Python 3.8 or higher.")
        return False
    else:
        print_success(f"Python {version.major}.{version.minor}.{version.micro} detected (meets requirements).")
        return True

def check_virtual_environment():
    """Check if running in a virtual environment."""
    print_header("Checking Virtual Environment")
    
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print_success("Running in a virtual environment.")
        return True
    else:
        print_warning("Not running in a virtual environment.")
        print_warning("Using a virtual environment is recommended for BSTI.")
        return None  # Not a critical error

def check_dependencies():
    """Check if all required dependencies are installed."""
    print_header("Checking Dependencies")
    
    # Core dependencies to check
    dependencies = [
        "requests", "colorama", "tqdm", "cryptography", "keyring",
        "rich", "paramiko", "PyQt5", "htmlwebshot", "scp", "pandas",
        "bcrypt", "colorlog", "py7zr", "filelock", "pretty_errors",
        "bs4", "toml", "pytest"
    ]
    
    success_count = 0
    failure_count = 0
    
    for dep in dependencies:
        try:
            importlib.import_module(dep)
            print_success(f"{dep} is installed.")
            success_count += 1
        except ImportError:
            print_error(f"{dep} is NOT installed.")
            failure_count += 1
    
    print(f"\nDependency check complete: {success_count} packages installed, {failure_count} missing.")
    
    if failure_count > 0:
        print_warning("Some dependencies are missing. Try running:")
        print("  pip install -r requirements.txt")
        return False
    else:
        return True

def check_external_tools():
    """Check if required external tools are installed."""
    print_header("Checking External Tools")
    
    # List of external tools to check with their commands
    tools = {
        "wkhtmltopdf": "wkhtmltopdf --version"
    }
    
    success_count = 0
    failure_count = 0
    
    for tool, command in tools.items():
        try:
            result = subprocess.run(command.split(), capture_output=True, text=True)
            if result.returncode == 0:
                print_success(f"{tool} is installed: {result.stdout.strip()}")
                success_count += 1
            else:
                print_error(f"{tool} returned an error: {result.stderr.strip()}")
                failure_count += 1
        except FileNotFoundError:
            print_error(f"{tool} is NOT installed or not in PATH.")
            failure_count += 1
    
    if failure_count > 0:
        return False
    else:
        return True

def check_bsti_files():
    """Check if key BSTI files exist."""
    print_header("Checking BSTI Files")
    
    files_to_check = [
        "bsti_refactored.py",
        "nmb.py",
        "setup_drone.py",
        "requirements.txt"
    ]
    
    success_count = 0
    failure_count = 0
    
    for file in files_to_check:
        if os.path.exists(file):
            print_success(f"{file} exists.")
            success_count += 1
        else:
            print_error(f"{file} is missing.")
            failure_count += 1
    
    if failure_count > 0:
        print_warning("Some BSTI files are missing. Make sure you're in the correct directory.")
        return False
    else:
        return True

def check_drone_config():
    """Check if drone configuration exists."""
    print_header("Checking Drone Configuration")
    
    # Determine config directory based on platform
    if platform.system() == "Windows":
        config_dir = os.path.join(os.path.expanduser("~"), ".bsti")
    else:
        config_dir = os.path.join(os.path.expanduser("~"), ".bsti")
    
    config_file = os.path.join(config_dir, "drone_config.json")
    
    if os.path.exists(config_dir):
        print_success(f"Configuration directory exists: {config_dir}")
    else:
        print_warning(f"Configuration directory doesn't exist: {config_dir}")
        print_warning("You can create it by running: python setup_drone.py --wizard")
        return None  # Not a critical error
    
    if os.path.exists(config_file):
        print_success(f"Drone configuration file exists: {config_file}")
        
        # Check if the file is valid JSON and has drone configurations
        try:
            with open(config_file, 'r') as f:
                config = json.load(f)
                if config:
                    print_success(f"Found {len(config)} drone configuration(s).")
                else:
                    print_warning("Drone configuration file is empty.")
        except json.JSONDecodeError:
            print_error("Drone configuration file is not valid JSON.")
        except Exception as e:
            print_error(f"Error reading drone configuration: {str(e)}")
    else:
        print_warning(f"Drone configuration file doesn't exist: {config_file}")
        print_warning("You can create it by running: python setup_drone.py --wizard")
    
    return None  # Not a critical error

def main():
    """Main function to run all checks."""
    print(f"{Colors.BOLD}{Colors.BLUE}BSTI Installation Verification{Colors.ENDC}")
    print(f"Running on {platform.system()} {platform.release()} ({os.name})")
    
    checks = [
        ("Python Version", check_python_version),
        ("Virtual Environment", check_virtual_environment),
        ("Dependencies", check_dependencies),
        ("External Tools", check_external_tools),
        ("BSTI Files", check_bsti_files),
        ("Drone Configuration", check_drone_config)
    ]
    
    results = {}
    
    for name, check_func in checks:
        results[name] = check_func()
    
    # Print summary
    print_header("Summary")
    
    all_critical_checks_passed = True
    
    for name, result in results.items():
        if result is True:
            print_success(f"{name}: Passed")
        elif result is False:
            print_error(f"{name}: Failed")
            if name != "Virtual Environment" and name != "Drone Configuration":
                all_critical_checks_passed = False
        elif result is None:
            print_warning(f"{name}: Warning (not critical)")
    
    if all_critical_checks_passed:
        print(f"\n{Colors.GREEN}{Colors.BOLD}All critical checks passed!{Colors.ENDC}")
        print("BSTI should be ready to use. Try running:")
        print("  python bsti_refactored.py --help")
        print("  python nmb.py --help")
        print("  python setup_drone.py --wizard")
        return 0
    else:
        print(f"\n{Colors.RED}{Colors.BOLD}Some critical checks failed.{Colors.ENDC}")
        print("Please fix the issues before using BSTI.")
        print("See the detailed installation guide: README_INSTALL.md")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 