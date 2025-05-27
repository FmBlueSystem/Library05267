#!/usr/bin/env python3
"""
Diálogo de Metadatos - Nueva Biblioteca
===================================

Diálogo para editar los metadatos de tracks, incluyendo edición
por lotes y extracción desde servicios externos.
"""

from typing import Any

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from nueva_biblioteca.core.metadata import MetadataManager
from nueva_biblioteca.data.models import Track
from nueva_biblioteca.utils.logger import get_logger
from nueva_biblioteca.utils.task_queue import get_task_queue

logger = get_logger(__name__)

class MetadataWorker(QThread):
    """Worker thread para operaciones de metadatos."""
    
    # Señales
    progress = pyqtSignal(int, str)  # porcentaje, mensaje
    finished = pyqtSignal(bool, str, object)  # éxito, mensaje, resultados
    
    def __init__(
        self,
        operation: str,
        tracks: list[Track],
        metadata: dict[str, Any] | None = None
    ):
        """
        Inicializa el worker.
        
        Args:
            operation: Tipo de operación
            tracks: Lista de tracks
            metadata: Metadatos a aplicar
        """
        super().__init__()
        self.operation = operation
        self.tracks = tracks
        self.metadata = metadata or {}
        self.metadata_manager = MetadataManager()
        self._cancelled = False
    
    def run(self) -> None:
        """Ejecuta la operación."""
        try:
            if self.operation == "apply":
                self._apply_metadata()
            elif self.operation == "fetch":
                self._fetch_metadata()
            else:
                raise ValueError(f"Operación no soportada: {self.operation}")
                
        except Exception as e:
            logger.error(f"Error en operación de metadatos: {e}")
            self.finished.emit(False, str(e), None)
    
    def _apply_metadata(self) -> None:
        """Aplica metadatos a los tracks."""
        results = []
        total = len(self.tracks)
        
        for i, track in enumerate(self.tracks, 1):
            if self._cancelled:
                break
                
            try:
                # Aplicar cada campo si está presente
                updated = {}
                for field, value in self.metadata.items():
                    if value is not None:
                        setattr(track, field, value)
                        updated[field] = value
                
                # Guardar cambios en archivo
                self.metadata_manager.write_metadata(track.file_path, updated)
                results.append(track)
                
            except Exception as e:
                logger.error(f"Error aplicando metadatos a {track.file_path}: {e}")
            
            # Actualizar progreso
            percentage = int((i / total) * 100)
            self.progress.emit(percentage, f"Procesando {i}/{total}")
        
        if self._cancelled:
            self.finished.emit(False, "Operación cancelada", results)
        else:
            self.finished.emit(True, "Metadatos aplicados correctamente", results)
    
    def _fetch_metadata(self) -> None:
        """Obtiene metadatos desde servicios externos."""
        results = []
        total = len(self.tracks)
        
        for i, track in enumerate(self.tracks, 1):
            if self._cancelled:
                break
                
            try:
                # Buscar metadatos
                metadata = self.metadata_manager.fetch_metadata(
                    track.title or "",
                    track.artist or ""
                )
                
                if metadata:
                    results.append((track, metadata))
                
            except Exception as e:
                logger.error(f"Error obteniendo metadatos para {track.title}: {e}")
            
            # Actualizar progreso
            percentage = int((i / total) * 100)
            self.progress.emit(percentage, f"Buscando {i}/{total}")
        
        if self._cancelled:
            self.finished.emit(False, "Operación cancelada", results)
        else:
            self.finished.emit(
                True,
                f"Encontrados metadatos para {len(results)} tracks",
                results
            )
    
    def cancel(self) -> None:
        """Cancela la operación."""
        self._cancelled = True

