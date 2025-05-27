#!/usr/bin/env python3
"""
Widgets Material Design 3 - Nueva Biblioteca
=====================================

Widgets personalizados que implementan los componentes
de Material Design 3.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QIcon
from PyQt6.QtWidgets import (
    QFrame,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from nueva_biblioteca.ui.theme import get_theme


class MD3Button(QPushButton):
    """Botón con estilo Material Design 3."""
    
    def __init__(
        self,
        text: str = "",
        variant: str = "filled",  # filled, outlined, text
        icon: str | None = None,
        parent: QWidget | None = None
    ):
        """
        Inicializa el botón.
        
        Args:
            text: Texto del botón
            variant: Estilo del botón
            icon: Nombre del icono
            parent: Widget padre
        """
        super().__init__(text, parent)
        
        self.theme = get_theme()
        self.variant = variant
        
        # Configurar estilo base
        self.setMinimumHeight(40)
        
        # Aplicar variante
        if variant == "outlined":
            self.setProperty("class", "outlined")
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.theme.colors.PRIMARY};
                    border: 1px solid {self.theme.colors.OUTLINE};
                    border-radius: {self.theme.shapes.SMALL};
                    padding: 8px 16px;
                }}
                
                QPushButton:hover {{
                    background-color: {self.theme.colors.HOVER_STATE_LAYER};
                }}
                
                QPushButton:pressed {{
                    background-color: {self.theme.colors.PRESSED_STATE_LAYER};
                }}
            """)
            
        elif variant == "text":
            self.setProperty("class", "text")
            self.setStyleSheet(f"""
                QPushButton {{
                    background-color: transparent;
                    color: {self.theme.colors.PRIMARY};
                    border: none;
                    padding: 8px 16px;
                }}
                
                QPushButton:hover {{
                    background-color: {self.theme.colors.HOVER_STATE_LAYER};
                }}
                
                QPushButton:pressed {{
                    background-color: {self.theme.colors.PRESSED_STATE_LAYER};
                }}
            """)
        
        # Agregar icono si se especifica
        if icon:
            self.setIcon(QIcon(icon))

class MD3Card(QFrame):
    """Tarjeta con estilo Material Design 3."""
    
    def __init__(
        self,
        parent: QWidget | None = None,
        elevation: int = 1
    ):
        """
        Inicializa la tarjeta.
        
        Args:
            parent: Widget padre
            elevation: Nivel de elevación (0-5)
        """
        super().__init__(parent)
        
        self.theme = get_theme()
        
        # Configurar estilo base
        self.setFrameStyle(QFrame.Shape.NoFrame)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.colors.SURFACE};
                border-radius: {self.theme.shapes.MEDIUM};
            }}
        """)
        
        # Agregar sombra
        if elevation > 0:
            shadow = QGraphicsDropShadowEffect()
            shadow.setBlurRadius(elevation * 4)
            shadow.setXOffset(0)
            shadow.setYOffset(elevation * 2)
            shadow.setColor(QColor(0, 0, 0, 50))
            self.setGraphicsEffect(shadow)

class MD3TextField(QLineEdit):
    """Campo de texto con estilo Material Design 3."""
    
    def __init__(
        self,
        parent: QWidget | None = None,
        placeholder: str = "",
        label: str = "",
        helper_text: str = "",
        error_text: str = ""
    ):
        """
        Inicializa el campo de texto.
        
        Args:
            parent: Widget padre
            placeholder: Texto de placeholder
            label: Etiqueta flotante
            helper_text: Texto de ayuda
            error_text: Texto de error
        """
        super().__init__(parent)
        
        self.theme = get_theme()
        self._label = label
        self._helper_text = helper_text
        self._error_text = error_text
        self._has_error = False
        
        # Container principal
        container = QWidget(parent)
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 8, 0, 8)
        
        # Etiqueta flotante
        if label:
            self.label = QLabel(label)
            self.label.setFont(self.theme.typography.BODY_SMALL)
            layout.addWidget(self.label)
        
        # Campo de texto
        layout.addWidget(self)
        self.setPlaceholderText(placeholder)
        
        # Texto de ayuda/error
        if helper_text or error_text:
            self.help_label = QLabel(helper_text)
            self.help_label.setFont(self.theme.typography.BODY_SMALL)
            layout.addWidget(self.help_label)
        
        # Estilo base
        self.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme.colors.SURFACE};
                color: {self.theme.colors.ON_SURFACE};
                border: 1px solid {self.theme.colors.OUTLINE};
                border-radius: {self.theme.shapes.SMALL};
                padding: 12px;
                font-family: Roboto;
            }}
            
            QLineEdit:focus {{
                border: 2px solid {self.theme.colors.PRIMARY};
            }}
            
            QLineEdit:disabled {{
                background-color: {self.theme.colors.SURFACE_VARIANT};
                border-color: {self.theme.colors.OUTLINE_VARIANT};
            }}
        """)
    
    def set_error(self, error: bool = True) -> None:
        """
        Establece el estado de error.
        
        Args:
            error: Si mostrar error
        """
        self._has_error = error
        
        if error:
            self.setStyleSheet(f"""
                QLineEdit {{
                    border: 2px solid {self.theme.colors.ERROR};
                }}
                
                QLineEdit:focus {{
                    border: 2px solid {self.theme.colors.ERROR};
                }}
            """)
            
            if hasattr(self, 'help_label'):
                self.help_label.setText(self._error_text)
                self.help_label.setStyleSheet(f"""
                    color: {self.theme.colors.ERROR};
                """)
        else:
            self.setStyleSheet("")
            if hasattr(self, 'help_label'):
                self.help_label.setText(self._helper_text)
                self.help_label.setStyleSheet("")

