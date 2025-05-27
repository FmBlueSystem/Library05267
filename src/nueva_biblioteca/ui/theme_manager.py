#!/usr/bin/env python3
"""
Gestor de Temas - Nueva Biblioteca
===========================

Sistema de gestión de temas con soporte para HiDPI, modo claro/oscuro
y animaciones Material Design 3.
"""

from typing import Any

from PyQt6.QtCore import QEasingCurve, QObject, QPoint, QPropertyAnimation, QRect
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import QApplication

from .theme import get_theme


class ThemeManager(QObject):
    """Gestor avanzado de temas y estilo."""
    
    def __init__(self):
        """Inicializa el gestor de temas."""
        super().__init__()
        
        self.theme = get_theme()
        self._dpi_scale = self._calculate_dpi_scale()
        self._animations: dict[str, QPropertyAnimation] = {}
        self._is_dark = False
    
    def _calculate_dpi_scale(self) -> float:
        """
        Calcula el factor de escala DPI.
        
        Returns:
            Factor de escala (1.0 = 96 DPI)
        """
        app = QApplication.instance()
        if not app:
            return 1.0
            
        screen = app.primaryScreen()
        if not screen:
            return 1.0
            
        # Factor de escala basado en DPI físico
        dpi = screen.physicalDotsPerInch()
        base_dpi = 96.0  # DPI base en Windows
        
        return max(1.0, dpi / base_dpi)
    
    def scale_size(self, size: int) -> int:
        """
        Escala un tamaño según DPI.
        
        Args:
            size: Tamaño original
            
        Returns:
            Tamaño escalado
        """
        return int(size * self._dpi_scale)
    
    def get_screen_info(self) -> dict[str, Any]:
        """
        Obtiene información de la pantalla.
        
        Returns:
            Diccionario con información
        """
        app = QApplication.instance()
        screen = app.primaryScreen()
        
        return {
            "resolution": (
                screen.size().width(),
                screen.size().height()
            ),
            "physical_size": (
                screen.physicalSize().width() / 25.4,  # mm a pulgadas
                screen.physicalSize().height() / 25.4
            ),
            "dpi": (
                screen.physicalDotsPerInchX(),
                screen.physicalDotsPerInchY()
            ),
            "scale_factor": self._dpi_scale,
            "density": screen.devicePixelRatio()
        }
    
    def optimize_layout(self, width: int, height: int) -> dict[str, Any]:
        """
        Calcula dimensiones óptimas para el layout.
        
        Args:
            width: Ancho disponible
            height: Alto disponible
            
        Returns:
            Dimensiones recomendadas
        """
        # Escalar dimensiones base
        nav_width = self.scale_size(80)
        details_width = self.scale_size(300)
        min_table_width = self.scale_size(600)
        
        # Calcular proporciones
        available_width = width - nav_width
        table_width = max(
            min_table_width,
            available_width - details_width
        )
        
        return {
            "navigation_width": nav_width,
            "table_width": table_width,
            "details_width": details_width,
            "controls_height": self.scale_size(100),
            "search_height": self.scale_size(60)
        }
    
    def create_animation(
        self,
        target: QObject,
        property_name: str,
        start_value: Any,
        end_value: Any,
        duration: int = 200,
        easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic
    ) -> QPropertyAnimation:
        """
        Crea una animación MD3.
        
        Args:
            target: Objeto a animar
            property_name: Propiedad a animar
            start_value: Valor inicial
            end_value: Valor final
            duration: Duración en ms
            easing: Tipo de easing
            
        Returns:
            Animación configurada
        """
        animation = QPropertyAnimation(
            target,
            property_name.encode()
        )
        
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setDuration(duration)
        animation.setEasingCurve(easing)
        
        # Almacenar referencia
        key = f"{id(target)}_{property_name}"
        self._animations[key] = animation
        
        return animation
    
    def add_ripple(
        self,
        widget: QObject,
        pos: QPoint,
        color: QColor | None = None,
        duration: int = 400
    ) -> None:
        """
        Añade efecto ripple a un widget.
        
        Args:
            widget: Widget objetivo
            pos: Posición del click
            color: Color del ripple
            duration: Duración en ms
        """
        if not color:
            color = QColor(self.theme.colors.PRIMARY)
            color.setAlpha(32)
        
        # Crear y configurar animación de ripple
        ripple = QPropertyAnimation(widget, b"ripple")
        ripple.setStartValue(QRect(pos.x(), pos.y(), 0, 0))
        ripple.setEndValue(QRect(
            pos.x() - widget.width(),
            pos.y() - widget.height(),
            widget.width() * 2,
            widget.height() * 2
        ))
        ripple.setDuration(duration)
        ripple.setEasingCurve(QEasingCurve.Type.OutQuad)
        
        # Almacenar y ejecutar
        key = f"ripple_{id(widget)}_{pos.x()}_{pos.y()}"
        self._animations[key] = ripple
        ripple.start()
    
    def toggle_theme(self) -> None:
        """Alterna entre tema claro y oscuro."""
        self._is_dark = not self._is_dark
        
        if self._is_dark:
            # Colores modo oscuro
            colors = {
                'BACKGROUND': '#1C1B1F',
                'ON_BACKGROUND': '#E6E1E5',
                'SURFACE': '#1C1B1F',
                'ON_SURFACE': '#E6E1E5',
                'SURFACE_VARIANT': '#49454F',
                'ON_SURFACE_VARIANT': '#CAC4D0',
                'PRIMARY': '#D0BCFF',
                'ON_PRIMARY': '#381E72',
                'PRIMARY_CONTAINER': '#4F378B',
                'ON_PRIMARY_CONTAINER': '#EADDFF',
                'SECONDARY': '#CCC2DC',
                'ON_SECONDARY': '#332D41',
                'SECONDARY_CONTAINER': '#4A4458',
                'ON_SECONDARY_CONTAINER': '#E8DEF8',
                'ERROR': '#F2B8B5',
                'ON_ERROR': '#601410',
                'ERROR_CONTAINER': '#8C1D18',
                'ON_ERROR_CONTAINER': '#F9DEDC'
            }
        else:
            # Restaurar colores claros por defecto
            colors = {
                'BACKGROUND': '#FFFBFE',
                'ON_BACKGROUND': '#1C1B1F',
                'SURFACE': '#FFFBFE',
                'ON_SURFACE': '#1C1B1F',
                'SURFACE_VARIANT': '#E7E0EC',
                'ON_SURFACE_VARIANT': '#49454F',
                'PRIMARY': '#6750A4',
                'ON_PRIMARY': '#FFFFFF',
                'PRIMARY_CONTAINER': '#EADDFF',
                'ON_PRIMARY_CONTAINER': '#21005E',
                'SECONDARY': '#625B71',
                'ON_SECONDARY': '#FFFFFF',
                'SECONDARY_CONTAINER': '#E8DEF8',
                'ON_SECONDARY_CONTAINER': '#1E192B',
                'ERROR': '#B3261E',
                'ON_ERROR': '#FFFFFF',
                'ERROR_CONTAINER': '#F9DEDC',
                'ON_ERROR_CONTAINER': '#410E0B'
            }
        
        # Actualizar colores del tema
        for name, value in colors.items():
            setattr(self.theme.colors, name, value)
        
        # Aplicar cambios
        self.theme.apply_to_application()

# Instancia global
_manager: ThemeManager | None = None

def get_theme_manager() -> ThemeManager:
    """Obtiene la instancia global del gestor de temas."""
    global _manager
    if _manager is None:
        _manager = ThemeManager()
    return _manager
