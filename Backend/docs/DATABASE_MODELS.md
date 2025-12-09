# Modelos de Base de Datos - Resumen Completo

Este documento describe todos los modelos SQLAlchemy de TwinSec Studio.

---

## 📊 Resumen de Tablas

| Tabla | Propósito | Registros Típicos |
|-------|-----------|-------------------|
| `users` | Usuarios del sistema | 10-1000 |
| `models` | Modelos de simulación guardados | 50-5000 |
| `simulation_runs` | Ejecuciones de simulación | 100-50000 |
| `attacks` | Ataques configurados en simulaciones | 200-100000 |
| `ids_alerts` | Alertas del IDS | 1000-1000000 |
| `thresholds` | Umbrales de alarma | 100-10000 |
| `llm_requests` | Peticiones a LLMs | 50-10000 |
| `audit_logs` | Logs de auditoría | 1000-10000000 |

---

## 🔐 1. User - Usuarios del Sistema

**Propósito:** Gestión de autenticación y autorización.

**Campos clave:**
- `username`, `email` - Identificación única
- `hashed_password` - Contraseña hasheada con bcrypt
- `is_superuser` - Permisos de administrador
- `oauth_provider`, `oauth_id` - Integración OAuth (Google, Facebook, GitHub)

**Relaciones:**
- → `models` (1:N) - Modelos creados
- → `simulation_runs` (1:N) - Simulaciones ejecutadas
- → `llm_requests` (1:N) - Peticiones LLM realizadas
- → `audit_logs` (1:N) - Acciones auditadas

---

## 🏗️ 2. Model - Modelos de Simulación

**Propósito:** Almacenar modelos OT generados por LLM o creados manualmente.

**Campos clave:**
- `name`, `description` - Identificación
- `model_type` - tank, microgrid, drone, hvac, custom
- `content` (JSON) - Modelo completo según `twinsec_model_v1.json`
- `llm_prompt`, `llm_provider`, `llm_model` - Metadata de generación

**Relaciones:**
- ← `users` (N:1) - Creado por
- → `simulation_runs` (1:N) - Ejecuciones del modelo
- → `thresholds` (1:N) - Umbrales de alarma

**Ejemplo de content:**
```json
{
  "name": "water-tank-system",
  "type": "tank",
  "solver": {"method": "euler", "timestep": 0.1, "duration": 100},
  "components": [...],
  "connections": [...],
  "signals": [...],
  "hmi": {...},
  "attacks": [...]
}
```

---

## ▶️ 3. SimulationRun - Ejecuciones

**Propósito:** Registrar cada ejecución de simulación con su estado y resultados.

**Campos clave:**
- `run_id` (UUID) - Identificador único
- `status` - pending, running, paused, completed, failed, stopped
- `duration`, `time_step` - Parámetros de simulación
- `progress` (0.0-1.0) - Porcentaje completado
- `results_summary` (JSON) - Estadísticas finales

**Relaciones:**
- ← `users` (N:1) - Ejecutado por
- ← `models` (N:1) - Basado en modelo
- → `attacks` (1:N) - Ataques configurados
- → `ids_alerts` (1:N) - Alertas generadas

**Estados del ciclo de vida:**
```
pending → running → {completed, failed, stopped}
              ↓↑
            paused
```

---

## 💥 4. Attack - Ataques Cibernéticos

**Propósito:** Registrar ataques ejecutados durante simulaciones para análisis forense.

**Campos clave:**
- `attack_id` (UUID) - Identificador único
- `attack_type` - fdi, dos, mitm, replay
- `target_component`, `target_signal` - Objetivo del ataque
- `status` - armed, active, stopped, completed, failed
- `parameters` (JSON) - Configuración del ataque
- `trigger_time`, `duration` - Ventana temporal

**Relaciones:**
- ← `simulation_runs` (N:1) - Parte de simulación
- ← `users` (N:1) - Configurado por
- → `ids_alerts` (1:N) - Alertas relacionadas

**Ejemplo de parameters (FDI):**
```json
{
  "bias": 0.5,
  "noise_amplitude": 0.1,
  "drift_rate": 0.01,
  "attack_mode": "constant_bias"
}
```

**Ejemplo de parameters (DoS):**
```json
{
  "packet_loss_rate": 0.8,
  "burst_duration": 5.0,
  "target_protocol": "modbus"
}
```

---

## 🚨 5. IDSAlert - Alertas del IDS

**Propósito:** Detectar y registrar anomalías usando Autoencoder + SHAP.

**Campos clave:**
- `alert_id` (UUID) - Identificador único
- `severity` - low, medium, high, critical
- `anomaly_score` (0.0-1.0) - Score del Autoencoder
- `detected_attack_type` - Clasificación del ataque
- `affected_signals` (JSON) - Señales anómalas
- `shap_explanation` (JSON) - Feature importance
- `false_positive`, `true_positive` - Ground truth para entrenamiento

