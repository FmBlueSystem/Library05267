#!/usr/bin/env python3
"""
Reproductor de Audio - Nueva Biblioteca
====================================

Proporciona funcionalidad para reproducir archivos de audio usando QMediaPlayer
con soporte para crossfade y gestión de memoria optimizada.
"""

import logging
from enum import Enum
from pathlib import Path

from PyQt6.QtCore import QObject, QUrl, pyqtSignal
from PyQt6.QtMultimedia import QAudioOutput, QMediaPlayer

from nueva_biblioteca.utils.config import PlayerConfig, get_config


class PlayerState(Enum):
    """Estados posibles del reproductor."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"

class Player(QObject):
    """Reproductor de audio con funcionalidades avanzadas."""
    
    # Señales
    state_changed = pyqtSignal(PlayerState)
    position_changed = pyqtSignal(int)  # milisegundos
    duration_changed = pyqtSignal(int)  # milisegundos
    media_changed = pyqtSignal(str)  # ruta del archivo
    error_occurred = pyqtSignal(str)  # mensaje de error
    playback_finished = pyqtSignal()
    previous_requested = pyqtSignal()  # Solicitud de track anterior
    next_requested = pyqtSignal()  # Solicitud de siguiente track
    
    def __init__(self):
        """Inicializa el reproductor de audio."""
        super().__init__()
        
        # Configuración
        self.config: PlayerConfig = get_config().player
        
        # Player principal
        self._player = QMediaPlayer()
        self._audio_output = QAudioOutput()
        self._player.setAudioOutput(self._audio_output)
        
        # Player secundario para crossfade
        self._next_player = QMediaPlayer()
        self._next_audio_output = QAudioOutput()
        self._next_player.setAudioOutput(self._next_audio_output)
        
        # Estado
        self._current_file: str | None = None
        self._state = PlayerState.STOPPED
        self._volume = self.config.volume
        self._position = 0
        self._duration = 0
        
        # Crossfade
        self._crossfade_active = False
        self._crossfade_duration = self.config.crossfade_duration * 1000  # ms
        
        # Conectar señales
        self._setup_signals()
    
    def _setup_signals(self) -> None:
        """Configura las conexiones de señales."""
        # Player principal
        self._player.errorOccurred.connect(self._handle_error)
        self._player.positionChanged.connect(self._handle_position_change)
        self._player.durationChanged.connect(self._handle_duration_change)
        self._player.mediaStatusChanged.connect(self._handle_media_status)
        self._player.playbackStateChanged.connect(self._handle_playback_state_change)
        
        # Player secundario
        self._next_player.errorOccurred.connect(self._handle_error)
    
    def load(self, file_path: str) -> bool:
        """
        Carga un archivo de audio.
        
        Args:
            file_path: Ruta al archivo de audio.
            
        Returns:
            bool: True si se cargó correctamente.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                self.error_occurred.emit(f"Archivo no encontrado: {file_path}")
                return False
            
            # Detener reproducción actual si existe
            if self._state != PlayerState.STOPPED:
                self.stop()
            
            # Cargar nuevo archivo
            self._current_file = str(path)
            self._state = PlayerState.LOADING
            self.state_changed.emit(PlayerState.LOADING)
            
            url = QUrl.fromLocalFile(str(path))
            self._player.setSource(url)
            
            # Restaurar volumen
            self._audio_output.setVolume(self._volume)
            
            self.media_changed.emit(self._current_file)
            return True
            
        except Exception as e:
            logging.error(f"Error cargando archivo {file_path}: {e}")
            self.error_occurred.emit(str(e))
            return False
    
    def play(self, track=None) -> None:
        """
        Inicia o resume la reproducción.
        
        Args:
            track: Track a reproducir (opcional). Si se proporciona, se carga primero.
        """
        if track is not None:
            # Si se proporciona un track, cargarlo primero
            if hasattr(track, 'file_path'):
                if not self.load(track.file_path):
                    return
            else:
                # Si track es una string (ruta de archivo)
                if not self.load(str(track)):
                    return
        
        if self._state in [PlayerState.STOPPED, PlayerState.PAUSED, PlayerState.LOADING]:
            self._player.play()
            # El estado se actualizará en _handle_playback_state_change
    
    def pause(self) -> None:
        """Pausa la reproducción."""
        if self._state == PlayerState.PLAYING:
            self._player.pause()
            # El estado se actualizará en _handle_playback_state_change
    
    def stop(self) -> None:
        """Detiene la reproducción."""
        self._player.stop()
        # El estado se actualizará en _handle_playback_state_change
    
    def seek(self, position: int) -> None:
        """
        Busca una posición específica en milisegundos.
        
        Args:
            position: Posición en milisegundos.
        """
        if self._duration > 0:
            position = max(0, min(position, self._duration))
            self._player.setPosition(position)
    
    def set_volume(self, volume: float) -> None:
        """
        Establece el volumen de reproducción.
        
        Args:
            volume: Volumen entre 0.0 y 1.0
        """
        volume = max(0.0, min(volume, 1.0))
        self._volume = volume
        self._audio_output.setVolume(volume)
        
        # Si hay crossfade activo, ajustar volumen secundario
        if self._crossfade_active:
            self._next_audio_output.setVolume(volume)
    
    def previous(self) -> None:
        """Solicita reproducir el track anterior."""
        self.previous_requested.emit()
    
    def next(self) -> None:
        """Solicita reproducir el siguiente track."""
        self.next_requested.emit()
    
    def get_next_track_from_queue(self) -> str | None:
        """
        Obtiene el siguiente track de la cola de reproducción.
        
        Returns:
            Ruta del siguiente track o None
        """
        from nueva_biblioteca.core.play_queue import get_play_queue
        
        queue = get_play_queue()
        next_track = queue.next_track()
        return next_track.file_path if next_track else None
    
    def get_previous_track_from_queue(self) -> str | None:
        """
        Obtiene el track anterior de la cola de reproducción.
        
        Returns:
            Ruta del track anterior o None
        """
        from nueva_biblioteca.core.play_queue import get_play_queue
        
        queue = get_play_queue()
        previous_track = queue.previous_track()
        return previous_track.file_path if previous_track else None
    
    def prepare_next(self, file_path: str) -> bool:
        """
        Prepara el siguiente archivo para crossfade.
        
        Args:
            file_path: Ruta al siguiente archivo.
            
        Returns:
            bool: True si se preparó correctamente.
        """
        if not self.config.enable_crossfade:
            return False
        
        try:
            path = Path(file_path)
            if not path.exists():
                return False
            
            url = QUrl.fromLocalFile(str(path))
            self._next_player.setSource(url)
            self._next_audio_output.setVolume(0)  # Iniciar silenciado
            return True
            
        except Exception as e:
            logging.error(f"Error preparando siguiente archivo: {e}")
            return False
    
    def _handle_error(self, error: str) -> None:
        """Maneja errores del reproductor."""
        self._state = PlayerState.ERROR
        self.error_occurred.emit(str(error))
        self.state_changed.emit(PlayerState.ERROR)
    
    def _handle_position_change(self, position: int) -> None:
        """Maneja cambios en la posición de reproducción."""
        self._position = position
        self.position_changed.emit(position)
        
        # Manejar crossfade si está habilitado
        if (self.config.enable_crossfade and 
            self._duration > 0 and 
            position >= self._duration - self._crossfade_duration):
            self._start_crossfade()
    
    def _handle_duration_change(self, duration: int) -> None:
        """Maneja cambios en la duración del archivo."""
        self._duration = duration
        self.duration_changed.emit(duration)
    
    def _handle_media_status(self, status) -> None:
        """Maneja cambios en el estado del archivo."""
        from PyQt6.QtMultimedia import QMediaPlayer
        
        if status == QMediaPlayer.MediaStatus.LoadedMedia:
            # Archivo cargado correctamente
            if self._state == PlayerState.LOADING:
                self._state = PlayerState.STOPPED
                self.state_changed.emit(PlayerState.STOPPED)
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            if not self._crossfade_active:
                self.playback_finished.emit()
                # Auto-reproducir siguiente track de la cola
                self._auto_play_next()
    
    def _handle_playback_state_change(self, state) -> None:
        """Maneja cambios en el estado de reproducción."""
        from PyQt6.QtMultimedia import QMediaPlayer
        
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self._state = PlayerState.PLAYING
            self.state_changed.emit(PlayerState.PLAYING)
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self._state = PlayerState.PAUSED
            self.state_changed.emit(PlayerState.PAUSED)
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self._state = PlayerState.STOPPED
            self._position = 0
            self.position_changed.emit(0)
            self.state_changed.emit(PlayerState.STOPPED)
    
    def _start_crossfade(self) -> None:
        """Inicia el crossfade al siguiente archivo."""
        if not self._crossfade_active and self._next_player.source().isValid():
            self._crossfade_active = True
            
            # Iniciar reproducción del siguiente archivo
            self._next_player.play()
            
            # Realizar fade out/in
            self._fade_out(self._player, self._audio_output)
            self._fade_in(self._next_player, self._next_audio_output)
    
    def _fade_out(self, player: QMediaPlayer, output: QAudioOutput) -> None:
        """Realiza un fade out gradual."""
        # TODO: Implementar fade out gradual usando QTimeLine
    
    def _fade_in(self, player: QMediaPlayer, output: QAudioOutput) -> None:
        """Realiza un fade in gradual."""
        # TODO: Implementar fade in gradual usando QTimeLine
    
    def _auto_play_next(self) -> None:
        """Reproduce automáticamente el siguiente track de la cola."""
        try:
            next_file = self.get_next_track_from_queue()
            if next_file:
                self.load(next_file)
                self.play()
        except Exception as e:
            logging.error(f"Error en auto-reproducción: {e}")
    
    @property
    def state(self) -> PlayerState:
        """Obtiene el estado actual del reproductor."""
        return self._state
    
    @property
    def position(self) -> int:
        """Obtiene la posición actual en milisegundos."""
        return self._position
    
    @property
    def duration(self) -> int:
        """Obtiene la duración total en milisegundos."""
        return self._duration
    
    @property
    def current_file(self) -> str | None:
        """Obtiene el archivo actual en reproducción."""
        return self._current_file
    
    @property
    def volume(self) -> float:
        """Retorna el volumen actual."""
        return self._volume
    
    def cleanup(self) -> None:
        """Limpia recursos del reproductor."""
        self.stop()
        self._player.deleteLater()
        self._next_player.deleteLater()
