#!/usr/bin/env python3
"""
Enhanced Icon Generator for BSTI Application

This script generates icon files for the BSTI application tabs.
The icons are created as SVG files in the assets/icons directory.
Features:
- Proper vector paths for each icon (instead of emoji)
- Support for different sizes
- Multiple theme options (Nord, Dracula, Light)
- Optimized SVG output
"""

import os
import sys
import argparse
from pathlib import Path
import json
import re

# Define the icons directory
ICONS_DIR = Path(os.path.dirname(os.path.abspath(__file__))) / "assets" / "icons"

# Create the icons directory if it doesn't exist
os.makedirs(ICONS_DIR, exist_ok=True)

# Define color themes
THEMES = {
    "nord": {
        "background": "#2e3440",
        "foreground": "#eceff4",
        "colors": {
            "blue": "#88c0d0",
            "dark_blue": "#5e81ac",
            "medium_blue": "#81a1c1",
            "purple": "#b48ead",
            "green": "#a3be8c",
            "yellow": "#ebcb8b",
            "orange": "#d08770",
            "red": "#bf616a"
        }
    },
    "dracula": {
        "background": "#282a36",
        "foreground": "#f8f8f2",
        "colors": {
            "blue": "#8be9fd",
            "dark_blue": "#6272a4",
            "medium_blue": "#bd93f9",
            "purple": "#ff79c6",
            "green": "#50fa7b",
            "yellow": "#f1fa8c",
            "orange": "#ffb86c",
            "red": "#ff5555"
        }
    },
    "light": {
        "background": "#ffffff",
        "foreground": "#333333",
        "colors": {
            "blue": "#0d6efd",
            "dark_blue": "#0a58ca",
            "medium_blue": "#3b82f6",
            "purple": "#6f42c1",
            "green": "#198754",
            "yellow": "#ffc107",
            "orange": "#fd7e14",
            "red": "#dc3545"
        }
    }
}

