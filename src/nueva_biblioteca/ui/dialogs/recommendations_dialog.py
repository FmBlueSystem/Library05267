#!/usr/bin/env python3
"""
Diálogo de Recomendaciones - Nueva Biblioteca
=======================================

Diálogo para mostrar y gestionar recomendaciones musicales basadas
en similitud de audio y metadatos.
"""

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QDoubleSpinBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSlider,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
)

from nueva_biblioteca.core.recommender import get_recommender
from nueva_biblioteca.data.models import Track
from nueva_biblioteca.data.repository import Repository
from nueva_biblioteca.utils.logger import get_logger

logger = get_logger(__name__)

class RecommendationsDialog(QDialog):
    """Diálogo de recomendaciones musicales."""
    
    # Señales
    track_selected = pyqtSignal(Track)  # Track seleccionado
    
    def __init__(
        self,
        parent=None,
        repository: Repository = None,
        seed_tracks: list[Track] | None = None
    ):
        """
        Inicializa el diálogo.
        
        Args:
            parent: Widget padre
            repository: Repositorio de datos
            seed_tracks: Tracks base para recomendaciones
        """
        super().__init__(parent)
        
        self.repository = repository
        self.seed_tracks = seed_tracks or []
        self.recommender = get_recommender(repository)
        self.current_recommendations: list[Track] = []
        
        self._setup_ui()
        
        # Cargar recomendaciones iniciales
        if seed_tracks:
            self._update_recommendations()
    
    def _setup_ui(self) -> None:
        """Configura la interfaz de usuario."""
        self.setWindowTitle("Recomendaciones")
        self.setMinimumWidth(800)
        self.setMinimumHeight(600)
        
        layout = QVBoxLayout(self)
        
        # Info de tracks base
        if self.seed_tracks:
            seeds_group = QGroupBox("Basado en")
            seeds_layout = QVBoxLayout(seeds_group)
            
            for track in self.seed_tracks:
                seeds_layout.addWidget(QLabel(
                    f"{track.title} - {track.artist or 'Desconocido'}"
                ))
            
            layout.addWidget(seeds_group)
        
        # Filtros y opciones
        options_group = QGroupBox("Opciones")
        options_layout = QHBoxLayout(options_group)
        
        # Cantidad de resultados
        limit_layout = QVBoxLayout()
        limit_layout.addWidget(QLabel("Cantidad:"))
        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(1, 100)
        self.limit_spin.setValue(20)
        limit_layout.addWidget(self.limit_spin)
        
        # Score mínimo
        score_layout = QVBoxLayout()
        score_layout.addWidget(QLabel("Score mínimo:"))
        self.min_score_spin = QDoubleSpinBox()
        self.min_score_spin.setRange(0, 1)
        self.min_score_spin.setSingleStep(0.1)
        self.min_score_spin.setValue(0.5)
        score_layout.addWidget(self.min_score_spin)
        
        # Pesos de características
        weights_group = QGroupBox("Pesos")
        weights_layout = QVBoxLayout(weights_group)
        
        self.weight_sliders = {}
        
        for feature, default in self.recommender.DEFAULT_WEIGHTS.items():
            slider_layout = QHBoxLayout()
            
            # Label con porcentaje
            label = QLabel(f"{int(default * 100)}%")
            
            # Slider
            slider = QSlider(Qt.Orientation.Horizontal)
            slider.setRange(0, 100)
            slider.setValue(int(default * 100))
            slider.valueChanged.connect(lambda v, lbl=label: lbl.setText(f"{v}%"))
            
            self.weight_sliders[feature] = slider
            
            slider_layout.addWidget(QLabel(feature.title()))
            slider_layout.addWidget(slider)
            slider_layout.addWidget(label)
            
            weights_layout.addLayout(slider_layout)
        
        # Botón actualizar
        self.update_button = QPushButton("Actualizar")
        self.update_button.clicked.connect(self._update_recommendations)
        
        # Layout de opciones
        options_layout.addLayout(limit_layout)
        options_layout.addLayout(score_layout)
        options_layout.addWidget(weights_group)
        options_layout.addWidget(self.update_button)
        
        # Tabla de recomendaciones
        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels([
            "Título", "Artista", "Álbum", "Score", "Género"
        ])
        self.table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        self.table.doubleClicked.connect(self._on_track_selected)
        
        # Ajustar columnas
        header = self.table.horizontalHeader()
        header.setStretchLastSection(True)
        for i in range(4):
            header.setSectionResizeMode(
                i,
                header.ResizeMode.ResizeToContents
            )
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        
        # Botones
        button_layout = QHBoxLayout()
        
        close_button = QPushButton("Cerrar")
        close_button.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(close_button)
        
        # Layout principal
        layout.addWidget(options_group)
        layout.addWidget(self.table)
        layout.addWidget(self.progress_bar)
        layout.addLayout(button_layout)
    
    def _update_recommendations(self) -> None:
        """Actualiza las recomendaciones."""
        try:
            self.progress_bar.setRange(0, 0)
            self.progress_bar.show()
            self.update_button.setEnabled(False)
            
            # Obtener parámetros
            limit = self.limit_spin.value()
            min_score = self.min_score_spin.value()
            
            # Obtener pesos personalizados
            weights = {}
            for feature, slider in self.weight_sliders.items():
                weights[feature] = slider.value() / 100
            
            # Obtener recomendaciones
            if len(self.seed_tracks) == 1:
                # Similitud con un track
                recommendations = self.recommender.get_similar_tracks(
                    self.seed_tracks[0],
                    limit=limit,
                    min_score=min_score,
                    weights=weights
                )
                self.current_recommendations = [t for t, _ in recommendations]
                scores = [s for _, s in recommendations]
                
            else:
                # Recomendaciones basadas en múltiples tracks
                self.current_recommendations = self.recommender.get_recommendations(
                    self.seed_tracks,
                    limit=limit
                )
                scores = [1.0] * len(self.current_recommendations)
            
            # Actualizar tabla
            self.table.setRowCount(len(self.current_recommendations))
            
            for i, (track, score) in enumerate(zip(
                self.current_recommendations, scores, strict=False
            )):
                self.table.setItem(
                    i, 0,
                    QTableWidgetItem(track.title or "Sin título")
                )
                self.table.setItem(
                    i, 1,
                    QTableWidgetItem(track.artist or "Desconocido")
                )
                self.table.setItem(
                    i, 2,
                    QTableWidgetItem(track.album or "-")
                )
                self.table.setItem(
                    i, 3,
                    QTableWidgetItem(f"{score:.0%}")
                )
                self.table.setItem(
                    i, 4,
                    QTableWidgetItem(track.genre or "-")
                )
            
            self.table.resizeColumnsToContents()
            
        except Exception as e:
            logger.error(f"Error actualizando recomendaciones: {e}")
            QMessageBox.critical(
                self,
                "Error",
                "Error al generar recomendaciones"
            )
            
        finally:
            self.progress_bar.hide()
            self.update_button.setEnabled(True)
    
    def _on_track_selected(self) -> None:
        """Maneja la selección de un track."""
        row = self.table.currentRow()
        if 0 <= row < len(self.current_recommendations):
            track = self.current_recommendations[row]
            self.track_selected.emit(track)
            self.accept()
    
    def get_selected_track(self) -> Track | None:
        """
        Obtiene el track seleccionado.
        
        Returns:
            Track seleccionado o None
        """
        row = self.table.currentRow()
        if 0 <= row < len(self.current_recommendations):
            return self.current_recommendations[row]
        return None
