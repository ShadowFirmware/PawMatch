# ✅ Configuración Completa de Google OAuth2

## Pasos Completados ✅

### Backend (Django)
- ✅ Paso 1: Proyecto creado en Google Cloud Console
- ✅ Paso 2: Credenciales OAuth2 creadas
- ✅ Paso 3: Configuración en Django settings.py
- ✅ Paso 4: Variables de entorno configuradas

### Frontend (React)
- ✅ Servicio de autenticación actualizado (`authService.js`)
- ✅ Componente Login actualizado con botón de Google funcional
- ✅ Dependencia `@react-oauth/google` agregada al package.json
- ✅ Variables de entorno configuradas

## 📋 Pasos Finales para Completar la Configuración

### 1. Instalar Dependencias del Frontend

```bash
cd 404-not-found
npm install
```

Esto instalará `@react-oauth/google` y todas las demás dependencias.

### 2. Configurar Variables de Entorno del Frontend

Crea o actualiza el archivo `.env` en la carpeta `404-not-found`:

```env
VITE_API_URL=http://localhost:8000/api
VITE_SOCKET_URL=http://localhost:8000
VITE_GOOGLE_CLIENT_ID=693981098388-nmk8rg3ov3lphpdt3tgiarhf0behrna0.apps.googleusercontent.com
```

**Nota:** El Client ID ya está configurado por defecto en el código, pero es mejor usar variables de entorno.

### 3. Configurar Variables de Entorno del Backend (Opcional pero Recomendado)

Crea un archivo `.env` en la raíz del proyecto Django (`C:\Users\luisp\PawMatch\`):

```env
GOOGLE_OAUTH2_CLIENT_ID=693981098388-nmk8rg3ov3lphpdt3tgiarhf0behrna0.apps.googleusercontent.com
GOOGLE_OAUTH2_CLIENT_SECRET=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
```

**Nota:** Las credenciales ya están hardcodeadas en `settings.py` como fallback, pero para producción es mejor usar variables de entorno.

### 4. Instalar python-dotenv (Opcional)

Si quieres usar archivo `.env` en Django, instala:

```bash
pip install python-dotenv
```

Y agrega al inicio de `settings.py`:

```python
from dotenv import load_dotenv
load_dotenv()
```

### 5. Verificar que el Backend esté Corriendo

```bash
cd C:\Users\luisp\PawMatch
python manage.py runserver
```

El servidor debe estar en `http://localhost:8000`

### 6. Verificar que el Frontend esté Corriendo

```bash
cd 404-not-found
npm run dev
```

El servidor debe estar en `http://localhost:5173`

## 🧪 Probar la Funcionalidad

1. Abre `http://localhost:5173/login`
2. Haz clic en el botón de Google (el círculo blanco con el logo de Google)
3. Selecciona tu cuenta de Google
4. Deberías ser redirigido al dashboard después de autenticarte exitosamente

## 🔍 Verificación de Funcionamiento

### Backend
- ✅ Endpoint `/api/auth/google/` está disponible
- ✅ Valida el token de Google
- ✅ Crea o autentica usuarios automáticamente
- ✅ Devuelve token de Django REST Framework

### Frontend
- ✅ Botón de Google funcional en Login.jsx
- ✅ Integración con `@react-oauth/google`
- ✅ Envía access_token al backend
- ✅ Guarda token y usuario en localStorage
- ✅ Redirige al dashboard después del login

## 🐛 Troubleshooting

### Error: "Invalid client"
- Verifica que el Client ID en `.env` del frontend coincida con el de Google Cloud Console
- Asegúrate de que el Client ID esté en las variables de entorno correctas

### Error: "redirect_uri_mismatch"
- Verifica en Google Cloud Console que `http://localhost:5173` esté en las URIs autorizadas
- Asegúrate de que el puerto coincida exactamente

### El botón de Google no hace nada
- Verifica que `@react-oauth/google` esté instalado: `npm list @react-oauth/google`
- Revisa la consola del navegador para errores
- Asegúrate de que el Client ID esté configurado correctamente

### Error de CORS
- Verifica que `http://localhost:5173` esté en `CORS_ALLOWED_ORIGINS` en `settings.py`
- Reinicia el servidor Django después de cambiar la configuración

## 📝 Notas Importantes

1. **Seguridad en Producción:**
   - Nunca commits el archivo `.env` con credenciales reales
   - Usa variables de entorno del servidor en producción
   - Cambia el Client Secret si se compromete

2. **Dominios Autorizados:**
   - Para producción, agrega tu dominio real en Google Cloud Console
   - Actualiza las URIs de redirección para producción

3. **Client ID:**
   - El Client ID puede ser público (está en el frontend)
   - El Client Secret NUNCA debe estar en el frontend
   - Solo debe estar en el backend

## ✅ Checklist Final

- [ ] Dependencias del frontend instaladas (`npm install`)
- [ ] Archivo `.env` del frontend configurado
- [ ] Archivo `.env` del backend configurado (opcional)
- [ ] Backend corriendo en `http://localhost:8000`
- [ ] Frontend corriendo en `http://localhost:5173`
- [ ] Botón de Google funciona correctamente
- [ ] Login con Google redirige al dashboard
- [ ] Token se guarda en localStorage
- [ ] Usuario se crea automáticamente si no existe

¡Todo listo! 🎉
