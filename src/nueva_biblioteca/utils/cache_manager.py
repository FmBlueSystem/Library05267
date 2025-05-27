#!/usr/bin/env python3
"""
Gestor de Caché - Nueva Biblioteca
===============================

Implementa un sistema de caché en memoria y disco para optimizar
el acceso a metadatos y resultados de APIs externas.
"""

import json
import logging
import os
import pickle
import sqlite3
from datetime import UTC, datetime, timedelta
from functools import wraps
from pathlib import Path
from threading import Lock
from typing import Any


class CacheManager:
    """
    Gestor de caché con soporte para memoria y disco.
    
    Características:
    - Caché en memoria con límite de tamaño
    - Persistencia en SQLite para datos frecuentes
    - Expiración configurable
    - Thread-safe
    """
    
    def __init__(
        self,
        db_path: str | None = None,
        max_memory_items: int = 1000,
        default_ttl: int = 3600  # 1 hora
    ):
        """
        Inicializa el gestor de caché.
        
        Args:
            db_path: Ruta al archivo SQLite
            max_memory_items: Máximo de items en memoria
            default_ttl: Tiempo de vida por defecto en segundos
        """
        # Configuración
        if db_path is None:
            db_path = os.path.expanduser("~/.nueva-biblioteca/cache.db")
        
        self.db_path = Path(db_path)
        self.max_memory_items = max_memory_items
        self.default_ttl = default_ttl
        
        # Estado
        self._memory_cache: dict[str, dict[str, Any]] = {}
        self._access_counts: dict[str, int] = {}
        self._lock = Lock()
        
        # Crear directorio si no existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar base de datos
        self._setup_database()
    
    def _setup_database(self) -> None:
        """Configura la base de datos SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS cache (
                    key TEXT PRIMARY KEY,
                    value BLOB NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    expires_at TIMESTAMP,
                    metadata TEXT
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_expires_at
                ON cache(expires_at)
            """)
    
    def get(
        self,
        key: str,
        default: Any = None,
        namespace: str = "default"
    ) -> Any:
        """
        Obtiene un valor del caché.
        
        Args:
            key: Clave a buscar
            default: Valor por defecto si no existe
            namespace: Espacio de nombres
            
        Returns:
            Valor almacenado o default
        """
        full_key = f"{namespace}:{key}"
        
        # Intentar obtener de memoria
        with self._lock:
            if full_key in self._memory_cache:
                item = self._memory_cache[full_key]
                if not self._is_expired(item):
                    self._access_counts[full_key] = (
                        self._access_counts.get(full_key, 0) + 1
                    )
                    return item["value"]
                else:
                    del self._memory_cache[full_key]
                    if full_key in self._access_counts:
                        del self._access_counts[full_key]
        
        # Intentar obtener de disco
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute("""
                    SELECT value, expires_at FROM cache
                    WHERE key = ?
                """, (full_key,)).fetchone()
                
                if row:
                    value_blob, expires_at = row
                    
                    # Verificar expiración
                    if (expires_at and 
                        datetime.fromisoformat(expires_at) < datetime.now(tz=UTC)):
                        conn.execute("DELETE FROM cache WHERE key = ?", (full_key,))
                        return default
                    
                    # Deserializar valor
                    value = pickle.loads(value_blob)
                    
                    # Actualizar caché en memoria si es frecuentemente accedido
                    if self._should_cache_in_memory(full_key):
                        self._add_to_memory_cache(full_key, value)
                    
                    return value
                
        except Exception as e:
            logging.error(f"Error accediendo a caché en disco: {e}")
        
        return default
    
    def set(
        self,
        key: str,
        value: Any,
        ttl: int | None = None,
        namespace: str = "default",
        metadata: dict | None = None
    ) -> bool:
        """
        Almacena un valor en caché.
        
        Args:
            key: Clave para almacenar
            value: Valor a almacenar
            ttl: Tiempo de vida en segundos
            namespace: Espacio de nombres
            metadata: Metadatos adicionales
            
        Returns:
            True si se almacenó correctamente
        """
        full_key = f"{namespace}:{key}"
        
        try:
            # Calcular expiración
            created_at = datetime.now(tz=UTC)
            expires_at = None
            if ttl is not None:
                expires_at = created_at + timedelta(seconds=ttl)
            elif self.default_ttl:
                expires_at = created_at + timedelta(seconds=self.default_ttl)
            
            # Serializar valor
            value_blob = pickle.dumps(value)
            
            # Almacenar en disco
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO cache
                    (key, value, created_at, expires_at, metadata)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    full_key,
                    value_blob,
                    created_at.isoformat(),
                    expires_at.isoformat() if expires_at else None,
                    json.dumps(metadata) if metadata else None
                ))
            
            # Actualizar caché en memoria si corresponde
            if self._should_cache_in_memory(full_key):
                self._add_to_memory_cache(full_key, value, expires_at)
            
            return True
            
        except Exception as e:
            logging.error(f"Error almacenando en caché: {e}")
            return False
    
    def delete(self, key: str, namespace: str = "default") -> bool:
        """
        Elimina una entrada del caché.
        
        Args:
            key: Clave a eliminar
            namespace: Espacio de nombres
            
        Returns:
            True si se eliminó correctamente
        """
        full_key = f"{namespace}:{key}"
        
        try:
            # Eliminar de memoria
            with self._lock:
                if full_key in self._memory_cache:
                    del self._memory_cache[full_key]
                if full_key in self._access_counts:
                    del self._access_counts[full_key]
            
            # Eliminar de disco
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM cache WHERE key = ?", (full_key,))
            
            return True
            
        except Exception as e:
            logging.error(f"Error eliminando de caché: {e}")
            return False
    
    def clear(self, namespace: str | None = None) -> bool:
        """
        Limpia el caché.
        
        Args:
            namespace: Espacio de nombres a limpiar, o None para todo
            
        Returns:
            True si se limpió correctamente
        """
        try:
            # Limpiar memoria
            with self._lock:
                if namespace:
                    prefix = f"{namespace}:"
                    keys_to_delete = [
                        k for k in self._memory_cache
                        if k.startswith(prefix)
                    ]
                    for key in keys_to_delete:
                        del self._memory_cache[key]
                        if key in self._access_counts:
                            del self._access_counts[key]
                else:
                    self._memory_cache.clear()
                    self._access_counts.clear()
            
            # Limpiar disco
            with sqlite3.connect(self.db_path) as conn:
                if namespace:
                    conn.execute(
                        "DELETE FROM cache WHERE key LIKE ?",
                        (f"{namespace}:%",)
                    )
                else:
                    conn.execute("DELETE FROM cache")
            
            return True
            
        except Exception as e:
            logging.error(f"Error limpiando caché: {e}")
            return False
    
    def cleanup_expired(self) -> int:
        """
        Limpia las entradas expiradas.
        
        Returns:
            Número de entradas eliminadas
        """
        count = 0
        
        try:
            # Limpiar memoria
            with self._lock:
                keys_to_delete = [
                    k for k, v in self._memory_cache.items()
                    if self._is_expired(v)
                ]
                for key in keys_to_delete:
                    del self._memory_cache[key]
                    if key in self._access_counts:
                        del self._access_counts[key]
                count += len(keys_to_delete)
            
            # Limpiar disco
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("""
                    DELETE FROM cache
                    WHERE expires_at < ?
                """, (datetime.now(tz=UTC).isoformat(),))
                count += cursor.rowcount
            
            return count
            
        except Exception as e:
            logging.error(f"Error limpiando caché expirado: {e}")
            return 0
    
    def _is_expired(self, item: dict[str, Any]) -> bool:
        """Verifica si un item está expirado."""
        expires_at = item.get("expires_at")
        return expires_at and expires_at < datetime.now(tz=UTC)
    
    def _should_cache_in_memory(self, key: str) -> bool:
        """Determina si un item debe cachearse en memoria."""
        # Si hay espacio, siempre cachear
        if len(self._memory_cache) < self.max_memory_items:
            return True
        
        # Si es frecuentemente accedido, cachear
        access_count = self._access_counts.get(key, 0)
        return access_count > 5
    
    def _add_to_memory_cache(
        self,
        key: str,
        value: Any,
        expires_at: datetime | None = None
    ) -> None:
        """Agrega un item al caché en memoria."""
        with self._lock:
            # Si está lleno, eliminar el menos accedido
            if (
                len(self._memory_cache) >= self.max_memory_items and
                key not in self._memory_cache
            ):
                min_key = min(
                    self._memory_cache.keys(),
                    key=lambda k: self._access_counts.get(k, 0)
                )
                del self._memory_cache[min_key]
                if min_key in self._access_counts:
                    del self._access_counts[min_key]
            
            # Agregar nuevo item
            self._memory_cache[key] = {
                "value": value,
                "expires_at": expires_at
            }
            self._access_counts[key] = self._access_counts.get(key, 0) + 1

def cached(
    ttl: int | None = None,
    namespace: str | None = None,
    key_prefix: str = ""
):
    """
    Decorador para cachear resultados de funciones.
    
    Args:
        ttl: Tiempo de vida en segundos
        namespace: Espacio de nombres
        key_prefix: Prefijo para la clave
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generar clave única
            key_parts = [key_prefix or func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
            cache_key = ":".join(key_parts)
            
            # Obtener instancia global de caché
            cache = get_cache()
            
            # Intentar obtener resultado cacheado
            result = cache.get(cache_key, namespace=namespace or func.__module__)
            if result is not None:
                return result
            
            # Calcular resultado
            result = func(*args, **kwargs)
            
            # Almacenar en caché
            cache.set(
                cache_key,
                result,
                ttl=ttl,
                namespace=namespace or func.__module__
            )
            
            return result
        return wrapper
    return decorator

# Instancia global
_cache_manager: CacheManager | None = None

def get_cache() -> CacheManager:
    """Obtiene la instancia global del gestor de caché."""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager()
    return _cache_manager
