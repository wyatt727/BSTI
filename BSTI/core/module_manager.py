#!/usr/bin/env python3
"""
BSTI Module Manager

This module provides functionality to manage, load, parse, validate, and save
modules for the BSTI application, supporting both the legacy format (comments-based)
and the new structured metadata format (YAML).
"""

import os
import re
import yaml
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModuleManager:
    """
    Class for managing BSTI modules, including loading, parsing, validating,
    and saving modules with support for both legacy and new metadata formats.
    """

    # Constants for legacy module parsing
    LEGACY_MARKERS = {
        'files_start': r'# STARTFILES',
        'files_end': r'# ENDFILES',
        'args_start': r'# ARGS',
        'args_end': r'# ENDARGS',
        'nessus_start': r'# NESSUSFINDING',
        'nessus_end': r'# ENDNESSUS',
        'author': r'# AUTHOR:',
    }

    # Module types supported
    MODULE_TYPES = {
        '.sh': 'bash',
        '.py': 'python',
        '.json': 'json'
    }

    def __init__(self, modules_dir: str = None, templates_dir: str = None):
        """
        Initialize the ModuleManager with paths to modules and templates.

        Args:
            modules_dir: Directory containing modules
            templates_dir: Directory containing module templates
        """
        # Set default paths if not provided
        base_dir = Path(__file__).parent.parent.parent
        self.modules_dir = modules_dir or os.path.join(base_dir, 'modules')
        self.templates_dir = templates_dir or os.path.join(base_dir, 'bsti', 'resources', 'module_templates')
        
        # Create directories if they don't exist
        os.makedirs(self.modules_dir, exist_ok=True)
        os.makedirs(self.templates_dir, exist_ok=True)
        
        # Dictionary to store loaded modules
        self.modules = {}
        
        # Load available modules
        self.load_all_modules()
        
        logger.info(f"ModuleManager initialized with {len(self.modules)} modules")

    def load_all_modules(self) -> None:
        """
        Load all modules from the modules directory.
        
        This will scan the modules directory, identify module files,
        and load each one's metadata and content.
        """
        logger.info(f"Loading modules from {self.modules_dir}")
        self.modules = {}
        
        if not os.path.isdir(self.modules_dir):
            logger.warning(f"Modules directory does not exist: {self.modules_dir}")
            return
        
        for root, _, files in os.walk(self.modules_dir):
            for filename in files:
                file_path = os.path.join(root, filename)
                
                # Skip non-module files
                ext = os.path.splitext(filename)[1]
                if ext not in self.MODULE_TYPES:
                    continue
                
                # Attempt to load the module
                try:
                    module_id = os.path.relpath(file_path, self.modules_dir)
                    self.load_module(module_id)
                except Exception as e:
                    logger.error(f"Failed to load module {filename}: {str(e)}")
        
        logger.info(f"Loaded {len(self.modules)} modules")

    def load_module(self, module_id: str) -> Dict[str, Any]:
        """
        Load a specific module by its ID (relative path from modules directory).
        
        Args:
            module_id: The module ID (relative path from modules directory)
        
        Returns:
            Dictionary containing module metadata and content
        
        Raises:
            FileNotFoundError: If the module file doesn't exist
            ValueError: If there's an error parsing the module
        """
        module_path = os.path.join(self.modules_dir, module_id)
        if not os.path.isfile(module_path):
            raise FileNotFoundError(f"Module file not found: {module_path}")
        
        # Get the module type based on file extension
        ext = os.path.splitext(module_id)[1]
        module_type = self.MODULE_TYPES.get(ext)
        
        if not module_type:
            raise ValueError(f"Unsupported module type: {ext}")
        
        # Check if there's a metadata file
        meta_path = f"{module_path}.meta"
        if os.path.isfile(meta_path):
            # New format with separate metadata file
            module_data = self._load_structured_metadata(meta_path)
        else:
            # Legacy format with comments
            module_data = self._load_legacy_metadata(module_path, module_type)
        
        # Store the loaded module
        self.modules[module_id] = module_data
        logger.debug(f"Loaded module: {module_id}")
        
        return module_data

    def _load_structured_metadata(self, meta_path: str) -> Dict[str, Any]:
        """
        Load structured metadata from a separate file.
        
        Args:
            meta_path: Path to the metadata file
            
        Returns:
            Dictionary of metadata
        """
        try:
            # Use the MetadataParser to load the metadata
            from BSTI.core.metadata_parser import MetadataParser
            parser = MetadataParser()
            metadata = parser.parse_structured_metadata(meta_path)
            return metadata
        except Exception as e:
            self.logger.error(f"Error parsing metadata file: {str(e)}")
            return {}

    def _load_legacy_metadata(self, module_path: str, module_type: str) -> Dict[str, Any]:
        """
        Load a module with legacy metadata from script comments.
        
        Args:
            module_path: Path to the module script
            module_type: Type of module (bash, python, json)
        
        Returns:
            Dictionary containing module metadata and content
        """
        # Load the module content
        with open(module_path, 'r') as f:
            content = f.read()
        
        # Parse the metadata from the content
        files = self._extract_legacy_section(content, 
                                            self.LEGACY_MARKERS['files_start'], 
                                            self.LEGACY_MARKERS['files_end'])
        
        args = self._extract_legacy_section(content, 
                                           self.LEGACY_MARKERS['args_start'], 
                                           self.LEGACY_MARKERS['args_end'])
        
        nessus = self._extract_legacy_section(content, 
                                             self.LEGACY_MARKERS['nessus_start'], 
                                             self.LEGACY_MARKERS['nessus_end'])
        
        author = self._extract_legacy_author(content)
        
        # Parse the files section
        parsed_files = []
        for line in files:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = line.split('"', 1)
            if len(parts) > 1:
                filename = parts[0].strip()
                description = parts[1].strip('" ')
                parsed_files.append({
                    'name': filename,
                    'description': description
                })
            else:
                parsed_files.append({
                    'name': line.strip(),
                    'description': ''
                })
        
        # Parse the args section
        parsed_args = []
        for line in args:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
                
            parts = line.split('"', 1)
            if len(parts) > 1:
                arg_name = parts[0].strip()
                description = parts[1].strip('" ')
                parsed_args.append({
                    'name': arg_name,
                    'description': description
                })
            else:
                parsed_args.append({
                    'name': line.strip(),
                    'description': ''
                })
        
        # Parse the nessus findings section
        parsed_nessus = []
        for line in nessus:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parsed_nessus.append(line)
        
        # Create the module data dictionary
        module_data = {
            'id': os.path.relpath(module_path, self.modules_dir),
            'path': module_path,
            'name': os.path.basename(module_path),
            'description': '',  # Not available in legacy format
            'type': module_type,
            'content': content,
            'author': author,
            'version': '1.0.0',  # Default for legacy format
            'files': parsed_files,
            'arguments': parsed_args,
            'nessus_findings': parsed_nessus,
            'metadata_format': 'legacy'
        }
        
        return module_data

    def _extract_legacy_section(self, content: str, start_marker: str, end_marker: str) -> List[str]:
        """
        Extract a section from legacy module content.
        
        Args:
            content: The module content
            start_marker: Start marker regex pattern
            end_marker: End marker regex pattern
        
        Returns:
            List of lines in the section
        """
        section = []
        in_section = False
        
        for line in content.splitlines():
            if re.match(start_marker, line):
                in_section = True
                continue
            elif re.match(end_marker, line):
                in_section = False
                continue
            
            if in_section:
                section.append(line)
        
        return section

    def _extract_legacy_author(self, content: str) -> str:
        """
        Extract the author from legacy module content.
        
        Args:
            content: The module content
        
        Returns:
            Author name or empty string if not found
        """
        author_pattern = self.LEGACY_MARKERS['author'] + r'\s*(.*)'
        match = re.search(author_pattern, content)
        if match:
            return match.group(1).strip()
        return ''

    def _validate_structured_metadata(self, metadata: Dict[str, Any]) -> bool:
        """
        Validate structured metadata for a module.
        
        Args:
            metadata: The metadata dictionary
        
        Returns:
            True if valid, False otherwise
        
        Raises:
            ValueError: If the metadata is invalid
        """
        # Check required fields
        required_fields = ['name', 'description', 'version', 'author']
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required metadata field: {field}")
        
        # Validate files format if present
        if 'files' in metadata:
            for file_info in metadata['files']:
                if not isinstance(file_info, dict) or 'name' not in file_info:
                    raise ValueError("Invalid format for 'files' metadata: each file must have at least a 'name' field")
        
        # Validate arguments format if present
        if 'arguments' in metadata:
            for arg_info in metadata['arguments']:
                if not isinstance(arg_info, dict) or 'name' not in arg_info:
                    raise ValueError("Invalid format for 'arguments' metadata: each argument must have at least a 'name' field")
        
        return True

    def create_module_from_template(self, template_id: str, module_name: str, metadata: Dict[str, Any] = None) -> str:
        """
        Create a new module from a template.
        
        Args:
            template_id: ID of the template to use
            module_name: Name for the new module
            metadata: Optional metadata to include
        
        Returns:
            ID of the newly created module
        
        Raises:
            FileNotFoundError: If the template doesn't exist
            ValueError: If there's an error creating the module
        """
        # Load the template manifest
        manifest_path = os.path.join(self.templates_dir, 'template_manifest.json')
        if not os.path.isfile(manifest_path):
            raise FileNotFoundError(f"Template manifest not found: {manifest_path}")
        
        with open(manifest_path, 'r') as f:
            manifest = json.load(f)
        
        # Find the template in the manifest
        template_info = None
        for template in manifest.get('templates', []):
            if template.get('id') == template_id:
                template_info = template
                break
        
        if not template_info:
            raise ValueError(f"Template not found: {template_id}")
        
        # Get the template file path
        template_file = template_info.get('file')
        if not template_file:
            raise ValueError(f"Template file not specified for template: {template_id}")
        
        template_path = os.path.join(self.templates_dir, template_file)
        if not os.path.isfile(template_path):
            raise FileNotFoundError(f"Template file not found: {template_path}")
        
        # Determine the file extension for the new module
        script_type = template_info.get('script_type', 'bash')
        if script_type == 'bash':
            ext = '.sh'
        elif script_type == 'python':
            ext = '.py'
        elif script_type == 'json':
            ext = '.json'
        else:
            raise ValueError(f"Unsupported script type: {script_type}")
        
        # Create safe filename
        safe_name = re.sub(r'[^\w\-\.]', '_', module_name)
        if not safe_name.endswith(ext):
            safe_name += ext
        
        # Destination path
        dest_path = os.path.join(self.modules_dir, safe_name)
        
        # Check if the module already exists
        if os.path.exists(dest_path):
            raise ValueError(f"Module already exists: {safe_name}")
        
        # Read the template content
        with open(template_path, 'r') as f:
            content = f.read()
        
        # If metadata is provided, create a structured metadata file
        if metadata:
            meta_path = f"{dest_path}.meta"
            
            # Add template data to metadata
            if 'categories' not in metadata and 'categories' in template_info:
                metadata['categories'] = template_info['categories']
                
            # Add script type
            metadata['script_type'] = script_type
            
            # Write metadata file
            with open(meta_path, 'w') as f:
                yaml.dump(metadata, f, default_flow_style=False)
        
        # Write the module file
        with open(dest_path, 'w') as f:
            f.write(content)
        
        # Make the file executable if it's a script
        if ext in ['.sh', '.py']:
            os.chmod(dest_path, 0o755)
        
        # Load the new module
        module_id = safe_name
        self.load_module(module_id)
        
        logger.info(f"Created new module {module_id} from template {template_id}")
        
        return module_id

    def save_module(self, module_id: str, content: str, metadata: Dict[str, Any] = None) -> bool:
        """
        Save a module with the provided content and metadata.
        
        Args:
            module_id: The module ID
            content: The module content
            metadata: Optional new metadata
        
        Returns:
            True if successful, False otherwise
        
        Raises:
            ValueError: If there's an error saving the module
        """
        if module_id not in self.modules:
            raise ValueError(f"Module not found: {module_id}")
        
        module_data = self.modules[module_id]
        module_path = module_data['path']
        
        # Write the module content
        with open(module_path, 'w') as f:
            f.write(content)
        
        # Update metadata if provided
        if metadata:
            # Determine if we're using structured metadata
            if module_data['metadata_format'] == 'structured':
                # Update structured metadata file
                meta_path = f"{module_path}.meta"
                
                with open(meta_path, 'w') as f:
                    yaml.dump(metadata, f, default_flow_style=False)
            else:
                # For legacy format, we need to update the content directly
                # This would involve parsing the current content, updating the metadata
                # sections, and then writing it back. This is complex and prone to errors.
                # For simplicity, we'll just note that this would need to be implemented.
                logger.warning("Updating metadata for legacy format modules is not fully implemented")
                
                # One approach would be to convert to structured format
                # meta_path = f"{module_path}.meta"
                # with open(meta_path, 'w') as f:
                #     yaml.dump(metadata, f, default_flow_style=False)
                # module_data['metadata_format'] = 'structured'
        
        # Reload the module to update internal state
        self.modules[module_id] = self.load_module(module_id)
        
        logger.info(f"Saved module: {module_id}")
        
        return True

    def delete_module(self, module_id: str) -> bool:
        """
        Delete a module.
        
        Args:
            module_id: The module ID
        
        Returns:
            True if successful, False otherwise
        """
        if module_id not in self.modules:
            logger.warning(f"Cannot delete module, not found: {module_id}")
            return False
        
        module_data = self.modules[module_id]
        module_path = module_data['path']
        
        # Check for metadata file
        meta_path = f"{module_path}.meta"
        
        # Delete the module file
        try:
            os.remove(module_path)
            logger.info(f"Deleted module file: {module_path}")
        except Exception as e:
            logger.error(f"Error deleting module file: {str(e)}")
            return False
        
        # Delete the metadata file if it exists
        if os.path.isfile(meta_path):
            try:
                os.remove(meta_path)
                logger.info(f"Deleted metadata file: {meta_path}")
            except Exception as e:
                logger.error(f"Error deleting metadata file: {str(e)}")
                # Continue anyway since the main file was deleted
        
        # Remove from loaded modules
        del self.modules[module_id]
        
        return True

    def convert_legacy_to_structured(self, module_id: str) -> bool:
        """
        Convert a legacy format module to the new structured metadata format.
        
        Args:
            module_id: The module ID
        
        Returns:
            True if successful, False otherwise
        """
        if module_id not in self.modules:
            logger.warning(f"Cannot convert module, not found: {module_id}")
            return False
        
        module_data = self.modules[module_id]
        
        # Skip if already using structured format
        if module_data['metadata_format'] == 'structured':
            logger.info(f"Module {module_id} is already using structured metadata format")
            return True
        
        # Create structured metadata
        metadata = {
            'name': os.path.basename(module_data['path']),
            'description': '',
            'version': '1.0.0',
            'author': module_data['author'],
            'script_type': module_data['type'],
            'script_path': os.path.relpath(module_data['path'], self.modules_dir),
            'files': module_data['files'],
            'arguments': module_data['arguments'],
            'nessus_findings': module_data['nessus_findings'],
            'categories': []
        }
        
        # Create the metadata file
        meta_path = f"{module_data['path']}.meta"
        try:
            with open(meta_path, 'w') as f:
                yaml.dump(metadata, f, default_flow_style=False)
        except Exception as e:
            logger.error(f"Error creating metadata file: {str(e)}")
            return False
        
        # Reload the module
        self.modules[module_id] = self.load_module(module_id)
        
        logger.info(f"Converted module {module_id} to structured metadata format")
        
        return True

    def get_module_templates(self) -> List[Dict[str, Any]]:
        """
        Get a list of available module templates.
        
        Returns:
            List of template dictionaries
        """
        manifest_path = os.path.join(self.templates_dir, 'template_manifest.json')
        if not os.path.isfile(manifest_path):
            logger.warning(f"Template manifest not found: {manifest_path}")
            return []
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                
            return manifest.get('templates', [])
        except Exception as e:
            logger.error(f"Error loading template manifest: {str(e)}")
            return []

    def get_module_categories(self) -> List[Dict[str, str]]:
        """
        Get a list of available module categories.
        
        Returns:
            List of category dictionaries
        """
        manifest_path = os.path.join(self.templates_dir, 'template_manifest.json')
        if not os.path.isfile(manifest_path):
            logger.warning(f"Template manifest not found: {manifest_path}")
            return []
        
        try:
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
                
            return manifest.get('categories', [])
        except Exception as e:
            logger.error(f"Error loading template manifest: {str(e)}")
            return []

    def get_module_by_id(self, module_id: str) -> Optional[Dict[str, Any]]:
        """
        Get a module by its ID.
        
        Args:
            module_id: The module ID
        
        Returns:
            Module data dictionary or None if not found
        """
        return self.modules.get(module_id)

    def get_modules_by_category(self, category: str) -> List[Dict[str, Any]]:
        """
        Get modules by category.
        
        Args:
            category: The category to filter by
        
        Returns:
            List of module data dictionaries
        """
        result = []
        
        for module_id, module_data in self.modules.items():
            # Check if using structured metadata
            if module_data['metadata_format'] == 'structured':
                categories = module_data.get('original_metadata', {}).get('categories', [])
                if category in categories:
                    result.append(module_data)
        
        return result

    def get_modules_by_nessus_finding(self, finding: str) -> List[Dict[str, Any]]:
        """
        Get modules by Nessus finding.
        
        Args:
            finding: The Nessus finding to filter by
        
        Returns:
            List of module data dictionaries
        """
        result = []
        
        for module_id, module_data in self.modules.items():
            if finding in module_data['nessus_findings']:
                result.append(module_data)
        
        return result

    def _load_module(self, module_path: str) -> Dict[str, Any]:
        """
        Load a module and its metadata.
        
        Args:
            module_path: Path to the module file
            
        Returns:
            Dictionary containing module metadata and content
            
        Raises:
            ValueError: If there's an error loading the module
        """
        # Identify the module type based on extension
        module_path = os.path.abspath(module_path)
        _, ext = os.path.splitext(module_path)
        
        if ext == '.py':
            module_type = 'python'
        elif ext == '.sh':
            module_type = 'bash'
        elif ext == '.json':
            module_type = 'json'
        else:
            self.logger.warning(f"Unknown module type for {module_path}, assuming bash")
            module_type = 'bash'
        
        # Load the module content
        try:
            with open(module_path, 'r') as f:
                content = f.read()
        except Exception as e:
            raise ValueError(f"Error reading module file: {str(e)}")
        
        # Check for structured metadata
        meta_path = f"{module_path}.meta"
        
        module_data = {}
        
        if os.path.isfile(meta_path):
            # New format with separate metadata file
            try:
                metadata = self._load_structured_metadata(meta_path)
                
                # Create the module data dictionary
                module_data = {
                    'id': os.path.relpath(module_path, self.modules_dir),
                    'path': module_path,
                    'name': metadata.get('name', os.path.basename(module_path)),
                    'description': metadata.get('description', ''),
                    'type': module_type,
                    'content': content,
                    'author': metadata.get('author', ''),
                    'version': metadata.get('version', '1.0.0'),
                    'files': metadata.get('files', []),
                    'arguments': metadata.get('arguments', []),
                    'nessus_findings': metadata.get('nessus_findings', []),
                    'categories': metadata.get('categories', []),
                    'metadata_format': 'structured',
                    'original_metadata': metadata
                }
            except Exception as e:
                self.logger.error(f"Failed to load structured metadata for {module_path}: {str(e)}")
                # Fall back to legacy format
                module_data = self._load_legacy_metadata(module_path, module_type)
        else:
            # Legacy format with comments
            module_data = self._load_legacy_metadata(module_path, module_type)
        
        return module_data


# Example usage
if __name__ == "__main__":
    module_manager = ModuleManager()
    print(f"Loaded {len(module_manager.modules)} modules")
    
    # Get available templates
    templates = module_manager.get_module_templates()
    print(f"Found {len(templates)} templates")
    
    # Show the module IDs
    for module_id in module_manager.modules:
        print(f"Module: {module_id}") 