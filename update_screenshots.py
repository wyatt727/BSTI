#!/usr/bin/env python3
# Screenshot Updater for existing findings in Plextrac
# Based on components from n2p_ng.py

import sys
import os
import pretty_errors
import argparse
import json

# Import helpers from n2p_ng
try:
    from helpers import (
        ArgumentParser, log, ArgumentValidator, PlextracHandler, RequestHandler, URLManager,
        ConfigLoader, FlawUpdater, FlawLister
    )
    from helpers.custom_logger import setup_logging
except ImportError:
    # Add the current directory to path for finding helper modules
    current_dir = os.path.dirname(os.path.abspath(__file__))
    if current_dir not in sys.path:
        sys.path.append(current_dir)
    try:
        from helpers import (
            ArgumentParser, log, ArgumentValidator, PlextracHandler, RequestHandler, URLManager,
            ConfigLoader, FlawUpdater, FlawLister
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

class ScreenshotUpdater:
    """Tool to update screenshots for existing flaws in Plextrac."""
    
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
        self.plextrac_handler = PlextracHandler(self.access_token, self.request_handler, self.url_manager)
        self.config = ConfigLoader.load_config('N2P_config.json')
        
        # Create a simple converter stub with organized_descriptions
        class SimpleConverter:
            def __init__(self):
                self.organized_descriptions = {}
        
        self.converter = SimpleConverter()
        self.flaw_lister = FlawLister(self.url_manager, self.request_handler)
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
    
    def force_update_flaws(self):
        """Force update of screenshots for all flaws, bypassing the exclude filter."""
        log.info("Forcing update of screenshots for existing flaws...")
        
        # Modified version of flaw_update_engine that ignores exclusion list
        flaws = self.flaw_lister.get_existing_flaws()  # Get all flaws
        
        log.debug(f'Found {len(flaws)} flaws to process')
        
        for flaw in flaws:
            flaw_id = flaw.get('flaw_id')
            references = flaw.get('references', '')
            title = flaw.get('title', '')
            
            log.info(f"Processing screenshots for flaw ID {flaw_id}: {title}")
            
            # Try to find screenshot by title
            screenshot_found = self.screenshot_uploader.try_find_screenshot_by_title(flaw_id, title)
            
            # If not found by title and there are references, try references
            if not screenshot_found and references:
                screenshot_found = self.screenshot_uploader.process_flaw_references(flaw_id, references)
                
            if screenshot_found:
                log.success(f"Successfully uploaded screenshot for flaw ID {flaw_id}")
            else:
                log.warning(f"No screenshot found for flaw ID {flaw_id}")

def parse_args():
    parser = argparse.ArgumentParser(description="Update screenshots for existing flaws in Plextrac")
    parser.add_argument("-u", "--username", required=True, help="Plextrac username")
    parser.add_argument("-p", "--password", required=True, help="Plextrac password")
    parser.add_argument("-c", "--client_id", required=True, help="Client ID in Plextrac")
    parser.add_argument("-r", "--report_id", required=True, help="Report ID in Plextrac")
    parser.add_argument("-t", "--target_plextrac", required=True, choices=["report"], help="Target Plextrac server")
    parser.add_argument("-ss", "--screenshot_dir", required=True, help="Directory containing screenshots")
    parser.add_argument("-s", "--scope", required=True, 
                        choices=["internal", "external", "mobile", "web", "surveillance"],
                        help="Scope/Tag for the findings")
    parser.add_argument("-v", "--verbosity", type=int, choices=[0, 1, 2], default=1, 
                        help="Increase output verbosity")
    return parser.parse_args()

def main():
    args = parse_args()
    setup_logging(args.verbosity)
    
    log.info("Starting screenshot update for existing flaws")
    
    updater = ScreenshotUpdater(args)
    updater.force_update_flaws()
    
    log.info("Screenshot update process completed")

if __name__ == "__main__":
    main() 