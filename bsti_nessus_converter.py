#!/usr/bin/env python3
"""
BSTI Nessus to Plextrac Converter

This is the main entry point for the BSTI Nessus to Plextrac Converter tool.
It handles converting Nessus CSV files to Plextrac format and uploading them.
"""
import sys
import os

# Ensure the package is in the path
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.append(current_dir)

from bsti_nessus.core.cli import main

if __name__ == "__main__":
    main() 