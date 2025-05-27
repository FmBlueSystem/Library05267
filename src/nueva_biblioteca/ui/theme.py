#!/usr/bin/env python3
"""
Material Design 3 - Nueva Biblioteca
==============================

Sistema de temas y estilos basado en Material Design 3.
"""

from typing import ClassVar

from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication, QWidget


class MD3ColorScheme:
    """
    Esquema de colores Material Design 3.
    
    Basado en:
    https://m3.material.io/styles/color/the-color-system/color-roles
    """
    
    # Primary colors - Azul moderno
    PRIMARY = "#1976D2"
    ON_PRIMARY = "#FFFFFF"
    PRIMARY_CONTAINER = "#E3F2FD"
    ON_PRIMARY_CONTAINER = "#0D47A1"
    
    # Secondary colors - Verde complementario
    SECONDARY = "#388E3C"
    ON_SECONDARY = "#FFFFFF"
    SECONDARY_CONTAINER = "#E8F5E8"
    ON_SECONDARY_CONTAINER = "#1B5E20"
    
    # Tertiary colors - Naranja de acento
    TERTIARY = "#FF9800"
    ON_TERTIARY = "#FFFFFF"
    TERTIARY_CONTAINER = "#FFF3E0"
    ON_TERTIARY_CONTAINER = "#E65100"
    
    # Error colors
    ERROR = "#B3261E"
    ON_ERROR = "#FFFFFF"
    ERROR_CONTAINER = "#F9DEDC"
    ON_ERROR_CONTAINER = "#410E0B"
    
    # Background colors
    BACKGROUND = "#FFFBFE"
    ON_BACKGROUND = "#1C1B1F"
    SURFACE = "#FFFBFE"
    ON_SURFACE = "#1C1B1F"
    
    # Surface colors
    SURFACE_VARIANT = "#E7E0EC"
    ON_SURFACE_VARIANT = "#49454F"
    OUTLINE = "#79747E"
    OUTLINE_VARIANT = "#CAC4D0"
    
    # State layers
    HOVER_STATE_LAYER = "#1F000000"  # 12% black
    FOCUS_STATE_LAYER = "#33000000"  # 20% black
    PRESSED_STATE_LAYER = "#14000000"  # 8% black
    DRAGGED_STATE_LAYER = "#29000000"  # 16% black

class MD3Elevation:
    """Niveles de elevación Material Design 3."""
    
    LEVEL_0 = "0px 0px 0px 0px rgba(0, 0, 0, 0.2)"
    LEVEL_1 = "0px 1px 3px 1px rgba(0, 0, 0, 0.15)"
    LEVEL_2 = "0px 2px 6px 2px rgba(0, 0, 0, 0.15)"
    LEVEL_3 = "0px 4px 8px 3px rgba(0, 0, 0, 0.15)"
    LEVEL_4 = "0px 6px 10px 4px rgba(0, 0, 0, 0.15)"
    LEVEL_5 = "0px 8px 12px 6px rgba(0, 0, 0, 0.15)"

class MD3Typography:
    """Tipografía Material Design 3."""
    
    DISPLAY_LARGE = QFont("Roboto", 57, QFont.Weight.Normal)
    DISPLAY_MEDIUM = QFont("Roboto", 45, QFont.Weight.Normal)
    DISPLAY_SMALL = QFont("Roboto", 36, QFont.Weight.Normal)
    
    HEADLINE_LARGE = QFont("Roboto", 32, QFont.Weight.Normal)
    HEADLINE_MEDIUM = QFont("Roboto", 28, QFont.Weight.Normal)
    HEADLINE_SMALL = QFont("Roboto", 24, QFont.Weight.Normal)
    
    TITLE_LARGE = QFont("Roboto", 22, QFont.Weight.Medium)
    TITLE_MEDIUM = QFont("Roboto", 16, QFont.Weight.Medium)
    TITLE_SMALL = QFont("Roboto", 14, QFont.Weight.Medium)
    
    LABEL_LARGE = QFont("Roboto", 14, QFont.Weight.Medium)
    LABEL_MEDIUM = QFont("Roboto", 12, QFont.Weight.Medium)
    LABEL_SMALL = QFont("Roboto", 11, QFont.Weight.Medium)
    
    BODY_LARGE = QFont("Roboto", 16, QFont.Weight.Normal)
    BODY_MEDIUM = QFont("Roboto", 14, QFont.Weight.Normal)
    BODY_SMALL = QFont("Roboto", 12, QFont.Weight.Normal)

class MD3Shapes:
    """
    Formas y bordes Material Design 3.
    
    Los valores son strings CSS para bordes.
    """
    
    # Corner styles
    NONE = "0px"
    EXTRA_SMALL = "4px"
    SMALL = "8px"
    MEDIUM = "12px"
    LARGE = "16px"
    EXTRA_LARGE = "28px"
    FULL = "9999px"
    
    # Shape families
    ROUNDED_FAMILY: ClassVar[dict[str, str]] = {
        "extra_small": EXTRA_SMALL,
        "small": SMALL,
        "medium": MEDIUM,
        "large": LARGE,
        "extra_large": EXTRA_LARGE,
    }
    
    CUT_FAMILY: ClassVar[dict[str, str]] = {
        "extra_small": "2px",
        "small": "4px",
        "medium": "8px",
        "large": "12px",
        "extra_large": "16px",
    }

