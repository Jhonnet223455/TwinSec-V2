# 📚 Guía: RAG Knowledge Base y Schema TwinSec

## 🎯 ¿Qué es el Schema `twinsec_model_v1.json`?

### Propósito Principal

El schema **`twinsec_model_v1.json`** es un **contrato JSON Schema** que define la **estructura exacta** que el LLM debe generar cuando crea un modelo de sistema OT. Es como un "molde" o "plantilla" que garantiza que todos los modelos generados:

1. ✅ **Tienen la estructura correcta** (campos obligatorios presentes)
2. ✅ **Usan tipos de datos válidos** (números donde deben ser números, strings donde deben ser strings)
3. ✅ **Son ejecutables por el motor de simulación** (formato compatible)
4. ✅ **Incluyen toda la información necesaria** (componentes, conexiones, solver, HMI, etc.)

### ¿Cómo se usa?

```
┌─────────────┐      ┌──────────────┐      ┌─────────────────┐
│   Usuario   │─────>│  LLM+RAG     │─────>│  Modelo JSON    │
│   Prompt    │      │  Service     │      │  (validado)     │
└─────────────┘      └──────────────┘      └─────────────────┘
                            │                        │
                            │                        │
                            v                        v
                     ┌──────────────┐      ┌─────────────────┐
                     │  RAG Context │      │  JSON Schema    │
                     │  (libros)    │      │  Validator      │
                     └──────────────┘      └─────────────────┘
```

**Flujo:**
1. Usuario envía prompt: *"Un tanque de agua con válvula de entrada"*
2. RAG recupera contexto de libros sobre tanques, ecuaciones diferenciales, control
3. LLM genera JSON siguiendo el schema `twinsec_model_v1.json`
4. Se valida contra el schema (TODO: implementar validación completa)
5. Si es válido, se guarda en BD y puede ejecutarse

### Estructura del Schema

El schema define que cada modelo DEBE tener:

```json
{
  "name": "tank_model_001",          // Identificador único
  "type": "tank",                     // Tipo de sistema
  "version": "1.0",                   // Versión del schema
  "description": "...",               // Descripción legible
  
  "solver": {                         // Configuración del solver numérico
    "method": "euler",                // euler, rk4, odeint
    "dt": 0.1,                        // Paso de tiempo (segundos)
    "max_duration": 300               // Duración máxima (segundos)
  },
  
  "components": [                     // Lista de componentes del sistema
    {
      "id": "tank",                   // ID único del componente
      "kind": "water_tank",           // Tipo de componente (plugin)
      "params": {                     // Parámetros físicos
        "area": 10.0,                 // m²
        "max_level": 5.0              // m
      },
      "initial_state": {              // Estado inicial
        "level": 2.5                  // m
      }
    },
    {
      "id": "inlet_valve",
      "kind": "valve",
      "params": {
        "max_flow": 0.5               // m³/s
      }
    }
  ],
  
  "connections": [                    // Conexiones entre componentes
    {
      "from": "inlet_valve.flow",    // Señal fuente
      "to": "tank.inflow",           // Señal destino
      "gain": 1.0                     // Factor de escala
    }
  ],
  
  "signals": {                        // Señales para monitoreo
    "outputs": [
      "tank.level",
      "tank.volume"
    ]
  },
  
  "hmi": {                            // Interfaz HMI
    "widgets": [
      {
        "kind": "tank_view",          // Tipo de widget
        "bind": "tank.level",         // Señal a mostrar
        "label": "Nivel del Tanque",
        "unit": "m"
      }
    ]
  },
  
  "attacks": {                        // Ataques sugeridos
    "fdi": [
      {
        "target": "tank.level_sensor",
        "mode": "constant",
        "value": 8.5
      }
    ]
  }
}
```

### Ventajas del Schema

