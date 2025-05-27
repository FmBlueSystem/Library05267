#!/usr/bin/env python3
"""Tests básicos para verificar que el proyecto funciona."""

import pytest
import sys
from pathlib import Path

# Agregar src al path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

def test_imports():
    """Test que verifica que los módulos principales se pueden importar."""
    # Core modules
    from nueva_biblioteca.core.metadata import MetadataManager
    from nueva_biblioteca.core.file_scanner import FileScanner
    from nueva_biblioteca.core.recommender import Recommender
    
    # Data modules
    from nueva_biblioteca.data.models import Track, Playlist
    from nueva_biblioteca.data.repository import Repository
    
    # Utils modules
    from nueva_biblioteca.utils.config import get_config
    from nueva_biblioteca.utils.logger import get_logger
    from nueva_biblioteca.utils.cache_manager import get_cache
    
    # UI modules
    from nueva_biblioteca.ui.theme import get_theme
    
    assert True  # Si llegamos aquí, todos los imports funcionaron

def test_config():
    """Test que verifica que la configuración funciona."""
    from nueva_biblioteca.utils.config import get_config
    
    config = get_config()
    assert config is not None
    assert hasattr(config, 'ui')
    assert hasattr(config, 'player')
    assert hasattr(config, 'files')

def test_logger():
    """Test que verifica que el logger funciona."""
    from nueva_biblioteca.utils.logger import get_logger
    
    logger = get_logger(__name__)
    assert logger is not None
    
    # Test logging
    logger.info("Test log message")
    logger.debug("Test debug message")

def test_theme():
    """Test que verifica que el tema funciona."""
    from nueva_biblioteca.ui.theme import get_theme
    
    theme = get_theme()
    assert theme is not None
    assert hasattr(theme, 'colors')
    assert hasattr(theme, 'typography')
    assert hasattr(theme, 'shapes')

def test_repository():
    """Test que verifica que el repositorio funciona."""
    from nueva_biblioteca.data.repository import Repository
    
    # Usar base de datos en memoria para tests
    repo = Repository(":memory:")
    assert repo is not None
    
    # Test obtener tracks (debería estar vacío)
    tracks = repo.get_all_tracks()
    assert isinstance(tracks, list)
    assert len(tracks) == 0

def test_metadata_manager():
    """Test que verifica que el gestor de metadatos funciona."""
    from nueva_biblioteca.core.metadata import MetadataManager
    
    manager = MetadataManager()
    assert manager is not None
    assert hasattr(manager, 'SUPPORTED_FORMATS')
    assert '.mp3' in manager.SUPPORTED_FORMATS

if __name__ == "__main__":
    pytest.main([__file__]) 