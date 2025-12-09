"""
API Router para gestión de ataques cibernéticos

Endpoints para inyectar, listar y gestionar ataques en simulaciones OT.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging

from app.database import get_db
from app.models import User, Attack, SimulationRun
from app.routers.models import get_current_user  # Mock auth temporal
from app.services.attack_service import get_attack_service, AttackType, AttackStatus

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/attacks",
    tags=["attacks"]
)


# ========================================
# SCHEMAS
# ========================================

class AttackCreateRequest(BaseModel):
    """Request para crear/inyectar un ataque."""
    run_id: int = Field(..., description="ID de la simulación donde inyectar el ataque")
    attack_type: AttackType = Field(..., description="Tipo de ataque (dos, false_data_injection, etc.)")
    target_signal: str = Field(..., description="Señal objetivo (ej: 'tank.level', 'valve.position')")
    start_time: float = Field(..., description="Tiempo de inicio del ataque (segundos desde t=0)", ge=0)
    duration: Optional[float] = Field(None, description="Duración del ataque en segundos (None = indefinido)", ge=0)
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parámetros específicos del ataque")
    description: Optional[str] = Field(None, description="Descripción del ataque")
    
    class Config:
        json_schema_extra = {
            "example": {
                "run_id": 1,
                "attack_type": "false_data_injection",
                "target_signal": "tank.level_sensor",
                "start_time": 50.0,
                "duration": 30.0,
                "parameters": {
                    "false_value": 8.5
                },
                "description": "Inyectar nivel falso de 8.5m en el sensor"
            }
        }


class AttackResponse(BaseModel):
    """Response de un ataque."""
    success: bool
    attack: Dict
    attack_id: int


class AttackListResponse(BaseModel):
    """Response para listado de ataques."""
    success: bool
    attacks: List[Dict]
    total: int


# ========================================
# ENDPOINTS
# ========================================

@router.post("/", response_model=AttackResponse)
async def create_attack(
    request: AttackCreateRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crea e inyecta un ataque en una simulación.
    
    **Tipos de ataques soportados:**
    
    1. **DoS (Denial of Service)**
       ```json
       {
         "attack_type": "dos",
         "target_signal": "valve.position",
         "parameters": {
           "blocked_value": 0.0  // Opcional, default 0
         }
       }
       ```
    
    2. **False Data Injection**
       ```json
       {
         "attack_type": "false_data_injection",
         "target_signal": "tank.level_sensor",
         "parameters": {
           "false_value": 8.5  // Valor falso a inyectar
         }
       }
       ```
    
    3. **Replay Attack**
       ```json
       {
         "attack_type": "replay_attack",
         "target_signal": "flow_sensor",
         "parameters": {
           "replay_buffer": [0.5, 0.6, 0.55, 0.52]  // Valores grabados
         }
       }
       ```
    
    4. **Ramp Attack**
       ```json
       {
         "attack_type": "ramp_attack",
         "target_signal": "setpoint",
         "parameters": {
           "rate": 0.1  // Incremento por segundo
         }
       }
       ```
    
    5. **Random Noise**
       ```json
       {
         "attack_type": "random_noise",
         "target_signal": "temperature_sensor",
         "parameters": {
           "noise_std": 2.0  // Desviación estándar del ruido
         }
       }
       ```
    """
    try:
        logger.info(f"Creando ataque '{request.attack_type}' en señal '{request.target_signal}'")
        
        # Verificar que la simulación existe y pertenece al usuario
        run = db.query(SimulationRun).filter(
            SimulationRun.id == request.run_id
        ).first()
        
        if not run:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Simulación {request.run_id} no encontrada"
            )
        
        # Verificar permisos (el modelo debe pertenecer al usuario)
        if run.model.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para atacar esta simulación"
            )
        
        # Validar parámetros del ataque
        # Combinar target_signal con parameters para la validación
        attack_params = {
            "target_signal": request.target_signal,
            **request.parameters
        }
        
        attack_service = get_attack_service()
        valid, error_msg = attack_service.validate_attack_params(
            request.attack_type,
            attack_params
        )
        
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Parámetros inválidos: {error_msg}"
            )
        
        # Crear registro de ataque en BD
        attack = Attack(
            simulation_run_id=request.run_id,
            attack_type=request.attack_type,
            target_component=request.target_signal,  # Usamos target_signal como target_component
            target_signal=request.target_signal,
            trigger_time=request.start_time,
            duration=request.duration,
            parameters=request.parameters,
            description=request.description,
            status="armed",  # Estado inicial según el modelo
            created_by=current_user.id
        )
        
        db.add(attack)
        db.commit()
        db.refresh(attack)
        
        # Registrar en el servicio de ataques (para ejecución en tiempo real)
        # Combinar target_signal con parameters
        attack_service.register_attack(
            attack_id=attack.attack_id,
            attack_type=request.attack_type,
            target_signal=request.target_signal,
            start_time=request.start_time,
            duration=request.duration,
            params=attack_params  # Usar los parámetros combinados
        )
        
        logger.info(f"✅ Ataque creado: {attack.attack_id} (ID BD: {attack.id})")
        
        return AttackResponse(
            success=True,
            attack={
                "id": attack.id,
                "attack_id": attack.attack_id,
                "attack_type": attack.attack_type,
                "target_signal": attack.target_signal,
                "target_component": attack.target_component,
                "start_time": attack.trigger_time,
                "duration": attack.duration,
                "parameters": attack.parameters,
                "status": attack.status,
                "severity": attack.severity,
                "created_at": attack.created_at.isoformat()
            },
            attack_id=attack.id
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Error al crear ataque: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al crear ataque: {str(e)}"
        )


