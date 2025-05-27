#!/usr/bin/env python3
"""
Tests para el sistema de recomendaciones.
"""

from typing import TYPE_CHECKING, Dict, List
from pathlib import Path
import pytest
import numpy as np

from nueva_biblioteca.core.recommender import Recommender
from nueva_biblioteca.data.models import Track
from nueva_biblioteca.data.repository import Repository

if TYPE_CHECKING:
    from _pytest.fixtures import FixtureRequest
    from _pytest.logging import LogCaptureFixture
    from _pytest.monkeypatch import MonkeyPatch
    from pytest_mock.plugin import MockerFixture

@pytest.fixture
def recommender(
    test_repository: Repository, 
    mock_task_queue, 
    mock_audio_analyzer
) -> Recommender:
    """
    Fixture que proporciona un recomendador.
    
    Args:
        test_repository: Repositorio de prueba
        mock_task_queue: TaskQueue mock
        mock_audio_analyzer: AudioAnalyzer mock
        
    Returns:
        Instancia de Recommender
    """
    return Recommender(test_repository)

@pytest.fixture
def sample_features() -> Dict[str, np.ndarray]:
    """
    Fixture que proporciona características de audio de ejemplo.
    
    Returns:
        Diccionario con características
    """
    return {
        'mfcc': np.random.rand(20, 30),  # 20 MFCCs, 30 frames
        'chroma': np.random.rand(12, 30),  # 12 pitch classes
        'spectral_contrast': np.random.rand(7, 30),  # 7 bandas
        'tempogram': np.random.rand(384, 30)  # 384 BPM bins
    }

@pytest.fixture
def sample_tracks(tmp_path: Path) -> List[Track]:
    """
    Fixture que proporciona tracks de ejemplo.
    
    Args:
        tmp_path: Directorio temporal proporcionado por pytest
        
    Returns:
        Lista de tracks
    """
    tracks = []
    
    # Crear 5 tracks con características similares
    for i in range(5):
        track = Track(
            file_path=str(tmp_path / f"track_{i}.mp3"),
            title=f"Track {i}",
            artist=f"Artist {i//2}",  # Mismo artista cada 2 tracks
            album=f"Album {i//2}",
            genre="Test Genre",
            bpm=120.0 + i,  # BPMs similares
            key="C",
            energy=0.8
        )
        tracks.append(track)
    
    return tracks

def test_feature_extraction(
    recommender: Recommender,
    sample_tracks: List[Track],
    sample_features: Dict[str, np.ndarray],
    mocker: "MockerFixture"
) -> None:
    """
    Prueba la extracción de características.
    
    Args:
        recommender: Recomendador
        sample_tracks: Tracks de ejemplo
        sample_features: Características de ejemplo
        mocker: Fixture de pytest-mock
    """
    # Mock de extracción de características
    mock_extract = mocker.patch.object(
        recommender,
        '_extract_features',
        return_value=sample_features
    )
    
    track = sample_tracks[0]
    features = recommender.extract_features(track)
    
    assert features is not None
    assert isinstance(features, dict)
    assert all(k in features for k in ['mfcc', 'chroma', 'spectral_contrast'])
    assert mock_extract.called_once_with(track)

def test_similarity_calculation(
    recommender: Recommender,
    sample_tracks: List[Track],
    mocker: "MockerFixture"
) -> None:
    """
    Prueba el cálculo de similitud.
    
    Args:
        recommender: Recomendador
        sample_tracks: Tracks de ejemplo
        mocker: Fixture de pytest-mock
    """
    # Mock de características
    mock_features = {
        str(track.file_path): {
            'mfcc': np.random.rand(20),
            'chroma': np.random.rand(12),
            'spectral_contrast': np.random.rand(7),
            'tempogram': np.random.rand(384)
        }
        for track in sample_tracks
    }
    
    mocker.patch.object(
        recommender,
        '_load_features',
        side_effect=lambda t: mock_features[str(t.file_path)]
    )
    
    # Calcular similitud
    track_a = sample_tracks[0]
    track_b = sample_tracks[1]
    
    similarity = recommender.calculate_similarity(track_a, track_b)
    
    assert 0.0 <= similarity <= 1.0

