# Motor de Simulación - TwinSec Studio

## 📋 Descripción General

El **Motor de Simulación** es el componente central de TwinSec Studio que ejecuta simulaciones de sistemas OT/ICS con:

✅ **Integración numérica** (Euler, Runge-Kutta 4)  
✅ **Plugins de sistemas** (Tank, HVAC, Motor)  
✅ **Controladores automáticos** (PID)  
✅ **Inyección de ataques** en tiempo real  
✅ **Telemetría por WebSocket**  

---

## 🏗️ Arquitectura

```
Backend/
├── engine/
│   ├── __init__.py
│   ├── core/
│   │   ├── __init__.py
│   │   ├── simulator.py          # ⚙️ Motor principal
│   │   └── plugin_manager.py     # 🔌 Gestor de plugins
│   ├── plugins/
│   │   ├── __init__.py
│   │   └── tank_plugin.py        # 🚰 Plugin de tanque
│   └── controllers/
│       ├── __init__.py
│       └── pid_controller.py     # 🎛️ Controlador PID
└── api/app/routers/
    └── websocket.py               # 📡 WebSocket telemetría
```

---

## ⚙️ Simulator Core

### Clase: `Simulator`

**Ubicación:** `engine/core/simulator.py`

Motor principal que orquesta la simulación:

```python
from engine.core.simulator import Simulator

simulator = Simulator(
    model=tank_model_json,  # Modelo JSON del LLM
    run_id=1,               # ID de SimulationRun en BD
    dt=0.1,                 # Paso de integración (s)
    method="rk4"            # 'euler' o 'rk4'
)

simulator.initialize()
await simulator.run(websocket_send=telemetry_callback)
```

### Flujo de Simulación

```
┌─────────────────────────────────────────────────────────────────┐
│                         STEP DE SIMULACIÓN                      │
└─────────────────────────────────────────────────────────────────┘

1. Calcular señales REALES del sistema
   ├─ Plugin.compute_signals(state)
   └─ Ejemplo: {"tank.level_sensor": 5.3}

2. INYECTAR ATAQUES 🎯
   ├─ AttackService.inject_attacks(t, run_id, signals)
   └─ Ejemplo: {"tank.level_sensor": 8.5}  ⚠️ FALSO

3. Computar control con señales ATACADAS
   ├─ Controller.compute(observed_signals, t)
   └─ PID recibe datos falsos → acción incorrecta

4. Integrar ecuaciones con dinámica REAL
   ├─ Plugin.compute_derivatives(t, state, control)
   └─ RK4 o Euler

5. Actualizar ataques en BD
   └─ armed → active → completed

6. Enviar telemetría por WebSocket
   └─ {real_state, observed_state, control, attacks}

7. t = t + dt
```

### Métodos de Integración

#### Euler (Orden 1)
```python
x(t + dt) = x(t) + dt * f(t, x)
```

- Rápido pero menos preciso
- Usar para sistemas simples o demos

#### Runge-Kutta 4 (Orden 4)
```python
k1 = f(t, x)
k2 = f(t + dt/2, x + dt/2 * k1)
k3 = f(t + dt/2, x + dt/2 * k2)
k4 = f(t + dt, x + dt * k3)

x(t + dt) = x(t) + dt/6 * (k1 + 2*k2 + 2*k3 + k4)
```

- **Recomendado** para sistemas OT/ICS
- Mayor precisión con mismo dt

---

## 🔌 Sistema de Plugins

### Clase Base: `PluginBase`

**Ubicación:** `engine/core/plugin_manager.py`

Todos los plugins heredan de esta clase:

```python
class PluginBase:
    def get_initial_state(self, model: Dict) -> Dict[str, float]:
        """Estado inicial del sistema."""
        raise NotImplementedError()
    
    def compute_derivatives(self, t, state, control, model) -> Dict[str, float]:
        """Ecuaciones diferenciales: dx/dt."""
        raise NotImplementedError()
    
    def compute_signals(self, state: Dict) -> Dict[str, float]:
        """Señales observables (sensores)."""
        raise NotImplementedError()
```

### Plugin Manager

Auto-descubre plugins en `engine/plugins/`:

```python
from engine.core.plugin_manager import get_plugin_manager

pm = get_plugin_manager()
print(pm.list_plugins())  # ['tank', 'hvac', 'motor']

tank_plugin = pm.get_plugin('tank')
```

---

## 🚰 Tank Plugin

**Ubicación:** `engine/plugins/tank_plugin.py`

### Ecuaciones Diferenciales

**Ecuación de nivel del tanque:**

$$
\frac{dh}{dt} = \frac{Q_{in} - Q_{out}}{A}
$$

**Flujos:**