# Define the icons with SVG paths
# These are simplified vector paths that represent each icon
ICONS = {
    "nmb": {
        "path": "M32 16c-8.84 0-16 7.16-16 16s7.16 16 16 16 16-7.16 16-16h-4c0 6.63-5.37 12-12 12s-12-5.37-12-12 5.37-12 12-12v8l12-12-12-12v8z",
        "color_key": "blue",
        "description": "NMB tab icon - sync/refresh symbol"
    },
    "drozer": {
        "path": "M48 24H32v-4l-8 8 8 8v-4h16v8H32v4l-8-8-8-8 8-8v4h32v-8H16v8h8v-4l8 8 8-8v4h8z",
        "color_key": "dark_blue",
        "description": "Drozer tab icon - shield/security symbol"
    },
    "explorer": {
        "path": "M43.7 38.3l-6.8-6.8c1-1.6 1.6-3.5 1.6-5.5 0-5.5-4.5-10-10-10s-10 4.5-10 10 4.5 10 10 10c2 0 3.9-0.6 5.5-1.6l6.8 6.8c0.4 0.4 1 0.4 1.4 0l1.4-1.4c0.4-0.4 0.4-1 0-1.4zM20.5 26c0-4.4 3.6-8 8-8s8 3.6 8 8-3.6 8-8 8-8-3.6-8-8z",
        "color_key": "medium_blue",
        "description": "Explorer tab icon - magnifying glass"
    },
    "mobile": {
        "path": "M38 12H26c-2.2 0-4 1.8-4 4v32c0 2.2 1.8 4 4 4h12c2.2 0 4-1.8 4-4V16c0-2.2-1.8-4-4-4zm0 32H26V20h12v24zm-6-4c1.1 0 2-0.9 2-2s-0.9-2-2-2-2 0.9-2 2 0.9 2 2 2z",
        "color_key": "purple",
        "description": "Mobile Testing tab icon - smartphone"
    },
    "web": {
        "path": "M32 16c-8.8 0-16 7.2-16 16s7.2 16 16 16 16-7.2 16-16-7.2-16-16-16zm-2 28.4c-6.5-0.6-11.6-6-11.6-12.4s5.1-11.8 11.6-12.4v24.8zm2-24.8c6.5 0.6 11.6 6 11.6 12.4s-5.1 11.8-11.6 12.4V19.6z",
        "color_key": "green",
        "description": "Web Testing tab icon - globe"
    },
    "screenshot": {
        "path": "M32 24c-4.4 0-8 3.6-8 8s3.6 8 8 8 8-3.6 8-8-3.6-8-8-8zm10-12h-5.2c-0.9-2.4-3.2-4-5.8-4h-4c-2.6 0-4.9 1.6-5.8 4H16c-2.2 0-4 1.8-4 4v24c0 2.2 1.8 4 4 4h32c2.2 0 4-1.8 4-4V16c0-2.2-1.8-4-4-4zm-10 28c-6.6 0-12-5.4-12-12s5.4-12 12-12 12 5.4 12 12-5.4 12-12 12z",
        "color_key": "yellow",
        "description": "Screenshot Editor tab icon - camera"
    },
    "workflow": {
        "path": "M48 38h-4V28h-8v10h-4V22h-8v16h-4V34h-8v4h-4v8h44v-8zm-44-4h4v-4h4v4h4v4h-12v-4zm36 0h-4v-10h4v10zm-16-16h4v16h-4V18zm-16 16h4v4h-4v-4z",
        "color_key": "orange",
        "description": "Workflow Editor tab icon - chart/graph"
    },
    "plextrac": {
        "path": "M42 16H22c-2.2 0-4 1.8-4 4v24c0 2.2 1.8 4 4 4h20c2.2 0 4-1.8 4-4V20c0-2.2-1.8-4-4-4zm0 28H22V20h20v24zM26 30h12v2H26v-2zm0-6h12v2H26v-2zm0 12h8v2h-8v-2z",
        "color_key": "red",
        "description": "PlexTrac tab icon - document/note"
    },
    "home": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M3 9l9-7 9 7v11a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2z"></path><polyline points="9 22 9 12 15 12 15 22"></polyline></svg>''',
    "editor": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 3a2.828 2.828 0 1 1 4 4L7.5 20.5 2 22l1.5-5.5L17 3z"></path></svg>''',
    "logs": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>''',
    "webapp": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="2" y1="12" x2="22" y2="12"></line><path d="M12 2a15.3 15.3 0 0 1 4 10 15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"></path></svg>''',
    "plugin": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M20.24 12.24a6 6 0 0 0-8.49-8.49L5 10.5V19h8.5z"></path><line x1="16" y1="8" x2="2" y2="22"></line><line x1="17.5" y1="15" x2="9" y2="15"></line></svg>''',
    "save": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M19 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h11l5 5v11a2 2 0 0 1-2 2z"></path><polyline points="17 21 17 13 7 13 7 21"></polyline><polyline points="7 3 7 8 15 8"></polyline></svg>''',
    "add": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"></circle><line x1="12" y1="8" x2="12" y2="16"></line><line x1="8" y1="12" x2="16" y2="12"></line></svg>''',
    "delete": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="3 6 5 6 21 6"></polyline><path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"></path><line x1="10" y1="11" x2="10" y2="17"></line><line x1="14" y1="11" x2="14" y2="17"></line></svg>''',
    "edit": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"></path><path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"></path></svg>''',
    "refresh": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="23 4 23 10 17 10"></polyline><polyline points="1 20 1 14 7 14"></polyline><path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"></path></svg>''',
    "run": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"></polygon></svg>''',
    "stop": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="2" ry="2"></rect></svg>''',
    "settings": '''<svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#d8dee9" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="3"></circle><path d="M19.4 15a1.65 1.65 0 0 0 .33 1.82l.06.06a2 2 0 0 1 0 2.83 2 2 0 0 1-2.83 0l-.06-.06a1.65 1.65 0 0 0-1.82-.33 1.65 1.65 0 0 0-1 1.51V21a2 2 0 0 1-2 2 2 2 0 0 1-2-2v-.09A1.65 1.65 0 0 0 9 19.4a1.65 1.65 0 0 0-1.82.33l-.06.06a2 2 0 0 1-2.83 0 2 2 0 0 1 0-2.83l.06-.06a1.65 1.65 0 0 0 .33-1.82 1.65 1.65 0 0 0-1.51-1H3a2 2 0 0 1-2-2 2 2 0 0 1 2-2h.09A1.65 1.65 0 0 0 4.6 9a1.65 1.65 0 0 0-.33-1.82l-.06-.06a2 2 0 0 1 0-2.83 2 2 0 0 1 2.83 0l.06.06a1.65 1.65 0 0 0 1.82.33H9a1.65 1.65 0 0 0 1-1.51V3a2 2 0 0 1 2-2 2 2 0 0 1 2 2v.09a1.65 1.65 0 0 0 1 1.51 1.65 1.65 0 0 0 1.82-.33l.06-.06a2 2 0 0 1 2.83 0 2 2 0 0 1 0 2.83l-.06.06a1.65 1.65 0 0 0-.33 1.82V9a1.65 1.65 0 0 0 1.51 1H21a2 2 0 0 1 2 2 2 2 0 0 1-2 2h-.09a1.65 1.65 0 0 0-1.51 1z"></path></svg>''',
}

