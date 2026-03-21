-- Script para agregar los campos requeridos por Django a la tabla dueños
-- Ejecutar en MySQL

USE PawMatch;

-- Agregar campo last_login (requerido por AbstractBaseUser)
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS last_login DATETIME NULL;

-- Si MySQL no soporta IF NOT EXISTS, usar:
-- ALTER TABLE dueños ADD COLUMN last_login DATETIME NULL;

-- Agregar campos de perfil si no existen
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS foto_perfil VARCHAR(255) NULL;
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS telefono VARCHAR(15) NULL;
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS biografia TEXT NULL;
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS fecha_nacimiento DATE NULL;
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS genero VARCHAR(20) NULL;
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS ciudad VARCHAR(100) NULL;
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS estado VARCHAR(100) NULL;
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS pais VARCHAR(100) NULL;
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS mostrar_telefono BOOLEAN DEFAULT FALSE;
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS mostrar_email BOOLEAN DEFAULT FALSE;

-- Agregar campos requeridos por Django para AbstractBaseUser
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS is_staff BOOLEAN DEFAULT FALSE;
ALTER TABLE dueños ADD COLUMN IF NOT EXISTS is_superuser BOOLEAN DEFAULT FALSE;
