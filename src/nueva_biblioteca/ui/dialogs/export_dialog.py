#!/usr/bin/env python3
"""
Diálogo de Exportación - Nueva Biblioteca
=====================================

Diálogo para exportar playlists y biblioteca a diferentes formatos.
"""

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
)

from nueva_biblioteca.data.models import Playlist, Track
from nueva_biblioteca.utils.exporter import Exporter, get_exporter
from nueva_biblioteca.utils.logger import get_logger

logger = get_logger(__name__)

class ExportWorker(QThread):
    """Worker thread para exportación."""
    
    # Señales
    progress = pyqtSignal(int, str)  # porcentaje, mensaje
    finished = pyqtSignal(bool, str)  # éxito, mensaje
    
    def __init__(
        self,
        exporter: Exporter,
        format_type: str,
        output_path: str,
        data: dict
    ):
        """
        Inicializa el worker.
        
        Args:
            exporter: Instancia del exportador
            format_type: Tipo de formato
            output_path: Ruta de salida
            data: Datos a exportar
        """
        super().__init__()
        self.exporter = exporter
        self.format_type = format_type
        self.output_path = output_path
        self.data = data
        self._cancelled = False
    
    def run(self) -> None:
        """Ejecuta la exportación."""
        try:
            self.progress.emit(0, "Iniciando exportación...")
            
            if self.format_type == "m3u":
                success = self.exporter.export_playlist_m3u(
                    playlist=self.data['playlist'],
                    output_path=self.output_path,
                    relative_paths=self.data.get('relative_paths', True),
                    include_metadata=self.data.get('include_metadata', True)
                )
                
            elif self.format_type == "csv":
                success = self.exporter.export_library_csv(
                    tracks=self.data['tracks'],
                    output_path=self.output_path,
                    fields=self.data.get('fields')
                )
                
            elif self.format_type == "json":
                success = self.exporter.export_json(
                    data=self.data['data'],
                    output_path=self.output_path,
                    pretty=self.data.get('pretty', True)
                )
                
            elif self.format_type == "html":
                success = self.exporter.export_playlist_html(
                    playlist=self.data['playlist'],
                    output_path=self.output_path,
                    include_images=self.data.get('include_images', True)
                )
                
            elif self.format_type == "backup":
                success = self.exporter.backup_library(
                    tracks=self.data['tracks'],
                    backup_dir=self.output_path,
                    include_files=self.data.get('include_files', True)
                )
            
            else:
                raise ValueError(f"Formato no soportado: {self.format_type}")
            
            self.progress.emit(100, "Exportación completada")
            
            if success:
                self.finished.emit(True, "Exportación completada exitosamente")
            else:
                self.finished.emit(False, "Error durante la exportación")
                
        except Exception as e:
            logger.error(f"Error en exportación: {e}")
            self.finished.emit(False, f"Error: {e!s}")
    
    def cancel(self) -> None:
        """Cancela la exportación."""
        self._cancelled = True

