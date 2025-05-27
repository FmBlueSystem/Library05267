#!/usr/bin/env python3
"""
Tests para el módulo de metadatos.
"""

from typing import TYPE_CHECKING
from pathlib import Path
import pytest
import tempfile
import shutil

from nueva_biblioteca.core.metadata import MetadataManager
from nueva_biblioteca.data.models import Track

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

@pytest.fixture
def metadata_manager() -> MetadataManager:
    """
    Fixture que proporciona un gestor de metadatos.
    
    Returns:
        Instancia de MetadataManager
    """
    return MetadataManager()

@pytest.fixture
def test_files(tmp_path: Path) -> Path:
    """
    Fixture que crea archivos de audio de prueba.
    
    Args:
        tmp_path: Directorio temporal proporcionado por pytest
        
    Returns:
        Directorio con archivos de prueba
    """
    test_dir = tmp_path / "test_audio"
    test_dir.mkdir()
    
    # Crear archivos dummy
    formats = [".mp3", ".flac", ".m4a"]
    for i, fmt in enumerate(formats):
        file = test_dir / f"test_track_{i}{fmt}"
        file.write_bytes(b"dummy audio data")
    
    return test_dir

def test_read_metadata(
    metadata_manager: MetadataManager,
    test_files: Path,
    mocker: "MockerFixture"
) -> None:
    """
    Prueba la lectura de metadatos.
    
    Args:
        metadata_manager: Gestor de metadatos
        test_files: Directorio con archivos de prueba
        mocker: Fixture de pytest-mock
    """
    # Mock de mutagen
    mock_mutagen = mocker.patch("mutagen.File")
    mock_mutagen.return_value = {
        "title": ["Test Track"],
        "artist": ["Test Artist"],
        "album": ["Test Album"],
        "genre": ["Test Genre"],
        "date": ["2025"],
        "track": ["1/12"]
    }
    
    test_file = test_files / "test_track_0.mp3"
    metadata = metadata_manager.read_metadata(test_file)
    
    assert metadata is not None
    assert metadata.title == "Test Track"
    assert metadata.artist == "Test Artist"
    assert metadata.album == "Test Album"
    assert metadata.genre == "Test Genre"
    assert metadata.year == 2025

def test_write_metadata(
    metadata_manager: MetadataManager,
    test_files: Path,
    mocker: "MockerFixture"
) -> None:
    """
    Prueba la escritura de metadatos.
    
    Args:
        metadata_manager: Gestor de metadatos
        test_files: Directorio con archivos de prueba
        mocker: Fixture de pytest-mock
    """
    # Mock de mutagen
    mock_file = mocker.MagicMock()
    mock_mutagen = mocker.patch("mutagen.File", return_value=mock_file)
    
    test_file = test_files / "test_track_0.mp3"
    track = Track(
        file_path=str(test_file),
        title="New Title",
        artist="New Artist",
        album="New Album",
        genre="New Genre",
        year=2025
    )
    
    success = metadata_manager.write_metadata(track)
    
    assert success
    assert mock_file.save.called
    
    # Verificar tags escritos
    calls = mock_file.__setitem__.call_args_list
    assert ("title", ["New Title"]) in [c[0] for c in calls]
    assert ("artist", ["New Artist"]) in [c[0] for c in calls]
    assert ("album", ["New Album"]) in [c[0] for c in calls]
    assert ("genre", ["New Genre"]) in [c[0] for c in calls]
    assert ("date", ["2025"]) in [c[0] for c in calls]

def test_extract_cover(
    metadata_manager: MetadataManager,
    test_files: Path,
    mocker: "MockerFixture"
) -> None:
    """
    Prueba la extracción de carátulas.
    
    Args:
        metadata_manager: Gestor de metadatos
        test_files: Directorio con archivos de prueba
        mocker: Fixture de pytest-mock
    """
    # Mock de mutagen y PIL
    mock_mutagen = mocker.patch("mutagen.File")
    mock_mutagen.return_value = {
        "APIC:": mocker.MagicMock(data=b"fake image data")
    }
    
    mock_image = mocker.patch("PIL.Image.open")
    mock_image.return_value = mocker.MagicMock()
    
    test_file = test_files / "test_track_0.mp3"
    cover = metadata_manager.get_cover(test_file)
    
    assert cover is not None
    assert mock_image.called

def test_batch_update(
    metadata_manager: MetadataManager,
    test_files: Path,
    mocker: "MockerFixture"
) -> None:
    """
    Prueba la actualización por lotes.
    
    Args:
        metadata_manager: Gestor de metadatos
        test_files: Directorio con archivos de prueba
        mocker: Fixture de pytest-mock
    """
    # Mock de write_metadata
    mock_write = mocker.patch.object(
        metadata_manager,
        'write_metadata',
        return_value=True
    )
    
    # Crear tracks de prueba
    tracks = []
    for i in range(3):
        track = Track(
            file_path=str(test_files / f"test_track_{i}.mp3"),
            title=f"Track {i}",
            artist="Common Artist",
            album="Common Album"
        )
        tracks.append(track)
    
    # Actualizar en lote
    changes = {
        "artist": "New Artist",
        "genre": "New Genre"
    }
    
    success = metadata_manager.batch_update(tracks, changes)
    
    assert success
    assert mock_write.call_count == len(tracks)
    
    # Verificar cambios
    for call in mock_write.call_args_list:
        track = call[0][0]
        assert track.artist == "New Artist"
        assert track.genre == "New Genre"

def test_invalid_file(
    metadata_manager: MetadataManager,
    test_files: Path,
    caplog: "LogCaptureFixture"
) -> None:
    """
    Prueba el manejo de archivos inválidos.
    
    Args:
        metadata_manager: Gestor de metadatos
        test_files: Directorio con archivos de prueba
        caplog: Fixture para capturar logs
    """
    nonexistent = test_files / "nonexistent.mp3"
    metadata = metadata_manager.read_metadata(nonexistent)
    
    assert metadata is None
    assert "Error reading metadata" in caplog.text

def test_supported_formats(metadata_manager: MetadataManager) -> None:
    """
    Prueba la detección de formatos soportados.
    
    Args:
        metadata_manager: Gestor de metadatos
    """
    assert metadata_manager.is_supported("test.mp3")
    assert metadata_manager.is_supported("test.flac")
    assert metadata_manager.is_supported("test.m4a")
    assert not metadata_manager.is_supported("test.wav")
    assert not metadata_manager.is_supported("test.txt")
