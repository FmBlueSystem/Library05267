#!/usr/bin/env python3
"""
Diálogo de Playlist Inteligente - Nueva Biblioteca
=============================================

Diálogo para crear y editar reglas de playlists inteligentes
basadas en metadatos y criterios dinámicos.
"""

from dataclasses import dataclass
from typing import Any, ClassVar

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from nueva_biblioteca.data.models import Playlist
from nueva_biblioteca.data.repository import Repository
from nueva_biblioteca.utils.logger import get_logger

logger = get_logger(__name__)

@dataclass
class Rule:
    """Regla de filtrado para playlist inteligente."""
    field: str
    operator: str
    value: Any
    enabled: bool = True

class RuleWidget(QGroupBox):
    """Widget para editar una regla de filtrado."""
    
    # Señales
    rule_changed = pyqtSignal()
    delete_requested = pyqtSignal()
    
    # Campos disponibles
    FIELDS: ClassVar[list[tuple[str, str]]] = [
        ("title", "Título"),
        ("artist", "Artista"),
        ("album", "Álbum"),
        ("genre", "Género"),
        ("year", "Año"),
        ("duration", "Duración"),
        ("bpm", "BPM"),
        ("key", "Key"),
        ("play_count", "Reproducciones"),
        ("rating", "Rating"),
        ("date_added", "Fecha agregado"),
        ("date_modified", "Fecha modificado"),
        ("last_played", "Última reproducción")
    ]
    
    # Operadores por tipo
    OPERATORS: ClassVar[dict[str, list[tuple[str, str]]]] = {
        "text": [
            ("contains", "contiene"),
            ("not_contains", "no contiene"),
            ("equals", "es igual a"),
            ("not_equals", "es diferente a"),
            ("starts_with", "comienza con"),
            ("ends_with", "termina con")
        ],
        "number": [
            ("equals", "es igual a"),
            ("not_equals", "es diferente a"),
            ("greater", "mayor que"),
            ("greater_equal", "mayor o igual que"),
            ("less", "menor que"),
            ("less_equal", "menor o igual que"),
            ("between", "entre")
        ],
        "date": [
            ("after", "después de"),
            ("before", "antes de"),
            ("between", "entre"),
            ("last_days", "últimos N días"),
            ("this_week", "esta semana"),
            ("this_month", "este mes"),
            ("this_year", "este año")
        ]
    }
    
    # Tipo de campo
    FIELD_TYPES: ClassVar[dict[str, str]] = {
        "title": "text",
        "artist": "text",
        "album": "text",
        "genre": "text",
        "year": "number",
        "duration": "number",
        "bpm": "number",
        "key": "text",
        "play_count": "number",
        "rating": "number",
        "date_added": "date",
        "date_modified": "date",
        "last_played": "date"
    }
    
    def __init__(self, rule: Rule | None = None):
        """
        Inicializa el widget de regla.
        
        Args:
            rule: Regla existente o None para nueva
        """
        super().__init__("Regla")
        
        self.rule = rule or Rule("title", "contains", "", True)
        self._setup_ui()
        
        if rule:
            self._load_rule(rule)
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        layout = QHBoxLayout(self)
        
        # Checkbox para habilitar/deshabilitar
        self.enabled_check = QCheckBox()
        self.enabled_check.setChecked(self.rule.enabled)
        self.enabled_check.stateChanged.connect(self._on_change)
        
        # Campo
        self.field_combo = QComboBox()
        for field_id, field_name in self.FIELDS:
            self.field_combo.addItem(field_name, field_id)
        self.field_combo.currentIndexChanged.connect(self._update_operators)
        self.field_combo.currentIndexChanged.connect(self._on_change)
        
        # Operador
        self.operator_combo = QComboBox()
        self._update_operators()
        self.operator_combo.currentIndexChanged.connect(self._on_change)
        
        # Valor
        self.value_container = QWidget()
        self.value_layout = QHBoxLayout(self.value_container)
        self.value_layout.setContentsMargins(0, 0, 0, 0)
        self._update_value_widget()
        
        # Botón eliminar
        self.delete_button = QPushButton("x")
        self.delete_button.setFixedWidth(30)
        self.delete_button.clicked.connect(self.delete_requested.emit)
        
        # Layout
        layout.addWidget(self.enabled_check)
        layout.addWidget(self.field_combo, 2)
        layout.addWidget(self.operator_combo, 2)
        layout.addWidget(self.value_container, 3)
        layout.addWidget(self.delete_button)
    
    def _update_operators(self) -> None:
        """Actualiza los operadores según el tipo de campo."""
        field = self.field_combo.currentData()
        field_type = self.FIELD_TYPES[field]
        
        self.operator_combo.clear()
        for op_id, op_name in self.OPERATORS[field_type]:
            self.operator_combo.addItem(op_name, op_id)
    
    def _update_value_widget(self) -> None:
        """Actualiza el widget de valor según el campo y operador."""
        # Limpiar widgets anteriores
        while self.value_layout.count():
            item = self.value_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        field = self.field_combo.currentData()
        field_type = self.FIELD_TYPES[field]
        operator = self.operator_combo.currentData()
        
        if field_type == "text":
            self.value_widget = QLineEdit()
            self.value_widget.textChanged.connect(self._on_change)
            self.value_layout.addWidget(self.value_widget)
            
        elif field_type == "number":
            if operator == "between":
                self.value_widget = [QSpinBox(), QSpinBox()]
                self.value_layout.addWidget(self.value_widget[0])
                self.value_layout.addWidget(QLabel("y"))
                self.value_layout.addWidget(self.value_widget[1])
                for spin in self.value_widget:
                    spin.setRange(0, 99999)
                    spin.valueChanged.connect(self._on_change)
            else:
                self.value_widget = QSpinBox()
                self.value_widget.setRange(0, 99999)
                self.value_widget.valueChanged.connect(self._on_change)
                self.value_layout.addWidget(self.value_widget)
                
        elif field_type == "date":
            if operator in ["between", "last_days"]:
                self.value_widget = QSpinBox()
                self.value_widget.setRange(1, 9999)
                self.value_widget.valueChanged.connect(self._on_change)
                self.value_layout.addWidget(self.value_widget)
                if operator == "last_days":
                    self.value_layout.addWidget(QLabel("días"))
            else:
                self.value_widget = None  # Usar fecha actual
    
    def _load_rule(self, rule: Rule) -> None:
        """Carga una regla existente."""
        # Seleccionar campo
        index = self.field_combo.findData(rule.field)
        if index >= 0:
            self.field_combo.setCurrentIndex(index)
        
        # Seleccionar operador
        self._update_operators()
        index = self.operator_combo.findData(rule.operator)
        if index >= 0:
            self.operator_combo.setCurrentIndex(index)
        
        # Establecer valor
        self._update_value_widget()
        if isinstance(self.value_widget, QLineEdit):
            self.value_widget.setText(str(rule.value))
        elif isinstance(self.value_widget, QSpinBox):
            self.value_widget.setValue(int(rule.value))
        elif isinstance(self.value_widget, list):
            if isinstance(rule.value, list | tuple) and len(rule.value) == 2:
                self.value_widget[0].setValue(int(rule.value[0]))
                self.value_widget[1].setValue(int(rule.value[1]))
    
    def _on_change(self) -> None:
        """Maneja cambios en los controles."""
        self._update_value_widget()
        self.rule_changed.emit()
    
    def get_rule(self) -> Rule:
        """
        Obtiene la regla actual.
        
        Returns:
            Regla configurada
        """
        field = self.field_combo.currentData()
        operator = self.operator_combo.currentData()
        
        # Obtener valor según tipo de widget
        if isinstance(self.value_widget, QLineEdit):
            value = self.value_widget.text()
        elif isinstance(self.value_widget, QSpinBox):
            value = self.value_widget.value()
        elif isinstance(self.value_widget, list):
            value = [w.value() for w in self.value_widget]
        else:
            value = None
        
        return Rule(
            field=field,
            operator=operator,
            value=value,
            enabled=self.enabled_check.isChecked()
        )

