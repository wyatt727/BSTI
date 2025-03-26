import re 
from typing import Any, Dict, List, Optional
from helpers.flaw_lister import FlawLister
from helpers.custom_logger import log
import os
import hashlib
import requests
import json
import time

# Check if BeautifulSoup is available
try:
    from bs4 import BeautifulSoup
    BEAUTIFULSOUP_AVAILABLE = True
except ImportError:
    BEAUTIFULSOUP_AVAILABLE = False

class FlawUpdater:
    MERGED_ASSETS_KEY = "merged_assets"
    MERGED_ASSETS_LABEL = "Merged assets"
    PROCESSED_FINDINGS_FILE = "_processed_findings.json" 
    def __init__(self, converter, args, request_handler, url_manager):
        """
        Initialize the FlawUpdater class.

        :param converter: Converter object used for processing descriptions.
        :param args: Arguments passed for the operations.
        :param request_handler: Handler for making HTTP requests.
        :param url_manager: Manager for generating URLs.
        """
        self.args = args
        self.url_manager = url_manager
        self.request_handler = request_handler
        self.processed_flaws = set()
        self.custom_fields = converter.organized_descriptions
        self.flaw_cache = {}
        self.md5_pattern = re.compile(r'([a-fA-F0-9]{32})')
        self.plugin_name_pattern = re.compile(r'<b>([^<]*?)(?: \(severity:.*?\))?</b>')
        self.md5_pattern = re.compile(r'[a-f0-9]{32}', re.IGNORECASE)
        self.url_pattern = re.compile(r'(https?://)')
        self.html_tag_pattern = re.compile(r'<.*?>')
        self.flaw_lister = FlawLister(self.url_manager, self.request_handler)
        mode_map = {
            "internal": "internal",
            "external": "external",
            "web": "web",
            "surveillance": "surveillance",
            "mobile": "mobile"
        }
        self.mode = mode_map.get(self.args.scope, "internal")
        
        # Load any previously processed findings at initialization
        self.previously_processed = self._load_processed_findings()

    def _load_processed_findings(self):
        """Load processed findings from json."""
        if os.path.exists(self.PROCESSED_FINDINGS_FILE):
            try:
                with open(self.PROCESSED_FINDINGS_FILE, "r") as file:
                    data = json.load(file)
                    log.info(f"Loaded {len(data)} previously processed findings")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                log.warning(f"Error loading processed findings file: {e}")
                return {}
        else:
            log.info("No previous processed findings file found")
            return {}

    def _save_processed_findings(self, data: dict) -> None:
        """
        Save all processed findings to a JSON file.

        :param data: A dictionary containing the processed findings data.
        """
        try:
            with open(self.PROCESSED_FINDINGS_FILE, "w") as file:
                json.dump(data, file, indent=4)
            log.debug(f"Saved {len(data)} processed findings to {self.PROCESSED_FINDINGS_FILE}")
        except IOError as e:
            log.error(f"Error saving processed findings: {e}")

    def flaw_update_engine(self, try_by_title_first=False):
        """
        Update findings with screenshots from a specified directory. This method will also
        handle flaws and add custom fields to them.
        
        Args:
            try_by_title_first (bool): If True, try to find screenshots by title hash first
        """
        # Get only new flaws that weren't processed before
        flaws = self.flaw_lister.list_flaws()
        log.debug(f'Found {len(flaws)} flaws')
        
        # Filter out any flaws that were already processed in previous runs
        new_flaws = []
        for flaw in flaws:
            flaw_id = flaw['flaw_id']
            if flaw_id in self.previously_processed:
                log.debug(f"Skipping previously processed flaw ID {flaw_id}")
                continue
            new_flaws.append(flaw)
            
        if not new_flaws:
            log.info("No new flaws to process")
            return
            
        log.info(f"Processing {len(new_flaws)} new flaws")
        
        # Debug information about screenshots
        if self.args.screenshot_dir:
            log.debug(f"Screenshot directory: {self.args.screenshot_dir}")
            import os
            import glob
            screenshot_files = glob.glob(os.path.join(self.args.screenshot_dir, "*"))
            log.debug(f"Found {len(screenshot_files)} files in screenshot directory")
            for file in screenshot_files[:5]:  # Only show first 5 to avoid cluttering logs
                log.debug(f"  Screenshot file: {os.path.basename(file)}")
            
        custom_fields_for_flaw = {}
        for flaw in new_flaws:
            flaw_id = flaw['flaw_id']
            references = flaw.get('references', '')
            title = flaw.get('title', '')
            
            # Generate expected screenshot hash
            title_prefix = self._get_title_prefix()
            full_title = title_prefix + title
            import hashlib
            expected_hash = hashlib.md5(full_title.lower().encode()).hexdigest()
            log.debug(f"Flaw ID {flaw_id} - Title: '{title}' - Expected hash: {expected_hash}")
            
            screenshot_found = False
            
            # Try to find screenshot by title if requested
            if try_by_title_first:
                log.debug(f"Trying to find screenshot by title hash first for flaw ID {flaw_id}")
                screenshot_found = self.try_find_screenshot_by_title(flaw_id, title)
            
            # If not found by title and there are references, try to find by references
            if not screenshot_found and references:
                log.debug(f"Processing references for flaw ID {flaw_id}")
                screenshot_found = self.process_flaw_references(flaw_id, references)
            # If not found by references and not already tried by title, try by title
            elif not screenshot_found and not try_by_title_first and title:
                log.debug(f"Trying to find screenshot by title hash for flaw ID {flaw_id}")
                screenshot_found = self.try_find_screenshot_by_title(flaw_id, title)
            
            if not screenshot_found:
                log.debug(f"No screenshot found for flaw ID {flaw_id}")

            custom_fields_for_flaw[flaw_id] = self.custom_fields.get(flaw_id, {})
        
        self.process_update_finding_with_custom_field(custom_fields_for_flaw, new_flaws)
        # Skip trying to update references since it's causing 404 errors
        # self.clear_md5_hashes_from_references(new_flaws)
        
        # Update the processed findings record with the newly processed flaws
        for flaw in new_flaws:
            flaw_id = flaw['flaw_id']
            self.previously_processed[flaw_id] = {
                'title': flaw.get('title', ''),
                'processed_timestamp': time.time()
            }
        
        # Save the updated processed findings
        self._save_processed_findings(self.previously_processed)
    
    def process_flaw_references(self, flaw_id: str, references: str) -> bool:
        """
        Process references of a given flaw to find MD5 hashes.

        :param flaw_id: The ID of the flaw.
        :param references: The references associated with the flaw.
        :return: True if a screenshot was found and processed, False otherwise
        """
        md5_hashes = self.md5_pattern.findall(references)
        for md5_hash in md5_hashes:
            if self.handle_md5_hashed_screenshot(flaw_id, md5_hash):
                return True
        return False

    def handle_md5_hashed_screenshot(self, flaw_id: str, md5_hash: str) -> bool:
        """
        Handle the screenshot associated with an MD5 hash for a given flaw.

        :param flaw_id: The ID of the flaw.
        :param md5_hash: The MD5 hash of the screenshot.
        :return: True if a screenshot was found and processed, False otherwise
        """
        if not self.args.screenshot_dir:
            log.debug("Screenshot directory is not provided. Skipping screenshot handling.")
            return False
        
        # Try both .png and other extensions for MacOS
        extensions = ['.png', '.jpg', '.jpeg'] if self._get_platform() == 'Darwin' else ['.png']
        screenshot_found = False
        
        for ext in extensions:
            screenshot_path = os.path.join(self.args.screenshot_dir, md5_hash + ext)
            if os.path.isfile(screenshot_path):
                log.debug(f"Found screenshot at path '{screenshot_path}' with MD5 {md5_hash}")
                screenshot_found = True
                with open(screenshot_path, 'rb') as file:
                    file_data = file.read()
                
                content_type = f'image/{ext[1:]}' 
                screenshot_bytes = {'file': (md5_hash + ext, file_data, content_type)}
                exhibit_id = self.upload_screenshot_to_finding(screenshot_bytes)
                if exhibit_id:
                    self.process_successful_upload(flaw_id, exhibit_id, md5_hash)
                    return True
                break
        
        if not screenshot_found:
            self.process_missing_screenshot(flaw_id, md5_hash)
        
        return False

    def process_successful_upload(self, flaw_id: str, exhibit_id: str, md5_hash: str) -> None:
        """
        Handle successful upload of a screenshot.

        :param flaw_id: The ID of the flaw.
        :param exhibit_id: The ID of the uploaded exhibit.
        :param md5_hash: The MD5 hash of the screenshot.
        """
        # Extract the caption (plugin name) for the given MD5 hash
        caption = self.get_caption_from_md5(md5_hash)
        
        log.debug(f"Uploaded screenshot with MD5 {md5_hash} for flaw ID {flaw_id} and received exhibit ID {exhibit_id}")
        self.update_finding(flaw_id, exhibit_id, caption)
        self.processed_flaws.add(flaw_id)

    def get_caption_from_md5(self, md5_hash: str) -> str:
        """
        Get the caption (plugin name) associated with an MD5 hash.

        :param md5_hash: The MD5 hash.
        :return: The caption (plugin name) or 'FIXME' if not found.
        """
        
        for flaw_id, custom_field in self.custom_fields.items():
            plugin_name_matches = self.plugin_name_pattern.findall(custom_field)
            for plugin_name in plugin_name_matches:
                plugin_name = plugin_name.strip().lower()
                generated_md5 = hashlib.md5(plugin_name.encode()).hexdigest()
                if generated_md5 == md5_hash:
                    return plugin_name
        return "FIXME"

    def process_missing_screenshot(self, flaw_id: str, md5_hash: str) -> None:
        """
        Handle cases where no screenshot is found for a given MD5 hash.

        :param flaw_id: The ID of the flaw.
        :param md5_hash: The MD5 hash of the screenshot.
        """
        log.debug(f"No screenshot found for MD5 hash '{md5_hash}' related to flaw ID {flaw_id}")
        self.processed_flaws.add(flaw_id)

    def get_existing_fields_for_flaw(self, flaw_id):
        """
        Fetch the existing fields for a given flaw.

        :param flaw_id: ID of the flaw.
        :return: A tuple containing the fields and the title for the flaw.
        """
        if flaw_id in self.flaw_cache:
            return self.flaw_cache[flaw_id]
        url = self.url_manager.get_update_finding_url(flaw_id)
        response = self.request_handler.get(url)
        if response.status_code == 200:
            content = response.json()
            fields = content.get("fields", [])
            title = content.get("title", "")

            if not isinstance(fields, list):
                fields = []
            
            self.flaw_cache[flaw_id] = (fields, title)
            return fields, title
        else:
            log.error(f"Failed to fetch fields for flaw ID {flaw_id}")
            return [], ""

        
    def process_update_finding_with_custom_field(self, custom_fields_for_flaw, flaws):
        """
        Process and update the finding with custom fields.

        :param custom_fields_for_flaw: Dictionary containing custom fields for each flaw.
        """
        if not self.processed_flaws:
            self.add_missing_flaws(flaws)
        for flaw_id in self.processed_flaws:
            self.update_finding_with_custom_field(flaw_id, custom_fields_for_flaw.get(flaw_id, {}))

    def add_missing_flaws(self, flaws):
        for flaw in flaws:
            self.processed_flaws.add(flaw['flaw_id'])

    def find_screenshot(self, flaw_name):
        """
        Search for a screenshot based on the MD5 hash of the flaw name, adjusting names based on scope.
        """
        title_prefix = self._get_title_prefix()
        flaw_name = title_prefix + flaw_name

        # Convert flaw name to lowercase and compute its MD5 hash
        flaw_name_md5 = hashlib.md5(flaw_name.lower().encode()).hexdigest()
        
        # Try multiple extensions on MacOS
        if self._get_platform() == 'Darwin':
            extensions = ['.png', '.jpg', '.jpeg']
        else:
            extensions = ['.png']
        
        for ext in extensions:
            flaw_name_md5_with_extension = flaw_name_md5 + ext
            screenshot_path = os.path.join(self.args.screenshot_dir, flaw_name_md5_with_extension)
            
            if os.path.isfile(screenshot_path):
                log.debug(f"Found screenshot at path '{screenshot_path}' for flaw name '{flaw_name}'")
                with open(screenshot_path, 'rb') as file:
                    file_data = file.read()
                content_type = f'image/{ext[1:]}'
                return {'file': (flaw_name_md5_with_extension, file_data, content_type)}
        
        log.warning(f"No screenshot found for flaw name '{flaw_name}'")
        return None

    def upload_screenshot_to_finding(self, screenshot_bytes):
        """
        Upload a screenshot to a finding.

        :param screenshot_bytes: Byte data of the screenshot.
        :return: The exhibit ID if the upload is successful, otherwise None.
        """
        if not screenshot_bytes:
            log.debug("No screenshot bytes provided, skipping upload")
            return None
            
        url = self.url_manager.get_upload_screenshot_url()
        log.debug(f"Upload URL: {url}")
        
        # Extract filename from screenshot_bytes for debugging
        filename = screenshot_bytes.get('file', ('unknown',))[0]
        log.debug(f"Uploading screenshot with filename: {filename}")
        
        try:
            # For MacOS compatibility, add extra debugging
            if self._get_platform() == 'Darwin':
                log.debug(f"MacOS detected: Uploading screenshot with URL: {url}")
                log.debug(f"Screenshot filename: {filename}")
            
            response = self.request_handler.post(url, files=screenshot_bytes)
            log.debug(f"Upload response status code: {response.status_code}")
            
            if response.status_code == 200:
                log.debug('Screenshot uploaded successfully')
                try:
                    content = response.json()
                    exhibit_id = content.get("id")
                    log.debug(f"Received exhibit ID: {exhibit_id}")
                    return exhibit_id
                except Exception as e:
                    log.error(f"Failed to parse response JSON: {str(e)}")
                    log.debug(f"Response content: {response.content}")
                    return None
            else:
                log.error(f'Failed to upload screenshot: Status code {response.status_code}')
                log.debug(f'Response content: {response.content}')
                return None
        except Exception as e:
            log.error(f"Exception during screenshot upload: {str(e)}")
            return None
            
    def clear_md5_hashes_from_references(self, flaws):
        """
        Clear the MD5 hashes from the references of the flaws.

        :param flaws: The flaws to update.
        """
        for flaw in flaws:
            flaw_id = flaw.get('flaw_id')
            references = flaw.get('references', '')
            md5_hashes = self.md5_pattern.findall(references)
            if md5_hashes:
                for md5_hash in md5_hashes:
                    if md5_hash in references:
                        # Replace the MD5 hash with an empty string
                        references = references.replace(md5_hash, '')
                        log.debug(f"Removed MD5 hash '{md5_hash}' from references for flaw ID {flaw_id}")
                
                # Clean up any extra line breaks that might have been left behind
                references = re.sub(r'\n{3,}', '\n\n', references)
                references = references.strip()
                
                # Only update if the references have actually changed
                if references != flaw.get('references', ''):
                    self.update_references(flaw_id, references)

    def update_references(self, flaw_id, references):
        """
        Update the references for a flaw.

        :param flaw_id: The ID of the flaw.
        :param references: The new references for the flaw.
        """
        url = self.url_manager.get_update_finding_url(flaw_id)
        payload = {
            'references': references
        }
        try:
            response = self.request_handler.patch(url, json=payload)
            if response.status_code == 200:
                log.debug(f"Updated references for flaw ID {flaw_id}")
                return True
            else:
                log.error(f"Failed to update references for flaw ID {flaw_id}")
                log.debug(f"Response content: {response.content}")
                return False
        except Exception as e:
            log.error(f"Exception while updating references for flaw ID {flaw_id}: {str(e)}")
            return False

    def update_finding_with_custom_field(self, flaw_id, custom_field):
        """
        Update a finding with a custom field.

        :param flaw_id: The ID of the flaw.
        :param custom_field: The custom field to add.
        """
        if not custom_field:
            log.debug(f"No custom field specified for flaw ID {flaw_id}. Skipping.")
            return

        custom_field_value = custom_field
        current_fields, title = self.get_existing_fields_for_flaw(flaw_id)
        
        # Check if the field already exists
        for field in current_fields:
            if field.get('key') == 'remediation':
                # Update the field with the custom field value
                field['value'] = custom_field_value
                break
        else:
            # No matching field found, create a new one
            current_fields.append({
                'key': 'remediation',
                'label': 'Detailed Information and Remediation',
                'value': custom_field_value
            })

        # Prepare the payload
        payload = {
            'fields': current_fields,
        }

        # Send the update
        url = self.url_manager.get_update_finding_url(flaw_id)
        response = self.request_handler.patch(url, json=payload)
        if response.status_code == 200:
            log.debug(f"Updated custom field for flaw ID {flaw_id}")
        else:
            log.error(f"Failed to update custom field for flaw ID {flaw_id}")
            log.debug(response.content)

    def get_current_exhibits(self, flaw_id):
        """
        Get the current exhibits for a flaw.

        :param flaw_id: The ID of the flaw.
        :return: The current exhibits for the flaw.
        """
        url = self.url_manager.get_finding_url(flaw_id)
        response = self.request_handler.get(url)
        if response.status_code == 200:
            content = response.json()
            return content.get('exhibits', [])
        else:
            log.error(f"Failed to get current exhibits for flaw ID {flaw_id}")
            return []
            
    def update_finding(self, flaw_id, exhibit_id, caption):
        """
        Update a finding with a new exhibit (screenshot).

        :param flaw_id: ID of the flaw to update.
        :param exhibit_id: ID of the exhibit (screenshot) to add to the finding.
        """
        # Fetch current exhibits
        current_exhibits = self.get_current_exhibits(flaw_id)
        
        # Create a new exhibit and append to the list of current exhibits
        new_exhibit = {
            'type': 'image/png',
            'caption': caption,
            'exhibitID': exhibit_id,
            'index': len(current_exhibits) + 1  # Set the index to be the next one in the list
        }
        current_exhibits.append(new_exhibit)
        
        variables = {
            'clientId': int(self.args.client_id),
            'data': {'exhibits': current_exhibits},
            'findingId': float(flaw_id),
            'reportId': int(self.args.report_id),
        }

        response = self.execute_graphql_query('FindingUpdate', variables)
        
        if response:
            log.debug('Finding updated with screenshot successfully')

    def execute_graphql_query(self, operation_name: str, variables: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute a GraphQL query and return the response.

        :param operation_name: The operation name for the GraphQL query.
        :param variables: The variables to be used in the GraphQL query.
        :return: Response JSON as a dictionary, or None if the query fails.
        """
        url = self.url_manager.get_graphql_url()
        query =  "mutation FindingUpdate($clientId: Int!, $data: FindingUpdateInput!, $findingId: Float!, $reportId: Int!) {\n  findingUpdate(\n    clientId: $clientId\n    data: $data\n    findingId: $findingId\n    reportId: $reportId\n  ) {\n    ... on FindingUpdateSuccess {\n      finding {\n        ...FindingFragment\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n}\n\nfragment FindingFragment on Finding {\n  assignedTo\n  closedAt\n  createdAt\n  code_samples {\n    caption\n    code\n    id\n    __typename\n  }\n  common_identifiers {\n    CVE {\n      name\n      id\n      year\n      link\n      __typename\n    }\n    CWE {\n      name\n      id\n      link\n      __typename\n    }\n    __typename\n  }\n  description\n  exhibits {\n    assets {\n      asset\n      id\n      __typename\n    }\n    caption\n    exhibitID\n    index\n    type\n    __typename\n  }\n  fields {\n    key\n    label\n    value\n    __typename\n  }\n  flaw_id\n  includeEvidence\n  recommendations\n  references\n  scores\n  selectedScore\n  severity\n  source\n  status\n  subStatus\n  tags\n  title\n  visibility\n  calculated_severity\n  risk_score {\n    CVSS3_1 {\n      overall\n      vector\n      subScore {\n        base\n        temporal\n        environmental\n        __typename\n      }\n      __typename\n    }\n    CVSS3 {\n      overall\n      vector\n      subScore {\n        base\n        temporal\n        environmental\n        __typename\n      }\n      __typename\n    }\n    CVSS2 {\n      overall\n      vector\n      subScore {\n        base\n        temporal\n        __typename\n      }\n      __typename\n    }\n    CWSS {\n      overall\n      vector\n      subScore {\n        base\n        environmental\n        attackSurface\n        __typename\n      }\n      __typename\n    }\n    __typename\n  }\n  hackerOneData {\n    bountyAmount\n    programId\n    programName\n    remoteId\n    __typename\n  }\n  snykData {\n    issueType\n    pkgName\n    issueUrl\n    identifiers {\n      CVE\n      CWE\n      __typename\n    }\n    exploitMaturity\n    patches\n    nearestFixedInVersion\n    isMaliciousPackage\n    violatedPolicyPublicId\n    introducedThrough\n    fixInfo {\n      isUpgradable\n      isPinnable\n      isPatchable\n      isFixable\n      isPartiallyFixable\n      nearestFixedInVersion\n      __typename\n    }\n    __typename\n  }\n  edgescanData {\n    id\n    portal_url\n    details {\n      html\n      id\n      orginal_detail_hash\n      parameter_name\n      parameter_type\n      port\n      protocol\n      screenshot_urls {\n        file\n        id\n        medium_thumb\n        small_thumb\n        __typename\n      }\n      src\n      type\n      __typename\n    }\n    __typename\n  }\n  __typename\n}\n"

        payload = {
            "operationName": operation_name,
            "variables": variables,
            "query": query
        }

        response = self.request_handler.post(url, json=payload)
        if response.status_code == 200:
            return response.json()
        else:
            log.error(f"Failed to execute GraphQL query '{operation_name}'")
            log.debug(response.content)
            return None

    def _get_platform(self):
        """Get the operating system platform."""
        import platform
        return platform.system()

    def _get_title_prefix(self):
        """Get the title prefix based on the scope."""
        scope_mapping = {
            "internal": "[INTERNAL] ",
            "external": "[EXTERNAL] ",
            "mobile": "[MOBILE] ",
            "web": "[WEB] ",
            "surveillance": "[SURV] "
        }
        return scope_mapping.get(self.args.scope, "")

    def try_find_screenshot_by_title(self, flaw_id, title):
        """
        Try to find a screenshot based on the MD5 hash of the flaw title.
        
        :param flaw_id: The ID of the flaw.
        :param title: The title of the flaw.
        :return: True if a screenshot was found and processed, False otherwise
        """
        if not self.args.screenshot_dir or not title:
            log.debug(f"Screenshot directory not provided or title empty for flaw ID {flaw_id}")
            return False

        title_prefix = self._get_title_prefix()
        full_title = title_prefix + title
        log.debug(f"Looking for screenshot for '{full_title}'")
        
        import hashlib
        import os
        import glob
        
        # Generate MD5 hash of the full title
        hash_value = hashlib.md5(full_title.lower().encode()).hexdigest()
        log.debug(f"Generated hash value: {hash_value}")
        
        # Try different extensions
        extensions = ['.png', '.jpg', '.jpeg'] if self._get_platform() == 'Darwin' else ['.png']
        screenshot_found = False
        
        # First try with the main title hash
        for ext in extensions:
            screenshot_path = os.path.join(self.args.screenshot_dir, hash_value + ext)
            log.debug(f"Looking for screenshot at path: {screenshot_path}")
            if os.path.isfile(screenshot_path):
                log.debug(f"Found screenshot at path '{screenshot_path}' with title hash {hash_value}")
                screenshot_found = True
                with open(screenshot_path, 'rb') as file:
                    file_data = file.read()
                
                content_type = f'image/{ext[1:]}' 
                screenshot_bytes = {'file': (hash_value + ext, file_data, content_type)}
                log.debug(f"Uploading screenshot with filename: {hash_value + ext}")
                exhibit_id = self.upload_screenshot_to_finding(screenshot_bytes)
                if exhibit_id:
                    log.info(f"Successfully uploaded screenshot for flaw '{title}' with ID {flaw_id}")
                    self.process_successful_upload(flaw_id, exhibit_id, hash_value)
                    return True
                else:
                    log.error(f"Failed to upload screenshot for flaw '{title}' with ID {flaw_id}")
                break
        
        # Special handling for grouped findings like "Software Components Out of Date and Vulnerable"
        if not screenshot_found and "Software Components Out of Date" in title:
            log.debug(f"Looking for component-specific screenshots for grouped finding: {title}")
            
            # Extract component names from custom fields if available
            if flaw_id in self.custom_fields:
                # Parse the HTML to extract component names
                if not BEAUTIFULSOUP_AVAILABLE:
                    log.warning("BeautifulSoup not installed. Cannot parse component names for screenshots.")
                    log.warning("To enable this feature, install BeautifulSoup: pip install beautifulsoup4")
                else:
                    # Get the custom field content which contains description of components
                    content = self.custom_fields.get("Software Components Out of Date and Vulnerable", "")
                    if content:
                        try:
                            # Extract component names (they are in <b> tags)
                            soup = BeautifulSoup(content, 'html.parser')
                            component_titles = []
                            
                            # Look for patterns like "Apache Lack of Updates" or similar
                            for bold_tag in soup.find_all('b'):
                                text = bold_tag.text
                                # Extract the component name (everything before " Lack of Updates")
                                match = re.match(r"([^(]+?)\s+Lack of Updates", text)
                                if match:
                                    component_name = match.group(1).strip()
                                    component_titles.append(component_name)
                            
                            log.debug(f"Found {len(component_titles)} component names in the description")
                            
                            # Look for screenshots for each component
                            for component_name in component_titles:
                                # Generate hash for the component name with prefix
                                component_full_name = title_prefix + component_name
                                component_hash = hashlib.md5(component_full_name.lower().encode()).hexdigest()
                                log.debug(f"Looking for component screenshot with hash: {component_hash} for '{component_name}'")
                                
                                # Check for component screenshot
                                for ext in extensions:
                                    component_path = os.path.join(self.args.screenshot_dir, component_hash + ext)
                                    if os.path.isfile(component_path):
                                        log.debug(f"Found component screenshot: {component_path}")
                                        with open(component_path, 'rb') as file:
                                            file_data = file.read()
                                        
                                        content_type = f'image/{ext[1:]}' 
                                        screenshot_bytes = {'file': (component_hash + ext, file_data, content_type)}
                                        exhibit_id = self.upload_screenshot_to_finding(screenshot_bytes)
                                        if exhibit_id:
                                            log.info(f"Uploaded component screenshot for '{component_name}' to grouped finding '{title}'")
                                            self.process_successful_upload(flaw_id, exhibit_id, component_hash)
                                            screenshot_found = True
                                            # Continue looking for more component screenshots to upload all of them
                        except Exception as e:
                            log.error(f"Error parsing component names for screenshots: {str(e)}")
        
        if not screenshot_found:
            log.debug(f"No screenshot found with hash {hash_value} for flaw title '{title}'")
            
        return screenshot_found