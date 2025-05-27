#!/usr/bin/env python3
"""
Procesador por Lotes - Nueva Biblioteca
===================================

Implementa el procesamiento optimizado por lotes para gestionar grandes
cantidades de archivos sin problemas de memoria.
"""

import asyncio
import logging
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Generic, TypeVar

T = TypeVar('T')
R = TypeVar('R')

@dataclass
class BatchProgress:
    """Representa el progreso del procesamiento por lotes."""
    total_items: int = 0
    processed_items: int = 0
    current_item: str | None = None
    errors: list[str] = None
    start_time: datetime = None
    
    def __post_init__(self):
        self.errors = self.errors or []
        self.start_time = self.start_time or datetime.now(tz=UTC)
    
    @property
    def completion_percentage(self) -> float:
        """Retorna el porcentaje de completitud."""
        if self.total_items == 0:
            return 0.0
        return (self.processed_items / self.total_items) * 100
    
    @property
    def elapsed_time(self) -> float:
        """Retorna el tiempo transcurrido en segundos."""
        return (datetime.now(tz=UTC) - self.start_time).total_seconds()

class BatchProcessor(Generic[T, R]):
    """
    Procesador genérico por lotes con gestión de memoria optimizada.
    
    TypeVars:
        T: Tipo de los items a procesar
        R: Tipo del resultado del procesamiento
    """
    
    def __init__(
        self,
        chunk_size: int = 10,
        max_workers: int = 2,
        cleanup_interval: int = 5
    ):
        """
        Inicializa el procesador por lotes.
        
        Args:
            chunk_size: Tamaño de cada lote
            max_workers: Máximo de workers concurrentes
            cleanup_interval: Intervalo de limpieza de memoria
        """
        self.chunk_size = chunk_size
        self.max_workers = max_workers
        self.cleanup_interval = cleanup_interval
        self._progress = BatchProgress()
        self._cancel_requested = False
    
    async def process_items(
        self,
        items: list[T],
        process_func: Callable[[T], R],
        on_progress: Callable[[BatchProgress], None] | None = None
    ) -> list[R]:
        """
        Procesa una lista de items en chunks.
        
        Args:
            items: Lista de items a procesar
            process_func: Función de procesamiento
            on_progress: Callback para reportar progreso
            
        Returns:
            Lista de resultados
        """
        # Reiniciar estado
        self._progress = BatchProgress(total_items=len(items))
        self._cancel_requested = False
        results: list[R] = []
        
        try:
            # Procesar en chunks
            for i in range(0, len(items), self.chunk_size):
                if self._cancel_requested:
                    break
                
                # Obtener chunk actual
                chunk = items[i:i + self.chunk_size]
                
                # Procesar chunk
                chunk_results = await self._process_chunk(chunk, process_func)
                results.extend(chunk_results)
                
                # Actualizar progreso
                self._progress.processed_items += len(chunk)
                if on_progress:
                    on_progress(self._progress)
                
                # Limpiar memoria si corresponde
                if (i + 1) % (self.cleanup_interval * self.chunk_size) == 0:
                    self._cleanup_memory()
            
            return results
            
        except Exception as e:
            logging.error(f"Error en procesamiento por lotes: {e}")
            self._progress.errors.append(str(e))
            return results
    
    async def _process_chunk(
        self,
        chunk: list[T],
        process_func: Callable[[T], R]
    ) -> list[R]:
        """Procesa un chunk de items en paralelo."""
        try:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                # Crear tareas para cada item
                tasks = []
                for item in chunk:
                    if self._cancel_requested:
                        break
                    
                    # Procesar en thread separado
                    task = asyncio.get_event_loop().run_in_executor(
                        executor,
                        process_func,
                        item
                    )
                    tasks.append(task)
                    
                    # Actualizar item actual
                    self._progress.current_item = str(item)
                
                # Esperar que se completen todas las tareas
                results = await asyncio.gather(*tasks, return_exceptions=True)
                
                # Filtrar errores
                valid_results = []
                for result in results:
                    if isinstance(result, Exception):
                        self._progress.errors.append(str(result))
                    else:
                        valid_results.append(result)
                
                return valid_results
                
        except Exception as e:
            logging.error(f"Error procesando chunk: {e}")
            self._progress.errors.append(str(e))
            return []
    
    def _cleanup_memory(self) -> None:
        """Realiza limpieza de memoria."""
        # TODO: Implementar limpieza de memoria más agresiva si es necesario
        import gc
        gc.collect()
    
    def cancel(self) -> None:
        """Cancela el procesamiento actual."""
        self._cancel_requested = True
    
    @property
    def progress(self) -> BatchProgress:
        """Obtiene el progreso actual."""
        return self._progress
