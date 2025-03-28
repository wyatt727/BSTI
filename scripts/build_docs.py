#!/usr/bin/env python3
"""
Build Sphinx documentation for BSTI Nessus.

This script automates the process of building the Sphinx documentation.
It can be used to build HTML documentation or to check for documentation errors.
"""
import argparse
import os
import subprocess
import sys
from pathlib import Path


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Build Sphinx documentation")
    parser.add_argument(
        "--html", 
        action="store_true", 
        help="Build HTML documentation"
    )
    parser.add_argument(
        "--check", 
        action="store_true", 
        help="Check documentation for errors"
    )
    parser.add_argument(
        "--clean", 
        action="store_true", 
        help="Clean build directory before building"
    )
    return parser.parse_args()


def get_project_root():
    """Get the project root directory."""
    script_dir = Path(__file__).resolve().parent
    return script_dir.parent


def build_html_docs(clean=False):
    """
    Build HTML documentation.
    
    Args:
        clean: Whether to clean the build directory first
    
    Returns:
        True if successful, False otherwise
    """
    project_root = get_project_root()
    docs_dir = project_root / "docs"
    source_dir = docs_dir / "source"
    build_dir = docs_dir / "build" / "html"
    
    # Ensure directories exist
    os.makedirs(source_dir, exist_ok=True)
    os.makedirs(build_dir, exist_ok=True)
    
    # Clean build directory if requested
    if clean and build_dir.exists():
        print(f"Cleaning build directory: {build_dir}")
        for item in build_dir.glob("*"):
            if item.is_file():
                item.unlink()
            elif item.is_dir():
                for subitem in item.glob("**/*"):
                    if subitem.is_file():
                        subitem.unlink()
                item.rmdir()
    
    # Build HTML documentation
    print(f"Building HTML documentation in {build_dir}")
    result = subprocess.run(
        [
            "sphinx-build",
            "-b", "html",
            str(source_dir),
            str(build_dir)
        ],
        cwd=str(project_root)
    )
    
    if result.returncode == 0:
        print(f"Documentation built successfully. Output in {build_dir}")
        return True
    else:
        print("Error building documentation", file=sys.stderr)
        return False


def check_docs():
    """
    Check documentation for errors.
    
    Returns:
        True if no errors, False otherwise
    """
    project_root = get_project_root()
    docs_dir = project_root / "docs"
    source_dir = docs_dir / "source"
    
    # Run sphinx-build with -n (nitpicky) and -W (warnings as errors)
    print("Checking documentation for errors")
    result = subprocess.run(
        [
            "sphinx-build",
            "-b", "html",
            "-n", "-W",  # Nitpicky mode, treat warnings as errors
            str(source_dir),
            str(docs_dir / "build" / "check")
        ],
        cwd=str(project_root)
    )
    
    if result.returncode == 0:
        print("Documentation check passed.")
        return True
    else:
        print("Documentation check failed. Please fix the errors.", file=sys.stderr)
        return False


def main():
    """Main function."""
    args = parse_args()
    
    # Default to building HTML if no action specified
    if not (args.html or args.check):
        args.html = True
    
    success = True
    if args.html:
        success = build_html_docs(clean=args.clean) and success
    if args.check:
        success = check_docs() and success
    
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main()) 