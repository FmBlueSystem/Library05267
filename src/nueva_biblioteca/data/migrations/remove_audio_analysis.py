#!/usr/bin/env python3
"""
Migración: Eliminar columnas de análisis de audio
===============================================

Elimina las columnas relacionadas con el análisis de audio
que ya no se utilizan.
"""

import logging
from pathlib import Path
from sqlalchemy import create_engine, text

logger = logging.getLogger(__name__)

def migrate(db_path: str | Path) -> None:
    """
    Ejecuta la migración.
    
    Args:
        db_path: Ruta al archivo de base de datos
    """
    try:
        # Conectar a la base de datos
        engine = create_engine(f'sqlite:///{db_path}')
        
        # Eliminar columnas
        with engine.connect() as conn:
            # Crear tabla temporal
            conn.execute(text("""
                CREATE TABLE tracks_new (
                    id INTEGER PRIMARY KEY,
                    file_path VARCHAR UNIQUE NOT NULL,
                    title VARCHAR,
                    artist VARCHAR,
                    album VARCHAR,
                    year INTEGER,
                    genre VARCHAR,
                    duration FLOAT,
                    format VARCHAR,
                    bitrate INTEGER,
                    sample_rate INTEGER,
                    channels INTEGER,
                    file_size INTEGER,
                    date_added DATETIME,
                    date_modified DATETIME,
                    last_played DATETIME,
                    play_count INTEGER DEFAULT 0
                )
            """))
            
            # Copiar datos
            conn.execute(text("""
                INSERT INTO tracks_new
                SELECT 
                    id,
                    file_path,
                    title,
                    artist,
                    album,
                    year,
                    genre,
                    duration,
                    format,
                    bitrate,
                    sample_rate,
                    channels,
                    file_size,
                    date_added,
                    date_modified,
                    last_played,
                    play_count
                FROM tracks
            """))
            
            # Eliminar tabla original
            conn.execute(text("DROP TABLE tracks"))
            
            # Renombrar tabla temporal
            conn.execute(text("ALTER TABLE tracks_new RENAME TO tracks"))
            
            # Commit cambios
            conn.commit()
            
        logger.info("Migración completada exitosamente")
        
    except Exception as e:
        logger.error(f"Error en la migración: {e}")
        raise

if __name__ == '__main__':
    import sys
    if len(sys.argv) != 2:
        print("Uso: python remove_audio_analysis.py <ruta_base_datos>")
        sys.exit(1)
    migrate(sys.argv[1]) 