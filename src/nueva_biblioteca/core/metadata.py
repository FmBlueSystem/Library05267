#!/usr/bin/env python3
"""
Gestor de Metadatos - Nueva Biblioteca
====================================

Proporciona funcionalidades para extraer y gestionar metadatos de archivos de audio
usando mutagen y otras bibliotecas especializadas.
"""

import contextlib
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import ClassVar

import mutagen
from mutagen.easyid3 import EasyID3
from mutagen.flac import FLAC
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4


@dataclass
class AudioMetadata:
    """Representa los metadatos de un archivo de audio."""
    # Información básica
    title: str = ""
    artist: str = ""
    album: str = ""
    year: int | None = None
    genre: list[str] = None
    track_number: int | None = None
    disc_number: int | None = None
    
    # Información técnica
    duration: float = 0.0  # en segundos
    bitrate: int = 0  # en kbps
    sample_rate: int = 0  # en Hz
    channels: int = 0
    format: str = ""
    
    # Información musical
    bpm: float | None = None
    key: str | None = None
    
    # Información del archivo
    file_path: str = ""
    file_size: int = 0
    date_modified: datetime = None
    
    def __post_init__(self):
        self.genre = self.genre or []
        if self.date_modified is None:
            self.date_modified = datetime.now(tz=UTC)

