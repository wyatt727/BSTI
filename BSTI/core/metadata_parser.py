#!/usr/bin/env python3
"""
BSTI Metadata Parser

This module provides functionality to parse metadata from BSTI modules,
supporting both the legacy format (comments-based) and the new structured
metadata format (YAML/JSON).
"""

import os
import re
import yaml
import json
import logging
from typing import Dict, List, Any, Optional, Tuple, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class MetadataParser:
    """
    Parser for module metadata, supporting both legacy and structured formats.
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
    
    def __init__(self):
        """Initialize the metadata parser."""
        pass
    
    def parse_module_metadata(self, module_path: str) -> Dict[str, Any]:
        """
        Parse metadata from a module file, detecting format automatically.
        
        Args:
            module_path: Path to the module file
            
        Returns:
            Dictionary of parsed metadata
            
        Raises:
            FileNotFoundError: If the module file doesn't exist
            ValueError: If there's an error parsing the metadata
        """
        if not os.path.isfile(module_path):
            raise FileNotFoundError(f"Module file not found: {module_path}")
        
        # Check if there's a metadata file
        meta_path = f"{module_path}.meta"
        if os.path.isfile(meta_path):
            # New format with separate metadata file
            return self.parse_structured_metadata(meta_path)
        else:
            # Legacy format with comments
            with open(module_path, 'r') as f:
                content = f.read()
            return self.parse_legacy_metadata(content)
    
    def parse_structured_metadata(self, meta_path: str) -> Dict[str, Any]:
        """
        Parse structured metadata from a separate file.
        
        Args:
            meta_path: Path to the metadata file
            
        Returns:
            Dictionary of parsed metadata
            
        Raises:
            FileNotFoundError: If the metadata file doesn't exist
            ValueError: If there's an error parsing the metadata
        """
        if not os.path.isfile(meta_path):
            raise FileNotFoundError(f"Metadata file not found: {meta_path}")
        
        try:
            with open(meta_path, 'r') as f:
                content = f.read().strip()
                
            # Handle empty files
            if not content:
                logger.warning(f"Empty metadata file: {meta_path}")
                return {}
            
            metadata = None
            
            # Try YAML first (for .meta, .yaml, .yml files)
            if meta_path.endswith('.yaml') or meta_path.endswith('.yml') or meta_path.endswith('.meta'):
                try:
                    metadata = yaml.safe_load(content)
                    logger.debug(f"Successfully parsed YAML metadata from {meta_path}")
                except yaml.YAMLError as e:
                    logger.warning(f"Failed to parse YAML metadata: {str(e)}")
                    logger.debug(f"YAML content that failed to parse: {content}")
                    # Don't raise here, try JSON as a fallback
            
            # If YAML failed or it's a JSON file, try JSON
            if metadata is None:
                try:
                    metadata = json.loads(content)
                    logger.debug(f"Successfully parsed JSON metadata from {meta_path}")
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse metadata as JSON: {str(e)}")
                    logger.debug(f"JSON content that failed to parse: {content}")
                    
                    # Last resort: try parsing as a simple key-value format
                    try:
                        metadata = self._parse_simple_key_value(content)
                        if metadata:
                            logger.info(f"Parsed metadata using simple key-value format from {meta_path}")
                        else:
                            raise ValueError("Simple key-value parsing returned empty result")
                    except Exception as simple_e:
                        logger.error(f"Failed to parse metadata with all methods: {str(simple_e)}")
                        logger.error(f"Metadata content: {content}")
                        raise ValueError(f"Failed to parse metadata file {meta_path} with all available methods")
            
            # Handle None result
            if metadata is None:
                logger.warning(f"Metadata file parsing returned None: {meta_path}")
                return {}
            
            # Validate required fields
            self._validate_structured_metadata(metadata)
            
            return metadata
        except Exception as e:
            logger.error(f"Error parsing metadata file {meta_path}: {str(e)}")
            logger.error(f"File content: {content if 'content' in locals() else '<content not read>'}")
            raise ValueError(f"Error parsing metadata file: {str(e)}")
    
    def _parse_simple_key_value(self, content: str) -> Dict[str, Any]:
        """
        Parse metadata in a simple key-value format (like YAML but without advanced features).
        This is a fallback method when YAML and JSON parsing fails.
        
        Args:
            content: The metadata file content
            
        Returns:
            Dictionary of parsed metadata
        """
        result = {}
        current_list = None
        current_key = None
        indentation = 0
        
        for line in content.splitlines():
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            
            # Check if this is a list item
            if stripped.startswith('- '):
                # If we're already in a list context
                if current_list is not None and current_key:
                    current_list.append(stripped[2:])
                continue
            
            # This should be a key-value pair
            if ':' in stripped:
                parts = stripped.split(':', 1)
                key = parts[0].strip()
                value = parts[1].strip() if len(parts) > 1 else ""
                
                # If value is empty, this might be a dictionary or list start
                if not value:
                    current_key = key
                    current_list = []
                    result[key] = current_list
                else:
                    # Simple key-value pair
                    result[key] = value
                    current_key = None
                    current_list = None
        
        return result
    
    def parse_legacy_metadata(self, content: str) -> Dict[str, Any]:
        """
        Parse legacy metadata from module content.
        
        Args:
            content: The module content as a string
            
        Returns:
            Dictionary of parsed metadata
        """
        # Extract metadata sections
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
                    'description': description,
                    'required': True
                })
            else:
                parsed_files.append({
                    'name': line.strip(),
                    'description': '',
                    'required': True
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
                    'description': description,
                    'required': True
                })
            else:
                parsed_args.append({
                    'name': line.strip(),
                    'description': '',
                    'required': True
                })
        
        # Parse the nessus findings section
        parsed_nessus = []
        for line in nessus:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            parsed_nessus.append(line)
        
        # Construct the metadata dictionary in the structured format
        metadata = {
            'name': '',  # Will be filled by caller with filename
            'description': 'Converted from legacy format',
            'version': '1.0.0',
            'author': author,
            'files': parsed_files,
            'arguments': parsed_args,
            'nessus_findings': parsed_nessus,
            'categories': []
        }
        
        return metadata
    
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
        Validate structured metadata.
        
        Args:
            metadata: The metadata dictionary
            
        Returns:
            True if valid
            
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
    
    def generate_metadata_from_legacy(self, module_path: str) -> Dict[str, Any]:
        """
        Generate structured metadata from a legacy module and save it.
        
        Args:
            module_path: Path to the legacy module file
            
        Returns:
            Dictionary of generated metadata
            
        Raises:
            FileNotFoundError: If the module file doesn't exist
            ValueError: If there's an error parsing the metadata
        """
        if not os.path.isfile(module_path):
            raise FileNotFoundError(f"Module file not found: {module_path}")
        
        # Check if there's already a metadata file
        meta_path = f"{module_path}.meta"
        if os.path.isfile(meta_path):
            logger.warning(f"Metadata file already exists: {meta_path}")
            return self.parse_structured_metadata(meta_path)
        
        # Read the module content
        with open(module_path, 'r') as f:
            content = f.read()
        
        # Parse the legacy metadata
        metadata = self.parse_legacy_metadata(content)
        
        # Add filename-based info
        filename = os.path.basename(module_path)
        metadata['name'] = filename
        
        # Determine script type
        ext = os.path.splitext(filename)[1]
        if ext == '.sh':
            script_type = 'bash'
        elif ext == '.py':
            script_type = 'python'
        elif ext == '.json':
            script_type = 'json'
        else:
            script_type = 'unknown'
        
        metadata['script_type'] = script_type
        
        # Save the metadata file
        with open(meta_path, 'w') as f:
            yaml.dump(metadata, f, default_flow_style=False)
        
        logger.info(f"Generated metadata file: {meta_path}")
        
        return metadata
    
    def format_legacy_metadata(self, metadata: Dict[str, Any]) -> str:
        """
        Format structured metadata as legacy comment-based metadata.
        
        Args:
            metadata: The metadata dictionary
            
        Returns:
            String of formatted legacy metadata
        """
        lines = []
        
        # Format files section
        if 'files' in metadata and metadata['files']:
            lines.append('# STARTFILES')
            for file_info in metadata['files']:
                name = file_info['name']
                desc = file_info.get('description', '')
                if desc:
                    lines.append(f'# {name} "{desc}"')
                else:
                    lines.append(f'# {name}')
            lines.append('# ENDFILES')
            lines.append('')
        
        # Format args section
        if 'arguments' in metadata and metadata['arguments']:
            lines.append('# ARGS')
            for arg_info in metadata['arguments']:
                name = arg_info['name']
                desc = arg_info.get('description', '')
                if desc:
                    lines.append(f'# {name} "{desc}"')
                else:
                    lines.append(f'# {name}')
            lines.append('# ENDARGS')
            lines.append('')
        
        # Format nessus findings section
        if 'nessus_findings' in metadata and metadata['nessus_findings']:
            lines.append('# NESSUSFINDING')
            for finding in metadata['nessus_findings']:
                lines.append(f'# {finding}')
            lines.append('# ENDNESSUS')
            lines.append('')
        
        # Format author
        if 'author' in metadata and metadata['author']:
            lines.append(f'# AUTHOR: {metadata["author"]}')
            lines.append('')
        
        return '\n'.join(lines)
    
    def update_module_with_metadata(self, module_path: str, metadata: Dict[str, Any], use_structured: bool = True) -> bool:
        """
        Update a module file with new metadata.
        
        Args:
            module_path: Path to the module file
            metadata: The metadata dictionary
            use_structured: Whether to use structured metadata (separate file)
            
        Returns:
            True if successful, False otherwise
        """
        if not os.path.isfile(module_path):
            raise FileNotFoundError(f"Module file not found: {module_path}")
        
        if use_structured:
            # Save as structured metadata file
            meta_path = f"{module_path}.meta"
            try:
                with open(meta_path, 'w') as f:
                    yaml.dump(metadata, f, default_flow_style=False)
                logger.info(f"Updated metadata file: {meta_path}")
                return True
            except Exception as e:
                logger.error(f"Error updating metadata file: {str(e)}")
                return False
        else:
            # Update the module content with legacy metadata
            try:
                # Read the current content
                with open(module_path, 'r') as f:
                    content = f.read()
                
                # Remove existing metadata sections
                content = self._remove_legacy_metadata(content)
                
                # Format the new metadata
                legacy_metadata = self.format_legacy_metadata(metadata)
                
                # Add the new metadata at the beginning, preserving shebang if present
                if content.startswith('#!'):
                    shebang_end = content.find('\n') + 1
                    new_content = content[:shebang_end] + '\n' + legacy_metadata + content[shebang_end:]
                else:
                    new_content = legacy_metadata + content
                
                # Write the updated content
                with open(module_path, 'w') as f:
                    f.write(new_content)
                
                logger.info(f"Updated module file with legacy metadata: {module_path}")
                return True
            except Exception as e:
                logger.error(f"Error updating module file: {str(e)}")
                return False
    
    def _remove_legacy_metadata(self, content: str) -> str:
        """
        Remove legacy metadata sections from module content.
        
        Args:
            content: The module content
            
        Returns:
            Content with metadata sections removed
        """
        # Remove files section
        content = self._remove_legacy_section(content, 
                                             self.LEGACY_MARKERS['files_start'], 
                                             self.LEGACY_MARKERS['files_end'])
        
        # Remove args section
        content = self._remove_legacy_section(content, 
                                            self.LEGACY_MARKERS['args_start'], 
                                            self.LEGACY_MARKERS['args_end'])
        
        # Remove nessus section
        content = self._remove_legacy_section(content, 
                                             self.LEGACY_MARKERS['nessus_start'], 
                                             self.LEGACY_MARKERS['nessus_end'])
        
        # Remove author line
        author_pattern = self.LEGACY_MARKERS['author'] + r'.*\n'
        content = re.sub(author_pattern, '', content)
        
        return content
    
    def _remove_legacy_section(self, content: str, start_marker: str, end_marker: str) -> str:
        """
        Remove a legacy section from module content.
        
        Args:
            content: The module content
            start_marker: Start marker regex pattern
            end_marker: End marker regex pattern
            
        Returns:
            Content with section removed
        """
        # Find start and end positions
        lines = content.splitlines(True)  # Keep line endings
        new_lines = []
        in_section = False
        
        for line in lines:
            if re.match(start_marker, line):
                in_section = True
                continue
            elif re.match(end_marker, line):
                in_section = False
                continue
            
            if not in_section:
                new_lines.append(line)
        
        return ''.join(new_lines)


# Example usage
if __name__ == "__main__":
    parser = MetadataParser()
    
    # Example for parsing legacy metadata
    try:
        sample_content = """#!/bin/bash
# STARTFILES
# targets.txt "List of target hosts"
# ENDFILES
# ARGS
# PORT "Port number to scan"
# ENDARGS
# NESSUSFINDING
# SSH Server CBC Mode Ciphers Enabled
# ENDNESSUS
# AUTHOR: Test User

echo "This is a test module"
"""
        metadata = parser.parse_legacy_metadata(sample_content)
        print("Parsed legacy metadata:")
        print(json.dumps(metadata, indent=2))
        
        # Format back to legacy
        legacy_format = parser.format_legacy_metadata(metadata)
        print("\nFormatted as legacy metadata:")
        print(legacy_format)
    except Exception as e:
        print(f"Error: {str(e)}") 