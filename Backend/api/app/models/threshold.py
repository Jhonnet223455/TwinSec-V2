"""
Modelo SQLAlchemy para umbrales de alarma en señales
"""
from sqlalchemy import Column, String, Integer, ForeignKey, Float, Boolean, JSON
from sqlalchemy.orm import relationship
from datetime import datetime
from sqlalchemy import DateTime

from app.db.base import Base


class Threshold(Base):
    """
    Umbral de alarma para una señal específica de un modelo.
    
    Define límites (superiores, inferiores, o tasa de cambio) que cuando se
    exceden generan alarmas visuales en el HMI y pueden desencadenar acciones
    automáticas de seguridad.
    
    Relaciones:
        - model: Modelo al que pertenece el umbral
        - created_by_user: Usuario que definió el umbral
    """
    __tablename__ = "thresholds"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Relación con modelo
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    model = relationship("Model", back_populates="thresholds")
    
    # Señal objetivo
    signal_name = Column(String(100), nullable=False, index=True)
    # Formato: "component_id.signal_id" (ej. "T1.h", "V_in.q")
    
    component_id = Column(String(100), nullable=False)  # "T1", "V_in"
    signal_id = Column(String(100), nullable=False)     # "h", "q"
    
    # Tipo de umbral
    threshold_type = Column(
        String(30),
        nullable=False
    )  # 'upper' (límite superior), 'lower' (límite inferior), 'rate_of_change' (derivada)
    
    # Valor del umbral
    value = Column(Float, nullable=False)
    # Para 'upper' o 'lower': valor absoluto
    # Para 'rate_of_change': cambio máximo permitido por segundo
    
    # Configuración de histéresis (evita alarmas oscilantes)
    hysteresis = Column(Float, nullable=True, default=0.0)
    # Banda muerta: la señal debe volver a value ± hysteresis antes de desactivar alarma
    
    # Severidad de la alarma
    severity = Column(
        String(20),
        nullable=False,
        default="warning"
    )  # 'info', 'warning', 'critical'
    
    # Estado del umbral
    enabled = Column(Boolean, nullable=False, default=True)
    
    # Descripción y metadata
    description = Column(String(500), nullable=True)
    alarm_message = Column(String(200), nullable=True)  # Mensaje a mostrar en HMI
    
    # Color para visualización en HMI
    color = Column(String(7), nullable=True)  # Hex color (ej. "#FF0000" para rojo)
    
    # Acciones automatizadas (JSON)
    auto_actions = Column(JSON, nullable=True)
    # Ejemplo: {"stop_simulation": true, "send_notification": true, "log_event": true}
    
    # Usuario que creó el umbral
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by_user = relationship("User")
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<Threshold(id={self.id}, signal='{self.signal_name}', type='{self.threshold_type}', value={self.value})>"
    
    def check_violation(self, current_value: float, previous_value: float = None, dt: float = None) -> dict:
        """
        Verifica si un valor viola el umbral.
        
        Args:
            current_value: Valor actual de la señal
            previous_value: Valor anterior (requerido para rate_of_change)
            dt: Delta de tiempo (requerido para rate_of_change)
            
        Returns:
            dict con 'violated' (bool) y 'details' (dict)
        """
        if not self.enabled:
            return {"violated": False, "details": {"reason": "threshold_disabled"}}
        
        if self.threshold_type == "upper":
            violated = current_value > self.value
            return {
                "violated": violated,
                "details": {
                    "threshold": self.value,
                    "current_value": current_value,
                    "excess": current_value - self.value if violated else 0
                }
            }
        
        elif self.threshold_type == "lower":
            violated = current_value < self.value
            return {
                "violated": violated,
                "details": {
                    "threshold": self.value,
                    "current_value": current_value,
                    "deficit": self.value - current_value if violated else 0
                }
            }
        
        elif self.threshold_type == "rate_of_change":
            if previous_value is None or dt is None:
                return {"violated": False, "details": {"reason": "insufficient_data"}}
            
            rate = abs(current_value - previous_value) / dt
            violated = rate > self.value
            return {
                "violated": violated,
                "details": {
                    "threshold": self.value,
                    "current_rate": rate,
                    "excess_rate": rate - self.value if violated else 0
                }
            }
        
        return {"violated": False, "details": {"reason": "unknown_threshold_type"}}
    
    def to_dict(self):
        """Convierte el umbral a diccionario para serialización"""
        return {
            "id": self.id,
            "signal_name": self.signal_name,
            "component_id": self.component_id,
            "signal_id": self.signal_id,
            "threshold_type": self.threshold_type,
            "value": self.value,
            "hysteresis": self.hysteresis,
            "severity": self.severity,
            "enabled": self.enabled,
            "description": self.description,
            "alarm_message": self.alarm_message,
            "color": self.color,
            "auto_actions": self.auto_actions
        }
