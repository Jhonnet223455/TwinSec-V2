# 🔄 Migración de Supabase a FastAPI JWT + OAuth

## ✅ Cambios Realizados

### 📂 Frontend

#### Archivos Modificados:

1. **`src/hooks/useAuth.tsx`** - ✅ Completamente reescrito
   - ❌ Eliminado: Dependencia de Supabase
   - ✅ Nuevo: Autenticación con backend FastAPI
   - ✅ Nuevo: Manejo de JWT tokens (access + refresh)
   - ✅ Nuevo: OAuth con Google y Facebook
   - ✅ Nuevo: Detección automática de tokens en URL (callback OAuth)

2. **`src/pages/Auth.tsx`** - ✅ Actualizado
   - ❌ Eliminado: Botón de GitHub (no implementado en backend todavía)
   - ✅ Actualizado: Campo "Full Name" opcional en registro
   - ✅ Actualizado: Iconos correctos (Google: Mail, Facebook: Facebook)
   - ✅ Actualizado: Solo Google y Facebook OAuth

3. **`.env`** - ✅ Actualizado
   - ❌ Eliminado: Variables de Supabase
   - ✅ Nuevo: `VITE_API_BASE_URL=http://localhost:8000`
   - ✅ Nuevo: `VITE_WS_BASE_URL=ws://localhost:8000`

4. **`.env.example`** - ✅ Creado
   - Template para otros desarrolladores

#### Archivos Eliminados:

- ❌ `src/integrations/supabase/` - Carpeta completa eliminada
- ❌ `src/integrations/supabase/client.ts`
- ❌ `src/integrations/supabase/types.ts`

#### Dependencias:

- ❌ Desinstalado: `@supabase/supabase-js`

---

### 📂 Backend

#### Archivos Creados:

1. **`app/routers/auth.py`** - ✅ Nuevo (540 líneas)
   - Endpoints de autenticación completos:
     - `POST /api/v1/auth/register` - Registro de usuario
     - `POST /api/v1/auth/login` - Login con email/password
     - `GET /api/v1/auth/me` - Información del usuario actual
     - `POST /api/v1/auth/refresh` - Refresh token
     - `POST /api/v1/auth/reset-password` - Reset de contraseña
     - `GET /api/v1/auth/oauth/google` - Iniciar OAuth Google
     - `GET /api/v1/auth/oauth/google/callback` - Callback Google
     - `GET /api/v1/auth/oauth/facebook` - Iniciar OAuth Facebook
     - `GET /api/v1/auth/oauth/facebook/callback` - Callback Facebook

2. **`app/config.py`** - ✅ Nuevo
   - Configuración centralizada con Pydantic Settings
   - Variables de OAuth (Google, Facebook, GitHub)
   - Variables de API, Database, LLM, etc.

3. **`docs/OAUTH_SETUP.md`** - ✅ Nuevo (200+ líneas)
   - Guía completa para configurar Google OAuth
   - Guía completa para configurar Facebook OAuth
   - Troubleshooting
   - Notas de seguridad

#### Archivos Modificados:

1. **`app/main.py`**
   - ✅ Importado: `auth` router
   - ✅ Incluido: `app.include_router(auth.router)`

2. **`app/core/security.py`**
   - ✅ Ya tenía: `create_refresh_token()` (no se necesitó cambiar)

3. **`.env`**
   - ✅ Agregado: `API_BASE_URL=http://localhost:8000`
   - ✅ Agregado: `REFRESH_TOKEN_EXPIRE_DAYS=7`
   - ✅ Agregado: Variables OAuth (vacías, para configurar):
     ```env
     GOOGLE_CLIENT_ID=
     GOOGLE_CLIENT_SECRET=
     FACEBOOK_APP_ID=
     FACEBOOK_APP_SECRET=
     ```

---

## 🔧 Configuración Requerida

### 1. Google OAuth (Opcional)

Para habilitar login con Google:

