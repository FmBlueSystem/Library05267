#!/usr/bin/env python3
"""
Configuración Global - Nueva Biblioteca
=====================================

Gestiona la configuración global de la aplicación usando SQLite para persistencia
y proporciona una interfaz unificada para acceder a las preferencias del usuario.
"""

import json
import logging
import os
import sqlite3
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class UIConfig:
    """Configuración de la interfaz de usuario."""
    theme: str = "dark"
    language: str = "es"
    window_width: int = 1200
    window_height: int = 800
    show_sidebar: bool = True
    table_page_size: int = 100
    font_size: int = 12

@dataclass
class PlayerConfig:
    """Configuración del reproductor de audio."""
    volume: float = 1.0
    enable_crossfade: bool = False
    crossfade_duration: float = 2.0  # segundos
    remember_position: bool = True
    auto_play_on_select: bool = False

@dataclass
class FileConfig:
    """Configuración de gestión de archivos."""
    music_folder: str = str(Path.home() / "Music")
    export_folder: str = str(Path.home() / "Music/Organized")
    backup_enabled: bool = True
    organize_by_artist: bool = True
    supported_formats: list = None
    
    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = [".mp3", ".flac", ".m4a", ".wav", ".ogg"]

@dataclass
class LoggingConfig:
    """Configuración de logging."""
    root_level: str = "INFO"
    file_level: str = "DEBUG"
    console_level: str = "INFO"
    log_directory: str = str(Path.home() / ".nueva-biblioteca" / "logs")
    max_file_size: int = 10 * 1024 * 1024  # 10MB
    backup_count: int = 5

@dataclass
class AppConfig:
    """Configuración principal de la aplicación."""
    ui: UIConfig = field(default_factory=UIConfig)
    player: PlayerConfig = field(default_factory=PlayerConfig)
    files: FileConfig = field(default_factory=FileConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    debug: bool = False

class ConfigManager:
    """Gestor de configuración con persistencia en SQLite."""
    
    def __init__(self, db_path: str | None = None):
        """
        Inicializa el gestor de configuración.
        
        Args:
            db_path: Ruta al archivo SQLite. Si es None, usa el path por defecto.
        """
        if db_path is None:
            db_path = os.path.expanduser("~/.nueva-biblioteca/config.db")
        
        # Crear directorio si no existe
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        
        self.db_path = db_path
        self._config = None
        self._setup_database()
        self._load_config()
    
    def _setup_database(self) -> None:
        """Configura la base de datos SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS config (
                    id INTEGER PRIMARY KEY CHECK (id = 1),
                    data TEXT NOT NULL
                )
            """)
    
    def _load_config(self) -> None:
        """Carga la configuración desde SQLite."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                result = conn.execute("SELECT data FROM config WHERE id = 1").fetchone()
                
                if result:
                    # Cargar configuración existente
                    data = json.loads(result[0])
                    self._config = AppConfig(
                        ui=UIConfig(**data.get('ui', {})),
                        player=PlayerConfig(**data.get('player', {})),
                        files=FileConfig(**data.get('files', {})),
                        logging=LoggingConfig(**data.get('logging', {})),
                        debug=data.get('debug', False)
                    )
                else:
                    # Crear configuración por defecto
                    self._config = AppConfig()
                    self.save()
                    
        except Exception as e:
            logging.error(f"Error cargando configuración: {e}")
            self._config = AppConfig()
    
    def save(self) -> None:
        """Guarda la configuración actual en SQLite."""
        if not self._config:
            return
            
        try:
            data = {
                'ui': asdict(self._config.ui),
                'player': asdict(self._config.player),
                'files': asdict(self._config.files),
                'logging': asdict(self._config.logging),
                'debug': self._config.debug
            }
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO config (id, data)
                    VALUES (1, ?)
                """, (json.dumps(data),))
                
        except Exception as e:
            logging.error(f"Error guardando configuración: {e}")
    
    @property
    def config(self) -> AppConfig:
        """Obtiene la configuración actual."""
        if self._config is None:
            self._load_config()
        return self._config
    
    def update(self, **kwargs) -> None:
        """
        Actualiza la configuración con nuevos valores.
        
        Los valores pueden ser anidados usando notación de punto, por ejemplo:
        update(ui.theme='light', files.music_folder='/path/to/music')
        """
        if self._config is None:
            self._load_config()
            
        for key, value in kwargs.items():
            parts = key.split('.')
            target = self._config
            
            # Navegar hasta el último nivel
            for part in parts[:-1]:
                if hasattr(target, part):
                    target = getattr(target, part)
                else:
                    raise ValueError(f"Configuración inválida: {key}")
            
            # Actualizar el valor final
            if hasattr(target, parts[-1]):
                setattr(target, parts[-1], value)
            else:
                raise ValueError(f"Configuración inválida: {key}")
        
        self.save()
    
    def get_music_folder(self) -> str:
        """Obtiene la carpeta de música configurada."""
        return os.path.expanduser(self.config.files.music_folder)
    
    def get_export_folder(self) -> str:
        """Obtiene la carpeta de exportación configurada."""
        return os.path.expanduser(self.config.files.export_folder)

# Instancia global
_config_manager: ConfigManager | None = None

def get_config() -> AppConfig:
    """Obtiene la configuración global de la aplicación."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    return _config_manager.config

def update_config(**kwargs) -> None:
    """Actualiza la configuración global."""
    global _config_manager
    if _config_manager is None:
        _config_manager = ConfigManager()
    _config_manager.update(**kwargs)
