#!/usr/bin/env python3
"""
Panel de Detalles - Nueva Biblioteca
==============================

Panel de detalles de pista con estilo Material Design 3.
"""


from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPainter, QPainterPath, QPixmap, QFont
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from nueva_biblioteca.core.metadata import MetadataManager
from nueva_biblioteca.data.models import Track
from nueva_biblioteca.ui.theme import get_theme
from nueva_biblioteca.ui.widgets.md3_widgets import MD3Button, MD3Card


class RoundedImageLabel(QLabel):
    """Label con imagen redondeada."""
    
    def __init__(self, parent=None):
        """
        Inicializa el label.
        
        Args:
            parent: Widget padre
        """
        super().__init__(parent)
        self.setMinimumSize(200, 200)
        self.setMaximumSize(200, 200)
        self._pixmap = None
    
    def setPixmap(self, pixmap: QPixmap) -> None:
        """
        Establece la imagen.
        
        Args:
            pixmap: Imagen a mostrar
        """
        self._pixmap = pixmap
        self.update()
    
    def paintEvent(self, event) -> None:
        """Dibuja la imagen con bordes redondeados."""
        if not self._pixmap:
            return
        
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Crear máscara redondeada
        path = QPainterPath()
        path.addRoundedRect(0, 0, self.width(), self.height(), 16, 16)
        
        # Aplicar máscara y dibujar imagen escalada
        painter.setClipPath(path)
        scaled = self._pixmap.scaled(
            self.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        painter.drawPixmap(0, 0, scaled)

class DetailRow(QWidget):
    """Fila de detalle con etiqueta y valor."""
    
    def __init__(
        self,
        label: str,
        value: str = "-",
        parent: QWidget | None = None
    ):
        """
        Inicializa la fila.
        
        Args:
            label: Etiqueta
            value: Valor
            parent: Widget padre
        """
        super().__init__(parent)
        
        self.theme = get_theme()
        
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 4, 0, 4)
        
        # Etiqueta
        label_widget = QLabel(label)
        label_widget.setFont(self.theme.typography.LABEL_MEDIUM)
        label_widget.setStyleSheet(f"""
            color: {self.theme.colors.ON_SURFACE_VARIANT};
        """)
        
        # Valor
        self.value_widget = QLabel(value)
        self.value_widget.setFont(self.theme.typography.BODY_MEDIUM)
        
        layout.addWidget(label_widget)
        layout.addWidget(self.value_widget, alignment=Qt.AlignmentFlag.AlignRight)
    
    def set_value(self, value: str) -> None:
        """
        Establece el valor.
        
        Args:
            value: Nuevo valor
        """
        self.value_widget.setText(value or "-")

