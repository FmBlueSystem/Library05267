#!/usr/bin/env python3
"""
Script de entrada para Nueva Biblioteca (GUI)
===========================================

Script que mantiene la aplicación abierta.
"""

import sys
import signal
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

def signal_handler(sig, frame):
    """Maneja la señal de interrupción."""
    print('\nCerrando aplicación...')
    sys.exit(0)

if __name__ == "__main__":
    # Configurar manejo de señales
    signal.signal(signal.SIGINT, signal_handler)
    
    from nueva_biblioteca.main import Application
    
    # Crear aplicación
    app = Application(sys.argv)
    
    # Ejecutar loop de eventos
    try:
        sys.exit(app.exec())
    except KeyboardInterrupt:
        print('\nCerrando aplicación...')
        sys.exit(0) 