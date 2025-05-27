#!/usr/bin/env python3
"""
Tests para Modelos de Datos - Nueva Biblioteca
============================================

Tests específicos para los modelos SQLAlchemy.
"""

import pytest
from datetime import datetime, UTC
from pathlib import Path

from nueva_biblioteca.data.models import Track, Playlist, TrackComment, PlayHistory


def test_track_creation():
    """Prueba la creación de un track con todos los campos."""
    track = Track(
        file_path="/test/track.mp3",
        title="Test Track",
        artist="Test Artist",
        album="Test Album",
        year=2025,
        genre="Rock",
        duration=180.5,
        format="mp3",
        bitrate=320,
        sample_rate=44100,
        channels=2,
        bpm=120.0,
        key="C major",
        camelot_key="8B",
        energy=0.8,
        file_size=5242880,
        play_count=5
    )
    
    assert track.file_path == "/test/track.mp3"
    assert track.title == "Test Track"
    assert track.artist == "Test Artist"
    assert track.album == "Test Album"
    assert track.year == 2025
    assert track.genre == "Rock"
    assert track.duration == 180.5
    assert track.format == "mp3"
    assert track.bitrate == 320
    assert track.sample_rate == 44100
    assert track.channels == 2
    assert track.bpm == 120.0
    assert track.key == "C major"
    assert track.camelot_key == "8B"
    assert track.energy == 0.8
    assert track.file_size == 5242880
    assert track.play_count == 5


def test_track_minimal():
    """Prueba la creación de un track con campos mínimos."""
    track = Track(file_path="/test/minimal.mp3")
    
    assert track.file_path == "/test/minimal.mp3"
    assert track.title is None
    assert track.artist is None
    assert track.play_count is None or track.play_count == 0


def test_track_rating_property():
    """Prueba la propiedad rating del track."""
    track = Track(file_path="/test/track.mp3")
    
    # Sin comentarios, rating debe ser 0
    assert track.rating == 0.0
    
    # Agregar comentarios con ratings
    comment1 = TrackComment(rating=4)
    comment2 = TrackComment(rating=5)
    comment3 = TrackComment()  # Sin rating
    
    track.comments = [comment1, comment2, comment3]
    
    # Rating promedio debe ser (4 + 5) / 2 = 4.5
    assert track.rating == 4.5


def test_playlist_creation():
    """Prueba la creación de una playlist."""
    playlist = Playlist(
        name="Test Playlist",
        description="A test playlist",
        is_smart=False
    )
    
    assert playlist.name == "Test Playlist"
    assert playlist.description == "A test playlist"
    assert playlist.is_smart is False
    assert playlist.rules is None
    # Los timestamps se establecen solo cuando se guarda en DB
    assert playlist.created_at is None or isinstance(playlist.created_at, datetime)
    assert playlist.updated_at is None or isinstance(playlist.updated_at, datetime)


def test_smart_playlist():
    """Prueba la creación de una playlist inteligente."""
    rules = '{"genre": ["Rock"], "year": {"min": 2020}}'
    playlist = Playlist(
        name="Smart Rock Playlist",
        description="Auto-generated rock playlist",
        is_smart=True,
        rules=rules
    )
    
    assert playlist.name == "Smart Rock Playlist"
    assert playlist.is_smart is True
    assert playlist.rules == rules


def test_playlist_duration_property():
    """Prueba la propiedad duration de la playlist."""
    playlist = Playlist(name="Test Playlist")
    
    # Sin tracks, duración debe ser 0
    assert playlist.duration == 0
    
    # Agregar tracks con duración
    track1 = Track(file_path="/test/track1.mp3", duration=180.0)
    track2 = Track(file_path="/test/track2.mp3", duration=240.0)
    track3 = Track(file_path="/test/track3.mp3")  # Sin duración
    
    playlist.tracks = [track1, track2, track3]
    
    # Duración total debe ser 180 + 240 + 0 = 420
    assert playlist.duration == 420.0


def test_playlist_track_count_property():
    """Prueba la propiedad track_count de la playlist."""
    playlist = Playlist(name="Test Playlist")
    
    # Sin tracks
    assert playlist.track_count == 0
    
    # Con tracks
    tracks = [
        Track(file_path="/test/track1.mp3"),
        Track(file_path="/test/track2.mp3"),
        Track(file_path="/test/track3.mp3")
    ]
    playlist.tracks = tracks
    
    assert playlist.track_count == 3


def test_track_comment_creation():
    """Prueba la creación de comentarios de track."""
    comment = TrackComment(
        track_id=1,
        comment="Great track!",
        rating=5
    )
    
    assert comment.track_id == 1
    assert comment.comment == "Great track!"
    assert comment.rating == 5
    assert comment.created_at is None or isinstance(comment.created_at, datetime)


def test_track_comment_minimal():
    """Prueba la creación de comentario mínimo."""
    comment = TrackComment(track_id=1)
    
    assert comment.track_id == 1
    assert comment.comment is None
    assert comment.rating is None


def test_play_history_creation():
    """Prueba la creación de historial de reproducción."""
    history = PlayHistory(
        track_id=1,
        completed=True,
        position=120.5
    )
    
    assert history.track_id == 1
    assert history.completed is True
    assert history.position == 120.5
    assert history.played_at is None or isinstance(history.played_at, datetime)


def test_play_history_defaults():
    """Prueba los valores por defecto del historial."""
    history = PlayHistory(track_id=1)
    
    assert history.track_id == 1
    assert history.completed is None or history.completed is True
    assert history.position is None


def test_track_relationships():
    """Prueba las relaciones del track."""
    track = Track(file_path="/test/track.mp3")
    
    # Inicialmente sin relaciones
    assert len(track.playlists) == 0
    assert len(track.comments) == 0
    
    # Las relaciones deben ser listas
    assert isinstance(track.playlists, list)
    assert isinstance(track.comments, list)


def test_playlist_relationships():
    """Prueba las relaciones de la playlist."""
    playlist = Playlist(name="Test Playlist")
    
    # Inicialmente sin tracks
    assert len(playlist.tracks) == 0
    assert isinstance(playlist.tracks, list) 