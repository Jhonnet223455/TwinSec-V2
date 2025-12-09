"""
Modelo SQLAlchemy para logs de auditoría
"""
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey, Text, JSON
from sqlalchemy.orm import relationship
from datetime import datetime

from app.db.base import Base


class AuditLog(Base):
    """
    Registro de auditoría para trazabilidad completa del sistema.
    
    Cada acción importante en el sistema genera un log de auditoría:
    - Autenticación (login, logout, failed login)
    - Operaciones sobre modelos (create, update, delete)
    - Simulaciones (start, stop, pause)
    - Ataques ejecutados
    - Cambios de configuración
    
    Estos logs pueden exportarse a Wazuh u otros SIEM en formato CEF.
    
    Relaciones:
        - user: Usuario que realizó la acción (nullable para eventos del sistema)
    """
    __tablename__ = "audit_logs"
    
    # Primary Key
    id = Column(Integer, primary_key=True, index=True)
    
    # Tipo de evento
    event_type = Column(
        String(50), 
        nullable=False, 
        index=True
    )  # "login", "logout", "model_created", "simulation_started", "attack_executed", etc.
    
    # Severidad (compatible con syslog/CEF)
    severity = Column(
        String(20), 
        nullable=False, 
        default="info"
    )  # "debug", "info", "warning", "error", "critical"
    
    # Descripción del evento
    message = Column(Text, nullable=False)
    
    # Contexto adicional (JSON con detalles específicos del evento)
    details = Column(JSON, nullable=True)
    
    # Usuario relacionado (nullable para eventos del sistema)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    user = relationship("User")  # back_populates="audit_logs" cuando se habilite
    
    # Información de la petición HTTP
    ip_address = Column(String(45), nullable=True)  # IPv4 o IPv6
    user_agent = Column(String(500), nullable=True)
    endpoint = Column(String(255), nullable=True)  # Ruta del endpoint llamado
    method = Column(String(10), nullable=True)     # GET, POST, PUT, DELETE
    
    # IDs de recursos relacionados (para facilitar búsqueda)
    model_id = Column(Integer, nullable=True)
    simulation_run_id = Column(Integer, nullable=True)
    
    # Timestamp
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    def __repr__(self):
        return f"<AuditLog(id={self.id}, event_type='{self.event_type}', severity='{self.severity}', user_id={self.user_id})>"
    
    def to_cef(self) -> str:
        """
        Convierte el log al formato CEF (Common Event Format) para Wazuh.
        
        Formato CEF:
        CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
        
        Ejemplo:
        CEF:0|TwinSec|Studio|1.0.0|1|User Login|5|src=192.168.1.100 suser=jhon msg=User logged in successfully
        """
        extensions = []
        
        if self.ip_address:
            extensions.append(f"src={self.ip_address}")
        
        if self.user_id:
            extensions.append(f"suid={self.user_id}")
        
        if self.endpoint:
            extensions.append(f"request={self.endpoint}")
        
        if self.method:
            extensions.append(f"requestMethod={self.method}")
        
        extensions.append(f"msg={self.message}")
        
        # Mapeo de severidad a CEF (0-10)
        severity_map = {
            "debug": "2",
            "info": "5",
            "warning": "7",
            "error": "8",
            "critical": "10"
        }
        cef_severity = severity_map.get(self.severity, "5")
        
        cef_string = (
            f"CEF:0|TwinSec|Studio|1.0.0|{self.id}|{self.event_type}|{cef_severity}|"
            f"{' '.join(extensions)}"
        )
        
        return cef_string
