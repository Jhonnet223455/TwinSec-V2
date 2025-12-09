"""
Modelo SQLAlchemy para usuarios
"""
from sqlalchemy import Column, String, Boolean, DateTime, Integer
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class User(Base):
    """
    Modelo de usuario para autenticación y autorización.
    
    Relaciones:
        - models: Lista de modelos de simulación creados por el usuario
        - simulation_runs: Lista de ejecuciones de simulación del usuario
        - audit_logs: Lista de logs de auditoría del usuario
    """
    __tablename__ = "users"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificación
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    full_name = Column(String(100))
    
    # Autenticación
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    
    # OAuth (para futura integración con Google, Facebook, LinkedIn)
    oauth_provider = Column(String(50), nullable=True)  # "google", "facebook", "linkedin"
    oauth_id = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relaciones
    models = relationship("Model", back_populates="owner", cascade="all, delete-orphan")
    simulation_runs = relationship("SimulationRun", back_populates="user", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="user")
    llm_requests = relationship("LLMRequest", back_populates="user")
    
    def __repr__(self):
        return f"<User(id={self.id}, username='{self.username}', email='{self.email}')>"
