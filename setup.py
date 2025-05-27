#!/usr/bin/env python3
"""
Script de configuración para Nueva Biblioteca.
"""

from typing import List, Dict
from pathlib import Path
import os
import re

from setuptools import setup, find_packages

def read(fname: str) -> str:
    """Lee un archivo y retorna su contenido."""
    return Path(fname).read_text('utf-8')

def get_version() -> str:
    """Obtiene la versión desde el archivo __init__.py."""
    init = Path('src/nueva_biblioteca/__init__.py').read_text()
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", init, re.M)
    if version_match:
        return version_match.group(1)
    raise RuntimeError("Versión no encontrada")

def parse_requirements(filename: str) -> List[str]:
    """
    Parsea un archivo de requerimientos.
    
    Args:
        filename: Nombre del archivo
        
    Returns:
        Lista de requerimientos
    """
    requirements = []
    extras: Dict[str, List[str]] = {}
    current_extra = None
    
    for line in read(filename).splitlines():
        line = line.strip()
        
        # Saltar comentarios y líneas vacías
        if not line or line.startswith('#'):
            continue
        
        # Detectar extras
        if line.startswith('[') and line.endswith(']'):
            current_extra = line[1:-1]
            extras[current_extra] = []
            continue
        
        # Manejar dependencias condicionales
        if ';' in line:
            pkg, cond = line.split(';', 1)
            # Agregar solo si la condición se cumple
            if _evaluate_marker(cond.strip()):
                line = pkg.strip()
            else:
                continue
        
        if current_extra:
            extras[current_extra].append(line)
        else:
            requirements.append(line)
    
    return requirements

def _evaluate_marker(marker: str) -> bool:
    """
    Evalúa un marcador de ambiente.
    
    Args:
        marker: Marcador a evaluar
        
    Returns:
        True si el marcador se cumple
    """
    import platform
    
    env = {
        'sys_platform': platform.system().lower(),
        'python_version': platform.python_version(),
        'platform_machine': platform.machine().lower()
    }
    
    try:
        return eval(marker, {'__builtins__': {}}, env)
    except:
        return False

setup(
    name="nueva-biblioteca",
    version=get_version(),
    description="Sistema de biblioteca musical con playlists inteligentes",
    long_description=read('README.md'),
    long_description_content_type="text/markdown",
    author="FmBlueSystem",
    author_email="info@fmbluesystem.com",
    url="https://github.com/FmBlueSystem/nueva-biblioteca",
    license="MIT",
    
    # Paquetes y datos
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    include_package_data=True,
    package_data={
        "nueva_biblioteca": [
            "assets/fonts/*.ttf",
            "assets/icons/*.svg",
            "assets/icons/*.ico",
            "assets/i18n/*.qm"
        ]
    },
    
    # Entrypoints
    entry_points={
        "console_scripts": [
            "nueva-biblioteca=nueva_biblioteca.main:main",
        ],
        "gui_scripts": [
            "nueva-biblioteca-gui=nueva_biblioteca.main:main",
        ]
    },
    
    # Requerimientos
    python_requires=">=3.11",
    install_requires=parse_requirements('requirements.txt'),
    extras_require={
        "dev": parse_requirements('requirements.txt')["dev"],
        "docs": parse_requirements('requirements.txt')["docs"],
        "performance": parse_requirements('requirements.txt')["performance"],
        "gui": parse_requirements('requirements.txt')["gui"],
        "audio": parse_requirements('requirements.txt')["audio"],
        "full": [
            dep for extra in ["dev", "docs", "performance", "gui", "audio"]
            for dep in parse_requirements('requirements.txt')[extra]
        ]
    },
    
    # Metadatos
    keywords=[
        "music",
        "library",
        "audio",
        "playlist",
        "metadata",
        "analysis",
        "recommendations"
    ],
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: Qt",
        "Intended Audience :: End Users/Desktop",
        "License :: OSI Approved :: MIT License",
        "Natural Language :: Spanish",
        "Operating System :: OS Independent",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: Multimedia :: Sound/Audio",
        "Topic :: Multimedia :: Sound/Audio :: Analysis",
        "Topic :: Multimedia :: Sound/Audio :: Players",
    ],
    
    # Opciones de proyecto
    zip_safe=False,
    platforms=["any"],
)
