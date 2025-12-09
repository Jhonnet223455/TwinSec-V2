"""
PID Controller - Controlador PID clásico

PID:
    u(t) = Kp * e(t) + Ki * ∫e(τ)dτ + Kd * de/dt
    
    e(t) = setpoint - measured_value
"""

import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class PIDController:
    """
    Controlador PID con anti-windup.
    
    Attributes:
        Kp: Ganancia proporcional
        Ki: Ganancia integral
        Kd: Ganancia derivativa
        setpoint: Punto de consigna
        integral: Acumulador integral
        prev_error: Error previo (para derivada)
        output_limits: Límites de salida (min, max)
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Inicializa el controlador PID.
        
        Args:
            config: Diccionario con configuración:
                - Kp, Ki, Kd: Ganancias
                - setpoint: Punto de consigna
                - output_min, output_max: Límites
                - controlled_variable: Nombre de la variable a controlar
                - manipulated_variable: Nombre de la variable manipulada
        """
        self.Kp = config.get("Kp", 1.0)
        self.Ki = config.get("Ki", 0.1)
        self.Kd = config.get("Kd", 0.05)
        
        self.setpoint = config.get("setpoint", 0.0)
        
        self.output_min = config.get("output_min", 0.0)
        self.output_max = config.get("output_max", 1.0)
        
        self.controlled_variable = config.get("controlled_variable", "tank.level_sensor")
        self.manipulated_variable = config.get("manipulated_variable", "valve_in_target")
        
        # Estado interno
        self.integral = 0.0
        self.prev_error = 0.0
        
        logger.info(f"PID Controller: Kp={self.Kp}, Ki={self.Ki}, Kd={self.Kd}, SP={self.setpoint}")
    
    def compute(self, signals: Dict[str, float], dt: float) -> Dict[str, float]:
        """
        Calcula la acción de control.
        
        Args:
            signals: Señales medidas del sistema
            dt: Paso de tiempo (segundos)
            
        Returns:
            Dict con variable manipulada
        """
        # Obtener valor medido
        measured_value = signals.get(self.controlled_variable, 0.0)
        
        # Error
        error = self.setpoint - measured_value
        
        # Término proporcional
        P = self.Kp * error
        
        # Término integral (con anti-windup)
        self.integral += error * dt
        I = self.Ki * self.integral
        
        # Término derivativo
        if dt > 0:
            derivative = (error - self.prev_error) / dt
        else:
            derivative = 0.0
        D = self.Kd * derivative
        
        # Salida PID
        output = P + I + D
        
        # Saturación
        output_saturated = max(self.output_min, min(self.output_max, output))
        
        # Anti-windup: detener integración si saturado
        if output != output_saturated:
            self.integral -= error * dt  # Revertir integración
        
        # Actualizar error previo
        self.prev_error = error
        
        logger.debug(f"PID: e={error:.3f}, P={P:.3f}, I={I:.3f}, D={D:.3f}, u={output_saturated:.3f}")
        
        return {
            self.manipulated_variable: output_saturated
        }
    
    def reset(self):
        """Resetea el estado interno del controlador."""
        self.integral = 0.0
        self.prev_error = 0.0
        logger.info("PID Controller reseteado")
    
    def set_setpoint(self, new_setpoint: float):
        """Cambia el setpoint dinámicamente."""
        self.setpoint = new_setpoint
        logger.info(f"Setpoint actualizado: {new_setpoint}")
