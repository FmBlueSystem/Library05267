#!/usr/bin/env python3
"""
Controles de Reproducción - Nueva Biblioteca
====================================

Controles de reproducción con estilo Material Design 3.
"""


from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QHBoxLayout, QLabel, QSlider, QVBoxLayout, QWidget

from nueva_biblioteca.core.player import Player, PlayerState
from nueva_biblioteca.data.models import Track
from nueva_biblioteca.ui.theme import get_theme
from nueva_biblioteca.ui.widgets.md3_widgets import MD3Button, MD3Card


class PlayerControls(MD3Card):
    """Controles de reproducción con estilo Material Design 3."""
    
    def __init__(self, parent: QWidget | None = None):
        """
        Inicializa los controles.
        
        Args:
            parent: Widget padre
        """
        super().__init__(parent, elevation=2)
        
        self.theme = get_theme()
        self.player = Player()
        self.current_track: Track | None = None
        self._duration = 0
        
        self._setup_ui()
        self._connect_signals()
        
        # Timer para actualizar progreso
        self.update_timer = QTimer()
        self.update_timer.setInterval(1000)  # 1 segundo
        self.update_timer.timeout.connect(self._update_progress)
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        # Layout principal
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(16)
        
        # Info del track actual
        track_info = QWidget()
        track_layout = QVBoxLayout(track_info)
        track_layout.setContentsMargins(0, 0, 0, 0)
        
        self.title_label = QLabel("Sin reproducción")
        self.title_label.setFont(self.theme.typography.TITLE_MEDIUM)
        
        self.artist_label = QLabel("-")
        self.artist_label.setFont(self.theme.typography.BODY_MEDIUM)
        self.artist_label.setStyleSheet(f"""
            color: {self.theme.colors.ON_SURFACE_VARIANT};
        """)
        
        track_layout.addWidget(self.title_label)
        track_layout.addWidget(self.artist_label)
        
        layout.addWidget(track_info, stretch=1)
        
        # Controles de reproducción
        controls = QWidget()
        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)
        controls_layout.setSpacing(8)
        
        # Botones principales
        self.prev_button = MD3Button(variant="text")
        self.prev_button.setIcon(QIcon("icons/prev.svg"))
        self.prev_button.setFixedSize(40, 40)
        
        self.play_button = MD3Button(variant="filled")
        self.play_button.setIcon(QIcon("icons/play.svg"))
        self.play_button.setFixedSize(48, 48)
        
        self.next_button = MD3Button(variant="text")
        self.next_button.setIcon(QIcon("icons/next.svg"))
        self.next_button.setFixedSize(40, 40)
        
        # Botones de modo
        self.shuffle_button = MD3Button(variant="text")
        self.shuffle_button.setIcon(QIcon("icons/shuffle.svg"))
        self.shuffle_button.setFixedSize(40, 40)
        self.shuffle_button.setCheckable(True)
        self.shuffle_button.setToolTip("Aleatorio")
        
        self.repeat_button = MD3Button(variant="text")
        self.repeat_button.setIcon(QIcon("icons/repeat.svg"))
        self.repeat_button.setFixedSize(40, 40)
        self.repeat_button.setToolTip("Repetir")
        
        controls_layout.addWidget(self.shuffle_button)
        controls_layout.addWidget(self.prev_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.next_button)
        controls_layout.addWidget(self.repeat_button)
        controls_layout.addStretch()
        
        layout.addWidget(controls)
        
        # Controles secundarios
        secondary = QWidget()
        secondary_layout = QVBoxLayout(secondary)
        secondary_layout.setContentsMargins(0, 0, 0, 0)
        
        # Progreso y tiempo
        progress = QWidget()
        progress_layout = QHBoxLayout(progress)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        self.time_label = QLabel("0:00")
        self.time_label.setFont(self.theme.typography.BODY_SMALL)
        self.time_label.setStyleSheet(f"""
            color: {self.theme.colors.ON_SURFACE_VARIANT};
        """)
        
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setRange(0, 1000)
        self.progress_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {self.theme.colors.SURFACE_VARIANT};
                height: 4px;
                border-radius: 2px;
            }}
            
            QSlider::sub-page:horizontal {{
                background: {self.theme.colors.PRIMARY};
                border-radius: 2px;
            }}
            
            QSlider::handle:horizontal {{
                background: {self.theme.colors.PRIMARY};
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            
            QSlider::handle:horizontal:hover {{
                background: {self.theme.colors.PRIMARY};
                border: 2px solid {self.theme.colors.ON_PRIMARY};
            }}
        """)
        
        self.duration_label = QLabel("0:00")
        self.duration_label.setFont(self.theme.typography.BODY_SMALL)
        self.duration_label.setStyleSheet(f"""
            color: {self.theme.colors.ON_SURFACE_VARIANT};
        """)
        
        progress_layout.addWidget(self.time_label)
        progress_layout.addWidget(self.progress_slider, stretch=1)
        progress_layout.addWidget(self.duration_label)
        
        # Controles de volumen
        volume = QWidget()
        volume_layout = QHBoxLayout(volume)
        volume_layout.setContentsMargins(0, 0, 0, 0)
        
        self.volume_button = MD3Button(variant="text")
        self.volume_button.setIcon(QIcon("icons/volume.svg"))
        self.volume_button.setFixedSize(32, 32)
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(100)
        self.volume_slider.setStyleSheet(f"""
            QSlider::groove:horizontal {{
                background: {self.theme.colors.SURFACE_VARIANT};
                height: 4px;
                border-radius: 2px;
            }}
            
            QSlider::sub-page:horizontal {{
                background: {self.theme.colors.SECONDARY};
                border-radius: 2px;
            }}
            
            QSlider::handle:horizontal {{
                background: {self.theme.colors.SECONDARY};
                width: 16px;
                margin: -6px 0;
                border-radius: 8px;
            }}
        """)
        
        volume_layout.addWidget(self.volume_button)
        volume_layout.addWidget(self.volume_slider)
        
        secondary_layout.addWidget(progress)
        secondary_layout.addWidget(volume)
        
        layout.addWidget(secondary, stretch=1)
    
    def _connect_signals(self) -> None:
        """Conecta las señales de los controles."""
        # Botones
        self.play_button.clicked.connect(self._toggle_playback)
        self.prev_button.clicked.connect(self._handle_previous)
        self.next_button.clicked.connect(self._handle_next)
        self.shuffle_button.clicked.connect(self._toggle_shuffle)
        self.repeat_button.clicked.connect(self._toggle_repeat)
        
        # Progreso
        self.progress_slider.sliderMoved.connect(self._seek)
        self.progress_slider.sliderPressed.connect(self._on_slider_pressed)
        self.progress_slider.sliderReleased.connect(self._on_slider_released)
        
        # Volumen
        self.volume_slider.valueChanged.connect(self._set_volume)
        self.volume_button.clicked.connect(self._toggle_mute)
        
        # Player
        self.player.state_changed.connect(self._update_play_button)
        self.player.position_changed.connect(self._update_position)
        self.player.duration_changed.connect(self._update_duration)
        self.player.media_changed.connect(self._update_track_info)
        
        # Cola de reproducción
        from nueva_biblioteca.core.play_queue import get_play_queue
        self.queue = get_play_queue()
        self.queue.current_changed.connect(self._on_queue_track_changed)
        self.queue.mode_changed.connect(self._update_mode_buttons)
    
    def play_track(self, track: Track) -> None:
        """
        Reproduce un track.
        
        Args:
            track: Track a reproducir
        """
        self.current_track = track
        
        # Añadir a la cola si no está ya
        if track not in self.queue.queue:
            self.queue.add_track(track)
        
        # Saltar a este track en la cola
        track_index = self.queue.queue.index(track)
        self.queue.jump_to_track(track_index)
        
        if self.player.load(track.file_path):
            self.player.play()
            self.update_timer.start()
        self._update_track_info()
    
    def _toggle_playback(self) -> None:
        """Alterna reproducción/pausa."""
        if not self.current_track:
            return
            
        if self.player.state == PlayerState.PLAYING:
            self.player.pause()
        else:
            self.player.play()
    
    def _seek(self, position: int) -> None:
        """
        Busca una posición.
        
        Args:
            position: Posición del slider (0-1000)
        """
        if not self.current_track or self._duration == 0:
            return
            
        # Convertir posición del slider a milisegundos
        ms_position = int((position / 1000.0) * self._duration)
        self.player.seek(ms_position)
    
    def _set_volume(self, volume: int) -> None:
        """
        Establece el volumen.
        
        Args:
            volume: Volumen (0-100)
        """
        self.player.set_volume(volume / 100.0)
        
        # Actualizar icono
        if volume == 0:
            self.volume_button.setIcon(QIcon("icons/volume_mute.svg"))
        elif volume < 50:
            self.volume_button.setIcon(QIcon("icons/volume_low.svg"))
        else:
            self.volume_button.setIcon(QIcon("icons/volume.svg"))
    
    def _toggle_mute(self) -> None:
        """Alterna silencio."""
        if self.volume_slider.value() == 0:
            self.volume_slider.setValue(100)
        else:
            self.volume_slider.setValue(0)
    
    def _handle_previous(self) -> None:
        """Maneja el botón anterior."""
        previous_file = self.player.get_previous_track_from_queue()
        if previous_file:
            self.player.load(previous_file)
            self.player.play()
    
    def _handle_next(self) -> None:
        """Maneja el botón siguiente."""
        next_file = self.player.get_next_track_from_queue()
        if next_file:
            self.player.load(next_file)
            self.player.play()
    
    def _toggle_shuffle(self) -> None:
        """Alterna el modo shuffle."""
        self.queue.toggle_shuffle()
    
    def _toggle_repeat(self) -> None:
        """Alterna el modo repeat."""
        self.queue.toggle_repeat()
    
    def _on_queue_track_changed(self, track: Track) -> None:
        """
        Maneja cambio de track en la cola.
        
        Args:
            track: Nuevo track actual
        """
        self.current_track = track
        self._update_track_info()
    
    def _update_mode_buttons(self) -> None:
        """Actualiza el estado de los botones de modo."""
        from nueva_biblioteca.core.play_queue import RepeatMode, ShuffleMode
        
        # Shuffle
        self.shuffle_button.setChecked(self.queue.shuffle_mode == ShuffleMode.ON)
        
        # Repeat
        repeat_mode = self.queue.repeat_mode
        if repeat_mode == RepeatMode.NONE:
            self.repeat_button.setIcon(QIcon("icons/repeat.svg"))
            self.repeat_button.setChecked(False)
            self.repeat_button.setToolTip("Repetir")
        elif repeat_mode == RepeatMode.ONE:
            self.repeat_button.setIcon(QIcon("icons/repeat_one.svg"))
            self.repeat_button.setChecked(True)
            self.repeat_button.setToolTip("Repetir uno")
        elif repeat_mode == RepeatMode.ALL:
            self.repeat_button.setIcon(QIcon("icons/repeat.svg"))
            self.repeat_button.setChecked(True)
            self.repeat_button.setToolTip("Repetir todo")
    
    def _update_progress(self) -> None:
        """Actualiza la barra de progreso."""
        if not self.current_track or self.player.state != PlayerState.PLAYING:
            return
            
        position = self.player.position
        duration = self.player.duration
        
        if duration > 0:
            value = int((position / duration) * 1000)
            self.progress_slider.setValue(value)
            
            self.time_label.setText(self._format_time(position / 1000))
            self.duration_label.setText(self._format_time(duration / 1000))
    
    def _update_position(self, position: int) -> None:
        """
        Actualiza la posición del reproductor.
        
        Args:
            position: Posición en milisegundos
        """
        if self._duration > 0:
            value = int((position / self._duration) * 1000)
            self.progress_slider.setValue(value)
            
            self.time_label.setText(self._format_time(position / 1000))
    
    def _update_duration(self, duration: int) -> None:
        """
        Actualiza la duración del track.
        
        Args:
            duration: Duración en milisegundos
        """
        self._duration = duration
        self.progress_slider.setRange(0, 1000)
        self.duration_label.setText(self._format_time(duration / 1000))
    
    def _update_play_button(self, state: PlayerState) -> None:
        """
        Actualiza el botón de reproducción.
        
        Args:
            state: Estado del reproductor
        """
        is_playing = state == PlayerState.PLAYING
        self.play_button.setIcon(
            QIcon("icons/pause.svg" if is_playing else "icons/play.svg")
        )
    
    def _update_track_info(self) -> None:
        """Actualiza la información del track."""
        if self.current_track:
            self.title_label.setText(self.current_track.title or "Sin título")
            self.artist_label.setText(self.current_track.artist or "Desconocido")
        else:
            self.title_label.setText("Sin reproducción")
            self.artist_label.setText("-")
    
    def _on_slider_pressed(self) -> None:
        """Maneja el inicio de arrastre del slider."""
        self.update_timer.stop()
    
    def _on_slider_released(self) -> None:
        """Maneja el fin de arrastre del slider."""
        self.update_timer.start()
    
    @staticmethod
    def _format_time(seconds: float) -> str:
        """
        Formatea un tiempo en segundos.
        
        Args:
            seconds: Tiempo en segundos
            
        Returns:
            Tiempo formateado
        """
        minutes = int(seconds // 60)
        seconds = int(seconds % 60)
        return f"{minutes}:{seconds:02d}"
