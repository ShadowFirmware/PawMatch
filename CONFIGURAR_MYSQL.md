# 🔧 Configuración de MySQL para PawMatch

## Problema Actual

El error indica que MySQL está rechazando la conexión porque requiere una contraseña para el usuario 'root':

```
Access denied for user 'root'@'localhost' (using password: NO)
```

## Soluciones

### Opción 1: Configurar Contraseña en Variables de Entorno (Recomendado)

1. **Crea un archivo `.env` en la raíz del proyecto** (`C:\Users\luisp\PawMatch\.env`):

```env
DATABASE_NAME=PawMatch
DATABASE_USER=root
DATABASE_PASSWORD=tu_contraseña_aqui
DATABASE_HOST=localhost
DATABASE_PORT=3306
```

2. **Instala python-dotenv** (si aún no lo tienes):

```bash
pip install python-dotenv
```

3. **Agrega al inicio de `PawMatch/settings.py`**:

```python
from dotenv import load_dotenv
load_dotenv()
```

### Opción 2: Configurar Directamente en settings.py

Edita `PawMatch/settings.py` y cambia la contraseña:

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': 'PawMatch',
        'USER': 'root',
        'PASSWORD': 'tu_contraseña_aqui',  # ← Cambia esto
        'HOST': 'localhost',
        'PORT': '3306',
    }
}
```

### Opción 3: Si MySQL no tiene contraseña (No recomendado para producción)

Si realmente no tienes contraseña configurada en MySQL, puedes:

1. **Verificar si MySQL está corriendo:**
   ```bash
   # En Windows, verifica en el Administrador de Tareas
   # O intenta conectarte con:
   mysql -u root
   ```

2. **Si necesitas crear una contraseña para root:**
   ```sql
   ALTER USER 'root'@'localhost' IDENTIFIED BY 'tu_nueva_contraseña';
   FLUSH PRIVILEGES;
   ```

## Verificar Conexión a MySQL

Antes de ejecutar las migraciones, verifica que puedes conectarte:

```bash
mysql -u root -p
```

Si te pide contraseña, ingrésala. Si no te pide contraseña, entonces MySQL está configurado sin contraseña y deberías usar la Opción 2 con `'PASSWORD': ''`.

## Crear la Base de Datos

Si la base de datos `PawMatch` no existe, créala:

```sql
CREATE DATABASE PawMatch CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

## Ejecutar Migraciones

Una vez configurada la contraseña correctamente:

```bash
py manage.py migrate
```

## Troubleshooting

### Error: "Can't connect to MySQL server"
- Verifica que MySQL esté corriendo
- Verifica que el puerto 3306 esté disponible
- Verifica el HOST (debe ser 'localhost' o '127.0.0.1')

### Error: "Unknown database 'PawMatch'"
- Crea la base de datos primero (ver arriba)

### Error: "Access denied"
- Verifica que el usuario y contraseña sean correctos
- Verifica que el usuario tenga permisos en la base de datos:
  ```sql
  GRANT ALL PRIVILEGES ON PawMatch.* TO 'root'@'localhost';
  FLUSH PRIVILEGES;
  ```