1. **Consistencia**: Todos los modelos tienen la misma estructura
2. **Validación**: Se pueden detectar errores antes de ejecutar
3. **Documentación**: El schema ES la documentación del formato
4. **Interoperabilidad**: Otros sistemas pueden entender el formato
5. **Evolución**: Puedes versionar el schema (v1, v2, v3...)

---

## 📚 Libros Actuales en el RAG

**Ubicación:** `Backend/knowledge_base/`

### 1. Modern Control Engineering 5th Ed.
- **Autor:** Katsuhiko Ogata
- **Temas:**
  - Teoría de control clásica
  - Función de transferencia
  - Análisis de estabilidad
  - Diseño de controladores PID
  - Control en espacio de estados
  - Control digital

### 2. Feedback Control of Dynamic Systems 8th Ed.
- **Autores:** Franklin, Powell, Emami-Naeini
- **Temas:**
  - Modelado de sistemas dinámicos
  - Respuesta temporal
  - Análisis de frecuencia
  - Diseño de compensadores
  - Control moderno (LQR, Kalman Filter)
  - Sistemas no lineales

---

## 📖 Libros Recomendados para Ampliar el RAG

### 🎯 PRIORIDAD ALTA (Sistemas OT y Control)

#### 1. **Process Control: Modeling, Design, and Simulation**
- **Autor:** B. Wayne Bequette
- **¿Por qué?** 
  - Enfocado en procesos industriales (tanques, reactores, intercambiadores)
  - Ecuaciones diferenciales de procesos químicos
  - Control PID en contexto industrial
  - Ejemplos prácticos de plantas

#### 2. **Chemical Process Control: An Introduction to Theory and Practice**
- **Autor:** George Stephanopoulos
- **¿Por qué?**
  - Control de procesos químicos (válvulas, bombas, tanques)
  - Modelado de sistemas de flujo
  - Dinámicas de nivel, presión, temperatura
  - Casos de estudio industriales

#### 3. **Industrial Control Systems: Mathematical and Statistical Models**
- **Autor:** Adedeji B. Badiru
- **¿Por qué?**
  - Sistemas SCADA y DCS
  - Modelado de actuadores y sensores
  - Arquitecturas de control industrial
  - Seguridad en sistemas críticos


---

### ⚡ PRIORIDAD MEDIA (Energía y Smart Grids)

#### 5. **Power System Analysis and Design**
- **Autor:** J. Duncan Glover, Mulukutla S. Sarma
- **¿Por qué?**
  - Modelado de microgrids DC/AC
  - Generadores, baterías, inversores
  - Flujo de potencia
  - Estabilidad de red


#### 7. **Smart Grid: Fundamentals of Design and Analysis**
- **Autor:** James Momoh
- **¿Por qué?**
  - Arquitectura de smart grids
  - Comunicación y ciberseguridad
  - Demand response
  - Gestión distribuida

---

### 🚁 PRIORIDAD MEDIA (Drones y Robótica)

#### 8. **Small Unmanned Aircraft: Theory and Practice**
- **Autor:** Randal W. Beard, Timothy W. McLain
- **¿Por qué?**
  - Dinámica de drones (cuadricópteros, ala fija)
  - Control de vuelo (PID, LQR, MPC)
  - Navegación y path planning
  - Modelos no lineales


---

### 🏢 PRIORIDAD BAJA (HVAC y Edificios)

#### 10. **HVAC Control Systems: Optimization and Energy Efficiency**
- **Autor:** Hongye Su
- **¿Por qué?**
  - Control de temperatura y humedad
  - Sistemas de ventilación
  - Optimización energética
  - Building automation

#### 11. **Building Automation: Communication Systems with EIB/KNX, LON and BACnet**
- **Autor:** Hermann Merz
- **¿Por qué?**
  - Protocolos industriales
  - Arquitecturas de control
  - Integración de sistemas
  - Monitoreo y alarmas

---

### 🛡️ PRIORIDAD ALTA (Ciberseguridad OT)