$$
Q_{in} = C_v^{in} \cdot \text{valve\_in} \cdot \sqrt{\Delta P_{in}}
$$

$$
Q_{out} = C_v^{out} \cdot \text{valve\_out} \cdot \sqrt{2 g h}
$$

**Dinámica de válvulas (primer orden):**

$$
\frac{d(\text{valve})}{dt} = \frac{\text{valve\_target} - \text{valve}}{τ}
$$

### Parámetros del Modelo

```json
{
  "type": "tank",
  "parameters": {
    "area": 10.0,          // Área transversal (m²)
    "max_height": 10.0,    // Altura máxima (m)
    "Cv_in": 0.05,         // Coeficiente válvula entrada
    "Cv_out": 0.05,        // Coeficiente válvula salida
    "dP_in": 200000,       // ΔP entrada (Pa) = 2 bar
    "tau_valve": 2.0       // Constante tiempo válvula (s)
  },
  "initial_conditions": {
    "level": 5.0,
    "valve_in_position": 0.5,
    "valve_out_position": 0.5
  }
}
```

### Señales

| Señal | Descripción |
|-------|-------------|
| `tank.level_sensor` | Nivel del tanque (m) |
| `tank.valve_in_position` | Posición válvula entrada (0-1) |
| `tank.valve_out_position` | Posición válvula salida (0-1) |

---

## 🎛️ Controlador PID

**Ubicación:** `engine/controllers/pid_controller.py`

### Ecuación PID

$$
u(t) = K_p \cdot e(t) + K_i \cdot \int e(\tau) d\tau + K_d \cdot \frac{de}{dt}
$$

Donde:
- $e(t) = \text{setpoint} - \text{measured\_value}$
- $K_p$: Ganancia proporcional
- $K_i$: Ganancia integral
- $K_d$: Ganancia derivativa

### Configuración

```json
{
  "type": "pid",
  "Kp": 0.5,
  "Ki": 0.1,
  "Kd": 0.05,
  "setpoint": 7.0,                        // Mantener nivel en 7m
  "output_min": 0.0,
  "output_max": 1.0,
  "controlled_variable": "tank.level_sensor",
  "manipulated_variable": "valve_in_target"
}
```

### Características

✅ **Anti-windup:** Detiene integración cuando la salida satura  
✅ **Límites de salida:** Restringe $u(t)$ a $[u_{min}, u_{max}]$  
✅ **Derivada del error:** Filtro para reducir ruido  

### Uso

```python
from engine.controllers.pid_controller import PIDController

pid = PIDController(controller_config)

# En cada step
control_actions = pid.compute(
    signals={"tank.level_sensor": 5.3},
    dt=0.1
)
# {'valve_in_target': 0.65}
```

---

## 📡 WebSocket Telemetría

**Ubicación:** `api/app/routers/websocket.py`

### Endpoint

```
ws://localhost:8001/ws/runs/{run_id}/telemetry
```

### Formato de Datos

**Enviados al cliente:**

```json
{
  "timestamp": 12.5,
  "real_state": {
    "tank.level_sensor": 7.3,
    "tank.valve_in_position": 0.6,
    "tank.valve_out_position": 0.4
  },
  "observed_state": {
    "tank.level_sensor": 8.5,  // ⚠️ Atacado
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
```

**Comandos del cliente:**

```json
{"command": "pause"}
{"command": "resume"}
{"command": "stop"}
```

### Conexión desde Frontend

```javascript
const ws = new WebSocket('ws://localhost:8001/ws/runs/1/telemetry');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  
  // Graficar nivel real vs observado
  plotChart(data.timestamp, data.real_state['tank.level_sensor'], data.observed_state['tank.level_sensor']);
  
  // Mostrar ataques activos
  if (data.attacks.length > 0) {
    showAttackAlert(data.attacks[0]);
  }
};

// Pausar simulación
ws.send(JSON.stringify({command: 'pause'}));
```

---

## 🧪 Prueba Completa

**Script:** `Backend/test_simulation.py`

### Escenario de Prueba

1. Sistema de tanque con PID manteniendo nivel en 7m
2. En **t=10s** se inyecta **false_data_injection** (reporta 8.5m)
3. PID recibe datos falsos → cierra válvula entrada
4. Nivel real baja → sistema se desestabiliza

### Ejecución

```powershell
cd Backend
python test_simulation.py
```

**Salida esperada:**

