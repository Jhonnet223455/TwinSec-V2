"""
Tank Plugin - Sistema de tanque con válvulas

Ecuaciones:
    dh/dt = (Q_in - Q_out) / A
    
    Q_in = Cv * valve_position * sqrt(ΔP_in)
    Q_out = Cv * sqrt(2 * g * h)
    
Variables de estado:
    - h: Nivel del tanque (m)
    - valve_in_position: Posición válvula entrada (0-1)
    - valve_out_position: Posición válvula salida (0-1)

Señales:
    - tank.level_sensor: Sensor de nivel (m)
    - tank.flow_in: Flujo de entrada (m³/s)
    - tank.flow_out: Flujo de salida (m³/s)
"""

import logging
from typing import Dict, Any
from engine.core.plugin_manager import PluginBase

logger = logging.getLogger(__name__)


class TankPlugin(PluginBase):
    """
    Plugin para sistema de tanque de agua.
    """
    
    def get_initial_state(self, model: Dict[str, Any]) -> Dict[str, float]:
        """
        Estado inicial del tanque.
        
        Extrae del modelo JSON:
        - initial_conditions.level
        - initial_conditions.valve_in_position
        - initial_conditions.valve_out_position
        """
        initial = model.get("initial_conditions", {})
        
        state = {
            "h": initial.get("level", 5.0),                    # Nivel inicial (m)
            "valve_in_position": initial.get("valve_in_position", 0.5),
            "valve_out_position": initial.get("valve_out_position", 0.5)
        }
        
        logger.info(f"Estado inicial del tanque: h={state['h']}m")
        return state
    
    def compute_derivatives(
        self,
        t: float,
        state: Dict[str, float],
        control: Dict[str, float],
        model: Dict[str, Any]
    ) -> Dict[str, float]:
        """
        Calcula dh/dt, d(valve_in)/dt, d(valve_out)/dt.
        
        Ecuaciones:
            dh/dt = (Q_in - Q_out) / A
            d(valve)/dt = (valve_target - valve_current) / tau
        """
        # Parámetros del tanque
        params = model.get("parameters", {})
        A = params.get("area", 10.0)              # Área (m²)
        Cv_in = params.get("Cv_in", 0.05)         # Coeficiente válvula entrada
        Cv_out = params.get("Cv_out", 0.05)       # Coeficiente válvula salida
        dP_in = params.get("dP_in", 2e5)          # ΔP entrada (Pa)
        g = 9.81                                   # Gravedad (m/s²)
        tau_valve = params.get("tau_valve", 2.0)  # Constante tiempo válvula (s)
        
        # Estado actual
        h = state["h"]
        valve_in = state["valve_in_position"]
        valve_out = state["valve_out_position"]
        
        # Control targets
        valve_in_target = control.get("valve_in_target", valve_in)
        valve_out_target = control.get("valve_out_target", valve_out)
        
        # Flujos
        Q_in = Cv_in * valve_in * (dP_in ** 0.5)
        Q_out = Cv_out * valve_out * ((2 * g * max(h, 0)) ** 0.5)
        
        # Derivadas
        dh_dt = (Q_in - Q_out) / A
        
        # Dinámica de válvulas (primer orden)
        dvalve_in_dt = (valve_in_target - valve_in) / tau_valve
        dvalve_out_dt = (valve_out_target - valve_out) / tau_valve
        
        derivatives = {
            "h": dh_dt,
            "valve_in_position": dvalve_in_dt,
            "valve_out_position": dvalve_out_dt
        }
        
        # Limitar nivel físicamente (no puede ser negativo)
        if h <= 0 and dh_dt < 0:
            derivatives["h"] = 0
        
        # Limitar altura máxima del tanque
        max_height = params.get("max_height", 10.0)
        if h >= max_height and dh_dt > 0:
            derivatives["h"] = 0
        
        return derivatives
    
    def compute_signals(self, state: Dict[str, float]) -> Dict[str, float]:
        """
        Calcula señales observables (sensores).
        
        Returns:
            - tank.level_sensor: Nivel medido
            - tank.valve_in_position: Posición válvula entrada
            - tank.valve_out_position: Posición válvula salida
        """
        signals = {
            "tank.level_sensor": state["h"],
            "tank.valve_in_position": state["valve_in_position"],
            "tank.valve_out_position": state["valve_out_position"]
        }
        
        return signals
