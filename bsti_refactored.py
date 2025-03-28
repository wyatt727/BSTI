#!/usr/bin/env python3
"""
BSTI - BlackStack Testing Interface (Refactored)

This is the entry point for the refactored BSTI application.

Command line usage:
    python bsti_refactored.py                          # Run the full GUI application
    python bsti_refactored.py --safe-mode              # Run with minimal UI for troubleshooting
    python bsti_refactored.py --plugin-manager         # Run the plugin manager in interactive mode
    python bsti_refactored.py --plugin-manager --csv-file FILE.csv  # Run with a specific CSV file
    python bsti_refactored.py --plugin-manager --action simulate --csv-file FILE.csv  # Simulate findings 

Core Options:
    --safe-mode              Run with minimal UI for troubleshooting

Plugin Manager CLI Options:
    --plugin-manager          Run the plugin manager
    --csv-file FILE.csv       Path to the CSV file
    --action ACTION           Action to perform: select_csv, simulate, add_plugin,
                              remove_plugin, view_changes, write_changes, clear_changes
    --category CATEGORY       Category name (for add_plugin and remove_plugin actions)
    --plugin-ids ID1,ID2      Comma-separated list of plugin IDs (for add_plugin and remove_plugin)
"""

import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Create temp directory if it doesn't exist
temp_dir = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'temp')
os.makedirs(temp_dir, exist_ok=True)

# Import the main function from the application
from src.__main__ import main

if __name__ == "__main__":
    # Forward all command-line arguments to the main function
    main() 