def optimize_svg(svg_content):
    """
    Optimize SVG content by removing unnecessary whitespace and attributes.
    """
    # Remove whitespace between tags
    svg_content = re.sub(r'>\s+<', '><', svg_content)
    
    # Remove comments
    svg_content = re.sub(r'<!--.*?-->', '', svg_content)
    
    # Remove unnecessary attributes
    svg_content = svg_content.replace('standalone="no"', '')
    
    # Minify
    svg_content = svg_content.strip()
    
    return svg_content

def generate_svg(icon_data, theme_data, size=64, optimize=True):
    """
    Generate SVG content for an icon.
    
    Args:
        icon_data: Dictionary containing icon information
        theme_data: Dictionary containing theme colors
        size: Size of the icon in pixels
        optimize: Whether to optimize the SVG output
        
    Returns:
        SVG content as a string
    """
    # Calculate dimensions and positioning
    center = size / 2
    radius = (size / 2) * 0.875  # Slightly smaller than half size
    stroke_width = size / 32
    
    # Get colors
    bg_color = theme_data["colors"][icon_data["color_key"]]
    fg_color = theme_data["foreground"]
    stroke_color = theme_data["background"]
    
    # Create SVG
    svg_template = f"""<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<svg width="{size}" height="{size}" viewBox="0 0 64 64" xmlns="http://www.w3.org/2000/svg">
  <circle cx="32" cy="32" r="{radius}" fill="{bg_color}" stroke="{stroke_color}" stroke-width="{stroke_width}"/>
  <path d="{icon_data['path']}" fill="{fg_color}"/>
</svg>
"""
    
    if optimize:
        return optimize_svg(svg_template)
    return svg_template

def create_icons(theme_name, sizes, optimize):
    """Create the icon files for the specified theme and sizes."""
    if theme_name not in THEMES:
        print(f"Error: Theme '{theme_name}' not found. Available themes: {', '.join(THEMES.keys())}")
        sys.exit(1)
    
    theme_data = THEMES[theme_name]
    
    # Create theme directory
    theme_dir = ICONS_DIR / theme_name
    os.makedirs(theme_dir, exist_ok=True)
    
    print(f"Creating icon files in {theme_dir}")
    
    # Generate icons for each size
    for size in sizes:
        size_dir = theme_dir / str(size)
        os.makedirs(size_dir, exist_ok=True)
        
        for name, data in ICONS.items():
            svg_content = generate_svg(data, theme_data, size, optimize)
            
            # Save SVG file
            svg_path = size_dir / f"{name}.svg"
            with open(svg_path, "w", encoding="utf-8") as f:
                f.write(svg_content)
            print(f"Created {svg_path}")
    
    print(f"Done creating icons for theme '{theme_name}'.")

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description="Generate SVG icons for BSTI application")
    parser.add_argument('--theme', choices=THEMES.keys(), default='nord', 
                        help=f"Theme to use (default: nord)")
    parser.add_argument('--sizes', type=int, nargs='+', default=[16, 24, 32, 48, 64],
                        help="Icon sizes to generate (default: 16 24 32 48 64)")
    parser.add_argument('--all-themes', action='store_true',
                        help="Generate icons for all themes")
    parser.add_argument('--no-optimize', action='store_true',
                        help="Don't optimize SVG output")
    return parser.parse_args()

def main():
    """Process arguments and create icon files."""
    args = parse_arguments()
    
    if args.all_themes:
        for theme_name in THEMES:
            create_icons(theme_name, args.sizes, not args.no_optimize)
    else:
        create_icons(args.theme, args.sizes, not args.no_optimize)
    
    # Generate a manifest file with icon information
    manifest = {
        "icons": {name: data["description"] for name, data in ICONS.items()},
        "themes": list(THEMES.keys()),
        "sizes": args.sizes
    }
    
    manifest_path = ICONS_DIR / "manifest.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2)
    
    print(f"Created icon manifest at {manifest_path}")

if __name__ == "__main__":
    main() 