class SmartPlaylistDialog(QDialog):
    """Diálogo para configurar playlist inteligente."""
    
    def __init__(
        self,
        parent=None,
        repository: Repository = None,
        playlist: Playlist | None = None
    ):
        """
        Inicializa el diálogo.
        
        Args:
            parent: Widget padre
            repository: Repositorio de datos
            playlist: Playlist existente o None para nueva
        """
        super().__init__(parent)
        
        self.repository = repository
        self.playlist = playlist
        self._setup_ui()
        
        if playlist:
            self._load_playlist()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        self.setWindowTitle("Playlist Inteligente")
        self.setMinimumWidth(600)
        
        layout = QVBoxLayout(self)
        
        # Nombre y descripción
        form = QFormLayout()
        
        self.name_edit = QLineEdit()
        if self.playlist:
            self.name_edit.setText(self.playlist.name)
        form.addRow("Nombre:", self.name_edit)
        
        self.description_edit = QLineEdit()
        if self.playlist:
            self.description_edit.setText(self.playlist.description)
        form.addRow("Descripción:", self.description_edit)
        
        # Scroll area para reglas
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        self.rules_container = QWidget()
        self.rules_layout = QVBoxLayout(self.rules_container)
        scroll.setWidget(self.rules_container)
        
        # Botón agregar regla
        add_button = QPushButton("Agregar Regla")
        add_button.clicked.connect(self._add_rule)
        
        # Opciones
        options_group = QGroupBox("Opciones")
        options_layout = QVBoxLayout(options_group)
        
        self.match_all = QCheckBox("Cumplir todas las reglas")
        self.match_all.setChecked(True)
        
        self.limit_results = QCheckBox("Limitar resultados")
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 9999)
        self.limit_spin.setValue(100)
        self.limit_spin.setEnabled(False)
        
        limit_layout = QHBoxLayout()
        limit_layout.addWidget(self.limit_results)
        limit_layout.addWidget(self.limit_spin)
        limit_layout.addStretch()
        
        self.limit_results.stateChanged.connect(
            lambda state: self.limit_spin.setEnabled(
                state == Qt.CheckState.Checked.value
            )
        )
        
        options_layout.addWidget(self.match_all)
        options_layout.addLayout(limit_layout)
        
        # Vista previa
        preview_group = QGroupBox("Vista Previa")
        preview_layout = QVBoxLayout(preview_group)
        
        self.matches_label = QLabel("0 tracks coinciden")
        self.update_preview_button = QPushButton("Actualizar Vista Previa")
        self.update_preview_button.clicked.connect(self._update_preview)
        
        preview_layout.addWidget(self.matches_label)
        preview_layout.addWidget(self.update_preview_button)
        
        # Botones
        button_layout = QHBoxLayout()
        
        self.save_button = QPushButton("Guardar")
        self.save_button.clicked.connect(self.accept)
        
        cancel_button = QPushButton("Cancelar")
        cancel_button.clicked.connect(self.reject)
        
        button_layout.addWidget(self.save_button)
        button_layout.addWidget(cancel_button)
        
        # Layout principal
        layout.addLayout(form)
        layout.addWidget(scroll)
        layout.addWidget(add_button)
        layout.addWidget(options_group)
        layout.addWidget(preview_group)
        layout.addLayout(button_layout)
        
        # Agregar regla inicial
        self._add_rule()
    
    def _add_rule(self) -> None:
        """Agrega una nueva regla."""
        rule_widget = RuleWidget()
        rule_widget.rule_changed.connect(self._update_preview)
        rule_widget.delete_requested.connect(lambda: self._delete_rule(rule_widget))
        self.rules_layout.addWidget(rule_widget)
    
    def _delete_rule(self, widget: RuleWidget) -> None:
        """Elimina una regla."""
        if self.rules_layout.count() > 1:
            widget.deleteLater()
            self._update_preview()
    
    def _load_playlist(self) -> None:
        """Carga una playlist existente."""
        # TODO: Implementar carga de reglas
    
    def _update_preview(self) -> None:
        """Actualiza la vista previa de coincidencias."""
        try:
            # Obtener reglas activas
            rules = []
            for i in range(self.rules_layout.count()):
                widget = self.rules_layout.itemAt(i).widget()
                if isinstance(widget, RuleWidget):
                    rule = widget.get_rule()
                    if rule.enabled:
                        rules.append(rule)
            
            if not rules:
                self.matches_label.setText("0 tracks coinciden")
                return
            
            # Construir consulta
            filters = []
            for rule in rules:
                if rule.field == "title":
                    if rule.operator == "contains":
                        filters.append(("title", "LIKE", f"%{rule.value}%"))
                    elif rule.operator == "equals":
                        filters.append(("title", "=", rule.value))
                # TODO: Implementar más filtros
            
            # Ejecutar consulta
            matches = self.repository.count_tracks(
                filters=filters,
                match_all=self.match_all.isChecked()
            )
            
            self.matches_label.setText(f"{matches} tracks coinciden")
            
        except Exception as e:
            logger.error(f"Error actualizando vista previa: {e}")
            self.matches_label.setText("Error al actualizar vista previa")
    
    def accept(self) -> None:
        """Guarda la playlist y cierra el diálogo."""
        name = self.name_edit.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "Debe ingresar un nombre")
            return
        
        # TODO: Implementar guardado de playlist inteligente
        super().accept()