class ExportDialog(QDialog):
    """Diálogo para exportar playlists y biblioteca."""
    
    def __init__(
        self,
        parent=None,
        playlist: Playlist | None = None,
        tracks: list[Track] | None = None
    ):
        """
        Inicializa el diálogo.
        
        Args:
            parent: Widget padre
            playlist: Playlist a exportar
            tracks: Tracks a exportar
        """
        super().__init__(parent)
        
        self.playlist = playlist
        self.tracks = tracks
        self.exporter = get_exporter()
        self._worker: ExportWorker | None = None
        
        self._setup_ui()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        # Configuración básica
        self.setWindowTitle("Exportar")
        self.setMinimumWidth(400)
        
        layout = QVBoxLayout(self)
        
        # Formato
        format_group = QGroupBox("Formato de exportación")
        format_layout = QVBoxLayout(format_group)
        
        self.format_combo = QComboBox()
        
        # Agregar formatos según el contenido
        if self.playlist:
            self.format_combo.addItem("Playlist M3U", "m3u")
            self.format_combo.addItem("Página HTML", "html")
        if self.tracks:
            self.format_combo.addItem("CSV", "csv")
            self.format_combo.addItem("Backup completo", "backup")
        self.format_combo.addItem("JSON", "json")
        
        format_layout.addWidget(QLabel("Formato:"))
        format_layout.addWidget(self.format_combo)
        
        # Opciones específicas por formato
        self.options_group = QGroupBox("Opciones")
        self.options_layout = QVBoxLayout(self.options_group)
        
        # M3U
        self.relative_paths_check = QCheckBox("Usar rutas relativas")
        self.relative_paths_check.setChecked(True)
        self.include_metadata_check = QCheckBox("Incluir metadatos extendidos")
        self.include_metadata_check.setChecked(True)
        
        # HTML
        self.include_images_check = QCheckBox("Incluir carátulas")
        self.include_images_check.setChecked(True)
        
        # Backup
        self.include_files_check = QCheckBox("Incluir archivos de audio")
        self.include_files_check.setChecked(True)
        
        # JSON
        self.pretty_json_check = QCheckBox("Formatear JSON")
        self.pretty_json_check.setChecked(True)
        
        # Actualizar opciones según formato
        self.format_combo.currentIndexChanged.connect(self._update_options)
        self._update_options()
        
        # Ruta de salida
        path_group = QGroupBox("Ubicación")
        path_layout = QHBoxLayout(path_group)
        
        self.path_edit = QLineEdit()
        self.path_edit.setPlaceholderText("Seleccione ubicación...")
        self.path_edit.setReadOnly(True)
        
        self.browse_button = QPushButton("Examinar...")
        self.browse_button.clicked.connect(self._browse_output)
        
        path_layout.addWidget(self.path_edit)
        path_layout.addWidget(self.browse_button)
        
        # Progreso
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.export_button = QPushButton("Exportar")
        self.export_button.clicked.connect(self._export)
        self.export_button.setEnabled(False)
        
        self.cancel_button = QPushButton("Cancelar")
        self.cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.export_button)
        button_layout.addWidget(self.cancel_button)
        
        # Layout principal
        layout.addWidget(format_group)
        layout.addWidget(self.options_group)
        layout.addWidget(path_group)
        layout.addWidget(self.progress_bar)
        layout.addLayout(button_layout)
    
    def _update_options(self) -> None:
        """Actualiza las opciones según el formato seleccionado."""
        # Limpiar opciones anteriores
        while self.options_layout.count():
            item = self.options_layout.takeAt(0)
            if item.widget():
                item.widget().hide()
                self.options_layout.removeWidget(item.widget())
        
        format_type = self.format_combo.currentData()
        
        if format_type == "m3u":
            self.options_layout.addWidget(self.relative_paths_check)
            self.options_layout.addWidget(self.include_metadata_check)
            self.relative_paths_check.show()
            self.include_metadata_check.show()
            
        elif format_type == "html":
            self.options_layout.addWidget(self.include_images_check)
            self.include_images_check.show()
            
        elif format_type == "backup":
            self.options_layout.addWidget(self.include_files_check)
            self.include_files_check.show()
            
        elif format_type == "json":
            self.options_layout.addWidget(self.pretty_json_check)
            self.pretty_json_check.show()
    
    def _browse_output(self) -> None:
        """Muestra diálogo para seleccionar ubicación."""
        format_type = self.format_combo.currentData()
        
        if format_type == "backup":
            path = QFileDialog.getExistingDirectory(
                self,
                "Seleccionar directorio de backup"
            )
            if path:
                self.path_edit.setText(path)
                self.export_button.setEnabled(True)
            
        else:
            filters = {
                "m3u": "Playlist M3U (*.m3u)",
                "csv": "Archivo CSV (*.csv)",
                "json": "Archivo JSON (*.json)",
                "html": "Página HTML (*.html)"
            }
            
            path, _ = QFileDialog.getSaveFileName(
                self,
                "Guardar como",
                "",
                filters.get(format_type, "Todos los archivos (*.*)")
            )
            
            if path:
                self.path_edit.setText(path)
                self.export_button.setEnabled(True)
    
    def _export(self) -> None:
        """Inicia la exportación."""
        format_type = self.format_combo.currentData()
        output_path = self.path_edit.text()
        
        if not output_path:
            QMessageBox.warning(
                self,
                "Error",
                "Debe seleccionar una ubicación de salida"
            )
            return
        
        # Preparar datos según formato
        data = {}
        
        if format_type == "m3u":
            if not self.playlist:
                return
            data['playlist'] = self.playlist
            data['relative_paths'] = self.relative_paths_check.isChecked()
            data['include_metadata'] = self.include_metadata_check.isChecked()
            
        elif format_type == "csv":
            if not self.tracks:
                return
            data['tracks'] = self.tracks
            
        elif format_type == "json":
            # Exportar todo lo disponible
            data['data'] = {
                'playlist': self.playlist.name if self.playlist else None,
                'tracks': [
                    {
                        'title': track.title,
                        'artist': track.artist,
                        'album': track.album,
                        'duration': track.duration
                    }
                    for track in (self.tracks or [])
                ]
            }
            data['pretty'] = self.pretty_json_check.isChecked()
            
        elif format_type == "html":
            if not self.playlist:
                return
            data['playlist'] = self.playlist
            data['include_images'] = self.include_images_check.isChecked()
            
        elif format_type == "backup":
            if not self.tracks:
                return
            data['tracks'] = self.tracks
            data['include_files'] = self.include_files_check.isChecked()
        
        # Configurar UI para exportación
        self.export_button.setEnabled(False)
        self.cancel_button.setText("Cancelar")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.show()
        
        # Crear y configurar worker
        self._worker = ExportWorker(
            self.exporter,
            format_type,
            output_path,
            data
        )
        self._worker.progress.connect(self._update_progress)
        self._worker.finished.connect(self._export_finished)
        self._worker.start()
    
    def _update_progress(self, percentage: int, message: str) -> None:
        """Actualiza la barra de progreso."""
        self.progress_bar.setValue(percentage)
        self.progress_bar.setFormat(f"{percentage}% - {message}")
    
    def _export_finished(self, success: bool, message: str) -> None:
        """Maneja el fin de la exportación."""
        self._worker = None
        self.progress_bar.hide()
        self.export_button.setEnabled(True)
        self.cancel_button.setText("Cerrar")
        
        if success:
            QMessageBox.information(self, "Éxito", message)
            self.accept()
        else:
            QMessageBox.critical(self, "Error", message)
    
    def reject(self) -> None:
        """Maneja el cierre del diálogo."""
        if self._worker and self._worker.isRunning():
            # Cancelar exportación en curso
            reply = QMessageBox.question(
                self,
                "Cancelar exportación",
                "¿Está seguro de cancelar la exportación?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            )
            
            if reply == QMessageBox.StandardButton.Yes:
                self._worker.cancel()
                self._worker.wait()
                super().reject()
        else:
            super().reject()
