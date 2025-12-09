"""
Pydantic schemas for simulation execution and real-time data.
"""
from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field
from enum import Enum


class SimulationStatus(str, Enum):
    """Simulation execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    STOPPED = "stopped"


class SimulationCreate(BaseModel):
    """Request to create/start a new simulation."""
    model_id: str = Field(..., description="ID of the model to simulate")
    duration: Optional[float] = Field(default=None, description="Override max duration")
    dt: Optional[float] = Field(default=None, description="Override time step")
    initial_conditions: Optional[Dict[str, float]] = Field(default=None, description="Override initial conditions")


class SimulationResponse(BaseModel):
    """Response after creating a simulation."""
    run_id: str = Field(..., description="Unique simulation run ID")
    status: SimulationStatus
    model_id: str
    created_at: datetime
    websocket_url: str = Field(..., description="WebSocket URL for real-time data")

    class Config:
        json_schema_extra = {
            "example": {
                "run_id": "run_123abc",
                "status": "running",
                "model_id": "tank_2v_demo",
                "created_at": "2025-10-01T10:00:00Z",
                "websocket_url": "ws://localhost:8000/ws/simulation/run_123abc"
            }
        }


class SimulationState(BaseModel):
    """Current state of a simulation."""
    run_id: str
    status: SimulationStatus
    current_time: float = Field(..., description="Simulation time in seconds")
    progress: float = Field(..., ge=0.0, le=1.0, description="Progress (0-1)")
    signals: Dict[str, float] = Field(default_factory=dict, description="Current signal values")


class CommandType(str, Enum):
    """Types of commands that can be sent to a simulation."""
    PAUSE = "pause"
    RESUME = "resume"
    STOP = "stop"
    SET_PARAMETER = "set_parameter"
    ENABLE_ATTACK = "enable_attack"
    DISABLE_ATTACK = "disable_attack"


class SimulationCommand(BaseModel):
    """Command to control a running simulation."""
    command: CommandType
    payload: Optional[Dict[str, Any]] = Field(default=None, description="Command-specific data")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "command": "set_parameter",
                    "payload": {
                        "component_id": "V_in",
                        "param": "Kv",
                        "value": 1.5
                    }
                },
                {
                    "command": "enable_attack",
                    "payload": {
                        "attack_type": "fdi",
                        "target": "T1.h",
                        "mode": "bias",
                        "value": 0.5
                    }
                }
            ]
        }


class TelemetryMessage(BaseModel):
    """Real-time telemetry data sent via WebSocket."""
    type: str = "telemetry"
    run_id: str
    timestamp: float = Field(..., description="Simulation time")
    signals: Dict[str, float] = Field(..., description="Signal name -> value")
    alarms: Optional[List[str]] = Field(default=None, description="Active alarms")


class EventMessage(BaseModel):
    """Event notification sent via WebSocket."""
    type: str = "event"
    run_id: str
    timestamp: float
    event_type: str = Field(..., description="Type of event (e.g., 'attack_enabled', 'threshold_exceeded')")
    details: Dict[str, Any]


class ErrorMessage(BaseModel):
    """Error message sent via WebSocket."""
    type: str = "error"
    run_id: str
    error: str
    details: Optional[str] = None
