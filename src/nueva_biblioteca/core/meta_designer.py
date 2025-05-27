#!/usr/bin/env python3
"""
Meta Designer 3 - Nueva Biblioteca
============================

Sistema avanzado de gestión y manipulación de metadatos musicales
con templates y transformaciones automáticas.
"""

import contextlib
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any

from nueva_biblioteca.utils.cache_manager import get_cache
from nueva_biblioteca.utils.logger import get_logger

from .metadata import MetadataManager

logger = get_logger(__name__)

@dataclass
class MetaTemplate:
    """Template para transformación de metadatos."""
    name: str
    pattern: str  # Patrón de regex
    fields: dict[str, str]  # Mapeo de grupos a campos
    transformers: dict[str, Callable]  # Funciones de transformación por campo
    enabled: bool = True

@dataclass
class MetaRule:
    """Regla de transformación de metadatos."""
    field: str
    condition: str
    value: Any
    action: str
    parameters: dict[str, Any]
    enabled: bool = True

class MetaDesigner:
    """
    Meta Designer 3 - Sistema avanzado de metadatos.
    
    Características:
    - Templates basados en expresiones regulares
    - Reglas de transformación configurables
    - Normalización automática
    - Validación de consistencia
    - Historial de cambios
    """
    
    def __init__(self):
        """Inicializa el Meta Designer."""
        self.metadata_manager = MetadataManager()
        self.cache = get_cache()
        
        # Cargar templates y reglas por defecto
        self.templates: dict[str, MetaTemplate] = self._load_default_templates()
        self.rules: dict[str, MetaRule] = self._load_default_rules()
        
        # Historial de cambios
        self.history: list[dict[str, Any]] = []
    
    def _load_default_templates(self) -> dict[str, MetaTemplate]:
        """Carga los templates predefinidos."""
        templates = {}
        
        # Template para "Artista - Título"
        templates["artist_title"] = MetaTemplate(
            name="Artista - Título",
            pattern=r"^(?P<artist>.+?)\s*-\s*(?P<title>.+?)$",
            fields={
                "artist": "artist",
                "title": "title"
            },
            transformers={
                "artist": str.strip,
                "title": str.strip
            }
        )
        
        # Template para "Artista - Álbum - ## - Título"
        templates["artist_album_track"] = MetaTemplate(
            name="Artista - Álbum - ## - Título",
            pattern=r"^(?P<artist>.+?)\s*-\s*(?P<album>.+?)\s*-\s*(?P<track>\d+)\s*-\s*(?P<title>.+?)$",
            fields={
                "artist": "artist",
                "album": "album",
                "track": "track_number",
                "title": "title"
            },
            transformers={
                "artist": str.strip,
                "album": str.strip,
                "track": int,
                "title": str.strip
            }
        )
        
        return templates
    
    def _load_default_rules(self) -> dict[str, MetaRule]:
        """Carga las reglas predefinidas."""
        rules = {}
        
        # Regla para normalizar artistas
        rules["normalize_artist"] = MetaRule(
            field="artist",
            condition="any",
            value=None,
            action="normalize",
            parameters={
                "capitalize": True,
                "remove_prefixes": ["The ", "Los ", "Las "],
                "remove_suffixes": [" Band", " Orchestra"]
            }
        )
        
        # Regla para normalizar títulos
        rules["normalize_title"] = MetaRule(
            field="title",
            condition="any",
            value=None,
            action="normalize",
            parameters={
                "capitalize": True,
                "remove_parentheses": True,
                "clean_spaces": True
            }
        )
        
        return rules
    
    def apply_template(
        self,
        filename: str,
        template_name: str
    ) -> dict[str, Any] | None:
        """
        Aplica un template a un nombre de archivo.
        
        Args:
            filename: Nombre del archivo
            template_name: Nombre del template
            
        Returns:
            Diccionario con metadatos extraídos o None
        """
        try:
            template = self.templates.get(template_name)
            if not template or not template.enabled:
                return None
            
            # Aplicar regex
            match = re.match(template.pattern, filename)
            if not match:
                return None
            
            # Extraer y transformar campos
            result = {}
            
            for group, field in template.fields.items():
                value = match.group(group)
                if value and group in template.transformers:
                    with contextlib.suppress(Exception):
                        value = template.transformers[group](value)
                result[field] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Error aplicando template {template_name}: {e}")
            return None
    
    def apply_rules(
        self,
        metadata: dict[str, Any],
        rule_names: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Aplica reglas de transformación a metadatos.
        
        Args:
            metadata: Metadatos originales
            rule_names: Lista de reglas a aplicar o None para todas
            
        Returns:
            Metadatos transformados
        """
        try:
            result = metadata.copy()
            
            # Filtrar reglas a aplicar
            rules_to_apply = []
            for name, rule in self.rules.items():
                if rule.enabled and (
                    not rule_names or name in rule_names
                ):
                    rules_to_apply.append(rule)
            
            # Aplicar cada regla
            for rule in rules_to_apply:
                if rule.field not in result:
                    continue
                
                value = result[rule.field]
                
                # Verificar condición
                if rule.condition == "any" or (
                    rule.condition == "equals" and value == rule.value
                ) or (
                    rule.condition == "contains" and 
                    isinstance(value, str) and
                    str(rule.value) in value
                ):
                    # Aplicar acción
                    if rule.action == "normalize":
                        value = self._normalize_value(
                            value,
                            **rule.parameters
                        )
                    
                    elif rule.action == "replace":
                        if isinstance(value, str):
                            value = value.replace(
                                rule.parameters.get("old", ""),
                                rule.parameters.get("new", "")
                            )
                    
                    elif rule.action == "format":
                        if isinstance(value, int | float):
                            value = rule.parameters.get("format", "{}").format(value)
                    
                    result[rule.field] = value
            
            return result
            
        except Exception as e:
            logger.error(f"Error aplicando reglas: {e}")
            return metadata
    
    def _normalize_value(
        self,
        value: Any,
        capitalize: bool = False,
        remove_prefixes: list[str] | None = None,
        remove_suffixes: list[str] | None = None,
        remove_parentheses: bool = False,
        clean_spaces: bool = False
    ) -> Any:
        """Normaliza un valor según parámetros."""
        if not isinstance(value, str):
            return value
        
        result = value
        
        # Limpiar espacios
        if clean_spaces:
            result = " ".join(result.split())
        
        # Remover prefijos
        if remove_prefixes:
            for prefix in remove_prefixes:
                if result.startswith(prefix):
                    result = result[len(prefix):]
                    break
        
        # Remover sufijos
        if remove_suffixes:
            for suffix in remove_suffixes:
                if result.endswith(suffix):
                    result = result[:-len(suffix)]
                    break
        
        # Remover paréntesis y contenido
        if remove_parentheses:
            result = re.sub(r"\([^)]*\)", "", result)
        
        # Capitalizar
        if capitalize:
            result = result.title()
        
        return result.strip()
    
    def add_template(self, template: MetaTemplate) -> bool:
        """
        Agrega un nuevo template.
        
        Args:
            template: Template a agregar
            
        Returns:
            True si se agregó correctamente
        """
        try:
            if not template.name:
                return False
            
            # Validar regex
            re.compile(template.pattern)
            
            # Validar campos y transformers
            for group in template.fields.values():
                if not isinstance(group, str):
                    return False
            
            for transformer in template.transformers.values():
                if not callable(transformer):
                    return False
            
            self.templates[template.name] = template
            return True
            
        except Exception as e:
            logger.error(f"Error agregando template: {e}")
            return False
    
    def add_rule(self, rule: MetaRule) -> bool:
        """
        Agrega una nueva regla.
        
        Args:
            rule: Regla a agregar
            
        Returns:
            True si se agregó correctamente
        """
        try:
            if not rule.field:
                return False
            
            # Validar condición
            if rule.condition not in ["any", "equals", "contains"]:
                return False
            
            # Validar acción
            if rule.action not in ["normalize", "replace", "format"]:
                return False
            
            # Generar ID único
            rule_id = f"{rule.field}_{rule.action}_{datetime.now(tz=UTC).timestamp()}"
            
            self.rules[rule_id] = rule
            return True
            
        except Exception as e:
            logger.error(f"Error agregando regla: {e}")
            return False
    
    def analyze_consistency(
        self,
        metadata_list: list[dict[str, Any]]
    ) -> dict[str, Any]:
        """
        Analiza la consistencia de metadatos.
        
        Args:
            metadata_list: Lista de metadatos a analizar
            
        Returns:
            Diccionario con estadísticas y problemas
        """
        try:
            stats = {
                "total": len(metadata_list),
                "fields": {},
                "problems": []
            }
            
            # Analizar cada campo
            all_fields = set()
            for metadata in metadata_list:
                all_fields.update(metadata.keys())
            
            for field in all_fields:
                field_stats = {
                    "present": 0,
                    "empty": 0,
                    "values": set()
                }
                
                for metadata in metadata_list:
                    value = metadata.get(field)
                    
                    if value is not None:
                        field_stats["present"] += 1
                        if str(value).strip():
                            field_stats["values"].add(str(value))
                        else:
                            field_stats["empty"] += 1
                
                stats["fields"][field] = {
                    "present": field_stats["present"],
                    "empty": field_stats["empty"],
                    "unique_values": len(field_stats["values"]),
                    "completeness": field_stats["present"] / len(metadata_list)
                }
                
                # Detectar problemas
                if field_stats["empty"] > 0:
                    stats["problems"].append({
                        "type": "empty_values",
                        "field": field,
                        "count": field_stats["empty"]
                    })
                
                if field_stats["present"] < len(metadata_list):
                    stats["problems"].append({
                        "type": "missing_field",
                        "field": field,
                        "count": len(metadata_list) - field_stats["present"]
                    })
            
            return stats
            
        except Exception as e:
            logger.error(f"Error analizando consistencia: {e}")
            return {
                "total": len(metadata_list),
                "fields": {},
                "problems": [{"type": "error", "message": str(e)}]
            }
    
    def save_history(
        self,
        original: dict[str, Any],
        modified: dict[str, Any],
        source: str
    ) -> None:
        """
        Guarda un cambio en el historial.
        
        Args:
            original: Metadatos originales
            modified: Metadatos modificados
            source: Fuente del cambio
        """
        try:
            self.history.append({
                "timestamp": datetime.now(tz=UTC).isoformat(),
                "source": source,
                "original": original.copy(),
                "modified": modified.copy(),
                "changes": {
                    k: modified[k]
                    for k in modified
                    if k not in original or original[k] != modified[k]
                }
            })
            
            # Limitar tamaño del historial
            if len(self.history) > 1000:
                self.history = self.history[-1000:]
                
        except Exception as e:
            logger.error(f"Error guardando historial: {e}")

# Instancia global
_meta_designer: MetaDesigner | None = None

def get_meta_designer() -> MetaDesigner:
    """Obtiene la instancia global del Meta Designer."""
    global _meta_designer
    if _meta_designer is None:
        _meta_designer = MetaDesigner()
    return _meta_designer
