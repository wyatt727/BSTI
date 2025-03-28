# Configuration file for the Sphinx documentation builder.
#
# This file only contains a selection of the most common options. For a full
# list see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
import datetime

# -- Path setup --------------------------------------------------------------

# Add the project source directory to the path so that autodoc can find the modules
sys.path.insert(0, os.path.abspath('../..'))

# Import the version from the package
from bsti_nessus import __version__

# -- Project information -----------------------------------------------------

project = 'BSTI Nessus'
copyright = f'{datetime.datetime.now().year}, BSTI Team'
author = 'BSTI Team'

# The full version, including alpha/beta/rc tags
release = __version__

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension modules here
extensions = [
    'sphinx.ext.autodoc',  # Automatically generate API documentation
    'sphinx.ext.napoleon',  # Support for Google style docstrings
    'sphinx.ext.viewcode',  # Add links to view the source code
    'sphinx.ext.intersphinx',  # Link to other projects' documentation
    'sphinx.ext.coverage',  # Check documentation coverage
    'sphinx.ext.autosummary',  # Generate summary tables for API docs
]

# Add any paths that contain templates here, relative to this directory
templates_path = ['_templates']

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files
exclude_patterns = ['_build', 'Thumbs.db', '.DS_Store']

# The name of the Pygments (syntax highlighting) style to use
pygments_style = 'sphinx'

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.
html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# Configure intersphinx mapping
intersphinx_mapping = {
    'python': ('https://docs.python.org/3', None),
}

# Generate API docs for all modules
autosummary_generate = True
autodoc_member_order = 'bysource'

# Add module names to the documents
add_module_names = False 