"""
Modelo SQLAlchemy para modelos de simulación guardados
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class Model(Base):
    """
    Modelo de simulación generado por LLM y guardado en la base de datos.
    
    Cada modelo representa un sistema OT completo (planta de agua, microgrid, etc.)
    con sus componentes, conexiones, señales y configuración de simulación.
    
    Relaciones:
        - owner: Usuario que creó el modelo
        - simulation_runs: Lista de ejecuciones de este modelo
    """
    __tablename__ = "models"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificación
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Metadata del modelo
    model_type = Column(String(50), nullable=False)  # "tank", "microgrid", "drone", "hvac", "custom"
    version = Column(String(20), default="1.0.0")
    
    # Contenido del modelo (JSON completo según twinsec_model_v1.json)
    content = Column(JSON, nullable=False)
    
    # Generación vía LLM
    llm_prompt = Column(Text, nullable=True)  # Prompt original usado para generar el modelo
    llm_provider = Column(String(50), nullable=True)  # "openai", "anthropic", "azure_openai"
    llm_model = Column(String(50), nullable=True)  # "gpt-4", "claude-3-opus", etc.
    
    # Relación con usuario
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    owner = relationship("User", back_populates="models")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relaciones
    simulation_runs = relationship("SimulationRun", back_populates="model", cascade="all, delete-orphan")
    thresholds = relationship("Threshold", back_populates="model", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Model(id={self.id}, name='{self.name}', type='{self.model_type}', owner_id={self.owner_id})>"
