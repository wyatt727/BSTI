#!/usr/bin/env python3
"""
Help script for BSTI Refactored.
Displays command-line options and examples.
"""

import argparse
import sys

def show_help():
    """Show help information for bsti_refactored.py"""
    print("""
BSTI - BlackStack Testing Interface (Refactored)
================================================

This is the help guide for the refactored BSTI application.

BASIC USAGE:
    python bsti_refactored.py                       # Run the full GUI application
    python bsti_refactored.py --safe-mode           # Run with minimal UI for troubleshooting
    python bsti_refactored.py --plugin-manager      # Run the plugin manager in interactive mode

CORE OPTIONS:
    --safe-mode                 Run with minimal UI for troubleshooting

PLUGIN MANAGER OPTIONS:
    --plugin-manager            Run the plugin manager
    --csv-file FILE.csv         Path to the CSV file with findings
    --action ACTION             Action to perform with the plugin manager
    --category CATEGORY         Category name for add_plugin and remove_plugin actions
    --plugin-ids ID1,ID2,...    Comma-separated list of plugin IDs for add_plugin/remove_plugin

PLUGIN MANAGER ACTIONS:
    select_csv                  Select a CSV file to work with
    simulate                    Simulate which findings will be merged
    add_plugin                  Add plugins to a specific category
    remove_plugin               Remove plugins from a specific category
    view_changes                View pending changes made during the session
    write_changes               Save pending changes to the configuration file
    clear_changes               Discard pending changes

EXAMPLES:
    # Simulate findings with a specific CSV file
    python bsti_refactored.py --plugin-manager --csv-file findings.csv --action simulate

    # Add plugins to a category
    python bsti_refactored.py --plugin-manager --action add_plugin --category "SSH" --plugin-ids "10881,10862"

For more detailed documentation, see:
- docs/bsti_refactored_usage.md   (Full usage guide)
- docs/plugin_manager.md          (Plugin manager documentation)
- bsti_refactored_commands.md     (Quick command reference)
- man -l bsti-refactored.1        (Man page)
""")

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--version', action='store_true', help='Show version')
    
    args, _ = parser.parse_known_args()
    
    if args.version:
        print("BSTI Refactored v1.0.0")
        return
        
    show_help()

if __name__ == "__main__":
    main() 