# Documentación: Core y Main.py

Esta documentación explica en detalle el contenido de la carpeta `core/` y el archivo `main.py` de la API de TwinSec Studio.

---

## 📁 Carpeta `core/` - Funcionalidades Centrales

La carpeta `core` contiene los módulos fundamentales que son utilizados en toda la aplicación. Son la "columna vertebral" del sistema.

---

## 1️⃣ `core/security.py` - Seguridad y Autenticación

Este módulo maneja todo lo relacionado con **seguridad, JWT tokens y hashing de contraseñas**.

### Componentes Clave:

#### a) Hashing de Contraseñas (Bcrypt)

```python
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
```

- Usa **bcrypt** para hacer hash de contraseñas (nunca se guardan en texto plano)
- `verify_password()`: Compara una contraseña ingresada con el hash guardado
- `get_password_hash()`: Convierte una contraseña en texto a su hash seguro

**¿Por qué es importante?**
- Si la base de datos es comprometida, los atacantes NO pueden ver las contraseñas
- Bcrypt es resistente a ataques de fuerza bruta (es intencionalmente lento)

#### b) Generación de JWT Tokens

```python
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
```

- Crea un **JSON Web Token (JWT)** firmado con una clave secreta
- El token contiene datos del usuario (ej. `sub: user_id`)
- Tiene un tiempo de expiración configurable (default: 30 minutos)
- Se usa para autenticar peticiones API sin enviar la contraseña en cada request

**¿Cómo funciona?**
1. Usuario hace login con username/password
2. API valida las credenciales
3. API genera un JWT y lo envía al cliente
4. Cliente guarda el JWT (localStorage/cookie)
5. En cada petición, el cliente envía el JWT en el header `Authorization: Bearer <token>`
6. API valida el JWT y permite o rechaza la petición

#### c) Decodificación de Tokens

```python
def decode_access_token(token: str) -> Optional[dict]:
```

- Decodifica y valida un JWT
- Verifica que no esté expirado
- Verifica que la firma sea válida (no ha sido modificado)
- Retorna los datos del usuario si es válido, `None` si no

#### d) Refresh Tokens

```python
def create_refresh_token(data: dict) -> str:
```

- Tokens de larga duración (7 días) para renovar access tokens
- Permiten mantener al usuario logueado sin pedirle credenciales constantemente
- Más seguros que access tokens permanentes

**Flujo de uso:**
```
1. Login → Recibe access_token (30 min) + refresh_token (7 días)
2. Después de 30 min, access_token expira
3. Cliente usa refresh_token para obtener un nuevo access_token
4. Después de 7 días, debe hacer login de nuevo
```

### Ejemplo de Uso en un Endpoint:

```python
from fastapi import Depends
from app.core.security import get_current_user

@app.get("/protected")
async def protected_route(current_user: dict = Depends(get_current_user)):
    return {"user_id": current_user["sub"]}
```

---

## 2️⃣ `core/exceptions.py` - Excepciones Personalizadas

Define **errores específicos del dominio** de TwinSec Studio.

### Jerarquía de Excepciones:

```
TwinSecException                    # Base para todas las excepciones
├── AuthenticationError             # Credenciales inválidas
├── AuthorizationError              # Sin permisos
├── ValidationError                 # Datos inválidos
├── ModelNotFoundError              # Modelo no existe
├── SimulationError                 # Error en simulación
└── LLMError                        # Error al llamar al LLM
```

### Helpers de HTTP Exceptions

El módulo incluye funciones helper para crear excepciones HTTP comunes:

```python
credentials_exception()      # 401 Unauthorized
not_found_exception()        # 404 Not Found
forbidden_exception()        # 403 Forbidden
conflict_exception()         # 409 Conflict
validation_exception()       # 422 Unprocessable Entity
internal_server_exception()  # 500 Internal Server Error
```

### ¿Por qué son útiles?

1. **Manejo de errores más específico**: Puedes capturar errores de simulación de manera diferente a errores de LLM
2. **Mejor logging**: Cada error puede tener su propio código y contexto
3. **Claridad del código**: `raise LLMError("OpenAI timeout")` es más descriptivo que `raise Exception()`

### Ejemplo de Uso:

```python
# En vez de:
if not user:
    raise Exception("User not found")

# Usamos:
if not user:
    raise ModelNotFoundError(f"User {user_id} not found")

# Esto se traduce automáticamente a un HTTP 404
```

---

## 3️⃣ `core/logging.py` - Logging Estructurado

Configura el sistema de logging de la aplicación con formato JSON estructurado.

### Características Clave:

#### a) Formato JSON Estructurado

```python
class JSONFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "module": record.module,
            ...
        }
        return json.dumps(log_data)
```

**Beneficios del formato JSON:**
- Fácil de parsear automáticamente
- Compatible con herramientas de análisis (ElasticSearch, Splunk, Wazuh)
- Permite búsquedas estructuradas (ej. "todos los errores del usuario X")

