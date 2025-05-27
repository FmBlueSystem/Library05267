#!/usr/bin/env python3
"""
Script de Optimización de Rendimiento - Nueva Biblioteca
======================================================

Optimiza el rendimiento del proyecto mediante varias técnicas:
- Análisis de imports lentos
- Optimización de consultas de base de datos
- Caché de operaciones costosas
- Perfilado de código crítico
"""

import cProfile
import io
import pstats
import time
from pathlib import Path
from typing import Any, Dict, List

import psutil


class PerformanceOptimizer:
    """Optimizador de rendimiento para Nueva Biblioteca."""
    
    def __init__(self):
        """Inicializa el optimizador."""
        self.results: Dict[str, Any] = {}
        self.start_time = time.time()
    
    def analyze_imports(self) -> Dict[str, float]:
        """
        Analiza el tiempo de importación de módulos.
        
        Returns:
            Diccionario con tiempos de importación
        """
        print("🔍 Analizando tiempos de importación...")
        
        import_times = {}
        modules_to_test = [
            'nueva_biblioteca.data.models',
            'nueva_biblioteca.data.repository',
            'nueva_biblioteca.utils.config',
            'nueva_biblioteca.utils.logger',
            'nueva_biblioteca.core.metadata',
            'nueva_biblioteca.core.audio_analyzer',
            'nueva_biblioteca.ui.main_window',
        ]
        
        for module in modules_to_test:
            start = time.time()
            try:
                __import__(module)
                import_time = time.time() - start
                import_times[module] = import_time
                print(f"  ✓ {module}: {import_time:.3f}s")
            except ImportError as e:
                print(f"  ✗ {module}: Error - {e}")
                import_times[module] = -1
        
        # Ordenar por tiempo
        sorted_times = sorted(
            [(k, v) for k, v in import_times.items() if v > 0],
            key=lambda x: x[1],
            reverse=True
        )
        
        print(f"\n📊 Módulos más lentos:")
        for module, time_taken in sorted_times[:5]:
            print(f"  {module}: {time_taken:.3f}s")
        
        self.results['import_times'] = import_times
        return import_times
    
    def profile_database_operations(self) -> Dict[str, float]:
        """
        Perfila operaciones de base de datos.
        
        Returns:
            Diccionario con tiempos de operaciones
        """
        print("\n🗄️ Perfilando operaciones de base de datos...")
        
        try:
            from nueva_biblioteca.data.repository import Repository
            from nueva_biblioteca.data.models import Track, Playlist
            
            repo = Repository()
            operation_times = {}
            
            # Test de creación de track
            start = time.time()
            track_data = {
                "file_path": "/test/performance_test.mp3",
                "title": "Performance Test Track",
                "artist": "Test Artist",
                "duration": 180.0
            }
            saved_track = repo.add_track(track_data)
            operation_times['save_track'] = time.time() - start
            
            # Test de búsqueda
            start = time.time()
            found_tracks = repo.search_tracks("Performance")
            operation_times['search_tracks'] = time.time() - start
            
            # Test de obtener todos los tracks
            start = time.time()
            all_tracks = repo.get_all_tracks()
            operation_times['get_all_tracks'] = time.time() - start
            
            # Test de creación de playlist
            start = time.time()
            saved_playlist = repo.create_playlist(
                name="Performance Test Playlist",
                description="Test playlist for performance"
            )
            if saved_track and saved_playlist:
                repo.add_track_to_playlist(saved_playlist.id, saved_track.id)
            operation_times['save_playlist'] = time.time() - start
            
            # Limpiar datos de test
            if saved_playlist:
                repo.delete_playlist(saved_playlist.id)
            if saved_track:
                repo.delete_track(saved_track.id)
            
            for operation, time_taken in operation_times.items():
                print(f"  ✓ {operation}: {time_taken:.3f}s")
            
            self.results['db_operations'] = operation_times
            return operation_times
            
        except Exception as e:
            print(f"  ✗ Error en operaciones de DB: {e}")
            return {}
    
    def analyze_memory_usage(self) -> Dict[str, float]:
        """
        Analiza el uso de memoria.
        
        Returns:
            Diccionario con métricas de memoria
        """
        print("\n🧠 Analizando uso de memoria...")
        
        process = psutil.Process()
        memory_info = process.memory_info()
        
        memory_metrics = {
            'rss_mb': memory_info.rss / 1024 / 1024,  # Resident Set Size
            'vms_mb': memory_info.vms / 1024 / 1024,  # Virtual Memory Size
            'percent': process.memory_percent(),
        }
        
        print(f"  📊 Memoria RSS: {memory_metrics['rss_mb']:.1f} MB")
        print(f"  📊 Memoria Virtual: {memory_metrics['vms_mb']:.1f} MB")
        print(f"  📊 Porcentaje del sistema: {memory_metrics['percent']:.1f}%")
        
        self.results['memory'] = memory_metrics
        return memory_metrics
    
    def profile_critical_functions(self) -> str:
        """
        Perfila funciones críticas usando cProfile.
        
        Returns:
            Reporte de perfilado
        """
        print("\n⚡ Perfilando funciones críticas...")
        
        def test_critical_operations():
            """Función que ejecuta operaciones críticas para perfilar."""
            try:
                # Test de configuración
                from nueva_biblioteca.utils.config import get_config
                config = get_config()
                
                # Test de logging
                from nueva_biblioteca.utils.logger import get_logger
                logger = get_logger(__name__)
                logger.info("Test de rendimiento")
                
                # Test de modelos
                from nueva_biblioteca.data.models import Track
                for i in range(100):
                    track = Track(
                        file_path=f"/test/track_{i}.mp3",
                        title=f"Track {i}",
                        artist="Test Artist"
                    )
                
            except Exception as e:
                print(f"Error en operaciones críticas: {e}")
        
        # Ejecutar perfilado
        profiler = cProfile.Profile()
        profiler.enable()
        test_critical_operations()
        profiler.disable()
        
        # Generar reporte
        stream = io.StringIO()
        stats = pstats.Stats(profiler, stream=stream)
        stats.sort_stats('cumulative')
        stats.print_stats(20)  # Top 20 funciones
        
        profile_report = stream.getvalue()
        print("  ✓ Perfilado completado")
        
        self.results['profile_report'] = profile_report
        return profile_report
    
    def generate_optimization_recommendations(self) -> List[str]:
        """
        Genera recomendaciones de optimización.
        
        Returns:
            Lista de recomendaciones
        """
        print("\n💡 Generando recomendaciones de optimización...")
        
        recommendations = []
        
        # Analizar tiempos de importación
        if 'import_times' in self.results:
            slow_imports = [
                (k, v) for k, v in self.results['import_times'].items()
                if v > 0.1  # Más de 100ms
            ]
            if slow_imports:
                recommendations.append(
                    f"🐌 Optimizar imports lentos: {', '.join([k for k, v in slow_imports])}"
                )
        
        # Analizar operaciones de DB
        if 'db_operations' in self.results:
            slow_ops = [
                (k, v) for k, v in self.results['db_operations'].items()
                if v > 0.05  # Más de 50ms
            ]
            if slow_ops:
                recommendations.append(
                    f"🗄️ Optimizar operaciones de DB: {', '.join([k for k, v in slow_ops])}"
                )
        
        # Analizar memoria
        if 'memory' in self.results:
            if self.results['memory']['rss_mb'] > 100:
                recommendations.append(
                    "🧠 Considerar optimización de memoria (>100MB en uso)"
                )
        
        # Recomendaciones generales
        recommendations.extend([
            "⚡ Implementar lazy loading para módulos pesados",
            "🔄 Agregar caché para operaciones repetitivas",
            "📦 Considerar usar SQLite con WAL mode para mejor concurrencia",
            "🎯 Implementar índices en columnas de búsqueda frecuente",
            "🚀 Usar connection pooling para operaciones de DB intensivas"
        ])
        
        for i, rec in enumerate(recommendations, 1):
            print(f"  {i}. {rec}")
        
        self.results['recommendations'] = recommendations
        return recommendations
    
    def save_report(self, output_file: str = "performance_report.md") -> None:
        """
        Guarda un reporte completo de rendimiento.
        
        Args:
            output_file: Archivo donde guardar el reporte
        """
        total_time = time.time() - self.start_time
        
        report = f"""# Reporte de Rendimiento - Nueva Biblioteca

## Resumen Ejecutivo
- **Tiempo total de análisis:** {total_time:.2f}s
- **Fecha:** {time.strftime('%Y-%m-%d %H:%M:%S')}

## Métricas de Rendimiento

### Tiempos de Importación
"""
        
        if 'import_times' in self.results:
            for module, time_taken in self.results['import_times'].items():
                if time_taken > 0:
                    report += f"- `{module}`: {time_taken:.3f}s\n"
        
        report += "\n### Operaciones de Base de Datos\n"
        if 'db_operations' in self.results:
            for operation, time_taken in self.results['db_operations'].items():
                report += f"- `{operation}`: {time_taken:.3f}s\n"
        
        report += "\n### Uso de Memoria\n"
        if 'memory' in self.results:
            memory = self.results['memory']
            report += f"- **RSS:** {memory['rss_mb']:.1f} MB\n"
            report += f"- **Virtual:** {memory['vms_mb']:.1f} MB\n"
            report += f"- **Porcentaje del sistema:** {memory['percent']:.1f}%\n"
        
        report += "\n## Recomendaciones de Optimización\n"
        if 'recommendations' in self.results:
            for i, rec in enumerate(self.results['recommendations'], 1):
                report += f"{i}. {rec}\n"
        
        if 'profile_report' in self.results:
            report += f"\n## Reporte de Perfilado\n```\n{self.results['profile_report']}\n```\n"
        
        Path(output_file).write_text(report)
        print(f"\n📄 Reporte guardado en: {output_file}")
    
    def run_full_analysis(self) -> None:
        """Ejecuta análisis completo de rendimiento."""
        print("🚀 Iniciando análisis completo de rendimiento...\n")
        
        self.analyze_imports()
        self.profile_database_operations()
        self.analyze_memory_usage()
        self.profile_critical_functions()
        self.generate_optimization_recommendations()
        self.save_report()
        
        total_time = time.time() - self.start_time
        print(f"\n✅ Análisis completado en {total_time:.2f}s")


def main():
    """Función principal."""
    optimizer = PerformanceOptimizer()
    optimizer.run_full_analysis()


if __name__ == "__main__":
    main() 