class MD3Chip(QFrame):
    """Chip con estilo Material Design 3."""
    
    clicked = pyqtSignal()
    
    def __init__(
        self,
        text: str,
        parent: QWidget | None = None,
        selected: bool = False,
        removable: bool = False,
        icon: str | None = None
    ):
        """
        Inicializa el chip.
        
        Args:
            text: Texto del chip
            parent: Widget padre
            selected: Si está seleccionado
            removable: Si se puede eliminar
            icon: Nombre del icono
        """
        super().__init__(parent)
        
        self.theme = get_theme()
        self._selected = selected
        
        # Layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(4)
        
        # Icono
        if icon:
            icon_label = QLabel()
            icon_label.setPixmap(QIcon(icon).pixmap(16, 16))
            layout.addWidget(icon_label)
        
        # Texto
        self.label = QLabel(text)
        self.label.setFont(self.theme.typography.LABEL_LARGE)
        layout.addWidget(self.label)
        
        # Botón de eliminar
        if removable:
            close_btn = QPushButton("x")
            close_btn.setFixedSize(16, 16)
            close_btn.clicked.connect(self.remove)
            layout.addWidget(close_btn)
        
        # Estilo base
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.colors.SURFACE_VARIANT};
                color: {self.theme.colors.ON_SURFACE_VARIANT};
                border-radius: {self.theme.shapes.SMALL};
            }}
            
            QFrame:hover {{
                background-color: {self.theme.colors.HOVER_STATE_LAYER};
            }}
        """)
        
        if selected:
            self.set_selected(True)
    
    def set_selected(self, selected: bool = True) -> None:
        """
        Establece el estado de selección.
        
        Args:
            selected: Si está seleccionado
        """
        self._selected = selected
        
        if selected:
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: {self.theme.colors.SECONDARY_CONTAINER};
                    color: {self.theme.colors.ON_SECONDARY_CONTAINER};
                    border-radius: {self.theme.shapes.SMALL};
                }}
            """)
        else:
            self.setStyleSheet("")
    
    def mousePressEvent(self, event):
        """Maneja el click."""
        self.clicked.emit()
    
    def remove(self):
        """Elimina el chip."""
        self.deleteLater()

class MD3NavigationRail(QFrame):
    """Barra de navegación vertical con estilo Material Design 3."""
    
    current_changed = pyqtSignal(int)  # Índice seleccionado
    
    def __init__(
        self,
        parent: QWidget | None = None,
        fab_text: str | None = None  # Texto del FAB
    ):
        """
        Inicializa la barra de navegación.
        
        Args:
            parent: Widget padre
            fab_text: Texto del FAB o None
        """
        super().__init__(parent)
        
        self.theme = get_theme()
        self.items = []  # [(icon, text), ...]
        self._current = 0
        
        # Layout principal
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(8, 8, 8, 8)
        self.layout.setSpacing(4)
        
        # FAB
        if fab_text:
            fab = MD3Button(fab_text, parent=self)
            fab.setFixedSize(56, 56)
            self.layout.addWidget(fab)
        
        # Estilo base mejorado
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme.colors.SURFACE};
                border-right: 2px solid {self.theme.colors.PRIMARY_CONTAINER};
                border-radius: 0px 12px 12px 0px;
            }}
        """)
        
        self.setFixedWidth(80)
    
    def add_item(self, icon: str, text: str) -> None:
        """
        Agrega un ítem a la barra.
        
        Args:
            icon: Nombre del icono
            text: Texto del ítem
        """
        # Contenedor del ítem
        item = QWidget(self)
        item_layout = QVBoxLayout(item)
        item_layout.setContentsMargins(0, 8, 0, 8)
        
        # Icono
        icon_label = QLabel(item)
        icon_label.setPixmap(QIcon(icon).pixmap(24, 24))
        item_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Texto
        text_label = QLabel(text, item)
        text_label.setFont(self.theme.typography.LABEL_MEDIUM)
        text_label.setWordWrap(True)
        text_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        item_layout.addWidget(text_label)
        
        # Almacenar y agregar al layout
        index = len(self.items)
        self.items.append((icon_label, text_label))
        self.layout.addWidget(item)
        
        # Conectar click
        item.mousePressEvent = lambda e: self.set_current(index)
        
        # Actualizar estilos
        self._update_styles()
    
    def set_current(self, index: int) -> None:
        """
        Establece el ítem actual.
        
        Args:
            index: Índice del ítem
        """
        if 0 <= index < len(self.items):
            self._current = index
            self._update_styles()
            self.current_changed.emit(index)
    
    def _update_styles(self) -> None:
        """Actualiza los estilos de los ítems."""
        for i, (icon, text) in enumerate(self.items):
            if i == self._current:
                icon.setStyleSheet(f"""
                    QLabel {{
                        color: {self.theme.colors.PRIMARY};
                    }}
                """)
                text.setStyleSheet(f"""
                    QLabel {{
                        color: {self.theme.colors.PRIMARY};
                    }}
                """)
            else:
                icon.setStyleSheet(f"""
                    QLabel {{
                        color: {self.theme.colors.ON_SURFACE_VARIANT};
                    }}
                """)
                text.setStyleSheet(f"""
                    QLabel {{
                        color: {self.theme.colors.ON_SURFACE_VARIANT};
                    }}
                """)
