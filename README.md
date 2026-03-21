# PawMatch - Backend Django

Backend desarrollado con Django REST Framework para la aplicación PawMatch, una red social de emparejamiento para mascotas.

## 🚀 Tecnologías

- **Django 4.2.10** - Framework web
- **Django REST Framework** - API REST
- **MySQL** - Base de datos
- **django-cors-headers** - Configuración CORS para React

## 📁 Estructura del Proyecto

```
PawMatch/
├── auth_app/          # Autenticación y usuarios (Dueños)
├── pets_app/          # Gestión de mascotas y preferencias
├── matches_app/       # Sistema de emparejamiento y reportes
├── chat_app/          # Mensajería entre usuarios
├── admin_app/         # Panel administrativo (futuro)
└── PawMatch/          # Configuración del proyecto
```

## 🛠️ Instalación

1. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

2. **Configurar la base de datos MySQL:**
   - Crear la base de datos `PawMatch` ejecutando el archivo `PawMatch.sql`
   - Configurar las credenciales en `PawMatch/settings.py`:
   ```python
   DATABASES = {
       'default': {
           'ENGINE': 'django.db.backends.mysql',
           'NAME': 'PawMatch',
           'USER': 'tu_usuario',
           'PASSWORD': 'tu_contraseña',
           'HOST': 'localhost',
           'PORT': '3306',
       }
   }
   ```

3. **Ejecutar migraciones:**
```bash
python manage.py makemigrations
python manage.py migrate
```

4. **Crear superusuario (opcional):**
```bash
python manage.py createsuperuser
```

5. **Iniciar el servidor:**
```bash
python manage.py runserver
```

El servidor estará disponible en `http://localhost:8000`

## 📋 Endpoints de la API

### Autenticación (`/api/auth/`)
- `POST /api/auth/register/` - Registrar nuevo usuario (crea perfil automáticamente)
- `POST /api/auth/login/` - Iniciar sesión con email y contraseña
- `POST /api/auth/google/` - Iniciar sesión con Google OAuth2
- `GET /api/dueños/mi_perfil/` - Obtener mi perfil completo
- `PUT /api/dueños/actualizar_perfil/` - Actualizar mi perfil

### Perfiles (`/api/perfiles/`)
- `GET /api/perfiles/` - Obtener mi perfil
- `PUT /api/perfiles/{id}/` - Actualizar perfil
- `PATCH /api/perfiles/{id}/` - Actualizar parcialmente perfil

### Mascotas (`/api/pets/`)
- `GET /api/pets/my-pets/` - Obtener mis mascotas
- `GET /api/pets/{id}/` - Obtener una mascota
- `POST /api/pets/` - Crear mascota
- `PUT /api/pets/{id}/` - Actualizar mascota
- `DELETE /api/pets/{id}/` - Eliminar mascota

### Emparejamiento (`/api/matches/`)
- `GET /api/matches/potential/{pet_id}/?radius=10` - Obtener posibles matches
- `POST /api/matches/like/` - Dar like a una mascota
- `POST /api/matches/pass/` - Rechazar una mascota
- `GET /api/matches/my-matches/{pet_id}/` - Obtener mis matches aceptados

### Chat REST API (`/api/chat/`)
- `GET /api/chat/conversations/` - Obtener todas las conversaciones
- `GET /api/chat/conversations/{conversationId}/messages/` - Obtener historial de mensajes
- `POST /api/chat/conversations/{conversationId}/messages/` - Enviar mensaje (fallback)

### Chat WebSocket (`/ws/chat/{match_id}/`)
- Conexión WebSocket para chat en tiempo real tipo WhatsApp
- Ver documentación completa en `WEBSOCKET_CHAT.md`

## 🔐 Autenticación

La API utiliza autenticación por token. Después de iniciar sesión o registrarse, recibirás un token que debes incluir en las peticiones:

```
Authorization: Bearer {token}
```

### Métodos de Autenticación

1. **Login Tradicional**: Email y contraseña
   ```json
   POST /api/auth/login/
   {
     "email": "usuario@example.com",
     "password": "contraseña123"
   }
   ```

2. **Registro Tradicional**: Crear cuenta nueva
   ```json
   POST /api/auth/register/
   {
     "nombre": "Juan Pérez",
     "email": "usuario@example.com",
     "password": "contraseña123",
     "ubicación": "19.4326,-99.1332"
   }
   ```

3. **Login con Google**: Autenticación OAuth2
   ```json
   POST /api/auth/google/
   {
     "access_token": "ya29.a0AfH6..."
   }
   ```
   Ver `GOOGLE_OAUTH_SETUP.md` para configuración completa.

## 🗄️ Modelos Principales

- **Dueño**: Usuarios de la plataforma (modelo de usuario personalizado)
- **Perfil**: Información extendida del usuario (foto, biografía, ubicación, etc.)
- **Mascota**: Perfiles de mascotas (máximo 5 por dueño)
- **Match**: Emparejamientos entre mascotas
- **Mensaje**: Mensajes entre dueños con match aceptado
- **Preferencia**: Preferencias de búsqueda del usuario
- **Reporte**: Reportes de contenido inapropiado

## 🧮 Algoritmo de Matching

El sistema de emparejamiento considera dos factores con igual peso (50% cada uno):

1. **Características de la mascota** (50%):
   - Misma especie
   - Edad similar
   - Género compatible
   - Misma raza (bonus)
   - Descripción similar

2. **Ubicación geográfica** (50%):
   - Distancia mínima: 1 km
   - Distancia ideal: hasta 10 km
   - Distancia máxima: 15 km

## 📝 Notas

- El límite de 5 mascotas por dueño se valida automáticamente
- Los matches solo se crean cuando ambas mascotas se dan like mutuamente
- El chat solo está disponible para matches aceptados
- Las coordenadas de ubicación deben estar en formato "lat,lng" (ej: "19.4326,-99.1332")
- Cada usuario tiene un perfil que se crea automáticamente al registrarse
- El chat utiliza WebSockets para comunicación en tiempo real tipo WhatsApp
- Ver `WEBSOCKET_CHAT.md` para documentación completa del sistema de chat
- Ver `GOOGLE_OAUTH_SETUP.md` para configurar autenticación con Google
- Los usuarios de Google pueden iniciar sesión sin contraseña
