#!/usr/bin/env python3
"""
Tests Simples - Nueva Biblioteca
==============================

Tests básicos que no dependen de componentes complejos.
"""

import pytest
from pathlib import Path

from nueva_biblioteca.data.models import Track, Playlist
from nueva_biblioteca.data.repository import Repository
from nueva_biblioteca.utils.config import get_config
from nueva_biblioteca.core.metadata import MetadataManager


def test_track_creation():
    """Prueba la creación de un track."""
    track = Track(
        file_path="/test/track.mp3",
        title="Test Track",
        artist="Test Artist",
        album="Test Album",
        genre="Test Genre",
        year=2025,
        duration=180.0
    )
    
    assert track.title == "Test Track"
    assert track.artist == "Test Artist"
    assert track.album == "Test Album"
    assert track.genre == "Test Genre"
    assert track.year == 2025
    assert track.duration == 180.0


def test_playlist_creation():
    """Prueba la creación de una playlist."""
    playlist = Playlist(
        name="Test Playlist",
        description="A test playlist"
    )
    
    assert playlist.name == "Test Playlist"
    assert playlist.description == "A test playlist"
    assert playlist.is_smart is None or playlist.is_smart is False
    assert len(playlist.tracks) == 0


def test_config_loading():
    """Prueba la carga de configuración."""
    config = get_config()
    
    assert config is not None
    assert hasattr(config, 'ui')
    assert hasattr(config, 'files')
    assert hasattr(config, 'logging')


def test_metadata_manager():
    """Prueba el gestor de metadatos."""
    manager = MetadataManager()
    
    assert manager is not None
    assert hasattr(manager, 'SUPPORTED_FORMATS')
    assert '.mp3' in manager.SUPPORTED_FORMATS
    assert '.flac' in manager.SUPPORTED_FORMATS


def test_repository_creation():
    """Prueba la creación del repositorio."""
    repo = Repository()
    
    assert repo is not None
    assert hasattr(repo, 'engine')
    assert hasattr(repo, 'Session')


def test_track_validation():
    """Prueba la validación de tracks."""
    # Track válido
    valid_track = Track(
        file_path="/test/valid.mp3",
        title="Valid Track"
    )
    assert valid_track.title == "Valid Track"
    
    # Track con datos opcionales
    full_track = Track(
        file_path="/test/full.mp3",
        title="Full Track",
        artist="Artist",
        album="Album",
        genre="Genre",
        year=2025,
        duration=200.0,
        bpm=120.0,
        key="C major"
    )
    assert full_track.bpm == 120.0
    assert full_track.key == "C major"


def test_playlist_with_tracks():
    """Prueba playlist con tracks."""
    tracks = [
        Track(file_path="/test/track1.mp3", title="Track 1"),
        Track(file_path="/test/track2.mp3", title="Track 2"),
        Track(file_path="/test/track3.mp3", title="Track 3")
    ]
    
    playlist = Playlist(
        name="Multi Track Playlist",
        tracks=tracks
    )
    
    assert len(playlist.tracks) == 3
    assert playlist.tracks[0].title == "Track 1"
    assert playlist.tracks[1].title == "Track 2"
    assert playlist.tracks[2].title == "Track 3"


def test_smart_playlist():
    """Prueba playlist inteligente."""
    smart_playlist = Playlist(
        name="Smart Playlist",
        description="Auto-generated playlist",
        is_smart=True,
        rules='{"genre": ["Rock"], "year": {"min": 2020}}'
    )
    
    assert smart_playlist.is_smart is True
    assert smart_playlist.rules is not None
    assert "Rock" in smart_playlist.rules 