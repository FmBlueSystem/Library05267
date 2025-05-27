#!/usr/bin/env python3
"""
Tabla de Biblioteca - Nueva Biblioteca
===============================

Tabla para mostrar la biblioteca musical con estilo Material Design 3.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHeaderView,
    QMenu,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from nueva_biblioteca.data.models import Playlist, Track
from nueva_biblioteca.data.repository import Repository
from nueva_biblioteca.ui.theme import get_theme
from nueva_biblioteca.ui.widgets.md3_widgets import MD3Card


class LibraryTable(MD3Card):
    """Tabla de biblioteca con estilo Material Design 3."""
    
    # Señales
    track_selected = pyqtSignal(Track)  # Track seleccionado
    
    def __init__(self, repository: Repository, parent: QWidget | None = None):
        """
        Inicializa la tabla.
        
        Args:
            repository: Repositorio de datos
            parent: Widget padre
        """
        super().__init__(parent, elevation=1)
        
        self.repository = repository
        self.theme = get_theme()
        self.current_playlist: Playlist | None = None
        
        self._setup_ui()
        self._load_data()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        # Layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Tabla
        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels([
            "Título",
            "Artista",
            "Álbum",
            "Género",
            "Duración",
            "Año"
        ])
        
        # Configurar cabecera
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Título
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed)  # Duración
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)  # Año
        
        # Configurar selección
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)  # Filas alternadas
        self.table.setShowGrid(False)  # Sin líneas de grid
        
        # Señales
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Estilos MD3 mejorados
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.theme.colors.SURFACE};
                border: none;
                gridline-color: {self.theme.colors.OUTLINE_VARIANT};
                alternate-background-color: {self.theme.colors.SURFACE_VARIANT};
                selection-background-color: {self.theme.colors.PRIMARY_CONTAINER};
            }}
            
            QTableWidget::item {{
                padding: 12px 8px;
                border-bottom: 1px solid {self.theme.colors.OUTLINE_VARIANT};
                font-size: 14px;
            }}
            
            QTableWidget::item:selected {{
                background-color: {self.theme.colors.PRIMARY_CONTAINER};
                color: {self.theme.colors.ON_PRIMARY_CONTAINER};
                border-radius: 4px;
            }}
            
            QTableWidget::item:hover {{
                background-color: {self.theme.colors.SURFACE_VARIANT};
            }}
            
            QHeaderView::section {{
                background-color: {self.theme.colors.PRIMARY};
                color: {self.theme.colors.ON_PRIMARY};
                padding: 12px 8px;
                border: none;
                border-right: 1px solid {self.theme.colors.PRIMARY_CONTAINER};
                font-weight: bold;
                font-size: 13px;
            }}
            
            QHeaderView::section:hover {{
                background-color: {self.theme.colors.SECONDARY};
            }}
            
            QHeaderView::section:first {{
                border-top-left-radius: 8px;
            }}
            
            QHeaderView::section:last {{
                border-top-right-radius: 8px;
                border-right: none;
            }}
        """)
        
        layout.addWidget(self.table)
    
    def _load_data(self) -> None:
        """Carga los datos de la biblioteca."""
        tracks = (
            self.current_playlist.tracks if self.current_playlist
            else self.repository.get_all_tracks()
        )
        
        self.table.setRowCount(len(tracks))
        
        for i, track in enumerate(tracks):
            # Título
            title_item = QTableWidgetItem(track.title or "Sin título")
            title_item.setData(Qt.ItemDataRole.UserRole, track)
            self.table.setItem(i, 0, title_item)
            
            # Artista
            self.table.setItem(
                i, 1,
                QTableWidgetItem(track.artist or "Desconocido")
            )
            
            # Álbum
            self.table.setItem(
                i, 2,
                QTableWidgetItem(track.album or "-")
            )
            
            # Género
            self.table.setItem(
                i, 3,
                QTableWidgetItem(track.genre or "-")
            )
            
            # Duración
            duration = (
                self._format_duration(track.duration)
                if track.duration else "-"
            )
            self.table.setItem(i, 4, QTableWidgetItem(duration))
            
            # Año
            year = str(track.year) if track.year else "-"
            self.table.setItem(i, 5, QTableWidgetItem(year))
    
    def filter(self, query: str) -> None:
        """
        Filtra la tabla según una búsqueda.
        
        Args:
            query: Texto de búsqueda
        """
        for i in range(self.table.rowCount()):
            matches = False
            
            for j in range(self.table.columnCount()):
                item = self.table.item(i, j)
                if item and query.lower() in item.text().lower():
                    matches = True
                    break
            
            self.table.setRowHidden(i, not matches)
    
    def set_playlist(self, playlist: Playlist | None) -> None:
        """
        Establece la playlist actual.
        
        Args:
            playlist: Playlist a mostrar o None para biblioteca
        """
        self.current_playlist = playlist
        self._load_data()
    
    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """
        Maneja el doble click en un ítem.
        
        Args:
            item: Ítem clickeado
        """
        track = self.table.item(item.row(), 0).data(Qt.ItemDataRole.UserRole)
        if track:
            self.track_selected.emit(track)
    
    def _show_context_menu(self, pos) -> None:
        """Muestra el menú contextual."""
        item = self.table.itemAt(pos)
        if not item:
            return
            
        track = item.data(Qt.ItemDataRole.UserRole)
        if not track:
            return
            
        menu = QMenu(self)
        
        # Agregar a playlist
        add_to_menu = menu.addMenu("Agregar a playlist")
        playlists = self.repository.get_all_playlists()
        
        for playlist in playlists:
            if playlist != self.current_playlist:
                action = add_to_menu.addAction(playlist.name)
                action.triggered.connect(
                    lambda checked, t=track, p=playlist:
                    self._add_to_playlist(t, p)
                )
        
        # Editar metadatos
        edit_action = menu.addAction("Editar metadatos")
        edit_action.triggered.connect(lambda: self._edit_metadata(track))
        
        # Mostrar recomendaciones
        recommend_action = menu.addAction("Mostrar similares")
        recommend_action.triggered.connect(
            lambda: self._show_recommendations(track)
        )
        
        menu.exec(self.table.viewport().mapToGlobal(pos))
    
    def _add_to_playlist(self, track: Track, playlist: Playlist) -> None:
        """
        Agrega un track a una playlist.
        
        Args:
            track: Track a agregar
            playlist: Playlist destino
        """
        playlist.add_track(track)
        self.repository.update_playlist(playlist)
    
    def _edit_metadata(self, track: Track) -> None:
        """
        Abre el diálogo de edición de metadatos.
        
        Args:
            track: Track a editar
        """
        from nueva_biblioteca.ui.dialogs.metadata_dialog import MetadataDialog
        dialog = MetadataDialog(self, tracks=[track])
        dialog.exec()
    
    def _show_recommendations(self, track: Track) -> None:
        """
        Abre el diálogo de recomendaciones.
        
        Args:
            track: Track base
        """
        from nueva_biblioteca.ui.dialogs.recommendations_dialog import (
            RecommendationsDialog,
        )
        dialog = RecommendationsDialog(
            self,
            repository=self.repository,
            seed_tracks=[track]
        )
        dialog.exec()
    
    @staticmethod
    def _format_duration(seconds: float | None) -> str:
        """
        Formatea una duración en segundos.
        
        Args:
            seconds: Duración en segundos
            
        Returns:
            Duración formateada
        """
        if seconds is None:
            return "-"
            
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        
        return f"{minutes}:{seconds:02d}"
    
    def get_visible_tracks(self) -> list[Track]:
        """
        Obtiene todos los tracks visibles en la tabla.
        
        Returns:
            Lista de tracks visibles
        """
        tracks = []
        for i in range(self.table.rowCount()):
            if not self.table.isRowHidden(i):
                track = self.table.item(i, 0).data(Qt.ItemDataRole.UserRole)
                if track:
                    tracks.append(track)
        return tracks
    
    def select_track(self, track: Track) -> None:
        """
        Selecciona un track en la tabla.
        
        Args:
            track: Track a seleccionar
        """
        for i in range(self.table.rowCount()):
            item = self.table.item(i, 0)
            if item:
                item_track = item.data(Qt.ItemDataRole.UserRole)
                if item_track and item_track.id == track.id:
                    self.table.selectRow(i)
                    self.table.scrollToItem(item)
                    break
