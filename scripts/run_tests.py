#!/usr/bin/env python3
"""
Script para ejecutar tests de Nueva Biblioteca.

Este script ejecuta las pruebas unitarias y de integración
usando pytest, generando reportes de cobertura y resultados.
"""

from typing import List, Optional, Dict, Any
from pathlib import Path
import subprocess
import json
import sys
import os

def run_command(command: List[str], env: Optional[Dict[str, str]] = None) -> bool:
    """
    Ejecuta un comando del sistema.
    
    Args:
        command: Lista con el comando y sus argumentos
        env: Variables de entorno adicionales
        
    Returns:
        True si el comando fue exitoso
    """
    try:
        full_env = os.environ.copy()
        if env:
            full_env.update(env)
        
        subprocess.run(
            command,
            env=full_env,
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando {' '.join(command)}:", file=sys.stderr)
        print(f"Código de salida: {e.returncode}", file=sys.stderr)
        return False

def create_test_env() -> Dict[str, str]:
    """
    Crea variables de entorno para testing.
    
    Returns:
        Diccionario con variables de entorno
    """
    return {
        "NUEVA_BIBLIOTECA_ENV": "test",
        "NUEVA_BIBLIOTECA_CONFIG": "tests/data/test_config.json",
        "PYTHONPATH": str(Path(__file__).parent.parent)
    }

def setup_test_data(data_dir: Path) -> None:
    """
    Prepara datos de prueba.
    
    Args:
        data_dir: Directorio de datos
    """
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Configuración de prueba
    config = {
        "files": {
            "music_folder": str(data_dir / "music"),
            "supported_formats": [".mp3", ".flac", ".m4a"]
        },
        "database": {
            "path": str(data_dir / "test.db")
        },
        "logging": {
            "level": "DEBUG",
            "directory": str(data_dir / "logs")
        },
        "cache": {
            "directory": str(data_dir / "cache"),
            "max_size_mb": 100
        }
    }
    
    config_file = data_dir / "test_config.json"
    config_file.write_text(json.dumps(config, indent=2))
    
    # Crear directorios necesarios
    for path in [
        config["files"]["music_folder"],
        config["logging"]["directory"],
        config["cache"]["directory"]
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)

def run_tests(project_dir: Path, coverage: bool = True) -> bool:
    """
    Ejecuta las pruebas.
    
    Args:
        project_dir: Directorio del proyecto
        coverage: Si debe generar reporte de cobertura
        
    Returns:
        True si las pruebas pasaron
    """
    print("\n=== Ejecutando Tests ===")
    
    # Preparar comandos
    cmd = ["pytest"]
    
    if coverage:
        cmd.extend([
            "--cov=nueva_biblioteca",
            "--cov-report=term-missing",
            "--cov-report=html",
            "--cov-report=xml"
        ])
    
    cmd.extend([
        "-v",                    # Verbose
        "--tb=short",           # Traceback corto
        "-W", "ignore",         # Ignorar warnings
        "--color=yes",          # Colorear salida
        str(project_dir / "tests")
    ])
    
    # Crear entorno de prueba
    test_data = project_dir / "tests" / "data"
    setup_test_data(test_data)
    
    # Ejecutar tests
    return run_command(cmd, env=create_test_env())

def check_dependencies() -> bool:
    """
    Verifica dependencias de testing.
    
    Returns:
        True si todas las dependencias están instaladas
    """
    print("\nVerificando dependencias...")
    
    required = [
        "pytest",
        "pytest-cov",
        "pytest-mock",
        "pytest-asyncio"
    ]
    
    for package in required:
        try:
            __import__(package.replace("-", "_"))
            print(f"✓ {package}")
        except ImportError:
            print(f"✗ Falta {package}")
            return False
    
    return True

def main() -> int:
    """
    Función principal.
    
    Returns:
        0 si todo fue exitoso, otro valor en caso de error
    """
    project_dir = Path(__file__).parent.parent
    
    # Verificar dependencias
    if not check_dependencies():
        print("\n⚠ Instala las dependencias faltantes con:")
        print("pip install pytest pytest-cov pytest-mock pytest-asyncio")
        return 1
    
    # Ejecutar tests
    success = run_tests(project_dir)
    
    if success:
        print("\n✨ Todas las pruebas pasaron exitosamente")
        print("\nReportes generados:")
        print(f"- HTML: {project_dir}/htmlcov/index.html")
        print(f"- XML: {project_dir}/coverage.xml")
        return 0
    else:
        print("\n⚠ Algunas pruebas fallaron")
        return 1

if __name__ == "__main__":
    sys.exit(main())