class MetadataDialog(QDialog):
    """
    Diálogo para editar metadatos.
    
    Características:
    - Edición individual y por lotes
    - Búsqueda en servicios externos
    - Vista previa de cambios
    - Operaciones asíncronas
    """
    
    def __init__(
        self,
        parent=None,
        tracks: list[Track] | None = None
    ):
        """
        Inicializa el diálogo.
        
        Args:
            parent: Widget padre
            tracks: Lista de tracks a editar
        """
        super().__init__(parent)
        
        self.tracks = tracks or []
        self.task_queue = get_task_queue()
        self._worker: MetadataWorker | None = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        # Configuración básica
        self.setWindowTitle("Editar Metadatos")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Tabs para diferentes modos
        tabs = QTabWidget()
        tabs.addTab(self._create_edit_tab(), "Editar")
        if len(self.tracks) > 1:
            tabs.addTab(self._create_batch_tab(), "Edición por Lotes")
        tabs.addTab(self._create_fetch_tab(), "Buscar")
        
        # Progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.apply_button = QPushButton("Aplicar")
        self.apply_button.clicked.connect(self._apply_changes)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.apply_button)
        button_layout.addWidget(self.cancel_button)
        
        # Layout principal
        layout.addWidget(tabs)
        layout.addWidget(self.progress_bar)
        layout.addLayout(button_layout)
    
    def _create_edit_tab(self) -> QWidget:
        """Crea tab para edición individual."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        if len(self.tracks) == 1:
            # Edición de un solo track
            track = self.tracks[0]
            form = QFormLayout()
            
            # Campos editables
            self.title_edit = QLineEdit(track.title or "")
            form.addRow("Título:", self.title_edit)
            
            self.artist_edit = QLineEdit(track.artist or "")
            form.addRow("Artista:", self.artist_edit)
            
            self.album_edit = QLineEdit(track.album or "")
            form.addRow("Álbum:", self.album_edit)
            
            self.genre_edit = QLineEdit(track.genre or "")
            form.addRow("Género:", self.genre_edit)
            
            self.year_spin = QSpinBox()
            self.year_spin.setRange(0, 9999)
            self.year_spin.setValue(track.year or 0)
            form.addRow("Año:", self.year_spin)
            
            layout.addLayout(form)
            
        else:
            # Vista de múltiples tracks
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            content = QWidget()
            content_layout = QVBoxLayout(content)
            
            for track in self.tracks:
                group = QGroupBox(track.title or "Sin título")
                group_layout = QFormLayout(group)
                
                title = QLabel(track.title or "-")
                artist = QLabel(track.artist or "-")
                album = QLabel(track.album or "-")
                genre = QLabel(track.genre or "-")
                year = QLabel(str(track.year) if track.year else "-")
                
                group_layout.addRow("Título:", title)
                group_layout.addRow("Artista:", artist)
                group_layout.addRow("Álbum:", album)
                group_layout.addRow("Género:", genre)
                group_layout.addRow("Año:", year)
                
                content_layout.addWidget(group)
            
            scroll.setWidget(content)
            layout.addWidget(scroll)
        
        return widget
    
    def _create_batch_tab(self) -> QWidget:
        """Crea tab para edición por lotes."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Selección de campos a editar
        fields_group = QGroupBox("Campos a modificar")
        fields_layout = QVBoxLayout(fields_group)
        
        self.title_check = QCheckBox("Título")
        self.artist_check = QCheckBox("Artista")
        self.album_check = QCheckBox("Álbum")
        self.genre_check = QCheckBox("Género")
        self.year_check = QCheckBox("Año")
        
        fields_layout.addWidget(self.title_check)
        fields_layout.addWidget(self.artist_check)
        fields_layout.addWidget(self.album_check)
        fields_layout.addWidget(self.genre_check)
        fields_layout.addWidget(self.year_check)
        
        # Valores a aplicar
        values_group = QGroupBox("Nuevos valores")
        values_layout = QFormLayout(values_group)
        
        self.batch_title = QLineEdit()
        self.batch_artist = QLineEdit()
        self.batch_album = QLineEdit()
        self.batch_genre = QLineEdit()
        self.batch_year = QSpinBox()
        self.batch_year.setRange(0, 9999)
        
        values_layout.addRow("Título:", self.batch_title)
        values_layout.addRow("Artista:", self.batch_artist)
        values_layout.addRow("Álbum:", self.batch_album)
        values_layout.addRow("Género:", self.batch_genre)
        values_layout.addRow("Año:", self.batch_year)
        
        # Habilitar/deshabilitar campos
        def _toggle_field(check: QCheckBox, field: QWidget) -> None:
            field.setEnabled(check.isChecked())
        
        self.title_check.stateChanged.connect(
            lambda: _toggle_field(self.title_check, self.batch_title))
        self.artist_check.stateChanged.connect(
            lambda: _toggle_field(self.artist_check, self.batch_artist))
        self.album_check.stateChanged.connect(
            lambda: _toggle_field(self.album_check, self.batch_album))
        self.genre_check.stateChanged.connect(
            lambda: _toggle_field(self.genre_check, self.batch_genre))
        self.year_check.stateChanged.connect(
            lambda: _toggle_field(self.year_check, self.batch_year))
        
        # Deshabilitar todos inicialmente
        for field in [self.batch_title, self.batch_artist, self.batch_album,
                     self.batch_genre, self.batch_year]:
            field.setEnabled(False)
        
        layout.addWidget(fields_group)
        layout.addWidget(values_group)
        
        return widget
    
    def _create_fetch_tab(self) -> QWidget:
        """Crea tab para búsqueda externa."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        
        # Servicios disponibles
        services_group = QGroupBox("Servicios")
        services_layout = QVBoxLayout(services_group)
        
        self.musicbrainz_check = QCheckBox("MusicBrainz")
        self.lastfm_check = QCheckBox("Last.fm")
        self.spotify_check = QCheckBox("Spotify")
        
        services_layout.addWidget(self.musicbrainz_check)
        services_layout.addWidget(self.lastfm_check)
        services_layout.addWidget(self.spotify_check)
        
        # Opciones de búsqueda
        options_group = QGroupBox("Opciones")
        options_layout = QVBoxLayout(options_group)
        
        self.auto_apply = QCheckBox("Aplicar automáticamente")
        self.auto_apply.setChecked(True)
        
        self.prefer_albums = QCheckBox("Preferir coincidencias de álbum")
        self.prefer_albums.setChecked(True)
        
        options_layout.addWidget(self.auto_apply)
        options_layout.addWidget(self.prefer_albums)
        
        # Botón de búsqueda
        self.fetch_button = QPushButton("Buscar metadatos")
        self.fetch_button.clicked.connect(self._fetch_metadata)
        
        layout.addWidget(services_group)
        layout.addWidget(options_group)
        layout.addWidget(self.fetch_button)
        layout.addStretch()
        
        return widget
    
    def _apply_changes(self) -> None:
        """Aplica los cambios de metadatos."""
        if not self.tracks:
            return
            
        metadata = {}
        
        if len(self.tracks) == 1:
            # Edición individual
            metadata = {
                'title': self.title_edit.text(),
                'artist': self.artist_edit.text(),
                'album': self.album_edit.text(),
                'genre': self.genre_edit.text(),
                'year': self.year_spin.value() or None
            }
            
        else:
            # Edición por lotes
            if self.title_check.isChecked():
                metadata['title'] = self.batch_title.text()
            if self.artist_check.isChecked():
                metadata['artist'] = self.batch_artist.text()
            if self.album_check.isChecked():
                metadata['album'] = self.batch_album.text()
            if self.genre_check.isChecked():
                metadata['genre'] = self.batch_genre.text()
            if self.year_check.isChecked():
                metadata['year'] = self.batch_year.value() or None
        
        # Iniciar worker
        self._start_operation("apply", metadata)
    
    def _fetch_metadata(self) -> None:
        """Busca metadatos en servicios externos."""
        self._start_operation("fetch")
    
    def _start_operation(
        self,
        operation: str,
        metadata: dict[str, Any] | None = None
    ) -> None:
        """Inicia una operación de metadatos."""
        # Configurar UI
        self.apply_button.setEnabled(False)
        self.fetch_button.setEnabled(False)
        self.cancel_button.setText("Cancelar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        # Crear worker
        self._worker = MetadataWorker(operation, self.tracks, metadata)
        self._worker.progress.connect(self._update_progress)
        self._worker.finished.connect(self._operation_finished)
        self._worker.start()
    
    def _update_progress(self, percentage: int, message: str) -> None:
        """Actualiza la barra de progreso."""
        self.progress_bar.setValue(percentage)
        self.progress_bar.setFormat(f"{percentage}% - {message}")
    
    def _operation_finished(
        self,
        success: bool,
        message: str,
        results: Any
    ) -> None:
        """Maneja el fin de una operación."""
        self._worker = None
        self.progress_bar.hide()
        self.apply_button.setEnabled(True)
        self.fetch_button.setEnabled(True)
        self.cancel_button.setText("Cerrar")
        
        if success:
            QMessageBox.information(self, "Éxito", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)
    
    def reject(self) -> None:
        """Maneja el cierre del diálogo."""
        if self._worker and self._worker.isRunning():
            # Cancelar operación en curso
            reply = QMessageBox.question(
                self,
                "Cancelar operación",
                "¿Está seguro de cancelar la operación?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._worker.cancel()
                self._worker.wait()
                super().reject()
        else:
            super().reject()
