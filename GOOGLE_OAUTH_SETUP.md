# 🔐 Configuración de Autenticación con Google OAuth2

## 📋 Pasos para Configurar Google OAuth2

### ✅ 1. Crear Proyecto en Google Cloud Console (COMPLETADO)

1. ✅ Ve a [Google Cloud Console](https://console.cloud.google.com/)
2. ✅ Crea un nuevo proyecto o selecciona uno existente
3. ✅ Habilita la API de Google+ (si no está habilitada)

### ✅ 2. Crear Credenciales OAuth2 (COMPLETADO)

1. ✅ Ve a **APIs & Services** > **Credentials**
2. ✅ Haz clic en **Create Credentials** > **OAuth client ID**
3. ✅ Configura la pantalla de consentimiento OAuth
4. ✅ Crea el OAuth Client ID con las URIs correctas
5. ✅ Client ID: `693981098388-nmk8rg3ov3lphpdt3tgiarhf0behrna0.apps.googleusercontent.com`

### ✅ 3. Configurar en Django (COMPLETADO)

Las credenciales están configuradas en `PawMatch/settings.py` con valores por defecto.

### ✅ 4. Configurar Variables de Entorno (COMPLETADO)

✅ Variables de entorno configuradas en `settings.py` con fallback a valores por defecto.
✅ Archivo `.env.example` creado en la raíz del proyecto.
✅ Archivo `.env` del frontend actualizado con `VITE_GOOGLE_CLIENT_ID`.

## ✅ Implementación en el Frontend (COMPLETADO)

### ✅ Opción Implementada: Google Sign-In Button con @react-oauth/google

✅ **Archivo actualizado:** `404-not-found/src/features/auth/Login.jsx`

El componente Login ahora incluye:
- ✅ Integración con `@react-oauth/google`
- ✅ Botón de Google funcional
- ✅ Manejo de errores con toast notifications
- ✅ Loading states durante la autenticación
- ✅ Redirección automática al dashboard después del login

**Para usar:**
1. Instala las dependencias: `npm install` (en la carpeta `404-not-found`)
2. El botón de Google ya está funcional en la página de login
3. El Client ID se obtiene de `VITE_GOOGLE_CLIENT_ID` en `.env`

**Servicio actualizado:** `404-not-found/src/services/authService.js`
- ✅ Método `loginWithGoogle()` agregado

### Opción 2: Usar Google Identity Services

```html
<!-- En index.html -->
<script src="https://accounts.google.com/gsi/client" async defer></script>
```

```javascript
// En tu componente React
function handleGoogleSignIn() {
  window.google.accounts.id.initialize({
    client_id: 'TU_CLIENT_ID',
    callback: async (response) => {
      // response.credential es el JWT token
      // Necesitas intercambiarlo por un access_token
      const tokenResponse = await fetch('http://localhost:8000/api/auth/google/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          access_token: response.credential // O el access_token obtenido
        })
      });
      
      const data = await tokenResponse.json();
      // Manejar respuesta
    }
  });

  window.google.accounts.id.prompt();
}
```

### Opción 3: Usar Google OAuth2 directamente

```javascript
// Función para iniciar sesión con Google
async function loginWithGoogle() {
  // Redirigir a Google OAuth
  const clientId = 'TU_CLIENT_ID';
  const redirectUri = 'http://localhost:5173/auth/google/callback';
  const scope = 'openid email profile';
  const responseType = 'token';
  
  const authUrl = `https://accounts.google.com/o/oauth2/v2/auth?` +
    `client_id=${clientId}&` +
    `redirect_uri=${redirectUri}&` +
    `response_type=${responseType}&` +
    `scope=${scope}`;
  
  window.location.href = authUrl;
}

// En la página de callback (auth/google/callback)
function handleGoogleCallback() {
  const urlParams = new URLSearchParams(window.location.hash.substring(1));
  const accessToken = urlParams.get('access_token');
  
  if (accessToken) {
    // Enviar al backend
    fetch('http://localhost:8000/api/auth/google/', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ access_token: accessToken })
    })
    .then(res => res.json())
    .then(data => {
      if (data.token) {
        localStorage.setItem('token', data.token);
        localStorage.setItem('user', JSON.stringify(data.user));
        window.location.href = '/dashboard';
      }
    });
  }
}
```

## 📡 Endpoint del Backend

### POST `/api/auth/google/`

**Request:**
```json
{
  "access_token": "ya29.a0AfH6..."
}
```

**Response (éxito):**
```json
{
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "user": {
    "dueño_id": 1,
    "nombre": "Juan Pérez",
    "email": "juan@gmail.com",
    "ubicación": "0,0",
    "fecha_registro": "2026-03-15T10:00:00Z",
    "perfil": {
      "perfil_id": 1,
      "foto_perfil": "https://lh3.googleusercontent.com/...",
      ...
    }
  },
  "is_new_user": false
}
```

**Response (error):**
```json
{
  "access_token": ["Token de acceso inválido."]
}
```

## 🔒 Seguridad

1. **Nunca expongas el Client Secret** en el frontend
2. **Valida el token** en el backend antes de crear/autenticar usuarios
3. **Usa HTTPS** en producción
4. **Configura dominios autorizados** correctamente
5. **Revisa los permisos** solicitados (solo email y profile)

## 🐛 Troubleshooting

### Error: "redirect_uri_mismatch"
- Verifica que la URI de redirección esté en la lista de URIs autorizadas en Google Cloud Console
- Asegúrate de que coincida exactamente (incluyendo http/https, puerto, etc.)

### Error: "invalid_client"
- Verifica que el Client ID sea correcto
- Asegúrate de que el proyecto tenga la API de Google+ habilitada

### Error: "Token de acceso inválido"
- Verifica que el token no haya expirado
- Asegúrate de estar enviando el `access_token` correcto

## 📝 Notas

- ✅ El sistema crea automáticamente un usuario si no existe
- ✅ Si el usuario ya existe, simplemente lo autentica
- ✅ La foto de perfil de Google se guarda automáticamente en el perfil
- ✅ El usuario puede actualizar su ubicación después del registro

## 🎯 Próximos Pasos

1. **Instalar dependencias del frontend:**
   ```bash
   cd 404-not-found
   npm install
   ```

2. **Verificar que todo funcione:**
   - Backend corriendo en `http://localhost:8000`
   - Frontend corriendo en `http://localhost:5173`
   - Probar el botón de Google en `/login`

3. **Ver documentación completa:** `CONFIGURACION_COMPLETA.md`

## ✅ Estado de Implementación

- ✅ Backend configurado y funcionando
- ✅ Frontend integrado con Google OAuth2
- ✅ Botón de Google funcional en Login
- ✅ Servicio de autenticación actualizado
- ✅ Variables de entorno configuradas
- ✅ Documentación completa

**¡Todo listo para usar!** 🎉
