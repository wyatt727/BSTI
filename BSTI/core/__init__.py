#!/usr/bin/env python3
"""
BSTI Core Module

This package provides the core functionality for the BSTI application,
including module management, metadata parsing, validation, and template handling.
"""

from .module_manager import ModuleManager
from .metadata_parser import MetadataParser
from .module_validator import ModuleValidator
from .template_engine import TemplateEngine

__all__ = [
    'ModuleManager',
    'MetadataParser',
    'ModuleValidator',
    'TemplateEngine'
] 