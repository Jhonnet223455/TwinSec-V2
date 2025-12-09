# 📚 Knowledge Base - Libros para RAG TwinSec

Esta carpeta contiene los libros y documentos técnicos que el sistema RAG utilizará para generar modelos de sistemas OT.

## 🎯 ¿Qué hace el RAG?

El sistema RAG (Retrieval-Augmented Generation) busca fragmentos relevantes de estos libros cuando generas un modelo:

```
Usuario → Prompt → RAG busca contexto → LLM + Contexto → Modelo JSON
```

**Ejemplo:**
- Prompt: *"Un tanque de agua con válvula PID"*
- RAG recupera: Ecuaciones de balance de masa, parámetros típicos de válvulas, diseño PID
- LLM genera: Modelo JSON completo con física realista

## 📚 Estructura Recomendada

```
knowledge_base/
├── control_systems/
│   ├── ogata_control_systems.pdf
│   ├── franklin_feedback_control.pdf
│   └── modern_control_systems.pdf
├── process_control/
│   ├── chemical_process_control.pdf
│   ├── water_treatment_systems.pdf
│   └── hvac_control.pdf
├── scada/
│   ├── scada_handbook.pdf
│   ├── industrial_automation.pdf
│   └── plc_programming.pdf
├── cybersecurity/
│   ├── ot_security_guide.pdf
│   ├── ics_attack_vectors.pdf
│   └── critical_infrastructure_protection.pdf
└── examples/
    ├── tank_systems_examples.pdf
    ├── power_systems_modeling.pdf
    └── water_distribution_networks.pdf
```

## 📖 Libros Recomendados

### Control de Sistemas
1. **"Modern Control Engineering" - Katsuhiko Ogata**
   - Fundamentos de sistemas de control
   - Función de transferencia
   - Espacio de estados

2. **"Feedback Control of Dynamic Systems" - Franklin, Powell, Emami-Naeini**
   - Control clásico y moderno
   - Diseño de controladores PID

3. **"Digital Control System Analysis and Design" - Charles L. Phillips**
   - Control digital
   - Discretización de sistemas

### Control de Procesos
1. **"Process Control: Modeling, Design, and Simulation" - B. Wayne Bequette**
   - Modelado de procesos químicos
   - Tanques, válvulas, intercambiadores

2. **"Chemical Process Control" - George Stephanopoulos**
   - Control avanzado de procesos
   - Control multivariable

### SCADA y OT
1. **"SCADA Handbook" - Stuart A. Boyer**
   - Arquitectura SCADA
   - Protocolos industriales (Modbus, DNP3)

2. **"Industrial Network Security" - Eric D. Knapp**
   - Seguridad en redes OT
   - Vectores de ataque

## 🔧 Formatos Soportados

- ✅ PDF (.pdf)
- ✅ Word (.docx)
- ✅ Text (.txt)
- ✅ Markdown (.md)
- ⏳ LaTeX (.tex) - Futuro

## 📝 Instrucciones de Uso

1. **Agregar libros:**
   ```bash
   # Copiar tus PDFs a esta carpeta
   cp /ruta/a/tu/libro.pdf Backend/knowledge_base/control_systems/
   ```

2. **Indexar documentos:**
   ```bash
   # El sistema indexará automáticamente al iniciar
   # O ejecutar manualmente:
   python Backend/scripts/index_knowledge_base.py
   ```

3. **Verificar indexación:**
   ```bash
   # Ver estadísticas de la base de conocimientos
   curl http://localhost:8000/api/v1/rag/stats
   ```

## 🔍 Cómo Funciona el RAG

```
Usuario ingresa prompt
    ↓
Embeddings del prompt (sentence-transformers)
    ↓
Búsqueda semántica en ChromaDB
    ↓
Top 5 fragmentos relevantes del knowledge base
    ↓
Prompt enriquecido = prompt original + contexto de libros
    ↓
LLM (GPT-4o-mini) genera el modelo JSON
    ↓
Validación con twinsec_model_v1.json
```

## 📊 Ejemplo de Prompt Enriquecido

**Prompt original del usuario:**
```
"Create a water tank system with 2 tanks and a pump"
```

**Contexto recuperado del knowledge base:**
```
[Extracto de "Process Control" - Bequette, pág. 145]
"A tank system can be modeled with the mass balance equation:
dh/dt = (Q_in - Q_out) / A
where h is the level, Q is flow rate, A is cross-sectional area..."

[Extracto de "SCADA Handbook" - Boyer, pág. 67]
"Tank level sensors typically use differential pressure transmitters
with 4-20mA output signal..."
```

**Prompt final al LLM:**
```
You are an expert in OT systems modeling. Use the following technical 
context to create a detailed water tank system:

CONTEXT:
{contexto recuperado}

USER REQUEST:
Create a water tank system with 2 tanks and a pump

Generate a JSON model following the twinsec_model_v1.json schema...
```

## ⚠️ Notas Importantes

1. **Copyright:** Asegúrate de tener derecho a usar los libros (uso académico/personal)
2. **Idioma:** El sistema soporta documentos en inglés y español
3. **Calidad:** PDFs con OCR de mala calidad pueden afectar la precisión
4. **Tamaño:** Archivos muy grandes (>100MB) pueden tardar en indexarse

## 🎯 Mejores Prácticas

- Nombra los archivos descriptivamente: `ogata_control_ch5_tank_systems.pdf`
- Organiza por categorías (carpetas)
- Incluye ejemplos prácticos y casos de estudio
- Agrega papers académicos de IEEE/ACM para casos avanzados

---

**Última actualización:** Noviembre 6, 2025
