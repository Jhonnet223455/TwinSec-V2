"""
Modelos SQLAlchemy - ORM para PostgreSQL

Este módulo expone todos los modelos de base de datos para facilitar imports.

Uso:
    from app.models import User, Model, SimulationRun, AuditLog, Attack, IDSAlert, Threshold, LLMRequest, Base
"""
from app.database import Base
from app.models.user import User
from app.models.model import Model
from app.models.simulation import SimulationRun
from app.models.audit_log import AuditLog
from app.models.attack import Attack
from app.models.ids_alert import IDSAlert
from app.models.threshold import Threshold
from app.models.llm_request import LLMRequest

__all__ = [
    "Base",
    "User",
    "Model",
    "SimulationRun",
    "AuditLog",
    "Attack",
    "IDSAlert",
    "Threshold",
    "LLMRequest"
]
