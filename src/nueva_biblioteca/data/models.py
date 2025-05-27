#!/usr/bin/env python3
"""
Modelos de Base de Datos - Nueva Biblioteca
========================================

Define los modelos SQLAlchemy para la persistencia de datos de la biblioteca musical.
"""

from datetime import datetime

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Table,
    create_engine,
)
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

# Tabla de asociación para playlists y tracks
playlist_tracks = Table(
    'playlist_tracks',
    Base.metadata,
    Column('playlist_id', Integer, ForeignKey('playlists.id'), primary_key=True),
    Column('track_id', Integer, ForeignKey('tracks.id'), primary_key=True),
    Column('position', Integer),
    Column('added_at', DateTime, default=datetime.utcnow)
)

class Track(Base):
    """Modelo para tracks de música."""
    __tablename__ = 'tracks'
    
    id = Column(Integer, primary_key=True)
    file_path = Column(String, unique=True, nullable=False)
    title = Column(String)
    artist = Column(String)
    album = Column(String)
    year = Column(Integer)
    genre = Column(String)
    duration = Column(Float)  # en segundos
    
    # Información técnica
    format = Column(String)  # mp3, flac, etc.
    bitrate = Column(Integer)  # kbps
    sample_rate = Column(Integer)  # Hz
    channels = Column(Integer)
    
    # Metadatos del archivo
    file_size = Column(Integer)  # bytes
    date_added = Column(DateTime, default=datetime.utcnow)
    date_modified = Column(DateTime)
    last_played = Column(DateTime)
    play_count = Column(Integer, default=0)
    
    # Relaciones
    playlists = relationship(
        'Playlist', secondary=playlist_tracks, back_populates='tracks'
    )
    comments = relationship(
        'TrackComment', back_populates='track', cascade='all, delete-orphan'
    )
    
    @hybrid_property
    def rating(self) -> float:
        """Calcula el rating promedio del track."""
        if not self.comments:
            return 0.0
        ratings = [c.rating for c in self.comments if c.rating is not None]
        return sum(ratings) / len(ratings) if ratings else 0.0

class Playlist(Base):
    """Modelo para playlists."""
    __tablename__ = 'playlists'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    is_smart = Column(Boolean, default=False)
    rules = Column(String)  # JSON con reglas para playlists inteligentes
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    tracks = relationship(
        'Track', secondary=playlist_tracks, back_populates='playlists'
    )
    
    @hybrid_property
    def duration(self) -> float:
        """Calcula la duración total de la playlist en segundos."""
        return sum(track.duration or 0 for track in self.tracks)
    
    @hybrid_property
    def track_count(self) -> int:
        """Retorna el número de tracks en la playlist."""
        return len(self.tracks)

class TrackComment(Base):
    """Modelo para comentarios y ratings de tracks."""
    __tablename__ = 'track_comments'
    
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey('tracks.id'), nullable=False)
    comment = Column(String)
    rating = Column(Integer)  # 1-5 estrellas
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relaciones
    track = relationship('Track', back_populates='comments')

class PlayHistory(Base):
    """Modelo para historial de reproducción."""
    __tablename__ = 'play_history'
    
    id = Column(Integer, primary_key=True)
    track_id = Column(Integer, ForeignKey('tracks.id'), nullable=False)
    played_at = Column(DateTime, default=datetime.utcnow)
    completed = Column(Boolean, default=True)  # Si se reprodujo completo
    position = Column(Float)  # Posición en segundos donde se detuvo

def init_db(db_path: str) -> None:
    """
    Inicializa la base de datos.
    
    Args:
        db_path: Ruta al archivo SQLite.
    """
    engine = create_engine(f'sqlite:///{db_path}')
    Base.metadata.create_all(engine)
