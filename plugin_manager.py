# Title: Plugin Manager
# Version: 1.0.0
# Author: Connor Fancy

import json
import csv
from helpers.custom_logger import log
import os
import argparse
import atexit
import sys
import tkinter as tk
from tkinter import filedialog


class PluginManager:
    # Constants
    TEMP_FILE = "temp.json"
    IGNORE_PLUGIN = "11213"
    IGNORE_INFORMATIONAL = "None"

    def __init__(self, config_path, csv_path=None):
        self.config_path = config_path
        self.csv_path = csv_path
        self.config = self.read_json_file(self.config_path)
        self.findings = []
        self.temp_changes = {}
        
        # Load temp changes from file if it exists
        if os.path.exists(self.TEMP_FILE):
            try:
                with open(self.TEMP_FILE, 'r') as f:
                    self.temp_changes = json.load(f)
                    log.info(f"Loaded {len(self.temp_changes)} temporary changes from {self.TEMP_FILE}")
            except Exception as e:
                log.warning(f"Error loading temporary changes: {str(e)}")
        
        if csv_path:
            self.load_csv(csv_path)
            
        atexit.register(self.cleanup)

    def load_csv(self, csv_path):
        """Load findings from the given CSV file."""
        self.csv_path = csv_path
        self.findings = self.read_findings_csv(self.csv_path)
        log.success(f"Loaded findings from {self.csv_path}")
        return True

    def select_csv_file(self):
        """Open a file dialog to select a CSV file."""
        # Create a root window and hide it
        root = tk.Tk()
        root.withdraw()
        
        # Show the file dialog
        file_path = filedialog.askopenfilename(
            title="Select CSV File",
            filetypes=[("CSV Files", "*.csv")]
        )
        
        # Destroy the root window
        root.destroy()
        
        if file_path:
            return self.load_csv(file_path)
        else:
            log.warning("No CSV file selected.")
            return False

    def read_json_file(self, path: str) -> dict:
        try:
            with open(path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            log.error(f"File {path} not found.")
            sys.exit(1)

    def write_json_file(self, path: str, data: dict):
        with open(path, 'w') as f:
            json.dump(data, f, indent=4)

    def read_findings_csv(self, path: str) -> list:
        findings = []
        try:
            with open(path, mode='r', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                findings = [
                    {key: row[key] for key in ['Plugin ID', 'Name', 'Risk']}
                    for row in csv_reader if row['Risk'] and row['Risk'].strip()
                ]
        except FileNotFoundError:
            log.error(f"File {path} not found.")
            sys.exit(1)
        return findings


    def identify_merged_findings(self, no_informational=False):
        if not self.findings:
            log.warning("No findings loaded. Please select a CSV file first.")
            return {}, []
            
        merged_findings = {}
        individual_findings = set()
        plugin_categories = self.build_plugin_categories()
        
        filtered_count = 0
        for finding in self.findings:
            plugin_id = finding['Plugin ID']
            name = finding['Name']
            risk = finding['Risk']
            
            # Always ignore None risk findings
            if risk == self.IGNORE_INFORMATIONAL:
                continue
                
            # Skip informational findings if requested
            if no_informational and risk.lower() in ['informational', 'info']:
                filtered_count += 1
                continue
                
            if plugin_id == self.IGNORE_PLUGIN:  # Ignore the "Track/Trace" plugin
                continue
            if plugin_id in plugin_categories:
                if plugin_categories[plugin_id] not in merged_findings:
                    merged_findings[plugin_categories[plugin_id]] = set()
                plugin_info = f"Plugin ID: {plugin_id}, Name: {name}, Risk: {risk}"
                merged_findings[plugin_categories[plugin_id]].add(plugin_info)
            else:
                individual_findings.add(f"Plugin ID: {plugin_id}, Name: {name}, Risk: {risk}")
                
        for category in merged_findings:
            merged_findings[category] = list(merged_findings[category])
        individual_findings = list(individual_findings)
        
        if filtered_count > 0:
            log.info(f"Filtered out {filtered_count} informational findings")
            
        return merged_findings, individual_findings

    def build_plugin_categories(self):
            categories = {}
            for category, details in self.config["plugins"].items():
                for plugin_id in details["ids"]:
                    categories[plugin_id] = category
            return categories

    def confirm_exit(self):
        if self.temp_changes:
            exit_confirm = input('You have pending changes. Do you really want to exit without saving? (y/n): ')
            if exit_confirm.lower() in ['y', 'yes']:
                sys.exit()
        else:
            sys.exit()

    def remove_plugin(self):
        plugin_names = self.get_plugin_names_from_csv()
        categories = list(self.config['plugins'].keys())
        category_name = self._prompt_choice('Select the category from which to remove plugins:', categories + ['Cancel'])

        if category_name == 'Cancel':
            return

        filter_string = input('Enter a filter string to narrow down the plugins (leave empty for all): ').lower()
        current_plugin_ids = self.config['plugins'].get(category_name, {}).get('ids', [])
        filtered_plugins = [
            {'id': plugin_id, 'name': plugin_names[plugin_id]}
            for plugin_id in current_plugin_ids
            if plugin_id in plugin_names and filter_string in plugin_names[plugin_id].lower()
        ]

        if not filtered_plugins:
            log.info("No plugins matched your filter. Please try again with a different filter string.")
            return

        choices_for_plugin_removal = [
            f"{plugin['id']} - {plugin['name']}" for plugin in filtered_plugins
        ]

        selected_plugins = self._prompt_choices('Select the Plugin IDs to remove from \'{}\':'.format(category_name), choices_for_plugin_removal)

        for plugin_selection in selected_plugins:
            plugin_id = plugin_selection.split(" - ")[0]
            if plugin_id in current_plugin_ids:
                current_plugin_ids.remove(plugin_id)
                log.success(f"Removed plugin {plugin_id} from category {category_name}.")
            else:
                log.warning(f"Plugin {plugin_id} not found in category {category_name}.")

        self.temp_changes[category_name] = current_plugin_ids
        
        # Save temp changes to file
        self.write_to_temp_file(self.temp_changes)


    def add_plugin(self, non_merged_plugins):
        available_plugins = [plugin for plugin in non_merged_plugins if plugin['id'] not in sum(self.temp_changes.values(), [])]
        available_plugins = sorted(available_plugins, key=lambda x: x['name'])
        choices_for_plugin_selections = [f"{plugin['id']} - {plugin['name']}" for plugin in available_plugins]

        plugin_selections = self._prompt_choices('Select the Plugin IDs to add:', choices_for_plugin_selections)
        category_name = self._prompt_choice('Select a category:', list(self.config['plugins'].keys()) + ['Main Menu'])

        if 'Main Menu' in plugin_selections or category_name == 'Main Menu':
            return

        plugin_ids = [selection.split(" - ")[0] for selection in plugin_selections]

        if plugin_ids and category_name:
            if self.temp_changes is None:
                self.temp_changes = {}

            if category_name not in self.temp_changes:
                self.temp_changes[category_name] = []
            for plugin_id in plugin_ids:
                if plugin_id not in self.temp_changes[category_name]:
                    self.temp_changes[category_name].append(plugin_id)
                    log.success(f"Temporarily added plugin {plugin_id} to category {category_name}. Use 'Write Changes' to save.")
                else:
                    log.warning(f"Plugin {plugin_id} is already in category {category_name}.")
                    
            # Save temp changes to file
            self.write_to_temp_file(self.temp_changes)

    def _prompt_choice(self, message, choices):
        print(f"\n{message}")
        for i, choice in enumerate(choices, 1):
            print(f"{i}. {choice}")
        while True:
            try:
                selection = int(input(f"Select an option (1-{len(choices)}): "))
                if 1 <= selection <= len(choices):
                    return choices[selection - 1]
                else:
                    print("Invalid selection. Try again.")
            except ValueError:
                print("Invalid input. Please enter a number.")

    def _prompt_choices(self, message, choices):
        print(f"\n{message}")
        for i, choice in enumerate(choices, 1):
            print(f"{i}. {choice}")
        selections = []
        while True:
            try:
                input_selections = input("Select options by number, separated by commas (e.g., 1,2,3): ").split(',')
                selections = [choices[int(i.strip()) - 1] for i in input_selections if i.strip().isdigit() and 1 <= int(i.strip()) <= len(choices)]
                if selections:
                    return selections
                else:
                    print("No valid selections. Try again.")
            except (IndexError, ValueError):
                print("Invalid input. Please enter valid numbers.")


    def clear_changes(self):
        self.temp_changes.clear()
        # Remove the temp file if it exists
        if os.path.exists(self.TEMP_FILE):
            os.remove(self.TEMP_FILE)
        log.success("Changes cleared.")

    def view_changes(self):
        log.info("Current Changes:")
        for category, plugin_ids in self.temp_changes.items():
            print(f"\n• {category}:")
            for plugin_id in plugin_ids:
                print(f"  └── {plugin_id}")
        print()

    def write_changes(self):
        self.update_config()
        log.success("Changes written to N2P_config.json.")

    def write_to_temp_file(self, temp_changes):
        with open(self.TEMP_FILE, 'w') as f:
            json.dump(temp_changes, f)

    def update_config(self):
        if not self.temp_changes:
            log.warning("No changes to update.")
            return
        for category, plugin_ids in self.temp_changes.items():
            if category in self.config['plugins']:
                self.config['plugins'][category]['ids'].extend(
                    [pid for pid in plugin_ids if pid not in self.config['plugins'][category]['ids']])
            else:
                log.error(f"Error: The category '{category}' does not exist in the config.")
        self.write_json_file('N2P_config.json', self.config)
        self.temp_changes.clear()
        
        # Clear the temp file after successfully writing changes
        if os.path.exists(self.TEMP_FILE):
            os.remove(self.TEMP_FILE)

    def cleanup(self):
        if os.path.exists(self.TEMP_FILE):
            os.remove(self.TEMP_FILE)


    def get_plugin_names_from_csv(self) -> dict:
        """Returns a dictionary of plugin names from the CSV file."""
        plugin_names = {}
        
        if not self.csv_path:
            log.warning("No CSV file selected. Please select a CSV file first.")
            return plugin_names
            
        try:
            with open(self.csv_path, mode='r', encoding='utf-8') as csv_file:
                csv_reader = csv.DictReader(csv_file)
                for row in csv_reader:
                    plugin_id = row.get('Plugin ID')
                    name = row.get('Name')
                    if plugin_id and name:
                        plugin_names[plugin_id] = name
        except FileNotFoundError:
            log.error(f"File {self.csv_path} not found.")
            sys.exit(1)
        return plugin_names


    def simulate_findings(self, no_informational=False):
        """Simulate merged and individual findings."""
        if not self.csv_path:
            log.warning("No CSV file selected. Please select a CSV file first.")
            return False
        
        merged_findings, individual_findings = self.identify_merged_findings(no_informational)
        
        log.info("==== Merged Findings ====")
        if merged_findings:
            for category, findings in merged_findings.items():
                log.info(f"{category}: {len(findings)} plugins")
        else:
            log.info("No merged findings identified.")
        
        log.info("\n==== Individual Findings ====")
        if individual_findings:
            log.info(f"Total individual findings: {len(individual_findings)}")
        else:
            log.info("No individual findings identified.")
        
        # Print the detailed output when running in CLI mode
        print("\n\n===== SIMULATION RESULTS =====")
        print("\n==== Merged Findings ====")
        if merged_findings:
            for category, findings in merged_findings.items():
                print(f"\n{category} ({len(findings)} findings):")
                for finding in sorted(findings):
                    print(f"  - {finding}")
        else:
            print("No merged findings identified.")
        
        print("\n==== Individual Findings ====")
        if individual_findings:
            print(f"Total individual findings: {len(individual_findings)}")
            for finding in sorted(individual_findings):
                print(f"  - {finding}")
            
        return True


class ArgParser:
    @staticmethod
    def parse_args() -> argparse.Namespace:
        parser = argparse.ArgumentParser(description='Plugin Manager for PlexTrac')
        parser.add_argument('-f', '--csv-file', dest='csv_file_path', type=str, help='Path to the CSV file.')
        parser.add_argument('--action', choices=['select_csv', 'simulate', 'add_plugin', 'remove_plugin', 'view_changes', 
                                              'write_changes', 'clear_changes'], 
                         help='Action to perform in CLI mode')
        parser.add_argument('--category', type=str, help='Category name for adding or removing plugins')
        parser.add_argument('--plugin-ids', type=str, help='Comma-separated list of plugin IDs to add or remove')
        parser.add_argument('--no-informational', action='store_true', help='Filter out Informational findings')
        return parser.parse_args()


def run_interactive_mode(manager):
    """Run the plugin manager in interactive mode with a console menu."""
    log.info("Starting interactive mode...")
    # Action map
    action_map = {
        'Select CSV File': manager.select_csv_file,
        'Add Plugin': manager.add_plugin,
        'Simulate Findings': manager.simulate_findings,
        'Remove Plugin': manager.remove_plugin,
        'View Changes': manager.view_changes,
        'Write Changes': manager.write_changes,
        'Clear Changes': manager.clear_changes,
        'Exit': manager.confirm_exit
    }

    # If CSV file was provided via command line, identify findings right away
    merged_findings, individual_findings = {}, []
    non_merged_plugins = []
    
    if manager.csv_path:
        log.info(f"Using CSV file: {manager.csv_path}")
        merged_findings, individual_findings = manager.identify_merged_findings()
        non_merged_plugins = [{'id': finding.split(", ")[0].split(": ")[1],
                            'name': finding.split(", ")[1].split(": ")[1]} for finding in individual_findings]

    while True:
        print("\nSelect an action:")
        for i, action in enumerate(action_map.keys(), 1):
            print(f"{i}. {action}")

        try:
            choice = int(input(f"Select an option (1-{len(action_map)}): "))
            log.info(f"User selected option: {choice}")
            if 1 <= choice <= len(action_map):
                action = list(action_map.keys())[choice - 1]
                log.info(f"Executing action: {action}")
                if action == 'Add Plugin':
                    if not manager.findings:
                        log.warning("No findings loaded. Please select a CSV file first.")
                        continue
                    # Refresh non_merged_plugins in case CSV was changed
                    _, individual_findings = manager.identify_merged_findings()
                    non_merged_plugins = [{'id': finding.split(", ")[0].split(": ")[1],
                                        'name': finding.split(", ")[1].split(": ")[1]} for finding in individual_findings]
                    action_map[action](non_merged_plugins)
                else:
                    action_map[action]()
            else:
                print("Invalid selection. Try again.")
        except ValueError:
            log.error("Invalid input. Please enter a number.")
        except KeyboardInterrupt:
            log.error("Keyboard Interrupt. Exiting...")
            sys.exit()
        except Exception as e:
            log.error(f"Unexpected error in interactive mode: {str(e)}")
            import traceback
            log.error(traceback.format_exc())


def run_cli_action(manager, args):
    """Run a specific action in CLI mode based on command line arguments."""
    if args.action == 'select_csv':
        if args.csv_file_path:
            manager.load_csv(args.csv_file_path)
        else:
            log.error("CSV file path is required for 'select_csv' action")
            sys.exit(1)
    
    elif args.action == 'simulate':
        manager.simulate_findings(args.no_informational)
    
    elif args.action == 'add_plugin':
        if not args.category or not args.plugin_ids:
            log.error("Both --category and --plugin-ids are required for 'add_plugin' action")
            sys.exit(1)
        
        plugin_ids = args.plugin_ids.split(',')
        if not manager.csv_path:
            log.error("No CSV file loaded. Please use --csv-file to specify a CSV file.")
            sys.exit(1)
        
        _, individual_findings = manager.identify_merged_findings()
        non_merged_plugins = [{'id': finding.split(", ")[0].split(": ")[1],
                              'name': finding.split(", ")[1].split(": ")[1]} 
                              for finding in individual_findings]
        
        # Filter non_merged_plugins to only those in plugin_ids
        available_plugins = [plugin for plugin in non_merged_plugins if plugin['id'] in plugin_ids]
        
        # Add each plugin to the specified category
        for plugin in available_plugins:
            if manager.temp_changes is None:
                manager.temp_changes = {}
            if args.category not in manager.temp_changes:
                manager.temp_changes[args.category] = []
            
            if plugin['id'] not in manager.temp_changes[args.category]:
                manager.temp_changes[args.category].append(plugin['id'])
                log.success(f"Temporarily added plugin {plugin['id']} to category {args.category}.")
            else:
                log.warning(f"Plugin {plugin['id']} is already in category {args.category}.")
        
        # Save temp changes to file
        manager.write_to_temp_file(manager.temp_changes)
    
    elif args.action == 'remove_plugin':
        if not args.category or not args.plugin_ids:
            log.error("Both --category and --plugin-ids are required for 'remove_plugin' action")
            sys.exit(1)
            
        plugin_ids = args.plugin_ids.split(',')
        current_plugin_ids = manager.config['plugins'].get(args.category, {}).get('ids', [])
        
        for plugin_id in plugin_ids:
            if plugin_id in current_plugin_ids:
                current_plugin_ids.remove(plugin_id)
                log.success(f"Removed plugin {plugin_id} from category {args.category}.")
            else:
                log.warning(f"Plugin {plugin_id} not found in category {args.category}.")
                
        manager.temp_changes[args.category] = current_plugin_ids
        
        # Save temp changes to file
        manager.write_to_temp_file(manager.temp_changes)
    
    elif args.action == 'view_changes':
        manager.view_changes()
    
    elif args.action == 'write_changes':
        manager.write_changes()
    
    elif args.action == 'clear_changes':
        manager.clear_changes()


def main():
    """Main entry point for the plugin manager script."""
    try:
        log.info("Starting Plugin Manager...")
        
        args = ArgParser.parse_args()
        
        # Check if N2P_config.json exists
        if not os.path.exists('N2P_config.json'):
            log.error("N2P_config.json not found in current directory!")
            sys.exit(1)
            
        log.info("Initializing PluginManager...")
        
        try:
            manager = PluginManager('N2P_config.json', args.csv_file_path if hasattr(args, 'csv_file_path') and args.csv_file_path else None)
            log.success("PluginManager initialized successfully")
        except Exception as e:
            log.error(f"Failed to initialize PluginManager: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            sys.exit(1)

        # Determine if we should run in CLI mode or interactive mode
        if args.action:
            # CLI mode
            log.info(f"Running in CLI mode with action: {args.action}")
            run_cli_action(manager, args)
        else:
            # Interactive mode
            log.info("Running in interactive mode...")
            run_interactive_mode(manager)
    
    except KeyboardInterrupt:
        log.error("Keyboard Interrupt. Exiting...")
        sys.exit()
    except Exception as e:
        log.error(f"Unexpected error in main: {str(e)}")
        import traceback
        log.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    main()
