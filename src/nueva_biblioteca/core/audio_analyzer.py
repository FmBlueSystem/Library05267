#!/usr/bin/env python3
"""
Analizador de Audio - Nueva Biblioteca
=================================

Sistema para analizar características musicales de archivos de audio
como BPM, energía, key, segmentos, etc.
"""

from concurrent.futures import ThreadPoolExecutor
from typing import Any

try:
    import essentia
    import essentia.standard as es
    ESSENTIA_AVAILABLE = True
except ImportError:
    ESSENTIA_AVAILABLE = False
    essentia = None
    es = None
import numpy as np

from nueva_biblioteca.utils.cache_manager import get_cache
from nueva_biblioteca.utils.logger import get_logger
from nueva_biblioteca.utils.task_queue import get_task_queue

logger = get_logger(__name__)

class AudioAnalyzer:
    """
    Analizador de características musicales.
    
    Características:
    - BPM y tempo
    - Análisis de key/tonalidad
    - Detección de segmentos
    - Nivel de energía
    - Características espectrales
    """
    
    def __init__(self, max_workers: int = 2):
        """
        Inicializa el analizador.
        
        Args:
            max_workers: Máximo de workers concurrentes
        """
        self.max_workers = max_workers
        self.cache = get_cache()
        self.task_queue = get_task_queue()
        
        # Configurar essentia si está disponible
        if ESSENTIA_AVAILABLE:
            essentia.init()
        else:
            logger.warning(
                "Essentia no está disponible. Funcionalidad de análisis limitada."
            )
    
    def analyze_file(
        self,
        file_path: str,
        features: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Analiza un archivo de audio.
        
        Args:
            file_path: Ruta al archivo
            features: Lista de características a extraer
            
        Returns:
            Diccionario con resultados del análisis
        """
        try:
            # Verificar si essentia está disponible
            if not ESSENTIA_AVAILABLE:
                logger.warning("Essentia no disponible, retornando análisis vacío")
                return {}
            
            # Verificar caché
            cache_key = f"analysis:{file_path}"
            cached = self.cache.get(cache_key)
            if cached:
                return cached
            
            # Cargar archivo
            audio = es.MonoLoader(filename=file_path)()
            
            # Características por defecto
            if features is None:
                features = [
                    'bpm',
                    'key',
                    'energy',
                    'danceability',
                    'segments'
                ]
            
            # Resultados
            results = {}
            
            # Extraer cada característica solicitada
            if 'bpm' in features:
                results['bpm'] = self._extract_bpm(audio)
            
            if 'key' in features:
                results['key'] = self._extract_key(audio)
            
            if 'energy' in features:
                results['energy'] = self._extract_energy(audio)
            
            if 'danceability' in features:
                results['danceability'] = self._extract_danceability(audio)
            
            if 'segments' in features:
                results['segments'] = self._extract_segments(audio)
            
            # Cachear resultados
            self.cache.set(cache_key, results, ttl=3600*24)  # 24 horas
            
            return results
            
        except Exception as e:
            logger.error(f"Error analizando {file_path}: {e}")
            return {}
    
    def batch_analyze(
        self,
        files: list[str],
        features: list[str] | None = None,
        on_progress = None
    ) -> dict[str, dict[str, Any]]:
        """
        Analiza múltiples archivos en paralelo.
        
        Args:
            files: Lista de archivos
            features: Lista de características
            on_progress: Callback de progreso
            
        Returns:
            Diccionario con resultados por archivo
        """
        results = {}
        total = len(files)
        
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # Crear tareas
            futures = []
            for file_path in files:
                future = executor.submit(self.analyze_file, file_path, features)
                futures.append((file_path, future))
            
            # Procesar resultados
            for i, (file_path, future) in enumerate(futures, 1):
                try:
                    result = future.result()
                    results[file_path] = result
                except Exception as e:
                    logger.error(f"Error en análisis de {file_path}: {e}")
                    results[file_path] = {}
                
                # Reportar progreso
                if on_progress:
                    percentage = (i / total) * 100
                    on_progress(percentage, f"Analizando {i}/{total}")
        
        return results
    
    def _extract_bpm(self, audio: np.ndarray) -> float:
        """
        Extrae el BPM de un audio.
        
        Args:
            audio: Señal de audio
            
        Returns:
            BPM detectado
        """
        rhythm_extractor = es.RhythmExtractor2013()
        bpm, beats, confidence, _, _ = rhythm_extractor(audio)
        return float(bpm)
    
    def _extract_key(self, audio: np.ndarray) -> tuple[str, float]:
        """
        Detecta la tonalidad musical.
        
        Args:
            audio: Señal de audio
            
        Returns:
            Tupla (key, confianza)
        """
        key_extractor = es.KeyExtractor()
        key, scale, confidence = key_extractor(audio)
        return f"{key} {scale}", float(confidence)
    
    def _extract_energy(self, audio: np.ndarray) -> float:
        """
        Calcula el nivel de energía.
        
        Args:
            audio: Señal de audio
            
        Returns:
            Nivel de energía normalizado (0-1)
        """
        energy = es.Energy()
        frame_size = 2048
        hop_size = 1024
        
        energies = []
        for frame in es.FrameGenerator(audio, frameSize=frame_size, hopSize=hop_size):
            energies.append(energy(frame))
        
        # Normalizar a 0-1
        energies = np.array(energies)
        if len(energies) > 0:
            return float(np.mean(energies) / np.max(energies))
        return 0.0
    
    def _extract_danceability(self, audio: np.ndarray) -> float:
        """
        Estima la bailabilidad.
        
        Args:
            audio: Señal de audio
            
        Returns:
            Score de bailabilidad (0-1)
        """
        danceability = es.Danceability()
        return float(danceability(audio))
    
    def _extract_segments(
        self,
        audio: np.ndarray,
        min_duration: float = 1.0
    ) -> list[dict[str, Any]]:
        """
        Detecta segmentos musicales.
        
        Args:
            audio: Señal de audio
            min_duration: Duración mínima de segmento
            
        Returns:
            Lista de segmentos con timestamps
        """
        # Detector de novedades
        novelty = es.NoveltyCurve()
        novelty_curve = novelty(audio)
        
        # Detector de picos
        peaks = es.PeakDetection()
        peak_positions, peak_values = peaks(novelty_curve)
        
        # Convertir a timestamps
        sample_rate = 44100  # TODO: Obtener del archivo
        segments = []
        
        for i, (pos, val) in enumerate(zip(peak_positions, peak_values, strict=False)):
            start = float(pos) / sample_rate
            
            # Fin del segmento
            if i < len(peak_positions) - 1:
                end = float(peak_positions[i + 1]) / sample_rate
            else:
                end = float(len(audio)) / sample_rate
            
            duration = end - start
            
            # Filtrar segmentos muy cortos
            if duration >= min_duration:
                segments.append({
                    'start': start,
                    'end': end,
                    'duration': duration,
                    'confidence': float(val)
                })
        
        return segments
    
    def get_key_distance(self, key1: str, key2: str) -> int:
        """
        Calcula la distancia entre dos tonalidades en el círculo de quintas.
        
        Args:
            key1: Primera tonalidad (ej: "C major")
            key2: Segunda tonalidad
            
        Returns:
            Distancia en pasos
        """
        # Mapeo de notas a posiciones en círculo de quintas
        circle = {
            'C': 0, 'G': 1, 'D': 2, 'A': 3, 'E': 4, 'B': 5, 'F#': 6,
            'C#': 7, 'G#': 8, 'D#': 9, 'A#': 10, 'F': 11
        }
        
        # Extraer nota y escala
        note1, scale1 = key1.split()
        note2, scale2 = key2.split()
        
        # Convertir a posición en círculo
        pos1 = circle.get(note1, 0)
        pos2 = circle.get(note2, 0)
        
        # Calcular distancia menor
        distance = min(
            abs(pos1 - pos2),
            12 - abs(pos1 - pos2)
        )
        
        # Ajustar por escala
        if scale1 != scale2:
            distance += 3  # Penalización por cambio de escala
        
        return distance
    
    def get_compatible_keys(
        self,
        key: str,
        max_distance: int = 2
    ) -> list[str]:
        """
        Obtiene tonalidades compatibles musicalmente.
        
        Args:
            key: Tonalidad base
            max_distance: Distancia máxima en círculo de quintas
            
        Returns:
            Lista de tonalidades compatibles
        """
        result = []
        
        # Todas las posibles tonalidades
        notes = ['C', 'G', 'D', 'A', 'E', 'B', 'F#', 'C#', 'G#', 'D#', 'A#', 'F']
        scales = ['major', 'minor']
        
        for note in notes:
            for scale in scales:
                test_key = f"{note} {scale}"
                distance = self.get_key_distance(key, test_key)
                
                if distance <= max_distance:
                    result.append(test_key)
        
        return result
    
    def estimate_sections(
        self,
        audio: np.ndarray,
        duration: float
    ) -> list[dict[str, Any]]:
        """
        Estima la estructura de secciones musicales.
        
        Args:
            audio: Señal de audio
            duration: Duración en segundos
            
        Returns:
            Lista de secciones con tipo y timestamps
        """
        # TODO: Implementar detección de secciones (intro, verso, estribillo, etc)
        return []
    
    def analyze_track(self, track) -> dict[str, Any]:
        """
        Analiza un track específico.
        
        Args:
            track: Track a analizar (debe tener atributo file_path)
            
        Returns:
            Diccionario con resultados del análisis
        """
        if hasattr(track, 'file_path'):
            return self.analyze_file(track.file_path)
        else:
            # Si track es una string (ruta de archivo)
            return self.analyze_file(str(track))
    
    def analyze_batch(self, tracks: list, features: list[str] | None = None) -> dict[str, dict[str, Any]]:
        """
        Analiza múltiples tracks en lote.
        
        Args:
            tracks: Lista de tracks a analizar
            features: Lista de características a extraer
            
        Returns:
            Diccionario con resultados por track
        """
        file_paths = []
        for track in tracks:
            if hasattr(track, 'file_path'):
                file_paths.append(track.file_path)
            else:
                file_paths.append(str(track))
        
        return self.batch_analyze(file_paths, features)
    
    async def analyze_async(self, track, features: list[str] | None = None) -> dict[str, Any]:
        """
        Analiza un track de forma asíncrona.
        
        Args:
            track: Track a analizar
            features: Lista de características a extraer
            
        Returns:
            Diccionario con resultados del análisis
        """
        import asyncio
        
        # Ejecutar análisis en un thread pool
        loop = asyncio.get_event_loop()
        
        if hasattr(track, 'file_path'):
            file_path = track.file_path
        else:
            file_path = str(track)
        
        return await loop.run_in_executor(
            None, 
            self.analyze_file, 
            file_path, 
            features
        )

# Instancia global
_analyzer: AudioAnalyzer | None = None

def get_analyzer() -> AudioAnalyzer:
    """Obtiene la instancia global del analizador."""
    global _analyzer
    if _analyzer is None:
        _analyzer = AudioAnalyzer()
    return _analyzer