#### b) Niveles de Logging

| Nivel | Cuándo usarlo | Ejemplo |
|-------|---------------|---------|
| `DEBUG` | Información detallada para debugging | "Ejecutando query SQL: SELECT..." |
| `INFO` | Eventos normales de la aplicación | "Usuario jhon@example.com inició sesión" |
| `WARNING` | Algo inusual pero no crítico | "API de OpenAI respondió lento (2.5s)" |
| `ERROR` | Error que debe investigarse | "Fallo al conectar con PostgreSQL" |
| `CRITICAL` | Error grave que puede detener la app | "Disco lleno, no se pueden guardar logs" |

#### c) Contexto Adicional con `extra`

```python
logger.info("User logged in", extra={
    "user_id": user.id,
    "ip_address": request.client.host,
    "user_agent": request.headers.get("User-Agent")
})
```

Esto genera un log como:
```json
{
  "timestamp": "2025-10-27T10:30:00Z",
  "level": "INFO",
  "message": "User logged in",
  "user_id": "abc123",
  "ip_address": "192.168.1.100",
  "user_agent": "Mozilla/5.0..."
}
```

### Función Helper:

```python
logger = get_logger(__name__)
```

Uso en cualquier módulo:
```python
from app.core.logging import get_logger

logger = get_logger(__name__)

logger.info("Starting model generation")
logger.error("Failed to generate model", extra={"error": str(e)})
```

---

## 📄 `main.py` - Punto de Entrada de la API

Este es el archivo principal que crea y configura la aplicación FastAPI.

---

## Componentes del Archivo:

### 1️⃣ Importaciones

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
```

- `FastAPI`: La clase principal para crear la aplicación
- `CORSMiddleware`: Middleware para permitir peticiones cross-origin
- `asynccontextmanager`: Para manejar eventos de startup/shutdown

### 2️⃣ Lifespan Events

```python
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting TwinSec Studio API")
    # Aquí podrías conectar a la base de datos
    yield
    # Shutdown
    logger.info("Shutting down TwinSec Studio API")
    # Aquí podrías cerrar conexiones
```

**¿Para qué sirve?**
- **Startup**: Se ejecuta UNA VEZ al iniciar la aplicación
  - Ideal para: conectar a DB, cargar configuración, inicializar caches
- **Shutdown**: Se ejecuta UNA VEZ al cerrar la aplicación
  - Ideal para: cerrar conexiones DB, guardar estado, liberar recursos

### 3️⃣ Creación de la App FastAPI

```python
app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="OT Cybersecurity Testing Platform...",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)
```

**Parámetros importantes:**
- `title` y `version`: Aparecen en la documentación automática
- `docs_url="/docs"`: Swagger UI interactivo (http://localhost:8000/docs)
- `redoc_url="/redoc"`: Documentación alternativa más elegante
- `openapi_url`: Especificación OpenAPI en JSON (para generar clientes automáticamente)

### 4️⃣ Configuración de CORS

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### ¿Qué es CORS?

**CORS** (Cross-Origin Resource Sharing) es una política de seguridad de los navegadores.

**Problema:**
- Tu frontend (React) corre en `http://localhost:5173`
- Tu API (FastAPI) corre en `http://localhost:8000`
- Son **orígenes diferentes** (diferente puerto)
- Por seguridad, el navegador BLOQUEA estas peticiones por defecto

**Solución:**
- El servidor (API) debe explícitamente permitir peticiones del frontend
- Esto se hace con CORS

**Configuración actual:**
```python
allow_origins=["http://localhost:5173"]  # Permite SOLO este origen
allow_credentials=True                    # Permite enviar cookies/tokens
allow_methods=["*"]                       # Permite GET, POST, PUT, DELETE, etc.
allow_headers=["*"]                       # Permite Authorization, Content-Type, etc.
```

### 5️⃣ Endpoints Base

#### a) Root Endpoint (`/`)

```python
@app.get("/")
async def root():
    return {
        "name": settings.PROJECT_NAME,
        "version": settings.VERSION,
        "status": "running",
        "docs": "/docs"
    }
```

**Uso:**
- Verificar que la API está corriendo
- Obtener información básica
- Descubrir la URL de la documentación

#### b) Health Check (`/health`)

```python
@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-10-01T00:00:00Z"}
```

**Uso:**
- Monitoreo automático (Kubernetes, Docker Swarm)
- Verificar que la API responde
- Load balancers usan esto para saber si un servidor está vivo

### 6️⃣ Inclusión de Routers (Comentados)

```python
# app.include_router(auth.router, prefix=f"{settings.API_V1_STR}/auth", tags=["Authentication"])
# app.include_router(models.router, prefix=f"{settings.API_V1_STR}/models", tags=["Models"])
```

**Cuando se descomentan**, la estructura de rutas será:

