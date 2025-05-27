Testing
=======

Esta guía describe el sistema de pruebas de Nueva Biblioteca.

Estructura
---------

El proyecto utiliza pytest y sigue una estructura organizada de tests:

.. code-block:: text

    tests/
    ├── conftest.py          # Configuración común y fixtures
    ├── unit/               # Tests unitarios
    │   ├── test_audio_analyzer.py
    │   ├── test_metadata.py
    │   ├── test_player.py
    │   ├── test_recommender.py
    │   └── test_file_scanner.py
    └── integration/        # Tests de integración
        ├── test_library.py
        ├── test_playlists.py
        └── test_ui.py

Dependencias
-----------

Las dependencias de testing están definidas en requirements.txt:

- pytest: Framework principal de testing
- pytest-cov: Cobertura de código
- pytest-mock: Mocking y spies
- pytest-asyncio: Soporte para tests asíncronos
- pytest-qt: Testing de interfaces Qt

Ejecutando Tests
--------------

Ejecutar todos los tests::

    python scripts/run_tests.py

Con reporte de cobertura::

    python scripts/run_tests.py --coverage

Ejecutar tests específicos::

    pytest tests/unit/test_metadata.py
    pytest tests/integration/test_library.py

Tests Unitarios
-------------

Los tests unitarios verifican componentes individuales:

Audio Analyzer
~~~~~~~~~~~~

- Detección de BPM
- Identificación de tonalidad
- Análisis de energía
- Manejo de errores

Metadata
~~~~~~~

- Lectura de tags
- Escritura de tags
- Extracción de carátulas
- Actualización por lotes

Player
~~~~~

- Reproducción de audio
- Control de volumen
- Navegación de tracks
- Estados de reproducción

Recommender
~~~~~~~~~

- Extracción de características
- Cálculo de similitud
- Generación de recomendaciones
- Caché de resultados

File Scanner
~~~~~~~~~~

- Escaneo de directorios
- Parseo de nombres de archivo
- Detección de formatos
- Actualización de biblioteca

Tests de Integración
------------------

Los tests de integración verifican el funcionamiento conjunto:

Biblioteca
~~~~~~~~

- Escaneo y metadata
- Reproducción y análisis
- Sistema de recomendaciones
- Gestión de playlists

Playlists Inteligentes
~~~~~~~~~~~~~~~~~~~

- Reglas por género
- Rangos de BPM
- Condiciones múltiples
- Reglas anidadas
- Actualización dinámica

Interfaz de Usuario
~~~~~~~~~~~~~~~~

- Visualización de biblioteca
- Controles de reproducción
- Gestión de playlists
- Búsqueda y filtrado
- Edición de metadatos

Fixtures
-------

El archivo conftest.py define fixtures comunes:

- test_config: Configuración de prueba
- test_repository: Repositorio con base de datos en memoria
- music_dir: Directorio con archivos de prueba
- sample_tracks: Tracks de ejemplo
- sample_playlist: Playlist de ejemplo

Mocking
------

Se utilizan mocks para:

- Reproducción de audio (sounddevice)
- Análisis de audio (librosa)
- Operaciones de archivo
- Cálculos intensivos

Ejemplo::

    def test_audio_analysis(mocker):
        mock_load = mocker.patch("librosa.load")
        mock_load.return_value = (
            [0.0] * 44100,  # Audio simulado
            44100           # Sample rate
        )

Cobertura
--------

Se busca mantener una cobertura mínima del 80%:

- Core: 90%
- Data: 85%
- Utils: 80%
- UI: 75%

El reporte de cobertura se genera en HTML y XML.

Testing de UI
-----------

Se utiliza pytest-qt para testing de interfaces:

- Simulación de eventos
- Verificación de estados
- Interacción con diálogos
- Manejo de señales

Ejemplo::

    def test_playback(qtbot, main_window):
        qtbot.mouseClick(
            main_window.player_controls.play_button,
            Qt.MouseButton.LeftButton
        )

Testing Asíncrono
---------------

Para tests asíncronos::

    @pytest.mark.asyncio
    async def test_async_feature():
        result = await async_function()
        assert result is not None

Integración Continua
------------------

Los tests se ejecutan automáticamente en CI:

- Push a main
- Pull requests
- Releases

Ver :doc:`/development/ci_cd` para más detalles.

Mejores Prácticas
---------------

1. Mantener tests pequeños y enfocados
2. Usar nombres descriptivos
3. Documentar casos de prueba
4. Evitar dependencias entre tests
5. Mantener fixtures livianos
6. Usar type hints en tests
7. Capturar y verificar logs
8. Limpiar recursos en teardown
