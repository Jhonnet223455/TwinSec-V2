"""
API Router para gestión de simulaciones

Endpoints para iniciar, monitorear y obtener resultados de simulaciones OT.
"""

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from datetime import datetime
import logging
import asyncio
import json

from app.database import get_db
from app.models import User, Model, SimulationRun
from app.routers.models import get_current_user  # Mock auth temporal

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/simulations",
    tags=["simulations"]
)


# ========================================
# SCHEMAS
# ========================================

class SimulationStartRequest(BaseModel):
    """Request para iniciar una simulación."""
    model_id: int = Field(..., description="ID del modelo a simular")
    duration: float = Field(..., description="Duración de la simulación en segundos", gt=0)
    time_step: float = Field(0.1, description="Paso de tiempo (dt) en segundos", gt=0, le=1.0)
    initial_conditions: Dict[str, float] = Field(
        default_factory=dict,
        description="Condiciones iniciales {signal_name: value}"
    )
    controller_config: Optional[Dict[str, Any]] = Field(
        None,
        description="Configuración del controlador (PID, etc.)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "model_id": 1,
                "duration": 100.0,
                "time_step": 0.1,
                "initial_conditions": {
                    "tank.level": 5.0,
                    "inlet_valve.position": 0.5
                },
                "controller_config": {
                    "type": "pid",
                    "setpoint": 5.0,
                    "kp": 0.5,
                    "ki": 0.1,
                    "kd": 0.05
                }
            }
        }


class SimulationStatusResponse(BaseModel):
    """Response con estado de simulación."""
    success: bool
    run_id: int
    status: str  # "pending", "running", "paused", "completed", "failed"
    progress: float  # 0.0 - 1.0
    current_time: float  # Tiempo actual de simulación
    duration: float
    error_message: Optional[str] = None


# ========================================
# ENDPOINTS
# ========================================

@router.post("/start", response_model=SimulationStatusResponse)
async def start_simulation(
    request: SimulationStartRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Inicia una nueva simulación con el modelo especificado.
    
    Crea un SimulationRun y lo ejecuta en background.
    Durante la simulación, los ataques registrados serán inyectados automáticamente.
    """
    try:
        # Verificar que el modelo existe
        model = db.query(Model).filter(Model.id == request.model_id).first()
        
        if not model:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Modelo {request.model_id} no encontrado"
            )
        
        # Verificar permisos
        if model.owner_id != current_user.id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No tienes permisos para simular este modelo"
            )
        
        # Crear SimulationRun
        import uuid
        run = SimulationRun(
            run_id=str(uuid.uuid4()),
            name=f"Sim-{model.name}-{datetime.utcnow().strftime('%Y%m%d-%H%M%S')}",
            model_id=request.model_id,
            user_id=current_user.id,
            status="pending",
            duration=request.duration,
            time_step=request.time_step,
            start_time=datetime.utcnow(),
            progress=0.0
        )
        
        db.add(run)
        db.commit()
        db.refresh(run)
        
        logger.info(f"✅ SimulationRun creado: {run.id} (run_id: {run.run_id})")
        
        # TODO: Iniciar simulación en background con motor
        # Por ahora solo marcamos como "running" para testing
        run.status = "running"
        db.commit()
        
        return SimulationStatusResponse(
            success=True,
            run_id=run.id,
            status=run.status,
            progress=0.0,
            current_time=0.0,
            duration=request.duration
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error al iniciar simulación: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al iniciar simulación: {str(e)}"
        )


@router.get("/{run_id}", response_model=SimulationStatusResponse)
async def get_simulation_status(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene el estado actual de una simulación.
    """
    run = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulación no encontrada"
        )
    
    # Verificar permisos
    if run.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver esta simulación"
        )
    
    return SimulationStatusResponse(
        success=True,
        run_id=run.id,
        status=run.status,
        progress=run.progress or 0.0,
        current_time=0.0,  # TODO: Obtener del simulador
        duration=run.duration,
        error_message=run.error_message
    )


@router.post("/{run_id}/stop")
async def stop_simulation(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Detiene una simulación en ejecución.
    """
    run = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulación no encontrada"
        )
    
    if run.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para detener esta simulación"
        )
    
    if run.status not in ["pending", "running"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No se puede detener una simulación en estado '{run.status}'"
        )
    
    # TODO: Detener simulador
    run.status = "stopped"
    run.end_time = datetime.utcnow()
    db.commit()
    
    logger.info(f"Simulación {run_id} detenida por usuario {current_user.id}")
    
    return {"success": True, "message": "Simulación detenida"}


@router.get("/{run_id}/results")
async def get_simulation_results(
    run_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Obtiene los resultados de una simulación completada.
    
    Retorna series temporales de todas las señales, estados de ataques, etc.
    """
    run = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
    
    if not run:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Simulación no encontrada"
        )
    
    if run.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="No tienes permisos para ver los resultados"
        )
    
    # TODO: Obtener resultados reales del simulador
    # Por ahora retornamos estructura de ejemplo
    
    return {
        "success": True,
        "run_id": run.id,
        "status": run.status,
        "duration": run.duration,
        "time_step": run.time_step,
        "results": {
            "time": [],  # Array de tiempos
            "signals": {},  # {signal_name: [values]}
            "attacks": [],  # Ataques que se ejecutaron
            "alerts": []  # Alertas del IDS
        },
        "summary": run.results_summary or {}
    }


@router.websocket("/ws/{run_id}")
async def simulation_websocket(
    websocket: WebSocket,
    run_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket para streaming en tiempo real de telemetría de simulación.
    
    El cliente recibe actualizaciones cada step de simulación con:
    - Estado actual de todas las señales
    - Ataques activos
    - Alertas del IDS
    """
    await websocket.accept()
    logger.info(f"WebSocket conectado para simulación {run_id}")
    
    try:
        # TODO: Conectar con el simulador real
        # Por ahora enviamos datos de ejemplo
        
        t = 0.0
        while t < 10.0:  # Simulación de ejemplo de 10 segundos
            data = {
                "timestamp": t,
                "signals": {
                    "tank.level": 5.0 + (t * 0.1),
                    "inlet_valve.flow": 0.5
                },
                "attacks": [],
                "status": "running"
            }
            
            await websocket.send_json(data)
            await asyncio.sleep(0.1)  # 10 Hz
            t += 0.1
        
        await websocket.send_json({"status": "completed"})
        
    except WebSocketDisconnect:
        logger.info(f"WebSocket desconectado para simulación {run_id}")
    except Exception as e:
        logger.error(f"Error en WebSocket: {str(e)}")
        await websocket.close()
