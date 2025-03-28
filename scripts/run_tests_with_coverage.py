#!/usr/bin/env python3
"""
Script to run tests with coverage reporting.

This script runs pytest with coverage reporting and generates HTML and XML reports.
"""
import os
import sys
import subprocess
import argparse


def run_tests_with_coverage(args):
    """
    Run tests with coverage reporting.
    
    Args:
        args: Command line arguments.
    
    Returns:
        int: Exit code from the test run.
    """
    # Ensure we're in the project root directory
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    os.chdir(project_root)
    
    # Base command
    cmd = ["pytest"]
    
    # Add coverage
    cmd.extend(["--cov=bsti_nessus", "--cov-report=term", "--cov-report=html"])
    
    # Generate XML report for CI tools if requested
    if args.xml:
        cmd.append("--cov-report=xml")
    
    # Add verbose flag if requested
    if args.verbose:
        cmd.append("-v")
    
    # Add test selection options
    if args.unit_only:
        cmd.append("-m")
        cmd.append("unit")
    elif args.integration_only:
        cmd.append("-m")
        cmd.append("integration")
    
    # Filter by keywords
    if args.keywords:
        cmd.append("-k")
        cmd.append(args.keywords)
    
    # Specify test paths if provided
    if args.test_paths:
        cmd.extend(args.test_paths)
    
    # Run the command
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd)
    
    # Report coverage location
    print("\nCoverage HTML report generated at:")
    print(f"{os.path.join(project_root, 'coverage_html_report', 'index.html')}")
    
    if args.xml:
        print("\nCoverage XML report generated at:")
        print(f"{os.path.join(project_root, 'coverage.xml')}")
    
    return result.returncode


def parse_arguments():
    """
    Parse command line arguments.
    
    Returns:
        argparse.Namespace: Parsed arguments.
    """
    parser = argparse.ArgumentParser(description="Run tests with coverage reporting")
    
    # Test selection options
    selection = parser.add_argument_group("Test Selection")
    selection.add_argument("--unit-only", action="store_true", 
                          help="Run only unit tests")
    selection.add_argument("--integration-only", action="store_true", 
                          help="Run only integration tests")
    selection.add_argument("-k", "--keywords", 
                          help="Only run tests matching the given substring expression")
    selection.add_argument("test_paths", nargs="*", 
                          help="Specific test files or directories to run")
    
    # Output options
    output = parser.add_argument_group("Output Options")
    output.add_argument("-v", "--verbose", action="store_true", 
                       help="Increase verbosity")
    output.add_argument("--xml", action="store_true", 
                       help="Generate XML coverage report for CI tools")
    
    return parser.parse_args()


def main():
    """
    Main entry point.
    """
    args = parse_arguments()
    return run_tests_with_coverage(args)


if __name__ == "__main__":
    sys.exit(main()) 