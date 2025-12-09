"""
Modelo SQLAlchemy para alertas del sistema de detección de intrusiones (IDS)
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Float, Boolean, JSON, Text
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

from app.db.base import Base


def generate_uuid():
    """Genera un UUID como string"""
    return str(uuid.uuid4())


class IDSAlert(Base):
    """
    Alerta generada por el sistema de detección de intrusiones (IDS).
    
    El IDS utiliza un Autoencoder para detectar anomalías en los datos de 
    telemetría y SHAP para explicar qué señales contribuyeron a la anomalía.
    Cada alerta representa una posible intrusión o comportamiento anómalo.
    
    Relaciones:
        - simulation_run: Simulación donde se detectó la anomalía
        - related_attack: Ataque real que causó la alerta (si se conoce)
    """
    __tablename__ = "ids_alerts"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String(36), unique=True, default=generate_uuid, nullable=False, index=True)
    
    # Relación con simulación
    simulation_run_id = Column(Integer, ForeignKey("simulation_runs.id"), nullable=False)
    simulation_run = relationship("SimulationRun", back_populates="ids_alerts")
    
    # Tiempo de la detección
    timestamp = Column(DateTime, nullable=False, index=True)
    simulation_time = Column(Float, nullable=False)  # Tiempo de simulación (segundos)
    
    # Severidad de la alerta
    severity = Column(
        String(20),
        nullable=False,
        index=True
    )  # 'low', 'medium', 'high', 'critical'
    
    # Score de anomalía del Autoencoder
    anomaly_score = Column(Float, nullable=False)  # 0.0 - 1.0 (mayor = más anómalo)
    threshold_used = Column(Float, nullable=False)  # Umbral que se superó
    
    # Clasificación del tipo de ataque (si el modelo pudo identificarlo)
    detected_attack_type = Column(String(50), nullable=True)  # 'fdi', 'dos', 'unknown'
    confidence = Column(Float, nullable=True)  # Confianza en la clasificación (0.0 - 1.0)
    
    # Señales afectadas
    affected_signals = Column(JSON, nullable=False)
    # Ejemplo: ["T1.h", "V_in.q", "L_sens.value"]
    
    # Explicación SHAP (feature importance)
    shap_explanation = Column(JSON, nullable=True)
    # Ejemplo: {"T1.h": 0.85, "V_in.q": 0.65, "T2.h": 0.23}
    
    # Detalles adicionales de la anomalía
    anomaly_details = Column(JSON, nullable=True)
    # Ejemplo: {"reconstruction_error": 0.245, "affected_components": ["T1", "V_in"]}
    
    # Ground truth (para entrenamiento y evaluación)
    related_attack_id = Column(Integer, ForeignKey("attacks.id"), nullable=True)
    related_attack = relationship("Attack")
    
    false_positive = Column(Boolean, nullable=True)  # Si se confirmó que fue falso positivo
    true_positive = Column(Boolean, nullable=True)   # Si se confirmó que fue verdadero positivo
    
    # Estado de la alerta
    status = Column(
        String(20),
        nullable=False,
        default="new"
    )  # 'new', 'investigating', 'confirmed', 'false_alarm', 'resolved'
    
    # Respuesta y resolución
    investigated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    investigated_by_user = relationship("User", foreign_keys=[investigated_by])
    
    investigation_notes = Column(Text, nullable=True)
    resolved_at = Column(DateTime, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<IDSAlert(id={self.id}, severity='{self.severity}', score={self.anomaly_score:.3f}, status='{self.status}')>"
    
    def to_dict(self):
        """Convierte la alerta a diccionario para serialización"""
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "severity": self.severity,
            "anomaly_score": self.anomaly_score,
            "detected_attack_type": self.detected_attack_type,
            "confidence": self.confidence,
            "affected_signals": self.affected_signals,
            "status": self.status,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
            "simulation_time": self.simulation_time,
            "false_positive": self.false_positive,
            "true_positive": self.true_positive
        }
    
    def calculate_metrics(self) -> dict:
        """
        Calcula métricas de efectividad del IDS.
        Útil para evaluar el modelo Autoencoder.
        """
        is_tp = self.true_positive is True
        is_fp = self.false_positive is True
        is_fn = self.true_positive is False and self.related_attack_id is not None
        
        return {
            "is_true_positive": is_tp,
            "is_false_positive": is_fp,
            "is_false_negative": is_fn,
            "precision_contribution": 1 if is_tp else (0 if is_fp else None),
            "recall_contribution": 1 if is_tp else (0 if is_fn else None)
        }
