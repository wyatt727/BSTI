#!/usr/bin/env python3
"""
Test Script for BSTI Module System

This script demonstrates the usage of the new BSTI module system backend components.
It tests loading, creating, and managing modules with the new structured metadata format.
"""

import os
import sys
import json
import logging
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path

# Add the current directory to sys.path to ensure modules can be imported
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Import the modules directly from BSTI directory
from BSTI.core.module_manager import ModuleManager
from BSTI.core.metadata_parser import MetadataParser 
from BSTI.core.module_validator import ModuleValidator
from BSTI.core.template_engine import TemplateEngine

def print_separator(title):
    """Print a section separator with title."""
    print("\n" + "=" * 80)
    print(f" {title} ".center(80, "="))
    print("=" * 80 + "\n")

def test_module_manager():
    """Test the ModuleManager functionality."""
    print_separator("Testing ModuleManager")
    
    # Initialize the module manager
    manager = ModuleManager()
    
    # Display available modules
    modules = manager.modules
    print(f"Found {len(modules)} modules:")
    for i, (module_id, module_data) in enumerate(modules.items(), 1):
        print(f"{i}. {module_id} ({module_data['type']})")
    
    # Display available templates
    templates = manager.get_module_templates()
    print(f"\nFound {len(templates)} templates:")
    for i, template in enumerate(templates, 1):
        print(f"{i}. {template['name']} ({template['script_type']})")
    
    # Display categories
    categories = manager.get_module_categories()
    print(f"\nFound {len(categories)} categories:")
    for i, category in enumerate(categories, 1):
        print(f"{i}. {category['name']}: {category['description']}")
    
    return manager

def test_metadata_parser():
    """Test the MetadataParser functionality."""
    print_separator("Testing MetadataParser")
    
    # Initialize the parser
    parser = MetadataParser()
    
    # Example of parsing legacy metadata
    legacy_content = """#!/bin/bash
# STARTFILES
# targets.txt "List of target hosts"
# ENDFILES
# ARGS
# PORT "Port number to scan"
# TIMEOUT "Timeout in seconds"
# ENDARGS
# NESSUSFINDING
# SSH Server CBC Mode Ciphers Enabled
# ENDNESSUS
# AUTHOR: Test User

echo "This is a test module"
"""
    
    print("Parsing legacy metadata from content...")
    legacy_metadata = parser.parse_legacy_metadata(legacy_content)
    print(json.dumps(legacy_metadata, indent=2))
    
    # Format back to legacy
    print("\nFormatting back to legacy metadata...")
    legacy_format = parser.format_legacy_metadata(legacy_metadata)
    print(legacy_format)
    
    return parser

def test_module_validator():
    """Test the ModuleValidator functionality."""
    print_separator("Testing ModuleValidator")
    
    # Initialize the validator
    validator = ModuleValidator()
    
    # Example of validating metadata
    metadata = {
        'name': 'Test Module',
        'description': 'A test module',
        'version': '1.0.0',
        'author': 'Test User',
        'files': [
            {'name': 'targets.txt', 'description': 'List of target hosts'}
        ],
        'arguments': [
            {'name': 'PORT', 'description': 'Port number to scan'},
            {'name': 'TIMEOUT', 'description': 'Timeout in seconds'}
        ],
        'nessus_findings': ['SSH Server CBC Mode Ciphers Enabled'],
        'categories': ['network', 'ssh']
    }
    
    print("Validating metadata...")
    valid, errors = validator.validate_metadata(metadata)
    if valid:
        print("Metadata is valid!")
    else:
        print("Metadata validation failed:")
        for error in errors:
            print(f"- {error}")
    
    # Example of validating bash content
    bash_content = """#!/bin/bash
# Test script
echo "Hello, world!"
exit 0
"""
    
    # Write to temporary file for testing
    temp_file = os.path.join(os.getcwd(), 'temp_test_script.sh')
    with open(temp_file, 'w') as f:
        f.write(bash_content)
    
    print("\nValidating bash script...")
    valid, errors = validator.validate_module_content(temp_file, 'bash')
    if valid:
        print("Bash script is valid!")
    else:
        print("Bash script validation failed:")
        for error in errors:
            print(f"- {error}")
    
    # Clean up
    os.remove(temp_file)
    
    return validator

def test_template_engine():
    """Test the TemplateEngine functionality."""
    print_separator("Testing TemplateEngine")
    
    # Initialize the template engine
    engine = TemplateEngine()
    
    # Display available templates
    templates = engine.get_available_templates()
    print(f"Found {len(templates)} templates:")
    if templates:
        for i, template in enumerate(templates, 1):
            print(f"{i}. {template['name']} ({template['script_type']})")
        
        # Example of getting template variables
        template_id = templates[0]['id']
        print(f"\nTemplate variables for {template_id}:")
        variables = engine.get_template_variables(template_id)
        for var in variables:
            print(f"- {var}")
        
        # Example of populating a template
        values = {var: f"VALUE_{var}" for var in variables}
        print(f"\nPopulating template with values: {values}")
        content = engine.populate_template(template_id, values)
        if content:
            print("Template populated successfully!")
            print("First 200 characters of content:")
            print(content[:200] + "..." if len(content) > 200 else content)
    else:
        print("No templates found. Check the templates directory.")
    
    return engine

