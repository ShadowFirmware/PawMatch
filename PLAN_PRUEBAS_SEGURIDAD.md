# Plan de Pruebas de Seguridad — PawMatch

**Proyecto:** PawMatch (Red social para mascotas)  
**Equipo:** 404 Not Found — 8° B IDGS  
**Fecha:** 2026-04-14  
**Stack:** Django 4.2 + DRF 3.14 + React 19 + MySQL  
**Entorno de prueba:** `http://localhost:8000` (backend) / `http://localhost:5173` (frontend)

---

## Índice

1. [Autenticación y Gestión de Tokens](#1-autenticación-y-gestión-de-tokens)
2. [Autorización e IDOR](#2-autorización-e-idor)
3. [Rate Limiting](#3-rate-limiting)
4. [OAuth (Google / Facebook)](#4-oauth-google--facebook)
5. [Subida de Archivos](#5-subida-de-archivos)
6. [Validación de Entradas](#6-validación-de-entradas)
7. [WebSocket](#7-websocket)
8. [Cabeceras HTTP de Seguridad](#8-cabeceras-http-de-seguridad)
9. [CORS](#9-cors)
10. [Enumeración e Information Disclosure](#10-enumeración-e-information-disclosure)
11. [Lógica de Negocio](#11-lógica-de-negocio)
12. [Bitácora de Base de Datos](#12-bitácora-de-base-de-datos)
13. [Cifrado de Datos](#13-cifrado-de-datos)
14. [Configuración del Entorno](#14-configuración-del-entorno)
15. [Resumen de Prioridades](#15-resumen-de-prioridades)

---

## 1. Autenticación y Gestión de Tokens

### PT-AUTH-01 — Acceso sin token
- **Descripción:** Verificar que los endpoints protegidos rechacen requests sin token.
- **Pasos:**
  ```bash
  curl http://localhost:8000/api/pets/
  curl http://localhost:8000/api/matches/
  curl http://localhost:8000/api/chat/
  ```
- **Resultado esperado:** `401 Unauthorized`
- **Archivo:** `auth_app/authentication.py`

### PT-AUTH-02 — Token expirado (> 7 días)
- **Descripción:** Verificar que tokens con más de 7 días sean rechazados.
- **Pasos:**
  1. Autenticarse y obtener token.
  2. En MySQL, actualizar `created` de `authtoken_token` a una fecha de hace 8 días.
  3. Usar ese token en cualquier endpoint protegido.
- **Resultado esperado:** `401 Unauthorized`
- **Archivo:** `auth_app/authentication.py` — lógica de expiración `TOKEN_EXPIRY_DAYS = 7`

### PT-AUTH-03 — Token de otro usuario
- **Descripción:** Verificar que el token del usuario A no acceda a recursos del usuario B.
- **Pasos:**
  1. Obtener token de Usuario A.
  2. Usar ese token para `GET /api/pets/{id_mascota_usuario_B}/`.
- **Resultado esperado:** `404 Not Found` (get_queryset filtra por dueño)

### PT-AUTH-04 — Token no invalidado tras logout
- **Descripción:** Verificar que el token quede inutilizable después del logout.
- **Pasos:**
  ```bash
  # 1. Guardar token
  TOKEN=$(curl -s -X POST http://localhost:8000/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email":"test@test.com","password":"Pass1234!"}' | python -c "import sys,json; print(json.load(sys.stdin)['token'])")

  # 2. Logout
  curl -X POST http://localhost:8000/api/auth/logout/ \
    -H "Authorization: Bearer $TOKEN"

  # 3. Reintentar con el mismo token
  curl http://localhost:8000/api/pets/my-pets/ \
    -H "Authorization: Bearer $TOKEN"
  ```
- **Resultado esperado:** Paso 3 devuelve `401 Unauthorized`

### PT-AUTH-05 — Token anterior inválido tras nuevo login
- **Descripción:** Verificar que el login rota el token (el token viejo deja de funcionar).
- **Pasos:**
  1. Login → guardar `TOKEN_VIEJO`.
  2. Login de nuevo → guardar `TOKEN_NUEVO`.
  3. Usar `TOKEN_VIEJO` en un endpoint protegido.
- **Resultado esperado:** `TOKEN_VIEJO` devuelve `401`
- **Archivo:** `auth_app/views.py:100-101` — `Token.objects.filter(user=user).delete()`

### PT-AUTH-06 — Token con formato inválido
- **Descripción:** Verificar que tokens malformados sean rechazados sin errores 500.
- **Pasos:**
  ```bash
  curl http://localhost:8000/api/pets/ -H "Authorization: Bearer token_falso_abc123"
  curl http://localhost:8000/api/pets/ -H "Authorization: Token "
  curl http://localhost:8000/api/pets/ -H "Authorization: "
  ```
- **Resultado esperado:** `401`, nunca `500`

---

## 2. Autorización e IDOR

### PT-IDOR-01 — Acceso a mascotas de otro usuario
- **Descripción:** Verificar que un usuario no pueda leer/modificar/eliminar mascotas ajenas.
- **Pasos:**
  ```bash
  # Con token de Usuario A, intentar acceder a mascota de Usuario B
  curl http://localhost:8000/api/pets/{id_mascota_usuario_B}/ \
    -H "Authorization: Bearer TOKEN_USUARIO_A"

  curl -X PUT http://localhost:8000/api/pets/{id_mascota_usuario_B}/ \
    -H "Authorization: Bearer TOKEN_USUARIO_A" \
    -H "Content-Type: application/json" \
    -d '{"name":"Hackeado"}'

  curl -X DELETE http://localhost:8000/api/pets/{id_mascota_usuario_B}/ \
    -H "Authorization: Bearer TOKEN_USUARIO_A"
  ```
- **Resultado esperado:** `404 Not Found` en los tres casos
- **Archivo:** `pets_app/views.py:16` — `get_queryset` filtra por `dueño=user`

### PT-IDOR-02 — Acceso a mensajes de conversación ajena
- **Descripción:** Verificar que un usuario no pueda leer el chat de un match en el que no participa.
- **Pasos:**
  ```bash
  curl http://localhost:8000/api/chat/{match_id_ajeno}/messages/ \
    -H "Authorization: Bearer TOKEN_USUARIO_C"
  ```
- **Resultado esperado:** `403 Forbidden`
- **Archivo:** `chat_app/views.py:80` — verificación de participantes en el match

### PT-IDOR-03 — Like con mascota ajena
- **Descripción:** Verificar que un usuario no pueda dar like usando una mascota que no le pertenece.
- **Pasos:**
  ```bash
  curl -X POST http://localhost:8000/api/matches/like/ \
    -H "Authorization: Bearer TOKEN_USUARIO_A" \
    -H "Content-Type: application/json" \
    -d '{"pet_id": ID_MASCOTA_USUARIO_B, "target_pet_id": cualquier_id}'
  ```
- **Resultado esperado:** `404 Not Found`
- **Archivo:** `matches_app/views.py:224` — `get_object_or_404(Mascota, pk=pet_id, dueño=request.user)`

### PT-IDOR-04 — Ver matches de mascota ajena
- **Descripción:** Verificar que solo el dueño pueda consultar los matches de su mascota.
- **Pasos:**
  ```bash
  curl http://localhost:8000/api/matches/my-matches/{id_mascota_ajena}/ \
    -H "Authorization: Bearer TOKEN_USUARIO_A"
  ```
- **Resultado esperado:** `404 Not Found`

### PT-IDOR-05 — Escalada de privilegios en registro
- **Descripción:** Verificar que no se puedan asignar `is_staff` o `is_superuser` desde el registro.
- **Pasos:**
  ```bash
  curl -X POST http://localhost:8000/api/auth/register/ \
    -H "Content-Type: application/json" \
    -d '{"email":"hacker@test.com","password":"Pass1234!","nombre":"Hacker",
         "ubicación":"0,0","is_staff":true,"is_superuser":true}'
  ```
- **Resultado esperado:** Usuario creado sin privilegios elevados (`is_staff=false`, `is_superuser=false`)

### PT-IDOR-06 — Enumeración de IDs secuenciales
- **Descripción:** Los IDs (mascota_id, match_id, msg_id) son AutoField secuenciales. Verificar que las vistas filtren correctamente por propietario.
- **Pasos:** Iterar IDs del 1 al 50 en `/api/pets/{id}/` con token de usuario sin mascotas.
- **Resultado esperado:** Todos devuelven `404`, ninguno expone datos ajenos.

---

## 3. Rate Limiting

### PT-RATE-01 — Brute force en login (límite: 5/min)
- **Descripción:** Verificar que el sistema bloquee más de 5 intentos de login por minuto desde la misma IP.
- **Pasos:**
  ```bash
  for i in $(seq 1 10); do
    echo -n "Intento $i: "
    curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/auth/login/ \
      -H "Content-Type: application/json" \
      -d '{"email":"victim@test.com","password":"contrasena_incorrecta"}'
    echo
  done
  ```
- **Resultado esperado:** Intentos 1-5 → `400`, intentos 6-10 → `429 Too Many Requests`
- **Archivo:** `auth_app/throttles.py` — `LoginRateThrottle (5/min)`

### PT-RATE-02 — Bypass de rate limiting via X-Forwarded-For
- **Descripción:** Verificar si el throttle usa la IP del header `X-Forwarded-For` sin validar, permitiendo bypass.
- **Pasos:**
  ```bash
  # Agotar el límite de 5 intentos normalmente
  for i in $(seq 1 5); do
    curl -s -o /dev/null -X POST http://localhost:8000/api/auth/login/ \
      -H "Content-Type: application/json" \
      -d '{"email":"victim@test.com","password":"wrong"}'
  done

  # Intentar bypass con IP falsa
  curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/auth/login/ \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: 9.9.9.9" \
    -d '{"email":"victim@test.com","password":"wrong"}'
  ```
- **Resultado esperado:** `429` (el header no debe evadir el límite)
- **Riesgo:** `audit.py:12-15` también toma la IP de este header sin validar

### PT-RATE-03 — Rate limit en registro (límite: 3/min)
- **Descripción:** Verificar que no se puedan crear más de 3 cuentas por minuto desde la misma IP.
- **Pasos:**
  ```bash
  for i in $(seq 1 5); do
    echo -n "Intento $i: "
    curl -s -o /dev/null -w "%{http_code}" -X POST http://localhost:8000/api/auth/register/ \
      -H "Content-Type: application/json" \
      -d "{\"email\":\"test$i@test.com\",\"password\":\"Pass1234!\",\"nombre\":\"Test\",\"ubicación\":\"0,0\"}"
    echo
  done
  ```
- **Resultado esperado:** Intentos 1-3 → `201`, intentos 4-5 → `429`
- **Archivo:** `auth_app/throttles.py` — `RegisterRateThrottle (3/min)`

### PT-RATE-04 — Rate limit global para usuarios autenticados (2000/hora)
- **Descripción:** Verificar que el throttle de usuario autenticado esté activo.
- **Pasos:** Enviar 2001 requests con el mismo token en menos de una hora.
- **Resultado esperado:** Request 2001 → `429`

---

## 4. OAuth (Google / Facebook)

### PT-OAUTH-01 — Token de Google inválido
- **Descripción:** Verificar que un access_token forjado no cree una cuenta ni devuelva datos.
- **Pasos:**
  ```bash
  curl -X POST http://localhost:8000/api/auth/google/ \
    -H "Content-Type: application/json" \
    -d '{"access_token": "token.forjado.completamente.invalido"}'
  ```
- **Resultado esperado:** `400 Bad Request` con mensaje de error, nunca `201` ni `500`
- **Archivo:** `auth_app/serializers.py:123-142`

### PT-OAUTH-02 — Token de Google expirado (válido pero caducado)
- **Descripción:** Usar un access_token real pero expirado (copiar uno anterior).
- **Resultado esperado:** `400 Bad Request` — Google devuelve error al verificarlo

### PT-OAUTH-03 — Cuenta OAuth no puede hacer login normal
- **Descripción:** Un usuario registrado vía Google (`set_unusable_password`) no debe poder autenticarse con contraseña.
- **Pasos:**
  1. Crear cuenta vía `POST /api/auth/google/` con token válido.
  2. Intentar `POST /api/auth/login/` con el email de esa cuenta y cualquier contraseña.
- **Resultado esperado:** `400 Bad Request — Credenciales inválidas`
- **Archivo:** `auth_app/views.py:170` — `dueno.set_unusable_password()`

### PT-OAUTH-04 — Token de Facebook con email faltante
- **Descripción:** Verificar que la app rechace cuentas de Facebook sin email asociado.
- **Resultado esperado:** `400 Bad Request` con mensaje descriptivo
- **Archivo:** `auth_app/serializers.py:164-165`

---

## 5. Subida de Archivos

### PT-FILE-01 — Archivo malicioso renombrado como imagen
- **Descripción:** Verificar que el servidor no almacene ni ejecute archivos peligrosos con extensión falsa.
- **Pasos:**
  ```bash
  # Crear archivo de prueba con contenido PHP pero extensión .jpg
  echo '<?php echo "hacked"; ?>' > test_shell.jpg

  curl -X POST http://localhost:8000/api/pets/ \
    -H "Authorization: Bearer TOKEN" \
    -F "photo=@test_shell.jpg;type=image/jpeg" \
    -F "name=TestPet" -F "type=Perro" -F "age=2"
  ```
- **Resultado esperado:** El archivo se guarda con nombre seguro; no es ejecutable desde `/media/`

### PT-FILE-02 — Archivo que excede el límite de 5 MB
- **Descripción:** Verificar que el límite de tamaño de archivo sea respetado.
- **Pasos:**
  ```bash
  # Generar archivo de 6 MB
  dd if=/dev/urandom bs=1M count=6 of=archivo_grande.bin

  curl -X POST http://localhost:8000/api/pets/ \
    -H "Authorization: Bearer TOKEN" \
    -F "photo=@archivo_grande.bin" \
    -F "name=TestPet" -F "type=Perro" -F "age=2"
  ```
- **Resultado esperado:** `413 Request Entity Too Large`
- **Archivo:** `settings.py:126-127` — `FILE_UPLOAD_MAX_MEMORY_SIZE = 5MB`

### PT-FILE-03 — Path traversal en nombre de archivo
- **Descripción:** Verificar que nombres de archivo con `../` no escriban fuera de `/media/`.
- **Pasos:**
  ```bash
  # Renombrar archivo localmente con path traversal
  cp test.jpg "../../evil.jpg"
  curl -X POST http://localhost:8000/api/pets/ \
    -H "Authorization: Bearer TOKEN" \
    -F "photo=@../../evil.jpg" \
    -F "name=TestPet" -F "type=Perro" -F "age=2"
  ```
- **Resultado esperado:** Archivo guardado dentro de `/media/`, no en directorios superiores

### PT-FILE-04 — Acceso a archivos de otros usuarios en /media/
- **Descripción:** Verificar si los archivos en `/media/` son accesibles sin autenticación por URL directa.
- **Pasos:** Conocer la URL de una foto subida por otro usuario y acceder directamente.
- **Resultado esperado idealmente:** Requiere autenticación. En la implementación actual Django sirve `/media/` estáticamente, lo que puede ser un riesgo en producción.

---

## 6. Validación de Entradas

### PT-INPUT-01 — XSS en campos de texto
- **Descripción:** Verificar que el contenido malicioso se almacene escapado y no ejecute scripts.
- **Pasos:**
  ```bash
  curl -X POST http://localhost:8000/api/pets/ \
    -H "Authorization: Bearer TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"<script>alert(1)</script>","type":"Perro","age":2}'
  ```
- **Resultado esperado:** El dato se almacena como texto literal, nunca se ejecuta en el navegador.

### PT-INPUT-02 — Inyección de coordenadas en ubicación
- **Descripción:** El campo `ubicación` se parsea con `split(',')` y `float()`. Verificar manejo de valores inválidos.
- **Pasos:**
  ```bash
  # Coordenadas inválidas
  curl -X PATCH http://localhost:8000/api/auth/users/actualizar_perfil/ \
    -H "Authorization: Bearer TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"ubicación": "abc,xyz"}'

  # Coordenadas fuera de rango
  curl -X PATCH http://localhost:8000/api/auth/users/actualizar_perfil/ \
    -H "Authorization: Bearer TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"ubicación": "999999,999999"}'

  # Intentar SQL en el campo (ORM debería proteger)
  curl -X PATCH http://localhost:8000/api/auth/users/actualizar_perfil/ \
    -H "Authorization: Bearer TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"ubicación": "0,0; DROP TABLE dueños--"}'
  ```
- **Resultado esperado:** `400` para inválidos, `200` para el SQL (el ORM lo parametriza automáticamente)
- **Archivo:** `matches_app/views.py:90` — bloque `except (ValueError, AttributeError, TypeError)`

### PT-INPUT-03 — Valores extremos en edad de mascota
- **Descripción:** Verificar que los validadores de rango funcionen correctamente.
- **Pasos:**
  ```bash
  curl -X POST http://localhost:8000/api/pets/ \
    -H "Authorization: Bearer TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test","type":"Perro","age":99999}'

  curl -X POST http://localhost:8000/api/pets/ \
    -H "Authorization: Bearer TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"name":"Test","type":"Perro","age":-5}'
  ```
- **Resultado esperado:** `400 Bad Request`
- **Archivo:** `pets_app/models.py:18` — `MinValueValidator(0), MaxValueValidator(30)`

### PT-INPUT-04 — Payload JSON masivo
- **Descripción:** Verificar que el servidor no se bloquee con payloads excesivamente grandes.
- **Pasos:**
  ```bash
  python -c "import json; print(json.dumps({'name': 'A'*100000, 'type':'Perro','age':1}))" | \
    curl -X POST http://localhost:8000/api/pets/ \
      -H "Authorization: Bearer TOKEN" \
      -H "Content-Type: application/json" \
      -d @-
  ```
- **Resultado esperado:** `400` o `413`, no `500` ni timeout indefinido

### PT-INPUT-05 — Número de mascotas por usuario (límite: 5)
- **Descripción:** Verificar que no se puedan registrar más de 5 mascotas por dueño.
- **Pasos:** Crear 6 mascotas con el mismo usuario.
- **Resultado esperado:** La 6ª devuelve `400 Bad Request`
- **Archivo:** `pets_app/models.py:36-39`

---

## 7. WebSocket

### PT-WS-01 — Conexión WebSocket sin token
- **Descripción:** Verificar que el WS rechace conexiones no autenticadas.
- **Pasos:**
  ```javascript
  const ws = new WebSocket('ws://localhost:8000/ws/chat/1/');
  ws.onopen = () => {
    // No enviar token — esperar cierre
  };
  ws.onclose = (e) => console.log('Cerrado:', e.code, e.reason);
  ```
- **Resultado esperado:** Conexión cerrada con código `4001` o similar

### PT-WS-02 — Primer mensaje con token inválido
- **Descripción:** La autenticación WS ocurre en el primer mensaje. Verificar que tokens forjados sean rechazados.
- **Pasos:**
  ```javascript
  const ws = new WebSocket('ws://localhost:8000/ws/chat/1/');
  ws.onopen = () => {
    ws.send(JSON.stringify({ token: 'token_completamente_inventado' }));
  };
  ```
- **Resultado esperado:** Conexión cerrada tras el primer mensaje inválido

### PT-WS-03 — IDOR en WebSocket (unirse a chat ajeno)
- **Descripción:** Verificar que un usuario no pueda leer/enviar mensajes en el canal de un match ajeno.
- **Pasos:**
  ```javascript
  // Usuario C intenta conectarse al canal del match entre A y B
  const ws = new WebSocket('ws://localhost:8000/ws/chat/{match_id_entre_A_y_B}/');
  ws.onopen = () => {
    ws.send(JSON.stringify({ token: TOKEN_USUARIO_C }));
  };
  ```
- **Resultado esperado:** Conexión cerrada, el usuario C no recibe ni envía mensajes

### PT-WS-04 — Token expirado en WebSocket
- **Descripción:** Verificar que un token expirado no pueda autenticar una conexión WS.
- **Pasos:** Usar un token con `created` modificado a > 7 días en la conexión WS.
- **Resultado esperado:** Conexión rechazada

---

## 8. Cabeceras HTTP de Seguridad

### PT-HDR-01 — Verificar cabeceras de seguridad presentes
- **Descripción:** Confirmar que todas las cabeceras de seguridad requeridas por la guía estén configuradas.
- **Pasos:**
  ```bash
  curl -I http://localhost:8000/api/auth/login/
  ```
- **Cabeceras esperadas:**

  | Cabecera | Valor esperado | Estado actual |
  |---|---|---|
  | `X-Content-Type-Options` | `nosniff` | ✅ Configurada |
  | `X-Frame-Options` | `DENY` | ✅ Configurada |
  | `X-XSS-Protection` | `1; mode=block` | ✅ Configurada |
  | `Content-Security-Policy` | Directivas restrictivas | ❌ No configurada |
  | `Strict-Transport-Security` | `max-age=31536000` | ❌ Solo en HTTPS/prod |
  | `Referrer-Policy` | `no-referrer` | ❌ No configurada |

- **Archivo:** `settings.py:175-177`

---

## 9. CORS

### PT-CORS-01 — Origen no permitido bloqueado
- **Descripción:** Verificar que orígenes no listados en `CORS_ALLOWED_ORIGINS` sean rechazados.
- **Pasos:**
  ```bash
  curl -s -I -H "Origin: http://evil.com" \
    -H "Authorization: Bearer TOKEN" \
    http://localhost:8000/api/pets/my-pets/
  ```
- **Resultado esperado:** La respuesta NO incluye `Access-Control-Allow-Origin: http://evil.com`
- **Archivo:** `settings.py:131-134` — solo permite `localhost:5173`

### PT-CORS-02 — Preflight con origen malicioso
- **Descripción:** Verificar que el preflight OPTIONS también rechace orígenes no autorizados.
- **Pasos:**
  ```bash
  curl -X OPTIONS \
    -H "Origin: http://attacker.com" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: Authorization,Content-Type" \
    http://localhost:8000/api/auth/login/
  ```
- **Resultado esperado:** Sin `Access-Control-Allow-Origin` en la respuesta

### PT-CORS-03 — Verificar que no exista wildcard
- **Descripción:** Confirmar que en ningún caso se responda con `Access-Control-Allow-Origin: *`.
- **Pasos:** Revisar todas las respuestas de los pasos anteriores.
- **Resultado esperado:** Nunca se debe ver `*` como origen permitido

---

## 10. Enumeración e Information Disclosure

### PT-INFO-01 — Enumeración de usuarios por timing en login
- **Descripción:** Verificar que la respuesta no revele si un email existe o no en el sistema.
- **Pasos:**
  ```bash
  # Email que existe
  time curl -s -X POST http://localhost:8000/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email":"usuario_real@test.com","password":"contrasena_incorrecta"}'

  # Email que NO existe
  time curl -s -X POST http://localhost:8000/api/auth/login/ \
    -H "Content-Type: application/json" \
    -d '{"email":"noexiste_zxzxzx@test.com","password":"contrasena_incorrecta"}'
  ```
- **Resultado esperado:** Mismo mensaje de error, tiempos de respuesta similares
- **Archivo:** `auth_app/views.py:104-106` — `login_fallo` no registra el email

### PT-INFO-02 — Stack traces en producción
- **Descripción:** Verificar que `DEBUG=False` evite la exposición de stack traces al cliente.
- **Pasos:**
  1. Configurar `.env` con `DEBUG=False`.
  2. Provocar un error (enviar JSON malformado, campos faltantes, etc.).
  3. Verificar que la respuesta solo contenga el mensaje genérico.
- **Resultado esperado:** `{"error": "Error interno del servidor"}` sin detalles técnicos
- **Archivo:** `PawMatch/exception_handler.py:26-31`

### PT-INFO-03 — Headers que revelan versión del servidor
- **Descripción:** Verificar que la respuesta no incluya `Server: Django/4.2` ni `X-Powered-By`.
- **Pasos:**
  ```bash
  curl -I http://localhost:8000/api/auth/login/
  ```
- **Resultado esperado:** Sin headers que revelen tecnología o versión exacta

---

## 11. Lógica de Negocio

### PT-BIZ-01 — Self-like (like a sí mismo)
- **Descripción:** Un usuario no debe poder dar like a su propia mascota.
- **Pasos:**
  ```bash
  curl -X POST http://localhost:8000/api/matches/like/ \
    -H "Authorization: Bearer TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"pet_id": ID_MI_MASCOTA, "target_pet_id": ID_MI_MASCOTA}'
  ```
- **Resultado esperado:** `400 Bad Request — No puedes hacer match contigo mismo`
- **Archivo:** `matches_app/views.py:227-229`

### PT-BIZ-02 — Match forzado sin like mutuo
- **Descripción:** Verificar que no se pueda crear un match con estado `Aceptado` directamente.
- **Pasos:**
  ```bash
  curl -X POST http://localhost:8000/api/matches/ \
    -H "Authorization: Bearer TOKEN" \
    -H "Content-Type: application/json" \
    -d '{"mascota1": ID_A, "mascota2": ID_B, "estado": "Aceptado"}'
  ```
- **Resultado esperado:** `400` o el estado `Aceptado` es ignorado

### PT-BIZ-03 — Spam de reportes
- **Descripción:** Verificar si existe un límite en la cantidad de reportes que un usuario puede enviar.
- **Pasos:**
  ```bash
  for i in $(seq 1 20); do
    curl -s -o /dev/null -w "%{http_code}\n" \
      -X POST http://localhost:8000/api/matches/reportes/ \
      -H "Authorization: Bearer TOKEN" \
      -H "Content-Type: application/json" \
      -d '{"motivo":"Spam","mascota": ID_MASCOTA}'
  done
  ```
- **Resultado esperado:** Limitado tras N reportes (actualmente no hay límite — riesgo identificado)

### PT-BIZ-04 — Limit bypass en actividad reciente
- **Descripción:** El endpoint `activity` acepta un parámetro `limit` con máximo de 100. Verificar que se respete.
- **Pasos:**
  ```bash
  curl "http://localhost:8000/api/matches/activity/?limit=99999" \
    -H "Authorization: Bearer TOKEN"
  ```
- **Resultado esperado:** Devuelve máximo 100 registros
- **Archivo:** `matches_app/views.py:397` — `limit = min(int(...), 100)`

---

## 12. Bitácora de Base de Datos

### PT-LOG-01 — Cobertura de eventos de autenticación
- **Descripción:** Verificar que los eventos de auth se registren correctamente en `BitacoraEvento`.
- **Pasos:**
  1. Ejecutar login exitoso, login fallido, registro, logout.
  2. Consultar en MySQL: `SELECT accion, ip_address, fecha FROM bitacora_eventos ORDER BY fecha DESC LIMIT 10;`
- **Resultado esperado:** Todos los eventos aparecen con IP y fecha correctas

### PT-LOG-02 — Eventos de negocio NO registrados (brecha identificada)
- **Descripción:** Confirmar que los siguientes eventos definidos en el modelo nunca se registran.
- **Verificación en MySQL:**
  ```sql
  SELECT accion, COUNT(*) FROM bitacora_eventos
  WHERE accion IN ('mascota_creada','mascota_eliminada','like_enviado','match_formado','mensaje_enviado','acceso_denegado')
  GROUP BY accion;
  ```
- **Resultado esperado (brecha):** 0 registros en todas esas categorías
- **Impacto:** Sin trazabilidad de las acciones principales de la app

### PT-LOG-03 — PII en archivos de log
- **Descripción:** Verificar que el archivo `security.log` no contenga emails en texto plano.
- **Pasos:**
  ```bash
  grep -E "@.*\." logs/security.log | head -5
  ```
- **Resultado esperado (brecha):** Se encontrarán emails — `audit.py:38` los escribe explícitamente
- **Archivo:** `auth_app/audit.py:38` — `getattr(user, 'email', 'anónimo')`

### PT-LOG-04 — IP falsa en bitácora via X-Forwarded-For
- **Descripción:** Verificar que la IP registrada pueda ser falsificada.
- **Pasos:**
  ```bash
  curl -X POST http://localhost:8000/api/auth/login/ \
    -H "Content-Type: application/json" \
    -H "X-Forwarded-For: 1.2.3.4" \
    -d '{"email":"test@test.com","password":"Pass1234!"}'
  ```
  Luego: `SELECT ip_address FROM bitacora_eventos ORDER BY fecha DESC LIMIT 1;`
- **Resultado esperado (brecha):** La IP registrada es `1.2.3.4` (falsificada)
- **Archivo:** `auth_app/audit.py:12-15`

---

## 13. Cifrado de Datos

### PT-CRYPT-01 — Contraseñas hasheadas con PBKDF2
- **Descripción:** Verificar que las contraseñas no se almacenen en texto plano.
- **Pasos:**
  ```sql
  SELECT email, contraseña FROM dueños LIMIT 3;
  ```
- **Resultado esperado:** `pbkdf2_sha256$...` — nunca texto plano

### PT-CRYPT-02 — Datos PII en texto plano (brecha identificada)
- **Descripción:** Verificar que campos sensibles no estén cifrados a nivel de campo.
- **Pasos:**
  ```sql
  SELECT email, telefono, ubicación, fecha_nacimiento FROM dueños LIMIT 3;
  ```
- **Resultado esperado (brecha):** Todos los campos visibles en texto plano

### PT-CRYPT-03 — Mensajes de chat en texto plano (brecha identificada)
- **Descripción:** Verificar que el contenido de los mensajes no esté cifrado.
- **Pasos:**
  ```sql
  SELECT contenido FROM mensajes LIMIT 5;
  ```
- **Resultado esperado (brecha):** Mensajes legibles directamente en la BD

### PT-CRYPT-04 — Conexión a MySQL sin TLS
- **Descripción:** Verificar si la conexión entre Django y MySQL usa cifrado en tránsito.
- **Pasos:**
  ```bash
  # En MySQL
  SHOW STATUS LIKE 'Ssl_cipher';
  ```
- **Resultado esperado (brecha en prod):** `Ssl_cipher` vacío indica conexión sin TLS

---

## 14. Configuración del Entorno

### PT-ENV-01 — Credenciales hardcodeadas en settings.py
- **Descripción:** Verificar que no existan contraseñas con fallback hardcodeado en el código.
- **Verificación:**
  ```bash
  grep -n "default='.*'" PawMatch/settings.py | grep -i "pass\|secret\|key\|token"
  ```
- **Resultado esperado (brecha):** `settings.py:93` — `'PASSWORD': os.environ.get('DATABASE_PASSWORD', 'pablito2907')`

### PT-ENV-02 — DEBUG=True accidentalmente en producción
- **Descripción:** Verificar que el servidor no arranque si `DEBUG=True` con `ALLOWED_HOSTS` en producción.
- **Pasos:** Revisar que `settings.py` valide la combinación `DEBUG=True` + hosts de producción.

### PT-ENV-03 — .env commiteado al repositorio
- **Descripción:** Verificar que el archivo `.env` real no esté en el historial de git.
- **Pasos:**
  ```bash
  git log --all --full-history -- .env
  git grep -l "DATABASE_PASSWORD" $(git rev-list --all)
  ```
- **Resultado esperado:** Sin commits que incluyan el `.env` real

### PT-ENV-04 — Ausencia de .env.example
- **Descripción:** Verificar la ausencia de plantilla de variables de entorno (brecha identificada).
- **Resultado esperado (brecha):** No existe `.env.example` en el repositorio

---

## 15. Resumen de Prioridades

### Alta — Deben corregirse antes de cualquier despliegue

| ID | Hallazgo | Archivo |
|---|---|---|
| PT-IDOR-01 a 04 | IDOR en pets/matches/chat | `*/views.py` |
| PT-WS-01 a 03 | WebSocket sin autenticación verificada | `chat_app/consumers.py` |
| PT-ENV-01 | Contraseña de BD hardcodeada en `settings.py` | `settings.py:93` |
| PT-LOG-03 | Emails (PII) escritos en `security.log` | `audit.py:38` |
| PT-OAUTH-01 | Token OAuth inválido podría crear cuenta | `serializers.py:123` |

### Media — Corregir antes de fase beta

| ID | Hallazgo | Archivo |
|---|---|---|
| PT-RATE-02 | Bypass de rate limiting via X-Forwarded-For | `audit.py:12` |
| PT-FILE-01 a 03 | Validación insuficiente de archivos subidos | `pets_app/views.py` |
| PT-LOG-02 | 6 eventos de negocio definidos pero nunca registrados | `auth_app/models.py` |
| PT-LOG-04 | IP falsificable en bitácora | `audit.py:12` |
| PT-HDR-01 | `Content-Security-Policy` ausente | `settings.py` |
| PT-ENV-04 | Sin `.env.example` | — |
| PT-BIZ-03 | Sin límite de reportes por usuario | `matches_app/views.py` |

### Baja — Mejoras recomendadas

| ID | Hallazgo | Archivo |
|---|---|---|
| PT-CRYPT-02 | Teléfono y ubicación en texto plano en BD | `auth_app/models.py` |
| PT-CRYPT-03 | Mensajes de chat sin cifrado | `chat_app/models.py` |
| PT-CRYPT-04 | Conexión MySQL sin TLS | `settings.py:96` |
| PT-INFO-03 | Headers que revelan versión del servidor | Middleware |
| PT-IDOR-06 | IDs secuenciales predecibles | Todos los modelos |
| PT-AUTH-01 | Sin `Content-Security-Policy` en frontend | `settings.py` |

---

## Herramientas recomendadas

| Herramienta | Propósito | Comando |
|---|---|---|
| `bandit` | SAST — análisis estático Python | `pip install bandit && bandit -r . -x venv` |
| `safety` | Dependencias Python con CVEs | `pip install safety && safety check` |
| `npm audit` | Dependencias JS vulnerables | `npm audit --production` |
| `OWASP ZAP` | DAST — escaneo dinámico de la API | Interfaz gráfica o CLI |
| `pytest-django` | Tests de integración con BD real | `pip install pytest-django pytest-cov` |

---

*Documento generado el 2026-04-14. Basado en revisión del código fuente de PawMatch y la Guía de Desarrollo Seguro del equipo 404 Not Found.*
