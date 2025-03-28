#!/usr/bin/env python3
"""
BSTI Template Engine

This module provides functionality to load and populate module templates
for the BSTI application, making it easier for users to create new modules.
"""

import os
import re
import json
import yaml
import logging
import string
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class TemplateEngine:
    """
    Engine for loading and populating module templates.
    """
    
    def __init__(self, templates_dir: str = None):
        """
        Initialize the template engine.
        
        Args:
            templates_dir: Directory containing module templates
        """
        # Set default path if not provided
        base_dir = Path(__file__).parent.parent.parent
        self.templates_dir = templates_dir or os.path.join(base_dir, 'bsti', 'resources', 'module_templates')
        
        # Create directory if it doesn't exist
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Load template manifest if it exists
        self.manifest = self._load_manifest()
        
        logger.info(f"TemplateEngine initialized with {len(self.get_available_templates())} templates")
    
    def _load_manifest(self) -> Dict[str, Any]:
        """
        Load the template manifest file.
        
        Returns:
            Dictionary containing the manifest data
        """
        manifest_path = os.path.join(self.templates_dir, 'template_manifest.json')
        if not os.path.isfile(manifest_path):
            logger.warning(f"Template manifest not found: {manifest_path}")
            return {
                'version': '1.0.0',
                'templates': [],
                'categories': []
            }
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                
            # Validate basic structure
            if 'templates' not in manifest:
                manifest['templates'] = []
            
            if 'categories' not in manifest:
                manifest['categories'] = []
                
            return manifest
        except Exception as e:
            logger.error(f"Error loading template manifest: {str(e)}")
            return {
                'version': '1.0.0',
                'templates': [],
                'categories': []
            }
    
    def get_available_templates(self) -> List[Dict[str, Any]]:
        """
        Get a list of available templates.
        
        Returns:
            List of template dictionaries
        """
        return self.manifest.get('templates', [])
    
    def get_template_categories(self) -> List[Dict[str, str]]:
        """
        Get a list of template categories.
        
        Returns:
            List of category dictionaries
        """
        return self.manifest.get('categories', [])
    
    def get_template_by_id(self, template_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a template by its ID.
        
        Args:
            template_id: ID of the template
        
        Returns:
            Template dictionary or None if not found
        """
        templates = self.get_available_templates()
        for template in templates:
            if template.get('id') == template_id:
                return template
        
        return None
    
    def get_templates_by_category(self, category_id: str) -> List[Dict[str, Any]]:
        """
        Get templates by category.
        
        Args:
            category_id: ID of the category
        
        Returns:
            List of template dictionaries
        """
        templates = self.get_available_templates()
        return [t for t in templates if category_id in t.get('categories', [])]
    
    def get_template_content(self, template_id: str) -> Optional[str]:
        """
        Get the content of a template.
        
        Args:
            template_id: ID of the template
        
        Returns:
            Template content or None if not found
        """
        template = self.get_template_by_id(template_id)
        if not template:
            logger.warning(f"Template not found: {template_id}")
            return None
        
        template_file = template.get('file')
        if not template_file:
            logger.warning(f"Template file not specified: {template_id}")
            return None
        
        template_path = os.path.join(self.templates_dir, template_file)
        if not os.path.isfile(template_path):
            logger.warning(f"Template file not found: {template_path}")
            return None
        
        try:
            with open(template_path, 'r') as f:
                content = f.read()
            return content
        except Exception as e:
            logger.error(f"Error reading template file: {str(e)}")
            return None
    
    def populate_template(self, template_id: str, variables: Dict[str, str]) -> Optional[str]:
        """
        Populate a template with variables.
        
        Args:
            template_id: ID of the template
            variables: Dictionary of variables to replace in the template
        
        Returns:
            Populated template content or None if error
        """
        content = self.get_template_content(template_id)
        if not content:
            return None
        
        try:
            # Create a safe string Template
            template = string.Template(content)
            
            # Substitute variables
            return template.safe_substitute(variables)
        except Exception as e:
            logger.error(f"Error populating template: {str(e)}")
            return None
    
    def create_module_from_template(self, template_id: str, module_path: str, template_vars: Dict[str, str] = None, metadata: Dict[str, Any] = None) -> str:
        """
        Create a new module from a template.
        
        Args:
            template_id: ID of the template
            module_path: Path where the module should be created
            template_vars: Dictionary of template variables and their values
            metadata: Optional metadata for the module
            
        Returns:
            Path to the created module
            
        Raises:
            ValueError: If template doesn't exist or there's an error creating the module
        """
        # Get the template
        if template_id not in self.manifest['templates']:
            raise ValueError(f"Template not found: {template_id}")
        
        template = self.get_template_by_id(template_id)
        
        # Ensure template variables are provided
        template_vars = template_vars or {}
        for var in template.get('variables', []):
            if var not in template_vars:
                logger.warning(f"Template variable not provided: {var}")
        
        # Create module content by replacing template variables
        content = self.populate_template(template_id, template_vars)
        if not content:
            raise ValueError("Error populating template")
        
        # Create the module file
        try:
            os.makedirs(os.path.dirname(module_path), exist_ok=True)
            with open(module_path, 'w') as f:
                f.write(content)
            
            # Set executable permission for scripts
            if module_path.endswith('.py') or module_path.endswith('.sh'):
                os.chmod(module_path, 0o755)
            
            logger.info(f"Created module: {module_path}")
            
            # Create metadata file if provided
            if metadata:
                meta_path = f"{module_path}.meta"
                
                # Add template info to metadata if not already present
                if 'template' not in metadata:
                    metadata['template'] = template_id
                
                # Write the metadata file in JSON format
                try:
                    with open(meta_path, 'w') as f:
                        f.write(json.dumps(metadata, indent=2))
                    logger.info(f"Created metadata file: {meta_path}")
                except Exception as e:
                    logger.error(f"Failed to create metadata file: {str(e)}")
            
            return module_path
        
        except Exception as e:
            raise ValueError(f"Error creating module: {str(e)}")
    
    def get_template_variables(self, template_id: str) -> List[str]:
        """
        Get the variables used in a template.
        
        Args:
            template_id: ID of the template
        
        Returns:
            List of variable names
        """
        content = self.get_template_content(template_id)
        if not content:
            return []
        
        # Find all ${variable} or $variable patterns
        pattern = r'\$\{([a-zA-Z0-9_]+)\}|\$([a-zA-Z0-9_]+)'
        matches = re.findall(pattern, content)
        
        # Extract variable names (either from ${var} or $var format)
        variables = []
        for match in matches:
            # match is a tuple with groups, add the non-empty group
            var = match[0] if match[0] else match[1]
            if var and var not in variables:
                variables.append(var)
        
        return variables
    
    def create_template(self, template_id: str, name: str, description: str, 
                       content: str, script_type: str, categories: List[str] = None) -> bool:
        """
        Create a new template.
        
        Args:
            template_id: ID for the new template
            name: Name of the template
            description: Description of the template
            content: Template content
            script_type: Type of script ('bash', 'python', 'json')
            categories: List of category IDs
        
        Returns:
            True if successful, False otherwise
        """
        # Check if template already exists
        if self.get_template_by_id(template_id):
            logger.warning(f"Template already exists: {template_id}")
            return False
        
        # Validate script type
        if script_type not in ['bash', 'python', 'json']:
            logger.error(f"Invalid script type: {script_type}")
            return False
        
        # Determine file extension
        if script_type == 'bash':
            ext = '.sh'
        elif script_type == 'python':
            ext = '.py'
        elif script_type == 'json':
            ext = '.json'
        else:
            ext = '.txt'
        
        # Create template file name
        file_name = f"{template_id}_template{ext}"
        file_path = os.path.join(self.templates_dir, file_name)
        
        # Check if file already exists
        if os.path.exists(file_path):
            logger.warning(f"Template file already exists: {file_path}")
            return False
        
        try:
            # Write the template content
            with open(file_path, 'w') as f:
                f.write(content)
            
            # Add to manifest
            template_info = {
                'id': template_id,
                'name': name,
                'description': description,
                'file': file_name,
                'script_type': script_type,
                'categories': categories or [],
                'complexity': 'medium',
                'requires_files': False
            }
            
            self.manifest['templates'].append(template_info)
            
            # Save the manifest
            manifest_path = os.path.join(self.templates_dir, 'template_manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump(self.manifest, f, indent=4)
            
            logger.info(f"Created template: {template_id}")
            return True
        except Exception as e:
            logger.error(f"Error creating template: {str(e)}")
            return False
    
    def delete_template(self, template_id: str) -> bool:
        """
        Delete a template.
        
        Args:
            template_id: ID of the template
        
        Returns:
            True if successful, False otherwise
        """
        template = self.get_template_by_id(template_id)
        if not template:
            logger.warning(f"Template not found: {template_id}")
            return False
        
        template_file = template.get('file')
        if not template_file:
            logger.warning(f"Template file not specified: {template_id}")
            return False
        
        template_path = os.path.join(self.templates_dir, template_file)
        
        try:
            # Delete the template file
            if os.path.isfile(template_path):
                os.remove(template_path)
                logger.info(f"Deleted template file: {template_path}")
            
            # Remove from manifest
            self.manifest['templates'] = [t for t in self.manifest['templates'] if t.get('id') != template_id]
            
            # Save the manifest
            manifest_path = os.path.join(self.templates_dir, 'template_manifest.json')
            with open(manifest_path, 'w') as f:
                json.dump(self.manifest, f, indent=4)
            
            logger.info(f"Deleted template: {template_id}")
            return True
        except Exception as e:
            logger.error(f"Error deleting template: {str(e)}")
            return False


# Example usage
if __name__ == "__main__":
    engine = TemplateEngine()
    
    # Get available templates
    templates = engine.get_available_templates()
    print(f"Found {len(templates)} templates")
    
    # Example of creating a module from a template
    if templates:
        template_id = templates[0]['id']
        print(f"Using template: {template_id}")
        
        variables = {
            'MODULE_NAME': 'Test Module',
            'AUTHOR': 'Test User',
            'PORT': '8080'
        }
        
        metadata = {
            'name': 'Test Module',
            'description': 'A test module created from a template',
            'version': '1.0.0',
            'author': 'Test User'
        }
        
        output_path = os.path.join(os.getcwd(), 'test_module.sh')
        
        result = engine.create_module_from_template(template_id, output_path, variables, metadata)
        print(f"Created module: {result}") 