#!/usr/bin/env python3
"""
Script de construcción para Nueva Biblioteca.

Este script maneja la compilación, empaquetado y generación
de instaladores para diferentes plataformas.
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
import subprocess
import platform
import shutil
import json
import sys
import os

def run_command(command: List[str], cwd: Optional[Path] = None) -> bool:
    """
    Ejecuta un comando del sistema.
    
    Args:
        command: Lista con el comando y sus argumentos
        cwd: Directorio de trabajo
        
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

def clean_build_dirs(project_dir: Path) -> None:
    """
    Limpia directorios de construcción.
    
    Args:
        project_dir: Directorio del proyecto
    """
    dirs_to_clean = [
        "build",
        "dist",
        "*.egg-info",
        "__pycache__",
        ".pytest_cache",
        ".ruff_cache",
        ".mypy_cache",
        "htmlcov"
    ]
    
    for pattern in dirs_to_clean:
        for path in project_dir.rglob(pattern):
            if path.is_dir():
                shutil.rmtree(path)
            else:
                path.unlink()
    
    print("✓ Directorios de construcción limpiados")

def build_ui_resources(project_dir: Path) -> bool:
    """
    Compila recursos de UI.
    
    Args:
        project_dir: Directorio del proyecto
        
    Returns:
        True si la compilación fue exitosa
    """
    print("\n=== Compilando recursos de UI ===")
    
    resources_dir = project_dir / "src" / "nueva_biblioteca" / "ui" / "resources"
    if not resources_dir.exists():
        return True
    
    success = True
    
    # Compilar archivos .qrc
    for qrc_file in resources_dir.glob("*.qrc"):
        py_file = qrc_file.with_suffix(".py")
        
        if not run_command(["pyside6-rcc", "-o", str(py_file), str(qrc_file)]):
            success = False
    
    # Compilar archivos .ui
    for ui_file in resources_dir.glob("*.ui"):
        py_file = ui_file.with_suffix(".py")
        
        if not run_command(["pyside6-uic", "-o", str(py_file), str(ui_file)]):
            success = False
    
    return success

def build_package(project_dir: Path) -> bool:
    """
    Construye el paquete Python.
    
    Args:
        project_dir: Directorio del proyecto
        
    Returns:
        True si la construcción fue exitosa
    """
    print("\n=== Construyendo paquete Python ===")
    
    # Construir distribución
    if not run_command(["python", "-m", "build"], cwd=project_dir):
        return False
    
    print("✓ Paquete construido exitosamente")
    return True

def build_executable(project_dir: Path) -> bool:
    """
    Construye ejecutable con PyInstaller.
    
    Args:
        project_dir: Directorio del proyecto
        
    Returns:
        True si la construcción fue exitosa
    """
    print("\n=== Construyendo ejecutable ===")
    
    # Configuración de PyInstaller
    spec = {
        "name": "nueva-biblioteca",
        "console": False,
        "icon": "assets/icons/app.ico",
        "data": [
            ("assets/fonts/*", "assets/fonts"),
            ("assets/icons/*", "assets/icons"),
            ("assets/i18n/*", "assets/i18n")
        ],
        "hidden_imports": [
            "PyQt6.QtSvg",
            "PyQt6.QtMultimedia"
        ]
    }
    
    # Guardar spec
    spec_file = project_dir / "nueva-biblioteca.spec"
    spec_file.write_text(json.dumps(spec, indent=2))
    
    # Construir ejecutable
    command = [
        "pyinstaller",
        "--clean",
        "--windowed",
        "--onefile",
        f"--name={spec['name']}",
        f"--icon={project_dir/spec['icon']}",
        "--specpath", str(project_dir),
        "--distpath", str(project_dir/"dist"),
        "--workpath", str(project_dir/"build"),
        str(project_dir/"src"/"nueva_biblioteca"/"main.py")
    ]
    
    for src, dest in spec["data"]:
        command.extend(["--add-data", f"{src};{dest}"])
    
    for imp in spec["hidden_imports"]:
        command.extend(["--hidden-import", imp])
    
    if not run_command(command):
        return False
    
    print("✓ Ejecutable construido exitosamente")
    return True

def create_installer(project_dir: Path) -> bool:
    """
    Crea instalador según la plataforma.
    
    Args:
        project_dir: Directorio del proyecto
        
    Returns:
        True si la creación fue exitosa
    """
    print("\n=== Creando instalador ===")
    
    system = platform.system().lower()
    
    if system == "windows":
        return _create_windows_installer(project_dir)
    elif system == "darwin":
        return _create_macos_installer(project_dir)
    elif system == "linux":
        return _create_linux_installer(project_dir)
    else:
        print(f"⚠ Plataforma no soportada: {system}")
        return False

def _create_windows_installer(project_dir: Path) -> bool:
    """
    Crea instalador para Windows usando NSIS.
    
    Args:
        project_dir: Directorio del proyecto
        
    Returns:
        True si la creación fue exitosa
    """
    # TODO: Implementar creación de instalador Windows
    print("⚠ Creación de instalador Windows no implementada")
    return False

def _create_macos_installer(project_dir: Path) -> bool:
    """
    Crea instalador para macOS (.dmg).
    
    Args:
        project_dir: Directorio del proyecto
        
    Returns:
        True si la creación fue exitosa
    """
    # TODO: Implementar creación de instalador macOS
    print("⚠ Creación de instalador macOS no implementada")
    return False

def _create_linux_installer(project_dir: Path) -> bool:
    """
    Crea instalador para Linux (.deb/.rpm).
    
    Args:
        project_dir: Directorio del proyecto
        
    Returns:
        True si la creación fue exitosa
    """
    # TODO: Implementar creación de instalador Linux
    print("⚠ Creación de instalador Linux no implementada")
    return False

def main() -> int:
    """
    Función principal.
    
    Returns:
        0 si todo fue exitoso, otro valor en caso de error
    """
    project_dir = Path(__file__).parent.parent
    
    # Limpiar directorios
    clean_build_dirs(project_dir)
    
    # Compilar recursos
    if not build_ui_resources(project_dir):
        print("\n⚠ Error compilando recursos de UI")
        return 1
    
    # Construir paquete
    if not build_package(project_dir):
        print("\n⚠ Error construyendo paquete")
        return 1
    
    # Construir ejecutable
    if not build_executable(project_dir):
        print("\n⚠ Error construyendo ejecutable")
        return 1
    
    # Crear instalador
    if not create_installer(project_dir):
        print("\n⚠ Error creando instalador")
        return 1
    
    print("\n✨ Construcción completada exitosamente")
    print("\nArtefactos generados:")
    print(f"- Paquete: {project_dir}/dist/")
    print(f"- Ejecutable: {project_dir}/dist/nueva-biblioteca")
    return 0

if __name__ == "__main__":
    sys.exit(main())
