"""
Pydantic schemas for audit logging and SIEM export.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class EventType(str, Enum):
    """Types of auditable events."""
    # Model events
    MODEL_GENERATED = "model_generated"
    MODEL_CREATED = "model_created"
    MODEL_UPDATED = "model_updated"
    MODEL_DELETED = "model_deleted"
    
    # Simulation events
    RUN_STARTED = "run_started"
    RUN_PAUSED = "run_paused"
    RUN_RESUMED = "run_resumed"
    RUN_STOPPED = "run_stopped"
    RUN_COMPLETED = "run_completed"
    RUN_FAILED = "run_failed"
    
    # Attack events
    ATTACK_ENABLED = "attack_enabled"
    ATTACK_DISABLED = "attack_disabled"
    
    # Parameter events
    PARAMETER_CHANGED = "parameter_changed"
    
    # Security events
    ANOMALY_DETECTED = "anomaly_detected"
    THRESHOLD_EXCEEDED = "threshold_exceeded"
    
    # Auth events
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTERED = "user_registered"
    AUTH_FAILED = "auth_failed"


class Severity(str, Enum):
    """Event severity levels."""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class AuditLogCreate(BaseModel):
    """Schema for creating audit log entries."""
    event_type: EventType
    severity: Severity = Severity.INFO
    user_id: Optional[str] = None
    run_id: Optional[str] = None
    component_id: Optional[str] = None
    details: Dict[str, Any] = Field(default_factory=dict)
    source_ip: Optional[str] = None


class AuditLogResponse(BaseModel):
    """Schema for audit log responses."""
    id: str
    timestamp: datetime
    event_type: EventType
    severity: Severity
    user_id: Optional[str]
    run_id: Optional[str]
    component_id: Optional[str]
    details: Dict[str, Any]
    source_ip: Optional[str]

    class Config:
        from_attributes = True


class LogExportFormat(str, Enum):
    """Export format for logs."""
    JSON = "json"
    CEF = "cef"  # Common Event Format for Wazuh/SIEM


class LogExportRequest(BaseModel):
    """Request to export logs."""
    run_id: Optional[str] = Field(default=None, description="Filter by simulation run")
    start_time: Optional[datetime] = Field(default=None, description="Start of time range")
    end_time: Optional[datetime] = Field(default=None, description="End of time range")
    event_types: Optional[List[EventType]] = Field(default=None, description="Filter by event types")
    severity: Optional[Severity] = Field(default=None, description="Minimum severity")
    format: LogExportFormat = Field(default=LogExportFormat.JSON, description="Export format")


class CEFLog(BaseModel):
    """
    Common Event Format (CEF) log entry for SIEM integration.
    Format: CEF:Version|Device Vendor|Device Product|Device Version|Signature ID|Name|Severity|Extension
    """
    version: str = "0"
    device_vendor: str = "TwinSec"
    device_product: str = "TwinSec Studio"
    device_version: str = "1.0"
    signature_id: str
    name: str
    severity: int = Field(..., ge=0, le=10)
    extension: Dict[str, Any]

    def to_cef_string(self) -> str:
        """Convert to CEF format string."""
        # Build extension string
        ext_parts = []
        for key, value in self.extension.items():
            ext_parts.append(f"{key}={value}")
        extension_str = " ".join(ext_parts)
        
        # Build CEF string
        cef_parts = [
            f"CEF:{self.version}",
            self.device_vendor,
            self.device_product,
            self.device_version,
            self.signature_id,
            self.name,
            str(self.severity),
            extension_str
        ]
        return "|".join(cef_parts)

    class Config:
        json_schema_extra = {
            "example": {
                "version": "0",
                "device_vendor": "TwinSec",
                "device_product": "TwinSec Studio",
                "device_version": "1.0",
                "signature_id": "ATTACK_001",
                "name": "FDI Attack Enabled",
                "severity": 7,
                "extension": {
                    "src": "192.168.1.100",
                    "suser": "user123",
                    "cs1Label": "RunID",
                    "cs1": "run_abc123",
                    "cs2Label": "Target",
                    "cs2": "T1.h",
                    "msg": "False Data Injection attack enabled on sensor T1.h"
                }
            }
        }
