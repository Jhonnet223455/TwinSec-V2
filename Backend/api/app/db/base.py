"""
Base de datos - Declarative Base y configuración base
"""
from sqlalchemy.ext.declarative import declarative_base

# Base para todos los modelos SQLAlchemy
Base = declarative_base()

# Metadata estará disponible en Base.metadata
# Esto se usa para crear/eliminar todas las tablas
