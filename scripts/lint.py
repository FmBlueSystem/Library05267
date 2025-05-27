#!/usr/bin/env python3
"""
Script de linting para Nueva Biblioteca.

Este script ejecuta ruff y mypy para verificar el estilo
y tipos del código.
"""

from typing import List, Set, Tuple
from pathlib import Path
import subprocess
import sys
import os

def run_command(command: List[str], capture: bool = True) -> Tuple[int, str, str]:
    """
    Ejecuta un comando del sistema.
    
    Args:
        command: Lista con el comando y sus argumentos
        capture: Si debe capturar la salida
        
    Returns:
        Tupla con (código de salida, stdout, stderr)
    """
    try:
        result = subprocess.run(
            command,
            capture_output=capture,
            text=True,
            check=False
        )
        return result.returncode, result.stdout, result.stderr
    except Exception as e:
        return 1, "", str(e)

def find_python_files(directory: Path, exclude: Set[str]) -> List[Path]:
    """
    Encuentra archivos Python en un directorio.
    
    Args:
        directory: Directorio a buscar
        exclude: Conjunto de patrones a excluir
        
    Returns:
        Lista de rutas a archivos Python
    """
    python_files = []
    
    for path in directory.rglob("*.py"):
        # Verificar exclusiones
        if any(excl in str(path) for excl in exclude):
            continue
        python_files.append(path)
    
    return sorted(python_files)

def run_ruff(files: List[Path]) -> bool:
    """
    Ejecuta Ruff para linting y formato.
    
    Args:
        files: Lista de archivos a verificar
        
    Returns:
        True si no hubo errores
    """
    print("\n=== Ejecutando Ruff ===")
    
    # Verificar estilo
    print("\nVerificando estilo...")
    code, out, err = run_command(["ruff", "check"] + [str(f) for f in files])
    
    if code != 0:
        print("⚠ Problemas de estilo encontrados:")
        print(out)
        return False
    
    print("✓ Verificación de estilo exitosa")
    
    # Verificar formato
    print("\nVerificando formato...")
    code, out, err = run_command(["ruff", "format", "--check"] + [str(f) for f in files])
    
    if code != 0:
        print("⚠ Problemas de formato encontrados")
        print(out)
        print("\nPara corregir automáticamente ejecuta: ruff format")
        return False
    
    print("✓ Verificación de formato exitosa")
    return True

def run_mypy(files: List[Path]) -> bool:
    """
    Ejecuta MyPy para verificación de tipos.
    
    Args:
        files: Lista de archivos a verificar
        
    Returns:
        True si no hubo errores
    """
    print("\n=== Ejecutando MyPy ===")
    
    code, out, err = run_command(["mypy"] + [str(f) for f in files])
    
    if code != 0:
        print("⚠ Problemas de tipos encontrados:")
        print(out)
        return False
    
    print("✓ Verificación de tipos exitosa")
    return True

def main() -> int:
    """
    Función principal.
    
    Returns:
        0 si todo fue exitoso, otro valor en caso de error
    """
    # Configuración
    project_dir = Path(__file__).parent.parent
    src_dir = project_dir / "src"
    tests_dir = project_dir / "tests"
    
    exclude = {
        "/.venv/",
        "/.git/",
        "/__pycache__/",
        "/build/",
        "/dist/"
    }
    
    # Encontrar archivos
    python_files = (
        find_python_files(src_dir, exclude) +
        find_python_files(tests_dir, exclude)
    )
    
    if not python_files:
        print("No se encontraron archivos Python para verificar")
        return 1
    
    print(f"Verificando {len(python_files)} archivos...")
    
    # Ejecutar verificaciones
    success = True
    
    if not run_ruff(python_files):
        success = False
    
    if not run_mypy(python_files):
        success = False
    
    if success:
        print("\n✨ Todas las verificaciones pasaron exitosamente")
        return 0
    else:
        print("\n⚠ Se encontraron problemas que necesitan corrección")
        return 1

if __name__ == "__main__":
    sys.exit(main())