```
/                              → Info de la API
/health                        → Health check
/docs                          → Swagger UI
/api/v1/auth/login             → Login
/api/v1/auth/register          → Registro
/api/v1/models/generate        → Generar modelo vía LLM
/api/v1/models/{id}            → Obtener modelo
/api/v1/runs/start             → Iniciar simulación
/api/v1/runs/{id}/stop         → Detener simulación
/ws/telemetry/{run_id}         → WebSocket para datos en tiempo real
```

**¿Por qué `prefix`?**
- Agrupa rutas relacionadas bajo un prefijo común
- Facilita el versionado de la API (`/api/v1`, `/api/v2`)

**¿Por qué `tags`?**
- Agrupa endpoints en la documentación automática
- Hace la documentación más organizada y fácil de navegar

### 7️⃣ Ejecución Directa

```python
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.API_DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
```

**Permite ejecutar la API con:**
```bash
python app/main.py
```

**Parámetros de Uvicorn:**
- `host="0.0.0.0"`: Acepta conexiones de cualquier IP (no solo localhost)
- `port=8000`: Puerto donde escucha la API
- `reload=True`: En desarrollo, recarga automáticamente al cambiar código
- `log_level="info"`: Nivel de logging del servidor

---

## 🔄 Flujo de una Petición HTTP

Cuando un cliente hace una petición a la API, este es el flujo completo:

```
1. Cliente → GET http://localhost:8000/api/v1/models/123
   
2. CORS Middleware
   ↓ Verifica que el origen (frontend) esté permitido
   
3. FastAPI Router
   ↓ Busca el endpoint correspondiente (/api/v1/models/{id})
   
4. Autenticación (si es necesario)
   ↓ get_current_user() extrae y valida el JWT del header
   
5. Validación de Datos
   ↓ Pydantic valida los parámetros y el body
   
6. Ejecución del Endpoint
   ↓ Se ejecuta la función del router
   ↓ Llama a servicios (LLM, DB, etc.)
   
7. Manejo de Errores
   ↓ Si hay errores, las excepciones personalizadas los manejan
   
8. Logging
   ↓ Se registra la petición (nivel INFO, WARNING, o ERROR)
   
9. Respuesta → Cliente
   ↓ JSON con los datos o error
```

---

## 🔐 Ejemplo Completo: Login y Petición Autenticada

### 1. Login

**Request:**
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "jhon",
  "password": "SecurePass123"
}
```

**Response:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 1800
}
```

### 2. Petición Autenticada

**Request:**
```http
GET /api/v1/models/abc123
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Proceso interno:**
1. CORS Middleware permite la petición
2. `get_current_user()` extrae el token del header
3. `decode_access_token()` valida el token
4. Si es válido, se ejecuta el endpoint
5. Si no es válido, se retorna 401 Unauthorized

---

## 📊 Resumen Visual

```
main.py (FastAPI App)
    │
    ├── CORS Middleware
    │   └── Permite frontend (localhost:5173) → backend (localhost:8000)
    │
    ├── Lifespan Events
    │   ├── Startup: conectar DB, inicializar caches
    │   └── Shutdown: cerrar conexiones, liberar recursos
    │
    ├── Routers (API Endpoints)
    │   ├── /api/v1/auth     → Login, registro, logout
    │   ├── /api/v1/models   → CRUD de modelos, generate via LLM
    │   ├── /api/v1/runs     → Iniciar/detener simulaciones
    │   ├── /api/v1/logs     → Exportar logs para SIEM
    │   └── /ws              → WebSocket para telemetría en tiempo real
    │
    └── Core Modules (Utilizados por todo el sistema)
        ├── security.py      → JWT, passwords, autenticación
        ├── exceptions.py    → Errores personalizados del dominio
        └── logging.py       → Logging estructurado en JSON
```

---

## 🎯 Mejores Prácticas Implementadas

### 1. Separación de Responsabilidades
- `core/` para funcionalidad transversal
- `routers/` para endpoints
- `services/` para lógica de negocio
- `models/` para base de datos

### 2. Configuración Centralizada
- Todas las configuraciones en `config.py`
- Cargadas desde variables de entorno (`.env`)
- Fácil de cambiar entre desarrollo/producción

### 3. Seguridad
- Contraseñas hasheadas con bcrypt
- JWT tokens con expiración
- CORS configurado correctamente
- Validación estricta de datos con Pydantic

### 4. Observabilidad
- Logging estructurado en JSON
- Logs con contexto adicional
- Health check endpoint para monitoreo

### 5. Documentación Automática
- Swagger UI en `/docs`
- ReDoc en `/redoc`
- OpenAPI spec disponible

---

## 🔗 Referencias

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [JWT.io](https://jwt.io/)
- [Bcrypt](https://en.wikipedia.org/wiki/Bcrypt)
- [CORS MDN](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
- [Pydantic](https://docs.pydantic.dev/)

---

**Última actualización:** 27 de octubre de 2025
