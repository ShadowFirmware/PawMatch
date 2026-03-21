# 🔧 Solución Error 500 en Login con Google

## Problema

Error 500 al intentar iniciar sesión con Google. El error probablemente se debe a que la tabla `perfiles` no existe en la base de datos.

## Solución

### Opción 1: Crear la tabla de perfiles manualmente (Recomendado)

Ejecuta este SQL en MySQL:

```sql
USE PawMatch;

-- Tabla de perfiles de usuarios
CREATE TABLE IF NOT EXISTS perfiles (
    perfil_id INT AUTO_INCREMENT PRIMARY KEY,
    dueño_id INT NOT NULL UNIQUE,
    foto_perfil VARCHAR(255) NULL,
    telefono VARCHAR(15) NULL,
    biografia TEXT NULL,
    fecha_nacimiento DATE NULL,
    genero VARCHAR(20) NULL,
    ciudad VARCHAR(100) NULL,
    estado VARCHAR(100) NULL,
    pais VARCHAR(100) NULL,
    fecha_actualizacion DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    mostrar_telefono BOOLEAN DEFAULT FALSE,
    mostrar_email BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (dueño_id) REFERENCES dueños(dueño_id) ON DELETE CASCADE,
    INDEX idx_ciudad (ciudad),
    INDEX idx_estado (estado)
);
```

### Opción 2: Ejecutar el script SQL

Ejecuta el archivo `add_perfiles_table.sql` que ya está creado:

```bash
mysql -u root -p PawMatch < add_perfiles_table.sql
```

### Opción 3: Crear migración de Django

Si prefieres usar Django:

```bash
py manage.py makemigrations auth_app
py manage.py migrate auth_app
```

## Verificar que funcionó

Después de crear la tabla, prueba nuevamente el login con Google. El error 500 debería desaparecer.

## Cambios realizados en el código

1. ✅ Mejorado el manejo de errores en `google_auth_view`
2. ✅ Agregado logging para identificar problemas
3. ✅ El sistema ahora puede funcionar aunque falle la creación del perfil (se creará después)

## Si el error persiste

Revisa los logs del servidor Django para ver el error específico:

```bash
py manage.py runserver
```

Y revisa la consola del navegador para ver el mensaje de error completo.
