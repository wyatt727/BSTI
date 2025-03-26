import json
import csv
from scripts.creator import GenConfig
import os
from scripts.logging_config import log

class ConfigParser:
    """
    Parses configuration data from a CSV file and a JSON file.

    The class reads data from a CSV file, performs various operations on the data, and interacts with a JSON file.
    It provides methods to gather and process data from the CSV file, as well as load and manipulate data from the JSON file.

    """

    def __init__(self, csv_file):
        """
        Initialize the ConfigParser object.

        Parameters:
        - csv_file: The path of the CSV file containing configuration data.
        """
        self.csv_file = csv_file
        self.json_config = 'NMB_config.json'
        if not os.path.isfile(self.json_config):
            log.warning("'NMB_config.json' not found - generating it for you this will take awhile ...")
            GenConfig()
            log.success("NMB_config.json finished generating")

    def _get_last_modified_time(self):
        """
        Get the last modified time of the 'config.json' file.
        """
        return os.path.getmtime(self.json_config)

    def gather_data(self):
        """
        Gather and process data from the CSV file.

        Returns:
        - nessus_data: A list of tuples containing the gathered data.
        - json_config: The loaded JSON data as a dictionary.
        - supported_plugins: A list of supported plugin names.
        - missing_plugins: A list of plugin names from the CSV file that are missing in the JSON file.

        """

        nessus_data = []
        supported_plugins = []
        missing_plugins = []
        risk_factors = []

        try:
            with open(self.csv_file, 'r', encoding="utf8") as csv_file:
                csv_reader = csv.DictReader(csv_file)
                # Skip the header row
                next(csv_reader)

                # Create a dictionary to store the plugin names by ID
                plugin_names = {}
                # Also store the associated host, port, and name for each plugin_id
                plugin_data = {}

                # Loop through each row in the CSV file
                for row in csv_reader:
                    # Get the plugin ID, name, and severity from the row
                    plugin_id = row['Plugin ID']
                    plugin_name = row['Name']
                    severity = row['Risk']
                    risk_factors.append((plugin_id, plugin_name, severity))

                    # Add the plugin name to the dictionary with the ID as the key
                    plugin_names[plugin_id] = plugin_name

                    host = row['Host']
                    port = row['Port']
                    name = row['Name']
                    risk = row['Risk']
                    description = row['Description']
                    remedy = row['Solution']
                    nessus_data.append((host, port, name, plugin_id, risk, description, remedy))
                    
                    # Store associated host, port, and name for each plugin_id
                    plugin_data[plugin_id] = {'host': host, 'port': port, 'name': name}

            with open(self.json_config, 'r') as json_file:
                json_config = json.load(json_file)

                # Get the "ids" key from each plugin in the "plugins" dictionary
                plugin_id_sets = [set(plugin["ids"]) for plugin in json_config["plugins"].values()]

                # Flatten the list of sets into a single set of all plugin IDs
                all_plugin_ids = set().union(*plugin_id_sets)

                # Find the intersection between the plugin IDs from the CSV file and the plugin IDs in the JSON file
                matching_plugin_ids = all_plugin_ids.intersection(plugin_names.keys())

                for plugin_id, plugin_name, severity in risk_factors:
                    if plugin_id not in matching_plugin_ids and plugin_id not in json_config["plugins"] and severity != 'None':
                        host, port, name = plugin_data[plugin_id]['host'], plugin_data[plugin_id]['port'], plugin_data[plugin_id]['name']
                        missing_plugins.append((host, port, plugin_name))

                # Print the matching plugin names
                print("Supported plugins:")
                print("-" * 50)
                for plugin_id in matching_plugin_ids:
                    plugin_name = plugin_names[plugin_id]
                    supported_plugins.append(plugin_name)
                    print(f"[+] {plugin_name}")
                print("-" * 50)

                missing_plugins = list(set(missing_plugins))

            return nessus_data, json_config, supported_plugins, missing_plugins

        except Exception as e:
            log.error("Parsing failed - probably due to CSV file only containing the header row")