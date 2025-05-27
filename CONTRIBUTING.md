# Guía de Contribución - Nueva Biblioteca 🤝

¡Gracias por tu interés en contribuir a **Nueva Biblioteca**! Esta guía te ayudará a empezar y seguir las mejores prácticas del proyecto.

## 📋 Gestión de Tareas

**⚠️ IMPORTANTE:** Este proyecto utiliza **Dart AI** para la gestión de tareas.

🔗 **[Consulta PROJECT_MANAGEMENT.md](PROJECT_MANAGEMENT.md)** para instrucciones detalladas sobre:
- Acceso a Dart AI
- Flujo de trabajo
- Comunicación en tareas
- Prioridades del proyecto

## 🚀 Primeros Pasos

### 1. Configuración del Entorno

```bash
# Clonar el repositorio
git clone https://github.com/FmBlueSystem/Library05267.git
cd Library05267

# Crear entorno virtual
python -m venv .venv
source .venv/bin/activate  # En Windows: .venv\Scripts\activate

# Instalar dependencias de desarrollo
pip install -r requirements.txt
pip install -e .

# Instalar herramientas de desarrollo
pip install pytest pytest-cov black ruff mypy pre-commit

# Configurar pre-commit hooks
pre-commit install
```

### 2. Verificar Instalación

```bash
# Ejecutar tests
pytest

# Verificar linting
ruff check src/
mypy src/

# Ejecutar la aplicación
python run_gui.py
```

## 📝 Proceso de Contribución

### 1. Antes de Empezar
1. **Consulta Dart AI** para ver tareas disponibles
2. **Asígnate una tarea** o solicita asignación
3. **Lee la descripción completa** y dependencias
4. **Comenta en la tarea** que vas a empezar

### 2. Desarrollo

#### Crear Rama
```bash
# Crear rama desde main
git checkout main
git pull origin main
git checkout -b feature/nombre-funcionalidad

# O para bugs
git checkout -b fix/descripcion-bug
```

#### Convenciones de Nombres
- **Features:** `feature/sistema-cola-reproduccion`
- **Bugs:** `fix/error-reproduccion-mp3`
- **Docs:** `docs/actualizar-readme`
- **Refactor:** `refactor/optimizar-base-datos`

### 3. Estándares de Código

#### Formato y Linting
```bash
# Formatear código
black src/ tests/

# Verificar linting
ruff check src/ tests/

# Verificar tipos
mypy src/
```

#### Estructura de Commits
```bash
# Formato: tipo(scope): descripción - Tarea #123
git commit -m "feat(player): implementar crossfade - Tarea #456"
git commit -m "fix(ui): corregir botón shuffle - Tarea #789"
git commit -m "docs(readme): actualizar instalación - Tarea #012"
```

**Tipos de commit:**
- `feat` - Nueva funcionalidad
- `fix` - Corrección de bug
- `docs` - Documentación
- `style` - Formato (sin cambios de código)
- `refactor` - Refactoring
- `test` - Añadir/modificar tests
- `chore` - Tareas de mantenimiento

### 4. Testing

#### Escribir Tests
```python
# tests/unit/test_nueva_funcionalidad.py
import pytest
from nueva_biblioteca.core.nueva_funcionalidad import NuevaClase

class TestNuevaClase:
    def test_metodo_principal(self):
        # Arrange
        instancia = NuevaClase()
        
        # Act
        resultado = instancia.metodo_principal()
        
        # Assert
        assert resultado == valor_esperado
```

#### Ejecutar Tests
```bash
# Todos los tests
pytest

# Con cobertura
pytest --cov=nueva_biblioteca --cov-report=html

# Tests específicos
pytest tests/unit/test_player.py::TestPlayer::test_play
```

### 5. Documentación

#### Docstrings
```python
def nueva_funcion(parametro: str, opcional: int = 0) -> bool:
    """
    Descripción breve de la función.
    
    Args:
        parametro: Descripción del parámetro
        opcional: Parámetro opcional con valor por defecto
        
    Returns:
        True si la operación fue exitosa, False en caso contrario
        
    Raises:
        ValueError: Si el parámetro no es válido
        
    Example:
        >>> nueva_funcion("test", 5)
        True
    """
    pass
```

#### Comentarios en Código
```python
# Comentarios en español para explicar lógica compleja
# Evitar comentarios obvios

# ✅ Bueno
# Calcular el crossfade basado en la posición actual
fade_factor = calculate_fade_position(current_time, total_duration)

# ❌ Malo
# Asignar valor a variable
fade_factor = 0.5
```

## 🔄 Pull Request Process

