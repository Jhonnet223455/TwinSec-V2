"""
Configuración de sesión de base de datos con connection pooling
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator

from app.config import get_settings

settings = get_settings()

# Motor de base de datos con pool de conexiones
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,  # Verifica que la conexión esté activa antes de usarla
    pool_size=10,        # Número de conexiones en el pool
    max_overflow=20,     # Conexiones adicionales si el pool se llena
    echo=settings.API_DEBUG  # Log de queries SQL en modo debug
)

# Factory de sesiones
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)


def get_db() -> Generator[Session, None, None]:
    """
    Dependency para obtener una sesión de base de datos en endpoints FastAPI.
    
    Uso:
        @app.get("/users")
        def get_users(db: Session = Depends(get_db)):
            users = db.query(User).all()
            return users
    
    La sesión se cierra automáticamente después de la petición.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
