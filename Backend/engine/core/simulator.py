"""
Simulator Core - Motor principal de simulación

Orquesta la ejecución de simulaciones con:
- Integración numérica (RK4, Euler)
- Gestión de estado
- Inyección de ataques
- Telemetría en tiempo real
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
import numpy as np
from dataclasses import dataclass, field

# Imports del proyecto
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent.parent))

from api.app.services.attack_service import get_attack_service
from api.app.database import SessionLocal
from api.app.models import SimulationRun, Attack

logger = logging.getLogger(__name__)


@dataclass
class SimulationState:
    """
    Estado actual de la simulación.
    """
    t: float = 0.0                    # Tiempo actual (segundos)
    state: Dict[str, float] = field(default_factory=dict)  # Variables de estado
    signals: Dict[str, float] = field(default_factory=dict)  # Señales observables
    control: Dict[str, float] = field(default_factory=dict)  # Acciones de control
    
    def to_dict(self) -> Dict:
        """Serializa el estado para envío por WebSocket."""
        return {
            "t": self.t,
            "state": self.state,
            "signals": self.signals,
            "control": self.control
        }


class Simulator:
    """
    Motor de simulación principal.
    
    Ejecuta la simulación de un sistema OT/ICS con soporte para:
    - Ecuaciones diferenciales
    - Inyección de ataques cibernéticos
    - Control automático (PID, etc.)
    - Telemetría en tiempo real
    
    Attributes:
        model: Diccionario con la definición del modelo
        run_id: ID de la simulación en BD
        dt: Paso de integración (segundos)
        method: Método de integración ('euler', 'rk4')
        state: Estado actual de la simulación
    """
    
    def __init__(
        self,
        model: Dict[str, Any],
        run_id: int,
        dt: float = 0.1,
        method: str = "rk4"
    ):
        """
        Inicializa el simulador.
        
        Args:
            model: Modelo JSON del sistema (generado por LLM)
            run_id: ID de SimulationRun en BD
            dt: Paso de tiempo de integración (segundos)
            method: Método de integración ('euler' o 'rk4')
        """
        self.model = model
        self.run_id = run_id
        self.dt = dt
        self.method = method
        
        # Estado de simulación
        self.state = SimulationState()
        
        # Servicio de ataques
        self.attack_service = get_attack_service()
        
        # Plugin del sistema (tank, hvac, motor, etc.)
        self.plugin = None
        
        # Controlador (PID, MPC, etc.)
        self.controller = None
        
        # Duración de la simulación
        self.duration = model.get("simulation", {}).get("duration", 100.0)
        
        # Estado de ejecución
        self.running = False
        self.paused = False
        
        logger.info(f"Simulator iniciado para run_id={run_id}, dt={dt}, method={method}")
    
    def initialize(self):
        """
        Inicializa el simulador con el modelo.
        
        - Carga el plugin apropiado según el tipo de modelo
        - Inicializa el estado inicial
        - Carga ataques de la BD
        - Configura el controlador
        """
        logger.info(f"Inicializando simulación para modelo: {self.model.get('name')}")
        
        # 1. Cargar plugin según tipo de modelo
        model_type = self.model.get("type", "tank")
        self.plugin = self._load_plugin(model_type)
        
        # 2. Inicializar estado con valores iniciales del modelo
        self.state.state = self.plugin.get_initial_state(self.model)
        self.state.signals = self.plugin.compute_signals(self.state.state)
        
        logger.info(f"Estado inicial: {self.state.state}")
        
        # 3. Cargar ataques de la BD para este run
        self._load_attacks_from_db()
        
        # 4. Inicializar controlador (si aplica)
        if "controller" in self.model:
            self.controller = self._load_controller(self.model["controller"])
        
        logger.info("Simulación inicializada correctamente")
    
    def _load_plugin(self, model_type: str):
        """Carga el plugin apropiado según el tipo de modelo."""
        from engine.core.plugin_manager import get_plugin_manager
        
        plugin_manager = get_plugin_manager()
        plugin = plugin_manager.get_plugin(model_type)
        
        if not plugin:
            raise ValueError(f"Plugin no encontrado para tipo de modelo: {model_type}")
        
        return plugin
    
    def _load_controller(self, controller_config: Dict):
        """Carga el controlador según configuración."""
        controller_type = controller_config.get("type", "pid")
        
        if controller_type == "pid":
            from engine.controllers.pid_controller import PIDController
            return PIDController(controller_config)
        else:
            logger.warning(f"Controlador {controller_type} no implementado, usando control manual")
            return None
    
    def _load_attacks_from_db(self):
        """Carga ataques registrados en BD para este run."""
        db = SessionLocal()
        try:
            attacks = db.query(Attack).filter(
                Attack.simulation_run_id == self.run_id,
                Attack.status.in_(["armed", "active"])
            ).all()
            
            logger.info(f"Cargando {len(attacks)} ataques para run_id={self.run_id}")
            
            for attack in attacks:
                self.attack_service.register_attack(
                    attack_id=attack.attack_id,
                    attack_type=attack.attack_type,
                    target_signal=attack.target_signal,
                    start_time=attack.trigger_time,
                    duration=attack.duration,
                    params={
                        "target_signal": attack.target_signal,
                        **attack.parameters
                    }
                )
                logger.info(f"  - Ataque {attack.attack_type} en {attack.target_signal} @ t={attack.trigger_time}s")
        
        finally:
            db.close()
    
    async def run(self, websocket_send: Optional[Callable] = None):
        """
        Ejecuta la simulación completa.
        
        Args:
            websocket_send: Función async para enviar telemetría
                          Ejemplo: websocket_send(data)
        """
        logger.info(f"Iniciando simulación (duración={self.duration}s, dt={self.dt}s)")
        
        self.running = True
        
        # Actualizar BD: simulación iniciando
        self._update_run_status("running")
        
        try:
            while self.state.t < self.duration and self.running:
                # Si está pausada, esperar
                if self.paused:
                    await asyncio.sleep(0.1)
                    continue
                
                # Ejecutar un paso de simulación
                await self.step(websocket_send)
                
                # Control de velocidad de simulación (tiempo real)
                # await asyncio.sleep(self.dt)  # Descomentar para tiempo real
                await asyncio.sleep(0.05)  # 20 FPS para visualización fluida
            
            # Simulación completada
            logger.info(f"Simulación completada: t={self.state.t:.2f}s")
            self._update_run_status("completed")
        
        except Exception as e:
            logger.error(f"Error en simulación: {str(e)}", exc_info=True)
            self._update_run_status("failed", error_message=str(e))
            raise
        
        finally:
            self.running = False
    
    async def step(self, websocket_send: Optional[Callable] = None):
        """
        Ejecuta un paso de simulación.
        
        Flujo:
        1. Calcular señales reales del sistema
        2. Inyectar ataques cibernéticos
        3. Computar acciones de control con señales atacadas
        4. Integrar ecuaciones diferenciales con dinámica real
        5. Actualizar estados de ataques en BD
        6. Enviar telemetría por WebSocket
        """
        # 1. Calcular señales reales
        real_signals = self.plugin.compute_signals(self.state.state)
        
        # 2. INYECTAR ATAQUES 🎯
        observed_signals = self.attack_service.inject_attacks(
            t=self.state.t,
            run_id=self.run_id,
            signals=real_signals
        )
        
        # 3. Computar control con señales observadas (atacadas)
        if self.controller:
            control_actions = self.controller.compute(observed_signals, self.state.t)
        else:
            # Control manual o sin control
            control_actions = self.model.get("control", {}).get("manual_setpoints", {})
        
        # 4. Integrar estado con dinámica REAL
        self._integrate(control_actions)
        
        # 5. Actualizar estados de ataques en BD
        self._update_attack_states()
        
        # 6. Enviar telemetría
        if websocket_send:
            telemetry = {
                "timestamp": self.state.t,
                "real_state": real_signals,
                "observed_state": observed_signals,
                "control_actions": control_actions,
                "attacks": self.attack_service.get_active_attacks_for_run(self.run_id)
            }
            await websocket_send(telemetry)
        
        # Incrementar tiempo
        self.state.t += self.dt
    
    def _integrate(self, control_actions: Dict[str, float]):
        """
        Integra las ecuaciones diferenciales un paso de tiempo.
        
        Args:
            control_actions: Acciones de control calculadas
        """
        if self.method == "euler":
            self._integrate_euler(control_actions)
        elif self.method == "rk4":
            self._integrate_rk4(control_actions)
        else:
            raise ValueError(f"Método de integración desconocido: {self.method}")
    
    def _integrate_euler(self, control_actions: Dict[str, float]):
        """Método de Euler (orden 1)."""
        # Calcular derivadas
        derivatives = self.plugin.compute_derivatives(
            t=self.state.t,
            state=self.state.state,
            control=control_actions,
            model=self.model
        )
        
        # Actualizar estado: x(t+dt) = x(t) + dt * dx/dt
        for var, dvar in derivatives.items():
            self.state.state[var] = self.state.state[var] + self.dt * dvar
    
    def _integrate_rk4(self, control_actions: Dict[str, float]):
        """Método Runge-Kutta 4 (orden 4)."""
        # k1 = f(t, x)
        k1 = self.plugin.compute_derivatives(
            t=self.state.t,
            state=self.state.state,
            control=control_actions,
            model=self.model
        )
        
        # k2 = f(t + dt/2, x + dt/2 * k1)
        state_k2 = {var: val + self.dt/2 * k1[var] for var, val in self.state.state.items()}
        k2 = self.plugin.compute_derivatives(
            t=self.state.t + self.dt/2,
            state=state_k2,
            control=control_actions,
            model=self.model
        )
        
        # k3 = f(t + dt/2, x + dt/2 * k2)
        state_k3 = {var: val + self.dt/2 * k2[var] for var, val in self.state.state.items()}
        k3 = self.plugin.compute_derivatives(
            t=self.state.t + self.dt/2,
            state=state_k3,
            control=control_actions,
            model=self.model
        )
        
        # k4 = f(t + dt, x + dt * k3)
        state_k4 = {var: val + self.dt * k3[var] for var, val in self.state.state.items()}
        k4 = self.plugin.compute_derivatives(
            t=self.state.t + self.dt,
            state=state_k4,
            control=control_actions,
            model=self.model
        )
        
        # x(t+dt) = x(t) + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
        for var in self.state.state.keys():
            self.state.state[var] = self.state.state[var] + self.dt / 6 * (
                k1[var] + 2*k2[var] + 2*k3[var] + k4[var]
            )
    
    def _update_attack_states(self):
        """Sincroniza estados de ataques con BD."""
        db = SessionLocal()
        try:
            for attack_id, attack_data in self.attack_service._active_attacks.items():
                db_attack = db.query(Attack).filter(
                    Attack.attack_id == attack_id
                ).first()
                
                if db_attack and db_attack.status != attack_data["status"]:
                    db_attack.status = attack_data["status"]
                    
                    if attack_data["status"] == "active" and not db_attack.started_at:
                        db_attack.started_at = datetime.utcnow()
                    
                    if attack_data["status"] == "completed" and not db_attack.ended_at:
                        db_attack.ended_at = datetime.utcnow()
                        db_attack.success = True
            
            db.commit()
        finally:
            db.close()
    
    def _update_run_status(self, status: str, error_message: str = None):
        """Actualiza el estado de la simulación en BD."""
        db = SessionLocal()
        try:
            run = db.query(SimulationRun).filter(SimulationRun.id == self.run_id).first()
            if run:
                run.status = status
                run.progress = min(self.state.t / self.duration, 1.0)
                
                if status == "running" and not run.start_time:
                    run.start_time = datetime.utcnow()
                
                if status in ["completed", "failed"]:
                    run.end_time = datetime.utcnow()
                    if run.start_time:
                        run.execution_time = (run.end_time - run.start_time).total_seconds()
                
                if error_message:
                    run.error_message = error_message
                
                db.commit()
        finally:
            db.close()
    
    def pause(self):
        """Pausa la simulación."""
        self.paused = True
        logger.info("Simulación pausada")
    
    def resume(self):
        """Reanuda la simulación."""
        self.paused = False
        logger.info("Simulación reanudada")
    
    def stop(self):
        """Detiene la simulación."""
        self.running = False
        self._update_run_status("stopped")
        logger.info("Simulación detenida")
