#!/usr/bin/env python3
"""
Widget Base - Nueva Biblioteca
========================

Clase base para widgets con soporte para Material Design 3,
animaciones y efectos.
"""

from PyQt6.QtCore import QEasingCurve, QPoint, QPropertyAnimation, Qt, pyqtProperty
from PyQt6.QtGui import QColor, QPainter, QPaintEvent, QResizeEvent
from PyQt6.QtWidgets import QWidget

from nueva_biblioteca.ui.theme_manager import get_theme_manager


class MD3Widget(QWidget):
    """Widget base con soporte para Material Design 3."""
    
    def __init__(self, parent: QWidget | None = None):
        """
        Inicializa el widget.
        
        Args:
            parent: Widget padre
        """
        super().__init__(parent)
        
        self.theme_manager = get_theme_manager()
        self.setFont(self.theme_manager.theme.typography.BODY_MEDIUM)
        
        # Estado de ripple
        self._ripple_pos = QPoint()
        self._ripple_radius = 0
        self._ripple_opacity = 0.0
        self._ripple_animation: QPropertyAnimation | None = None
        self._fade_animation: QPropertyAnimation | None = None
        
        # Sombra y elevación
        self._elevation = 0
        self._elevation_animation: QPropertyAnimation | None = None
        
        # Tooltips mejorados
        self.setProperty("tooltip_style", "md3")
        
        # Habilitar seguimiento del mouse
        self.setMouseTracking(True)
    
    def mousePressEvent(self, event) -> None:
        """
        Maneja el click del mouse.
        
        Args:
            event: Evento del mouse
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_ripple(event.pos())
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event) -> None:
        """
        Maneja la liberación del mouse.
        
        Args:
            event: Evento del mouse
        """
        if event.button() == Qt.MouseButton.LeftButton:
            self.stop_ripple()
        super().mouseReleaseEvent(event)
    
    def enterEvent(self, event) -> None:
        """
        Maneja la entrada del mouse.
        
        Args:
            event: Evento del mouse
        """
        self.animate_elevation(2)
        super().enterEvent(event)
    
    def leaveEvent(self, event) -> None:
        """
        Maneja la salida del mouse.
        
        Args:
            event: Evento del mouse
        """
        self.animate_elevation(0)
        super().leaveEvent(event)
    
    def paintEvent(self, event: QPaintEvent) -> None:
        """
        Pinta el widget.
        
        Args:
            event: Evento de pintado
        """
        super().paintEvent(event)
        
        # Dibujar ripple
        if self._ripple_opacity > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Color del ripple
            color = QColor(self.theme_manager.theme.colors.PRIMARY)
            color.setAlphaF(self._ripple_opacity * 0.2)
            
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            
            painter.drawEllipse(
                self._ripple_pos,
                self._ripple_radius,
                self._ripple_radius
            )
    
    def resizeEvent(self, event: QResizeEvent) -> None:
        """
        Maneja el cambio de tamaño.
        
        Args:
            event: Evento de resize
        """
        super().resizeEvent(event)
        self._update_corner_radius()
    
    def _update_corner_radius(self) -> None:
        """Actualiza el radio de las esquinas según el tamaño."""
        size = min(self.width(), self.height())
        
        if size <= 40:
            radius = self.theme_manager.theme.shapes.EXTRA_SMALL
        elif size <= 80:
            radius = self.theme_manager.theme.shapes.SMALL
        elif size <= 120:
            radius = self.theme_manager.theme.shapes.MEDIUM
        else:
            radius = self.theme_manager.theme.shapes.LARGE
        
        self.setStyleSheet(f"""
            {self.__class__.__name__} {{
                border-radius: {radius};
            }}
        """)
    
    # Propiedades animables
    @pyqtProperty(float)
    def ripple_radius(self) -> float:
        """Radio del efecto ripple."""
        return self._ripple_radius
    
    @ripple_radius.setter
    def ripple_radius(self, radius: float) -> None:
        """
        Establece el radio del ripple.
        
        Args:
            radius: Nuevo radio
        """
        self._ripple_radius = radius
        self.update()
    
    @pyqtProperty(float)
    def ripple_opacity(self) -> float:
        """Opacidad del efecto ripple."""
        return self._ripple_opacity
    
    @ripple_opacity.setter
    def ripple_opacity(self, opacity: float) -> None:
        """
        Establece la opacidad del ripple.
        
        Args:
            opacity: Nueva opacidad
        """
        self._ripple_opacity = opacity
        self.update()
    
    @pyqtProperty(int)
    def elevation(self) -> int:
        """Nivel de elevación."""
        return self._elevation
    
    @elevation.setter
    def elevation(self, level: int) -> None:
        """
        Establece el nivel de elevación.
        
        Args:
            level: Nuevo nivel
        """
        self._elevation = level
        # Actualizar sombra según nivel
        shadow = self.theme_manager.theme.get_elevation_shadow(level)
        self.setGraphicsEffect(shadow)
    
    def start_ripple(self, pos: QPoint) -> None:
        """
        Inicia el efecto ripple.
        
        Args:
            pos: Posición del click
        """
        self._ripple_pos = pos
        
        # Calcular radio máximo
        to_right = self.width() - pos.x()
        to_left = pos.x()
        to_bottom = self.height() - pos.y()
        to_top = pos.y()
        
        self._ripple_radius = (max(
            to_right**2 + to_bottom**2,
            to_right**2 + to_top**2,
            to_left**2 + to_bottom**2,
            to_left**2 + to_top**2
        ) ** 0.5)
        
        # Animar radio y opacidad
        self._ripple_animation = self.theme_manager.create_animation(
            self,
            "ripple_radius",
            0,
            self._ripple_radius,
            duration=400,
            easing=QEasingCurve.Type.OutQuad
        )
        
        opacity_anim = self.theme_manager.create_animation(
            self,
            "ripple_opacity",
            0.0,
            1.0,
            duration=200,
            easing=QEasingCurve.Type.OutCubic
        )
        
        self._ripple_animation.start()
        opacity_anim.start()
    
    def stop_ripple(self) -> None:
        """Detiene el efecto ripple."""
        if self._ripple_animation:
            self._ripple_animation.stop()
        
        # Animar desvanecimiento
        self._fade_animation = self.theme_manager.create_animation(
            self,
            "ripple_opacity",
            self._ripple_opacity,
            0.0,
            duration=200,
            easing=QEasingCurve.Type.OutCubic
        )
        self._fade_animation.start()
    
    def animate_elevation(self, level: int) -> None:
        """
        Anima el cambio de elevación.
        
        Args:
            level: Nivel objetivo
        """
        if self._elevation == level:
            return
        
        self._elevation_animation = self.theme_manager.create_animation(
            self,
            "elevation",
            self._elevation,
            level,
            duration=150,
            easing=QEasingCurve.Type.OutCubic
        )
        self._elevation_animation.start()
    
    def set_tooltip_rich(self, text: str) -> None:
        """
        Establece un tooltip con formato rico.
        
        Args:
            text: Texto del tooltip
        """
        self.setToolTip(f"""
            <div style='
                background-color: {self.theme_manager.theme.colors.SURFACE_VARIANT};
                color: {self.theme_manager.theme.colors.ON_SURFACE_VARIANT};
                padding: 8px 12px;
                border-radius: {self.theme_manager.theme.shapes.SMALL};
                font-family: Roboto;
                font-size: {self.theme_manager.scale_size(12)}px;
            '>
                {text}
            </div>
        """)
