# Plugin Manager for PlexTrac

The Plugin Manager allows you to manage how findings are categorized and merged in the PlexTrac report generation process. This tool helps you properly categorize findings from Nessus scans before importing them into PlexTrac.

## Overview

The Plugin Manager provides the following functionality:

- Add plugins to categories for proper finding organization in PlexTrac
- Simulate which findings will be merged and which will remain individual
- View, write, and clear pending changes to the configuration
- Remove plugins from categories
- Interact with the plugin manager through both GUI and CLI interfaces

## Usage

### GUI Mode

You can access the Plugin Manager through the BSTI application's PlexTrac tab:

1. Launch BSTI: `python bsti_refactored.py`
2. Navigate to the "PlexTrac" tab
3. Click on the "Plugin Manager" dropdown button
4. Select the desired action from the dropdown menu:
   - Run Interactive Mode: Open the full interactive plugin manager console
   - Select CSV File: Choose a CSV file containing findings
   - Simulate Findings: Show which findings will be merged based on current configuration
   - Add Plugin to Category: Add individual plugins to a specific category
   - View Pending Changes: Display changes made during this session
   - Write Changes to Config: Save changes to the configuration file
   - Clear Pending Changes: Discard changes made during this session

### CLI Mode

The Plugin Manager can be used directly from the command line for automation and scripting:

```bash
# Run the plugin manager in interactive mode
python bsti_refactored.py --plugin-manager

# Select a CSV file and simulate findings
python bsti_refactored.py --plugin-manager --csv-file path/to/findings.csv --action simulate

# Add a plugin to a category
python bsti_refactored.py --plugin-manager --csv-file path/to/findings.csv --action add_plugin --category "SSL" --plugin-ids "42873"

# Remove a plugin from a category
python bsti_refactored.py --plugin-manager --action remove_plugin --category "SSL" --plugin-ids "42873"

# View pending changes
python bsti_refactored.py --plugin-manager --action view_changes

# Write changes to the configuration file
python bsti_refactored.py --plugin-manager --action write_changes

# Clear pending changes
python bsti_refactored.py --plugin-manager --action clear_changes
```

## Available CLI Options

| Option | Description |
|--------|-------------|
| `--plugin-manager` | Run the plugin manager |
| `--csv-file FILE.csv` | Path to the CSV file containing findings |
| `--action ACTION` | Action to perform: `select_csv`, `simulate`, `add_plugin`, `remove_plugin`, `view_changes`, `write_changes`, `clear_changes` |
| `--category CATEGORY` | Category name (for `add_plugin` and `remove_plugin` actions) |
| `--plugin-ids ID1,ID2` | Comma-separated list of plugin IDs (for `add_plugin` and `remove_plugin` actions) |

## Workflow Example

A typical workflow might look like:

1. Run a Nessus scan and export the results as a CSV file
2. Use the Plugin Manager to simulate findings and identify which will be merged
3. Add individual plugins to appropriate categories as needed
4. Write the changes to the configuration file
5. Use the PlexTrac integration to export the findings with the updated configuration

## Troubleshooting

If you encounter issues:

- Make sure your CSV file is properly formatted with the required columns (Plugin ID, Name, Risk, etc.)
- Check that the N2P_config.json file exists and is accessible
- Verify that you have the necessary permissions to write to the configuration file
- If using CLI mode, ensure that all required parameters are provided for the action

## Notes

- Changes made with the Plugin Manager are not applied until you explicitly write them to the configuration file
- The simulation is based on the current state of both the CSV file and the configuration file
- The Plugin Manager only affects how findings are categorized and merged; it does not modify the finding data itself 