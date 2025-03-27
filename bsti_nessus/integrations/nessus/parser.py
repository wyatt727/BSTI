"""
Nessus parser module for parsing Nessus CSV files.
"""
import csv
import os
import re
from typing import Any, Dict, List, Optional, Set, Tuple, Union
import hashlib
from collections import defaultdict

from ...utils.logger import log
from ...utils.config_manager import ConfigManager


class NessusParser:
    """
    Parser for Nessus CSV files.
    """
    def __init__(self, config_manager: ConfigManager):
        """
        Initialize the Nessus parser.
        
        Args:
            config_manager (ConfigManager): Configuration manager.
        """
        self.config = config_manager
        self.severity_mapping = self.config.get('nessus.severity_mapping', {
            "Critical": 5,
            "High": 4,
            "Medium": 3,
            "Low": 2,
            "Informational": 1
        })
        self.ignored_plugins = self.config.get('nessus.ignored_plugins', ["11213"])  # Default: ignore Track/Trace plugin
        self.merged_findings = {}
        self.individual_findings = []
        self.plugin_categories = self.config.get_plugin_categories()
        self.tag_map = self.config.get('tag_map', {})
        self.merged_plugin_ids = set()
        self.organized_descriptions = {}
    
    def process_directory(self, directory_path: str, mode: str = 'internal') -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Process all CSV files in a directory.
        
        Args:
            directory_path (str): Path to the directory containing Nessus CSV files.
            mode (str, optional): Mode for tagging findings (internal, external, etc.).
            
        Returns:
            tuple: (merged_findings, individual_findings)
        """
        csv_found = False
        
        for file in os.listdir(directory_path):
            if file.endswith(".csv"):
                csv_found = True
                log.info(f"Processing CSV file: {file}")
                self._process_csv_file(os.path.join(directory_path, file), mode)
        
        if not csv_found:
            log.error("No CSV files found in the provided directory.")
            raise FileNotFoundError("No CSV files found in the provided directory.")
        
        log.info(f"Processed {len(self.merged_findings)} merged finding categories and {len(self.individual_findings)} individual findings")
        
        return self.merged_findings, self.individual_findings
    
    def _process_csv_file(self, file_path: str, mode: str):
        """
        Process a single CSV file.
        
        Args:
            file_path (str): Path to the CSV file.
            mode (str): Mode for tagging findings (internal, external, etc.).
        """
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as infile:
                reader = csv.DictReader(infile)
                for row in reader:
                    self._process_csv_row(row, mode)
        except Exception as e:
            log.error(f"Error processing CSV file {file_path}: {str(e)}")
            raise
    
    def _process_csv_row(self, row: Dict[str, Any], mode: str):
        """
        Process a single row from a CSV file.
        
        Args:
            row (dict): A dictionary representing a row in the CSV file.
            mode (str): Mode for tagging findings (internal, external, etc.).
        """
        # Skip informational findings and ignored plugins
        if row.get('Risk') == "None" or row.get('Plugin ID') in self.ignored_plugins:
            return
        
        plugin_id = row.get('Plugin ID', '')
        
        # If the plugin belongs to a category, add it as a merged finding
        if plugin_id in self.plugin_categories:
            self._add_merged_finding(row, plugin_id)
        else:
            # Add as individual finding
            self._add_individual_finding(row, mode)
    
    def _add_merged_finding(self, row: Dict[str, Any], plugin_id: str):
        """
        Add a finding to a merged category.
        
        Args:
            row (dict): A dictionary representing a row in the CSV file.
            plugin_id (str): The plugin ID.
        """
        category = self.plugin_categories[plugin_id]
        
        if category not in self.merged_findings:
            self.merged_findings[category] = {
                'findings': [],
                'affected_assets': set()
            }
        
        self.merged_findings[category]['findings'].append(row)
        self.merged_findings[category]['affected_assets'].add(f"{row.get('Host', '')}:{row.get('Port', '')}")
        self.merged_plugin_ids.add(plugin_id)
    
    def _add_individual_finding(self, row: Dict[str, Any], mode: str):
        """
        Add an individual finding.
        
        Args:
            row (dict): A dictionary representing a row in the CSV file.
            mode (str): Mode for tagging findings (internal, external, etc.).
        """
        # Enhance the row with additional data before adding it
        row['tag'] = self.tag_map.get(mode, '')
        
        # Store the original row for reference
        self.individual_findings.append(row)
    
    def filter_existing_flaws(self, existing_flaws: Dict[str, Dict[str, Any]]) -> int:
        """
        Filter out findings that already exist in Plextrac.
        
        Args:
            existing_flaws (dict): Dictionary of existing flaws.
            
        Returns:
            int: Number of filtered findings.
        """
        filtered_count = 0
        
        # Filter out individual findings
        filtered_individual_findings = []
        for finding in self.individual_findings:
            title = finding.get('Name', '')
            
            # Check if this finding already exists in Plextrac
            already_exists = False
            for flaw_id, flaw_data in existing_flaws.items():
                if flaw_data.get('title') == title:
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
            category_details = self.config.get_plugin_details(category)
            writeup_name = category_details.get('writeup_name', category)
            
            # Check if this merged finding already exists in Plextrac
            already_exists = False
            for flaw_id, flaw_data in existing_flaws.items():
                if flaw_data.get('title') == writeup_name:
                    already_exists = True
                    break
            
            if not already_exists:
                filtered_merged_findings[category] = details
            else:
                filtered_count += 1
        
        self.merged_findings = filtered_merged_findings
        
        if filtered_count > 0:
            log.info(f"Filtered out {filtered_count} findings that were already in Plextrac")
        
        return filtered_count
    
    def process_description(self, description: str, plugin_id: str = None) -> str:
        """
        Process and enhance a description with additional content.
        
        Args:
            description (str): The original description text.
            plugin_id (str, optional): The Nessus plugin ID for this finding.
            
        Returns:
            str: Enhanced description text.
        """
        if not description:
            return ""
        
        # Basic formatting cleanup
        processed = description.replace("\n\n", "\n").strip()
        
        # Add plugin-specific details if available
        if plugin_id:
            plugin_details = self._get_plugin_details(plugin_id)
            if plugin_details:
                if "additional_info" in plugin_details:
                    processed += f"\n\n## Additional Information\n{plugin_details['additional_info']}"
                
                if "mitigation_details" in plugin_details:
                    processed += f"\n\n## Detailed Mitigation\n{plugin_details['mitigation_details']}"
        
        # Add references if available
        references = self._get_references_for_plugin(plugin_id) if plugin_id else None
        if references:
            processed += "\n\n## References\n"
            for ref in references:
                processed += f"- {ref}\n"
        
        return processed
    
    def _get_plugin_details(self, plugin_id: str) -> Optional[Dict[str, Any]]:
        """
        Get details for a specific plugin.
        
        Args:
            plugin_id (str): The Nessus plugin ID.
            
        Returns:
            dict or None: Plugin details if found, None otherwise.
        """
        # Check if we have specific details for this plugin
        for category, details in self.config.get_plugin_definitions().get("plugins", {}).items():
            if plugin_id in details.get("ids", []):
                return details
        
        return None
    
    def _get_references_for_plugin(self, plugin_id: str) -> List[str]:
        """
        Get references for a specific plugin.
        
        Args:
            plugin_id (str): The Nessus plugin ID.
            
        Returns:
            list: List of reference strings.
        """
        references = []
        
        # Add standard references based on plugin ID
        plugin_details = self._get_plugin_details(plugin_id)
        if plugin_details and "references" in plugin_details:
            references.extend(plugin_details["references"])
        
        # Could add other reference lookups (e.g. from NVD, CVE database, etc.)
        
        return references
    
    def generate_plextrac_csv(self, output_path: str, mode: str = 'internal'):
        """
        Generate a CSV file in Plextrac format.
        
        Args:
            output_path (str): Path to the output CSV file.
            mode (str, optional): Mode for tagging findings (internal, external, etc.).
        """
        with open(output_path, 'w', newline='', encoding='utf-8') as outfile:
            fieldnames = [
                "title", "severity", "status", "description", "recommendations",
                "references", "affected_assets", "tags", "cvss_temporal",
                "cwe", "cve", "category"
            ]
            writer = csv.DictWriter(outfile, fieldnames=fieldnames)
            writer.writeheader()
            
            # Write merged findings
            self._write_merged_findings(writer, mode)
            
            # Write individual findings
            self._write_individual_findings(writer, mode)
        
        log.success(f"Generated Plextrac CSV file at {output_path}")
    
    def _write_merged_findings(self, writer: csv.DictWriter, mode: str):
        """
        Write merged findings to the CSV writer.
        
        Args:
            writer (csv.DictWriter): CSV writer object.
            mode (str): Mode for tagging findings (internal, external, etc.).
        """
        for category, details in self.merged_findings.items():
            category_details = self.config.get_plugin_details(category)
            
            if not category_details:
                log.warning(f"No category details found for {category}, skipping")
                continue
            
            writeup_name = category_details.get('writeup_name', category)
            findings = details['findings']
            affected_assets = details['affected_assets']
            
            # Skip if no findings
            if not findings:
                continue
            
            # Get highest severity
            highest_severity = max(findings, key=lambda x: self.severity_mapping.get(x.get('Risk', 'Low')))
            severity = highest_severity.get('Risk', 'Low')
            
            # Get references
            references = set()
            for finding in findings:
                refs = finding.get('See Also', '')
                if refs:
                    for ref in refs.split('\n'):
                        references.add(ref.strip())
            
            # Get CVEs
            cves = set()
            for finding in findings:
                cvs = finding.get('CVE', '')
                if cvs:
                    for cve in cvs.split('\n'):
                        cves.add(cve.strip())
            
            # Get CVSS score
            cvss_score = next((finding.get('CVSS v3.0 Temporal Score', '') for finding in findings if finding.get('CVSS v3.0 Temporal Score')), '')
            
            # Get description from category details or combine from findings
            description = category_details.get('description', '')
            if not description:
                description = '\n\n'.join(f["Description"] for f in findings if f.get("Description"))
            
            # Get recommendations
            recommendations = '\n\n'.join(f["Solution"] for f in findings if f.get("Solution"))
            
            # Create row
            row = {
                "title": writeup_name,
                "severity": severity,
                "status": "Open",
                "description": self.process_description(description, plugin_id=category),
                "recommendations": recommendations,
                "references": '\n'.join(references),
                "affected_assets": '\n'.join(affected_assets),
                "tags": self.tag_map.get(mode, ''),
                "cvss_temporal": cvss_score,
                "cve": '\n'.join(cves),
                "category": category
            }
            
            writer.writerow(row)
    
    def _write_individual_findings(self, writer: csv.DictWriter, mode: str):
        """
        Write individual findings to the CSV writer.
        
        Args:
            writer (csv.DictWriter): CSV writer object.
            mode (str): Mode for tagging findings (internal, external, etc.).
        """
        for finding in self.individual_findings:
            name = finding.get('Name', '')
            severity = finding.get('Risk', 'Low')
            description = finding.get('Description', '')
            solution = finding.get('Solution', '')
            see_also = finding.get('See Also', '')
            host = finding.get('Host', '')
            port = finding.get('Port', '')
            cvss_score = finding.get('CVSS v3.0 Temporal Score', '')
            cve = finding.get('CVE', '')
            
            row = {
                "title": name,
                "severity": severity,
                "status": "Open",
                "description": self.process_description(description, plugin_id=name),
                "recommendations": solution,
                "references": see_also,
                "affected_assets": f"{host}:{port}",
                "tags": self.tag_map.get(mode, ''),
                "cvss_temporal": cvss_score,
                "cve": cve,
                "category": self._extract_category(name)
            }
            
            writer.writerow(row)
    
    def _extract_category(self, plugin_name: str) -> str:
        """
        Extract a category from a plugin name.
        
        Args:
            plugin_name (str): Name of the plugin.
            
        Returns:
            str: Extracted category or empty string.
        """
        match = re.match(r"([a-zA-Z\s]+)", plugin_name)
        if match:
            return match.group(1).strip()
        return "" 