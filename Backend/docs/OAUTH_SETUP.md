# Configuración de Autenticación OAuth - TwinSec Studio

Esta guía explica cómo configurar la autenticación con Google y Facebook para TwinSec Studio.

## 📋 Tabla de Contenidos

1. [Google OAuth](#google-oauth)
2. [Facebook OAuth](#facebook-oauth)
3. [Configurar el Backend](#configurar-el-backend)
4. [Probar la Autenticación](#probar-la-autenticación)

---

## 🔐 Google OAuth

### 1. Crear Proyecto en Google Cloud Console

1. Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. Crea un nuevo proyecto o selecciona uno existente
3. Habilita la **Google+ API** en el proyecto

### 2. Configurar OAuth Consent Screen

1. Ve a **APIs & Services** → **OAuth consent screen**
2. Selecciona **External** (para testing) o **Internal** (solo para tu organización)
3. Completa la información:
   - **App name**: TwinSec Studio
   - **User support email**: tu email
   - **Developer contact**: tu email
4. Agrega los scopes necesarios:
   - `openid`
   - `email`
   - `profile`
5. Guarda los cambios

### 3. Crear Credenciales OAuth 2.0

1. Ve a **APIs & Services** → **Credentials**
2. Click en **Create Credentials** → **OAuth 2.0 Client ID**
3. Selecciona **Web application**
4. Configura:
   - **Name**: TwinSec Studio Web Client
   - **Authorized JavaScript origins**:
     ```
     http://localhost:8000
     http://localhost:5173
     ```
   - **Authorized redirect URIs**:
     ```
     http://localhost:8000/api/v1/auth/oauth/google/callback
     ```
5. Click **Create**
6. **Guarda el Client ID y Client Secret** que aparecen

### 4. Agregar al Backend

Edita `Backend/api/.env`:
```env
GOOGLE_CLIENT_ID=tu-client-id-aqui.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret-aqui
```

---

## 📘 Facebook OAuth

### 1. Crear App en Facebook Developers

1. Ve a [Facebook Developers](https://developers.facebook.com/)
2. Click en **My Apps** → **Create App**
3. Selecciona **Consumer** como tipo de app
4. Completa:
   - **App Name**: TwinSec Studio
   - **App Contact Email**: tu email
5. Click **Create App**

### 2. Configurar Facebook Login

1. En el dashboard de tu app, click en **Add Product**
2. Busca **Facebook Login** y click **Set Up**
3. Selecciona **Web**
4. Configura:
   - **Site URL**: `http://localhost:5173`
5. Ve a **Facebook Login** → **Settings**
6. En **Valid OAuth Redirect URIs**, agrega:
   ```
   http://localhost:8000/api/v1/auth/oauth/facebook/callback
   ```
7. Guarda los cambios

### 3. Obtener App ID y App Secret

1. Ve a **Settings** → **Basic**
2. Copia el **App ID**
3. Copia el **App Secret** (click en "Show")

### 4. Configurar Permisos

1. Ve a **App Review** → **Permissions and Features**
2. Request permissions:
   - `email` (requerido)
   - `public_profile` (incluido por defecto)

### 5. Modo de Desarrollo vs Producción

**Modo Desarrollo** (para testing):
- Solo usuarios que agregues como testers pueden usar la app
- Ve a **Roles** → **Test Users** para agregar usuarios de prueba

**Modo Producción**:
- Ve a **App Review** → **Request** y solicita revisión
- Facebook revisará tu app antes de aprobarla

### 6. Agregar al Backend

Edita `Backend/api/.env`:
```env
FACEBOOK_APP_ID=tu-app-id-aqui
FACEBOOK_APP_SECRET=tu-app-secret-aqui
```

---

## ⚙️ Configurar el Backend

### 1. Instalar Dependencias

```bash
cd Backend/api
pip install httpx  # Para requests HTTP async
```

### 2. Verificar Variables de Entorno

El archivo `Backend/api/.env` debe tener:

```env
# API Base URL (importante para callbacks de OAuth)
API_BASE_URL=http://localhost:8000

# Google OAuth
GOOGLE_CLIENT_ID=tu-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=tu-client-secret

# Facebook OAuth
FACEBOOK_APP_ID=tu-app-id
FACEBOOK_APP_SECRET=tu-app-secret
```

### 3. Iniciar el Backend

```bash
cd Backend/api
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Verificar Endpoints

Abre http://localhost:8000/docs y verifica que existan estos endpoints:

- `GET /api/v1/auth/oauth/google` - Iniciar login con Google
- `GET /api/v1/auth/oauth/google/callback` - Callback de Google
- `GET /api/v1/auth/oauth/facebook` - Iniciar login con Facebook
- `GET /api/v1/auth/oauth/facebook/callback` - Callback de Facebook

---

## 🧪 Probar la Autenticación

### 1. Iniciar Frontend

```bash
cd frontend
npm run dev
```

El frontend estará en: http://localhost:5173

### 2. Probar Google Login

1. Ve a la página de login
2. Click en **Continue with Google**
3. Deberías ser redirigido a Google
4. Autoriza la aplicación
5. Serás redirigido de vuelta con el token en la URL
6. El frontend guardará el token automáticamente

### 3. Probar Facebook Login

1. Ve a la página de login
2. Click en **Continue with Facebook**
3. Autoriza la aplicación
4. Serás redirigido de vuelta con el token

### 4. Verificar en la Base de Datos

```sql
SELECT id, email, username, full_name, oauth_provider, oauth_id 
FROM users 
WHERE oauth_provider IN ('google', 'facebook');
```

---

## 🐛 Troubleshooting

### Error: "redirect_uri_mismatch" (Google)

**Solución**: Verifica que la URL de callback en Google Cloud Console coincida exactamente:
```
http://localhost:8000/api/v1/auth/oauth/google/callback
```

### Error: "URL Blocked: This redirect failed because..." (Facebook)

**Solución**: Verifica que la URL de callback esté en **Valid OAuth Redirect URIs** en Facebook:
```
http://localhost:8000/api/v1/auth/oauth/facebook/callback
```

### Error: "Google OAuth not configured"

**Solución**: Verifica que las variables de entorno estén configuradas correctamente en `.env`:
```env
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
```

Reinicia el servidor después de cambiar `.env`.

### Usuario no recibe email de Facebook

**Solución**: Facebook requiere que solicites el permiso `email` en **App Review**. Mientras tanto, usa usuarios de prueba que tengas agregados.

---

## 📝 Notas de Seguridad

1. **Nunca** subas las credenciales OAuth a GitHub
2. Agrega `.env` a `.gitignore`
3. En producción, usa HTTPS (`https://`)
4. Rota las credenciales regularmente
5. Limita los scopes solo a lo necesario

---

## 🔗 Enlaces Útiles

- [Google OAuth 2.0 Docs](https://developers.google.com/identity/protocols/oauth2)
- [Facebook Login Docs](https://developers.facebook.com/docs/facebook-login)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT.io](https://jwt.io/) - Debugger de tokens JWT