**Relaciones:**
- ← `simulation_runs` (N:1) - Detectado en simulación
- ← `attacks` (N:1) - Ataque real que causó la alerta (si existe)
- ← `users` (N:1) - Investigado por

**Estados:**
```
new → investigating → {confirmed, false_alarm} → resolved
```

**Ejemplo de shap_explanation:**
```json
{
  "T1.h": 0.85,    // Nivel del tanque 1 (muy importante)
  "V_in.q": 0.65,  // Flujo de entrada (importante)
  "T2.h": 0.23     // Nivel del tanque 2 (poco importante)
}
```

**Métricas del IDS:**
- **Precision** = TP / (TP + FP)
- **Recall** = TP / (TP + FN)
- **F1-Score** = 2 * (Precision * Recall) / (Precision + Recall)

---

## ⚠️ 6. Threshold - Umbrales de Alarma

**Propósito:** Definir límites de seguridad para señales del sistema.

**Campos clave:**
- `signal_name` - component_id.signal_id (ej. "T1.h")
- `threshold_type` - upper, lower, rate_of_change
- `value` - Valor del umbral
- `hysteresis` - Banda muerta (evita oscilaciones)
- `severity` - info, warning, critical
- `auto_actions` (JSON) - Acciones automáticas

**Relaciones:**
- ← `models` (N:1) - Asociado a modelo
- ← `users` (N:1) - Creado por

**Método `check_violation()`:**
```python
result = threshold.check_violation(
    current_value=1.9,
    previous_value=1.7,
    dt=0.1
)
# result = {
#   "violated": True,
#   "details": {
#     "threshold": 1.8,
#     "current_value": 1.9,
#     "excess": 0.1
#   }
# }
```

**Ejemplo de auto_actions:**
```json
{
  "stop_simulation": false,
  "send_notification": true,
  "log_event": true,
  "trigger_emergency_protocol": false
}
```

---

## 🤖 7. LLMRequest - Peticiones a LLMs

**Propósito:** Auditoría de costos, debugging y compliance.

**Campos clave:**
- `request_id` (UUID) - Identificador único
- `provider` - openai, anthropic, azure_openai, local
- `model_name` - gpt-4o-mini, claude-sonnet-4.5, etc.
- `prompt`, `response` - Contenido de la petición
- `total_tokens` - Tokens consumidos
- `cost_usd` - Costo estimado
- `latency_ms` - Tiempo de respuesta
- `validation_passed` - Si el JSON generado es válido

**Relaciones:**
- ← `users` (N:1) - Solicitado por
- → `models` (1:1) - Modelo generado (si tuvo éxito)

**Método `calculate_cost()`:**
Calcula costos según tarifas actuales:

| Provider | Model | Input ($/1M tokens) | Output ($/1M tokens) |
|----------|-------|---------------------|----------------------|
| OpenAI | GPT-4o-mini | $0.150 | $0.600 |
| OpenAI | GPT-4 | $30.00 | $60.00 |
| Anthropic | Claude Sonnet 4.5 | $3.00 | $15.00 |
| Anthropic | Claude Opus | $15.00 | $75.00 |

**Ejemplo de uso:**
```python
llm_request = LLMRequest(
    prompt="Create a water tank system...",
    provider="openai",
    model_name="gpt-4o-mini",
    prompt_tokens=250,
    completion_tokens=1500
)
cost = llm_request.calculate_cost()  # $0.000938
```

---

## 📝 8. AuditLog - Logs de Auditoría

**Propósito:** Trazabilidad completa del sistema para compliance y seguridad.

**Campos clave:**
- `event_type` - login, logout, model_created, simulation_started, attack_executed, etc.
- `severity` - debug, info, warning, error, critical
- `message` - Descripción del evento
- `details` (JSON) - Contexto adicional
- `ip_address`, `user_agent` - Info de la petición HTTP

**Relaciones:**
- ← `users` (N:1) - Usuario responsable (nullable para eventos del sistema)

**Método `to_cef()`:**
Convierte logs a formato CEF para Wazuh:

```python
log = AuditLog(
    event_type="login",
    severity="info",
    message="User logged in successfully",
    ip_address="192.168.1.100"
)
cef = log.to_cef()
# "CEF:0|TwinSec|Studio|1.0.0|123|login|5|src=192.168.1.100 msg=User logged in successfully"
```

**Eventos típicos:**
- `login`, `logout`, `failed_login` - Autenticación
- `model_created`, `model_updated`, `model_deleted` - CRUD modelos
- `simulation_started`, `simulation_stopped`, `simulation_failed` - Simulaciones
- `attack_executed`, `attack_failed` - Ataques
- `ids_alert_generated`, `ids_alert_investigated` - IDS
- `threshold_violated` - Alarmas
- `config_changed` - Cambios de configuración

---

## 🔄 Flujos de Datos Completos

### Flujo 1: Generación de Modelo con LLM

