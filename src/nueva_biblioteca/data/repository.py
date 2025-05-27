#!/usr/bin/env python3
"""
Repositorio de Datos - Nueva Biblioteca
====================================

Proporciona una capa de abstracción para interactuar con la base de datos
y realizar operaciones CRUD sobre los modelos.
"""

import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from sqlalchemy import create_engine, desc
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from .models import Base, PlayHistory, Playlist, Track, TrackComment


class Repository:
    """Repositorio principal para acceso a datos."""
    
    def __init__(self, db_path: str | None = None):
        """
        Inicializa el repositorio.
        
        Args:
            db_path: Ruta al archivo SQLite. Si es None, usa el path por defecto.
        """
        if db_path is None:
            db_path = str(Path.home() / ".nueva-biblioteca" / "library.db")
            
        # Crear directorio si no existe
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar engine y session
        self.engine = create_engine(f'sqlite:///{db_path}')
        self.Session = sessionmaker(bind=self.engine)
        
        # Crear tablas si no existen
        Base.metadata.create_all(self.engine)
    
    def _session(self) -> Session:
        """Crea una nueva sesión de base de datos."""
        return self.Session()
    
    # Operaciones de Track
    
    def add_track(self, track_data: dict[str, Any]) -> Track | None:
        """
        Agrega un nuevo track a la biblioteca.
        
        Args:
            track_data: Diccionario con datos del track
            
        Returns:
            Track creado o None si hubo error
        """
        try:
            with self._session() as session:
                track = Track(**track_data)
                session.add(track)
                session.commit()
                return track
        except SQLAlchemyError as e:
            logging.error(f"Error agregando track: {e}")
            return None
    
    def save_track(self, track: Track) -> Track | None:
        """
        Guarda un track (nuevo o existente) en la biblioteca.
        
        Args:
            track: Instancia de Track a guardar
            
        Returns:
            Track guardado o None si hay error
        """
        try:
            with self._session() as session:
                if track.id:
                    # Track existente - merge
                    track = session.merge(track)
                else:
                    # Track nuevo - add
                    session.add(track)
                session.commit()
                return track
        except SQLAlchemyError as e:
            logging.error(f"Error guardando track: {e}")
            return None
    
    def get_track(self, track_id: int) -> Track | None:
        """Obtiene un track por su ID."""
        try:
            with self._session() as session:
                return session.query(Track).get(track_id)
        except SQLAlchemyError as e:
            logging.error(f"Error obteniendo track {track_id}: {e}")
            return None
    
    def get_track_by_path(self, file_path: str) -> Track | None:
        """Obtiene un track por su ruta de archivo."""
        try:
            with self._session() as session:
                return session.query(Track).filter_by(file_path=file_path).first()
        except SQLAlchemyError as e:
            logging.error(f"Error obteniendo track por path {file_path}: {e}")
            return None
    
    def update_track(self, track_id: int, data: dict[str, Any]) -> bool:
        """Actualiza un track existente."""
        try:
            with self._session() as session:
                track = session.query(Track).get(track_id)
                if track:
                    for key, value in data.items():
                        setattr(track, key, value)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logging.error(f"Error actualizando track {track_id}: {e}")
            return False
    
    def delete_track(self, track_id: int) -> bool:
        """Elimina un track de la biblioteca."""
        try:
            with self._session() as session:
                track = session.query(Track).get(track_id)
                if track:
                    session.delete(track)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logging.error(f"Error eliminando track {track_id}: {e}")
            return False
    
    def delete_playlist(self, playlist_id: int) -> bool:
        """
        Elimina una playlist de la biblioteca.
        
        Args:
            playlist_id: ID de la playlist a eliminar
            
        Returns:
            True si se eliminó correctamente, False en caso contrario
        """
        try:
            with self._session() as session:
                playlist = session.query(Playlist).get(playlist_id)
                if playlist:
                    session.delete(playlist)
                    session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logging.error(f"Error eliminando playlist {playlist_id}: {e}")
            return False
    
    def get_all_tracks(self, limit: int = 1000) -> list[Track]:
        """
        Obtiene todos los tracks de la biblioteca.
        
        Args:
            limit: Límite de resultados
            
        Returns:
            Lista de todos los tracks
        """
        try:
            with self._session() as session:
                return session.query(Track).limit(limit).all()
        except SQLAlchemyError as e:
            logging.error(f"Error obteniendo todos los tracks: {e}")
            return []
    
    def search_tracks(
        self,
        query: str = "",
        filters: dict[str, Any] | None = None,
        order_by: str = "title",
        limit: int = 100,
        offset: int = 0
    ) -> list[Track]:
        """
        Busca tracks según criterios.
        
        Args:
            query: Texto a buscar
            filters: Diccionario de filtros
            order_by: Campo para ordenar
            limit: Límite de resultados
            offset: Desplazamiento para paginación
            
        Returns:
            Lista de tracks que coinciden
        """
        try:
            with self._session() as session:
                # Construir query base
                q = session.query(Track)
                
                # Aplicar búsqueda de texto
                if query:
                    q = q.filter(
                        Track.title.ilike(f"%{query}%") |
                        Track.artist.ilike(f"%{query}%") |
                        Track.album.ilike(f"%{query}%")
                    )
                
                # Aplicar filtros adicionales
                if filters:
                    for key, value in filters.items():
                        if hasattr(Track, key):
                            q = q.filter(getattr(Track, key) == value)
                
                # Ordenar
                if hasattr(Track, order_by):
                    q = q.order_by(getattr(Track, order_by))
                
                # Aplicar paginación
                return q.offset(offset).limit(limit).all()
                
        except SQLAlchemyError as e:
            logging.error(f"Error buscando tracks: {e}")
            return []
    
    # Operaciones de Playlist
    
    def create_playlist(
        self,
        name: str,
        description: str = "",
        is_smart: bool = False,
        rules: str | None = None
    ) -> Playlist | None:
        """Crea una nueva playlist."""
        try:
            with self._session() as session:
                playlist = Playlist(
                    name=name,
                    description=description,
                    is_smart=is_smart,
                    rules=rules
                )
                session.add(playlist)
                session.commit()
                return playlist
        except SQLAlchemyError as e:
            logging.error(f"Error creando playlist: {e}")
            return None
    
    def save_playlist(self, playlist: Playlist) -> Playlist | None:
        """
        Guarda una playlist (nueva o existente).
        
        Args:
            playlist: Instancia de Playlist a guardar
            
        Returns:
            Playlist guardada o None si hay error
        """
        try:
            with self._session() as session:
                if playlist.id:
                    # Playlist existente - merge
                    playlist = session.merge(playlist)
                else:
                    # Playlist nueva - add
                    session.add(playlist)
                session.commit()
                return playlist
        except SQLAlchemyError as e:
            logging.error(f"Error guardando playlist: {e}")
            return None
    
    def add_track_to_playlist(
        self,
        playlist_id: int,
        track_id: int,
        position: int | None = None
    ) -> bool:
        """Agrega un track a una playlist."""
        try:
            with self._session() as session:
                playlist = session.query(Playlist).get(playlist_id)
                track = session.query(Track).get(track_id)
                
                if playlist and track:
                    if track not in playlist.tracks:
                        playlist.tracks.append(track)
                        session.commit()
                    return True
                return False
        except SQLAlchemyError as e:
            logging.error(
                f"Error agregando track {track_id} a playlist {playlist_id}: {e}"
            )
            return False
    
    def get_all_playlists(self) -> list[Playlist]:
        """
        Obtiene todas las playlists.
        
        Returns:
            Lista de todas las playlists
        """
        try:
            with self._session() as session:
                from sqlalchemy.orm import joinedload
                playlists = session.query(Playlist).options(joinedload(Playlist.tracks)).all()
                # Expunge para poder usar fuera de la sesión
                for playlist in playlists:
                    session.expunge(playlist)
                return playlists
        except SQLAlchemyError as e:
            logging.error(f"Error obteniendo todas las playlists: {e}")
            return []
    
    def get_playlist_tracks(
        self,
        playlist_id: int,
        limit: int = 100,
        offset: int = 0
    ) -> list[Track]:
        """Obtiene los tracks de una playlist."""
        try:
            with self._session() as session:
                playlist = session.query(Playlist).get(playlist_id)
                if playlist:
                    return playlist.tracks[offset:offset + limit]
                return []
        except SQLAlchemyError as e:
            logging.error(f"Error obteniendo tracks de playlist {playlist_id}: {e}")
            return []
    
    # Operaciones de Historial
    
    def add_play_history(
        self,
        track_id: int,
        completed: bool = True,
        position: float = 0
    ) -> bool:
        """Registra una reproducción en el historial."""
        try:
            with self._session() as session:
                history = PlayHistory(
                    track_id=track_id,
                    completed=completed,
                    position=position
                )
                session.add(history)
                
                # Actualizar last_played y play_count del track
                track = session.query(Track).get(track_id)
                if track:
                    track.last_played = datetime.now(tz=UTC)
                    track.play_count += 1
                
                session.commit()
                return True
        except SQLAlchemyError as e:
            logging.error(f"Error registrando reproducción de track {track_id}: {e}")
            return False
    
    def get_play_history(
        self,
        limit: int = 50,
        offset: int = 0
    ) -> list[PlayHistory]:
        """Obtiene el historial de reproducción."""
        try:
            with self._session() as session:
                return (
                    session.query(PlayHistory)
                    .order_by(desc(PlayHistory.played_at))
                    .offset(offset)
                    .limit(limit)
                    .all()
                )
        except SQLAlchemyError as e:
            logging.error(f"Error obteniendo historial: {e}")
            return []
    
    # Operaciones de Comentarios
    
    def add_track_comment(
        self,
        track_id: int,
        comment: str = "",
        rating: int | None = None
    ) -> TrackComment | None:
        """Agrega un comentario/rating a un track."""
        try:
            with self._session() as session:
                track_comment = TrackComment(
                    track_id=track_id,
                    comment=comment,
                    rating=rating
                )
                session.add(track_comment)
                session.commit()
                return track_comment
        except SQLAlchemyError as e:
            logging.error(f"Error agregando comentario a track {track_id}: {e}")
            return None
    
    def get_track_comments(
        self,
        track_id: int,
        limit: int = 10,
        offset: int = 0
    ) -> list[TrackComment]:
        """Obtiene los comentarios de un track."""
        try:
            with self._session() as session:
                return (
                    session.query(TrackComment)
                    .filter_by(track_id=track_id)
                    .order_by(desc(TrackComment.created_at))
                    .offset(offset)
                    .limit(limit)
                    .all()
                )
        except SQLAlchemyError as e:
            logging.error(f"Error obteniendo comentarios de track {track_id}: {e}")
            return []
    
    def cleanup(self) -> None:
        """Limpia recursos del repositorio."""
        self.Session.close_all()

# Instancia global
_repository: Repository | None = None

def get_repository() -> Repository:
    """Obtiene la instancia global del repositorio."""
    global _repository
    if _repository is None:
        _repository = Repository()
    return _repository
