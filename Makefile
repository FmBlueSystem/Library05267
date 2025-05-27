.PHONY: help install test lint format clean run docs

help:  ## Mostrar esta ayuda
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-20s\033[0m %s\n", $$1, $$2}'

install:  ## Instalar dependencias
	pip install -r requirements.txt
	pip install -e .

test:  ## Ejecutar tests
	pytest tests/ -v

test-cov:  ## Ejecutar tests con cobertura
	pytest tests/ --cov=nueva_biblioteca --cov-report=html

lint:  ## Verificar calidad de código
	ruff check src/
	mypy src/ --ignore-missing-imports

format:  ## Formatear código
	ruff format src/
	ruff check --fix src/

clean:  ## Limpiar archivos temporales
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	rm -rf build/ dist/ .coverage htmlcov/

run:  ## Ejecutar la aplicación
	python run.py

docs:  ## Generar documentación
	cd docs && make html

setup-dev:  ## Configurar entorno de desarrollo
	python -m venv .venv
	.venv/bin/pip install -r requirements.txt
	.venv/bin/pip install -e .
	.venv/bin/pre-commit install

check:  ## Verificación completa
	make lint
	make test

build:  ## Construir paquete
	python -m build

release:  ## Preparar release
	make clean
	make check
	make build 