@router.get("/", response_model=AttackListResponse)
async def list_attacks(
    run_id: Optional[int] = None,
    attack_type: Optional[AttackType] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Lista los ataques del usuario actual.
    
    **Filtros:**
    - `run_id`: Filtrar por simulación
    - `attack_type`: Filtrar por tipo de ataque
    - `skip`, `limit`: Paginación
    """
    # Construir query base
    query = db.query(Attack).join(SimulationRun).join(SimulationRun.model).filter(
        SimulationRun.model.has(owner_id=current_user.id)
    )
    
    if run_id is not None:
        query = query.filter(Attack.simulation_run_id == run_id)
    
    if attack_type is not None:
        query = query.filter(Attack.attack_type == attack_type)
    
    total = query.count()
    attacks = query.order_by(Attack.created_at.desc()).offset(skip).limit(limit).all()
    
    return AttackListResponse(
        success=True,
        attacks=[{
            "id": a.id,
            "attack_id": a.attack_id,
            "run_id": a.simulation_run_id,
            "attack_type": a.attack_type,
            "target_signal": a.target_signal,
            "start_time": a.trigger_time,
            "duration": a.duration,
            "status": a.status,
            "detected": False,  # Placeholder hasta implementar IDS
            "created_at": a.created_at.isoformat()
        } for a in attacks],
        total=total
    )


@router.get("/{attack_id}")
async def get_attack(
    attack_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene un ataque por ID.
    """
    attack = db.query(Attack).filter(Attack.id == attack_id).first()
    
    if not attack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ataque no encontrado"
        )
    
    # Verificar permisos
    if attack.simulation_run.model.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver este ataque"
        )
    
    return {
        "success": True,
        "attack": {
            "id": attack.id,
            "attack_id": attack.attack_id,
            "run_id": attack.simulation_run_id,
            "attack_type": attack.attack_type,
            "target_signal": attack.target_signal,
            "target_component": attack.target_component,
            "start_time": attack.trigger_time,
            "duration": attack.duration,
            "parameters": attack.parameters,
            "description": attack.description,
            "status": attack.status,
            "severity": attack.severity,
            "success": attack.success,
            "created_at": attack.created_at.isoformat(),
            "started_at": attack.started_at.isoformat() if attack.started_at else None,
            "ended_at": attack.ended_at.isoformat() if attack.ended_at else None
        }
    }


@router.delete("/{attack_id}")
async def delete_attack(
    attack_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Elimina un ataque (solo si está en estado pending).
    """
    attack = db.query(Attack).filter(Attack.id == attack_id).first()
    
    if not attack:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ataque no encontrado"
        )
    
    # Verificar permisos
    if attack.simulation_run.model.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para eliminar este ataque"
        )
    
    # Solo se pueden eliminar ataques armed (no activos)
    if attack.status not in ["armed", "stopped"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede eliminar un ataque en estado '{attack.status}'"
        )
    
    db.delete(attack)
    db.commit()
    
    logger.info(f"Ataque {attack_id} eliminado por usuario {current_user.id}")
    
    return {"success": True, "message": "Ataque eliminado"}


@router.get("/types/list")
async def list_attack_types():
    """
    Lista los tipos de ataques soportados con descripción y parámetros requeridos.
    """
    return {
        "success": True,
        "attack_types": [
            {
                "type": "dos",
                "name": "Denial of Service",
                "description": "Bloquea completamente una señal",
                "parameters": {
                    "blocked_value": {
                        "type": "float",
                        "required": False,
                        "default": 0.0,
                        "description": "Valor al que se bloquea la señal"
                    }
                }
            },
            {
                "type": "false_data_injection",
                "name": "False Data Injection",
                "description": "Inyecta un valor falso en un sensor/señal",
                "parameters": {
                    "false_value": {
                        "type": "float",
                        "required": True,
                        "description": "Valor falso a inyectar"
                    }
                }
            },
            {
                "type": "replay_attack",
                "name": "Replay Attack",
                "description": "Repite valores grabados previamente",
                "parameters": {
                    "replay_buffer": {
                        "type": "array<float>",
                        "required": True,
                        "description": "Lista de valores grabados a repetir"
                    }
                }
            },
            {
                "type": "ramp_attack",
                "name": "Ramp Attack",
                "description": "Incrementa/decrementa gradualmente el valor",
                "parameters": {
                    "rate": {
                        "type": "float",
                        "required": True,
                        "description": "Tasa de cambio por segundo (positivo o negativo)"
                    }
                }
            },
            {
                "type": "random_noise",
                "name": "Random Noise",
                "description": "Añade ruido aleatorio gaussiano",
                "parameters": {
                    "noise_std": {
                        "type": "float",
                        "required": True,
                        "description": "Desviación estándar del ruido"
                    }
                }
            }
        ]
    }
