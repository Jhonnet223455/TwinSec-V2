"""
Script de inicialización de base de datos

Este script:
1. Crea todas las tablas en PostgreSQL
2. Crea un usuario administrador por defecto
3. Opcionalmente carga datos de ejemplo

Uso:
    python scripts/init_db.py
"""
import sys
import os
from pathlib import Path

# Agregar la carpeta api al path para poder importar app
api_path = str(Path(__file__).parent.parent / "api")
sys.path.insert(0, api_path)

# Cambiar al directorio api para que encuentre el .env
os.chdir(api_path)

from app.database import Base, engine, SessionLocal
from app.models import User, Model, SimulationRun, AuditLog, Attack, IDSAlert, Threshold, LLMRequest
from sqlalchemy.orm import Session
from passlib.context import CryptContext

from app.config import get_settings

settings = get_settings()

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hash a password."""
    return pwd_context.hash(password)


def create_tables():
    """
    Crea todas las tablas en la base de datos.
    """
    print("📦 Creando tablas en la base de datos...")
    Base.metadata.create_all(bind=engine)
    print("✅ Tablas creadas exitosamente")


def create_superuser(db: Session):
    """
    Crea un usuario administrador por defecto si no existe.
    """
    print("👤 Verificando usuario administrador...")
    
    # Verificar si ya existe un superuser
    existing_admin = db.query(User).filter(User.is_superuser == True).first()
    
    if existing_admin:
        print(f"ℹ️  Usuario administrador ya existe: {existing_admin.username}")
        return
    
    # Crear superuser
    admin_user = User(
        username="admin",
        email="admin@twinsec.local",
        full_name="Administrator",
        hashed_password=get_password_hash("Admin123!"),  # Cambiar en producción
        is_active=True,
        is_superuser=True
    )
    
    db.add(admin_user)
    db.commit()
    db.refresh(admin_user)
    
    print(f"✅ Usuario administrador creado: {admin_user.username}")
    print(f"   Email: {admin_user.email}")
    print(f"   Password: Admin123! (CAMBIAR EN PRODUCCIÓN)")


def create_sample_data(db: Session):
    """
    Opcionalmente crea datos de ejemplo para desarrollo.
    """
    print("\n📝 ¿Deseas crear datos de ejemplo? (y/n): ", end="")
    response = input().strip().lower()
    
    if response != 'y':
        print("⏭️  Saltando creación de datos de ejemplo")
        return
    
    print("📝 Creando datos de ejemplo...")
    
    # Usuario de prueba
    test_user = User(
        username="testuser",
        email="test@twinsec.local",
        full_name="Test User",
        hashed_password=get_password_hash("Test123!"),
        is_active=True,
        is_superuser=False
    )
    db.add(test_user)
    db.commit()
    db.refresh(test_user)
    
    # Modelo de ejemplo
    sample_model = Model(
        name="Water Tank System - Test",
        description="Sistema de tanque de agua de ejemplo para pruebas",
        model_type="tank",
        version="1.0.0",
        content={
            "name": "water-tank-test",
            "description": "Test water tank system",
            "type": "tank",
            "solver": {
                "method": "euler",
                "timestep": 0.1,
                "duration": 100.0
            },
            "components": [
                {
                    "id": "tank1",
                    "type": "tank",
                    "name": "Main Tank",
                    "params": {
                        "capacity": 1000.0,
                        "initial_level": 500.0,
                        "area": 10.0
                    }
                }
            ],
            "connections": [],
            "signals": [],
            "hmi": {"widgets": []},
            "attacks": []
        },
        llm_prompt="Create a simple water tank system for testing",
        llm_provider="manual",
        llm_model="human",
        owner_id=test_user.id
    )
    db.add(sample_model)
    db.commit()
    db.refresh(sample_model)
    
    # Log de auditoría de ejemplo
    audit_log = AuditLog(
        event_type="model_created",
        severity="info",
        message=f"Model '{sample_model.name}' created by {test_user.username}",
        details={
            "model_id": sample_model.id,
            "model_type": sample_model.model_type
        },
        user_id=test_user.id,
        model_id=sample_model.id
    )
    db.add(audit_log)
    db.commit()
    
    print(f"✅ Datos de ejemplo creados:")
    print(f"   - Usuario: {test_user.username} (password: Test123!)")
    print(f"   - Modelo: {sample_model.name}")
    print(f"   - Log de auditoría: {audit_log.event_type}")


def main():
    """
    Función principal de inicialización.
    """
    print("🚀 TwinSec Studio - Inicialización de Base de Datos")
    print("=" * 60)
    print(f"Database URL: {settings.DATABASE_URL}")
    print("=" * 60)
    
    try:
        # Crear tablas
        create_tables()
        
        # Crear sesión de base de datos
        db = SessionLocal()
        
        try:
            # Crear superuser
            create_superuser(db)
            
            # Crear datos de ejemplo (opcional)
            create_sample_data(db)
            
            print("\n" + "=" * 60)
            print("✅ Inicialización completada exitosamente")
            print("=" * 60)
            print("\n📚 Próximos pasos:")
            print("1. Asegúrate de que PostgreSQL esté corriendo")
            print("2. Actualiza el archivo .env con tus credenciales de base de datos")
            print("3. Ejecuta la API: python api/app/main.py")
            print("4. Visita http://localhost:8000/docs para ver la documentación")
            
        finally:
            db.close()
            
    except Exception as e:
        print(f"\n❌ Error durante la inicialización: {str(e)}")
        print("\nVerifica que:")
        print("1. PostgreSQL esté corriendo")
        print("2. Las credenciales en .env sean correctas")
        print("3. La base de datos exista (createdb twinsec_db)")
        sys.exit(1)


if __name__ == "__main__":
    main()