#### 12. **Industrial Network Security: Securing Critical Infrastructure Networks**
- **Autor:** Eric D. Knapp, Joel Thomas Langill
- **¿Por qué?**
  - Ataques a sistemas OT (Stuxnet, etc.)
  - Vectores de ataque (MITM, replay, DOS)
  - IDS/IPS para SCADA
  - Frameworks de seguridad (ISA/IEC 62443)

#### 13. **Cybersecurity for Industrial Control Systems: SCADA, DCS, PLC, HMI, and SIS**
- **Autor:** Tyson Macaulay, Bryan Singer
- **¿Por qué?**
  - Amenazas específicas de OT
  - Casos de estudio de ataques reales
  - Defensa en profundidad
  - Detección de anomalías

#### 14. **Applied Cyber-Physical Systems**
- **Autor:** Kyoung-Dae Kim
- **¿Por qué?**
  - Modelado de ataques en CPS
  - Simulación de cyber-attacks
  - Resiliencia de sistemas críticos
  - Control bajo ataque

---

### 📊 PRIORIDAD BAJA (Data Science e IDS)

#### 15. **Machine Learning for Intrusion Detection**
- **Autor:** Mostaque Hossain
- **¿Por qué?**
  - Algoritmos de detección (KNN, SVM, Random Forest)
  - Feature engineering para IDS
  - Detección de anomalías
  - Datasets (NSL-KDD, etc.)

#### 16. **Time Series Analysis and Its Applications**
- **Autor:** Robert H. Shumway, David S. Stoffer
- **¿Por qué?**
  - Análisis de señales temporales
  - Modelos ARIMA, Kalman Filters
  - Detección de outliers
  - Forecasting

---

## 🎓 Libros Técnicos Especializados

### 17. **Modeling and Simulation of Dynamic Systems**
- **Autor:** Robert L. Woods, Kent L. Lawrence
- **¿Por qué?**
  - Métodos numéricos (Euler, RK4, ODE solvers)
  - Modelado multifísico
  - Simulación de eventos discretos
  - Validación de modelos

### 18. **Nonlinear Control Systems**
- **Autor:** Alberto Isidori
- **¿Por qué?**
  - Control de sistemas no lineales
  - Lyapunov stability
  - Feedback linearization
  - Sliding mode control

---

## 📥 Cómo Agregar Libros al RAG

### 1. Descargar libros en formato PDF

Formatos soportados:
- ✅ PDF (recomendado)
- ✅ DOCX
- ✅ TXT

### 2. Colocar en `Backend/knowledge_base/`

```bash
Backend/
  knowledge_base/
    ├── Control-Modern Control Engineering 5th Ed.pdf
    ├── Feedback Control of Dynamic Systems 8th Ed.pdf
    ├── Process Control - Bequette.pdf          # NUEVO
    ├── Industrial Control Systems.pdf          # NUEVO
    ├── Microgrid Control.pdf                   # NUEVO
    ├── Industrial Network Security.pdf         # NUEVO
    └── README.md
```

### 3. Reiniciar el servidor

El servicio RAG carga los libros al iniciar:

```python
# Backend/api/app/services/rag_service.py
class RAGService:
    def __init__(self):
        self.knowledge_base_path = Path(__file__).parent.parent.parent / "knowledge_base"
        self._load_documents()  # Lee todos los PDFs/DOCX/TXT
        self._create_vectorstore()  # Crea embeddings con ChromaDB
```

### 4. Verificar que se cargaron

Busca en los logs del servidor:

```
INFO: ✅ Documentos cargados: 5 archivos, 3248 fragmentos
INFO: ✅ Vectorstore ChromaDB inicializado
```

---

## 🔍 Cómo el RAG Usa los Libros

### Proceso de Generación

1. **Usuario envía prompt:**
   ```
   "Un tanque de agua con válvula PID"
   ```

2. **RAG busca contexto relevante:**
   - Query: `"tank system water valve PID differential equations parameters"`
   - Recupera 5 fragmentos más relevantes de los libros
   - Fragmentos contienen: ecuaciones, parámetros típicos, ejemplos

