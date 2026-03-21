-- Script para agregar los campos de perfil a la tabla dueños
-- Ejecutar si las columnas no existen aún

USE PawMatch;

-- Agregar columnas de perfil a la tabla dueños (solo si no existen)
ALTER TABLE dueños 
ADD COLUMN IF NOT EXISTS foto_perfil VARCHAR(255) NULL AFTER fecha_registro,
ADD COLUMN IF NOT EXISTS telefono VARCHAR(15) NULL AFTER foto_perfil,
ADD COLUMN IF NOT EXISTS biografia TEXT NULL AFTER telefono,
ADD COLUMN IF NOT EXISTS fecha_nacimiento DATE NULL AFTER biografia,
ADD COLUMN IF NOT EXISTS genero VARCHAR(20) NULL AFTER fecha_nacimiento,
ADD COLUMN IF NOT EXISTS ciudad VARCHAR(100) NULL AFTER genero,
ADD COLUMN IF NOT EXISTS estado VARCHAR(100) NULL AFTER ciudad,
ADD COLUMN IF NOT EXISTS pais VARCHAR(100) NULL AFTER estado,
ADD COLUMN IF NOT EXISTS mostrar_telefono BOOLEAN DEFAULT FALSE AFTER pais,
ADD COLUMN IF NOT EXISTS mostrar_email BOOLEAN DEFAULT FALSE AFTER mostrar_telefono;

-- Si MySQL no soporta IF NOT EXISTS, usar este script alternativo:
-- ALTER TABLE dueños ADD COLUMN foto_perfil VARCHAR(255) NULL;
-- ALTER TABLE dueños ADD COLUMN telefono VARCHAR(15) NULL;
-- ALTER TABLE dueños ADD COLUMN biografia TEXT NULL;
-- ALTER TABLE dueños ADD COLUMN fecha_nacimiento DATE NULL;
-- ALTER TABLE dueños ADD COLUMN genero VARCHAR(20) NULL;
-- ALTER TABLE dueños ADD COLUMN ciudad VARCHAR(100) NULL;
-- ALTER TABLE dueños ADD COLUMN estado VARCHAR(100) NULL;
-- ALTER TABLE dueños ADD COLUMN pais VARCHAR(100) NULL;
-- ALTER TABLE dueños ADD COLUMN mostrar_telefono BOOLEAN DEFAULT FALSE;
-- ALTER TABLE dueños ADD COLUMN mostrar_email BOOLEAN DEFAULT FALSE;
