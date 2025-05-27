Entorno de Desarrollo
===================

Esta guía describe cómo configurar un entorno de desarrollo para Nueva Biblioteca.

Requisitos
---------

- Python 3.11 o superior
- uv (gestor de paquetes)
- git
- Qt 6.6 o superior
- Compiladores de C/C++ (para dependencias nativas)

Instalación
----------

1. Clonar repositorio::

    git clone https://github.com/FmBlueSystem/nueva-biblioteca.git
    cd nueva-biblioteca

2. Instalar uv::

    curl -LsSf https://astral.sh/uv/install.sh | sh

3. Crear entorno virtual::

    python -m venv .venv
    source .venv/bin/activate  # Linux/macOS
    .venv\Scripts\activate     # Windows

4. Instalar dependencias::

    uv pip install -e ".[dev]"

5. Instalar pre-commit hooks::

    pre-commit install

Configuración del Editor
---------------------

Visual Studio Code
~~~~~~~~~~~~~~~~

1. Instalar extensiones:

   - Python
   - Pylance
   - Python Type Checker
   - reStructuredText
   - Qt for Python
   - GitLens

2. Configuraciones recomendadas::

    {
        "python.analysis.typeCheckingMode": "strict",
        "python.linting.enabled": true,
        "python.linting.mypyEnabled": true,
        "python.formatting.provider": "ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.organizeImports": true
        }
    }

PyCharm
~~~~~~~

1. Abrir proyecto y configurar intérprete

2. Instalar plugins:
   
   - .ignore
   - Requirements
   - ReStructuredText
   - Qt UI Designer

3. Configurar:
   
   - Editor → Code Style → Python
   - Tools → Python Integrated Tools
   - Languages & Frameworks → Python Template Languages

Herramientas de Desarrollo
------------------------

Ruff
~~~~

Linting y formateo::

    # Verificar estilo
    ruff check .

    # Formatear código
    ruff format .

    # Configuración en pyproject.toml
    [tool.ruff]
    line-length = 88
    target-version = "py311"

MyPy
~~~~

Verificación de tipos::

    # Verificar tipos
    mypy src tests

    # Configuración en pyproject.toml
    [tool.mypy]
    python_version = "3.11"
    warn_return_any = true
    disallow_untyped_defs = true

Qt Designer
~~~~~~~~~~

Para editar archivos .ui::

    # Linux
    designer-qt6

    # Windows
    designer.exe

    # macOS
    open -a Designer

Base de Datos
-----------

SQLite::

    # CLI de SQLite
    sqlite3 library.db

    # GUI recomendada: DB Browser for SQLite
    # https://sqlitebrowser.org/

Debugging
--------

VSCode launch.json::

    {
        "version": "0.2.0",
        "configurations": [
            {
                "name": "Python: Nueva Biblioteca",
                "type": "python",
                "request": "launch",
                "program": "src/main.py",
                "console": "integratedTerminal",
                "justMyCode": false
            }
        ]
    }

PyTest Debug::

    pytest --pdb tests/
    pytest -s -v tests/  # Con output

Profiling
--------

cProfile::

    python -m cProfile -o profile.stats src/main.py
    python -m pstats profile.stats

Memory Profiler::

    pip install memory_profiler
    python -m memory_profiler src/main.py

Qt Debug
~~~~~~~

1. Habilitar debug de Qt::

    export QT_DEBUG_PLUGINS=1

2. Widget Inspector::

    from PyQt6.QtWidgets import QApplication
    app.window.show()
    QApplication.processEvents()

Logs
----

Configuración::

    # config.py
    LOGGING = {
        'version': 1,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'DEBUG',
            },
            'file': {
                'class': 'logging.FileHandler',
                'filename': 'nueva-biblioteca.log',
                'level': 'INFO',
            }
        },
        'root': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
        }
    }

Uso::

    import logging
    logger = logging.getLogger(__name__)
    logger.debug("Mensaje debug")
    logger.info("Mensaje info")

Documentación
-----------

Sphinx::

    # Generar documentación
    python scripts/generate_docs.py

    # Servir localmente
    python -m http.server --directory docs/_build/html/

Pre-commit
---------

Hooks configurados::

    # .pre-commit-config.yaml
    repos:
    - repo: https://github.com/astral-sh/ruff-pre-commit
      rev: v0.1.0
      hooks:
        - id: ruff
          args: [--fix]
        - id: ruff-format
    - repo: https://github.com/pre-commit/mirrors-mypy
      rev: v1.0.0
      hooks:
        - id: mypy
          additional_dependencies: [types-all]

Actualización::

    pre-commit autoupdate

Integración Continua
------------------

GitHub Actions::

    # Verificar workflow
    act -n

    # Ejecutar localmente
    act push

    # Ver :doc:`/development/ci_cd` para más detalles

Empaquetado
----------

PyInstaller::

    # Construir ejecutable
    python scripts/build.py --executable

    # Crear instalador
    python scripts/build.py --installer

Ver :doc:`/development/building` para más detalles.
