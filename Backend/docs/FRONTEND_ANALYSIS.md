# Análisis del Frontend - TwinSec Studio

Este documento analiza la estructura actual del frontend y proporciona recomendaciones para la integración con el backend FastAPI.

---

## 📋 Estado Actual del Frontend

### ✅ Tecnologías Detectadas

- **Framework**: React 18.3.1 con TypeScript
- **Build Tool**: Vite 5.4.19
- **Router**: React Router DOM 6.30.1
- **UI Components**: Shadcn/ui (Radix UI + Tailwind CSS)
- **Forms**: React Hook Form 7.61.1 + Zod 3.25.76
- **State Management**: TanStack React Query 5.83.0
- **Authentication**: Supabase (⚠️ **NECESITA MIGRACIÓN**)

### 🔴 Problemas Identificados

#### 1. **Integración con Supabase (CONFLICTO CRÍTICO)**

**Archivos afectados:**
- `src/integrations/supabase/client.ts` - Cliente Supabase
- `src/hooks/useAuth.tsx` - Hook de autenticación usando Supabase
- `src/pages/Auth.tsx` - Página de login/registro con Supabase OAuth

**Problema:**
El frontend actualmente está configurado para usar **Supabase** como backend de autenticación, pero tu backend es **FastAPI con JWT y PostgreSQL**.

**Conflictos específicos:**
```typescript
// ACTUAL (Supabase)
const { error } = await supabase.auth.signInWithPassword({
  email,
  password,
});

// NECESARIO (FastAPI)
const response = await fetch('http://localhost:8000/api/v1/auth/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ username: email, password })
});
```

**OAuth Providers:**
- **Actual**: `useAuth.tsx` soporta `'google' | 'facebook' | 'github'` ✅
- **Backend**: Configurado para Google, Facebook y GitHub ✅
- **Integración**: Supabase maneja el flujo OAuth, pero necesitas FastAPI para esto

#### 2. **Falta de Cliente API para FastAPI**

**Problema:**
No existe un cliente HTTP centralizado para comunicarse con tu backend FastAPI.

**Solución implementada:**
He creado `src/lib/api.ts` con:
- Cliente HTTP con manejo automático de JWT
- Endpoints para auth, models, simulations, logs
- Manejo de refresh tokens
- Interceptores de errores

#### 3. **Falta de Cliente WebSocket**

**Problema:**
No hay implementación de WebSocket para telemetría en tiempo real.

**Solución implementada:**
He creado `src/lib/websocket.ts` con:
- Cliente WebSocket para simulaciones
- Manejo de reconexión automática
- Tipos TypeScript para mensajes de telemetría

---

## 🔄 Plan de Migración de Supabase a FastAPI

### Fase 1: Crear nuevo hook `useAuthFastAPI` (Recomendado)

Crear un nuevo hook de autenticación que use FastAPI en lugar de Supabase:

**Ventajas:**
- Mantiene el código actual funcionando durante la migración
- Permite testing incremental
- Menor riesgo de bugs

**Pasos:**
1. Crear `src/hooks/useAuthFastAPI.tsx`
2. Implementar las mismas funciones que `useAuth` pero usando `api.ts`
3. Actualizar `App.tsx` para usar `AuthProviderFastAPI`
4. Actualizar páginas para usar el nuevo hook
5. Eliminar Supabase cuando todo funcione

### Fase 2: Migrar OAuth Social Login

**Backend FastAPI necesita implementar:**

```python
# api/app/routers/oauth.py (PENDIENTE DE CREAR)

@router.get("/auth/google")
async def google_login():
    # Redirigir a Google OAuth
    ...

@router.get("/auth/google/callback")
async def google_callback(code: str):
    # Obtener token de Google
    # Crear/buscar usuario en PostgreSQL
    # Generar JWT token
    # Redirigir al frontend con token
    ...

# Similar para Facebook y GitHub
```

**Frontend necesita:**
```typescript
// En useAuthFastAPI.tsx
const signInWithOAuth = async (provider: 'google' | 'facebook' | 'github') => {
  // Redirigir a http://localhost:8000/api/v1/auth/{provider}
  window.location.href = `${API_URL}/auth/${provider}`;
};
```

---

## 📂 Estructura del Frontend Actual

