"""
Database configuration and session management

Expone Base, engine, SessionLocal y get_db para uso en toda la aplicación.

Uso:
    from app.db import Base, engine, get_db
    from app.db.session import SessionLocal
"""
from app.db.base import Base
from app.db.session import engine, SessionLocal, get_db

__all__ = [
    "Base",
    "engine",
    "SessionLocal",
    "get_db"
]
