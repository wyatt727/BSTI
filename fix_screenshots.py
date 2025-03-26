#!/usr/bin/env python3
# Tool to fix screenshot filenames to match the expected MD5 hashes based on finding titles
import os
import re
import hashlib
import sys
import json
import glob
import shutil
from pprint import pprint

# Configuration - update these paths as needed
SCREENSHOT_DIR = '/Users/pentester/work/GAN/MA/Gan_Boston_Harbour_Internal_Scan'
OUTPUT_DIR = '/Users/pentester/work/GAN/MA/Gan_Boston_Harbour_Internal_Scan_Fixed'

def get_md5_hash_from_plugin_name(plugin_name, scope="internal"):
    """Generate MD5 hash from a plugin name with scope prefix (lowercase)."""
    scope_prefix_map = {
        "internal": "[INTERNAL] ",
        "external": "[EXTERNAL] ",
        "mobile": "[MOBILE] ",
        "web": "[WEB] ",
        "surveillance": "[SURV] "
    }
    prefix = scope_prefix_map.get(scope, "")
    full_title = prefix + plugin_name
    return hashlib.md5(full_title.lower().encode()).hexdigest()

def scan_screenshots():
    """Scan the screenshot directory for files and return their details."""
    screenshots = {}
    extensions = ['.png', '.jpg', '.jpeg']
    
    # Find all files with relevant extensions
    for ext in extensions:
        for file_path in glob.glob(os.path.join(SCREENSHOT_DIR, f'*{ext}')):
            file_name = os.path.basename(file_path)
            # Skip processing of non-image files like CSVs or HTML
            if not file_name.lower().endswith(tuple(extensions)):
                continue
                
            base_name = os.path.splitext(file_name)[0]
            
            # Check if the filename is an MD5 hash (32 hex characters)
            if re.match(r'^[a-f0-9]{32}$', base_name, re.IGNORECASE):
                screenshots[base_name] = {
                    'path': file_path,
                    'size': os.path.getsize(file_path),
                    'extension': os.path.splitext(file_name)[1]
                }
    
    return screenshots

def load_processed_findings():
    """Load processed findings from _processed_findings.json"""
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

def map_findings_to_screenshots():
    """Map findings to screenshots by their names"""
    processed_findings = load_processed_findings()
    unique_findings = {}
    
    # Remove duplicate entries and keep only unique finding titles
    for finding_id, data in processed_findings.items():
        title = data.get('title', '')
        if title and title not in unique_findings:
            unique_findings[title] = finding_id
    
    return unique_findings

def create_mapping_file(original_screenshots, generated_hashes):
    """Create a JSON mapping file showing the original -> new screenshot name mappings"""
    mapping = {}
    for original, details in original_screenshots.items():
        extension = details['extension']
        for title, hash_value in generated_hashes.items():
            mapping[f"{original}{extension}"] = f"{hash_value}{extension}"
    
    with open(os.path.join(OUTPUT_DIR, 'screenshot_mapping.json'), 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"Created screenshot mapping file in {os.path.join(OUTPUT_DIR, 'screenshot_mapping.json')}")

def copy_screenshots_with_new_names():
    """Copy screenshots with new names based on finding titles"""
    screenshots = scan_screenshots()
    findings = map_findings_to_screenshots()
    
    # Create output directory if it doesn't exist
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Store mapping for later reference
    mapping = {}
    
    # For each unique finding, generate hashes for different scopes
    hash_count = 0
    
    for title in findings.keys():
        for scope in ["internal", "external", "mobile", "web", "surveillance"]:
            hash_value = get_md5_hash_from_plugin_name(title, scope)
            
            # Check if we have screenshots to copy
            if screenshots:
                # Just copy all screenshots for each finding with the new hash name
                for i, (original_hash, details) in enumerate(screenshots.items()):
                    original_path = details['path']
                    extension = details['extension']
                    new_filename = f"{hash_value}{extension}"
                    new_path = os.path.join(OUTPUT_DIR, new_filename)
                    
                    # Copy the file
                    shutil.copy2(original_path, new_path)
                    print(f"Copied {original_path} to {new_path}")
                    
                    # Add to mapping
                    original_filename = os.path.basename(original_path)
                    mapping[original_filename] = new_filename
                    
                    hash_count += 1
                    
                    # Only copy the first screenshot for each finding/scope to avoid duplicates
                    break
    
    # Save the mapping
    with open(os.path.join(OUTPUT_DIR, 'screenshot_mapping.json'), 'w') as f:
        json.dump(mapping, f, indent=2)
    
    print(f"Created {hash_count} new screenshot files with proper hash names")
    print(f"Mapping saved to {os.path.join(OUTPUT_DIR, 'screenshot_mapping.json')}")

def main():
    print("== Screenshot Fixer Tool ==")
    
    # Scan for screenshots
    screenshots = scan_screenshots()
    print(f"\nFound {len(screenshots)} screenshots in {SCREENSHOT_DIR}")
    
    # Create renamed copies
    copy_screenshots_with_new_names()
    
    print("\nScreenshot fixing complete. Use the files in the output directory with the n2p_ng.py script.")
    print(f"Command example: python3 n2p_ng.py -c 78308 -r 356839437 -u wyatt.becker@bulletproofsi.com -ss {OUTPUT_DIR} -d /Users/pentester/work/GAN/MA/Gan_Boston_Harbour_Internal_Scan -p 'SecurePass!1' -t report")

if __name__ == "__main__":
    main() 