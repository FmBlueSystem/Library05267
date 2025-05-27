#!/usr/bin/env python3
"""
Configuración de Sphinx para la documentación de Nueva Biblioteca.
"""

import os
import sys
from datetime import datetime

# Agregar el código fuente al path
sys.path.insert(0, os.path.abspath("../src"))

# Información del proyecto
project = "Nueva Biblioteca"
copyright = f"{datetime.now().year}, FmBlueSystem"
author = "FmBlueSystem"
version = "1.0"
release = "1.0.0"

# Extensiones de Sphinx
extensions = [
    "sphinx.ext.autodoc",      # Documentación automática de código
    "sphinx.ext.napoleon",     # Soporte para docstrings Google/NumPy
    "sphinx.ext.viewcode",     # Enlaces al código fuente
    "sphinx.ext.intersphinx",  # Enlaces a otra documentación
    "sphinx.ext.todo",         # Soporte para TODOs
    "sphinx.ext.coverage",     # Cobertura de documentación
    "sphinx.ext.githubpages",  # Soporte para GitHub Pages
    "sphinx_rtd_theme",        # Tema Read the Docs
]

# Configuración de extensiones
autodoc_default_options = {
    "members": True,
    "undoc-members": True,
    "show-inheritance": True,
    "member-order": "bysource",
}

napoleon_google_docstring = True
napoleon_numpy_docstring = False
napoleon_include_init_with_doc = True
napoleon_include_private_with_doc = True

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
    "PyQt6": ("https://doc.qt.io/qtforpython/", None),
}

# Configuración de búsqueda
templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

# Opciones HTML
html_theme = "sphinx_rtd_theme"
html_static_path = ["_static"]
html_title = "Nueva Biblioteca"
html_logo = "_static/logo.png"
html_favicon = "_static/favicon.ico"

html_theme_options = {
    "logo_only": True,
    "display_version": True,
    "style_external_links": True,
    "style_nav_header_background": "#2980B9",
}

# Configuración de lenguaje
language = "es"
locale_dirs = ["locale/"]
gettext_compact = False

# Configuración de generación de PDF
latex_elements = {
    "papersize": "letterpaper",
    "pointsize": "10pt",
    "figure_align": "htbp",
    "babel": "\\usepackage[spanish]{babel}",
}

# Estructura de la documentación
master_doc = "index"
source_suffix = ".rst"

# Configuración de advertencias
nitpicky = True
nitpick_ignore = [
    ("py:class", "PyQt6.QtWidgets.QWidget"),
    ("py:class", "PyQt6.QtCore.QObject"),
]

# Logging
keep_warnings = True
warning_is_error = True

# Generación de documentación de API
add_module_names = False
autodoc_typehints = "description"
autodoc_typehints_format = "short"

# TODOs
todo_include_todos = True
todo_link_only = False

# Configuración de cobertura
coverage_show_missing_items = True
coverage_skip_undoc_in_source = True

# Configuración de GitHub
html_context = {
    "display_github": True,
    "github_user": "FmBlueSystem",
    "github_repo": "nueva-biblioteca",
    "github_version": "main",
    "conf_py_path": "/docs/",
}