```
frontend/src/
├── components/
│   ├── Header.tsx                    ✅ Usa useAuth (necesita migración)
│   ├── ModelViewer.tsx               ✅ Componente para visualizar modelos
│   ├── PromptEditor.tsx              ✅ Editor de prompts para LLM
│   ├── SimulationDashboard.tsx       ✅ Dashboard de simulación
│   └── ui/                           ✅ Shadcn/ui components (57 archivos)
├── hooks/
│   ├── useAuth.tsx                   🔴 USA SUPABASE (migrar)
│   ├── use-mobile.tsx                ✅ Hook optimizado para mobile
│   └── use-toast.ts                  ✅ Hook para notificaciones
├── integrations/
│   └── supabase/
│       ├── client.ts                 🔴 ELIMINAR después de migración
│       └── types.ts                  🔴 ELIMINAR después de migración
├── lib/
│   ├── utils.ts                      ✅ Utilidades de Tailwind
│   ├── api.ts                        ✅ NUEVO - Cliente API FastAPI
│   └── websocket.ts                  ✅ NUEVO - Cliente WebSocket
├── pages/
│   ├── Index.tsx                     ✅ Página principal (usa useAuth)
│   ├── Auth.tsx                      🔴 Página de login (migrar)
│   ├── ResetPassword.tsx             🔴 Reset password (migrar)
│   └── NotFound.tsx                  ✅ Página 404
├── App.tsx                           🔴 Usa AuthProvider de Supabase
└── main.tsx                          ✅ Entry point
```

---

## 🔧 Archivos que Necesitan Modificación

### 1. `src/hooks/useAuthFastAPI.tsx` (CREAR)

```typescript
import { useState, useEffect, createContext, useContext } from 'react';
import { authAPI } from '@/lib/api';

interface User {
  id: number;
  email: string;
  username: string;
  full_name?: string;
}

interface AuthContextType {
  user: User | null;
  loading: boolean;
  signUp: (email: string, password: string, fullName?: string) => Promise<void>;
  signIn: (email: string, password: string) => Promise<void>;
  signInWithOAuth: (provider: 'google' | 'facebook' | 'github') => Promise<void>;
  signOut: () => void;
}

export const AuthProviderFastAPI = ({ children }) => {
  // Implementación similar a useAuth pero usando api.ts
};
```

### 2. `src/pages/Auth.tsx` (MODIFICAR)

**Cambios necesarios:**
```typescript
// ANTES
import { useAuth } from '@/hooks/useAuth';
const { signIn, signUp, signInWithOAuth } = useAuth();

// DESPUÉS
import { useAuth } from '@/hooks/useAuthFastAPI';
const { signIn, signUp, signInWithOAuth } = useAuth();
```

### 3. `src/App.tsx` (MODIFICAR)

```typescript
// ANTES
import { AuthProvider } from '@/hooks/useAuth';

// DESPUÉS
import { AuthProvider } from '@/hooks/useAuthFastAPI';
```

### 4. `src/components/Header.tsx` (MODIFICAR)

Ya usa `useAuth`, solo necesita que apunte al nuevo hook.

### 5. `src/pages/Index.tsx` (MODIFICAR)

Ya usa `useAuth`, solo necesita que apunte al nuevo hook.

---

## 🚀 Pasos para Integración Completa

### Paso 1: Configurar Variables de Entorno

Crear `frontend/.env`:
```env
VITE_API_BASE_URL=http://localhost:8000
VITE_WS_BASE_URL=ws://localhost:8000
```

### Paso 2: Crear `useAuthFastAPI` Hook

Ver ejemplo arriba. Este hook debe:
1. ✅ Gestionar estado del usuario (id, email, username)
2. ✅ Llamar a `authAPI.login()` para login
3. ✅ Llamar a `authAPI.register()` para registro
4. ✅ Manejar OAuth redirects para Google/Facebook/GitHub
5. ✅ Implementar auto-refresh de tokens
6. ✅ Persistir sesión en localStorage

### Paso 3: Actualizar Componentes

```typescript
// src/components/Header.tsx
import { useAuth } from '@/hooks/useAuthFastAPI';

export function Header() {
  const { user, signOut } = useAuth();
  // El resto del código es idéntico
}
```

### Paso 4: Implementar OAuth en Backend

Necesitas crear `api/app/routers/oauth.py` con:
- Endpoints para `/auth/google`, `/auth/facebook`, `/auth/github`
- Callbacks para recibir el código de autorización
- Lógica para crear/buscar usuario en PostgreSQL
- Generación de JWT y redirect al frontend

### Paso 5: Conectar Generación de Modelos

