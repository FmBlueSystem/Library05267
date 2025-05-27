#!/usr/bin/env python3
"""
Tests para el módulo del reproductor de audio.
"""

from typing import TYPE_CHECKING
from pathlib import Path
from unittest.mock import call
import pytest

from nueva_biblioteca.core.player import Player, PlayerState
from nueva_biblioteca.data.models import Track

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

@pytest.fixture
def player() -> Player:
    """
    Fixture que proporciona un reproductor.
    
    Returns:
        Instancia de Player
    """
    return Player()

@pytest.fixture
def mock_track(tmp_path: Path) -> Track:
    """
    Fixture que proporciona un track de prueba.
    
    Args:
        tmp_path: Directorio temporal proporcionado por pytest
        
    Returns:
        Track de prueba
    """
    file_path = tmp_path / "test.mp3"
    file_path.write_bytes(b"dummy audio data")
    
    return Track(
        file_path=str(file_path),
        title="Test Track",
        artist="Test Artist",
        duration=180.0
    )

@pytest.mark.asyncio
async def test_play_track(
    player: Player,
    mock_track: Track,
    mocker: "MockerFixture"
) -> None:
    """
    Prueba la reproducción de un track.
    
    Args:
        player: Reproductor
        mock_track: Track de prueba
        mocker: Fixture de pytest-mock
    """
    # Mock de sounddevice
    mock_stream = mocker.MagicMock()
    mock_sounddevice = mocker.patch("sounddevice.OutputStream")
    mock_sounddevice.return_value = mock_stream
    
    # Mock de librosa
    mock_load = mocker.patch("librosa.load")
    mock_load.return_value = (
        [0.0] * 44100,  # Audio simulado de 1 segundo
        44100  # Sample rate
    )
    
    # Spy para state_changed
    state_changed_spy = mocker.spy(player.state_changed, 'emit')
    
    # Reproducir track
    await player.play(mock_track)
    
    # Verificar estado
    assert player.is_playing
    assert player.current_track == mock_track
    assert player.position == 0
    
    # Verificar señales
    state_changed_spy.assert_called_with(True)
    
    # Verificar stream
    mock_sounddevice.assert_called_once()
    mock_stream.start.assert_called_once()

def test_pause_resume(
    player: Player,
    mock_track: Track,
    mocker: "MockerFixture"
) -> None:
    """
    Prueba pausa y reanudación.
    
    Args:
        player: Reproductor
        mock_track: Track de prueba
        mocker: Fixture de pytest-mock
    """
    # Mock de stream
    mock_stream = mocker.MagicMock()
    player._stream = mock_stream
    player._current_track = mock_track
    player._state = PlayerState.PLAYING
    
    # Spy para state_changed
    state_changed_spy = mocker.spy(player.state_changed, 'emit')
    
    # Pausar
    player.pause()
    
    assert not player.is_playing
    assert player.state == PlayerState.PAUSED
    mock_stream.stop.assert_called_once()
    state_changed_spy.assert_called_with(False)
    
    # Reanudar
    player.resume()
    
    assert player.is_playing
    assert player.state == PlayerState.PLAYING
    mock_stream.start.assert_called_once()
    state_changed_spy.assert_called_with(True)

def test_stop(
    player: Player,
    mock_track: Track,
    mocker: "MockerFixture"
) -> None:
    """
    Prueba detener reproducción.
    
    Args:
        player: Reproductor
        mock_track: Track de prueba
        mocker: Fixture de pytest-mock
    """
    # Mock de stream
    mock_stream = mocker.MagicMock()
    player._stream = mock_stream
    player._current_track = mock_track
    player._state = PlayerState.PLAYING
    
    # Spy para state_changed
    state_changed_spy = mocker.spy(player.state_changed, 'emit')
    
    # Detener
    player.stop()
    
    assert not player.is_playing
    assert player.state == PlayerState.STOPPED
    assert player.position == 0
    assert player._stream is None
    
    mock_stream.stop.assert_called_once()
    mock_stream.close.assert_called_once()
    state_changed_spy.assert_called_with(False)

def test_seek(
    player: Player,
    mock_track: Track,
    mocker: "MockerFixture"
) -> None:
    """
    Prueba buscar posición.
    
    Args:
        player: Reproductor
        mock_track: Track de prueba
        mocker: Fixture de pytest-mock
    """
    # Mock de stream
    mock_stream = mocker.MagicMock()
    player._stream = mock_stream
    player._current_track = mock_track
    player._state = PlayerState.PLAYING
    
    # Spy para position_changed
    position_changed_spy = mocker.spy(player.position_changed, 'emit')
    
    # Buscar posición
    player.seek(60.0)  # 1 minuto
    
    assert player.position == 60.0
    position_changed_spy.assert_called_with(60.0)

def test_volume(
    player: Player,
    mock_track: Track,
    mocker: "MockerFixture"
) -> None:
    """
    Prueba control de volumen.
    
    Args:
        player: Reproductor
        mock_track: Track de prueba
        mocker: Fixture de pytest-mock
    """
    # Mock de stream
    mock_stream = mocker.MagicMock()
    player._stream = mock_stream
    player._current_track = mock_track
    
    # Probar cambios de volumen
    player.set_volume(0.5)  # 50%
    assert player.volume == 0.5
    
    player.set_volume(0.0)  # Mute
    assert player.volume == 0.0
    
    player.set_volume(1.0)  # 100%
    assert player.volume == 1.0
    
    # Valores inválidos
    player.set_volume(-0.5)  # Muy bajo
    assert player.volume == 0.0
    
    player.set_volume(1.5)  # Muy alto
    assert player.volume == 1.0

@pytest.mark.asyncio
async def test_error_handling(
    player: Player,
    mock_track: Track,
    mocker: "MockerFixture",
    caplog: "LogCaptureFixture"
) -> None:
    """
    Prueba manejo de errores.
    
    Args:
        player: Reproductor
        mock_track: Track de prueba
        mocker: Fixture de pytest-mock
        caplog: Fixture para capturar logs
    """
    # Mock de librosa para simular error
    mock_load = mocker.patch("librosa.load")
    mock_load.side_effect = Exception("Error loading audio")
    
    # Intentar reproducir
    await player.play(mock_track)
    
    assert not player.is_playing
    assert player.state == PlayerState.STOPPED
    assert "Error loading audio" in caplog.text
    
    # Mock de sounddevice para simular error
    mock_load.side_effect = None
    mock_sounddevice = mocker.patch("sounddevice.OutputStream")
    mock_sounddevice.side_effect = Exception("Audio device error")
    
    await player.play(mock_track)
    
    assert not player.is_playing
    assert player.state == PlayerState.STOPPED
    assert "Audio device error" in caplog.text
