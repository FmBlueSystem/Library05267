#!/usr/bin/env python3
"""
Script de entrada para Nueva Biblioteca
=====================================

Script simple para ejecutar la aplicación.
"""

import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

if __name__ == "__main__":
    from nueva_biblioteca.main import main
    sys.exit(main()) 