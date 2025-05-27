#!/usr/bin/env python3
"""
Ventana Principal - Nueva Biblioteca
==============================

Ventana principal de la aplicación con estilo Material Design 3.
"""

from pathlib import Path

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QMainWindow,
    QMenuBar,
    QMessageBox,
    QSplitter,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from nueva_biblioteca.data.models import Playlist, Track
from nueva_biblioteca.data.repository import Repository

from .theme import get_theme
from .widgets.library_table import LibraryTable
from .widgets.md3_widgets import MD3Card, MD3NavigationRail
from .widgets.player_controls import PlayerControls
from .widgets.playlist_panel import PlaylistPanel
from .widgets.queue_widget import QueueWidget
from .widgets.search_bar import SearchBar
from .widgets.track_details import TrackDetails


class MainWindow(QMainWindow):
    """Ventana principal de la aplicación."""
    
    def __init__(self, repository: Repository):
        """
        Inicializa la ventana principal.
        
        Args:
            repository: Repositorio de datos
        """
        super().__init__()
        
        self.repository = repository
        self.theme = get_theme()
        
        self._setup_ui()
        self.theme.apply_to_widget(self)
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        # Configuración básica
        self.setWindowTitle("Nueva Biblioteca")
        self.setMinimumSize(1200, 800)
        
        # Crear menú
        self._create_menu()
        
        # Widget central
        central = QWidget()
        self.setCentralWidget(central)
        
        # Layout principal
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Barra de navegación
        self.nav_rail = MD3NavigationRail(fab_text="Nueva Lista")
        self.nav_rail.add_item("icons/library.svg", "Biblioteca")
        self.nav_rail.add_item("icons/playlist.svg", "Playlists")
        self.nav_rail.add_item("icons/queue.svg", "Cola")
        self.nav_rail.add_item("icons/explore.svg", "Explorar")
        self.nav_rail.add_item("icons/settings.svg", "Ajustes")
        layout.addWidget(self.nav_rail)
        
        # Contenido principal
        main_content = QWidget()
        main_layout = QVBoxLayout(main_content)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        # Barra de búsqueda
        search_card = MD3Card(elevation=1)
        search_layout = QHBoxLayout(search_card)
        self.search_bar = SearchBar()
        search_layout.addWidget(self.search_bar)
        main_layout.addWidget(search_card)
        
        # Área central
        central_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Panel izquierdo (biblioteca/playlists)
        self.stack = QStackedWidget()
        
        # Vista de biblioteca
        self.library_view = QWidget()
        library_layout = QVBoxLayout(self.library_view)
        self.library_table = LibraryTable(self.repository)
        library_layout.addWidget(self.library_table)
        
        # Vista de playlists
        self.playlists_view = QWidget()
        playlists_layout = QVBoxLayout(self.playlists_view)
        self.playlist_panel = PlaylistPanel(self.repository)
        playlists_layout.addWidget(self.playlist_panel)
        
        # Vista de cola
        self.queue_view = QWidget()
        queue_layout = QVBoxLayout(self.queue_view)
        self.queue_widget = QueueWidget()
        queue_layout.addWidget(self.queue_widget)
        
        self.stack.addWidget(self.library_view)
        self.stack.addWidget(self.playlists_view)
        self.stack.addWidget(self.queue_view)
        central_splitter.addWidget(self.stack)
        
        # Panel derecho (detalles)
        details_panel = QWidget()
        details_layout = QVBoxLayout(details_panel)
        self.track_details = TrackDetails()
        self.track_details.repository = self.repository  # Pasar el repository
        details_layout.addWidget(self.track_details)
        central_splitter.addWidget(details_panel)
        
        # Ajustar proporción del splitter
        central_splitter.setStretchFactor(0, 2)
        central_splitter.setStretchFactor(1, 1)
        
        main_layout.addWidget(central_splitter)
        
        # Controles de reproducción
        controls_card = MD3Card(elevation=2)
        controls_layout = QHBoxLayout(controls_card)
        self.player_controls = PlayerControls()
        controls_layout.addWidget(self.player_controls)
        main_layout.addWidget(controls_card)
        
        layout.addWidget(main_content, stretch=1)
        
        # Conectar señales
        self.nav_rail.current_changed.connect(self._handle_navigation)
        self.search_bar.search_changed.connect(self._handle_search)
        self.library_table.track_selected.connect(self._handle_track_selected)
        self.playlist_panel.playlist_selected.connect(self._handle_playlist_selected)
        self.queue_widget.track_double_clicked.connect(self._handle_queue_track_play)
        
        # Conectar señales del reproductor
        self.player_controls.player.next_requested.connect(self._handle_next_track)
        self.player_controls.player.previous_requested.connect(self._handle_previous_track)
    
    def _create_menu(self) -> None:
        """Crea la barra de menú."""
        menubar = self.menuBar()
        
        # Menú Archivo
        file_menu = menubar.addMenu("Archivo")
        
        # Importar archivos
        import_files_action = QAction("Importar archivos...", self)
        import_files_action.setShortcut("Ctrl+I")
        import_files_action.triggered.connect(self._import_files)
        file_menu.addAction(import_files_action)
        
        # Importar carpeta
        import_folder_action = QAction("Importar carpeta...", self)
        import_folder_action.setShortcut("Ctrl+Shift+I")
        import_folder_action.triggered.connect(self._import_folder)
        file_menu.addAction(import_folder_action)
        
        file_menu.addSeparator()
        
        # Salir
        exit_action = QAction("Salir", self)
        exit_action.setShortcut("Ctrl+Q")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Menú Biblioteca
        library_menu = menubar.addMenu("Biblioteca")
        
        # Actualizar biblioteca
        refresh_action = QAction("Actualizar biblioteca", self)
        refresh_action.setShortcut("F5")
        refresh_action.triggered.connect(self._refresh_library)
        library_menu.addAction(refresh_action)
    
    def _handle_navigation(self, index: int) -> None:
        """
        Maneja cambios en la navegación.
        
        Args:
            index: Índice seleccionado
        """
        if index == 0:  # Biblioteca
            self.stack.setCurrentWidget(self.library_view)
        elif index == 1:  # Playlists
            self.stack.setCurrentWidget(self.playlists_view)
        elif index == 2:  # Cola
            self.stack.setCurrentWidget(self.queue_view)
        # TODO: Implementar otras vistas
    
    def _handle_search(self, query: str) -> None:
        """
        Maneja cambios en la búsqueda.
        
        Args:
            query: Texto de búsqueda
        """
        if self.stack.currentWidget() == self.library_view:
            self.library_table.filter(query)
        elif self.stack.currentWidget() == self.playlists_view:
            self.playlist_panel.filter(query)
    
    def _handle_track_selected(self, track: Track) -> None:
        """
        Maneja la selección de un track.
        
        Args:
            track: Track seleccionado
        """
        self.track_details.set_track(track)
        self.player_controls.play_track(track)
    
    def _handle_playlist_selected(self, playlist: Playlist) -> None:
        """
        Maneja la selección de una playlist.
        
        Args:
            playlist: Playlist seleccionada
        """
        self.library_table.set_playlist(playlist)
    
    def _handle_queue_track_play(self, track: Track) -> None:
        """
        Maneja reproducción de track desde la cola.
        
        Args:
            track: Track a reproducir
        """
        self.track_details.set_track(track)
        self.player_controls.play_track(track)
        self.stack.setCurrentWidget(self.library_view)
    
    def _handle_next_track(self) -> None:
        """Maneja la solicitud de reproducir el siguiente track."""
        current_track = self.player_controls.current_track
        if not current_track:
            return
        
        # Obtener todos los tracks visibles en la tabla
        tracks = self.library_table.get_visible_tracks()
        if not tracks:
            return
        
        # Encontrar el track actual
        current_index = -1
        for i, track in enumerate(tracks):
            if track.id == current_track.id:
                current_index = i
                break
        
        # Reproducir siguiente track
        if current_index >= 0 and current_index < len(tracks) - 1:
            next_track = tracks[current_index + 1]
            self.track_details.set_track(next_track)
            self.player_controls.play_track(next_track)
            # Seleccionar en la tabla
            self.library_table.select_track(next_track)
    
    def _handle_previous_track(self) -> None:
        """Maneja la solicitud de reproducir el track anterior."""
        current_track = self.player_controls.current_track
        if not current_track:
            return
        
        # Obtener todos los tracks visibles en la tabla
        tracks = self.library_table.get_visible_tracks()
        if not tracks:
            return
        
        # Encontrar el track actual
        current_index = -1
        for i, track in enumerate(tracks):
            if track.id == current_track.id:
                current_index = i
                break
        
        # Reproducir track anterior
        if current_index > 0:
            previous_track = tracks[current_index - 1]
            self.track_details.set_track(previous_track)
            self.player_controls.play_track(previous_track)
            # Seleccionar en la tabla
            self.library_table.select_track(previous_track)
    
    def _import_files(self) -> None:
        """Importa archivos de audio individuales."""
        file_dialog = QFileDialog(self)
        file_dialog.setFileMode(QFileDialog.FileMode.ExistingFiles)
        file_dialog.setNameFilter(
            "Archivos de audio (*.mp3 *.flac *.m4a *.wav *.ogg);;Todos los archivos (*.*)"
        )
        
        if file_dialog.exec():
            files = file_dialog.selectedFiles()
            if files:
                self._process_files(files)
    
    def _import_folder(self) -> None:
        """Importa una carpeta completa de archivos de audio."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Seleccionar carpeta de música",
            "",
            QFileDialog.Option.ShowDirsOnly
        )
        
        if folder:
            # Buscar archivos de audio en la carpeta
            from pathlib import Path
            audio_extensions = {'.mp3', '.flac', '.m4a', '.wav', '.ogg'}
            files = []
            
            for file_path in Path(folder).rglob('*'):
                if file_path.suffix.lower() in audio_extensions:
                    files.append(str(file_path))
            
            if files:
                self._process_files(files)
            else:
                QMessageBox.information(
                    self,
                    "Sin archivos",
                    "No se encontraron archivos de audio en la carpeta seleccionada."
                )
    
    def _process_files(self, files: list[str]) -> None:
        """
        Procesa una lista de archivos de audio.
        
        Args:
            files: Lista de rutas de archivos
        """
        from nueva_biblioteca.core.metadata import MetadataManager
        
        metadata_manager = MetadataManager()
        added_count = 0
        error_count = 0
        
        for file_path in files:
            try:
                # Verificar si el archivo ya existe
                existing_track = self.repository.get_track_by_path(file_path)
                if existing_track:
                    continue
                
                # Extraer metadatos
                metadata = metadata_manager.extract_metadata(file_path)
                
                if metadata:
                    # Crear track
                    track_data = {
                        'file_path': file_path,
                        'title': metadata.title or Path(file_path).stem,
                        'artist': metadata.artist,
                        'album': metadata.album,
                        'genre': ', '.join(metadata.genre) if metadata.genre else '',
                        'year': metadata.year,
                        'duration': metadata.duration,
                        'format': metadata.format,
                        'bitrate': metadata.bitrate,
                        'sample_rate': metadata.sample_rate,
                        'channels': metadata.channels,
                        'file_size': Path(file_path).stat().st_size,
                    }
                    
                    # Agregar a la base de datos
                    track = self.repository.add_track(track_data)
                    if track:
                        added_count += 1
                    else:
                        error_count += 1
                else:
                    error_count += 1
                    
            except Exception as e:
                print(f"Error procesando {file_path}: {e}")
                error_count += 1
        
        # Actualizar la vista
        self._refresh_library()
        
        # Mostrar resultado
        if added_count > 0:
            message = f"Se agregaron {added_count} archivos a la biblioteca."
            if error_count > 0:
                message += f"\n{error_count} archivos no pudieron ser procesados."
            QMessageBox.information(self, "Importación completada", message)
        elif error_count > 0:
            QMessageBox.warning(
                self,
                "Error en importación",
                f"No se pudieron procesar {error_count} archivos."
            )
        else:
            QMessageBox.information(
                self,
                "Sin cambios",
                "Todos los archivos ya estaban en la biblioteca."
            )
    
    def _refresh_library(self) -> None:
        """Actualiza la vista de la biblioteca."""
        self.library_table._load_data()
