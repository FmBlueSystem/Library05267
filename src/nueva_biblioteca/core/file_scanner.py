#!/usr/bin/env python3
"""
Escáner de Archivos - Nueva Biblioteca
===================================

Sistema de escaneo recursivo de archivos de música con procesamiento por lotes
y gestión optimizada de memoria.
"""

import logging
import os
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path

from nueva_biblioteca.utils.batch_processor import BatchProcessor, BatchProgress
from nueva_biblioteca.utils.config import get_config

from .metadata import AudioMetadata, MetadataManager


@dataclass
class ScanProgress:
    """Representa el progreso del escaneo."""
    total_files: int = 0
    processed_files: int = 0
    current_file: str = ""
    errors: list[str] = None
    start_time: datetime = None
    
    def __post_init__(self):
        self.errors = self.errors or []
        self.start_time = self.start_time or datetime.now(tz=UTC)
    
    @property
    def elapsed_time(self) -> float:
        """Retorna el tiempo transcurrido en segundos."""
        return (datetime.now(tz=UTC) - self.start_time).total_seconds()
    
    @property
    def completion_percentage(self) -> float:
        """Retorna el porcentaje de completitud."""
        if self.total_files == 0:
            return 0.0
        return (self.processed_files / self.total_files) * 100

class FileScanner:
    """Escáner de archivos de música con procesamiento optimizado."""
    
    def __init__(self, repository=None, config=None):
        """
        Inicializa el escáner de archivos.
        
        Args:
            repository: Repositorio para guardar tracks (opcional)
            config: Configuración de la aplicación (opcional)
        """
        from nueva_biblioteca.data.repository import Repository
        
        self.repository = repository
        self.config = config or get_config()
        self.metadata_manager = MetadataManager()
        self._supported_formats = set(self.config.files.supported_formats)
        self._processed_files: set[str] = set()
        self._current_progress = ScanProgress()
        
        # Configurar procesador por lotes
        self.batch_processor = BatchProcessor[str, AudioMetadata | None](
            chunk_size=10,  # 10 archivos por lote
            max_workers=2,  # 2 workers concurrentes
            cleanup_interval=5  # Limpiar cada 5 lotes
        )
    
    async def scan_directory(
        self, directory: str, recursive: bool = True
    ) -> list[AudioMetadata]:
        """
        Escanea un directorio en busca de archivos de música.
        
        Args:
            directory: Ruta al directorio a escanear
            recursive: Si debe buscar en subdirectorios
            
        Returns:
            Lista de metadatos de archivos encontrados
        """
        try:
            # Reiniciar progreso
            self._current_progress = ScanProgress()
            self._processed_files.clear()
            
            # Obtener lista de archivos
            music_files = self._find_music_files(directory, recursive)
            total_files = len(music_files)
            self._current_progress.total_files = total_files
            
            if total_files == 0:
                logging.info(f"No se encontraron archivos de música en {directory}")
                return []
            
            # Procesar archivos usando BatchProcessor
            results = await self.batch_processor.process_items(
                items=music_files,
                process_func=self._process_file,
                on_progress=self._update_progress
            )
            
            # Filtrar None results
            valid_results = [r for r in results if r is not None]
            
            logging.info(
                f"Escaneados {len(valid_results)} archivos en "
                f"{self._current_progress.elapsed_time:.2f} segundos"
            )
            return valid_results
            
        except Exception as e:
            logging.error(f"Error escaneando directorio {directory}: {e}")
            self._current_progress.errors.append(str(e))
            return []
    
    def _find_music_files(self, directory: str, recursive: bool) -> list[str]:
        """Encuentra todos los archivos de música en el directorio."""
        music_files = []
        
        try:
            if recursive:
                for root, _, files in os.walk(directory):
                    for file in files:
                        if self._is_supported_file(file):
                            music_files.append(os.path.join(root, file))
            else:
                for entry in os.scandir(directory):
                    if entry.is_file() and self._is_supported_file(entry.name):
                        music_files.append(entry.path)
                        
            return sorted(music_files)  # Ordenar para procesamiento predecible
            
        except Exception as e:
            logging.error(f"Error buscando archivos: {e}")
            self._current_progress.errors.append(str(e))
            return []
    
    def _is_supported_file(self, filename: str) -> bool:
        """Verifica si un archivo tiene una extensión soportada."""
        return Path(filename).suffix.lower() in self._supported_formats
    
    async def _process_file(self, file_path: str) -> AudioMetadata | None:
        """Procesa un archivo individual."""
        try:
            self._current_progress.current_file = file_path
            
            # Extraer metadatos
            metadata = self.metadata_manager.extract_metadata(file_path)
            
            if metadata:
                self._processed_files.add(file_path)
                return metadata
                
        except Exception as e:
            logging.error(f"Error procesando archivo {file_path}: {e}")
            self._current_progress.errors.append(f"Error en {file_path}: {e!s}")
        
        return None
    
    def _update_progress(self, batch_progress: BatchProgress) -> None:
        """Actualiza el progreso del escaneo desde el progreso del batch."""
        self._current_progress.processed_files = batch_progress.processed_items
        if batch_progress.current_item:
            self._current_progress.current_file = batch_progress.current_item
        if batch_progress.errors:
            self._current_progress.errors.extend(batch_progress.errors)
    
    def get_progress(self) -> ScanProgress:
        """Obtiene el progreso actual del escaneo."""
        return self._current_progress
    
    def cancel_scan(self) -> None:
        """Cancela el escaneo en curso."""
        self.batch_processor.cancel()
    
    def clear_cache(self) -> None:
        """Limpia las cachés internas."""
        self._processed_files.clear()
        self.metadata_manager.clear_cache()
    
    def find_audio_files(self, directory: Path) -> list[Path]:
        """
        Encuentra archivos de audio en un directorio.
        
        Args:
            directory: Directorio a escanear
            
        Returns:
            Lista de rutas de archivos de audio
        """
        audio_files = []
        try:
            for root, _, files in os.walk(directory):
                for file in files:
                    if self._is_supported_file(file):
                        audio_files.append(Path(root) / file)
            return sorted(audio_files)
        except Exception as e:
            logging.error(f"Error buscando archivos de audio: {e}")
            return []
    
    def parse_filename(self, filename: str) -> dict[str, str]:
        """
        Parsea información del nombre de archivo.
        
        Args:
            filename: Nombre del archivo
            
        Returns:
            Diccionario con información extraída
        """
        import re
        
        # Remover extensión
        name = Path(filename).stem
        info = {}
        
        # Patrón: número - artista - título
        pattern1 = r'^(\d+)\s*-\s*(.+?)\s*-\s*(.+)$'
        match = re.match(pattern1, name)
        if match:
            info['track_number'] = match.group(1)
            info['artist'] = match.group(2).strip()
            info['title'] = match.group(3).strip()
            return info
        
        # Patrón: número - título
        pattern2 = r'^(\d+)\s*-\s*(.+)$'
        match = re.match(pattern2, name)
        if match:
            info['track_number'] = match.group(1)
            info['title'] = match.group(2).strip()
            return info
        
        # Patrón: artista - título
        pattern3 = r'^(.+?)\s*-\s*(.+)$'
        match = re.match(pattern3, name)
        if match:
            info['artist'] = match.group(1).strip()
            info['title'] = match.group(2).strip()
            return info
        
        # Si no coincide con ningún patrón, usar como título
        info['title'] = name
        return info
    
    def scan_directory(self, directory: Path, recursive: bool = True) -> list:
        """
        Escanea directorio y retorna lista de tracks (versión síncrona para tests).
        
        Args:
            directory: Directorio a escanear
            recursive: Si debe buscar recursivamente
            
        Returns:
            Lista de tracks encontrados
        """
        from nueva_biblioteca.data.models import Track
        
        tracks = []
        try:
            audio_files = self.find_audio_files(directory)
            
            for file_path in audio_files:
                try:
                    # Extraer metadatos
                    metadata = self.metadata_manager.extract_metadata(str(file_path))
                    if metadata:
                        # Crear track desde metadatos
                        track = Track(
                            file_path=str(file_path),
                            title=metadata.title or self.parse_filename(file_path.name)['title'],
                            artist=metadata.artist,
                            album=metadata.album,
                            year=metadata.year,
                            genre=metadata.genre,
                            duration=metadata.duration,
                            format=metadata.format,
                            bitrate=metadata.bitrate,
                            sample_rate=metadata.sample_rate,
                            channels=metadata.channels,
                            bpm=metadata.bpm,
                            key=metadata.key,
                            energy=metadata.energy,
                            file_size=metadata.file_size
                        )
                        
                        # Inferir artista desde la estructura de directorios si no está disponible
                        if not track.artist:
                            parts = file_path.parts
                            if len(parts) >= 2:
                                track.artist = parts[-3]  # Directorio del artista
                        
                        tracks.append(track)
                        
                except Exception as e:
                    logging.error(f"Error procesando {file_path}: {e}")
                    continue
                    
            return tracks
            
        except Exception as e:
            logging.error(f"Error escaneando directorio {directory}: {e}")
            return []
    
    def update_library(self, directory: Path, on_progress=None, on_finished=None):
        """
        Actualiza la biblioteca con archivos del directorio.
        
        Args:
            directory: Directorio a escanear
            on_progress: Callback de progreso
            on_finished: Callback de finalización
        """
        try:
            tracks = self.scan_directory(directory)
            
            if self.repository:
                for i, track in enumerate(tracks):
                    try:
                        self.repository.save_track(track)
                        if on_progress:
                            on_progress(i + 1, len(tracks), track.file_path)
                    except Exception as e:
                        logging.error(f"Error guardando track {track.file_path}: {e}")
            
            if on_finished:
                on_finished(len(tracks))
                
        except Exception as e:
            logging.error(f"Error actualizando biblioteca: {e}")
            if on_finished:
                on_finished(0)
