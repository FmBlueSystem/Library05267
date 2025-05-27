#!/usr/bin/env python3
"""
Tests para Sistema de Configuración - Nueva Biblioteca
====================================================

Tests específicos para el manejo de configuración.
"""

import pytest
import json
import os
from pathlib import Path
from unittest.mock import patch

from nueva_biblioteca.utils.config import (
    AppConfig, UIConfig, FileConfig, LoggingConfig, PlayerConfig,
    get_config, ConfigManager
)


def test_ui_config_creation():
    """Prueba la creación de configuración de UI."""
    ui_config = UIConfig(
        theme="dark",
        language="es",
        window_width=1400,
        window_height=900,
        show_sidebar=False,
        table_page_size=100
    )
    
    assert ui_config.theme == "dark"
    assert ui_config.language == "es"
    assert ui_config.window_width == 1400
    assert ui_config.window_height == 900
    assert ui_config.show_sidebar is False
    assert ui_config.table_page_size == 100


def test_ui_config_defaults():
    """Prueba los valores por defecto de UI."""
    ui_config = UIConfig()
    
    assert ui_config.theme == "dark"
    assert ui_config.language == "es"
    assert ui_config.window_width == 1200
    assert ui_config.window_height == 800
    assert ui_config.show_sidebar is True
    assert ui_config.table_page_size == 100


def test_file_config_creation():
    """Prueba la creación de configuración de archivos."""
    file_config = FileConfig(
        music_folder="/custom/music",
        export_folder="/custom/export",
        supported_formats=[".mp3", ".flac", ".wav"],
        backup_enabled=False,
        organize_by_artist=False
    )
    
    assert file_config.music_folder == "/custom/music"
    assert file_config.export_folder == "/custom/export"
    assert file_config.supported_formats == [".mp3", ".flac", ".wav"]
    assert file_config.backup_enabled is False
    assert file_config.organize_by_artist is False


def test_file_config_defaults():
    """Prueba los valores por defecto de archivos."""
    file_config = FileConfig()
    
    assert file_config.music_folder == str(Path.home() / "Music")
    assert file_config.export_folder == str(Path.home() / "Music/Organized")
    assert ".mp3" in file_config.supported_formats
    assert ".flac" in file_config.supported_formats
    assert ".m4a" in file_config.supported_formats
    assert file_config.backup_enabled is True
    assert file_config.organize_by_artist is True


def test_logging_config_creation():
    """Prueba la creación de configuración de logging."""
    logging_config = LoggingConfig(
        root_level="DEBUG",
        log_directory="/custom/logs",
        max_file_size=20971520,  # 20MB
        backup_count=10
    )
    
    assert logging_config.root_level == "DEBUG"
    assert logging_config.log_directory == "/custom/logs"
    assert logging_config.max_file_size == 20971520
    assert logging_config.backup_count == 10


def test_logging_config_defaults():
    """Prueba los valores por defecto de logging."""
    logging_config = LoggingConfig()
    
    assert logging_config.root_level == "INFO"
    assert logging_config.file_level == "DEBUG"
    assert logging_config.console_level == "INFO"
    assert logging_config.log_directory == str(Path.home() / ".nueva-biblioteca" / "logs")
    assert logging_config.max_file_size == 10485760  # 10MB
    assert logging_config.backup_count == 5


def test_player_config_creation():
    """Prueba la creación de configuración del reproductor."""
    player_config = PlayerConfig(
        volume=0.8,
        enable_crossfade=True,
        crossfade_duration=3.0,
        remember_position=False,
        auto_play_on_select=True
    )
    
    assert player_config.volume == 0.8
    assert player_config.enable_crossfade is True
    assert player_config.crossfade_duration == 3.0
    assert player_config.remember_position is False
    assert player_config.auto_play_on_select is True


def test_player_config_defaults():
    """Prueba los valores por defecto del reproductor."""
    player_config = PlayerConfig()
    
    assert player_config.volume == 1.0
    assert player_config.enable_crossfade is False
    assert player_config.crossfade_duration == 2.0
    assert player_config.remember_position is True
    assert player_config.auto_play_on_select is False


def test_app_config_creation():
    """Prueba la creación de configuración completa."""
    ui_config = UIConfig(theme="light")
    file_config = FileConfig(music_folder="/test/music")
    logging_config = LoggingConfig(root_level="DEBUG")
    player_config = PlayerConfig(volume=0.5)
    
    app_config = AppConfig(
        ui=ui_config,
        files=file_config,
        logging=logging_config,
        player=player_config,
        debug=True
    )
    
    assert app_config.ui.theme == "light"
    assert app_config.files.music_folder == "/test/music"
    assert app_config.logging.root_level == "DEBUG"
    assert app_config.player.volume == 0.5
    assert app_config.debug is True


def test_app_config_defaults():
    """Prueba los valores por defecto de la aplicación."""
    app_config = AppConfig()
    
    assert isinstance(app_config.ui, UIConfig)
    assert isinstance(app_config.files, FileConfig)
    assert isinstance(app_config.logging, LoggingConfig)
    assert isinstance(app_config.player, PlayerConfig)
    assert app_config.debug is False


def test_config_manager_creation(tmp_path):
    """Prueba la creación del gestor de configuración."""
    db_path = tmp_path / "test_config.db"
    manager = ConfigManager(str(db_path))
    
    assert isinstance(manager.config, AppConfig)
    assert Path(db_path).exists()


def test_config_manager_update(tmp_path):
    """Prueba la actualización de configuración."""
    db_path = tmp_path / "test_config.db"
    manager = ConfigManager(str(db_path))
    
    # Actualizar configuración
    manager.update(**{
        'ui.theme': 'light',
        'files.music_folder': '/custom/music',
        'player.volume': 0.8
    })
    
    # Verificar cambios
    assert manager.config.ui.theme == "light"
    assert manager.config.files.music_folder == "/custom/music"
    assert manager.config.player.volume == 0.8


def test_config_manager_persistence(tmp_path):
    """Prueba la persistencia de configuración."""
    db_path = tmp_path / "test_config.db"
    
    # Crear y configurar primer manager
    manager1 = ConfigManager(str(db_path))
    manager1.update(**{'ui.theme': 'light'})
    
    # Crear segundo manager con la misma DB
    manager2 = ConfigManager(str(db_path))
    
    # Debe cargar la configuración guardada
    assert manager2.config.ui.theme == "light"


def test_get_config():
    """Prueba la obtención de configuración global."""
    config = get_config()
    
    assert isinstance(config, AppConfig)
    assert isinstance(config.ui, UIConfig)
    assert isinstance(config.files, FileConfig)
    assert isinstance(config.logging, LoggingConfig)
    assert isinstance(config.player, PlayerConfig)


def test_config_manager_methods(tmp_path):
    """Prueba los métodos del gestor de configuración."""
    db_path = tmp_path / "test_config.db"
    manager = ConfigManager(str(db_path))
    
    # Probar get_music_folder
    music_folder = manager.get_music_folder()
    assert isinstance(music_folder, str)
    
    # Probar get_export_folder
    export_folder = manager.get_export_folder()
    assert isinstance(export_folder, str) 