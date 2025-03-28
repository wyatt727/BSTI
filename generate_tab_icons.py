#!/usr/bin/env python3
"""
Simple Tab Icon Generator

This script generates SVG icons for our new tabs in the BSTI application.
"""

import os

# Icons to create
ICONS = {
    "home": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>''',
    
    "editor": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>''',
    
    "logs": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>''',
}

def create_icons():
    """Create SVG icon files in the assets/icons directory."""
    # Create assets/icons directory if it doesn't exist
    icons_dir = os.path.join('assets', 'icons')
    os.makedirs(icons_dir, exist_ok=True)
    
    # Write the SVG files
    for name, svg in ICONS.items():
        filename = os.path.join(icons_dir, f"{name}.svg")
        with open(filename, 'w') as f:
            f.write(svg)
        print(f"Created icon: {filename}")
    
    print(f"Created {len(ICONS)} icons in {icons_dir}")

if __name__ == "__main__":
    create_icons() 