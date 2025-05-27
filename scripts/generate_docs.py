#!/usr/bin/env python3
"""
Script para generar la documentación de Nueva Biblioteca.

Este script automatiza la generación de documentación usando Sphinx
y realiza varias tareas de preparación y limpieza.
"""

from typing import List, Optional
from pathlib import Path
import subprocess
import shutil
import sys
import os

def run_command(command: List[str], cwd: Optional[Path] = None) -> bool:
    """
    Ejecuta un comando del sistema.
    
    Args:
        command: Lista con el comando y sus argumentos
        cwd: Directorio de trabajo o None para usar el actual
        
    Returns:
        True si el comando fue exitoso
    """
    try:
        subprocess.run(
            command,
            cwd=cwd,
            check=True,
            capture_output=True,
            text=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando {' '.join(command)}:")
        print(e.stdout)
        print(e.stderr, file=sys.stderr)
        return False

def clean_build_directory(docs_dir: Path) -> None:
    """
    Limpia el directorio de construcción.
    
    Args:
        docs_dir: Directorio de documentación
    """
    build_dir = docs_dir / "_build"
    if build_dir.exists():
        shutil.rmtree(build_dir)
        print("✓ Limpiado directorio _build")

def verify_requirements() -> bool:
    """
    Verifica que estén instalados los requisitos.
    
    Returns:
        True si todos los requisitos están instalados
    """
    requirements = [
        "sphinx",
        "sphinx-rtd-theme",
        "sphinx-autodoc-typehints",
        "myst-parser"
    ]
    
    for req in requirements:
        try:
            __import__(req.replace("-", "_"))
        except ImportError:
            print(f"✗ Falta dependencia: {req}")
            return False
    
    print("✓ Todas las dependencias están instaladas")
    return True

def generate_api_docs(project_dir: Path, docs_dir: Path) -> bool:
    """
    Genera la documentación de API usando sphinx-apidoc.
    
    Args:
        project_dir: Directorio raíz del proyecto
        docs_dir: Directorio de documentación
        
    Returns:
        True si la generación fue exitosa
    """
    api_dir = docs_dir / "api"
    api_dir.mkdir(exist_ok=True)
    
    src_dir = project_dir / "src" / "nueva_biblioteca"
    
    command = [
        "sphinx-apidoc",
        "-f",                  # Forzar regeneración
        "-e",                  # Separar módulos
        "-M",                  # Poner módulo antes que paquete
        "-o", str(api_dir),    # Directorio de salida
        str(src_dir),          # Directorio fuente
        str(src_dir/"*/tests") # Excluir tests
    ]
    
    if run_command(command):
        print("✓ Documentación de API generada")
        return True
    return False

def build_html(docs_dir: Path) -> bool:
    """
    Construye la documentación en HTML.
    
    Args:
        docs_dir: Directorio de documentación
        
    Returns:
        True si la construcción fue exitosa
    """
    command = [
        "sphinx-build",
        "-b", "html",           # Formato HTML
        "-d", "_build/doctrees", # Directorio para doctrees
        "-W",                    # Warnings como errores
        ".",                     # Directorio fuente
        "_build/html"            # Directorio destino
    ]
    
    if run_command(command, docs_dir):
        print("✓ Documentación HTML generada")
        return True
    return False

def build_pdf(docs_dir: Path) -> bool:
    """
    Construye la documentación en PDF.
    
    Args:
        docs_dir: Directorio de documentación
        
    Returns:
        True si la construcción fue exitosa
    """
    command = [
        "sphinx-build",
        "-b", "latex",          # Formato LaTeX
        "-d", "_build/doctrees", # Directorio para doctrees
        ".",                     # Directorio fuente
        "_build/latex"           # Directorio destino
    ]
    
    if not run_command(command, docs_dir):
        return False
    
    # Construir PDF
    latex_dir = docs_dir / "_build" / "latex"
    command = ["make"]
    
    if run_command(command, latex_dir):
        print("✓ Documentación PDF generada")
        pdf = latex_dir / "nuevabiblioteca.pdf"
        if pdf.exists():
            shutil.copy(pdf, docs_dir / "_build" / "html")
            print("✓ PDF copiado al directorio HTML")
        return True
    return False

def main() -> int:
    """
    Función principal.
    
    Returns:
        0 si todo fue exitoso, otro valor en caso de error
    """
    project_dir = Path(__file__).parent.parent
    docs_dir = project_dir / "docs"
    
    print("=== Generando documentación ===")
    
    # Verificar requisitos
    if not verify_requirements():
        return 1
    
    # Limpiar directorio
    clean_build_directory(docs_dir)
    
    # Generar documentación
    if not generate_api_docs(project_dir, docs_dir):
        return 1
    
    # Construir HTML
    if not build_html(docs_dir):
        return 1
    
    # Construir PDF
    if not build_pdf(docs_dir):
        print("⚠ No se pudo generar el PDF")
    
    print("\n✨ Documentación generada exitosamente")
    print(f"HTML: {docs_dir}/_build/html/index.html")
    print(f"PDF: {docs_dir}/_build/latex/nuevabiblioteca.pdf")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
