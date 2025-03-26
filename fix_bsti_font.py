#!/usr/bin/env python3
"""
BSTI Font Fix Script

This script fixes the font configuration in BSTI to avoid segmentation faults
by replacing the problematic 'Segoe UI' font with an available system font.
"""

import os
import sys
import shutil
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFontDatabase

def main():
    """Apply font fixes to BSTI configuration."""
    print("BSTI Font Fix Script")
    print("====================")
    
    # Check if the config file exists
    config_path = os.path.join('src', 'config', 'config.py')
    if not os.path.exists(config_path):
        print(f"Error: Config file not found at {config_path}")
        print("Make sure you're running this script from the BSTI root directory.")
        return 1
    
    # Create a Qt application to query available fonts
    app = QApplication([])
    font_db = QFontDatabase()
    available_fonts = font_db.families()
    
    print(f"Found {len(available_fonts)} fonts on your system")
    
    # Look for suitable system fonts in order of preference
    system_font = None
    preferred_fonts = ['Arial', 'Helvetica', 'Tahoma', 'Verdana', 'San Francisco', '.SF NS Text', 'Lucida Grande']
    
    for font in preferred_fonts:
        if font in available_fonts:
            system_font = font
            print(f"Selected '{font}' as replacement font")
            break
    
    if not system_font:
        # Fallback to first available font
        system_font = available_fonts[0] if available_fonts else "Arial"
        print(f"Fallback to '{system_font}' as replacement font")
    
    # Backup the original config file
    backup_path = f"{config_path}.bak"
    if not os.path.exists(backup_path):
        shutil.copy(config_path, backup_path)
        print(f"Original config backed up to {backup_path}")
    
    # Read the config file
    try:
        with open(config_path, 'r') as f:
            config_content = f.read()
        
        # Replace the font family line
        old_font_line = 'FONT_FAMILY = "Segoe UI, Arial, sans-serif"'
        new_font_line = f'FONT_FAMILY = "{system_font}, Arial, sans-serif"'
        
        if old_font_line in config_content:
            modified_content = config_content.replace(old_font_line, new_font_line)
            
            # Write the modified config
            with open(config_path, 'w') as f:
                f.write(modified_content)
            
            print(f"Font setting changed from '{old_font_line}' to '{new_font_line}'")
            print("Fix applied successfully!")
        else:
            print("Could not find the font setting line in config.py.")
            print("Manual fix required: Change the font in src/config/config.py")
            print(f"Look for a line like 'FONT_FAMILY = \"Segoe UI, Arial, sans-serif\"'")
            print(f"and replace it with 'FONT_FAMILY = \"{system_font}, Arial, sans-serif\"'")
            return 1
    
    except Exception as e:
        print(f"Error updating config file: {str(e)}")
        return 1
    
    print("\nBSTI should now run without segmentation faults.")
    print("To run the application, use: python -m src")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 