```
1. Usuario ingresa prompt
   ↓
2. Se crea LLMRequest (status=pending)
   ↓
3. Se llama a OpenAI/Anthropic
   ↓
4. Se recibe JSON del modelo
   ↓
5. Se valida contra twinsec_model_v1.json
   ↓
6. Si válido:
   - Se crea Model
   - Se actualiza LLMRequest (success=True, model_id=X)
   - Se crea AuditLog (event_type=model_created)
   ↓
7. Si inválido:
   - Se actualiza LLMRequest (success=False, validation_errors=[...])
   - Se crea AuditLog (event_type=model_generation_failed)
```

### Flujo 2: Ejecución de Simulación con Ataque

```
1. Usuario inicia simulación
   ↓
2. Se crea SimulationRun (status=pending)
   ↓
3. Se crean Attacks (status=armed)
   ↓
4. Se carga Model desde DB
   ↓
5. Se crean Thresholds del modelo
   ↓
6. SimulationRun.status = running
   ↓
7. Engine ejecuta simulación:
   ├─ En trigger_time:
   │  └─ Attack.status = active
   ├─ En cada timestep:
   │  ├─ Se verifica cada Threshold
   │  │  └─ Si violado: AuditLog (threshold_violated)
   │  ├─ Autoencoder detecta anomalía
   │  │  └─ Se crea IDSAlert
   │  └─ Se envía telemetría por WebSocket
   ├─ Al finalizar ataque:
   │  └─ Attack.status = completed
   └─ Al terminar simulación:
      └─ SimulationRun.status = completed
```

### Flujo 3: Investigación de Alerta IDS

```
1. Se genera IDSAlert (status=new)
   ↓
2. Usuario revisa alerta en HMI
   ↓
3. IDSAlert.status = investigating
   ↓
4. Usuario correlaciona con Attack (si existe)
   ↓
5. Usuario marca:
   - true_positive = True (si era ataque real)
   - false_positive = True (si era benigno)
   ↓
6. IDSAlert.status = resolved
   ↓
7. Se crea AuditLog (ids_alert_investigated)
   ↓
8. Métricas del IDS se actualizan
```

---

## 📈 Consultas SQL Típicas

### Top 10 Usuarios Más Activos
```sql
SELECT u.username, COUNT(sr.id) as simulations
FROM users u
JOIN simulation_runs sr ON u.id = sr.user_id
GROUP BY u.id
ORDER BY simulations DESC
LIMIT 10;
```

### Efectividad del IDS (Precision & Recall)
```sql
SELECT 
  COUNT(*) FILTER (WHERE true_positive = TRUE) as TP,
  COUNT(*) FILTER (WHERE false_positive = TRUE) as FP,
  COUNT(*) FILTER (WHERE true_positive = FALSE AND related_attack_id IS NOT NULL) as FN
FROM ids_alerts
WHERE simulation_run_id = 123;
```

### Costos Totales de LLM por Usuario
```sql
SELECT u.username, SUM(lr.cost_usd) as total_cost
FROM users u
JOIN llm_requests lr ON u.id = lr.user_id
WHERE lr.created_at >= NOW() - INTERVAL '30 days'
GROUP BY u.id
ORDER BY total_cost DESC;
```

### Ataques Más Comunes
```sql
SELECT attack_type, COUNT(*) as count
FROM attacks
GROUP BY attack_type
ORDER BY count DESC;
```

---

## 🎯 Índices de Rendimiento

Los siguientes índices están automáticamente creados por SQLAlchemy:

- `users.username`, `users.email` - LOGIN rápido
- `models.name`, `models.model_type` - BÚSQUEDA de modelos
- `simulation_runs.run_id`, `simulation_runs.status` - QUERIES de estado
- `attacks.attack_id`, `attacks.attack_type` - ANÁLISIS forense
- `ids_alerts.alert_id`, `ids_alerts.severity`, `ids_alerts.timestamp` - MONITORING IDS
- `thresholds.signal_name` - VERIFICACIÓN de umbrales
- `llm_requests.request_id`, `llm_requests.provider`, `llm_requests.created_at` - AUDITORÍA costos
- `audit_logs.event_type`, `audit_logs.timestamp` - BÚSQUEDA de eventos

---

## 🔒 Seguridad y Compliance

### PII (Personally Identifiable Information)
- `users.email`, `users.full_name` - **Encriptar en producción**
- `audit_logs.ip_address` - **Anonimizar después de 90 días**

### Retention Policies
- `audit_logs` - Retener 2 años, luego archivar
- `ids_alerts` - Retener 1 año, luego eliminar
- `llm_requests` - Retener 6 meses para auditoría de costos
- `simulation_runs` - Retener indefinidamente (datos científicos)

### Backup Strategy
- **Daily**: Incremental backup
- **Weekly**: Full backup
- **Monthly**: Archived to cold storage

---

**Última actualización:** 31 de octubre de 2025
