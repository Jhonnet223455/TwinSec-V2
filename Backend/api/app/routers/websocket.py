"""
WebSocket Router - Telemetría en tiempo real

Endpoints:
    - ws/runs/{run_id}/telemetry: Telemetría de simulación en tiempo real
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
import asyncio
import logging
import json
import sys
from pathlib import Path
from typing import Dict, Any

# Agregar el directorio Backend al path para importar engine
# Path actual: Backend/api/app/routers/websocket.py
# Subir 3 niveles para llegar a Backend/
backend_path = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(backend_path))

from ..database import get_db
from ..models import SimulationRun

try:
    from engine.core.simulator import Simulator
except ImportError:
    # Si no se puede importar, crear una clase stub para no romper el servidor
    class Simulator:
        def __init__(self, *args, **kwargs):
            pass

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/ws", tags=["websocket"])


class ConnectionManager:
    """
    Gestor de conexiones WebSocket.
    
    Mantiene un registro de conexiones activas y permite broadcast.
    """
    
    def __init__(self):
        self.active_connections: Dict[int, list[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, run_id: int):
        """Acepta una nueva conexión."""
        await websocket.accept()
        
        if run_id not in self.active_connections:
            self.active_connections[run_id] = []
        
        self.active_connections[run_id].append(websocket)
        logger.info(f"WebSocket conectado: run_id={run_id}, total={len(self.active_connections[run_id])}")
    
    def disconnect(self, websocket: WebSocket, run_id: int):
        """Remueve una conexión."""
        if run_id in self.active_connections:
            self.active_connections[run_id].remove(websocket)
            
            if len(self.active_connections[run_id]) == 0:
                del self.active_connections[run_id]
        
        logger.info(f"WebSocket desconectado: run_id={run_id}")
    
    async def send_to_run(self, run_id: int, data: dict):
        """Envía datos a todos los clientes conectados a un run."""
        if run_id not in self.active_connections:
            return
        
        dead_connections = []
        
        for websocket in self.active_connections[run_id]:
            try:
                await websocket.send_json(data)
            except Exception as e:
                logger.error(f"Error enviando a WebSocket: {str(e)}")
                dead_connections.append(websocket)
        
        # Limpiar conexiones muertas
        for ws in dead_connections:
            self.disconnect(ws, run_id)


manager = ConnectionManager()


@router.websocket("/runs/{run_id}/telemetry")
async def telemetry_websocket(
    websocket: WebSocket,
    run_id: int,
    db: Session = Depends(get_db)
):
    """
    WebSocket para telemetría en tiempo real.
    
    El frontend se conecta a:
        ws://localhost:8001/ws/runs/{run_id}/telemetry
    
    Recibe:
        {
            "timestamp": 12.5,
            "real_state": {
                "tank.level_sensor": 7.3,
                "tank.valve_in_position": 0.6,
                "tank.valve_out_position": 0.4
            },
            "observed_state": {
                "tank.level_sensor": 8.5,  // ⚠️ Atacado por false_data_injection
                "tank.valve_in_position": 0.6,
                "tank.valve_out_position": 0.4
            },
            "control_actions": {
                "valve_in_target": 0.65
            },
            "attacks": [
                {
                    "attack_id": 2,
                    "attack_type": "false_data_injection",
                    "target_signal": "tank.level_sensor",
                    "status": "active",
                    "parameters": {
                        "false_value": 8.5
                    }
                }
            ]
        }
    
    Permite enviar comandos:
        {
            "command": "pause"
        }
        {
            "command": "resume"
        }
        {
            "command": "stop"
        }
    """
    # Verificar que existe el run
    run = db.query(SimulationRun).filter(SimulationRun.id == run_id).first()
    if not run:
        await websocket.close(code=4004, reason="Run not found")
        return
    
    # Conectar WebSocket
    await manager.connect(websocket, run_id)
    
    try:
        # Si la simulación ya está corriendo, solo escuchar comandos
        # Si no, podríamos iniciarla aquí
        
        while True:
            # Recibir comandos del cliente
            data = await websocket.receive_json()
            
            command = data.get("command")
            
            if command == "pause":
                # TODO: Pausar simulación
                logger.info(f"Pausa solicitada para run_id={run_id}")
            
            elif command == "resume":
                # TODO: Reanudar simulación
                logger.info(f"Reanudación solicitada para run_id={run_id}")
            
            elif command == "stop":
                # TODO: Detener simulación
                logger.info(f"Detención solicitada para run_id={run_id}")
                break
            
            else:
                logger.warning(f"Comando desconocido: {command}")
    
    except WebSocketDisconnect:
        manager.disconnect(websocket, run_id)
        logger.info(f"Cliente desconectado de run_id={run_id}")
    
    except Exception as e:
        logger.error(f"Error en WebSocket: {str(e)}", exc_info=True)
        manager.disconnect(websocket, run_id)


async def broadcast_telemetry(run_id: int, telemetry: dict):
    """
    Función auxiliar para enviar telemetría desde el Simulator.
    
    El Simulator la invoca en cada step():
        await broadcast_telemetry(self.run_id, telemetry_data)
    """
    await manager.send_to_run(run_id, telemetry)