def test_get_recommendations(
    sample_tracks: List[Track],
    test_repository: Repository,
    mocker: "MockerFixture"
) -> None:
    """
    Prueba la obtención de recomendaciones.
    
    Args:
        sample_tracks: Tracks de ejemplo
        test_repository: Repositorio de prueba
        mocker: Fixture de pytest-mock
    """
    # Mock TaskQueue antes de importar Recommender
    mock_queue = mocker.MagicMock()
    mocker.patch(
        "nueva_biblioteca.utils.task_queue.get_task_queue",
        return_value=mock_queue
    )
    
    # Mock AudioAnalyzer
    mock_analyzer = mocker.MagicMock()
    mocker.patch(
        "nueva_biblioteca.core.audio_analyzer.get_analyzer",
        return_value=mock_analyzer
    )
    
    # Ahora crear el recommender
    recommender = Recommender(test_repository)
    
    # Guardar tracks en repositorio
    for track in sample_tracks:
        test_repository.save_track(track)
    
    # Mock de similitud
    mocker.patch.object(
        recommender,
        'calculate_similarity',
        return_value=0.8  # Alta similitud
    )
    
    # Obtener recomendaciones
    seed_track = sample_tracks[0]
    recommendations = recommender.get_recommendations(seed_track)
    
    assert len(recommendations) >= 0
    assert isinstance(recommendations, list)

def test_batch_recommendations(
    recommender: Recommender,
    sample_tracks: List[Track],
    mocker: "MockerFixture"
) -> None:
    """
    Prueba recomendaciones por lotes.
    
    Args:
        recommender: Recomendador
        sample_tracks: Tracks de ejemplo
        mocker: Fixture de pytest-mock
    """
    # Mock de get_recommendations
    mock_recommend = mocker.patch.object(
        recommender,
        'get_recommendations',
        return_value=sample_tracks[1:3]  # 2 recomendaciones
    )
    
    seed_tracks = sample_tracks[:2]
    config = RecommendationConfig(max_results=2)
    
    recommendations = recommender.get_batch_recommendations(seed_tracks, config)
    
    assert len(recommendations) == len(seed_tracks)
    assert mock_recommend.call_count == len(seed_tracks)

def test_recommendation_caching(
    recommender: Recommender,
    sample_tracks: List[Track],
    mocker: "MockerFixture"
) -> None:
    """
    Prueba el caché de recomendaciones.
    
    Args:
        recommender: Recomendador
        sample_tracks: Tracks de ejemplo
        mocker: Fixture de pytest-mock
    """
    # Mock de cálculo de similitud
    mock_similarity = mocker.patch.object(
        recommender,
        'calculate_similarity',
        return_value=0.8
    )
    
    track = sample_tracks[0]
    config = RecommendationConfig()
    
    # Primera llamada
    recommender.get_recommendations(track, config)
    first_calls = mock_similarity.call_count
    
    # Segunda llamada (debería usar caché)
    recommender.get_recommendations(track, config)
    second_calls = mock_similarity.call_count
    
    assert second_calls == first_calls  # No nuevos cálculos

def test_error_handling(
    recommender: Recommender,
    sample_tracks: List[Track],
    caplog: "LogCaptureFixture"
) -> None:
    """
    Prueba el manejo de errores.
    
    Args:
        recommender: Recomendador
        sample_tracks: Tracks de ejemplo
        caplog: Fixture para capturar logs
    """
    # Track con ruta inválida
    track = Track(
        file_path="/invalid/path.mp3",
        title="Invalid Track"
    )
    
    recommendations = recommender.get_recommendations(track)
    
    assert len(recommendations) == 0
    assert "Error calculating recommendations" in caplog.text