1. Ir a [Google Cloud Console](https://console.cloud.google.com/)
2. Crear proyecto y credenciales OAuth 2.0
3. Configurar redirect URI: `http://localhost:8000/api/v1/auth/oauth/google/callback`
4. Copiar Client ID y Secret a `.env`:
   ```env
   GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
   GOOGLE_CLIENT_SECRET=tu-secret
   ```

**Ver guía completa:** [`Backend/docs/OAUTH_SETUP.md`](Backend/docs/OAUTH_SETUP.md)

### 2. Facebook OAuth (Opcional)

Para habilitar login con Facebook:

1. Ir a [Facebook Developers](https://developers.facebook.com/)
2. Crear app y configurar Facebook Login
3. Configurar redirect URI: `http://localhost:8000/api/v1/auth/oauth/facebook/callback`
4. Copiar App ID y Secret a `.env`:
   ```env
   FACEBOOK_APP_ID=tu-app-id
   FACEBOOK_APP_SECRET=tu-secret
   ```

**Ver guía completa:** [`Backend/docs/OAUTH_SETUP.md`](Backend/docs/OAUTH_SETUP.md)

---

## 🚀 Cómo Usar

### 1. Iniciar Backend

```bash
cd Backend/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Verifica que los endpoints estén disponibles en: http://localhost:8000/docs

### 2. Iniciar Frontend

```bash
cd frontend
npm run dev
```

Frontend en: http://localhost:5173

### 3. Probar Autenticación

#### Login con Email/Password:

1. Ve a http://localhost:5173/auth
2. Tab "Sign Up" → Crea una cuenta
3. Tab "Sign In" → Inicia sesión

#### Login con Google (si está configurado):

1. Click en "Continue with Google"
2. Autoriza la app en Google
3. Serás redirigido de vuelta con token automático

#### Login con Facebook (si está configurado):

1. Click en "Continue with Facebook"
2. Autoriza la app en Facebook
3. Serás redirigido de vuelta con token automático

---

## 📊 Flujo de Autenticación

### Login con Email/Password:

```
Frontend                Backend                    Database
   |                       |                           |
   |--POST /auth/login---->|                           |
   |  (email, password)    |--Query User------------->|
   |                       |<-User Data---------------|
   |                       |--Verify Password          |
   |                       |--Create JWT Tokens        |
   |<--Tokens--------------|                           |
   |  (access + refresh)   |                           |
   |                       |                           |
   |--GET /auth/me-------->|                           |
   |  (Bearer token)       |--Verify Token             |
   |                       |--Query User------------->|
   |<--User Info-----------|<-User Data---------------|
```

### Login con OAuth (Google/Facebook):

```
Frontend                Backend                OAuth Provider         Database
   |                       |                       |                      |
   |--Click OAuth button-->|                       |                      |
   |                       |                       |                      |
   |<--Redirect to OAuth---|                       |                      |
   |                       |                       |                      |
   |-------------------Redirect to Provider------->|                      |
   |                       |                       |                      |
   |<------------------User Authorizes-------------|                      |
   |                       |                       |                      |
   |-------------------Redirect with code--------->|                      |
   |                       |                       |                      |
   |                       |<--Exchange code------>|                      |
   |                       |    for access token   |                      |
   |                       |                       |                      |
   |                       |<--Get User Info------>|                      |
   |                       |                       |                      |
   |                       |--Find/Create User-------------------->|      |
   |                       |                       |                |      |
   |                       |<--User Data----------------------------      |
   |                       |                       |                      |
   |                       |--Create JWT Tokens    |                      |
   |                       |                       |                      |
   |<--Redirect with tokens|                       |                      |
   |  (in URL params)      |                       |                      |
   |                       |                       |                      |
   |--Parse tokens from URL|                       |                      |
   |--Store in localStorage|                       |                      |
```

---

## 🔐 Seguridad

### Tokens JWT:

- **Access Token**: Expira en 30 minutos
- **Refresh Token**: Expira en 7 días
- Ambos firmados con HS256 y SECRET_KEY
- Almacenados en localStorage del navegador

### OAuth:

- Flujo Authorization Code (más seguro)
- Scopes mínimos necesarios (email, profile)
- Usuarios OAuth tienen password hasheado único
- Se crea automáticamente en la BD si no existe

### Passwords:

- Hasheados con bcrypt
- Nunca se guardan en texto plano
- Bcrypt automáticamente genera salt único

---

## ✅ Testing Checklist

- [ ] Registro de nuevo usuario funciona
- [ ] Login con email/password funciona
- [ ] Token se guarda en localStorage
- [ ] Información de usuario se carga al iniciar (GET /auth/me)
- [ ] Logout limpia tokens
- [ ] Redirección a /auth si no está autenticado
- [ ] Redirección a / si ya está autenticado
- [ ] Google OAuth funciona (si está configurado)
- [ ] Facebook OAuth funciona (si está configurado)
- [ ] Refresh token funciona (implementar si es necesario)

---

## 📝 Próximos Pasos (Opcional)

1. **Reset de Contraseña**: Implementar envío de emails
2. **GitHub OAuth**: Agregar soporte (similar a Google/Facebook)
3. **2FA**: Autenticación de dos factores
4. **Rate Limiting**: Prevenir fuerza bruta en login
5. **Email Verification**: Verificar email en registro
6. **OAuth Scopes**: Agregar más información del perfil
7. **Refresh Token**: Auto-renovación en el frontend

---

## 🐛 Errores Comunes

### "redirect_uri_mismatch"
**Causa**: La URL de callback no coincide con la configurada en OAuth provider  
**Solución**: Verificar que la URL en Google/Facebook sea exactamente:
```
http://localhost:8000/api/v1/auth/oauth/{provider}/callback
```

### "Could not validate credentials"
**Causa**: Token JWT inválido o expirado  
**Solución**: Hacer logout y login de nuevo

### "Google OAuth not configured"
**Causa**: Variables de entorno no configuradas  
**Solución**: Agregar GOOGLE_CLIENT_ID y GOOGLE_CLIENT_SECRET a `.env`

### Frontend no conecta con backend
**Causa**: Backend no está corriendo o URL incorrecta  
**Solución**: Verificar que backend esté en http://localhost:8000

---

## 📚 Documentación Relacionada

- [`Backend/docs/OAUTH_SETUP.md`](Backend/docs/OAUTH_SETUP.md) - Configuración detallada de OAuth
- [`Backend/docs/API_CORE_EXPLANATION.md`](Backend/docs/API_CORE_EXPLANATION.md) - Explicación de security.py
- [FastAPI Security Docs](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/) - Debugger de tokens

---

**✅ Migración Completada con Éxito!**

Todos los archivos relacionados con Supabase han sido eliminados y reemplazados con autenticación nativa usando FastAPI + JWT + OAuth.
