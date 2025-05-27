#!/usr/bin/env python3
"""
Widget de Cola de Reproducción - Nueva Biblioteca
====================================

Widget para mostrar y gestionar la cola de reproducción con
interfaz Material Design 3.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QDragEnterEvent, QDropEvent, QIcon
from PyQt6.QtWidgets import (
    QAbstractItemView, QHBoxLayout, QHeaderView, QLabel, QMenu, 
    QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget
)

from nueva_biblioteca.core.play_queue import RepeatMode, ShuffleMode, get_play_queue
from nueva_biblioteca.data.models import Track
from nueva_biblioteca.ui.theme import get_theme
from nueva_biblioteca.ui.widgets.md3_widgets import MD3Button, MD3Card
from nueva_biblioteca.utils.logger import get_logger

logger = get_logger(__name__)


class QueueWidget(QWidget):
    """Widget para mostrar y gestionar la cola de reproducción."""
    
    # Señales
    track_selected = pyqtSignal(Track)
    track_double_clicked = pyqtSignal(Track)
    
    def __init__(self, parent=None):
        """
        Inicializa el widget de cola.
        
        Args:
            parent: Widget padre
        """
        super().__init__(parent)
        
        self.theme = get_theme()
        self.queue = get_play_queue()
        
        self._setup_ui()
        self._connect_signals()
        self._update_queue_display()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Encabezado
        header_card = MD3Card(elevation=1)
        header_layout = QVBoxLayout(header_card)
        
        # Título
        title_label = QLabel("Cola de Reproducción")
        title_label.setStyleSheet(f"""
            QLabel {{
                font-size: 20px;
                font-weight: 600;
                color: {self.theme.colors.ON_SURFACE};
                margin: 8px 0;
            }}
        """)
        header_layout.addWidget(title_label)
        
        # Controles
        controls_layout = QHBoxLayout()
        
        # Botón shuffle
        self.shuffle_button = MD3Button(variant="outlined")
        self.shuffle_button.setText("🔀")
        self.shuffle_button.setFixedSize(40, 40)
        self.shuffle_button.setToolTip("Aleatorio")
        
        # Botón repeat
        self.repeat_button = MD3Button(variant="outlined")
        self.repeat_button.setText("🔁")
        self.repeat_button.setFixedSize(40, 40)
        self.repeat_button.setToolTip("Repetir")
        
        # Botón limpiar
        self.clear_button = MD3Button(variant="outlined")
        self.clear_button.setText("🗑️")
        self.clear_button.setFixedSize(40, 40)
        self.clear_button.setToolTip("Limpiar cola")
        
        # Info de la cola
        self.queue_info = QLabel("0 tracks")
        self.queue_info.setStyleSheet(f"""
            QLabel {{
                color: {self.theme.colors.ON_SURFACE_VARIANT};
                font-size: 14px;
            }}
        """)
        
        controls_layout.addWidget(self.shuffle_button)
        controls_layout.addWidget(self.repeat_button)
        controls_layout.addWidget(self.clear_button)
        controls_layout.addStretch()
        controls_layout.addWidget(self.queue_info)
        
        header_layout.addLayout(controls_layout)
        layout.addWidget(header_card)
        
        # Tabla de tracks
        table_card = MD3Card(elevation=1)
        table_layout = QVBoxLayout(table_card)
        
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["#", "Título", "Artista", "Duración"])
        
        # Configurar tabla
        self.table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.table.setAlternatingRowColors(True)
        self.table.setDragDropMode(QAbstractItemView.DragDropMode.InternalMove)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        
        # Configurar encabezados
        header = self.table.horizontalHeader()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)  # #
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)  # Título
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Artista
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)  # Duración
        
        # Anchos fijos
        self.table.setColumnWidth(0, 50)
        self.table.setColumnWidth(3, 80)
        
        # Estilo de la tabla
        self.table.setStyleSheet(f"""
            QTableWidget {{
                background-color: {self.theme.colors.SURFACE};
                border: none;
                gridline-color: {self.theme.colors.OUTLINE_VARIANT};
                selection-background-color: {self.theme.colors.PRIMARY_CONTAINER};
                selection-color: {self.theme.colors.ON_PRIMARY_CONTAINER};
            }}
            QTableWidget::item {{
                padding: 8px;
                border-bottom: 1px solid {self.theme.colors.OUTLINE_VARIANT};
            }}
            QTableWidget::item:selected {{
                background-color: {self.theme.colors.PRIMARY_CONTAINER};
                color: {self.theme.colors.ON_PRIMARY_CONTAINER};
            }}
            QHeaderView::section {{
                background-color: {self.theme.colors.SURFACE_VARIANT};
                color: {self.theme.colors.ON_SURFACE_VARIANT};
                padding: 8px;
                border: none;
                border-bottom: 2px solid {self.theme.colors.PRIMARY};
                font-weight: 600;
            }}
        """)
        
        table_layout.addWidget(self.table)
        layout.addWidget(table_card)
        
        # Aplicar tema
        self.theme.apply_to_widget(self)
    
    def _connect_signals(self) -> None:
        """Conecta las señales."""
        # Botones
        self.shuffle_button.clicked.connect(self._toggle_shuffle)
        self.repeat_button.clicked.connect(self._toggle_repeat)
        self.clear_button.clicked.connect(self._clear_queue)
        
        # Tabla
        self.table.itemSelectionChanged.connect(self._on_selection_changed)
        self.table.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.table.customContextMenuRequested.connect(self._show_context_menu)
        
        # Cola de reproducción
        self.queue.queue_changed.connect(self._update_queue_display)
        self.queue.current_changed.connect(self._update_current_track)
        self.queue.mode_changed.connect(self._update_mode_buttons)
    
    def _update_queue_display(self) -> None:
        """Actualiza la visualización de la cola."""
        try:
            tracks = self.queue.queue
            self.table.setRowCount(len(tracks))
            
            for row, track in enumerate(tracks):
                # Número de posición
                pos_item = QTableWidgetItem(str(row + 1))
                pos_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                pos_item.setFlags(pos_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 0, pos_item)
                
                # Título
                title_item = QTableWidgetItem(track.title or "Sin título")
                title_item.setFlags(title_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                title_item.setData(Qt.ItemDataRole.UserRole, track)
                self.table.setItem(row, 1, title_item)
                
                # Artista
                artist_item = QTableWidgetItem(track.artist or "Artista desconocido")
                artist_item.setFlags(artist_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 2, artist_item)
                
                # Duración
                duration = self._format_duration(track.duration)
                duration_item = QTableWidgetItem(duration)
                duration_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                duration_item.setFlags(duration_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                self.table.setItem(row, 3, duration_item)
            
            # Actualizar info
            self.queue_info.setText(f"{len(tracks)} tracks")
            
            # Marcar track actual
            self._update_current_track(self.queue.current_track)
            
        except Exception as e:
            logger.error(f"Error actualizando visualización de cola: {e}")
    
    def _update_current_track(self, track: Track) -> None:
        """
        Actualiza la marca del track actual.
        
        Args:
            track: Track actual
        """
        try:
            # Limpiar marcas anteriores
            for row in range(self.table.rowCount()):
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    if item:
                        font = item.font()
                        font.setBold(False)
                        item.setFont(font)
            
            # Marcar track actual
            if track:
                tracks = self.queue.queue
                for row, queue_track in enumerate(tracks):
                    if queue_track.id == track.id:
                        for col in range(self.table.columnCount()):
                            item = self.table.item(row, col)
                            if item:
                                font = item.font()
                                font.setBold(True)
                                item.setFont(font)
                        break
                        
        except Exception as e:
            logger.error(f"Error actualizando track actual: {e}")
    
    def _update_mode_buttons(self) -> None:
        """Actualiza el estado de los botones de modo."""
        try:
            # Botón shuffle
            if self.queue.shuffle_mode == ShuffleMode.ON:
                self.shuffle_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.theme.colors.PRIMARY};
                        color: {self.theme.colors.ON_PRIMARY};
                    }}
                """)
            else:
                self.shuffle_button.setStyleSheet("")
            
            # Botón repeat
            repeat_text = "🔁"
            if self.queue.repeat_mode == RepeatMode.ONE:
                repeat_text = "🔂"
                self.repeat_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.theme.colors.PRIMARY};
                        color: {self.theme.colors.ON_PRIMARY};
                    }}
                """)
            elif self.queue.repeat_mode == RepeatMode.ALL:
                repeat_text = "🔁"
                self.repeat_button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: {self.theme.colors.PRIMARY};
                        color: {self.theme.colors.ON_PRIMARY};
                    }}
                """)
            else:
                self.repeat_button.setStyleSheet("")
            
            self.repeat_button.setText(repeat_text)
            
        except Exception as e:
            logger.error(f"Error actualizando botones de modo: {e}")
    
    def _toggle_shuffle(self) -> None:
        """Alterna el modo shuffle."""
        try:
            self.queue.toggle_shuffle()
        except Exception as e:
            logger.error(f"Error alternando shuffle: {e}")
    
    def _toggle_repeat(self) -> None:
        """Alterna el modo repeat."""
        try:
            self.queue.toggle_repeat()
        except Exception as e:
            logger.error(f"Error alternando repeat: {e}")
    
    def _clear_queue(self) -> None:
        """Limpia la cola de reproducción."""
        try:
            self.queue.clear()
        except Exception as e:
            logger.error(f"Error limpiando cola: {e}")
    
    def _on_selection_changed(self) -> None:
        """Maneja cambios en la selección."""
        try:
            current_row = self.table.currentRow()
            if current_row >= 0:
                title_item = self.table.item(current_row, 1)
                if title_item:
                    track = title_item.data(Qt.ItemDataRole.UserRole)
                    if track:
                        self.track_selected.emit(track)
        except Exception as e:
            logger.error(f"Error en selección: {e}")
    
    def _on_item_double_clicked(self, item: QTableWidgetItem) -> None:
        """
        Maneja doble clic en un item.
        
        Args:
            item: Item clickeado
        """
        try:
            row = item.row()
            title_item = self.table.item(row, 1)
            if title_item:
                track = title_item.data(Qt.ItemDataRole.UserRole)
                if track:
                    # Saltar a este track en la cola
                    self.queue.jump_to_track(row)
                    self.track_double_clicked.emit(track)
        except Exception as e:
            logger.error(f"Error en doble clic: {e}")
    
    def _show_context_menu(self, position) -> None:
        """
        Muestra el menú contextual.
        
        Args:
            position: Posición del menú
        """
        try:
            item = self.table.itemAt(position)
            if not item:
                return
            
            row = item.row()
            title_item = self.table.item(row, 1)
            if not title_item:
                return
            
            track = title_item.data(Qt.ItemDataRole.UserRole)
            if not track:
                return
            
            menu = QMenu(self)
            
            # Reproducir
            play_action = QAction("▶️ Reproducir", self)
            play_action.triggered.connect(
                lambda: self._play_track(row, track)
            )
            menu.addAction(play_action)
            
            menu.addSeparator()
            
            # Mover arriba
            if row > 0:
                move_up_action = QAction("⬆️ Mover arriba", self)
                move_up_action.triggered.connect(
                    lambda: self._move_track(row, row - 1)
                )
                menu.addAction(move_up_action)
            
            # Mover abajo
            if row < self.table.rowCount() - 1:
                move_down_action = QAction("⬇️ Mover abajo", self)
                move_down_action.triggered.connect(
                    lambda: self._move_track(row, row + 1)
                )
                menu.addAction(move_down_action)
            
            menu.addSeparator()
            
            # Eliminar
            remove_action = QAction("🗑️ Eliminar de la cola", self)
            remove_action.triggered.connect(
                lambda: self._remove_track(row)
            )
            menu.addAction(remove_action)
            
            menu.exec(self.table.mapToGlobal(position))
            
        except Exception as e:
            logger.error(f"Error mostrando menú contextual: {e}")
    
    def _play_track(self, row: int, track: Track) -> None:
        """
        Reproduce un track específico.
        
        Args:
            row: Fila del track
            track: Track a reproducir
        """
        try:
            self.queue.jump_to_track(row)
            self.track_double_clicked.emit(track)
        except Exception as e:
            logger.error(f"Error reproduciendo track: {e}")
    
    def _move_track(self, from_row: int, to_row: int) -> None:
        """
        Mueve un track a una nueva posición.
        
        Args:
            from_row: Fila origen
            to_row: Fila destino
        """
        try:
            self.queue.move_track(from_row, to_row)
        except Exception as e:
            logger.error(f"Error moviendo track: {e}")
    
    def _remove_track(self, row: int) -> None:
        """
        Elimina un track de la cola.
        
        Args:
            row: Fila del track a eliminar
        """
        try:
            self.queue.remove_track(row)
        except Exception as e:
            logger.error(f"Error eliminando track: {e}")
    
    def _format_duration(self, duration: int | float | None) -> str:
        """
        Formatea la duración en formato mm:ss.
        
        Args:
            duration: Duración en segundos
            
        Returns:
            Duración formateada
        """
        if not duration:
            return "--:--"
        
        duration = int(duration)  # Convertir a entero
        minutes = duration // 60
        seconds = duration % 60
        return f"{minutes:02d}:{seconds:02d}"
    
    # Métodos públicos
    
    def add_track(self, track: Track) -> None:
        """
        Añade un track a la cola.
        
        Args:
            track: Track a añadir
        """
        self.queue.add_track(track)
    
    def add_tracks(self, tracks: list[Track], clear_first: bool = False) -> None:
        """
        Añade múltiples tracks a la cola.
        
        Args:
            tracks: Lista de tracks
            clear_first: Si limpiar la cola primero
        """
        self.queue.add_tracks(tracks, clear_first)
    
    def get_selected_track(self) -> Track | None:
        """
        Obtiene el track seleccionado.
        
        Returns:
            Track seleccionado o None
        """
        current_row = self.table.currentRow()
        if current_row >= 0:
            title_item = self.table.item(current_row, 1)
            if title_item:
                return title_item.data(Qt.ItemDataRole.UserRole)
        return None 