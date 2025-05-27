Guía de Estilo
=============

Esta guía establece las convenciones de código para Nueva Biblioteca.

Principios Generales
------------------

1. Claridad sobre ingenio
2. Consistencia en todo el código
3. Explícito mejor que implícito
4. Tipo estático cuando sea posible
5. Documentación completa y clara

PEP 8
-----

Seguimos PEP 8 con algunas modificaciones:

.. code-block:: python

    # Correcto
    def calculate_bpm(audio_data: np.ndarray, sample_rate: int) -> float:
        """Calcula los BPM de una señal de audio."""
        return result

    # Incorrecto
    def calculateBpm(audioData, sampleRate):
        # Sin tipos, sin docstring
        return result

Imports
-------

Organizar imports en grupos, separados por línea en blanco:

.. code-block:: python

    # Stdlib
    from typing import Optional, List
    from pathlib import Path
    import json

    # Dependencias externas
    import numpy as np
    from PyQt6.QtWidgets import QWidget
    import librosa

    # Módulos locales
    from nueva_biblioteca.core.player import Player
    from nueva_biblioteca.utils.config import Config

Type Hints
---------

Usar type hints en todas las funciones y clases:

.. code-block:: python

    from typing import Optional, List, Dict, Any

    def process_track(
        track: Track,
        options: Optional[Dict[str, Any]] = None
    ) -> List[float]:
        """Procesa un track con opciones."""
        return results

    class AudioProcessor:
        def __init__(self, config: Config) -> None:
            self.config = config

        def analyze(self, data: np.ndarray) -> Optional[Analysis]:
            return result

Docstrings
---------

Usar el estilo Google para docstrings:

.. code-block:: python

    def complex_function(
        param1: int,
        param2: str,
        *args: Any,
        **kwargs: Any
    ) -> Dict[str, Any]:
        """
        Descripción breve de la función.

        Descripción más detallada que puede
        ocupar múltiples líneas.

        Args:
            param1: Descripción del primer parámetro
            param2: Descripción del segundo parámetro
            *args: Argumentos variables
            **kwargs: Argumentos de palabra clave

        Returns:
            Diccionario con resultados

        Raises:
            ValueError: Si param1 es negativo
            RuntimeError: Si hay un error de procesamiento

        Example:
            >>> result = complex_function(1, "test")
            >>> print(result)
            {'status': 'ok'}
        """

Clases
------

.. code-block:: python

    class AudioPlayer:
        """
        Reproductor de audio.

        Attributes:
            volume: Nivel de volumen actual
            is_playing: Estado de reproducción
        """

        def __init__(self, config: Config) -> None:
            """
            Inicializa el reproductor.

            Args:
                config: Configuración del reproductor
            """
            self.volume = 1.0
            self.is_playing = False

Nombres
------

- Clases: CamelCase
- Funciones y variables: snake_case
- Constantes: MAYUSCULAS_CON_GUIONES
- Privado: _prefijo_guion_bajo

Variables
--------

.. code-block:: python

    # Constantes
    MAX_VOLUME = 1.0
    DEFAULT_SAMPLE_RATE = 44100

    # Variables
    current_track: Optional[Track] = None
    is_playing: bool = False
    volume_level: float = 0.5

Formateo de Cadenas
-----------------

Usar f-strings:

.. code-block:: python

    # Correcto
    message = f"Procesando {track.title} por {track.artist}"

    # Incorrecto
    message = "Procesando %s por %s" % (track.title, track.artist)
    message = "Procesando {} por {}".format(track.title, track.artist)

Manejo de Errores
---------------

.. code-block:: python

    try:
        result = process_audio(data)
    except AudioError as e:
        logger.error(f"Error procesando audio: {e}")
        raise ProcessingError("Fallo en procesamiento") from e

Comentarios
---------

- Usar comentarios para explicar "por qué", no "qué"
- Mantener comentarios actualizados con el código
- Evitar comentarios obvios

.. code-block:: python

    # Correcto
    # Aplicar ventana Hann para reducir efectos de borde
    windowed_data = data * np.hanning(len(data))

    # Incorrecto
    # Multiplicar por ventana
    windowed_data = data * np.hanning(len(data))

Testing
------

.. code-block:: python

    def test_complex_feature(
        self,
        mock_data: np.ndarray,
        expected_result: Dict[str, Any]
    ) -> None:
        """
        Prueba característica compleja.

        Args:
            mock_data: Datos simulados para la prueba
            expected_result: Resultado esperado
        """
        result = process_feature(mock_data)
        assert result == expected_result

Espaciado
--------

- 4 espacios para indentación
- Líneas máximo 88 caracteres
- Dos líneas en blanco entre clases
- Una línea en blanco entre métodos
- Una línea en blanco para agrupar código relacionado

Herramientas
----------

Usamos las siguientes herramientas:

- ruff: Linting y formateo
- mypy: Verificación de tipos
- black: Formateo (a través de ruff)
- isort: Ordenamiento de imports (a través de ruff)

Ver :doc:`/development/environment` para la configuración.
