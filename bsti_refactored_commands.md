# BSTI Refactored - Command Reference

## Basic Usage

```bash
# Run the full GUI application
python bsti_refactored.py

# Run in safe mode (minimal UI for troubleshooting)
python bsti_refactored.py --safe-mode
```

## Plugin Manager Commands

```bash
# Run plugin manager in interactive mode
python bsti_refactored.py --plugin-manager

# Select a specific CSV file with findings
python bsti_refactored.py --plugin-manager --csv-file path/to/nessus_findings.csv

# Simulate findings with a specific CSV file
python bsti_refactored.py --plugin-manager --action simulate --csv-file path/to/nessus_findings.csv

# Add plugins to a category
python bsti_refactored.py --plugin-manager --action add_plugin --category "SSH" --plugin-ids "10881,10862"

# Remove plugins from a category
python bsti_refactored.py --plugin-manager --action remove_plugin --category "SSH" --plugin-ids "10881"

# View pending changes
python bsti_refactored.py --plugin-manager --action view_changes

# Write pending changes to the configuration
python bsti_refactored.py --plugin-manager --action write_changes

# Clear all pending changes
python bsti_refactored.py --plugin-manager --action clear_changes
```

## Common Workflows

### Nessus Scan to PlexTrac Workflow

1. Run Nessus scan and export results as CSV
2. View & simulate finding categorization:
   ```bash
   python bsti_refactored.py --plugin-manager --csv-file nessus_export.csv --action simulate
   ```
3. Add plugins to appropriate categories:
   ```bash
   python bsti_refactored.py --plugin-manager --action add_plugin --category "SSL/TLS" --plugin-ids "42873,10863"
   ```
4. Save changes:
   ```bash
   python bsti_refactored.py --plugin-manager --action write_changes
   ```
5. Launch full GUI for PlexTrac export:
   ```bash
   python bsti_refactored.py
   ```

For complete documentation, see the full [usage guide](docs/bsti_refactored_usage.md). 