```
============================================================
SIMULACIÓN DE TANQUE CON INYECCIÓN DE CIBERATAQUE
============================================================

⚠️  Registrando ataque: False Data Injection en tank.level_sensor
    - Inicio: t=10s
    - Duración: 20s
    - Valor falso: 8.5m

Iniciando simulación...

t=  0.00s | Real: 5.000m | Observed: 5.000m | Control: 0.650
t=  1.00s | Real: 5.234m | Observed: 5.234m | Control: 0.678
t=  2.00s | Real: 5.456m | Observed: 5.456m | Control: 0.698
...
t= 10.00s | Real: 6.823m | Observed: 8.500m | Control: 0.250 | ATTACK: false_data_injection ACTIVE
t= 11.00s | Real: 6.654m | Observed: 8.500m | Control: 0.220 | ATTACK: false_data_injection ACTIVE
...
t= 30.00s | Real: 5.102m | Observed: 5.102m | Control: 0.780
...

============================================================
SIMULACIÓN COMPLETADA
============================================================
```

---

## 🔗 Integración con API REST

### Crear simulación

**POST** `/api/v1/runs`

```json
{
  "model_id": 1,
  "name": "Tank Attack Test",
  "description": "Simulación con false_data_injection en t=10s",
  "duration": 50.0
}
```

**Response:**

```json
{
  "id": 1,
  "status": "pending",
  "start_time": null,
  "progress": 0.0
}
```

### Registrar ataque

**POST** `/api/v1/attacks`

```json
{
  "simulation_run_id": 1,
  "attack_type": "false_data_injection",
  "target_component": "tank",
  "target_signal": "tank.level_sensor",
  "trigger_time": 10.0,
  "duration": 20.0,
  "parameters": {
    "false_value": 8.5
  }
}
```

### Iniciar simulación (TODO)

**POST** `/api/v1/runs/{run_id}/start`

```json
{
  "dt": 0.1,
  "method": "rk4"
}
```

Internamente:
```python
simulator = Simulator(model=model_json, run_id=run_id, dt=0.1, method="rk4")
simulator.initialize()
asyncio.create_task(simulator.run(websocket_send=broadcast_telemetry))
```

### Conectar WebSocket

```javascript
const ws = new WebSocket(`ws://localhost:8001/ws/runs/1/telemetry`);
```

---

## 📊 Visualización en Frontend

### Gráfica de Nivel

```
        Level (m)
10 |                           
9  |                           
8  |        -------- (Observed - FALSO)
7  |-----                      ------
6  |     \                    /
5  |      \                  /  (Real)
4  |       ------------------
   +--------------------------------> t (s)
   0       10      20      30      40
        ↑ Ataque inicia
```

### Dashboard

```
┌────────────────────────────────────────────────────┐
│ SIMULACIÓN: Tank Attack Test          RUN ID: 1   │
├────────────────────────────────────────────────────┤
│ Tiempo: 15.3s / 50.0s          [■■■■■□□□□□] 30%  │
│                                                    │
│ ⚠️ ATAQUE ACTIVO                                   │
│ Tipo: False Data Injection                        │
│ Target: tank.level_sensor                         │
│ Valor Falso: 8.5m                                 │
│                                                    │
│ ESTADO REAL              ESTADO OBSERVADO         │
│ ├─ Nivel: 6.5m          ├─ Nivel: 8.5m ⚠️        │
│ ├─ Válvula In: 0.3      ├─ Válvula In: 0.3       │
│ └─ Válvula Out: 0.5     └─ Válvula Out: 0.5      │
│                                                    │
│ CONTROL PID                                       │
│ ├─ Setpoint: 7.0m                                │
│ ├─ Error (falso): -1.5m                          │
│ └─ Acción: 0.25 (cierra entrada)                 │
│                                                    │
│ [PAUSE] [STOP] [EXPORT]                          │
└────────────────────────────────────────────────────┘
```

---

## 🚀 Próximos Pasos

### Objetivo 3 - Completar Testing
- [ ] Ejecutar `test_simulation.py` con éxito
- [ ] Crear endpoint REST `/runs/{run_id}/start`
- [ ] Integrar simulaciones con BD
- [ ] Probar WebSocket con cliente real

### Objetivo 4 - IDS
- [ ] Implementar detección por umbrales
- [ ] Detección de anomalías estadísticas
- [ ] ML para detección avanzada
- [ ] Generar alertas en tiempo real

---

## 📚 Referencias

- [Runge-Kutta Methods](https://en.wikipedia.org/wiki/Runge%E2%80%93Kutta_methods)
- [PID Controller Theory](https://en.wikipedia.org/wiki/PID_controller)
- [WebSocket Protocol](https://datatracker.ietf.org/doc/html/rfc6455)
- **ATTACK_INJECTION_SYSTEM.md** - Sistema de inyección de ataques

---

**Autor:** TwinSec Studio  
**Versión:** 0.3.0  
**Fecha:** 2025-11-07
