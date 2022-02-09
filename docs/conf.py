# Configuration file for the Sphinx documentation builder.

# -- Setup function ----------------------------------------------------------

# Defines custom steps in the process.

def autodoc_skip_member(app, what, name, obj, skip, options):
    """Exclude all private attributes, methods, and dunder methods from Sphinx."""
    import re
    exclude = re.findall(r'\._.*', str(obj))
    return skip or exclude

def remove_module_docstring(app, what, name, obj, options, lines):
    if what == "module":
        del lines[:]
    return

def setup(app):
    app.connect('autodoc-skip-member', autodoc_skip_member)
    app.connect("autodoc-process-docstring", remove_module_docstring)
    return

# -- Path setup --------------------------------------------------------------

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
import os
import sys
sys.path.insert(0, os.path.abspath('..')) 

# -- Project information -----------------------------------------------------
project = 'snowfake'
copyright = '2022, Agile Scientific'
author = 'Agile Scientific'

# -- General configuration ---------------------------------------------------

# Add any Sphinx extension module names here, as strings. They can be
# extensions coming with Sphinx (named 'sphinx.ext.*') or your custom
# ones.
extensions = ['sphinxcontrib.apidoc',
              'sphinx.ext.napoleon',
              'myst_parser',
              'sphinx.ext.viewcode'
]

myst_enable_extensions = ["dollarmath", "amsmath"]

# Declare suffix for autodoc
source_suffix = {
                '.rst': 'restructuredtext',
                '.txt': 'markdown',
                '.md': 'markdown',
            }

# Add any paths that contain templates here, relative to this directory.
templates_path = ['_templates']

# Add sidebar.
html_sidebars = {
   '**': ['about.html',
          'searchbox.html',
          'navigation.html',
          ],
}

html_theme_options = {
    'canonical_url': 'https://code.agilescientific.com/',
    'description': 'Gravner&ndash;Griffeath snowflake simulation. Cool!',
    'logo': 'snowfake_logo.png',
    'logo_name': False,
    'show_powered_by': False,
    'fixed_sidebar': True,
    'github_user': 'agile-geoscience',
    'github_repo': 'snowfake',
    'github_banner': True,
    'github_button': True,
    'github_type': 'star',
    'extra_nav_links': {
        'snowfake@GitHub': 'https://github.com/agile-geoscience/snowfake',
        'Agile website': 'https://agilescientific.com/',
    }
}

# List of patterns, relative to source directory, that match files and
# directories to ignore when looking for source files.
# This pattern also affects html_static_path and html_extra_path.
exclude_patterns = []

# Apidoc automation
# https://pypi.org/project/sphinxcontrib-apidoc/
# The apidoc extension and this code automatically update apidoc.
apidoc_module_dir = '../snowfake'
apidoc_output_dir = './'
apidoc_excluded_paths = []
apidoc_toc_file = False
apidoc_separate_modules = False

# -- Options for HTML output -------------------------------------------------

# The theme to use for HTML and HTML Help pages.  See the documentation for
# a list of builtin themes.
#
# html_theme = 'sphinx_rtd_theme'

# Add any paths that contain custom static files (such as style sheets) here,
# relative to this directory. They are copied after the builtin static files,
# so a file named "default.css" will overwrite the builtin "default.css".
html_static_path = ['_static']

# The name of an image file (within the static path) to use as favicon of the
# docs.  This file should be a Windows icon file (.ico) being 16x16 or 32x32
# pixels large.
html_favicon = '_static/favicon.ico'
