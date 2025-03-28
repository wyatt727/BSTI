#!/usr/bin/env python3
"""
BSTI Module Validator

This module provides functionality to validate BSTI modules, including checking
their structure, metadata, and performing basic syntax checking.
"""

import os
import re
import json
import yaml
import logging
import subprocess
import tempfile
from typing import Dict, List, Any, Optional, Tuple, Union

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ModuleValidator:
    """
    Validator for BSTI modules, checking structure, metadata, and syntax.
    """
    
    def __init__(self):
        """Initialize the module validator."""
        pass
    
    def validate_module(self, module_path: str, metadata: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """
        Validate a module file.
        
        Args:
            module_path: Path to the module file
            metadata: Optional metadata dictionary (if not provided, will be parsed from file)
            
        Returns:
            Tuple of (success, error_messages)
        """
        if not os.path.isfile(module_path):
            return False, [f"Module file not found: {module_path}"]
        
        errors = []
        
        # Determine module type from file extension
        _, ext = os.path.splitext(module_path)
        if ext == '.sh':
            script_type = 'bash'
        elif ext == '.py':
            script_type = 'python'
        elif ext == '.json':
            script_type = 'json'
        else:
            return False, [f"Unsupported module type: {ext}"]
        
        # Check metadata if provided
        if metadata is not None:
            metadata_valid, metadata_errors = self.validate_metadata(metadata)
            if not metadata_valid:
                errors.extend(metadata_errors)
        
        # Check the module content
        content_valid, content_errors = self.validate_module_content(module_path, script_type)
        if not content_valid:
            errors.extend(content_errors)
        
        # Return overall validation result
        return len(errors) == 0, errors
    
    def validate_metadata(self, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate module metadata.
        
        Args:
            metadata: The metadata dictionary
            
        Returns:
            Tuple of (success, error_messages)
        """
        errors = []
        
        # Check required fields
        required_fields = ['name', 'description', 'version', 'author']
        for field in required_fields:
            if field not in metadata:
                errors.append(f"Missing required metadata field: {field}")
        
        # Validate version format (semantic versioning)
        if 'version' in metadata:
            version = metadata['version']
            if not re.match(r'^\d+\.\d+(\.\d+)?$', str(version)):
                errors.append(f"Invalid version format (should be X.Y.Z): {version}")
        
        # Validate files format
        if 'files' in metadata:
            for i, file_info in enumerate(metadata['files']):
                if not isinstance(file_info, dict):
                    errors.append(f"Invalid format for file #{i+1}: must be a dictionary")
                    continue
                
                if 'name' not in file_info:
                    errors.append(f"Missing 'name' field for file #{i+1}")
        
        # Validate arguments format
        if 'arguments' in metadata:
            for i, arg_info in enumerate(metadata['arguments']):
                if not isinstance(arg_info, dict):
                    errors.append(f"Invalid format for argument #{i+1}: must be a dictionary")
                    continue
                
                if 'name' not in arg_info:
                    errors.append(f"Missing 'name' field for argument #{i+1}")
        
        # Return validation result
        return len(errors) == 0, errors
    
    def validate_module_content(self, module_path: str, script_type: str) -> Tuple[bool, List[str]]:
        """
        Validate the content of a module file.
        
        Args:
            module_path: Path to the module file
            script_type: Type of script ('bash', 'python', 'json')
            
        Returns:
            Tuple of (success, error_messages)
        """
        errors = []
        
        # Check file exists and is readable
        if not os.path.isfile(module_path):
            return False, [f"Module file not found: {module_path}"]
        
        try:
            with open(module_path, 'r') as f:
                content = f.read()
        except Exception as e:
            return False, [f"Error reading module file: {str(e)}"]
        
        # Check if file is empty
        if not content.strip():
            return False, ["Module file is empty"]
        
        # Check for specific script type
        if script_type == 'bash':
            return self._validate_bash_content(content)
        elif script_type == 'python':
            return self._validate_python_content(content)
        elif script_type == 'json':
            return self._validate_json_content(content)
        else:
            return False, [f"Unsupported script type: {script_type}"]
    
    def _validate_bash_content(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate bash script content.
        
        Args:
            content: The script content
            
        Returns:
            Tuple of (success, error_messages)
        """
        errors = []
        
        # Check for shebang
        if not content.startswith('#!/bin/bash') and not content.startswith('#!/bin/sh'):
            errors.append("Bash script should start with #!/bin/bash or #!/bin/sh")
        
        # Use bash -n to check for syntax errors
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.sh') as tmp:
                tmp.write(content)
                tmp.flush()
                
                # Run bash -n to check syntax without executing
                result = subprocess.run(['bash', '-n', tmp.name], 
                                       capture_output=True, 
                                       text=True)
                
                if result.returncode != 0:
                    errors.append(f"Bash syntax error: {result.stderr.strip()}")
        except Exception as e:
            errors.append(f"Error checking bash syntax: {str(e)}")
        
        # Check for common issues
        if 'rm -rf /' in content or 'rm -rf /*' in content:
            errors.append("Dangerous command detected: rm -rf / or rm -rf /*")
        
        # Return validation result
        return len(errors) == 0, errors
    
    def _validate_python_content(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate Python script content.
        
        Args:
            content: The script content
            
        Returns:
            Tuple of (success, error_messages)
        """
        errors = []
        
        # Check for shebang
        if not content.startswith('#!/usr/bin/env python') and not content.startswith('#!/usr/bin/python'):
            errors.append("Python script should start with #!/usr/bin/env python or #!/usr/bin/python")
        
        # Check for syntax errors
        try:
            compile(content, '<string>', 'exec')
        except SyntaxError as e:
            errors.append(f"Python syntax error: {str(e)}")
        
        # Check for potentially dangerous operations
        danger_patterns = [
            r'os\.system\([\'"]rm -rf',
            r'shutil\.rmtree\([\'"]/',
            r'exec\([\'"]',
            r'eval\([\'"]'
        ]
        
        for pattern in danger_patterns:
            if re.search(pattern, content):
                errors.append(f"Potentially dangerous code pattern detected: {pattern}")
        
        # Return validation result
        return len(errors) == 0, errors
    
    def _validate_json_content(self, content: str) -> Tuple[bool, List[str]]:
        """
        Validate JSON content.
        
        Args:
            content: The JSON content
            
        Returns:
            Tuple of (success, error_messages)
        """
        errors = []
        
        # Check if it's valid JSON
        try:
            json_data = json.loads(content)
            
            # Check for required high-level fields for BSTI JSON modules
            required_fields = ['name', 'tabs']
            for field in required_fields:
                if field not in json_data:
                    errors.append(f"Missing required field in JSON module: {field}")
            
            # Check tabs structure if present
            if 'tabs' in json_data:
                if not isinstance(json_data['tabs'], list):
                    errors.append("'tabs' field must be an array")
                else:
                    for i, tab in enumerate(json_data['tabs']):
                        if not isinstance(tab, dict):
                            errors.append(f"Tab #{i+1} must be an object")
                            continue
                            
                        if 'title' not in tab:
                            errors.append(f"Tab #{i+1} missing 'title' field")
                        
                        if 'content' not in tab and 'script' not in tab:
                            errors.append(f"Tab #{i+1} must have either 'content' or 'script' field")
            
        except json.JSONDecodeError as e:
            errors.append(f"Invalid JSON: {str(e)}")
        
        # Return validation result
        return len(errors) == 0, errors
    
    def check_external_dependencies(self, metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Check if external dependencies are installed.
        
        Args:
            metadata: The metadata dictionary
            
        Returns:
            Tuple of (success, messages)
        """
        if 'dependencies' not in metadata or not metadata['dependencies']:
            return True, []
        
        messages = []
        missing = []
        
        for dep in metadata['dependencies']:
            # Parse the dependency string (name, version, etc.)
            # For now, just check if command exists
            parts = dep.split()
            cmd = parts[0]
            
            # Check if command exists
            try:
                result = subprocess.run(['which', cmd], 
                                       capture_output=True, 
                                       text=True)
                
                if result.returncode != 0:
                    missing.append(cmd)
                    messages.append(f"Missing dependency: {cmd}")
                else:
                    messages.append(f"Dependency found: {cmd}")
            except Exception as e:
                messages.append(f"Error checking dependency {cmd}: {str(e)}")
                missing.append(cmd)
        
        # Return success if no missing dependencies
        return len(missing) == 0, messages
    
    def validate_module_files(self, module_dir: str) -> Tuple[bool, List[str]]:
        """
        Validate all modules in a directory.
        
        Args:
            module_dir: Directory containing modules
            
        Returns:
            Tuple of (success, error_messages)
        """
        if not os.path.isdir(module_dir):
            return False, [f"Module directory not found: {module_dir}"]
        
        errors = []
        success_count = 0
        failed_count = 0
        
        # Scan directory for module files
        for root, _, files in os.walk(module_dir):
            for filename in files:
                # Skip non-module files and metadata files
                if (not filename.endswith('.sh') and 
                    not filename.endswith('.py') and 
                    not filename.endswith('.json')):
                    continue
                
                if filename.endswith('.meta'):
                    continue
                
                # Validate the module
                module_path = os.path.join(root, filename)
                valid, module_errors = self.validate_module(module_path)
                
                if valid:
                    success_count += 1
                else:
                    failed_count += 1
                    error_msg = f"Validation failed for {module_path}: {', '.join(module_errors)}"
                    errors.append(error_msg)
        
        # Add summary
        summary = f"Validated {success_count + failed_count} modules: {success_count} passed, {failed_count} failed"
        errors.insert(0, summary)
        
        return failed_count == 0, errors


# Example usage
if __name__ == "__main__":
    validator = ModuleValidator()
    
    # Example bash script
    bash_content = """#!/bin/bash
# Test script
echo "Hello, world!"
exit 0
"""
    
    valid, errors = validator.validate_module_content(None, "bash")
    print(f"Bash validation: {'Passed' if valid else 'Failed'}")
    if errors:
        print("Errors:")
        for error in errors:
            print(f"- {error}")
    
    # Example Python script with error
    python_content = """#!/usr/bin/env python3
# Test script with syntax error
print("Hello, world!"
"""
    
    # Example JSON module
    json_content = """{
    "name": "Test Module",
    "tabs": [
        {
            "title": "Info",
            "content": "This is a test module"
        },
        {
            "title": "Run",
            "script": "echo 'Running test...'"
        }
    ]
}
""" 