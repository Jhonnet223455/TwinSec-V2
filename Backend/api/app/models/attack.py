"""
Modelo SQLAlchemy para ataques ejecutados en simulaciones
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


def generate_uuid():
    """Genera un UUID como string"""
    return str(uuid.uuid4())


class Attack(Base):
    """
    Registro de ataques ejecutados durante una simulación.
    
    Cada ataque representa una manipulación maliciosa de señales o componentes
    del sistema durante la ejecución de una simulación. Permite análisis forense
    y correlación con detecciones del IDS.
    
    Relaciones:
        - simulation_run: Simulación en la que se ejecutó el ataque
        - created_by_user: Usuario que configuró/activó el ataque
    """
    __tablename__ = "attacks"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    attack_id = Column(String(36), unique=True, default=generate_uuid, nullable=False, index=True)
    
    # Relación con simulación
    simulation_run_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=False)
    simulation_run = relationship("SimulationRun", back_populates="attacks")
    
    # Tipo y objetivo del ataque
    attack_type = Column(
        String(50), 
        nullable=False,
        index=True
    )  # 'fdi' (False Data Injection), 'dos' (Denial of Service), 'mitm', 'replay', etc.
    
    target_component = Column(String(100), nullable=False)  # ID del componente afectado (ej. "V_in", "T1")
    target_signal = Column(String(100), nullable=True)  # Señal específica afectada (ej. "h", "q_in")
    
    # Estado del ataque
    status = Column(
        String(20),
        nullable=False,
        default="armed"
    )  # 'armed', 'active', 'stopped', 'completed', 'failed'
    
    # Parámetros del ataque (JSON con configuración específica)
    parameters = Column(JSON, nullable=False)
    # Ejemplo para FDI: {"bias": 0.5, "noise_amplitude": 0.1, "drift_rate": 0.01}
    # Ejemplo para DoS: {"packet_loss_rate": 0.8, "burst_duration": 5.0}
    
    # Ventana temporal del ataque
    trigger_time = Column(Float, nullable=False)  # Tiempo de simulación en que inicia (segundos)
    duration = Column(Float, nullable=True)  # Duración del ataque (segundos), null = indefinido
    
    # Tiempos reales de ejecución
    started_at = Column(DateTime, nullable=True)  # Cuando realmente comenzó
    ended_at = Column(DateTime, nullable=True)    # Cuando realmente terminó
    
    # Resultados y métricas
    success = Column(Boolean, nullable=True)  # Si el ataque se ejecutó correctamente
    error_message = Column(String(500), nullable=True)  # Si falló, el mensaje de error
    
    # Metadata adicional
    description = Column(String(500), nullable=True)  # Descripción del ataque
    severity = Column(String(20), default="medium")  # 'low', 'medium', 'high', 'critical'
    
    # Usuario que configuró el ataque
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_user = relationship("User")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Attack(id={self.id}, type='{self.attack_type}', target='{self.target_component}', status='{self.status}')>"
    
    def to_dict(self):
        """Convierte el ataque a diccionario para serialización"""
        return {
            "id": self.id,
            "attack_id": self.attack_id,
            "attack_type": self.attack_type,
            "target_component": self.target_component,
            "target_signal": self.target_signal,
            "status": self.status,
            "parameters": self.parameters,
            "trigger_time": self.trigger_time,
            "duration": self.duration,
            "severity": self.severity,
            "success": self.success,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