class MetadataManager:
    """Gestor principal de metadatos de audio."""
    
    SUPPORTED_FORMATS: ClassVar[dict] = {
        '.mp3': (MP3, EasyID3),
        '.flac': (FLAC, None),
        '.m4a': (MP4, None),
        '.mp4': (MP4, None),
        '.wav': (mutagen.File, None),
        '.ogg': (mutagen.File, None)
    }
    
    def __init__(self):
        """Inicializa el gestor de metadatos."""
        self._cached_metadata = {}
    
    def extract_metadata(self, file_path: str) -> AudioMetadata | None:
        """
        Extrae los metadatos de un archivo de audio.
        
        Args:
            file_path: Ruta al archivo de audio.
            
        Returns:
            AudioMetadata si se pudo extraer la información, None si hubo error.
        """
        try:
            # Verificar si ya está en caché
            if file_path in self._cached_metadata:
                return self._cached_metadata[file_path]
            
            path = Path(file_path)
            if not path.exists():
                logging.error(f"Archivo no encontrado: {file_path}")
                return None
            
            # Obtener el formato correcto para el archivo
            ext = path.suffix.lower()
            if ext not in self.SUPPORTED_FORMATS:
                logging.error(f"Formato no soportado: {ext}")
                return None
            
            # Cargar archivo con mutagen
            audio_class, easy_class = self.SUPPORTED_FORMATS[ext]
            audio = audio_class(file_path)
            easy = None if easy_class is None else easy_class(file_path)
            
            # Extraer metadatos básicos
            metadata = AudioMetadata(
                file_path=file_path,
                file_size=path.stat().st_size,
                date_modified=datetime.fromtimestamp(path.stat().st_mtime, tz=UTC),
                format=ext[1:].upper()  # Remover el punto
            )
            
            # Extraer información técnica
            if hasattr(audio.info, 'length'):
                metadata.duration = float(audio.info.length)
            if hasattr(audio.info, 'bitrate'):
                metadata.bitrate = int(audio.info.bitrate / 1000)
            if hasattr(audio.info, 'sample_rate'):
                metadata.sample_rate = audio.info.sample_rate
            if hasattr(audio.info, 'channels'):
                metadata.channels = audio.info.channels
            
            # Extraer tags según el formato
            if ext == '.mp3' and easy:
                self._extract_mp3_tags(easy, metadata)
            elif ext == '.flac':
                self._extract_flac_tags(audio, metadata)
            elif ext in ['.m4a', '.mp4']:
                self._extract_mp4_tags(audio, metadata)
            
            # Guardar en caché
            self._cached_metadata[file_path] = metadata
            return metadata
            
        except Exception as e:
            logging.error(f"Error extrayendo metadatos de {file_path}: {e}")
            return None
    
    def _extract_mp3_tags(self, easy: EasyID3, metadata: AudioMetadata) -> None:
        """Extrae tags de archivos MP3."""
        metadata.title = easy.get('title', [''])[0]
        metadata.artist = easy.get('artist', [''])[0]
        metadata.album = easy.get('album', [''])[0]
        metadata.genre = easy.get('genre', [])
        
        # Año
        if 'date' in easy:
            with contextlib.suppress(ValueError, IndexError):
                metadata.year = int(easy['date'][0][:4])
        
        # Número de track
        if 'tracknumber' in easy:
            with contextlib.suppress(ValueError, IndexError):
                metadata.track_number = int(easy['tracknumber'][0].split('/')[0])
    
    def _extract_flac_tags(self, audio: FLAC, metadata: AudioMetadata) -> None:
        """Extrae tags de archivos FLAC."""
        metadata.title = audio.tags.get('TITLE', [''])[0]
        metadata.artist = audio.tags.get('ARTIST', [''])[0]
        metadata.album = audio.tags.get('ALBUM', [''])[0]
        metadata.genre = audio.tags.get('GENRE', [])
        
        # Año
        if 'DATE' in audio.tags:
            with contextlib.suppress(ValueError, IndexError):
                metadata.year = int(audio.tags['DATE'][0][:4])
        
        # BPM
        if 'BPM' in audio.tags:
            with contextlib.suppress(ValueError, IndexError):
                metadata.bpm = float(audio.tags['BPM'][0])
    
    def _extract_mp4_tags(self, audio: MP4, metadata: AudioMetadata) -> None:
        """Extrae tags de archivos M4A/MP4."""
        tags = audio.tags if audio.tags else {}
        
        metadata.title = tags.get('\xa9nam', [''])[0]
        metadata.artist = tags.get('\xa9ART', [''])[0]
        metadata.album = tags.get('\xa9alb', [''])[0]
        metadata.genre = tags.get('\xa9gen', [])
        
        # Año
        if '\xa9day' in tags:
            with contextlib.suppress(ValueError, IndexError):
                metadata.year = int(tags['\xa9day'][0][:4])
        
        # Número de track
        if 'trkn' in tags:
            with contextlib.suppress(IndexError, TypeError):
                metadata.track_number = tags['trkn'][0][0]
    
    def clear_cache(self) -> None:
        """Limpia la caché de metadatos."""
        self._cached_metadata.clear()
    
    def update_metadata(self, file_path: str, **kwargs) -> bool:
        """
        Actualiza los metadatos de un archivo de audio.
        
        Args:
            file_path: Ruta al archivo de audio.
            **kwargs: Pares clave-valor de metadatos a actualizar.
            
        Returns:
            bool: True si se actualizó correctamente, False en caso contrario.
        """
        try:
            path = Path(file_path)
            if not path.exists():
                logging.error(f"Archivo no encontrado: {file_path}")
                return False
            
            ext = path.suffix.lower()
            if ext not in self.SUPPORTED_FORMATS:
                logging.error(f"Formato no soportado: {ext}")
                return False
            
            # Actualizar según el formato
            if ext == '.mp3':
                return self._update_mp3_tags(file_path, **kwargs)
            elif ext == '.flac':
                return self._update_flac_tags(file_path, **kwargs)
            elif ext in ['.m4a', '.mp4']:
                return self._update_mp4_tags(file_path, **kwargs)
            
            return False
            
        except Exception as e:
            logging.error(f"Error actualizando metadatos de {file_path}: {e}")
            return False
    
    def _update_mp3_tags(self, file_path: str, **kwargs) -> bool:
        """Actualiza tags de archivos MP3."""
        try:
            audio = EasyID3(file_path)
            
            for key, value in kwargs.items():
                if key in audio.valid_keys:
                    audio[key] = str(value)
            
            audio.save()
            
            # Actualizar caché
            if file_path in self._cached_metadata:
                self.extract_metadata(file_path)
                
            return True
            
        except Exception as e:
            logging.error(f"Error actualizando tags MP3: {e}")
            return False
    
    def _update_flac_tags(self, file_path: str, **kwargs) -> bool:
        """Actualiza tags de archivos FLAC."""
        try:
            audio = FLAC(file_path)
            
            for key, value in kwargs.items():
                audio.tags[key.upper()] = str(value)
            
            audio.save()
            
            # Actualizar caché
            if file_path in self._cached_metadata:
                self.extract_metadata(file_path)
                
            return True
            
        except Exception as e:
            logging.error(f"Error actualizando tags FLAC: {e}")
            return False
    
    def _update_mp4_tags(self, file_path: str, **kwargs) -> bool:
        """Actualiza tags de archivos M4A/MP4."""
        try:
            audio = MP4(file_path)
            
            # Mapeo de claves a tags MP4
            mp4_map = {
                'title': '\xa9nam',
                'artist': '\xa9ART',
                'album': '\xa9alb',
                'genre': '\xa9gen',
                'year': '\xa9day'
            }
            
            for key, value in kwargs.items():
                if key in mp4_map:
                    audio.tags[mp4_map[key]] = str(value)
            
            audio.save()
            
            # Actualizar caché
            if file_path in self._cached_metadata:
                self.extract_metadata(file_path)
                
            return True
            
        except Exception as e:
            logging.error(f"Error actualizando tags MP4: {e}")
            return False
    
    def read_metadata(self, file_path: str) -> AudioMetadata | None:
        """
        Lee los metadatos de un archivo (alias para extract_metadata).
        
        Args:
            file_path: Ruta al archivo de audio
            
        Returns:
            AudioMetadata si se pudo leer, None en caso contrario
        """
        return self.extract_metadata(file_path)
    
    def write_metadata(self, file_path: str, metadata: dict) -> bool:
        """
        Escribe metadatos a un archivo (alias para update_metadata).
        
        Args:
            file_path: Ruta al archivo de audio
            metadata: Diccionario con metadatos a escribir
            
        Returns:
            bool: True si se escribió correctamente
        """
        return self.update_metadata(file_path, **metadata)
    
    def is_supported(self, file_path: str) -> bool:
        """
        Verifica si un archivo tiene un formato soportado.
        
        Args:
            file_path: Ruta al archivo
            
        Returns:
            bool: True si el formato es soportado
        """
        ext = Path(file_path).suffix.lower()
        return ext in self.SUPPORTED_FORMATS
    
    def extract_cover(self, file_path: str) -> bytes | None:
        """
        Extrae la portada de un archivo de audio.
        
        Args:
            file_path: Ruta al archivo de audio
            
        Returns:
            bytes: Datos de la imagen de portada, None si no hay
        """
        try:
            from PIL import Image
            import io
            
            path = Path(file_path)
            ext = path.suffix.lower()
            
            if ext == '.mp3':
                audio = MP3(file_path)
                if audio.tags:
                    for key in audio.tags.keys():
                        if key.startswith('APIC'):
                            return audio.tags[key].data
            
            elif ext == '.flac':
                audio = FLAC(file_path)
                if audio.pictures:
                    return audio.pictures[0].data
            
            elif ext in ['.m4a', '.mp4']:
                audio = MP4(file_path)
                if audio.tags and 'covr' in audio.tags:
                    return audio.tags['covr'][0]
            
            return None
            
        except Exception as e:
            logging.error(f"Error extrayendo portada de {file_path}: {e}")
            return None
    
    def batch_update(self, files_metadata: dict[str, dict]) -> dict[str, bool]:
        """
        Actualiza metadatos de múltiples archivos.
        
        Args:
            files_metadata: Diccionario {file_path: metadata_dict}
            
        Returns:
            Diccionario con resultados {file_path: success}
        """
        results = {}
        
        for file_path, metadata in files_metadata.items():
            try:
                results[file_path] = self.update_metadata(file_path, **metadata)
            except Exception as e:
                logging.error(f"Error en batch update para {file_path}: {e}")
                results[file_path] = False
        
        return results
