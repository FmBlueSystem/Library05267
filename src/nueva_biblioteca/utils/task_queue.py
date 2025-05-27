#!/usr/bin/env python3
"""
Cola de Tareas - Nueva Biblioteca
==============================

Sistema de cola persistente para tareas largas con soporte para
recuperación y reintentos automáticos.
"""

import asyncio
import json
import logging
import os
import sqlite3
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from enum import Enum
from pathlib import Path
from threading import Lock
from typing import Any


class TaskStatus(Enum):
    """Estados posibles de una tarea."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RETRYING = "retrying"

@dataclass
class TaskInfo:
    """Información de una tarea."""
    id: str
    type: str
    params: dict[str, Any]
    status: TaskStatus
    created_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    error: str | None = None
    result: Any | None = None
    retries: int = 0
    max_retries: int = 3
    retry_delay: int = 60  # segundos

class TaskQueue:
    """
    Cola de tareas persistente con soporte para reintentos.
    
    Características:
    - Persistencia en SQLite
    - Reintentos automáticos configurables
    - Recuperación tras fallos
    - Cancelación de tareas
    - Priorización
    """
    
    def __init__(
        self,
        db_path: str | None = None,
        max_concurrent: int = 2,
        cleanup_interval: int = 3600  # 1 hora
    ):
        """
        Inicializa la cola de tareas.
        
        Args:
            db_path: Ruta al archivo SQLite
            max_concurrent: Máximo de tareas concurrentes
            cleanup_interval: Intervalo de limpieza en segundos
        """
        # Configuración
        if db_path is None:
            db_path = os.path.expanduser("~/.nueva-biblioteca/tasks.db")
        
        self.db_path = Path(db_path)
        self.max_concurrent = max_concurrent
        self.cleanup_interval = cleanup_interval
        
        # Estado
        self._handlers: dict[str, Callable] = {}
        self._running_tasks: dict[str, asyncio.Task] = {}
        self._lock = Lock()
        
        # Crear directorio si no existe
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Inicializar base de datos
        self._setup_database()
        
        # Iniciar limpieza periódica
        self._start_cleanup()
    
    def _setup_database(self) -> None:
        """Configura la base de datos SQLite."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS tasks (
                    id TEXT PRIMARY KEY,
                    type TEXT NOT NULL,
                    params TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TIMESTAMP NOT NULL,
                    started_at TIMESTAMP,
                    completed_at TIMESTAMP,
                    error TEXT,
                    result TEXT,
                    retries INTEGER DEFAULT 0,
                    max_retries INTEGER DEFAULT 3,
                    retry_delay INTEGER DEFAULT 60
                )
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status_created
                ON tasks(status, created_at)
            """)
    
    def register_handler(
        self,
        task_type: str,
        handler: Callable[[dict[str, Any]], Awaitable[Any]]
    ) -> None:
        """
        Registra un manejador para un tipo de tarea.
        
        Args:
            task_type: Tipo de tarea
            handler: Función asíncrona que procesa la tarea
        """
        self._handlers[task_type] = handler
    
    async def enqueue(
        self,
        task_type: str,
        params: dict[str, Any],
        max_retries: int = 3,
        retry_delay: int = 60
    ) -> str:
        """
        Encola una nueva tarea.
        
        Args:
            task_type: Tipo de tarea
            params: Parámetros de la tarea
            max_retries: Máximo de reintentos
            retry_delay: Demora entre reintentos en segundos
            
        Returns:
            ID de la tarea
        """
        # Verificar que existe handler
        if task_type not in self._handlers:
            raise ValueError(f"No hay handler registrado para {task_type}")
        
        # Crear tarea
        task_id = f"{task_type}-{datetime.now(tz=UTC).timestamp()}"
        task_info = TaskInfo(
            id=task_id,
            type=task_type,
            params=params,
            status=TaskStatus.PENDING,
            created_at=datetime.now(tz=UTC),
            max_retries=max_retries,
            retry_delay=retry_delay
        )
        
        # Persistir tarea
        self._save_task(task_info)
        
        # Intentar procesar
        try:
            asyncio.create_task(self._process_pending_tasks())
        except RuntimeError:
            # No hay event loop, procesar síncronamente más tarde
            pass
        
        return task_id
    
    def get_task(self, task_id: str) -> TaskInfo | None:
        """
        Obtiene información de una tarea.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            Información de la tarea o None si no existe
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                row = conn.execute("""
                    SELECT * FROM tasks WHERE id = ?
                """, (task_id,)).fetchone()
                
                if row:
                    return self._row_to_task_info(row)
                
        except Exception as e:
            logging.error(f"Error obteniendo tarea {task_id}: {e}")
        
        return None
    
    def cancel_task(self, task_id: str) -> bool:
        """
        Cancela una tarea.
        
        Args:
            task_id: ID de la tarea
            
        Returns:
            True si se canceló correctamente
        """
        try:
            # Cancelar si está en ejecución
            if task_id in self._running_tasks:
                self._running_tasks[task_id].cancel()
            
            # Actualizar estado
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    UPDATE tasks
                    SET status = ?, completed_at = ?
                    WHERE id = ? AND status IN (?, ?)
                """, (
                    TaskStatus.CANCELLED.value,
                    datetime.now(tz=UTC).isoformat(),
                    task_id,
                    TaskStatus.PENDING.value,
                    TaskStatus.RUNNING.value
                ))
            
            return True
            
        except Exception as e:
            logging.error(f"Error cancelando tarea {task_id}: {e}")
            return False
    
    async def _process_pending_tasks(self) -> None:
        """Procesa tareas pendientes."""
        with self._lock:
            # Verificar si podemos procesar más tareas
            if len(self._running_tasks) >= self.max_concurrent:
                return
            
            # Obtener tareas pendientes
            try:
                with sqlite3.connect(self.db_path) as conn:
                    rows = conn.execute("""
                        SELECT * FROM tasks
                        WHERE status = ?
                        ORDER BY created_at ASC
                        LIMIT ?
                    """, (
                        TaskStatus.PENDING.value,
                        self.max_concurrent - len(self._running_tasks)
                    )).fetchall()
                    
                    for row in rows:
                        task_info = self._row_to_task_info(row)
                        if task_info:
                            # Crear tarea asíncrona
                            try:
                                task = asyncio.create_task(
                                    self._execute_task(task_info)
                                )
                                self._running_tasks[task_info.id] = task
                            except RuntimeError:
                                # No hay event loop activo
                                pass
                
            except Exception as e:
                logging.error(f"Error procesando tareas pendientes: {e}")
    
    async def _execute_task(self, task_info: TaskInfo) -> None:
        """Ejecuta una tarea."""
        try:
            # Actualizar estado
            task_info.status = TaskStatus.RUNNING
            task_info.started_at = datetime.now(tz=UTC)
            self._save_task(task_info)
            
            # Ejecutar handler
            handler = self._handlers[task_info.type]
            result = await handler(task_info.params)
            
            # Completar tarea
            task_info.status = TaskStatus.COMPLETED
            task_info.completed_at = datetime.now(tz=UTC)
            task_info.result = result
            
        except Exception as e:
            # Manejar error
            task_info.error = str(e)
            
            if task_info.retries < task_info.max_retries:
                # Programar reintento
                task_info.status = TaskStatus.RETRYING
                task_info.retries += 1
                
                # Esperar delay
                await asyncio.sleep(task_info.retry_delay)
                
                # Reintentar
                task_info.status = TaskStatus.PENDING
                task_info.error = None
                
            else:
                # Marcar como fallida
                task_info.status = TaskStatus.FAILED
                task_info.completed_at = datetime.now(tz=UTC)
            
            logging.error(f"Error ejecutando tarea {task_info.id}: {e}")
        
        finally:
            # Persistir estado final
            self._save_task(task_info)
            
            # Limpiar tarea en ejecución
            if task_info.id in self._running_tasks:
                del self._running_tasks[task_info.id]
            
            # Procesar siguientes tareas
            try:
                asyncio.create_task(self._process_pending_tasks())
            except RuntimeError:
                # No hay event loop activo
                pass
    
    def _save_task(self, task_info: TaskInfo) -> None:
        """Guarda una tarea en la base de datos."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT OR REPLACE INTO tasks (
                        id, type, params, status, created_at,
                        started_at, completed_at, error, result,
                        retries, max_retries, retry_delay
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    task_info.id,
                    task_info.type,
                    json.dumps(task_info.params),
                    task_info.status.value,
                    task_info.created_at.isoformat(),
                    task_info.started_at.isoformat() if task_info.started_at else None,
                    (
                        task_info.completed_at.isoformat() 
                        if task_info.completed_at else None
                    ),
                    task_info.error,
                    json.dumps(task_info.result) if task_info.result else None,
                    task_info.retries,
                    task_info.max_retries,
                    task_info.retry_delay
                ))
                
        except Exception as e:
            logging.error(f"Error guardando tarea {task_info.id}: {e}")
    
    def _row_to_task_info(self, row: tuple) -> TaskInfo | None:
        """Convierte una fila de la base de datos a TaskInfo."""
        try:
            return TaskInfo(
                id=row[0],
                type=row[1],
                params=json.loads(row[2]),
                status=TaskStatus(row[3]),
                created_at=datetime.fromisoformat(row[4]),
                started_at=datetime.fromisoformat(row[5]) if row[5] else None,
                completed_at=datetime.fromisoformat(row[6]) if row[6] else None,
                error=row[7],
                result=json.loads(row[8]) if row[8] else None,
                retries=row[9],
                max_retries=row[10],
                retry_delay=row[11]
            )
        except Exception as e:
            logging.error(f"Error convirtiendo fila a TaskInfo: {e}")
            return None
    
    def _start_cleanup(self) -> None:
        """Inicia la limpieza periódica."""
        async def cleanup():
            while True:
                try:
                    # Eliminar tareas completadas antiguas
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("""
                            DELETE FROM tasks
                            WHERE status IN (?, ?)
                            AND completed_at < ?
                        """, (
                            TaskStatus.COMPLETED.value,
                            TaskStatus.CANCELLED.value,
                            (datetime.now(tz=UTC) - timedelta(days=7)).isoformat()
                        ))
                        
                    # Reactivar tareas stuck
                    with sqlite3.connect(self.db_path) as conn:
                        conn.execute("""
                            UPDATE tasks
                            SET status = ?
                            WHERE status = ?
                            AND started_at < ?
                        """, (
                            TaskStatus.PENDING.value,
                            TaskStatus.RUNNING.value,
                            (datetime.now(tz=UTC) - timedelta(hours=1)).isoformat()
                        ))
                    
                except Exception as e:
                    logging.error(f"Error en limpieza periódica: {e}")
                
                await asyncio.sleep(self.cleanup_interval)
        
        # Solo crear la tarea si hay un event loop ejecutándose
        try:
            asyncio.create_task(cleanup())
        except RuntimeError:
            # No hay event loop ejecutándose, la limpieza se iniciará cuando sea necesario
            logging.debug("No hay event loop activo, limpieza diferida")

# Instancia global
_task_queue: TaskQueue | None = None

def get_task_queue() -> TaskQueue:
    """Obtiene la instancia global de la cola de tareas."""
    global _task_queue
    if _task_queue is None:
        _task_queue = TaskQueue()
    return _task_queue
