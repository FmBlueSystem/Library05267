#!/usr/bin/env python3
"""
Recomendador - Nueva Biblioteca
==========================

Sistema de recomendaciones musicales basado en similitud de metadatos.
"""

from typing import Any, ClassVar

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler

from nueva_biblioteca.data.models import Track
from nueva_biblioteca.data.repository import Repository
from nueva_biblioteca.utils.cache_manager import get_cache
from nueva_biblioteca.utils.logger import get_logger

logger = get_logger(__name__)

class Recommender:
    """
    Sistema de recomendaciones musicales.
    
    Características:
    - Recomendaciones por metadatos
    - Filtros por género y año
    - Cache de resultados
    """
    
    # Pesos por defecto para cada característica
    DEFAULT_WEIGHTS: ClassVar[dict[str, float]] = {
        'genre': 0.6,
        'year': 0.4
    }
    
    def __init__(self, repository: Repository):
        """
        Inicializa el recomendador.
        
        Args:
            repository: Repositorio de datos
        """
        self.repository = repository
        self.cache = get_cache()
        self._scaler = StandardScaler()
    
    def get_similar_tracks(
        self,
        track: Track,
        limit: int = 10,
        min_score: float = 0.5,
        weights: dict[str, float] | None = None
    ) -> list[tuple[Track, float]]:
        """
        Obtiene tracks similares a uno dado.
        
        Args:
            track: Track base
            limit: Máximo de resultados
            min_score: Score mínimo de similitud
            weights: Pesos personalizados
            
        Returns:
            Lista de tuplas (track, score)
        """
        try:
            # Verificar caché
            cache_key = f"similar:{track.id}:{limit}:{min_score}"
            if weights:
                cache_key += ":".join(f"{k}={v}" for k, v in sorted(weights.items()))
            
            cached = self.cache.get(cache_key)
            if cached:
                return cached
            
            # Obtener características del track base
            base_features = self._get_track_features(track)
            if not base_features:
                return []
            
            # Obtener todos los tracks
            all_tracks = self.repository.get_all_tracks()
            if not all_tracks:
                return []
            
            # Calcular similitud con cada track
            similarities = []
            
            for other in all_tracks:
                if other.id == track.id:
                    continue
                    
                # Obtener características
                other_features = self._get_track_features(other)
                if not other_features:
                    continue
                
                # Calcular score
                score = self._calculate_similarity(
                    base_features,
                    other_features,
                    weights or self.DEFAULT_WEIGHTS
                )
                
                if score >= min_score:
                    similarities.append((other, score))
            
            # Ordenar por score
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Limitar resultados
            results = similarities[:limit]
            
            # Cachear resultados
            self.cache.set(cache_key, results, ttl=3600)  # 1 hora
            
            return results
            
        except Exception as e:
            logger.error(f"Error obteniendo tracks similares: {e}")
            return []
    
    def get_recommendations(
        self,
        seed_tracks: list[Track],
        limit: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[Track]:
        """
        Genera recomendaciones basadas en múltiples tracks.
        
        Args:
            seed_tracks: Tracks base
            limit: Máximo de resultados
            filters: Filtros adicionales
            
        Returns:
            Lista de tracks recomendados
        """
        try:
            if not seed_tracks:
                return []
            
            # Verificar caché
            cache_key = f"recommendations:{','.join(str(t.id) for t in seed_tracks)}"
            if filters:
                cache_key += ":".join(f"{k}={v}" for k, v in sorted(filters.items()))
            
            cached = self.cache.get(cache_key)
            if cached:
                return cached
            
            # Obtener características promedio de seeds
            avg_features = {}
            
            for feature in self.DEFAULT_WEIGHTS:
                values = []
                
                for track in seed_tracks:
                    features = self._get_track_features(track)
                    if features and feature in features:
                        values.append(features[feature])
                
                if values:
                    avg_features[feature] = np.mean(values)
            
            if not avg_features:
                return []
            
            # Obtener todos los tracks que cumplan filtros
            candidates = self.repository.get_tracks(filters=filters)
            
            # Calcular similitud con características promedio
            similarities = []
            
            for track in candidates:
                if track.id in [t.id for t in seed_tracks]:
                    continue
                
                features = self._get_track_features(track)
                if not features:
                    continue
                
                score = self._calculate_similarity(
                    avg_features,
                    features,
                    self.DEFAULT_WEIGHTS
                )
                
                if score >= 0.5:  # Score mínimo
                    similarities.append((track, score))
            
            # Ordenar por score
            similarities.sort(key=lambda x: x[1], reverse=True)
            
            # Obtener solo los tracks
            results = [t for t, _ in similarities[:limit]]
            
            # Cachear resultados
            self.cache.set(cache_key, results, ttl=3600)  # 1 hora
            
            return results
            
        except Exception as e:
            logger.error(f"Error generando recomendaciones: {e}")
            return []
    
    def _get_track_features(self, track: Track) -> dict[str, float] | None:
        """
        Extrae características de un track.
        
        Args:
            track: Track a analizar
            
        Returns:
            Diccionario de características o None si error
        """
        try:
            features = {}
            
            # Género (one-hot encoding simple)
            if track.genre:
                features['genre'] = hash(track.genre) % 100 / 100.0
            else:
                features['genre'] = 0.0
            
            # Año (normalizado)
            if track.year:
                features['year'] = (track.year - 1900) / 200.0  # Normalizar a 0-1
            else:
                features['year'] = 0.5  # Valor por defecto
            
            return features
            
        except Exception as e:
            logger.error(f"Error extrayendo características: {e}")
            return None
    
    def _calculate_similarity(
        self,
        features1: dict[str, float],
        features2: dict[str, float],
        weights: dict[str, float]
    ) -> float:
        """
        Calcula la similitud entre dos conjuntos de características.
        
        Args:
            features1: Primer conjunto de características
            features2: Segundo conjunto de características
            weights: Pesos para cada característica
            
        Returns:
            Score de similitud (0-1)
        """
        try:
            # Verificar características comunes
            common_features = set(features1.keys()) & set(features2.keys())
            if not common_features:
                return 0.0
            
            # Crear vectores
            vec1 = []
            vec2 = []
            feature_weights = []
            
            for feature in common_features:
                vec1.append(features1[feature])
                vec2.append(features2[feature])
                feature_weights.append(weights.get(feature, 1.0))
            
            # Convertir a arrays
            vec1 = np.array(vec1).reshape(1, -1)
            vec2 = np.array(vec2).reshape(1, -1)
            feature_weights = np.array(feature_weights)
            
            # Aplicar pesos
            vec1 = vec1 * feature_weights
            vec2 = vec2 * feature_weights
            
            # Calcular similitud coseno
            similarity = cosine_similarity(vec1, vec2)[0][0]
            
            return float(similarity)
            
        except Exception as e:
            logger.error(f"Error calculando similitud: {e}")
            return 0.0

def get_recommender(repository: Repository) -> Recommender:
    """Obtiene la instancia global del recomendador."""
    return Recommender(repository)
