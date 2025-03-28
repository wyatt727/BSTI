---
layout: default
title: BSTI Refactored Usage
nav_order: 2
---

# BSTI Refactored Usage Guide

BSTI (BlackStack Testing Interface) Refactored is the new entry point for the BSTI application, designed to provide a more modular and maintainable codebase with enhanced functionality.

## Command Line Usage

The `bsti_refactored.py` script can be run in different modes depending on your needs:

```bash
# Run the full GUI application
python bsti_refactored.py

# Run the plugin manager in interactive mode
python bsti_refactored.py --plugin-manager

# Run the plugin manager with a specific CSV file
python bsti_refactored.py --plugin-manager --csv-file FILE.csv

# Simulate findings with the plugin manager
python bsti_refactored.py --plugin-manager --action simulate --csv-file FILE.csv
```

## Available Command Line Options

### Core Options

| Option | Description |
|--------|-------------|
| `--plugin-manager` | Run the plugin manager instead of the main GUI application |
| `--safe-mode` | Run with minimal UI for troubleshooting when the normal mode encounters errors |

### Plugin Manager Options

| Option | Description |
|--------|-------------|
| `--csv-file FILE.csv` | Path to the CSV file containing findings for the plugin manager |
| `--action ACTION` | Action to perform with the plugin manager (see actions below) |
| `--category CATEGORY` | Category name for adding or removing plugins |
| `--plugin-ids ID1,ID2` | Comma-separated list of plugin IDs for add_plugin and remove_plugin actions |

### Plugin Manager Actions

| Action | Description |
|--------|-------------|
| `select_csv` | Select a CSV file to work with |
| `simulate` | Simulate which findings will be merged based on current configuration |
| `add_plugin` | Add plugins to a specific category |
| `remove_plugin` | Remove plugins from a specific category |
| `view_changes` | View pending changes made during the current session |
| `write_changes` | Save pending changes to the configuration file |
| `clear_changes` | Discard pending changes |

## GUI Mode

When running BSTI Refactored without any command-line arguments, it launches the full GUI application with all available tabs and features.

```bash
python bsti_refactored.py
```

The GUI provides access to all BSTI functionality through an intuitive tabbed interface, including:

- Home tab for drone connection status and management
- Module editor for creating and executing modules
- View logs for module output
- Mobile testing tools
- NMB (Nessus Management Bridge) integration
- Plugin Manager for PlexTrac integration

## Plugin Manager Mode

The Plugin Manager allows you to manage how findings are categorized and merged in the PlexTrac report generation process. This tool helps you properly categorize findings from Nessus scans before importing them into PlexTrac.

### Interactive Mode

```bash
python bsti_refactored.py --plugin-manager
```

This launches the Plugin Manager in interactive mode, allowing you to:
- Select a CSV file containing findings
- Simulate which findings will be merged based on current configuration
- Add or remove plugins from categories
- View and manage pending changes

### Non-Interactive Mode

You can also use the Plugin Manager in non-interactive mode by specifying actions and parameters:

```bash
# Simulate findings with a specific CSV file
python bsti_refactored.py --plugin-manager --csv-file path/to/findings.csv --action simulate

# Add plugins to a category
python bsti_refactored.py --plugin-manager --action add_plugin --category "SSL" --plugin-ids "42873,10863"

# Remove plugins from a category
python bsti_refactored.py --plugin-manager --action remove_plugin --category "SSL" --plugin-ids "42873"

# View pending changes
python bsti_refactored.py --plugin-manager --action view_changes

# Write pending changes to the configuration file
python bsti_refactored.py --plugin-manager --action write_changes

# Clear pending changes
python bsti_refactored.py --plugin-manager --action clear_changes
```

## Workflow Examples

### Basic GUI Usage

1. Launch the full application:
   ```bash
   python bsti_refactored.py
   ```
2. Connect to a drone using the connection dropdown in the status bar
3. Navigate through the tabs to access different functionality

### Using the Plugin Manager to Prepare Findings

1. Run a Nessus scan and export the results as a CSV file
2. Launch the Plugin Manager:
   ```bash
   python bsti_refactored.py --plugin-manager
   ```
3. Select the CSV file when prompted
4. Simulate findings to see which will be merged
5. Add individual plugins to appropriate categories as needed
6. Write changes to the configuration file
7. Exit the Plugin Manager
8. Use the main GUI application to export findings to PlexTrac

### Automating Plugin Management

For regular workflows or scripting, you can automate plugin management:

```bash
# Add SSH-related plugins to the SSH category
python bsti_refactored.py --plugin-manager --action add_plugin --category "SSH" --plugin-ids "10881,10862,90317"

# Write the changes to the configuration
python bsti_refactored.py --plugin-manager --action write_changes
```

## Troubleshooting

If the application fails to start normally, you can use safe mode:

```bash
python bsti_refactored.py --safe-mode
```

This launches a simplified UI that can help diagnose issues with the full application.

Common issues:
- Make sure all dependencies are installed (see requirements.txt)
- Check that temp directory exists and is writable
- For plugin manager issues, verify that N2P_config.json exists in the current directory

## Additional Resources

- For more information on developing modules, see [DEVGUIDE.md](../DEVGUIDE.md)
- For general usage of BSTI, see [Usage.md](Usage.md)
- For plugin manager details, see [plugin_manager.md](plugin_manager.md) 