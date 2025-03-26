#!/usr/bin/env python3
# Debug script to check screenshot hashes and findings references
import os
import re
import hashlib
import sys
import json
import glob
from pprint import pprint

# Configuration - update these paths as needed
SCREENSHOT_DIR = '/Users/pentester/work/GAN/MA/Gan_Boston_Harbour_Internal_Scan'

def get_md5_hash_from_plugin_name(plugin_name):
    """Generate MD5 hash from a plugin name (lowercase)."""
    return hashlib.md5(plugin_name.lower().encode()).hexdigest()

def scan_screenshots():
    """Scan the screenshot directory for files and return their details."""
    screenshots = {}
    extensions = ['.png', '.jpg', '.jpeg']
    
    # Find all files with relevant extensions
    for ext in extensions:
        for file_path in glob.glob(os.path.join(SCREENSHOT_DIR, f'*{ext}')):
            file_name = os.path.basename(file_path)
            base_name = os.path.splitext(file_name)[0]
            
            # Check if the filename is an MD5 hash (32 hex characters)
            if re.match(r'^[a-f0-9]{32}$', base_name, re.IGNORECASE):
                screenshots[base_name] = {
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'extension': ext
                }
    
    return screenshots

def check_existing_flaws():
    """Check existing flaws file for MD5 hashes in references fields."""
    flaws_with_hashes = {}
    md5_pattern = re.compile(r'[a-f0-9]{32}', re.IGNORECASE)
    
    # Try to find the existing_flaws.json file
    for search_dir in ['.', SCREENSHOT_DIR]:
        file_path = os.path.join(search_dir, 'existing_flaws.json')
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    existing_flaws = json.load(f)
                    
                    for flaw_id, flaw_data in existing_flaws.items():
                        references = flaw_data.get('references', '')
                        hashes = md5_pattern.findall(references)
                        if hashes:
                            flaws_with_hashes[flaw_id] = {
                                'title': flaw_data.get('title', ''),
                                'hashes': hashes
                            }
                            
                    print(f"Found {len(existing_flaws)} flaws in {file_path}")
                    print(f"Found {len(flaws_with_hashes)} flaws with MD5 hashes in references")
                    return flaws_with_hashes
                    
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading {file_path}: {e}")
    
    print("No existing_flaws.json file found or no hashes found in references.")
    return {}

def check_processed_findings():
    """Check _processed_findings.json to see what flaws have been processed."""
    processed_findings = {}
    
    # Try to find the _processed_findings.json file
    for search_dir in ['.', SCREENSHOT_DIR]:
        file_path = os.path.join(search_dir, '_processed_findings.json')
        if os.path.exists(file_path):
            try:
                with open(file_path, 'r') as f:
                    data = json.load(f)
                    print(f"Found {len(data)} processed findings in {file_path}")
                    return data
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error reading {file_path}: {e}")
    
    print("No _processed_findings.json file found.")
    return {}

def generate_test_hash(finding_title, scope="internal"):
    """Generate a test hash for a finding title with scope prefix."""
    scope_prefix_map = {
        "internal": "[INTERNAL] ",
        "external": "[EXTERNAL] ",
        "mobile": "[MOBILE] ",
        "web": "[WEB] ",
        "surveillance": "[SURV] "
    }
    
    prefix = scope_prefix_map.get(scope, "")
    full_title = prefix + finding_title
    hash_value = hashlib.md5(full_title.lower().encode()).hexdigest()
    return hash_value

def main():
    print("== Screenshot and MD5 Hash Diagnostic Tool ==")
    
    # Scan for screenshots
    screenshots = scan_screenshots()
    print(f"\nFound {len(screenshots)} screenshots in {SCREENSHOT_DIR}:")
    for hash_value, details in screenshots.items():
        print(f"  {hash_value}{details['extension']} ({details['size']} bytes)")
    
    # Check existing flaws for MD5 hashes
    flaws_with_hashes = check_existing_flaws()
    if flaws_with_hashes:
        print("\nFlaws with MD5 hashes in references:")
        for flaw_id, data in flaws_with_hashes.items():
            print(f"  Flaw ID: {flaw_id}, Title: {data['title']}")
            print(f"    Hashes: {', '.join(data['hashes'])}")
    
    # Check processed findings
    processed_findings = check_processed_findings()
    
    # For each processed finding, generate its expected MD5 hash
    print("\nGenerating expected MD5 hashes for processed findings:")
    for finding_id, data in processed_findings.items():
        title = data.get('title', '')
        if title:
            # Try with different scope prefixes
            for scope in ["internal", "external", "mobile", "web", "surveillance"]:
                hash_value = generate_test_hash(title, scope)
                hash_exists = hash_value in screenshots
                print(f"  Finding: {title}")
                print(f"    Scope: {scope}, Hash: {hash_value}, Exists: {hash_exists}")
                
                if hash_exists:
                    print(f"    MATCH FOUND: {hash_value} exists in screenshot directory!")
    
    print("\nDiagnostic complete. Use this information to determine why screenshots aren't working.")

if __name__ == "__main__":
    main() 