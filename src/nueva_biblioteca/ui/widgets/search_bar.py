#!/usr/bin/env python3
"""
Barra de Búsqueda - Nueva Biblioteca
==============================

Barra de búsqueda con estilo Material Design 3.
"""


from PyQt6.QtCore import QTimer, pyqtSignal
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QLineEdit, QWidget

from nueva_biblioteca.ui.theme import get_theme
from nueva_biblioteca.ui.widgets.md3_widgets import MD3Button


class SearchBar(QWidget):
    """Barra de búsqueda con estilo Material Design 3."""
    
    # Señales
    search_changed = pyqtSignal(str)  # Texto de búsqueda
    
    def __init__(self, parent: QWidget | None = None):
        """
        Inicializa la barra.
        
        Args:
            parent: Widget padre
        """
        super().__init__(parent)
        
        self.theme = get_theme()
        
        # Timer para debounce
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(300)  # 300ms
        self.timer.timeout.connect(self._emit_search)
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)
        
        # Icono de búsqueda
        search_icon = QLabel()
        search_icon.setPixmap(QIcon("icons/search.svg").pixmap(24, 24))
        search_icon.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.colors.ON_SURFACE_VARIANT};
            }}
        """)
        
        # Campo de búsqueda
        self.search_field = QLineEdit()
        self.search_field.setPlaceholderText("Buscar en biblioteca...")
        self.search_field.textChanged.connect(self._on_text_changed)
        self.search_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {self.theme.colors.SURFACE_VARIANT};
                color: {self.theme.colors.ON_SURFACE};
                border: none;
                border-radius: {self.theme.shapes.FULL};
                padding: 8px 16px;
                font-family: Roboto;
                font-size: 16px;
            }}
            
            QLineEdit:focus {{
                background-color: {self.theme.colors.SURFACE};
                border: 2px solid {self.theme.colors.PRIMARY};
            }}
            
            QLineEdit::placeholder {{
                color: {self.theme.colors.ON_SURFACE_VARIANT};
            }}
        """)
        
        # Botón limpiar
        self.clear_button = MD3Button(
            variant="text",
            icon="icons/clear.svg"
        )
        self.clear_button.setFixedSize(32, 32)
        self.clear_button.clicked.connect(self.clear)
        self.clear_button.hide()
        
        # Botón filtros
        self.filter_button = MD3Button(
            variant="outlined",
            icon="icons/filter.svg",
            text="Filtros"
        )
        self.filter_button.clicked.connect(self._show_filters)
        
        # Layout
        layout.addWidget(search_icon)
        layout.addWidget(self.search_field, stretch=1)
        layout.addWidget(self.clear_button)
        layout.addWidget(self.filter_button)
        
        # Estilo del widget
        self.setStyleSheet(f"""
            SearchBar {{
                background-color: {self.theme.colors.SURFACE_VARIANT};
                border-radius: {self.theme.shapes.FULL};
            }}
        """)
    
    def _on_text_changed(self, text: str) -> None:
        """
        Maneja cambios en el texto.
        
        Args:
            text: Nuevo texto
        """
        # Mostrar/ocultar botón limpiar
        self.clear_button.setVisible(bool(text))
        
        # Reiniciar timer
        self.timer.stop()
        self.timer.start()
    
    def _emit_search(self) -> None:
        """Emite el texto de búsqueda."""
        self.search_changed.emit(self.search_field.text())
    
    def _show_filters(self) -> None:
        """Muestra el menú de filtros."""
        # TODO: Implementar diálogo de filtros
    
    def clear(self) -> None:
        """Limpia la búsqueda."""
        self.search_field.clear()
    
    def set_text(self, text: str) -> None:
        """
        Establece el texto de búsqueda.
        
        Args:
            text: Texto a establecer
        """
        self.search_field.setText(text)
    
    def get_text(self) -> str:
        """
        Obtiene el texto actual.
        
        Returns:
            Texto de búsqueda
        """
        return self.search_field.text()
    
    def setFocus(self) -> None:
        """Da foco al campo de búsqueda."""
        self.search_field.setFocus()
    
    def hasFocus(self) -> bool:
        """
        Verifica si tiene el foco.
        
        Returns:
            Si tiene el foco
        """
        return self.search_field.hasFocus()