### 1. Preparar PR
```bash
# Asegurar que está actualizado
git checkout main
git pull origin main
git checkout feature/mi-rama
git rebase main

# Push de la rama
git push origin feature/mi-rama
```

### 2. Crear Pull Request

**Título:** `feat: Implementar sistema de crossfade - Tarea #456`

**Descripción:**
```markdown
## 📋 Tarea Relacionada
Dart AI Tarea #456: [Enlace a la tarea]

## 🎯 Descripción
Implementación del sistema de crossfade para transiciones suaves entre tracks.

## ✅ Cambios Realizados
- [ ] Añadido algoritmo de crossfade en `player.py`
- [ ] Implementados controles de UI para ajustar duración
- [ ] Añadidos tests unitarios
- [ ] Actualizada documentación

## 🧪 Testing
- [ ] Tests unitarios pasan
- [ ] Tests de integración pasan
- [ ] Probado manualmente en diferentes formatos de audio

## 📸 Screenshots (si aplica)
[Capturas de pantalla de cambios en UI]

## 🔗 Referencias
- Documentación de crossfade: [enlace]
- Issue relacionado: #123
```

### 3. Review Process
1. **Automated checks** deben pasar
2. **Code review** por al menos un colaborador
3. **Testing** en diferentes entornos
4. **Actualizar tarea en Dart AI** con el estado

## 🐛 Reportar Bugs

### 1. Verificar Duplicados
- Busca en **Dart AI** si ya existe la tarea
- Revisa issues cerrados en GitHub

### 2. Crear Tarea en Dart AI
```markdown
**Título:** Error en reproducción de archivos MP3 con metadatos especiales

**Descripción:**
- **Comportamiento esperado:** El archivo debería reproducirse normalmente
- **Comportamiento actual:** La aplicación se congela
- **Pasos para reproducir:**
  1. Abrir archivo MP3 con metadatos Unicode
  2. Hacer doble clic para reproducir
  3. Observar congelamiento

**Entorno:**
- OS: macOS 14.0
- Python: 3.11.5
- PyQt6: 6.5.0

**Archivos de ejemplo:** [adjuntar si es posible]
```

## 💡 Sugerir Funcionalidades

### 1. Discusión Previa
- Crea una tarea en **Dart AI** con etiqueta `enhancement`
- Describe el caso de uso y beneficios
- Espera feedback del equipo antes de implementar

### 2. Propuesta Detallada
```markdown
**Funcionalidad:** Integración con Spotify API

**Justificación:**
- Permitir importar playlists desde Spotify
- Sincronizar favoritos
- Mejorar experiencia de usuario

**Implementación Propuesta:**
- Usar Spotify Web API
- Añadir configuración de credenciales
- Crear widget de importación

**Consideraciones:**
- Términos de servicio de Spotify
- Limitaciones de rate limiting
- Privacidad de datos del usuario
```

## 🏷️ Etiquetas y Categorización

### En Dart AI
- `bug` - Errores y problemas
- `feature` - Nuevas funcionalidades
- `enhancement` - Mejoras a funcionalidades existentes
- `docs` - Documentación
- `performance` - Optimizaciones
- `ui/ux` - Mejoras de interfaz

### Prioridades
- `critical` - Bloquea funcionalidad principal
- `high` - Importante para próximo release
- `medium` - Deseable pero no urgente
- `low` - Nice to have

## 📞 Comunicación

### Canales Principales
1. **Dart AI** - Comunicación principal en tareas
2. **GitHub Issues** - Solo para bugs críticos
3. **Pull Request Comments** - Discusión de código específico

### Mejores Prácticas
- **Sé específico** en descripciones
- **Incluye contexto** técnico relevante
- **Menciona dependencias** con otras tareas
- **Actualiza regularmente** el progreso
- **Pide ayuda** cuando la necesites

## 🎯 Objetivos de Calidad

### Cobertura de Tests
- **Mínimo 80%** de cobertura general
- **90%+ para core modules** (player, queue, etc.)
- **Tests de integración** para flujos principales

### Performance
- **Tiempo de inicio** < 3 segundos
- **Carga de biblioteca** < 5 segundos para 10k tracks
- **Uso de memoria** < 200MB en idle

### Compatibilidad
- **Python 3.11+**
- **PyQt6 6.5+**
- **macOS, Windows, Linux**

---

¡Gracias por contribuir a **Nueva Biblioteca**! Tu trabajo ayuda a crear una mejor experiencia musical para todos. 🎵✨

**¿Preguntas?** Consulta [PROJECT_MANAGEMENT.md](PROJECT_MANAGEMENT.md) o comenta en las tareas de Dart AI.
