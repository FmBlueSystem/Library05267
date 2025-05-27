#!/usr/bin/env python3
"""
Exportador - Nueva Biblioteca
=========================

Sistema para exportar playlists y biblioteca a diferentes formatos
(M3U, CSV, JSON) con soporte para personalización y metadatos.
"""

import contextlib
import csv
import json
import os
import shutil
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from nueva_biblioteca.data.models import Playlist, Track
from nueva_biblioteca.utils.config import get_config

from .logger import get_logger

logger = get_logger(__name__)

class Exporter:
    """
    Exportador de biblioteca y playlists.
    
    Formatos soportados:
    - M3U/M3U8 (playlists)
    - CSV (biblioteca)
    - JSON (todo)
    - HTML (reportes)
    """
    
    def __init__(self):
        """Inicializa el exportador."""
        self.config = get_config()
    
    def export_playlist_m3u(
        self,
        playlist: Playlist,
        output_path: str,
        relative_paths: bool = True,
        include_metadata: bool = True
    ) -> bool:
        """
        Exporta una playlist a formato M3U.
        
        Args:
            playlist: Playlist a exportar
            output_path: Ruta del archivo de salida
            relative_paths: Si usar rutas relativas
            include_metadata: Si incluir metadatos extendidos
            
        Returns:
            True si se exportó correctamente
        """
        try:
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                # Escribir cabecera
                f.write("#EXTM3U\n")
                
                if include_metadata:
                    f.write(f"#PLAYLIST:{playlist.name}\n")
                    if playlist.description:
                        f.write(f"#PLAYLISTDESCRIPTION:{playlist.description}\n")
                
                # Escribir tracks
                for track in playlist.tracks:
                    if include_metadata:
                        duration = int(track.duration) if track.duration else -1
                        f.write(f"#EXTINF:{duration},{track.artist} - {track.title}\n")
                        if track.genre:
                            f.write(f"#EXTGENRE:{track.genre}\n")
                    
                    # Procesar ruta
                    file_path = track.file_path
                    if relative_paths:
                        with contextlib.suppress(ValueError):
                            file_path = os.path.relpath(file_path, output_dir)
                    
                    f.write(f"{file_path}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error exportando playlist a M3U: {e}")
            return False
    
    def export_library_csv(
        self,
        tracks: list[Track],
        output_path: str,
        fields: list[str] | None = None
    ) -> bool:
        """
        Exporta la biblioteca a CSV.
        
        Args:
            tracks: Lista de tracks a exportar
            output_path: Ruta del archivo de salida
            fields: Lista de campos a incluir
            
        Returns:
            True si se exportó correctamente
        """
        try:
            # Campos por defecto
            if fields is None:
                fields = [
                    'title', 'artist', 'album', 'genre',
                    'year', 'duration', 'file_path'
                ]
            
            # Crear directorio si no existe
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fields)
                writer.writeheader()
                
                for track in tracks:
                    row = {}
                    for field in fields:
                        value = getattr(track, field, None)
                        if isinstance(value, int | float):
                            row[field] = str(value)
                        else:
                            row[field] = value or ""
                    writer.writerow(row)
            
            return True
            
        except Exception as e:
            logger.error(f"Error exportando biblioteca a CSV: {e}")
            return False
    
    def export_json(
        self,
        data: Any,
        output_path: str,
        pretty: bool = True
    ) -> bool:
        """
        Exporta datos a JSON.
        
        Args:
            data: Datos a exportar
            output_path: Ruta del archivo de salida
            pretty: Si formatear el JSON
            
        Returns:
            True si se exportó correctamente
        """
        try:
            # Crear directorio si no existe
            Path(output_path).parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                if pretty:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                else:
                    json.dump(data, f, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error exportando a JSON: {e}")
            return False
    
    def export_playlist_html(
        self,
        playlist: Playlist,
        output_path: str,
        include_images: bool = True
    ) -> bool:
        """
        Exporta una playlist a HTML con estilos Material Design.
        
        Args:
            playlist: Playlist a exportar
            output_path: Ruta del archivo de salida
            include_images: Si incluir carátulas
            
        Returns:
            True si se exportó correctamente
        """
        try:
            # Crear directorio y subdirectorio de recursos
            output_dir = Path(output_path).parent
            output_dir.mkdir(parents=True, exist_ok=True)
            
            if include_images:
                images_dir = output_dir / "images"
                images_dir.mkdir(exist_ok=True)
            
            # Generar HTML
            html = []
            html.append("<!DOCTYPE html>")
            html.append("<html>")
            html.append("<head>")
            html.append("<meta charset='utf-8'>")
            html.append(f"<title>Playlist: {playlist.name}</title>")
            html.append("""
                <style>
                    body {
                        font-family: 'Roboto', sans-serif;
                        margin: 0;
                        padding: 20px;
                        background: #f5f5f5;
                    }
                    .playlist-header {
                        background: #1976d2;
                        color: white;
                        padding: 20px;
                        border-radius: 4px;
                        margin-bottom: 20px;
                    }
                    .track-list {
                        background: white;
                        border-radius: 4px;
                        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                        overflow: hidden;
                    }
                    .track {
                        display: flex;
                        align-items: center;
                        padding: 10px 20px;
                        border-bottom: 1px solid #eee;
                    }
                    .track:last-child {
                        border-bottom: none;
                    }
                    .track img {
                        width: 50px;
                        height: 50px;
                        margin-right: 15px;
                        border-radius: 4px;
                    }
                    .track-info {
                        flex: 1;
                    }
                    .track-title {
                        font-weight: 500;
                        margin-bottom: 4px;
                    }
                    .track-details {
                        color: #666;
                        font-size: 0.9em;
                    }
                </style>
            """)
            html.append("</head>")
            html.append("<body>")
            
            # Cabecera de playlist
            html.append("<div class='playlist-header'>")
            html.append(f"<h1>{playlist.name}</h1>")
            if playlist.description:
                html.append(f"<p>{playlist.description}</p>")
            html.append(
                f"<p>{len(playlist.tracks)} tracks • Duración total: "
                f"{self._format_duration(playlist.duration)}</p>"
            )
            html.append("</div>")
            
            # Lista de tracks
            html.append("<div class='track-list'>")
            for track in playlist.tracks:
                html.append("<div class='track'>")
                
                # Carátula
                if include_images and hasattr(track, 'cover'):
                    try:
                        image_path = images_dir / f"{track.id}.jpg"
                        with open(image_path, 'wb') as f:
                            f.write(track.cover)
                        html.append(f"<img src='images/{track.id}.jpg' alt='Cover'>")
                    except Exception:
                        html.append(
                    "<img src='data:image/gif;base64,"
                    "R0lGODlhAQABAIAAAP///wAAACH5BAEAAAAALAAAAAABAAEAAAICRAEAOw==' "
                    "alt='No cover'>"
                )
                
                # Información del track
                html.append("<div class='track-info'>")
                html.append(
                    f"<div class='track-title'>{track.title or 'Sin título'}</div>"
                )
                html.append("<div class='track-details'>")
                details = []
                if track.artist:
                    details.append(track.artist)
                if track.album:
                    details.append(track.album)
                if track.genre:
                    details.append(track.genre)
                if track.duration:
                    details.append(self._format_duration(track.duration))
                html.append(" • ".join(details))
                html.append("</div>")
                html.append("</div>")
                
                html.append("</div>")
            html.append("</div>")
            
            # Pie de página
            html.append(
                "<div style='text-align: center; margin-top: 20px; color: #666;'>"
            )
            html.append(
                f"Exportado el {datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M')}"
            )
            html.append("</div>")
            
            html.append("</body>")
            html.append("</html>")
            
            # Escribir archivo
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("\n".join(html))
            
            return True
            
        except Exception as e:
            logger.error(f"Error exportando playlist a HTML: {e}")
            return False
    
    def backup_library(
        self,
        tracks: list[Track],
        backup_dir: str,
        include_files: bool = True
    ) -> bool:
        """
        Crea un backup completo de la biblioteca.
        
        Args:
            tracks: Lista de tracks
            backup_dir: Directorio de backup
            include_files: Si copiar archivos de audio
            
        Returns:
            True si se creó el backup correctamente
        """
        try:
            # Crear estructura de directorios
            backup_path = Path(backup_dir)
            backup_path.mkdir(parents=True, exist_ok=True)
            
            # Exportar metadatos
            metadata_path = backup_path / "metadata.json"
            self.export_json(
                {
                    'tracks': [
                        {
                            'id': track.id,
                            'file_path': track.file_path,
                            'title': track.title,
                            'artist': track.artist,
                            'album': track.album,
                            'year': track.year,
                            'genre': track.genre,
                            'duration': track.duration,
                            'format': track.format,
                            'bitrate': track.bitrate,
                            'sample_rate': track.sample_rate,
                            'channels': track.channels,
                            'file_size': track.file_size,
                            'date_added': (
                                track.date_added.isoformat() 
                                if track.date_added else None
                            ),
                            'date_modified': (
                                track.date_modified.isoformat() 
                                if track.date_modified else None
                            ),
                            'last_played': (
                                track.last_played.isoformat() 
                                if track.last_played else None
                            ),
                            'play_count': track.play_count
                        }
                        for track in tracks
                    ],
                    'backup_date': datetime.now(tz=UTC).isoformat(),
                    'total_tracks': len(tracks)
                },
                str(metadata_path)
            )
            
            # Copiar archivos si se requiere
            if include_files:
                files_dir = backup_path / "files"
                files_dir.mkdir(exist_ok=True)
                
                for track in tracks:
                    try:
                        src = Path(track.file_path)
                        if src.exists():
                            # Mantener estructura de directorios relativa
                            rel_path = src.relative_to(self.config.files.music_folder)
                            dst = files_dir / rel_path
                            dst.parent.mkdir(parents=True, exist_ok=True)
                            shutil.copy2(src, dst)
                    except Exception as e:
                        logger.warning(f"Error copiando archivo {track.file_path}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creando backup: {e}")
            return False
    
    @staticmethod
    def _format_duration(seconds: float | None) -> str:
        """Formatea una duración en segundos a HH:MM:SS."""
        if seconds is None:
            return "00:00"
            
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes}:{seconds:02d}"

# Instancia global
_exporter: Exporter | None = None

def get_exporter() -> Exporter:
    """Obtiene la instancia global del exportador."""
    global _exporter
    if _exporter is None:
        _exporter = Exporter()
    return _exporter
