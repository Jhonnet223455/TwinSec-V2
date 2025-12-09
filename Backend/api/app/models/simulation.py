"""
Modelo SQLAlchemy para ejecuciones de simulación
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class SimulationRun(Base):
    """
    Registro de una ejecución de simulación.
    
    Cada vez que un usuario inicia una simulación, se crea un registro aquí
    con los parámetros de ejecución, estado actual y resultados.
    
    Relaciones:
        - user: Usuario que inició la simulación
        - model: Modelo de simulación usado
    """
    __tablename__ = "simulation_runs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Identificación
    run_id = Column(String(50), unique=True, index=True, nullable=False)  # UUID generado
    name = Column(String(100), nullable=True)
    
    # Estado de la simulación
    status = Column(
        String(20), 
        nullable=False, 
        default="pending"
    )  # "pending", "running", "paused", "completed", "failed", "stopped"
    
    # Parámetros de ejecución
    duration = Column(Float, nullable=False)  # Duración en segundos
    time_step = Column(Float, nullable=False)  # dt en segundos
    
    # Configuración de ataques (si aplica)
    attack_config = Column(JSON, nullable=True)
    
    # Resultados
    progress = Column(Float, default=0.0)  # Porcentaje de completado (0.0 - 1.0)
    error_message = Column(String(500), nullable=True)  # Si falló, el mensaje de error
    
    # Métricas de ejecución
    start_time = Column(DateTime, nullable=True)  # Cuándo empezó la simulación
    end_time = Column(DateTime, nullable=True)    # Cuándo terminó
    execution_time = Column(Float, nullable=True)  # Tiempo real de ejecución (segundos)
    
    # Resultados guardados (resumen)
    results_summary = Column(JSON, nullable=True)  # Estadísticas, alertas, etc.
    
    # Relaciones con usuario y modelo
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    user = relationship("User", back_populates="simulation_runs")
    
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    model = relationship("Model", back_populates="simulation_runs")
    
    # Relaciones con ataques y alertas IDS
    attacks = relationship("Attack", back_populates="simulation_run", cascade="all, delete-orphan")
    ids_alerts = relationship("IDSAlert", back_populates="simulation_run", cascade="all, delete-orphan")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<SimulationRun(id={self.id}, run_id='{self.run_id}', status='{self.status}', user_id={self.user_id})>"
