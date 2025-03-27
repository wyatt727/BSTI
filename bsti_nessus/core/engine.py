"""
Main engine for the BSTI Nessus to Plextrac converter.
"""
import os
import json
import sys
import time
import atexit
from typing import Any, Dict, List, Optional, Tuple

from ..utils.logger import log
from ..utils.config_manager import ConfigManager
from ..integrations.plextrac.api import PlextracAPI
from ..integrations.nessus.parser import NessusParser


class NessusEngine:
    """
    Main engine for the BSTI Nessus to Plextrac converter.
    
    This class orchestrates the entire conversion and upload process.
    """
    def __init__(self, args: Any):
        """
        Initialize the engine.
        
        Args:
            args (Any): Command-line arguments.
        """
        self.args = args
        self.config_manager = ConfigManager()
        
        # Set file paths from config
        self.plextrac_format_file = self.config_manager.get('file_paths.plextrac_format', 'plextrac_format.csv')
        self.processed_findings_file = self.config_manager.get('file_paths.processed_findings', '_processed_findings.json')
        self.existing_flaws_file = self.config_manager.get('file_paths.existing_flaws', 'existing_flaws.json')
        
        # Load client-specific configuration if client is specified
        if hasattr(args, 'client') and args.client:
            self.client_name = args.client
            client_loaded = self.config_manager.load_client_config(self.client_name)
            if client_loaded:
                log.info(f"Loaded client-specific configuration for {self.client_name}")
            else:
                log.warning(f"No client-specific configuration found for {self.client_name}")
                self.client_name = None
        else:
            self.client_name = None
        
        # Initialize components
        self.plextrac_api = PlextracAPI(args.target_plextrac)
        self.nessus_parser = NessusParser(self.config_manager)
        
        # State variables
        self.existing_flaws = {}
        self.mode = self._get_mode()
        
        # Register cleanup on exit
        atexit.register(self.cleanup)
    
    def _get_mode(self) -> str:
        """
        Get the current mode based on command-line arguments.
        
        Returns:
            str: Mode (internal, external, etc.).
        """
        mode_map = {
            "internal": "internal",
            "external": "external",
            "web": "web",
            "surveillance": "surveillance",
            "mobile": "mobile"
        }
        
        # Check for client-specific tag map overrides
        if self.client_name:
            client_tag_map = self.config_manager.get('tag_map', {})
            if client_tag_map:
                mode_map.update(client_tag_map)
        
        return mode_map.get(self.args.scope, "internal")
    
    def run(self):
        """
        Run the engine.
        """
        start_time = time.time()
        
        try:
            # Execute the main operations
            self.authenticate()
            self.convert_nessus_to_plextrac()
            self.upload_nessus_file()
            
            if self.args.screenshots:
                self.upload_screenshots()
            
            if hasattr(self.args, 'non_core') and self.args.non_core:
                self.update_non_core_fields()
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            log.info(f"Process completed in {elapsed_time:.2f} seconds")
            
        except Exception as e:
            log.error(f"Error running the engine: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            sys.exit(1)
    
    def authenticate(self):
        """
        Authenticate with the Plextrac API.
        """
        log.info(f"Authenticating to Plextrac instance: {self.args.target_plextrac}")
        
        success, token = self.plextrac_api.authenticate(
            username=self.args.username,
            password=self.args.password
        )
        
        if not success:
            log.error("Failed to authenticate with Plextrac API")
            sys.exit(1)
        
        log.success("Successfully authenticated with Plextrac API")
    
    def convert_nessus_to_plextrac(self):
        """
        Convert Nessus files to Plextrac format.
        """
        log.info("Converting Nessus files to Plextrac format")
        
        # Load existing flaws to avoid duplicates
        self._load_existing_flaws()
        
        try:
            # Process Nessus CSV files
            self.nessus_parser.process_directory(self.args.directory, self.mode)
            
            # Apply client-specific exclusions
            if self.client_name:
                self._apply_client_exclusions()
            
            # Filter out existing flaws
            if self.existing_flaws:
                filtered_count = self.nessus_parser.filter_existing_flaws(self.existing_flaws)
                log.info(f"Filtered out {filtered_count} existing findings")
            
            # Generate Plextrac CSV
            self.nessus_parser.generate_plextrac_csv(self.plextrac_format_file, self.mode)
            
            log.success("Successfully converted Nessus files to Plextrac format")
            
        except Exception as e:
            log.error(f"Error converting Nessus files: {str(e)}")
            import traceback
            log.error(traceback.format_exc())
            raise
    
    def upload_nessus_file(self):
        """
        Upload the converted file to Plextrac.
        """
        log.info("Uploading findings to Plextrac")
        
        if not os.path.exists(self.plextrac_format_file):
            log.error(f"Plextrac format file not found: {self.plextrac_format_file}")
            return
        
        success, response_data = self.plextrac_api.upload_nessus_file(self.plextrac_format_file)
        
        if success:
            log.success("Successfully uploaded findings to Plextrac")
            
            # Store findings for future reference
            if response_data and isinstance(response_data, dict):
                self._save_processed_findings(response_data)
        else:
            log.error("Failed to upload findings to Plextrac")
    
    def upload_screenshots(self):
        """
        Upload screenshots for findings.
        """
        log.info("Uploading screenshots for findings")
        
        screenshot_dir = self.config_manager.get('file_paths.screenshot_dir', 'screenshots')
        
        if not os.path.exists(screenshot_dir):
            log.warning(f"Screenshot directory not found: {screenshot_dir}")
            return
        
        # Check if we have processed findings with flaw IDs
        if not os.path.exists(self.processed_findings_file):
            log.warning("No processed findings file found, cannot upload screenshots")
            return
        
        try:
            with open(self.processed_findings_file, 'r') as f:
                processed_findings = json.load(f)
        except Exception as e:
            log.error(f"Error loading processed findings: {str(e)}")
            return
        
        # Upload screenshots for each finding
        success_count = 0
        error_count = 0
        
        for flaw_id, finding in processed_findings.items():
            # Look for a screenshot matching the finding title
            title = finding.get('title', '')
            if not title:
                continue
            
            # Generate a safe filename
            safe_title = self._safe_filename(title)
            
            # Look for screenshots with this name
            for filename in os.listdir(screenshot_dir):
                if filename.startswith(safe_title) and (filename.endswith('.png') or filename.endswith('.jpg') or filename.endswith('.jpeg')):
                    screenshot_path = os.path.join(screenshot_dir, filename)
                    
                    if self.plextrac_api.upload_screenshot(flaw_id, screenshot_path):
                        success_count += 1
                    else:
                        error_count += 1
        
        if success_count > 0:
            log.success(f"Successfully uploaded {success_count} screenshots")
        
        if error_count > 0:
            log.warning(f"Failed to upload {error_count} screenshots")
    
    def _load_existing_flaws(self):
        """
        Load existing flaws from file or API.
        """
        # First try to load from file
        if os.path.exists(self.existing_flaws_file):
            try:
                with open(self.existing_flaws_file, 'r') as f:
                    self.existing_flaws = json.load(f)
                
                if self.existing_flaws:
                    log.info(f"Loaded {len(self.existing_flaws)} existing flaws from file")
                    return
            except Exception as e:
                log.warning(f"Error loading existing flaws from file: {str(e)}")
        
        # If file doesn't exist or is empty, fetch from API
        log.info("Fetching existing flaws from Plextrac API")
        
        success, flaws = self.plextrac_api.get_flaws()
        
        if success and flaws:
            # Convert to dictionary format with flaw ID as key
            self.existing_flaws = {flaw['id']: flaw for flaw in flaws}
            log.info(f"Fetched {len(self.existing_flaws)} existing flaws from Plextrac API")
            
            # Save for future use
            self._save_existing_flaws()
        else:
            log.warning("Failed to fetch existing flaws from Plextrac API, will not filter duplicates")
    
    def _save_existing_flaws(self):
        """
        Save existing flaws to file.
        """
        try:
            with open(self.existing_flaws_file, 'w') as f:
                json.dump(self.existing_flaws, f, indent=2)
            
            log.debug(f"Saved {len(self.existing_flaws)} existing flaws to {self.existing_flaws_file}")
        except Exception as e:
            log.warning(f"Error saving existing flaws to file: {str(e)}")
    
    def _save_processed_findings(self, response_data: Dict[str, Any]):
        """
        Save processed findings to file for future reference.
        
        Args:
            response_data (dict): Response data from the API.
        """
        if 'findings' not in response_data:
            log.warning("No findings data in API response")
            return
        
        findings = response_data['findings']
        
        try:
            with open(self.processed_findings_file, 'w') as f:
                json.dump(findings, f, indent=2)
            
            log.debug(f"Saved {len(findings)} processed findings to {self.processed_findings_file}")
        except Exception as e:
            log.warning(f"Error saving processed findings to file: {str(e)}")
    
    def _safe_filename(self, title: str) -> str:
        """
        Convert a finding title to a safe filename.
        
        Args:
            title (str): Finding title.
            
        Returns:
            str: Safe filename.
        """
        # Replace characters that are not safe for filenames
        safe = title.replace(' ', '_')
        safe = ''.join(c for c in safe if c.isalnum() or c in '_-')
        return safe.lower()
    
    def cleanup(self):
        """
        Clean up resources on exit.
        """
        log.debug("Cleaning up resources")
        
        # Move plextrac format file to _merged directory if needed
        if os.path.exists(self.plextrac_format_file) and self.args.cleanup:
            try:
                merged_dir = '_merged'
                if not os.path.exists(merged_dir):
                    os.makedirs(merged_dir)
                
                dest_path = os.path.join(merged_dir, os.path.basename(self.plextrac_format_file))
                os.rename(self.plextrac_format_file, dest_path)
                log.debug(f"Moved {self.plextrac_format_file} to {dest_path}")
            except Exception as e:
                log.warning(f"Error moving plextrac format file: {str(e)}")
    
    def update_non_core_fields(self):
        """
        Update non-core fields for uploaded findings.
        """
        log.info("Updating non-core fields for uploaded findings")
        
        # Check if we have processed findings with flaw IDs
        if not os.path.exists(self.processed_findings_file):
            log.warning("No processed findings file found, cannot update non-core fields")
            return
        
        try:
            with open(self.processed_findings_file, 'r') as f:
                processed_findings = json.load(f)
        except Exception as e:
            log.error(f"Error loading processed findings: {str(e)}")
            return
        
        success_count = 0
        error_count = 0
        
        for flaw_id, finding in processed_findings.items():
            # Prepare non-core data
            non_core_data = self._prepare_non_core_data(finding)
            
            if non_core_data:
                if self.plextrac_api.update_non_core_fields(flaw_id, non_core_data):
                    success_count += 1
                else:
                    error_count += 1
        
        if success_count > 0:
            log.success(f"Successfully updated non-core fields for {success_count} findings")
        
        if error_count > 0:
            log.warning(f"Failed to update non-core fields for {error_count} findings")
    
    def _prepare_non_core_data(self, finding: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare non-core data for a finding.
        
        Args:
            finding (dict): Finding data.
            
        Returns:
            dict: Non-core data.
        """
        non_core_data = {}
        
        # Extract title for reference
        title = finding.get('title', '')
        
        # Add client information if available
        if self.client_name:
            client_info = self.config_manager.get('client', {})
            if client_info:
                non_core_data['client'] = client_info.get('name', self.client_name)
                
                # Add custom fields if available
                custom_fields = self.config_manager.get('reporting.custom_fields', {})
                if custom_fields:
                    for field_name, field_value in custom_fields.items():
                        non_core_data[field_name] = field_value
        else:
            if hasattr(self.args, 'client') and self.args.client:
                non_core_data['client'] = self.args.client
        
        # Add report information if available
        if hasattr(self.args, 'report') and self.args.report:
            non_core_data['report'] = self.args.report
        
        # Add scope information
        non_core_data['scope'] = self.mode
        
        # Add discovery dates
        from datetime import datetime
        non_core_data['discovery_date'] = datetime.now().strftime('%Y-%m-%d')
        
        # Add additional fields based on plugin details
        if 'plugin_id' in finding:
            plugin_id = finding['plugin_id']
            plugin_details = self.nessus_parser._get_plugin_details(plugin_id)
            
            if plugin_details:
                if 'risk_rating' in plugin_details:
                    non_core_data['risk_rating'] = plugin_details['risk_rating']
                
                if 'remediation_effort' in plugin_details:
                    non_core_data['remediation_effort'] = plugin_details['remediation_effort']
        
        return non_core_data
    
    def _apply_client_exclusions(self):
        """
        Apply client-specific exclusions to the findings.
        """
        if not self.client_name:
            return
        
        exclusions = self.config_manager.get('exclusions', {})
        if not exclusions:
            return
        
        # Get host exclusions
        excluded_hosts = exclusions.get('hosts', [])
        # Get plugin exclusions
        excluded_plugins = exclusions.get('plugins', [])
        
        if not excluded_hosts and not excluded_plugins:
            return
        
        excluded_count = 0
        
        # Filter individual findings based on exclusions
        if hasattr(self.nessus_parser, 'individual_findings'):
            filtered_individual_findings = []
            for finding in self.nessus_parser.individual_findings:
                # Check if host is excluded
                host = finding.get('Host', '')
                if host and host in excluded_hosts:
                    excluded_count += 1
                    continue
                
                # Check if plugin ID is excluded
                plugin_id = finding.get('Plugin ID', '')
                if plugin_id and plugin_id in excluded_plugins:
                    excluded_count += 1
                    continue
                
                filtered_individual_findings.append(finding)
            
            self.nessus_parser.individual_findings = filtered_individual_findings
        
        # Filter merged findings based on exclusions
        if hasattr(self.nessus_parser, 'merged_findings'):
            filtered_merged_findings = {}
            for category, details in self.nessus_parser.merged_findings.items():
                # Check if all plugin IDs in this category are excluded
                category_details = self.config_manager.get_plugin_details(category)
                if category_details and 'ids' in category_details:
                    if all(plugin_id in excluded_plugins for plugin_id in category_details['ids']):
                        excluded_count += 1
                        continue
                
                filtered_merged_findings[category] = details
            
            self.nessus_parser.merged_findings = filtered_merged_findings
        
        if excluded_count > 0:
            log.info(f"Excluded {excluded_count} findings based on client-specific exclusions") 