def test_create_module():
    """Test creating a module from a template."""
    print_separator("Creating Test Module")
    
    # Get the template engine
    engine = TemplateEngine()
    
    # Get a template
    template_id = "bash_scanner"
    template = engine.get_template_by_id(template_id)
    print(f"Using template: {template['name']}")
    
    # Get template variables
    variables = engine.get_template_variables(template_id)
    print(f"Template variables: {variables}")
    
    # Populate template variables with sample values
    template_vars = {}
    for var in variables:
        template_vars[var] = f"VALUE_{var}"
    
    # Create the module
    module_path = os.path.join("modules", "test_auto_generated.sh")
    
    # Remove the module and metadata files if they already exist
    if os.path.exists(module_path):
        try:
            os.remove(module_path)
            print(f"Removed existing module: {module_path}")
        except Exception as e:
            print(f"Error removing existing module: {str(e)}")
    
    metadata_path = f"{module_path}.meta"
    if os.path.exists(metadata_path):
        try:
            os.remove(metadata_path)
            print(f"Removed existing metadata: {metadata_path}")
        except Exception as e:
            print(f"Error removing existing metadata: {str(e)}")
    
    # Create metadata
    metadata = {
        "name": "Test Auto-Generated Module",
        "description": "A module created for testing the new module system",
        "version": "1.0.0",
        "author": "Auto Test",
        "categories": ["test", "auto-generated"],
        "script_type": "bash"
    }
    
    # Create the module
    try:
        result = engine.create_module_from_template(
            template_id=template_id,
            module_path=module_path,
            template_vars=template_vars,
            metadata=metadata
        )
        
        if result:
            print(f"Module created successfully: {result}")
            
            # Test loading the module
            manager = ModuleManager()
            module_id = os.path.basename(module_path)
            
            if module_id in manager.modules:
                module_data = manager.modules[module_id]
                print("\nModule data:")
                print(f"Name: {module_data['name']}")
                print(f"Description: {module_data['description']}")
                print(f"Author: {module_data['author']}")
                print(f"Version: {module_data['version']}")
                print(f"Type: {module_data['type']}")
                print(f"Metadata format: {module_data['metadata_format']}")
            else:
                print("Module was not loaded. Available modules:")
                for mid in manager.modules:
                    print(f"- {mid}")
                
                # Try to read the metadata file
                try:
                    with open(metadata_path, 'r') as f:
                        print(f"Metadata file content: {f.read()}")
                except Exception as e:
                    print(f"Error reading metadata file: {str(e)}")
        else:
            print("Failed to create module.")
    except Exception as e:
        print(f"Error creating module: {str(e)}")

def create_test_module():
    """Create a test module without using the template system."""
    print_separator("Creating Test Module Directly")
    
    # Create a simple test module
    module_path = os.path.join("modules", "direct_test_module.sh")
    module_content = """#!/bin/bash
# Test module created directly for testing purposes

# AUTHOR: Test User

echo "This is a direct test module"
echo "Arguments: $@"
exit 0
"""
    
    # Create metadata
    metadata = {
        'name': 'Direct Test Module',
        'description': 'A module created directly for testing',
        'version': '1.0.0',
        'author': 'Test User',
        'categories': ['test', 'direct-test'],
        'script_type': 'bash'
    }
    
    # Remove files if they already exist
    if os.path.exists(module_path):
        try:
            os.remove(module_path)
            print(f"Removed existing module: {module_path}")
        except Exception as e:
            print(f"Error removing existing module: {str(e)}")
    
    meta_path = f"{module_path}.meta"
    if os.path.exists(meta_path):
        try:
            os.remove(meta_path)
            print(f"Removed existing metadata: {meta_path}")
        except Exception as e:
            print(f"Error removing existing metadata: {str(e)}")
    
    # Write the module file
    try:
        with open(module_path, 'w') as f:
            f.write(module_content)
        os.chmod(module_path, 0o755)
        print(f"Created module file: {module_path}")
        
        # Write metadata file as JSON
        with open(meta_path, 'w') as f:
            f.write(json.dumps(metadata, indent=2))
        print(f"Created metadata file: {meta_path}")
        
        # Test loading the module
        manager = ModuleManager()
        if 'direct_test_module.sh' in manager.modules:
            module_data = manager.modules['direct_test_module.sh']
            print("\nModule data:")
            print(f"Name: {module_data['name']}")
            print(f"Description: {module_data['description']}")
            print(f"Author: {module_data['author']}")
            print(f"Version: {module_data['version']}")
            print(f"Type: {module_data['type']}")
            print(f"Metadata format: {module_data['metadata_format']}")
            
            # Clean up
            print("\nCleaning up...")
            manager.delete_module('direct_test_module.sh')
            print("Module deleted.")
        else:
            print("Module was not loaded. Available modules:")
            for module_id in manager.modules:
                print(f"- {module_id}")
            
            # Check the content of the metadata file
            try:
                with open(meta_path, 'r') as f:
                    print(f"\nMetadata file content:\n{f.read()}")
            except Exception as e:
                print(f"Error reading metadata file: {str(e)}")
            
    except Exception as e:
        print(f"Error creating test module: {str(e)}")

def main():
    """Main test function."""
    print("BSTI Module System Test")
    print("======================\n")
    
    # Test each component
    manager = test_module_manager()
    parser = test_metadata_parser()
    validator = test_module_validator()
    engine = test_template_engine()
    
    # Test creating a module
    #test_create_module()
    
    # Use direct module creation instead
    create_test_module()
    
    print_separator("Test Completed")

if __name__ == "__main__":
    main() 