#!/usr/bin/env python3
"""
Nueva Biblioteca
=============

Aplicación de biblioteca musical con Material Design 3
y características avanzadas.
"""

import os
import sys
from pathlib import Path

from PyQt6.QtCore import QSettings
from PyQt6.QtGui import QFontDatabase
from PyQt6.QtWidgets import QApplication

from .data.repository import get_repository
from .ui.main_window import MainWindow
from .ui.theme_manager import get_theme_manager
from .utils.config import get_config
from .utils.logger import get_logger

logger = get_logger(__name__)

class Application(QApplication):
    """Aplicación principal."""
    
    def __init__(self, argv):
        """
        Inicializa la aplicación.
        
        Args:
            argv: Argumentos de línea de comandos
        """
        super().__init__(argv)
        
        self.setOrganizationName("FmBlueSystem")
        self.setOrganizationDomain("fmbluesystem.com")
        self.setApplicationName("Nueva Biblioteca")
        
        self._setup_app()
    
    def _setup_app(self) -> None:
        """Configura la aplicación."""
        # Configuración
        get_config()
        self.settings = QSettings()
        
        # Cargar fuentes
        self._load_fonts()
        
        # Configurar tema
        self.theme_manager = get_theme_manager()
        
        # Aplicar modo oscuro si estaba activo
        if self.settings.value("dark_mode", False, type=bool):
            self.theme_manager.toggle_theme()
        
        # Obtener información de pantalla
        screen_info = self.theme_manager.get_screen_info()
        logger.info(f"Screen info: {screen_info}")
        
        # Optimizar dimensiones
        size = self.primaryScreen().size()
        self.optimal_sizes = self.theme_manager.optimize_layout(
            size.width(),
            size.height()
        )
        
        # Repositorio
        self.repository = get_repository()
        
        # Ventana principal
        self.main_window = MainWindow(self.repository)
        self.main_window.resize(
            int(size.width() * 0.8),
            int(size.height() * 0.8)
        )
        
        # Asegurar que la ventana se muestre
        self.main_window.show()
        self.main_window.raise_()
        self.main_window.activateWindow()
        
        logger.info(f"Ventana principal mostrada - Tamaño: {self.main_window.size()}")
        logger.info(f"Ventana visible: {self.main_window.isVisible()}")
    
    def _load_fonts(self) -> None:
        """Carga las fuentes necesarias."""
        fonts_dir = Path(__file__).parent / "assets" / "fonts"
        
        for font_file in fonts_dir.glob("*.ttf"):
            font_id = QFontDatabase.addApplicationFont(str(font_file))
            if font_id < 0:
                logger.error(f"Error loading font: {font_file}")
                continue
            
            font_families = QFontDatabase.applicationFontFamilies(font_id)
            logger.debug(f"Loaded font family: {font_families}")
    
    def exec(self) -> int:
        """
        Ejecuta la aplicación.
        
        Returns:
            Código de salida
        """
        try:
            return super().exec()
        except Exception as e:
            logger.error(f"Error fatal: {e}")
            return 1
        finally:
            # Guardar configuración
            self.settings.setValue(
                "dark_mode",
                self.theme_manager._is_dark
            )
            self.settings.sync()

def main() -> int:
    """
    Punto de entrada principal.
    
    Returns:
        Código de salida
    """
    # Configurar atributos de HiDPI
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"
    # PyQt6 maneja automáticamente High DPI
    
    # Crear y ejecutar aplicación
    app = Application(sys.argv)
    return app.exec()

if __name__ == "__main__":
    sys.exit(main())