3. **Se enriquece el prompt:**
   ```
   CONTEXT FROM TEXTBOOKS:
   [Fragmento 1: Ecuación de balance de masa en tanques]
   [Fragmento 2: Parámetros típicos de válvulas industriales]
   [Fragmento 3: Diseño de controladores PID para nivel]
   
   USER REQUEST:
   Create a tank system with the following specifications:
   A water tank with inlet valve, outlet valve, and level sensor...
   ```

4. **LLM genera JSON siguiendo el schema:**
   ```json
   {
     "name": "water_tank_pid",
     "components": [
       {
         "id": "tank",
         "kind": "water_tank",
         "params": {
           "area": 10.0,      // Sacado del contexto RAG
           "max_level": 5.0   // Valor típico de los libros
         }
       }
     ]
   }
   ```

---

## 🎯 Estrategia Recomendada de Libros

### Para empezar (3-5 libros):

1. ✅ **Modern Control Engineering** (ya tienes)
2. ✅ **Feedback Control** (ya tienes)
3. 🆕 **Process Control** (Bequette) - Para sistemas industriales
4. 🆕 **Industrial Network Security** - Para ataques y defensa
5. 🆕 **Microgrid Control** - Si quieres generar modelos de energía

### Para cobertura completa (10-15 libros):

Agregar los de **PRIORIDAD ALTA** + **PRIORIDAD MEDIA**

---

## 💡 Tips

### Nombrar archivos correctamente

```
✅ BIEN:
Process_Control_Bequette.pdf
Industrial_Network_Security_Knapp.pdf

❌ EVITAR:
libro 1.pdf
book (1) copy.pdf
[2024] latest version final FINAL.pdf
```

### Calidad de los PDFs

- ✅ **Con OCR** (texto seleccionable)
- ❌ **Imágenes escaneadas** (no se puede extraer texto)

### Tamaño del RAG

- 2-3 libros: Básico (~500MB, ~1000 fragmentos)
- 5-7 libros: Bueno (~1.5GB, ~3000 fragmentos)
- 10-15 libros: Excelente (~3GB, ~6000 fragmentos)
- +20 libros: Overkill (puede ser lento)

---

## 🧪 Probar el RAG

### Ver fragmentos recuperados

```python
from app.services.rag_service import get_rag_service

rag = get_rag_service()
results = rag.retrieve_context(
    query="water tank level control PID",
    top_k=5,
    min_relevance_score=0.5
)

for doc in results:
    print(f"Score: {doc['score']:.3f}")
    print(f"Source: {doc['source']}")
    print(f"Text: {doc['text'][:200]}...")
    print()
```

---

## 📌 Resumen

| Componente | Propósito | Ubicación |
|------------|-----------|-----------|
| **Schema JSON** | Define estructura del modelo generado | `Backend/schemas/twinsec_model_v1.json` |
| **Libros RAG** | Contexto técnico para el LLM | `Backend/knowledge_base/*.pdf` |
| **RAG Service** | Busca fragmentos relevantes | `Backend/api/app/services/rag_service.py` |
| **LLM Service** | Orquesta RAG + LLM + validación | `Backend/api/app/services/llm_service.py` |

---

## 🎓 Próximos Pasos

1. ✅ Descargar 3-5 libros prioritarios
2. ✅ Colocarlos en `Backend/knowledge_base/`
3. ✅ Reiniciar servidor
4. ✅ Probar generación con `/models/generate`
5. ✅ Ver logs para confirmar que se cargaron
6. 🎯 Experimentar con diferentes prompts
7. 🎯 Implementar validación completa contra schema

---

## 📚 Links de Interés

- **JSON Schema Validator:** https://www.jsonschemavalidator.net/
- **ChromaDB Docs:** https://docs.trychroma.com/
- **LangChain RAG:** https://python.langchain.com/docs/use_cases/question_answering/
- **OpenAI JSON Mode:** https://platform.openai.com/docs/guides/structured-outputs