class MD3Theme:
    """
    Tema Material Design 3.
    
    Configura la apariencia global de la aplicación siguiendo
    las guías de Material Design 3.
    """
    
    def __init__(self):
        """Inicializa el tema con valores por defecto."""
        self.colors = MD3ColorScheme()
        self.elevation = MD3Elevation()
        self.typography = MD3Typography()
        self.shapes = MD3Shapes()
    
    def apply_to_widget(self, widget: QWidget) -> None:
        """
        Aplica el tema a un widget.
        
        Args:
            widget: Widget a estilizar
        """
        # Paleta de colores
        palette = widget.palette()
        
        # Colores base
        palette.setColor(QPalette.ColorRole.Window, QColor(self.colors.BACKGROUND))
        palette.setColor(
            QPalette.ColorRole.WindowText, QColor(self.colors.ON_BACKGROUND)
        )
        palette.setColor(QPalette.ColorRole.Base, QColor(self.colors.SURFACE))
        palette.setColor(QPalette.ColorRole.Text, QColor(self.colors.ON_SURFACE))
        
        # Colores de estado
        palette.setColor(QPalette.ColorRole.Button, QColor(self.colors.PRIMARY))
        palette.setColor(QPalette.ColorRole.ButtonText, QColor(self.colors.ON_PRIMARY))
        palette.setColor(QPalette.ColorRole.Highlight, QColor(self.colors.PRIMARY))
        palette.setColor(
            QPalette.ColorRole.HighlightedText, QColor(self.colors.ON_PRIMARY)
        )
        
        widget.setPalette(palette)
        
        # Tipografía por defecto
        widget.setFont(self.typography.BODY_MEDIUM)
    
    def apply_to_application(self) -> None:
        """Aplica el tema a toda la aplicación."""
        app = QApplication.instance()
        if app:
            self.apply_to_widget(app)
            
            # Stylesheet global
            app.setStyleSheet(f"""
                /* Botones */
                QPushButton {{
                    background-color: {self.colors.PRIMARY};
                    color: {self.colors.ON_PRIMARY};
                    border: none;
                    border-radius: {self.shapes.SMALL};
                    padding: 8px 16px;
                    font-family: Roboto;
                }}
                
                QPushButton:hover {{
                    background-color: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 {self.colors.PRIMARY},
                        stop:1 {self.colors.HOVER_STATE_LAYER}
                    );
                }}
                
                QPushButton:pressed {{
                    background-color: qlineargradient(
                        x1:0, y1:0, x2:0, y2:1,
                        stop:0 {self.colors.PRIMARY},
                        stop:1 {self.colors.PRESSED_STATE_LAYER}
                    );
                }}
                
                /* Campos de texto */
                QLineEdit {{
                    background-color: {self.colors.SURFACE};
                    color: {self.colors.ON_SURFACE};
                    border: 1px solid {self.colors.OUTLINE};
                    border-radius: {self.shapes.SMALL};
                    padding: 8px;
                }}
                
                QLineEdit:focus {{
                    border: 2px solid {self.colors.PRIMARY};
                }}
                
                /* Listas y tablas */
                QTableView {{
                    background-color: {self.colors.SURFACE};
                    color: {self.colors.ON_SURFACE};
                    gridline-color: {self.colors.OUTLINE_VARIANT};
                    border: none;
                }}
                
                QTableView::item:selected {{
                    background-color: {self.colors.PRIMARY_CONTAINER};
                    color: {self.colors.ON_PRIMARY_CONTAINER};
                }}
                
                /* Barras de progreso */
                QProgressBar {{
                    background-color: {self.colors.SURFACE_VARIANT};
                    border: none;
                    border-radius: {self.shapes.FULL};
                    height: 4px;
                }}
                
                QProgressBar::chunk {{
                    background-color: {self.colors.PRIMARY};
                    border-radius: {self.shapes.FULL};
                }}
                
                /* Pestañas */
                QTabWidget::pane {{
                    border: 1px solid {self.colors.OUTLINE_VARIANT};
                    border-radius: {self.shapes.SMALL};
                }}
                
                QTabBar::tab {{
                    background-color: {self.colors.SURFACE};
                    color: {self.colors.ON_SURFACE};
                    border: none;
                    padding: 8px 16px;
                }}
                
                QTabBar::tab:selected {{
                    color: {self.colors.PRIMARY};
                    border-bottom: 2px solid {self.colors.PRIMARY};
                }}
                
                /* Diálogos */
                QDialog {{
                    background-color: {self.colors.SURFACE};
                    border-radius: {self.shapes.MEDIUM};
                }}
            """)

# Instancia global
_theme: MD3Theme | None = None

def get_theme() -> MD3Theme:
    """Obtiene la instancia global del tema."""
    global _theme
    if _theme is None:
        _theme = MD3Theme()
    return _theme
