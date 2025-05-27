# Instalación - Nueva Biblioteca

## Requisitos del Sistema

- Python 3.11 o superior
- PyQt6
- Dependencias de audio (ver requirements.txt)

## Instalación

### 1. Clonar el repositorio
```bash
git clone <repository-url>
cd nueva-biblioteca
```

### 2. Crear entorno virtual
```bash
python3 -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate
```

### 3. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 4. Instalar el paquete en modo desarrollo
```bash
pip install -e .
```

## Ejecución

### Opción 1: Script directo
```bash
python run.py
```

### Opción 2: Módulo instalado
```bash
python -m nueva_biblioteca
```

### Opción 3: Comando directo (si está en PATH)
```bash
nueva-biblioteca
```

## Desarrollo

### Ejecutar tests
```bash
pytest tests/
```

### Verificar calidad de código
```bash
ruff check src/
mypy src/ --ignore-missing-imports
```

### Formatear código
```bash
ruff format src/
```

## Estructura del Proyecto

```
nueva-biblioteca/
├── src/nueva_biblioteca/    # Código fuente principal
│   ├── core/               # Lógica de negocio
│   ├── data/               # Modelos y repositorio
│   ├── ui/                 # Interfaz de usuario
│   └── utils/              # Utilidades
├── tests/                  # Tests
├── docs/                   # Documentación
└── requirements.txt        # Dependencias
```

## Solución de Problemas

### Error de dependencias de audio
Si hay problemas con librosa o sounddevice:
```bash
# En Ubuntu/Debian
sudo apt-get install libsndfile1 portaudio19-dev

# En macOS
brew install portaudio

# En Windows
# Instalar Microsoft Visual C++ Build Tools
```

### Error de PyQt6
```bash
pip install --upgrade PyQt6
```

### Problemas de permisos
```bash
# Asegurar permisos de ejecución
chmod +x run.py
``` 