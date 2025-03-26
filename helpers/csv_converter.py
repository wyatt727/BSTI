import csv
from typing import Any, Dict, List, Union
import re 
import os
import hashlib
from collections import defaultdict

class NessusToPlextracConverter:
    STATUS_OPEN = "Open"
    SEVERITY_MAPPING = {
        "Critical": 5,
        "High": 4,
        "Medium": 3,
        "Low": 2,
        "Informational": 1
    }

    def __init__(self, nessus_directory: str, config: Dict[str, Any], mode: str, args: Any):
        self.nessus_directory = nessus_directory
        self.args = args
        self.mode = mode
        self.config = config
        self.plugin_categories = self.build_plugin_categories()
        self.merged_findings = {}
        self.individual_findings = []
        self.merged_plugin_ids = set()
        self.organized_descriptions = {}

        self.tag_map = {
            "internal": "internal_finding",
            "external": "external_finding",
            "surveillance": "surveillance_finding",
            "web": "webapp_finding",
            "mobile": "mobileapp_finding"
        }

    def build_plugin_categories(self) -> Dict[str, str]:
        """
        Build a mapping of plugin categories from the configuration.

        :return: Dictionary mapping plugin IDs to their respective categories.
        """
        categories = {}
        for category, details in self.config["plugins"].items():
            for plugin_id in details["ids"]:
                categories[plugin_id] = category
        return categories

    def process_nessus_csv(self):
        """Process each CSV file in the directory."""
        csv_found = False 

        for file in os.listdir(self.nessus_directory):
            if file.endswith(".csv"):
                csv_found = True
                self.process_csv_file(file)
        
        if not csv_found:
            raise FileNotFoundError("No CSV files found in the provided directory.")

    def process_csv_file(self, file: str):
        """
        Process a CSV file and write findings to PlexTrac format.

        :param file: The name of the CSV file to process.
        """
        filepath = os.path.join(self.nessus_directory, file)
        with open(filepath, 'r', encoding='utf-8-sig') as infile:
            reader = csv.DictReader(infile)
            for row in reader:
                self.process_csv_row(row)

    def process_csv_row(self, row: Dict[str, Any]):
        """
        Process a single row from a CSV file.

        :param row: A dictionary representing a row in the CSV file.
        """
        if row['Risk'] == "None":
            return
        plugin_id = row['Plugin ID']
        if plugin_id == '11213': # Ignore the "Track/Trace" plugin
            return
        if plugin_id in self.plugin_categories:
            self.add_merged_finding(row, plugin_id)
        else:
            self.individual_findings.append(row)

    def add_merged_finding(self, row: Dict[str, Any], plugin_id: str):
        """
        Add a merged finding to the internal data structure based on the plugin ID.

        :param row: A dictionary representing a row in the CSV file.
        :param plugin_id: The plugin ID for categorizing the finding.
        """
        category = self.plugin_categories[plugin_id]
        if category not in self.merged_findings:
            self.merged_findings[category] = {
                'findings': [],
                'affected_assets': set()
            }
        self.merged_findings[category]['findings'].append(row)
        self.merged_findings[category]['affected_assets'].add(f"{row['Host']}:{row['Port']}")
        self.merged_plugin_ids.add(plugin_id)

    def write_to_plextrac_csv(self, output_csv_path: str):
        """
        Write findings to a CSV file in PlexTrac format.

        :param output_csv_path: The path to the output CSV file.
        """
        with open(output_csv_path, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = [
                "title", "severity", "status", "description", "recommendations",
                "references", "affected_assets", "tags", "cvss_temporal",
                "cwe", "cve", "category"
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            self.write_merged_findings(writer)
            self.write_individual_findings(writer)


    def extract_main_category(self, plugin_name: str) -> str:
        """
        Extract the main category from a plugin name using regex.

        :param plugin_name: The name of the plugin.
        :return: The main category if found; otherwise, None.
        """
        match = re.match(r"([a-zA-Z\s]+)", plugin_name)
        if match:
            main_cat = match.group(1).strip()
            return main_cat
        return None

    @staticmethod
    def map_severity_to_tags(severity: str) -> (str, str): # type: ignore
        """
        Map severity levels to tags for priority and complexity.

        :param severity: The severity level.
        :return: A tuple containing tags for priority and complexity.
        """
        severity_map = {
            "Low": "priority_low",
            "Medium": "priority_medium",
            "High": "priority_high",
            "Critical": "priority_high"
        }

        complexity_map = {
            "Low": "complexity_easy",
            "Medium": "complexity_intermediate",
            "High": "complexity_complex",
            "Critical": "complexity_complex"
        }

        return severity_map.get(severity, ""), complexity_map.get(severity, "")

    def _get_tag(self) -> str:
        """
        Get the appropriate tag based on the mode.

        Modes and their corresponding tags:
        - "internal": "internal_finding"
        - "external": "external_finding"
        - "surveillance": "surveillance_finding"
        - "web": "webapp_finding"
        - "mobile": "mobileapp_finding"

        :return: Tag as a string.
        """
        
        # Default to "internal_finding" if mode is not recognized
        return self.tag_map.get(self.mode, "internal_finding")


    def _get_title_prefix(self) -> str:
        """
        Get the appropriate title prefix based on the mode to ensure uniqueness and context clarity.

        Modes and their prefixes:
        - "external": Prefixes with "(External)"
        - "web": Prefixes with "(Web)"
        - "surveillance": Prefixes with "(Surveillance)"
        - "mobile": Prefixes with "(Mobile)"
        - Other/internal: No prefix

        :return: Title prefix as a string.
        """
        prefix_map = {
            "external": "(External) ",
            "web": "(Web) ",
            "surveillance": "(Surveillance) ",
            "mobile": "(Mobile) ",
            "internal": ""
        }
        return prefix_map.get(self.mode, "")


    def _format_text(self, text: str) -> str:
        """
        Format text by removing carriage returns and newlines.

        :param text: The original text.
        :return: Formatted text.
        """
        return text.replace('\r', '').replace('\n', ' ')

    def _group_findings_by_name(self, details: Dict[str, Any], category: str) -> Dict[str, List[Dict[str, Any]]]:
        """
        Groups findings by their names.
        
        :param details: Dictionary containing details of findings.
        :param category: The category of the findings.
        :return: Dictionary with findings grouped by their names.
        """
        finding_groups = {}
        for finding in details['findings']:
            finding_name = finding["Name"]
            group_by_name = self.extract_main_category(finding_name) if category == "Software Components Out of Date and Vulnerable" else finding_name
            if group_by_name not in finding_groups:
                finding_groups[group_by_name] = []
            finding_groups[group_by_name].append(finding)
        return finding_groups
    
    # Get the highest severity
    def _get_highest_severity(self, details: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Gets the highest severity level among the provided findings.
        
        :param details: Dictionary containing details of findings.
        :return: Highest severity level as a string.
        """
        severity_mapping = {
            "Critical": 5,
            "High": 4,
            "Medium": 3,
            "Low": 2,
            "Informational": 1
        }
        highest_severity_value = max(severity_mapping[finding["Risk"]] for finding in details['findings'])
        highest_severity = [key for key, value in severity_mapping.items() if value == highest_severity_value][0]
        return highest_severity

    # Get the final tags
    def _get_final_tags(self, tag: str, highest_severity: str) -> str:
        """
        Composes the final tags based on the highest severity.
        
        :param tag: Base tag for the finding.
        :param highest_severity: Highest severity level.
        :return: Final tags as a string.
        """
        severity_tag, complexity_tag = self.map_severity_to_tags(highest_severity)
        return f"{tag},{severity_tag},{complexity_tag}"

    # Get the full description
    def _get_full_description(self, finding_groups: Dict[str, List[Dict[str, Any]]], category: str) -> str:
        """
        Generates the full description for grouped findings.
        
        :param finding_groups: Dictionary of grouped findings.
        :param category: Category of the findings.
        :return: Full description as HTML string.
        """
        descriptions = []
        for group_name, findings in finding_groups.items():
            highest_group_severity = self._get_highest_severity({'findings': findings})
            assets = self._get_affected_assets_str(findings)
            
            # Add "Lack of Updates" if the category matches
            if category == "Software Components Out of Date and Vulnerable":
                description_chunk = f"<p><b>{group_name} Lack of Updates (severity: {highest_group_severity.lower()})</b></p><ul>{''.join([f'<li>{asset.strip()}</li>' for asset in assets.split(',')])}</ul>"
            else:
                description_chunk = f"<p><b>{group_name} (severity: {highest_group_severity.lower()})</b></p><ul>{''.join([f'<li>{asset.strip()}</li>' for asset in assets.split(',')])}</ul>"
            
            descriptions.append(description_chunk)
        return "\n\n".join(descriptions)

    
    # Compute MD5 hashes and use them as references
    def _get_references(self, details: Dict[str, List[Dict[str, Any]]]) -> str:
        """
        Generates references based on the MD5 hash of the finding names.
        
        :param details: Dictionary containing details of findings.
        :return: Concatenated references as a string.
        """
        hash_set = {hashlib.md5(finding["Name"].lower().encode()).hexdigest() for finding in details['findings']}
        return ";".join(list(hash_set))
    
    # Get the affected assets string
    def _get_affected_assets_str(self, findings: Union[List[Dict[str, Any]], Dict[str, Any]]) -> str:
        """
        Generates a string representing the affected assets.
        
        :param findings: List or Dictionary of findings.
        :return: Affected assets as a string.
        """
        if isinstance(findings, dict):
            findings = sum(findings.values(), [])
        
        ip_port_protocol_mapping = defaultdict(list)
        for finding in findings:
            host = finding.get('Host', 'Unknown')
            port = finding.get('Port', 'Unknown')
            protocol = finding.get('Protocol', 'Unknown')
            ip_port_protocol_mapping[(host, protocol)].append(port)
        
        return ', '.join(
            f"{host} ({protocol} {'; '.join(sorted(set(ports)))})"
            for (host, protocol), ports in ip_port_protocol_mapping.items()
        )

    def _get_individual_md5_hash(self, finding_name: str) -> str:
        """
        Computes the MD5 hash for a given finding name.

        :param finding_name: The name of the finding.
        :return: The MD5 hash as a string.
        """
        return hashlib.md5(finding_name.lower().encode()).hexdigest()


    def _write_to_csv(self, writer: csv.DictWriter, title_prefix: str, config_details: Dict[str, Any],
                      highest_severity: str, md5_hash: str, affected_assets_str: str, final_tags: str):
        """
        Write a single row to the CSV file using the given parameters.

        :param writer: The CSV writer object.
        :param title_prefix: The prefix to add to the title.
        :param config_details: The configuration details for the finding.
        :param highest_severity: The highest severity level for the finding.
        :param references: References are replaced by md5 hashes used to update finding with screenshot later.
        :param affected_assets_str: String representing affected assets.
        :param final_tags: Final tags for the finding.
        """
        writer.writerow({
            "title": title_prefix + config_details["writeup_name"],
            "severity": highest_severity,
            "status": "Open",
            "description": "FIXME",
            "recommendations": "FIXME",
            "references": md5_hash,
            "affected_assets": affected_assets_str,
            "tags": final_tags,
            "cvss_temporal": "",
            "cwe": "",
            "cve": "",
            "category": "",
        })
    
    # Write individual findings to the CSV
    def _write_individual_to_csv(self, writer: csv.DictWriter, title_prefix: str, finding: Dict[str, Any],
                                 description: str, recommendations: str, affected_assets: str, final_tags: str):
        """
        Write an individual finding to the CSV file.

        :param writer: The CSV writer object.
        :param title_prefix: The prefix to add to the title.
        :param finding: The finding details.
        :param description: Description of the finding.
        :param recommendations: Recommendations for the finding.
        :param affected_assets: String representing affected assets.
        :param final_tags: Final tags for the finding.
        """
        md5_hash = self._get_individual_md5_hash(finding["Name"])
        writer.writerow({
            "title": title_prefix + finding["Name"],
            "severity": finding["Risk"],
            "status": "Open",
            "description": description,
            "recommendations": recommendations,
            "references": f"{md5_hash} {finding['See Also']}",
            "affected_assets": affected_assets,
            "tags": final_tags,
            "cvss_temporal": "",
            "cwe": "",
            "cve": finding["CVE"],
            "category": ""
        })

    def write_individual_findings(self, writer: csv.DictWriter):
        """
        Write all individual findings to a CSV file.
        
        :param writer: The CSV writer object.
        """
        tag = self._get_tag()
        title_prefix = self._get_title_prefix()

        for finding in self.individual_findings:
            final_tags = self._get_final_tags(tag, finding["Risk"])
            description = self._format_text(finding["Description"])
            recommendations = self._format_text(finding["Solution"])

            affected_assets = f"{finding['Host']} ({finding['Protocol']} {finding['Port']})"
            
            self._write_individual_to_csv(writer, title_prefix, finding, description, recommendations, affected_assets, final_tags)
    
    def write_merged_findings(self, writer: csv.DictWriter):
        """
        Write all merged findings to a CSV file.
        
        :param writer: The CSV writer object.
        """
        tag = self._get_tag()
        title_prefix = self._get_title_prefix()

        for category, details in self.merged_findings.items():
            config_details = self.config["plugins"][category]

            finding_groups = self._group_findings_by_name(details, category)
            highest_severity = self._get_highest_severity(details)
            final_tags = self._get_final_tags(tag, highest_severity)

            full_description = self._get_full_description(finding_groups, category)
            self.organized_descriptions[category] = full_description

            references = self._get_references(details)
            affected_assets_str = self._get_affected_assets_str(finding_groups)

            self._write_to_csv(writer, title_prefix, config_details, highest_severity, references, affected_assets_str, final_tags)
    
    def convert(self, output_csv_path: str, existing_flaws=None):
        """
        Process Nessus CSV files and write the findings to a PlexTrac-compatible CSV file.
        
        :param output_csv_path: The path to the output CSV file.
        :param existing_flaws: Dictionary of existing flaws to avoid duplicating content.
        """
        self.process_nessus_csv()
        
        # Filter out findings that have already been processed in previous runs
        if existing_flaws:
            self._filter_existing_findings(existing_flaws)
            
        self.write_to_plextrac_csv(output_csv_path)
        
    def _filter_existing_findings(self, existing_flaws):
        """
        Filter out findings that have already been processed in previous runs.
        
        :param existing_flaws: Dictionary of existing flaws.
        """
        from helpers.custom_logger import log
        
        # Keep track of how many findings we're filtering out
        filtered_count = 0
        
        # Filter out individual findings
        filtered_individual_findings = []
        for finding in self.individual_findings:
            # Generate a title that would match what's in Plextrac
            title_prefix = self._get_title_prefix()
            full_title = title_prefix + finding["Name"]
            
            # Check if this finding already exists in Plextrac
            already_exists = False
            for flaw_id, flaw_data in existing_flaws.items():
                if flaw_data.get('title') == full_title:
                    already_exists = True
                    break
                    
            if not already_exists:
                filtered_individual_findings.append(finding)
            else:
                filtered_count += 1
                
        self.individual_findings = filtered_individual_findings
        
        # Filter out merged findings
        filtered_merged_findings = {}
        for category, details in self.merged_findings.items():
            config_details = self.config["plugins"].get(category)
            if not config_details:
                continue
                
            title_prefix = self._get_title_prefix()
            full_title = title_prefix + config_details["writeup_name"]
            
            # Check if this merged finding already exists in Plextrac
            already_exists = False
            for flaw_id, flaw_data in existing_flaws.items():
                if flaw_data.get('title') == full_title:
                    already_exists = True
                    break
                    
            if not already_exists:
                filtered_merged_findings[category] = details
            else:
                filtered_count += 1
                
        self.merged_findings = filtered_merged_findings
        
        if filtered_count > 0:
            log.info(f"Filtered out {filtered_count} findings that were already in Plextrac")