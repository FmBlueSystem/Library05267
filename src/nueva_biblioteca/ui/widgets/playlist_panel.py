#!/usr/bin/env python3
"""
Panel de Playlists - Nueva Biblioteca
==============================

Panel para gestionar playlists con estilo Material Design 3.
"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMenu,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from nueva_biblioteca.data.models import Playlist
from nueva_biblioteca.data.repository import Repository
from nueva_biblioteca.ui.theme import get_theme
from nueva_biblioteca.ui.widgets.md3_widgets import MD3Button, MD3Card, MD3Chip


class PlaylistItem(MD3Card):
    """Item de playlist con estilo Material Design 3."""
    
    # Señales
    clicked = pyqtSignal(Playlist)  # Playlist seleccionada
    edit_requested = pyqtSignal(Playlist)  # Solicitud de edición
    delete_requested = pyqtSignal(Playlist)  # Solicitud de eliminación
    
    def __init__(
        self,
        playlist: Playlist,
        parent: QWidget | None = None
    ):
        """
        Inicializa el item.
        
        Args:
            playlist: Playlist a mostrar
            parent: Widget padre
        """
        super().__init__(parent, elevation=1)
        
        self.playlist = playlist
        self.theme = get_theme()
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        
        # Info
        info = QVBoxLayout()
        
        # Título
        self.title_label = QLabel(self.playlist.name)
        self.title_label.setFont(self.theme.typography.TITLE_MEDIUM)
        
        # Descripción y cantidad
        details = QLabel()
        details.setFont(self.theme.typography.BODY_MEDIUM)
        details.setStyleSheet(f"""
            color: {self.theme.colors.ON_SURFACE_VARIANT};
        """)
        
        if self.playlist.is_smart:
            details.setText("Playlist inteligente")
        else:
            count = self.playlist.track_count
            tracks = "track" if count == 1 else "tracks"
            details.setText(f"{count} {tracks}")
        
        info.addWidget(self.title_label)
        info.addWidget(details)
        
        layout.addLayout(info, stretch=1)
        
        # Botones
        buttons = QHBoxLayout()
        buttons.setSpacing(8)
        
        self.edit_button = MD3Button(
            variant="text",
            icon="icons/edit.svg"
        )
        self.edit_button.setFixedSize(32, 32)
        self.edit_button.clicked.connect(
            lambda: self.edit_requested.emit(self.playlist)
        )
        
        self.menu_button = MD3Button(
            variant="text",
            icon="icons/more.svg"
        )
        self.menu_button.setFixedSize(32, 32)
        self.menu_button.clicked.connect(self._show_menu)
        
        buttons.addWidget(self.edit_button)
        buttons.addWidget(self.menu_button)
        
        layout.addLayout(buttons)
        
        # Estilo
        self.setStyleSheet(f"""
            PlaylistItem {{
                background-color: {self.theme.colors.SURFACE};
                border-radius: {self.theme.shapes.MEDIUM};
            }}
            
            PlaylistItem:hover {{
                background-color: {self.theme.colors.SURFACE_VARIANT};
            }}
        """)
    
    def mousePressEvent(self, event) -> None:
        """Maneja clicks en el item."""
        self.clicked.emit(self.playlist)
    
    def _show_menu(self) -> None:
        """Muestra el menú contextual."""
        menu = QMenu(self)
        
        export_action = menu.addAction("Exportar")
        export_action.triggered.connect(self._export_playlist)
        
        menu.addSeparator()
        
        delete_action = menu.addAction("Eliminar")
        delete_action.triggered.connect(
            lambda: self.delete_requested.emit(self.playlist)
        )
        
        menu.exec(self.menu_button.mapToGlobal(
            self.menu_button.rect().bottomRight()
        ))
    
    def _export_playlist(self) -> None:
        """Abre el diálogo de exportación."""
        from nueva_biblioteca.ui.dialogs.export_dialog import ExportDialog
        dialog = ExportDialog(self, playlist=self.playlist)
        dialog.exec()

class PlaylistPanel(MD3Card):
    """Panel de playlists."""
    
    # Señales
    playlist_selected = pyqtSignal(Playlist)  # Playlist seleccionada
    
    def __init__(
        self,
        repository: Repository,
        parent: QWidget | None = None
    ):
        """
        Inicializa el panel.
        
        Args:
            repository: Repositorio de datos
            parent: Widget padre
        """
        super().__init__(parent)
        
        self.repository = repository
        self.theme = get_theme()
        
        self._setup_ui()
        self._load_playlists()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        # Layout principal
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Cabecera
        header = QHBoxLayout()
        
        title = QLabel("Playlists")
        title.setFont(self.theme.typography.HEADLINE_SMALL)
        
        new_button = MD3Button(
            "Nueva Lista",
            variant="filled",
            icon="icons/add.svg"
        )
        new_button.clicked.connect(self._create_playlist)
        
        header.addWidget(title)
        header.addStretch()
        header.addWidget(new_button)
        
        layout.addLayout(header)
        
        # Filtros
        filters = QHBoxLayout()
        
        self.all_chip = MD3Chip("Todas", selected=True)
        self.normal_chip = MD3Chip("Normales")
        self.smart_chip = MD3Chip("Inteligentes")
        
        self.all_chip.clicked.connect(lambda: self._filter_playlists("all"))
        self.normal_chip.clicked.connect(lambda: self._filter_playlists("normal"))
        self.smart_chip.clicked.connect(lambda: self._filter_playlists("smart"))
        
        filters.addWidget(self.all_chip)
        filters.addWidget(self.normal_chip)
        filters.addWidget(self.smart_chip)
        filters.addStretch()
        
        layout.addLayout(filters)
        
        # Lista de playlists
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        
        self.playlists_container = QWidget()
        self.playlists_layout = QVBoxLayout(self.playlists_container)
        self.playlists_layout.setContentsMargins(0, 0, 0, 0)
        self.playlists_layout.setSpacing(8)
        
        scroll.setWidget(self.playlists_container)
        layout.addWidget(scroll)
    
    def _load_playlists(self) -> None:
        """Carga las playlists desde el repositorio."""
        # Limpiar lista
        while self.playlists_layout.count():
            item = self.playlists_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Cargar playlists
        playlists = self.repository.get_all_playlists()
        
        for playlist in playlists:
            item = PlaylistItem(playlist)
            item.clicked.connect(self.playlist_selected.emit)
            item.edit_requested.connect(self._edit_playlist)
            item.delete_requested.connect(self._delete_playlist)
            self.playlists_layout.addWidget(item)
        
        # Agregar stretch al final
        self.playlists_layout.addStretch()
    
    def _filter_playlists(self, filter_type: str) -> None:
        """
        Filtra las playlists mostradas.
        
        Args:
            filter_type: Tipo de filtro ("all", "normal" o "smart")
        """
        # Actualizar chips
        self.all_chip.set_selected(filter_type == "all")
        self.normal_chip.set_selected(filter_type == "normal")
        self.smart_chip.set_selected(filter_type == "smart")
        
        # Mostrar/ocultar playlists
        for i in range(self.playlists_layout.count()):
            item = self.playlists_layout.itemAt(i)
            if item and isinstance(item.widget(), PlaylistItem):
                playlist = item.widget().playlist
                
                if filter_type == "all":
                    item.widget().show()
                elif filter_type == "normal":
                    item.widget().setVisible(not playlist.is_smart)
                elif filter_type == "smart":
                    item.widget().setVisible(playlist.is_smart)
    
    def _create_playlist(self) -> None:
        """Abre el diálogo de nueva playlist."""
        from nueva_biblioteca.ui.dialogs.smart_playlist_dialog import (
            SmartPlaylistDialog,
        )
        dialog = SmartPlaylistDialog(self, repository=self.repository)
        if dialog.exec():
            self._load_playlists()
    
    def _edit_playlist(self, playlist: Playlist) -> None:
        """
        Edita una playlist.
        
        Args:
            playlist: Playlist a editar
        """
        if playlist.is_smart:
            from nueva_biblioteca.ui.dialogs.smart_playlist_dialog import (
                SmartPlaylistDialog,
            )
            dialog = SmartPlaylistDialog(
                self,
                repository=self.repository,
                playlist=playlist
            )
        else:
            from nueva_biblioteca.ui.dialogs.export_dialog import ExportDialog
            dialog = ExportDialog(self, playlist=playlist)
            
        if dialog.exec():
            self._load_playlists()
    
    def _delete_playlist(self, playlist: Playlist) -> None:
        """
        Elimina una playlist.
        
        Args:
            playlist: Playlist a eliminar
        """
        self.repository.delete_playlist(playlist)
        self._load_playlists()
    
    def filter(self, query: str) -> None:
        """
        Filtra las playlists por nombre.
        
        Args:
            query: Texto de búsqueda
        """
        query = query.lower()
        
        for i in range(self.playlists_layout.count()):
            item = self.playlists_layout.itemAt(i)
            if item and isinstance(item.widget(), PlaylistItem):
                playlist = item.widget().playlist
                matches = query in playlist.name.lower()
                item.widget().setVisible(matches)
