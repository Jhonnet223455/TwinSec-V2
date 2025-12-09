"""Pydantic schemas for API request/response validation."""

# Model schemas
from .model import (
    TwinSecModelV1,
    SolverConfig,
    Component,
    Connection,
    Signals,
    HMIWidget,
    Alarm,
    HMIConfig,
    FDIAttack,
    DoSAttack,
    AttacksConfig,
    ModelMetadata,
)

# Simulation schemas
from .simulation import (
    SimulationStatus,
    SimulationCreate,
    SimulationResponse,
    SimulationState,
    CommandType,
    SimulationCommand,
    TelemetryMessage,
    EventMessage,
    ErrorMessage,
)

# Auth schemas
from .auth import (
    UserBase,
    UserCreate,
    UserLogin,
    UserResponse,
    Token,
    TokenData,
    PasswordChange,
    PasswordReset,
    PasswordResetConfirm,
)

# Logs schemas
from .logs import (
    EventType,
    Severity,
    AuditLogCreate,
    AuditLogResponse,
    LogExportFormat,
    LogExportRequest,
    CEFLog,
)

__all__ = [
    # Model
    "TwinSecModelV1",
    "SolverConfig",
    "Component",
    "Connection",
    "Signals",
    "HMIWidget",
    "Alarm",
    "HMIConfig",
    "FDIAttack",
    "DoSAttack",
    "AttacksConfig",
    "ModelMetadata",
    # Simulation
    "SimulationStatus",
    "SimulationCreate",
    "SimulationResponse",
    "SimulationState",
    "CommandType",
    "SimulationCommand",
    "TelemetryMessage",
    "EventMessage",
    "ErrorMessage",
    # Auth
    "UserBase",
    "UserCreate",
    "UserLogin",
    "UserResponse",
    "Token",
    "TokenData",
    "PasswordChange",
    "PasswordReset",
    "PasswordResetConfirm",
    # Logs
    "EventType",
    "Severity",
    "AuditLogCreate",
    "AuditLogResponse",
    "LogExportFormat",
    "LogExportRequest",
    "CEFLog",
]