```typescript
// src/components/PromptEditor.tsx
import { modelsAPI } from '@/lib/api';

const handleGenerate = async (prompt: string) => {
  const model = await modelsAPI.generate(prompt, 'tank');
  setGeneratedModel(model);
};
```

### Paso 6: Conectar Simulaciones con WebSocket

```typescript
// src/components/SimulationDashboard.tsx
import { createSimulationWebSocket } from '@/lib/websocket';

const ws = createSimulationWebSocket(runId, accessToken);

ws.onMessage((message) => {
  if (message.type === 'telemetry') {
    updateChart(message.data);
  }
});
```

---

## ⚠️ Puntos Críticos de Atención

### 1. **CORS Configuration**

Tu backend FastAPI debe permitir:
```python
CORS_ORIGINS = ["http://localhost:5173", "http://localhost:3000"]
```

Ya está configurado en `config.py` ✅

### 2. **OAuth Redirect URIs**

Para Google OAuth Console:
```
http://localhost:8000/api/v1/auth/google/callback
```

Para Facebook App Dashboard:
```
http://localhost:8000/api/v1/auth/facebook/callback
```

Para GitHub OAuth Apps:
```
http://localhost:8000/api/v1/auth/github/callback
```

### 3. **Token Expiration Handling**

El cliente API debe:
1. Detectar 401 Unauthorized
2. Intentar refresh token automáticamente
3. Si falla, redirigir a login

```typescript
// Ya implementado en api.ts
if (response.status === 401) {
  await authAPI.refreshToken();
  // Reintentar petición original
}
```

### 4. **WebSocket Authentication**

El WebSocket debe recibir el JWT token:
```typescript
const ws = new WebSocket(`ws://localhost:8000/ws/telemetry/${runId}?token=${accessToken}`);
```

Backend debe validar el token en el handshake.

---

## 📊 Compatibilidad de OAuth Providers

| Provider | Frontend Actual | Backend Config | Implementado |
|----------|----------------|----------------|--------------|
| Google   | ✅ Soportado   | ✅ Configurado | 🔴 Pendiente |
| Facebook | ✅ Soportado   | ✅ Configurado | 🔴 Pendiente |
| GitHub   | ✅ Soportado   | ✅ Configurado | 🔴 Pendiente |

**Nota:** Los providers están configurados en ambos lados, pero falta la implementación de los endpoints OAuth en FastAPI.

---

## 🎯 Recomendaciones Finales

### 1. **Migración Incremental**

No elimines Supabase inmediatamente. Crea el nuevo sistema en paralelo:
- Renombra `useAuth` a `useAuthSupabase`
- Crea `useAuthFastAPI` nuevo
- Prueba con un flag de feature toggle
- Migra página por página

### 2. **Añadir Axios**

Considera usar Axios en lugar de fetch nativo:
```bash
npm install axios
```

Ventajas:
- Interceptores más fáciles
- Transformación automática de datos
- Mejor manejo de errores

### 3. **Añadir React Query para Cache**

Ya tienes `@tanstack/react-query` instalado. Úsalo para:
```typescript
const { data: models } = useQuery({
  queryKey: ['models'],
  queryFn: () => modelsAPI.list()
});
```

### 4. **Variables de Entorno por Ambiente**

Crear:
- `.env.development` → `http://localhost:8000`
- `.env.production` → `https://api.twinsec.com`

---

## 📝 Checklist de Migración

- [ ] Crear `frontend/.env` con API URLs
- [ ] Crear `src/hooks/useAuthFastAPI.tsx`
- [ ] Actualizar `src/App.tsx` para usar nuevo provider
- [ ] Actualizar `src/pages/Auth.tsx` para usar nuevo hook
- [ ] Actualizar `src/components/Header.tsx`
- [ ] Actualizar `src/pages/Index.tsx`
- [ ] Implementar endpoints OAuth en backend
- [ ] Configurar OAuth providers (Google, Facebook, GitHub)
- [ ] Probar flujo completo de login/registro
- [ ] Probar OAuth social login
- [ ] Conectar generación de modelos LLM
- [ ] Conectar simulaciones con WebSocket
- [ ] Eliminar `src/integrations/supabase/` cuando todo funcione
- [ ] Desinstalar `@supabase/supabase-js` del package.json

---

**Última actualización:** 31 de octubre de 2025

**Próximos pasos sugeridos:**
1. Implementar endpoints de autenticación en backend (`routers/auth.py`)
2. Crear `useAuthFastAPI` hook en frontend
3. Implementar OAuth en backend (`routers/oauth.py`)
