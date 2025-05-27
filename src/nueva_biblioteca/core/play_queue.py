#!/usr/bin/env python3
"""
Cola de Reproducción - Nueva Biblioteca
====================================

Sistema de cola y historial de reproducción con soporte para múltiples
modos de reproducción (normal, shuffle, repeat).
"""

import random
from collections import deque
from enum import Enum
from typing import Any, Optional

from PyQt6.QtCore import QObject, pyqtSignal

from nueva_biblioteca.data.models import Track
from nueva_biblioteca.utils.logger import get_logger

logger = get_logger(__name__)


class RepeatMode(Enum):
    """Modos de repetición."""
    NONE = "none"
    ONE = "one"
    ALL = "all"


class ShuffleMode(Enum):
    """Modos de aleatorio."""
    OFF = "off"
    ON = "on"


class PlayQueue(QObject):
    """
    Sistema de cola de reproducción con historial.
    
    Características:
    - Cola de reproducción con orden personalizable
    - Historial de tracks reproducidos
    - Modos de repetición (none, one, all)
    - Modo shuffle
    - Persistencia de estado
    """
    
    # Señales
    queue_changed = pyqtSignal()  # Cola modificada
    current_changed = pyqtSignal(Track)  # Track actual cambió
    mode_changed = pyqtSignal()  # Modo de reproducción cambió
    
    def __init__(self, max_history: int = 100):
        """
        Inicializa la cola de reproducción.
        
        Args:
            max_history: Máximo de tracks en el historial
        """
        super().__init__()
        
        # Cola principal
        self._queue: deque[Track] = deque()
        self._original_queue: list[Track] = []  # Para shuffle
        
        # Historial
        self._history: deque[Track] = deque(maxlen=max_history)
        
        # Estado actual
        self._current_index: int = -1
        self._current_track: Optional[Track] = None
        
        # Modos de reproducción
        self._repeat_mode = RepeatMode.NONE
        self._shuffle_mode = ShuffleMode.OFF
        
        # Estado de shuffle
        self._shuffle_indices: list[int] = []
        self._shuffle_position: int = -1
    
    def add_track(self, track: Track, position: Optional[int] = None) -> None:
        """
        Añade un track a la cola.
        
        Args:
            track: Track a añadir
            position: Posición específica (None = al final)
        """
        try:
            if position is None:
                self._queue.append(track)
                self._original_queue.append(track)
            else:
                # Insertar en posición específica
                queue_list = list(self._queue)
                queue_list.insert(position, track)
                self._queue = deque(queue_list)
                
                self._original_queue.insert(position, track)
            
            # Regenerar shuffle si está activo
            if self._shuffle_mode == ShuffleMode.ON:
                self._regenerate_shuffle()
            
            self.queue_changed.emit()
            logger.debug(f"Track añadido a la cola: {track.title}")
            
        except Exception as e:
            logger.error(f"Error añadiendo track a la cola: {e}")
    
    def add_tracks(self, tracks: list[Track], clear_first: bool = False) -> None:
        """
        Añade múltiples tracks a la cola.
        
        Args:
            tracks: Lista de tracks
            clear_first: Si limpiar la cola primero
        """
        try:
            if clear_first:
                self.clear()
            
            for track in tracks:
                self._queue.append(track)
                self._original_queue.append(track)
            
            # Regenerar shuffle si está activo
            if self._shuffle_mode == ShuffleMode.ON:
                self._regenerate_shuffle()
            
            self.queue_changed.emit()
            logger.info(f"{len(tracks)} tracks añadidos a la cola")
            
        except Exception as e:
            logger.error(f"Error añadiendo tracks a la cola: {e}")
    
    def remove_track(self, index: int) -> bool:
        """
        Elimina un track de la cola.
        
        Args:
            index: Índice del track a eliminar
            
        Returns:
            True si se eliminó correctamente
        """
        try:
            if 0 <= index < len(self._queue):
                queue_list = list(self._queue)
                removed_track = queue_list.pop(index)
                self._queue = deque(queue_list)
                
                # Eliminar de la cola original también
                if removed_track in self._original_queue:
                    self._original_queue.remove(removed_track)
                
                # Ajustar índice actual si es necesario
                if index <= self._current_index:
                    self._current_index -= 1
                
                # Regenerar shuffle si está activo
                if self._shuffle_mode == ShuffleMode.ON:
                    self._regenerate_shuffle()
                
                self.queue_changed.emit()
                logger.debug(f"Track eliminado de la cola: {removed_track.title}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error eliminando track de la cola: {e}")
            return False
    
    def move_track(self, from_index: int, to_index: int) -> bool:
        """
        Mueve un track a una nueva posición.
        
        Args:
            from_index: Índice origen
            to_index: Índice destino
            
        Returns:
            True si se movió correctamente
        """
        try:
            if (0 <= from_index < len(self._queue) and 
                0 <= to_index < len(self._queue)):
                
                queue_list = list(self._queue)
                track = queue_list.pop(from_index)
                queue_list.insert(to_index, track)
                self._queue = deque(queue_list)
                
                # Ajustar índice actual
                if from_index == self._current_index:
                    self._current_index = to_index
                elif from_index < self._current_index <= to_index:
                    self._current_index -= 1
                elif to_index <= self._current_index < from_index:
                    self._current_index += 1
                
                self.queue_changed.emit()
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error moviendo track en la cola: {e}")
            return False
    
    def clear(self) -> None:
        """Limpia la cola de reproducción."""
        self._queue.clear()
        self._original_queue.clear()
        self._current_index = -1
        self._current_track = None
        self._shuffle_indices.clear()
        self._shuffle_position = -1
        
        self.queue_changed.emit()
        logger.info("Cola de reproducción limpiada")
    
    def next_track(self) -> Optional[Track]:
        """
        Obtiene el siguiente track según el modo actual.
        
        Returns:
            Siguiente track o None si no hay más
        """
        try:
            if not self._queue:
                return None
            
            # Añadir track actual al historial si existe
            if self._current_track:
                self._add_to_history(self._current_track)
            
            next_track = None
            
            if self._shuffle_mode == ShuffleMode.ON:
                next_track = self._next_shuffle_track()
            else:
                next_track = self._next_normal_track()
            
            if next_track:
                self._current_track = next_track
                self.current_changed.emit(next_track)
                logger.debug(f"Siguiente track: {next_track.title}")
            
            return next_track
            
        except Exception as e:
            logger.error(f"Error obteniendo siguiente track: {e}")
            return None
    
    def previous_track(self) -> Optional[Track]:
        """
        Obtiene el track anterior del historial o cola.
        
        Returns:
            Track anterior o None si no hay
        """
        try:
            # Primero intentar del historial
            if self._history:
                previous = self._history.pop()
                self._current_track = previous
                self.current_changed.emit(previous)
                logger.debug(f"Track anterior del historial: {previous.title}")
                return previous
            
            # Si no hay historial, ir al track anterior en la cola
            if self._shuffle_mode == ShuffleMode.ON:
                return self._previous_shuffle_track()
            else:
                return self._previous_normal_track()
            
        except Exception as e:
            logger.error(f"Error obteniendo track anterior: {e}")
            return None
    
    def jump_to_track(self, index: int) -> Optional[Track]:
        """
        Salta a un track específico en la cola.
        
        Args:
            index: Índice del track
            
        Returns:
            Track seleccionado o None si índice inválido
        """
        try:
            if 0 <= index < len(self._queue):
                # Añadir track actual al historial
                if self._current_track:
                    self._add_to_history(self._current_track)
                
                track = list(self._queue)[index]
                self._current_index = index
                self._current_track = track
                
                # Ajustar posición de shuffle si está activo
                if self._shuffle_mode == ShuffleMode.ON:
                    try:
                        self._shuffle_position = self._shuffle_indices.index(index)
                    except ValueError:
                        # Si no está en shuffle, regenerar
                        self._regenerate_shuffle()
                
                self.current_changed.emit(track)
                logger.debug(f"Saltando a track: {track.title}")
                return track
            
            return None
            
        except Exception as e:
            logger.error(f"Error saltando a track: {e}")
            return None
    
    def set_repeat_mode(self, mode: RepeatMode) -> None:
        """
        Establece el modo de repetición.
        
        Args:
            mode: Nuevo modo de repetición
        """
        if self._repeat_mode != mode:
            self._repeat_mode = mode
            self.mode_changed.emit()
            logger.info(f"Modo de repetición cambiado a: {mode.value}")
    
    def set_shuffle_mode(self, mode: ShuffleMode) -> None:
        """
        Establece el modo shuffle.
        
        Args:
            mode: Nuevo modo shuffle
        """
        if self._shuffle_mode != mode:
            self._shuffle_mode = mode
            
            if mode == ShuffleMode.ON:
                self._regenerate_shuffle()
            else:
                self._shuffle_indices.clear()
                self._shuffle_position = -1
            
            self.mode_changed.emit()
            logger.info(f"Modo shuffle cambiado a: {mode.value}")
    
    def toggle_repeat(self) -> RepeatMode:
        """
        Alterna entre modos de repetición.
        
        Returns:
            Nuevo modo de repetición
        """
        modes = [RepeatMode.NONE, RepeatMode.ONE, RepeatMode.ALL]
        current_index = modes.index(self._repeat_mode)
        new_mode = modes[(current_index + 1) % len(modes)]
        self.set_repeat_mode(new_mode)
        return new_mode
    
    def toggle_shuffle(self) -> ShuffleMode:
        """
        Alterna el modo shuffle.
        
        Returns:
            Nuevo modo shuffle
        """
        new_mode = (ShuffleMode.ON if self._shuffle_mode == ShuffleMode.OFF 
                   else ShuffleMode.OFF)
        self.set_shuffle_mode(new_mode)
        return new_mode
    
    def _next_normal_track(self) -> Optional[Track]:
        """Obtiene el siguiente track en modo normal."""
        if self._repeat_mode == RepeatMode.ONE and self._current_track:
            return self._current_track
        
        next_index = self._current_index + 1
        
        if next_index < len(self._queue):
            self._current_index = next_index
            return list(self._queue)[next_index]
        elif self._repeat_mode == RepeatMode.ALL and self._queue:
            self._current_index = 0
            return list(self._queue)[0]
        
        return None
    
    def _previous_normal_track(self) -> Optional[Track]:
        """Obtiene el track anterior en modo normal."""
        if self._current_index > 0:
            self._current_index -= 1
            track = list(self._queue)[self._current_index]
            self._current_track = track
            self.current_changed.emit(track)
            return track
        elif self._repeat_mode == RepeatMode.ALL and self._queue:
            self._current_index = len(self._queue) - 1
            track = list(self._queue)[self._current_index]
            self._current_track = track
            self.current_changed.emit(track)
            return track
        
        return None
    
    def _next_shuffle_track(self) -> Optional[Track]:
        """Obtiene el siguiente track en modo shuffle."""
        if self._repeat_mode == RepeatMode.ONE and self._current_track:
            return self._current_track
        
        if not self._shuffle_indices:
            self._regenerate_shuffle()
        
        next_position = self._shuffle_position + 1
        
        if next_position < len(self._shuffle_indices):
            self._shuffle_position = next_position
            index = self._shuffle_indices[next_position]
            self._current_index = index
            return list(self._queue)[index]
        elif self._repeat_mode == RepeatMode.ALL and self._shuffle_indices:
            # Regenerar shuffle para evitar repetir el mismo orden
            self._regenerate_shuffle()
            self._shuffle_position = 0
            index = self._shuffle_indices[0]
            self._current_index = index
            return list(self._queue)[index]
        
        return None
    
    def _previous_shuffle_track(self) -> Optional[Track]:
        """Obtiene el track anterior en modo shuffle."""
        if self._shuffle_position > 0:
            self._shuffle_position -= 1
            index = self._shuffle_indices[self._shuffle_position]
            self._current_index = index
            track = list(self._queue)[index]
            self._current_track = track
            self.current_changed.emit(track)
            return track
        
        return None
    
    def _regenerate_shuffle(self) -> None:
        """Regenera los índices de shuffle."""
        if not self._queue:
            self._shuffle_indices.clear()
            self._shuffle_position = -1
            return
        
        # Crear lista de índices
        indices = list(range(len(self._queue)))
        
        # Mezclar evitando que el track actual sea el primero
        if self._current_index >= 0 and len(indices) > 1:
            # Remover índice actual temporalmente
            current = indices.pop(self._current_index)
            random.shuffle(indices)
            # Insertar en posición aleatoria que no sea la primera
            if indices:
                pos = random.randint(1, len(indices))
                indices.insert(pos, current)
            else:
                indices.append(current)
        else:
            random.shuffle(indices)
        
        self._shuffle_indices = indices
        
        # Encontrar posición actual en shuffle
        if self._current_index >= 0:
            try:
                self._shuffle_position = self._shuffle_indices.index(self._current_index)
            except ValueError:
                self._shuffle_position = -1
        else:
            self._shuffle_position = -1
    
    def _add_to_history(self, track: Track) -> None:
        """
        Añade un track al historial.
        
        Args:
            track: Track a añadir
        """
        # Evitar duplicados consecutivos
        if not self._history or self._history[-1].id != track.id:
            self._history.append(track)
    
    # Propiedades
    
    @property
    def queue(self) -> list[Track]:
        """Obtiene la cola actual como lista."""
        return list(self._queue)
    
    @property
    def history(self) -> list[Track]:
        """Obtiene el historial como lista."""
        return list(self._history)
    
    @property
    def current_track(self) -> Optional[Track]:
        """Obtiene el track actual."""
        return self._current_track
    
    @property
    def current_index(self) -> int:
        """Obtiene el índice actual en la cola."""
        return self._current_index
    
    @property
    def repeat_mode(self) -> RepeatMode:
        """Obtiene el modo de repetición actual."""
        return self._repeat_mode
    
    @property
    def shuffle_mode(self) -> ShuffleMode:
        """Obtiene el modo shuffle actual."""
        return self._shuffle_mode
    
    @property
    def is_empty(self) -> bool:
        """Verifica si la cola está vacía."""
        return len(self._queue) == 0
    
    @property
    def size(self) -> int:
        """Obtiene el tamaño de la cola."""
        return len(self._queue)
    
    def get_state(self) -> dict[str, Any]:
        """
        Obtiene el estado actual para persistencia.
        
        Returns:
            Diccionario con el estado
        """
        return {
            'queue': [track.id for track in self._queue],
            'current_index': self._current_index,
            'current_track_id': self._current_track.id if self._current_track else None,
            'repeat_mode': self._repeat_mode.value,
            'shuffle_mode': self._shuffle_mode.value,
            'history': [track.id for track in self._history]
        }
    
    def restore_state(self, state: dict[str, Any], track_lookup: dict[int, Track]) -> None:
        """
        Restaura el estado desde persistencia.
        
        Args:
            state: Estado guardado
            track_lookup: Diccionario para buscar tracks por ID
        """
        try:
            # Restaurar cola
            self._queue.clear()
            self._original_queue.clear()
            
            for track_id in state.get('queue', []):
                if track_id in track_lookup:
                    track = track_lookup[track_id]
                    self._queue.append(track)
                    self._original_queue.append(track)
            
            # Restaurar índice y track actual
            self._current_index = state.get('current_index', -1)
            current_track_id = state.get('current_track_id')
            if current_track_id and current_track_id in track_lookup:
                self._current_track = track_lookup[current_track_id]
            
            # Restaurar modos
            repeat_value = state.get('repeat_mode', RepeatMode.NONE.value)
            self._repeat_mode = RepeatMode(repeat_value)
            
            shuffle_value = state.get('shuffle_mode', ShuffleMode.OFF.value)
            self._shuffle_mode = ShuffleMode(shuffle_value)
            
            # Restaurar historial
            self._history.clear()
            for track_id in state.get('history', []):
                if track_id in track_lookup:
                    self._history.append(track_lookup[track_id])
            
            # Regenerar shuffle si está activo
            if self._shuffle_mode == ShuffleMode.ON:
                self._regenerate_shuffle()
            
            logger.info("Estado de cola restaurado correctamente")
            
        except Exception as e:
            logger.error(f"Error restaurando estado de cola: {e}")


# Instancia global
_play_queue: Optional[PlayQueue] = None


def get_play_queue() -> PlayQueue:
    """Obtiene la instancia global de la cola de reproducción."""
    global _play_queue
    if _play_queue is None:
        _play_queue = PlayQueue()
    return _play_queue 