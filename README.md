# TwinSec Studio

**OT Cybersecurity Testing Platform with LLM-Powered Model Generation**

TwinSec Studio permite que usuarios describan sistemas dinámicos en lenguaje natural y un LLM genere automáticamente modelos estructurados listos para simulación, visualización y pruebas de ciberseguridad (ataques FDI/DoS).

## 🏗️ Arquitectura del Proyecto

```
TwinSec V2/
├── Backend/          # Servicios backend (FastAPI + Python)
│   ├── api/          # REST API y WebSocket
│   ├── engine/       # Motor de simulación
│   ├── connectors/   # Adaptadores LLM
│   ├── schemas/      # Contratos de datos compartidos
│   └── scripts/      # Scripts de utilidad
└── frontend/         # Interfaz de usuario (React + TypeScript)
    └── src/
        ├── components/
        ├── pages/
        └── hooks/
```

## 🚀 Quick Start

### Prerrequisitos

- **Python 3.11+**
- **Node.js 18+** (o Bun)
- **PostgreSQL 14+**
- **Clave API de OpenAI** (o proveedor LLM alternativo)

### 1. Backend Setup

```bash
cd Backend

# Crear entorno virtual
python -m venv venv
.\venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
cd api
pip install -r requirements.txt

# Configurar variables de entorno
copy .env.example .env
# Editar .env con tus credenciales

# Inicializar base de datos
python ../scripts/init_db.py

# Ejecutar servidor
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**API disponible en:** http://localhost:8000  
**Documentación:** http://localhost:8000/docs

### 2. Frontend Setup

```bash
cd frontend

# Instalar dependencias
npm install
# o: bun install

# Ejecutar en modo desarrollo
npm run dev
# o: bun dev
```

**Frontend disponible en:** http://localhost:5173

## 📋 Funcionalidades Principales

### ✅ Fase Actual (MVP)
- ✅ Arquitectura base del proyecto
- 🚧 Generación de modelos vía LLM (en desarrollo)
- 🚧 Sistema de autenticación JWT
- 🚧 Motor de simulación con plugins
- 🚧 WebSocket para telemetría en tiempo real

### 🔜 Próximas Fases
- [ ] Autenticación social (Google, LinkedIn, Facebook)
- [ ] HMI interactivo con modificación de parámetros en tiempo real
- [ ] Sistema de ataques (FDI, DoS)
- [ ] IDS con Autoencoder + SHAP
- [ ] Exportación de logs para Wazuh
- [ ] Visualización 2D/3D de sistemas

## 🛠️ Stack Tecnológico

### Backend
- **Framework:** FastAPI
- **Base de datos:** PostgreSQL + SQLAlchemy
- **LLM:** OpenAI GPT-4, Azure, Anthropic, o modelos locales
- **Simulación:** NumPy, SciPy
- **WebSocket:** FastAPI WebSockets

### Frontend
- **Framework:** React 18 + TypeScript
- **Build tool:** Vite
- **Styling:** Tailwind CSS
- **Components:** Shadcn/ui
- **Charts:** Recharts / Plotly
- **State:** React Query

## 📁 Estructura Detallada

### Backend

```
Backend/
├── api/
│   ├── app/
│   │   ├── main.py              # Punto de entrada FastAPI
│   │   ├── config.py            # Configuración
│   │   ├── dependencies.py      # Dependencias compartidas
│   │   ├── schemas/             # Pydantic schemas (validación API)
│   │   ├── models/              # SQLAlchemy ORM models (DB)
│   │   ├── db/                  # Configuración de base de datos
│   │   ├── crud/                # Operaciones CRUD
│   │   ├── routers/             # Endpoints de la API
│   │   ├── services/            # Lógica de negocio
│   │   └── core/                # Security, logging, exceptions
│   ├── tests/
│   └── requirements.txt
├── engine/
│   ├── engine/
│   │   ├── core/                # Simulator, componentes base
│   │   ├── plugins/             # Plugins por tipo de sistema
│   │   ├── attacks/             # Módulos de ataque (FDI, DoS)
│   │   └── utils/
│   └── requirements.txt
├── connectors/
│   └── llm/                     # Adaptadores para LLMs
├── schemas/                     # JSON Schemas compartidos
└── scripts/                     # Scripts de inicialización
```

### Frontend

```
frontend/
├── src/
│   ├── pages/                   # Páginas principales
│   │   ├── Index.tsx
│   │   ├── Login.tsx
│   │   ├── Dashboard.tsx
│   │   ├── ModelEditor.tsx
│   │   └── SimulationView.tsx
│   ├── components/
│   │   ├── ui/                  # Componentes Shadcn
│   │   ├── Header.tsx
│   │   ├── PromptEditor.tsx
│   │   ├── ModelViewer.tsx
│   │   ├── HMI/                 # Widgets de interfaz HMI
│   │   └── Charts/              # Gráficas en tiempo real
│   ├── hooks/                   # Custom hooks
│   ├── lib/                     # Utilidades
│   │   ├── api.ts               # Cliente HTTP
│   │   ├── websocket.ts         # Cliente WebSocket
│   │   └── auth.ts              # Helpers de autenticación
│   └── types/                   # TypeScript types
```

## 🔐 Seguridad

- **Autenticación:** JWT con refresh tokens
- **OAuth:** Google, Facebook, LinkedIn (próximamente)
- **Rate Limiting:** Protección contra abuso
- **Validación:** Pydantic para entrada de datos
- **Secrets:** Variables de entorno (.env)
- **CORS:** Configurado para dominios permitidos



## 👥 Autores

- **Equipo TwinSec Studio**

---

**Estado del Proyecto:** 🚧 En desarrollo activo (MVP)