class TrackDetails(MD3Card):
    """Panel de detalles de pista."""
    
    def __init__(self, parent: QWidget | None = None):
        """
        Inicializa el panel.
        
        Args:
            parent: Widget padre
        """
        super().__init__(parent, elevation=1)
        
        self.theme = get_theme()
        self.metadata_manager = MetadataManager()
        self.track = None  # Track actual
        self.repository = None  # Se establecerá desde MainWindow
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Portada
        self.cover_label = RoundedImageLabel()
        self.cover_label.setPixmap(QPixmap("icons/music.svg"))
        layout.addWidget(
            self.cover_label,
            alignment=Qt.AlignmentFlag.AlignHCenter
        )
        
        # Título y artista
        self.title_label = QLabel("Sin reproducción")
        # Configurar fuente robusta para el título
        title_font = QFont()
        title_font.setFamily("SF Pro Display, Helvetica Neue, Arial, sans-serif")  # Fuentes macOS/fallback
        title_font.setPointSize(18)
        title_font.setWeight(QFont.Weight.DemiBold)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_label.setWordWrap(True)  # Permitir wrap de texto
        
        self.artist_label = QLabel("-")
        self.artist_label.setFont(self.theme.typography.TITLE_MEDIUM)
        self.artist_label.setStyleSheet(f"""
            color: {self.theme.colors.ON_SURFACE_VARIANT};
        """)
        self.artist_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.title_label)
        layout.addWidget(self.artist_label)
        
        # Acciones mejoradas
        actions = QWidget()
        actions_layout = QHBoxLayout(actions)
        actions_layout.setContentsMargins(0, 8, 0, 8)
        actions_layout.setSpacing(8)
        
        self.edit_button = MD3Button(
            "Editar",
            variant="filled",
            icon="icons/edit.svg"
        )
        self.recommend_button = MD3Button(
            "Similares",
            variant="text",
            icon="icons/recommend.svg"
        )
        
        actions_layout.addWidget(self.edit_button)
        actions_layout.addWidget(self.recommend_button)
        actions_layout.addStretch()  # Empujar botones a la izquierda
        
        layout.addWidget(actions)
        
        # Detalles
        details = QWidget()
        details_layout = QVBoxLayout(details)
        details_layout.setContentsMargins(0, 0, 0, 0)
        details_layout.setSpacing(0)
        
        # Filas de detalles
        self.album_row = DetailRow("Álbum")
        self.genre_row = DetailRow("Género")
        self.year_row = DetailRow("Año")
        self.duration_row = DetailRow("Duración")
        self.bitrate_row = DetailRow("Bitrate")
        self.format_row = DetailRow("Formato")
        
        details_layout.addWidget(self.album_row)
        details_layout.addWidget(self.genre_row)
        details_layout.addWidget(self.year_row)
        details_layout.addWidget(self.duration_row)
        details_layout.addWidget(self.bitrate_row)
        details_layout.addWidget(self.format_row)
        
        layout.addWidget(details)
        
        # Conectar señales
        self.edit_button.clicked.connect(self._edit_metadata)
        self.recommend_button.clicked.connect(self._show_recommendations)
        
        # Estirar espacio al final
        layout.addStretch()
    
    def set_track(self, track: Track | None) -> None:
        """
        Establece el track actual.
        
        Args:
            track: Track a mostrar
        """
        self.track = track  # Almacenar el track actual
        
        if not track:
            self.title_label.setText("Sin reproducción")
            self.artist_label.setText("-")
            self.cover_label.setPixmap(QPixmap("icons/music.svg"))
            
            # Limpiar detalles
            self.album_row.set_value("-")
            self.genre_row.set_value("-")
            self.year_row.set_value("-")
            self.duration_row.set_value("-")
            self.format_row.set_value("-")
            self.bitrate_row.set_value("-")
            
            # Deshabilitar botones
            self.edit_button.setEnabled(False)
            self.recommend_button.setEnabled(False)
            
            return
        
        # Info básica
        title_text = track.title or "Sin título"
        artist_text = track.artist or "Desconocido"
        
        self.title_label.setText(title_text)
        self.artist_label.setText(artist_text)
        
        # Cargar portada (temporalmente deshabilitado)
        # cover = self.metadata_manager.get_cover(track.file_path)
        # if cover:
        #     self.cover_label.setPixmap(QPixmap.fromImage(cover))
        # else:
        self.cover_label.setPixmap(QPixmap("icons/music.svg"))
        
        # Metadatos
        self.album_row.set_value(track.album or "-")
        self.genre_row.set_value(track.genre or "-")
        self.year_row.set_value(str(track.year) if track.year else "-")
        self.duration_row.set_value(
            self._format_duration(track.duration) if track.duration else "-"
        )
        self.format_row.set_value(track.format or "-")
        self.bitrate_row.set_value(
            f"{track.bitrate} kbps" if track.bitrate else "-"
        )
        
        # Habilitar botones
        self.edit_button.setEnabled(True)
        self.recommend_button.setEnabled(True)
    
    def _edit_metadata(self) -> None:
        """Abre el diálogo de edición de metadatos."""
        if self.track:
            from nueva_biblioteca.ui.dialogs.metadata_dialog import MetadataDialog
            dialog = MetadataDialog(self.track, self)
            dialog.exec()
    
    def _show_recommendations(self) -> None:
        """Muestra recomendaciones basadas en la pista actual."""
        if self.track and self.repository:
            from nueva_biblioteca.ui.dialogs.recommendations_dialog import RecommendationsDialog
            dialog = RecommendationsDialog(self.track, self.repository, self)
            dialog.exec()
    
    @staticmethod
    def _format_duration(seconds: float) -> str:
        """
        Formatea una duración en segundos a formato MM:SS.
        
        Args:
            seconds: Duración en segundos
            
        Returns:
            Duración formateada
        """
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes:02d}:{seconds:02d}"
