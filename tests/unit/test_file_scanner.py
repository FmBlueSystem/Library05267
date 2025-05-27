#!/usr/bin/env python3
"""
Tests para el módulo de escaneo de archivos.
"""

from typing import TYPE_CHECKING, List, Set
from pathlib import Path
import pytest
import shutil

from nueva_biblioteca.core.file_scanner import FileScanner
from nueva_biblioteca.data.models import Track
from nueva_biblioteca.data.repository import Repository
from nueva_biblioteca.utils.config import AppConfig

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

@pytest.fixture
def music_dir(tmp_path: Path) -> Path:
    """
    Fixture que crea una estructura de directorios de música.
    
    Args:
        tmp_path: Directorio temporal proporcionado por pytest
        
    Returns:
        Ruta al directorio de música
    """
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    
    # Crear estructura de ejemplo
    structure = {
        "Artist1/Album1": ["01 - Track1.mp3", "02 - Track2.flac"],
        "Artist1/Album2": ["01 - Track3.m4a", "02 - Track4.wav"],
        "Artist2/Album1": ["01 - Track5.mp3", "invalid.txt"],
        "Various/Compilation": ["01 - Artist3 - Track6.mp3"]
    }
    
    for path, files in structure.items():
        folder = music_dir / path
        folder.mkdir(parents=True)
        for file in files:
            (folder / file).write_bytes(b"dummy audio data")
    
    return music_dir

@pytest.fixture
def scanner(
    test_repository: Repository,
    test_config: AppConfig
) -> FileScanner:
    """
    Fixture que proporciona un escáner de archivos.
    
    Args:
        test_repository: Repositorio de prueba
        test_config: Configuración de prueba
        
    Returns:
        Instancia de FileScanner
    """
    return FileScanner(test_repository, test_config)

def test_find_audio_files(
    scanner: FileScanner,
    music_dir: Path
) -> None:
    """
    Prueba la búsqueda de archivos de audio.
    
    Args:
        scanner: Escáner de archivos
        music_dir: Directorio de música
    """
    files = scanner.find_audio_files(music_dir)
    
    # Verificar cantidad
    assert len(files) == 5  # Solo archivos soportados
    
    # Verificar extensiones
    extensions = {f.suffix for f in files}
    assert extensions == {".mp3", ".flac", ".m4a"}
    
    # Verificar estructura
    paths = {f.parent.name for f in files}
    assert "Album1" in paths
    assert "Album2" in paths
    assert "Compilation" in paths

def test_parse_filename(scanner: FileScanner) -> None:
    """
    Prueba el parseo de nombres de archivo.
    
    Args:
        scanner: Escáner de archivos
    """
    # Formato: número - título
    info = scanner.parse_filename("01 - Test Track.mp3")
    assert info["title"] == "Test Track"
    assert info["track_number"] == "01"
    
    # Formato: artista - título
    info = scanner.parse_filename("Artist - Test Track.mp3")
    assert info["artist"] == "Artist"
    assert info["title"] == "Test Track"
    
    # Formato: número - artista - título
    info = scanner.parse_filename("01 - Artist - Test Track.mp3")
    assert info["track_number"] == "01"
    assert info["artist"] == "Artist"
    assert info["title"] == "Test Track"

def test_scan_directory(
    scanner: FileScanner,
    music_dir: Path,
    mocker: "MockerFixture"
) -> None:
    """
    Prueba el escaneo de directorio.
    
    Args:
        scanner: Escáner de archivos
        music_dir: Directorio de música
        mocker: Fixture de pytest-mock
    """
    # Mock de análisis de audio
    mock_analyze = mocker.patch("nueva_biblioteca.core.audio_analyzer.get_analyzer")
    mock_analyze.return_value.analyze_track.return_value = mocker.MagicMock(
        bpm=120.0,
        key="C",
        energy=0.8,
        danceability=0.7
    )
    
    # Escanear directorio
    tracks = list(scanner.scan_directory(music_dir))
    
    assert len(tracks) == 5  # Solo archivos soportados
    
    # Verificar metadata
    for track in tracks:
        assert track.title
        assert track.file_path
        if "Artist1" in track.file_path:
            assert track.artist == "Artist1"

def test_update_library(
    scanner: FileScanner,
    music_dir: Path,
    test_repository: Repository,
    mocker: "MockerFixture"
) -> None:
    """
    Prueba la actualización de biblioteca.
    
    Args:
        scanner: Escáner de archivos
        music_dir: Directorio de música
        test_repository: Repositorio de prueba
        mocker: Fixture de pytest-mock
    """
    # Mock de análisis de audio
    mock_analyze = mocker.patch("nueva_biblioteca.core.audio_analyzer.get_analyzer")
    mock_analyze.return_value.analyze_track.return_value = mocker.MagicMock()
    
    # Mock de callbacks
    mock_progress = mocker.Mock()
    mock_finished = mocker.Mock()
    
    scanner.update_library(
        music_dir,
        on_progress=mock_progress,
        on_finished=mock_finished
    )
    
    # Verificar callbacks
    assert mock_progress.call_count > 0
    mock_finished.assert_called_once()
    
    # Verificar biblioteca
    tracks = test_repository.get_all_tracks()
    assert len(tracks) == 5

def test_removed_files(
    scanner: FileScanner,
    music_dir: Path,
    test_repository: Repository
) -> None:
    """
    Prueba el manejo de archivos eliminados.
    
    Args:
        scanner: Escáner de archivos
        music_dir: Directorio de música
        test_repository: Repositorio de prueba
    """
    # Escanear primero
    tracks = list(scanner.scan_directory(music_dir))
    for track in tracks:
        test_repository.save_track(track)
    
    # Eliminar algunos archivos
    file_to_remove = next(music_dir.rglob("*.mp3"))
    file_to_remove.unlink()
    
    # Re-escanear
    scanner.update_library(music_dir)
    
    # Verificar que se eliminó
    updated_tracks = test_repository.get_all_tracks()
    assert len(updated_tracks) == len(tracks) - 1

def test_error_handling(
    scanner: FileScanner,
    music_dir: Path,
    caplog: "LogCaptureFixture"
) -> None:
    """
    Prueba el manejo de errores.
    
    Args:
        scanner: Escáner de archivos
        music_dir: Directorio de música
        caplog: Fixture para capturar logs
    """
    # Crear archivo corrupto
    bad_file = music_dir / "Artist1/Album1/corrupted.mp3"
    bad_file.write_text("not an audio file")
    
    # Escanear
    tracks = list(scanner.scan_directory(music_dir))
    
    # Verificar que se ignoró el archivo corrupto
    assert all(track.file_path != str(bad_file) for track in tracks)
    assert "Error processing file" in caplog.text
