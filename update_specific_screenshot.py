#!/usr/bin/env python3
# Specific Screenshot Updater for findings in Plextrac
# Based on components from n2p_ng.py

import sys
import os
import pretty_errors
import argparse
import json

# Import helpers from n2p_ng
try:
    from helpers import (
        log, RequestHandler, URLManager, FlawUpdater
    )
    from helpers.custom_logger import setup_logging
except ImportError:
    # Add the current directory to path for finding helper modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    try:
        from helpers import (
            log, RequestHandler, URLManager, FlawUpdater
        )
        from helpers.custom_logger import setup_logging
    except ImportError as e:
        print(f"Error importing helpers: {e}")
        print("Current sys.path:")
        for p in sys.path:
            print(f"  {p}")
        sys.exit(1)

# Disable SSL warnings
import requests
requests.packages.urllib3.disable_warnings()

class ScreenshotSpecificUpdater:
    """Tool to update a specific screenshot for a specific flaw in Plextrac."""
    
    def __init__(self, args):
        self.args = args
        self.initialize()
        
    def initialize(self):
        """Initialize components."""
        BASE_URL = f'https://{self.args.target_plextrac}.kevlar.bulletproofsi.net/'
        self.url_manager = URLManager(self.args, BASE_URL)
        self.request_handler = RequestHandler(None)
        self.access_token = self.get_access_token()
        self.request_handler.access_token = self.access_token
        
        # Create a simple converter stub with organized_descriptions
        class SimpleConverter:
            def __init__(self):
                self.organized_descriptions = {}
        
        self.converter = SimpleConverter()
        self.screenshot_uploader = FlawUpdater(self.converter, self.args, self.request_handler, self.url_manager)
        
    def get_access_token(self):
        """Authenticate and obtain access token."""
        auth_url = self.url_manager.authenticate_url
        headers = {'Content-Type': 'application/json'}
        payload = {
            'username': self.args.username,
            'password': self.args.password
        }
        
        response = self.request_handler.post(auth_url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            return data.get('token')
        else:
            raise Exception(f"Failed to authenticate to Plextrac: {response.status_code} - {response.text}")
    
    def upload_specific_screenshot(self):
        """Upload a specific screenshot to a specific flaw."""
        flaw_id = self.args.flaw_id
        screenshot_path = os.path.join(self.args.screenshot_dir, self.args.screenshot_file)
        
        log.info(f"Uploading screenshot {self.args.screenshot_file} to flaw ID {flaw_id}")
        
        if not os.path.exists(screenshot_path):
            log.error(f"Screenshot file not found: {screenshot_path}")
            return False
            
        # Extract MD5 from filename if it's an MD5 hash
        import re
        md5_pattern = re.compile(r'^([a-f0-9]{32})\.png$', re.IGNORECASE)
        filename = os.path.basename(screenshot_path)
        md5_match = md5_pattern.match(filename)
        
        if md5_match:
            md5_hash = md5_match.group(1)
            log.debug(f"Extracted MD5 hash from filename: {md5_hash}")
        else:
            # Generate a random MD5-like hash
            import hashlib
            import time
            md5_hash = hashlib.md5(f"{time.time()}".encode()).hexdigest()
            log.debug(f"Generated random MD5 hash: {md5_hash}")
        
        # Prepare the screenshot for upload
        try:
            with open(screenshot_path, 'rb') as f:
                screenshot_bytes = {'file': (filename, f, 'image/png')}
                
                # Upload the screenshot
                url = self.url_manager.get_upload_screenshot_url()
                log.debug(f"Uploading to URL: {url}")
                response = self.request_handler.post(url, files=screenshot_bytes)
                
                if response.status_code == 200:
                    log.success(f"Screenshot uploaded successfully")
                    
                    # Get the exhibit ID
                    data = response.json()
                    exhibit_id = data.get('id')
                    log.debug(f"Got exhibit ID: {exhibit_id}")
                    
                    # Add the exhibit to the finding
                    if exhibit_id:
                        finding_url = self.url_manager.get_finding_url(flaw_id)
                        log.debug(f"Getting current finding details from: {finding_url}")
                        finding_response = self.request_handler.get(finding_url)
                        
                        if finding_response.status_code == 200:
                            finding_data = finding_response.json()
                            
                            # Get current exhibits if any
                            exhibits = finding_data.get('exhibits', [])
                            
                            # Add new exhibit
                            new_exhibit = {
                                "exhibitID": exhibit_id,
                                "caption": f"Screenshot - {os.path.splitext(filename)[0]}",
                                "type": "png"
                            }
                            
                            exhibits.append(new_exhibit)
                            
                            # Update the finding
                            update_url = self.url_manager.get_update_finding_url(flaw_id)
                            update_payload = {
                                "exhibits": exhibits,
                                "references": f"<p>{md5_hash}</p>" + finding_data.get('references', '')
                            }
                            
                            log.debug(f"Updating finding at URL: {update_url}")
                            update_response = self.request_handler.post(update_url, json=update_payload)
                            
                            if update_response.status_code == 200:
                                log.success(f"Successfully attached screenshot to flaw ID {flaw_id}")
                                return True
                            else:
                                log.error(f"Failed to update finding with exhibit. Status: {update_response.status_code}, Response: {update_response.text}")
                        else:
                            log.error(f"Failed to get finding details. Status: {finding_response.status_code}")
                    else:
                        log.error("No exhibit ID returned from screenshot upload")
                else:
                    log.error(f"Failed to upload screenshot. Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            log.error(f"Error uploading screenshot: {str(e)}")
            
        return False

def parse_args():
    parser = argparse.ArgumentParser(description="Upload a specific screenshot to a specific flaw in Plextrac")
    parser.add_argument("-u", "--username", required=True, help="Plextrac username")
    parser.add_argument("-p", "--password", required=True, help="Plextrac password")
    parser.add_argument("-c", "--client_id", required=True, help="Client ID in Plextrac")
    parser.add_argument("-r", "--report_id", required=True, help="Report ID in Plextrac")
    parser.add_argument("-f", "--flaw_id", required=True, help="Flaw ID to update")
    parser.add_argument("-t", "--target_plextrac", required=True, choices=["report"], help="Target Plextrac server")
    parser.add_argument("-ss", "--screenshot_dir", required=True, help="Directory containing screenshots")
    parser.add_argument("-sf", "--screenshot_file", required=True, help="Screenshot filename to upload")
    parser.add_argument("-s", "--scope", required=True, 
                        choices=["internal", "external", "mobile", "web", "surveillance"],
                        help="Scope/Tag for the findings")
    parser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2], default=1, 
                        help="Increase output verbosity")
    return parser.parse_args()

def main():
    args = parse_args()
    setup_logging(args.verbosity)
    
    log.info(f"Starting specific screenshot update for flaw ID {args.flaw_id}")
    
    updater = ScreenshotSpecificUpdater(args)
    updater.upload_specific_screenshot()
    
    log.info("Specific screenshot update process completed")

if __name__ == "__main__":
    main() 