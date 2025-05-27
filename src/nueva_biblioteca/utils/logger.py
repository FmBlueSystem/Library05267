#!/usr/bin/env python3
"""
Sistema de Logging - Nueva Biblioteca
=================================

Configura un sistema de logging centralizado con soporte para
diferentes niveles, rotación de archivos y formateo personalizado.
"""

import logging
import logging.handlers
import os
import sys
from datetime import UTC, datetime
from pathlib import Path
from threading import Lock
from typing import Any, ClassVar

from .config import get_config


class CustomFormatter(logging.Formatter):
    """Formateador personalizado con colores y detalles extendidos."""
    
    # Códigos ANSI para colores
    COLORS: ClassVar[dict[str, str]] = {
        'DEBUG': '\033[0;36m',    # Cyan
        'INFO': '\033[0;32m',     # Green
        'WARNING': '\033[0;33m',  # Yellow
        'ERROR': '\033[0;31m',    # Red
        'CRITICAL': '\033[1;31m', # Bold Red
        'RESET': '\033[0m'        # Reset
    }
    
    def __init__(self, colored: bool = True):
        """
        Inicializa el formateador.
        
        Args:
            colored: Si debe usar colores en la salida
        """
        super().__init__()
        self.colored = colored and sys.stderr.isatty()
    
    def format(self, record: logging.LogRecord) -> str:
        """Formatea un registro de log."""
        # Agregar timestamp con milisegundos
        record.created_fmt = datetime.fromtimestamp(record.created, tz=UTC).strftime(
            '%Y-%m-%d %H:%M:%S.%f'
        )[:-3]
        
        # Agregar nombre del thread si no es el principal
        if record.threadName != "MainThread":
            record.threadName = f"[{record.threadName}]"
        else:
            record.threadName = ""
        
        # Formatear mensaje base
        fmt = (
            "%(created_fmt)s %(threadName)s "
            "%(levelname)8s %(name)s: %(message)s"
        )
        
        if self.colored:
            # Agregar colores
            color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
            fmt = f"{color}{fmt}{self.COLORS['RESET']}"
        
        # Agregar información de excepción si existe
        if record.exc_info:
            fmt = f"{fmt}\n%(exc_text)s"
        
        formatter = logging.Formatter(fmt)
        return formatter.format(record)

class Logger:
    """
    Gestor de logging centralizado.
    
    Características:
    - Múltiples handlers (consola, archivo, rotación)
    - Formateo personalizado con colores
    - Niveles configurables por módulo
    - Rotación de archivos
    """
    
    def __init__(
        self,
        name: str,
        level: int = logging.INFO,
        log_file: str | None = None,
        max_size: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 5
    ):
        """
        Inicializa el logger.
        
        Args:
            name: Nombre del logger
            level: Nivel de logging
            log_file: Ruta al archivo de log
            max_size: Tamaño máximo del archivo en bytes
            backup_count: Número de backups a mantener
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)
        
        # Evitar duplicación de handlers
        if self.logger.handlers:
            return
        
        # Handler de consola
        console = logging.StreamHandler()
        console.setFormatter(CustomFormatter())
        self.logger.addHandler(console)
        
        # Handler de archivo si se especifica
        if log_file:
            # Crear directorio si no existe
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Configurar handler rotativo
            file_handler = logging.handlers.RotatingFileHandler(
                log_file,
                maxBytes=max_size,
                backupCount=backup_count,
                encoding='utf-8'
            )
            file_handler.setFormatter(CustomFormatter(colored=False))
            self.logger.addHandler(file_handler)
    
    def debug(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a nivel DEBUG."""
        self.logger.debug(msg, *args, **kwargs)
    
    def info(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a nivel INFO."""
        self.logger.info(msg, *args, **kwargs)
    
    def warning(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a nivel WARNING."""
        self.logger.warning(msg, *args, **kwargs)
    
    def error(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a nivel ERROR."""
        self.logger.error(msg, *args, **kwargs)
    
    def critical(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log a nivel CRITICAL."""
        self.logger.critical(msg, *args, **kwargs)
    
    def exception(self, msg: str, *args: Any, **kwargs: Any) -> None:
        """Log de excepción con traceback."""
        self.logger.exception(msg, *args, **kwargs)

class LoggerManager:
    """Gestor centralizado de loggers."""
    
    def __init__(self):
        """Inicializa el gestor de loggers."""
        self.config = get_config()
        self._loggers: dict[str, Logger] = {}
        self._lock = Lock()
        
        # Configurar logging global
        logging.getLogger().setLevel(self.config.logging.root_level)
    
    def get_logger(
        self,
        name: str,
        level: int | None = None,
        log_file: str | None = None
    ) -> Logger:
        """
        Obtiene o crea un logger.
        
        Args:
            name: Nombre del logger
            level: Nivel de logging opcional
            log_file: Archivo de log opcional
            
        Returns:
            Logger configurado
        """
        with self._lock:
            if name not in self._loggers:
                # Usar configuración por defecto si no se especifica
                if level is None:
                    level = getattr(
                        logging, self.config.logging.console_level, logging.INFO
                    )
                
                if log_file is None:
                    log_file = os.path.join(
                        self.config.logging.log_directory,
                        f"{name}.log"
                    )
                
                self._loggers[name] = Logger(
                    name=name,
                    level=level,
                    log_file=log_file,
                    max_size=self.config.logging.max_file_size,
                    backup_count=self.config.logging.backup_count
                )
            
            return self._loggers[name]
    
    def set_level(self, name: str, level: int) -> None:
        """
        Establece el nivel de un logger.
        
        Args:
            name: Nombre del logger
            level: Nivel de logging
        """
        logger = self.get_logger(name)
        logger.logger.setLevel(level)

# Instancia global
_logger_manager: LoggerManager | None = None

def get_logger(name: str) -> Logger:
    """
    Obtiene un logger configurado.
    
    Args:
        name: Nombre del logger
        
    Returns:
        Logger configurado
    """
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager.get_logger(name)
