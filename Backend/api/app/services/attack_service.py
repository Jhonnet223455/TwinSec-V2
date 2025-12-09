"""
Attack Injection Service

Sistema de inyección de ataques cibernéticos en simulaciones OT.
Soporta múltiples tipos de ataques con parámetros configurables.

Tipos de ataques:
1. DoS (Denial of Service) - Bloquea una señal completamente
2. False Data Injection - Inyecta valores falsos en sensores
3. Replay Attack - Repite valores antiguos (secuencia grabada)
4. Ramp Attack - Incremento/decremento gradual de valores
5. Random Noise - Ruido aleatorio sobre la señal real
"""

import logging
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum

logger = logging.getLogger(__name__)


class AttackType(str, Enum):
    """Tipos de ataques soportados."""
    DOS = "dos"  # Denial of Service
    FALSE_DATA = "false_data_injection"
    REPLAY = "replay_attack"
    RAMP = "ramp_attack"
    RANDOM_NOISE = "random_noise"
    MITM = "man_in_the_middle"  # Futuro


class AttackStatus(str, Enum):
    """Estados de un ataque."""
    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"


class AttackService:
    """
    Servicio de inyección de ataques en simulaciones.
    
    Permite inyectar ataques en tiempo de simulación para evaluar
    la respuesta del IDS y el comportamiento del sistema.
    """
    
    def __init__(self):
        """Inicializar servicio de ataques."""
        self.active_attacks: Dict[str, Dict] = {}
        logger.info("✅ AttackService inicializado")
    
    def validate_attack_params(
        self,
        attack_type: AttackType,
        params: Dict[str, Any]
    ) -> tuple[bool, Optional[str]]:
        """
        Valida los parámetros de un ataque.
        
        Args:
            attack_type: Tipo de ataque
            params: Parámetros del ataque
        
        Returns:
            (válido, mensaje_error)
        """
        if attack_type == AttackType.DOS:
            # DoS: solo necesita target_signal
            if "target_signal" not in params:
                return False, "DoS requiere 'target_signal'"
            return True, None
        
        elif attack_type == AttackType.FALSE_DATA:
            # False Data Injection: valor falso a inyectar
            required = ["target_signal", "false_value"]
            missing = [k for k in required if k not in params]
            if missing:
                return False, f"False Data Injection requiere: {', '.join(missing)}"
            return True, None
        
        elif attack_type == AttackType.REPLAY:
            # Replay: necesita buffer de valores grabados
            required = ["target_signal", "replay_buffer"]
            missing = [k for k in required if k not in params]
            if missing:
                return False, f"Replay Attack requiere: {', '.join(missing)}"
            if not isinstance(params.get("replay_buffer"), list):
                return False, "replay_buffer debe ser una lista"
            return True, None
        
        elif attack_type == AttackType.RAMP:
            # Ramp: incremento gradual
            required = ["target_signal", "rate"]
            missing = [k for k in required if k not in params]
            if missing:
                return False, f"Ramp Attack requiere: {', '.join(missing)}"
            return True, None
        
        elif attack_type == AttackType.RANDOM_NOISE:
            # Random Noise: ruido gaussiano
            required = ["target_signal", "noise_std"]
            missing = [k for k in required if k not in params]
            if missing:
                return False, f"Random Noise requiere: {', '.join(missing)}"
            return True, None
        
        return False, f"Tipo de ataque no soportado: {attack_type}"
    
    def apply_dos_attack(
        self,
        signal_value: float,
        params: Dict[str, Any]
    ) -> float:
        """
        Aplica ataque DoS (Denial of Service).
        
        Bloquea completamente la señal, retornando 0 o un valor predefinido.
        
        Args:
            signal_value: Valor original de la señal
            params: Parámetros del ataque
        
        Returns:
            Valor atacado (típicamente 0)
        """
        blocked_value = params.get("blocked_value", 0.0)
        logger.debug(f"DoS: {signal_value} -> {blocked_value}")
        return blocked_value
    
    def apply_false_data_injection(
        self,
        signal_value: float,
        params: Dict[str, Any]
    ) -> float:
        """
        Aplica ataque de inyección de datos falsos.
        
        Reemplaza el valor real por un valor falso.
        
        Args:
            signal_value: Valor original
            params: Debe contener 'false_value'
        
        Returns:
            Valor falso inyectado
        """
        false_value = params["false_value"]
        logger.debug(f"False Data Injection: {signal_value} -> {false_value}")
        return false_value
    
    def apply_replay_attack(
        self,
        signal_value: float,
        params: Dict[str, Any],
        current_step: int
    ) -> float:
        """
        Aplica ataque de replay.
        
        Retorna valores de un buffer pre-grabado en lugar del valor real.
        
        Args:
            signal_value: Valor original (ignorado)
            params: Debe contener 'replay_buffer' (lista de valores)
            current_step: Paso actual de simulación
        
        Returns:
            Valor del buffer de replay
        """
        replay_buffer = params["replay_buffer"]
        
        # Ciclar el buffer si es necesario
        index = current_step % len(replay_buffer)
        replayed_value = replay_buffer[index]
        
        logger.debug(f"Replay Attack: {signal_value} -> {replayed_value} (step {current_step})")
        return replayed_value
    
    def apply_ramp_attack(
        self,
        signal_value: float,
        params: Dict[str, Any],
        elapsed_time: float
    ) -> float:
        """
        Aplica ataque de rampa.
        
        Incrementa/decrementa gradualmente el valor real.
        
        Args:
            signal_value: Valor original
            params: Debe contener 'rate' (cambio por segundo)
            elapsed_time: Tiempo desde inicio del ataque
        
        Returns:
            Valor con rampa aplicada
        """
        rate = params["rate"]
        offset = rate * elapsed_time
        attacked_value = signal_value + offset
        
        logger.debug(f"Ramp Attack: {signal_value} -> {attacked_value} (offset={offset:.2f})")
        return attacked_value
    
    def apply_random_noise(
        self,
        signal_value: float,
        params: Dict[str, Any]
    ) -> float:
        """
        Aplica ruido aleatorio.
        
        Añade ruido gaussiano al valor real.
        
        Args:
            signal_value: Valor original
            params: Debe contener 'noise_std' (desviación estándar)
        
        Returns:
            Valor con ruido añadido
        """
        noise_std = params["noise_std"]
        noise = np.random.normal(0, noise_std)
        attacked_value = signal_value + noise
        
        logger.debug(f"Random Noise: {signal_value} -> {attacked_value} (noise={noise:.3f})")
        return attacked_value
    
    def inject_attack(
        self,
        attack_id: str,
        attack_type: AttackType,
        signal_name: str,
        signal_value: float,
        params: Dict[str, Any],
        current_time: float,
        attack_start_time: float,
        current_step: int = 0
    ) -> float:
        """
        Inyecta un ataque en una señal.
        
        Args:
            attack_id: ID único del ataque
            attack_type: Tipo de ataque
            signal_name: Nombre de la señal afectada
            signal_value: Valor original de la señal
            params: Parámetros del ataque
            current_time: Tiempo actual de simulación
            attack_start_time: Tiempo de inicio del ataque
            current_step: Paso actual de simulación
        
        Returns:
            Valor de la señal después del ataque
        """
        elapsed_time = current_time - attack_start_time
        
        try:
            if attack_type == AttackType.DOS:
                return self.apply_dos_attack(signal_value, params)
            
            elif attack_type == AttackType.FALSE_DATA:
                return self.apply_false_data_injection(signal_value, params)
            
            elif attack_type == AttackType.REPLAY:
                return self.apply_replay_attack(signal_value, params, current_step)
            
            elif attack_type == AttackType.RAMP:
                return self.apply_ramp_attack(signal_value, params, elapsed_time)
            
            elif attack_type == AttackType.RANDOM_NOISE:
                return self.apply_random_noise(signal_value, params)
            
            else:
                logger.warning(f"Tipo de ataque no implementado: {attack_type}")
                return signal_value
        
        except Exception as e:
            logger.error(f"Error al inyectar ataque {attack_id}: {e}")
            return signal_value
    
    def register_attack(
        self,
        attack_id: str,
        attack_type: AttackType,
        target_signal: str,
        start_time: float,
        duration: Optional[float],
        params: Dict[str, Any]
    ):
        """
        Registra un ataque para ejecución posterior.
        
        Args:
            attack_id: ID único
            attack_type: Tipo de ataque
            target_signal: Señal objetivo
            start_time: Tiempo de inicio (segundos desde t=0)
            duration: Duración del ataque (None = indefinido)
            params: Parámetros del ataque
        """
        self.active_attacks[attack_id] = {
            "type": attack_type,
            "target_signal": target_signal,
            "start_time": start_time,
            "duration": duration,
            "params": params,
            "status": AttackStatus.PENDING,
            "registered_at": datetime.utcnow()
        }
        
        logger.info(
            f"✅ Ataque registrado: {attack_id} "
            f"({attack_type} en '{target_signal}', t={start_time}s)"
        )
    
    def get_active_attacks_for_signal(
        self,
        signal_name: str,
        current_time: float
    ) -> List[Dict]:
        """
        Obtiene los ataques activos para una señal en un tiempo dado.
        
        Args:
            signal_name: Nombre de la señal
            current_time: Tiempo actual de simulación
        
        Returns:
            Lista de ataques activos
        """
        active = []
        
        for attack_id, attack in self.active_attacks.items():
            # Verificar si el ataque afecta a esta señal
            if attack["target_signal"] != signal_name:
                continue
            
            # Verificar si el ataque está en el tiempo correcto
            start_time = attack["start_time"]
            duration = attack["duration"]
            
            if current_time < start_time:
                continue  # Aún no ha empezado
            
            if duration is not None and current_time > start_time + duration:
                attack["status"] = AttackStatus.COMPLETED
                continue  # Ya terminó
            
            # Ataque activo
            attack["status"] = AttackStatus.ACTIVE
            active.append({
                "id": attack_id,
                "type": attack["type"],
                "params": attack["params"],
                "start_time": start_time
            })
        
        return active
    
    def clear_attacks(self):
        """Limpia todos los ataques registrados."""
        self.active_attacks.clear()
        logger.info("🗑️ Ataques limpiados")


# Singleton global
_attack_service: Optional[AttackService] = None


def get_attack_service() -> AttackService:
    """Obtiene la instancia singleton del servicio de ataques."""
    global _attack_service
    
    if _attack_service is None:
        _attack_service = AttackService()
    
    return _attack_service
