#!/usr/bin/env python3
"""
Configuración común de tests para Nueva Biblioteca.
"""

from typing import TYPE_CHECKING, Generator, Dict, Any
from pathlib import Path
import pytest
import tempfile
import shutil
import json
import asyncio
import pytest_asyncio

from nueva_biblioteca.utils.config import AppConfig, get_config
from nueva_biblioteca.data.repository import Repository, get_repository
from nueva_biblioteca.data.models import Track, Playlist

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

@pytest.fixture
def test_config(tmp_path: Path, monkeypatch: "MonkeyPatch") -> AppConfig:
    """
    Fixture que proporciona una configuración de prueba.
    
    Args:
        tmp_path: Directorio temporal proporcionado por pytest
        monkeypatch: Fixture para modificar objetos
        
    Returns:
        Configuración de prueba
    """
    config_data = {
        "files": {
            "music_folder": str(tmp_path / "music"),
            "supported_formats": [".mp3", ".flac", ".m4a"],
        },
        "database": {
            "path": str(tmp_path / "library.db")
        },
        "logging": {
            "level": "DEBUG",
            "directory": str(tmp_path / "logs")
        },
        "cache": {
            "directory": str(tmp_path / "cache"),
            "max_size_mb": 100
        }
    }
    
    # Crear directorios necesarios
    for path in [
        config_data["files"]["music_folder"],
        config_data["logging"]["directory"],
        config_data["cache"]["directory"]
    ]:
        Path(path).mkdir(parents=True, exist_ok=True)
    
    # Guardar configuración temporal
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))
    
    # Modificar ruta de configuración
    monkeypatch.setenv("NUEVA_BIBLIOTECA_CONFIG", str(config_file))
    
    return get_config()

@pytest.fixture
def test_repository(test_config: AppConfig) -> Generator[Repository, None, None]:
    """
    Fixture que proporciona un repositorio de prueba.
    
    Args:
        test_config: Configuración de prueba
        
    Yields:
        Repositorio de prueba
    """
    repository = get_repository()
    
    yield repository
    
    # Limpiar base de datos
    db_path = Path.home() / ".nueva-biblioteca" / "library.db"
    if db_path.exists():
        db_path.unlink()

@pytest.fixture
def sample_tracks(test_config: AppConfig) -> Generator[Dict[str, Track], None, None]:
    """
    Fixture que proporciona tracks de ejemplo.
    
    Args:
        test_config: Configuración de prueba
        
    Yields:
        Diccionario de tracks de ejemplo
    """
    music_dir = Path(test_config.files.music_folder)
    tracks = {}
    
    # Crear archivos de audio dummy
    for i in range(3):
        file_path = music_dir / f"track_{i}.mp3"
        file_path.write_bytes(b"dummy audio data")
        
        track = Track(
            file_path=str(file_path),
            title=f"Track {i}",
            artist=f"Artist {i//2}",  # Mismo artista cada 2 tracks
            album=f"Album {i//2}",
            genre="Test Genre",
            year=2025,
            duration=180.0
        )
        tracks[f"track_{i}"] = track
    
    yield tracks
    
    # Limpiar archivos
    for track in tracks.values():
        if Path(track.file_path).exists():
            Path(track.file_path).unlink()

@pytest.fixture
def sample_playlist(
    test_repository: Repository,
    sample_tracks: Dict[str, Track]
) -> Playlist:
    """
    Fixture que proporciona una playlist de ejemplo.
    
    Args:
        test_repository: Repositorio de prueba
        sample_tracks: Tracks de ejemplo
        
    Returns:
        Playlist de ejemplo
    """
    # Crear y guardar tracks
    tracks = []
    for track in sample_tracks.values():
        saved_track = test_repository.save_track(track)
        tracks.append(saved_track)
    
    # Crear playlist
    playlist = Playlist(
        name="Test Playlist",
        description="A test playlist",
        tracks=tracks,
        is_smart=False
    )
    
    return test_repository.save_playlist(playlist)

@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: "MonkeyPatch") -> None:
    """
    Fixture que limpia variables de entorno.
    
    Args:
        monkeypatch: Fixture para modificar objetos
    """
    # Limpiar variables que podrían afectar los tests
    for var in [
        "NUEVA_BIBLIOTECA_CONFIG",
        "NUEVA_BIBLIOTECA_ENV",
        "NUEVA_BIBLIOTECA_DEBUG"
    ]:
        monkeypatch.delenv(var, raising=False)

@pytest.fixture
def mock_config(mocker: "MockerFixture") -> Dict[str, Any]:
    """
    Fixture que proporciona una configuración mock.
    
    Args:
        mocker: Fixture de pytest-mock
        
    Returns:
        Configuración mock
    """
    config = {
        "files": {
            "music_folder": "/mock/music",
            "supported_formats": [".mp3"]
        },
        "database": {
            "path": ":memory:"
        },
        "logging": {
            "level": "DEBUG",
            "directory": "/mock/logs"
        }
    }
    
    # Mock get_config
    mocker.patch(
        "nueva_biblioteca.utils.config.get_config",
        return_value=config
    )
    
    return config

@pytest.fixture(scope="session")
def event_loop():
    """
    Fixture que proporciona un event loop para toda la sesión de tests.
    """
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def mock_task_queue(mocker: "MockerFixture"):
    """
    Fixture que proporciona un TaskQueue mock sin asyncio.
    
    Args:
        mocker: Fixture de pytest-mock
        
    Returns:
        TaskQueue mock
    """
    mock_queue = mocker.MagicMock()
    mock_queue.add_task = mocker.MagicMock()
    mock_queue.get_status = mocker.MagicMock(return_value="idle")
    
    # Mock del singleton
    mocker.patch(
        "nueva_biblioteca.utils.task_queue.get_task_queue",
        return_value=mock_queue
    )
    
    return mock_queue

@pytest.fixture
def mock_audio_analyzer(mocker: "MockerFixture"):
    """
    Fixture que proporciona un AudioAnalyzer mock sin TaskQueue.
    
    Args:
        mocker: Fixture de pytest-mock
        
    Returns:
        AudioAnalyzer mock
    """
    mock_analyzer = mocker.MagicMock()
    mock_analyzer.analyze_track = mocker.MagicMock(return_value=mocker.MagicMock(
        bpm=120.0,
        key="C",
        energy=0.8,
        danceability=0.7,
        valence=0.6,
        acousticness=0.3,
        instrumentalness=0.1,
        liveness=0.2,
        speechiness=0.1
    ))
    
    # Mock del singleton
    mocker.patch(
        "nueva_biblioteca.core.audio_analyzer.get_analyzer",
        return_value=mock_analyzer
    )
    
    return mock_analyzer
