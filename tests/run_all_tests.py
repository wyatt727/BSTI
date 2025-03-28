#!/usr/bin/env python3
"""
Script to run all tests in the BSTI project
"""

import os
import sys
import subprocess
import argparse
from datetime import datetime

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run all BSTI tests')
    parser.add_argument('--html', action='store_true', help='Generate HTML coverage report')
    parser.add_argument('--xml', action='store_true', help='Generate XML coverage report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Run tests in verbose mode')
    parser.add_argument('--test-file', '-t', help='Run tests only for a specific file')
    parser.add_argument('--skip-nmb', action='store_true', help='Skip NMB tests')
    parser.add_argument('--skip-ui', action='store_true', help='Skip UI component tests')
    parser.add_argument('--skip-module', action='store_true', help='Skip module system tests')
    return parser.parse_args()

def run_tests(args):
    """Run the tests based on the specified arguments."""
    # Get the project root directory
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(root_dir)
    
    # Build the pytest command
    pytest_cmd = ["python", "-m", "pytest"]
    
    if args.verbose:
        pytest_cmd.append("-v")
    
    if args.test_file:
        pytest_cmd.append(args.test_file)
    else:
        # Add specific test files or patterns
        test_files = []
        
        if not args.skip_nmb:
            test_files.append("tests/test_nmb.py")
        
        if not args.skip_ui:
            test_files.extend([
                "tests/test_home_tab.py",
                "tests/test_module_editor_tab.py",
                "tests/test_view_logs_tab.py"
            ])
        
        if not args.skip_module:
            test_files.append("tests/test_module_system.py")
        
        # Add plugin manager tests if they exist
        if os.path.exists(os.path.join(root_dir, "tests/test_plugin_manager.py")):
            test_files.append("tests/test_plugin_manager.py")
            
        # Add BSTI general tests if they exist
        if os.path.exists(os.path.join(root_dir, "tests/bsti_test.py")):
            test_files.append("tests/bsti_test.py")
        
        pytest_cmd.extend(test_files)
    
    # Add coverage options if requested
    if args.html or args.xml:
        pytest_cmd.append("--cov=BSTI")
        
        if args.html:
            pytest_cmd.append("--cov-report=html")
        
        if args.xml:
            pytest_cmd.append("--cov-report=xml")
    
    # Run the command
    print(f"Running command: {' '.join(pytest_cmd)}")
    return subprocess.run(pytest_cmd).returncode

def main():
    """Main function to run all tests."""
    args = parse_args()
    
    # Print header
    print("=" * 80)
    print(f"Running BSTI Tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    
    exit_code = run_tests(args)
    
    # Print summary
    print("\n" + "=" * 80)
    if exit_code == 0:
        print("✅ All tests passed successfully!")
    else:
        print("❌ Some tests failed!")
    print("=" * 80)
    
    return exit_code

if __name__ == '__main__':
    sys.exit(main()) 