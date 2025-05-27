# Nueva Biblioteca 🎵

Sistema de biblioteca musical con playlists inteligentes y análisis avanzado de audio.

## Características ✨

- **Gestión de Biblioteca**
  - Soporte para múltiples formatos (MP3, FLAC, M4A)
  - Organización automática de archivos
  - Edición de metadatos en lote
  - Búsqueda y filtrado avanzado

- **Playlists Inteligentes**
  - Creación basada en reglas
  - Actualización automática
  - Filtros por metadatos y análisis
  - Exportación a múltiples formatos

- **Análisis de Audio**
  - Detección de BPM
  - Identificación de tonalidad
  - Análisis de energía y danceability
  - Generación de espectrogramas

- **Sistema de Recomendaciones**
  - Recomendaciones basadas en similitud
  - Descubrimiento de música similar
  - Personalización por preferencias
  - Historial de reproducción

- **Interfaz Moderna**
  - Material Design 3
  - Soporte para HiDPI
  - Temas claro/oscuro
  - Animaciones fluidas

## Instalación 🚀

### Usando pip

```bash
# Instalación básica
pip install nueva-biblioteca

# Con características opcionales
pip install nueva-biblioteca[audio,gui]

# Instalación completa
pip install nueva-biblioteca[full]
```

### Desde el código fuente

```bash
# Clonar repositorio
git clone https://github.com/FmBlueSystem/nueva-biblioteca.git
cd nueva-biblioteca

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # Linux/macOS
.venv\Scripts\activate     # Windows

# Instalar dependencias
python -m pip install uv
uv pip install -e ".[dev]"
```

## Uso 📖

### Interfaz Gráfica

```bash
nueva-biblioteca-gui
```

### Línea de Comandos

```bash
# Escanear directorio
nueva-biblioteca scan ~/Música

# Analizar archivos
nueva-biblioteca analyze --batch ~/Música

# Exportar playlist
nueva-biblioteca export "Mi Playlist" --format m3u8
```

## Desarrollo 🛠️

### Configuración del Entorno

```bash
# Instalar dependencias de desarrollo
uv pip install -e ".[dev]"

# Instalar pre-commit hooks
pre-commit install
```

### Tests

```bash
# Ejecutar todos los tests
python scripts/run_tests.py

# Con cobertura
python scripts/run_tests.py --coverage
```

### Linting

```bash
# Verificar estilo y tipos
python scripts/lint.py

# Formatear código
ruff format
```

### Documentación

```bash
# Generar documentación
python scripts/generate_docs.py

# Servir documentación localmente
cd docs && python -m http.server
```

### Construcción

```bash
# Construir paquete
python scripts/build.py

# Crear ejecutable
python scripts/build.py --executable

# Crear instalador
python scripts/build.py --installer
```

## Estructura del Proyecto 📁

```
nueva-biblioteca/
├── src/
│   └── nueva_biblioteca/
│       ├── core/         # Lógica principal
│       ├── data/         # Modelos y repositorio
│       ├── ui/           # Interfaz de usuario
│       └── utils/        # Utilidades
├── tests/                # Tests unitarios y de integración
├── docs/                 # Documentación
└── scripts/              # Scripts de desarrollo
```

## Contribuir 🤝

1. Fork el proyecto
2. Crea una rama (`git checkout -b feature/nueva-caracteristica`)
3. Haz commit de tus cambios (`git commit -am "Agregar característica"`)
4. Push a la rama (`git push origin feature/nueva-caracteristica`)
5. Abre un Pull Request

## Licencia 📄

Este proyecto está licenciado bajo la Licencia MIT - ver el archivo [LICENSE](LICENSE) para más detalles.

## Créditos 👏

Desarrollado por [FmBlueSystem](https://fmbluesystem.com).

Iconos por [Material Design](https://material.io/icons/).
