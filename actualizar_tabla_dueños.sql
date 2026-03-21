-- Script completo para actualizar la tabla dueños con todos los campos necesarios
-- Ejecutar en MySQL

USE PawMatch;

-- Agregar campo last_login (requerido por AbstractBaseUser de Django)
-- Si la columna ya existe, este comando fallará, pero puedes ignorarlo
ALTER TABLE dueños ADD COLUMN last_login DATETIME NULL;

-- Agregar campos requeridos por Django para AbstractBaseUser
ALTER TABLE dueños ADD COLUMN is_active BOOLEAN DEFAULT TRUE;
ALTER TABLE dueños ADD COLUMN is_staff BOOLEAN DEFAULT FALSE;
ALTER TABLE dueños ADD COLUMN is_superuser BOOLEAN DEFAULT FALSE;

-- Agregar campos de perfil
ALTER TABLE dueños ADD COLUMN foto_perfil VARCHAR(255) NULL;
ALTER TABLE dueños ADD COLUMN telefono VARCHAR(15) NULL;
ALTER TABLE dueños ADD COLUMN biografia TEXT NULL;
ALTER TABLE dueños ADD COLUMN fecha_nacimiento DATE NULL;
ALTER TABLE dueños ADD COLUMN genero VARCHAR(20) NULL;
ALTER TABLE dueños ADD COLUMN ciudad VARCHAR(100) NULL;
ALTER TABLE dueños ADD COLUMN estado VARCHAR(100) NULL;
ALTER TABLE dueños ADD COLUMN pais VARCHAR(100) NULL;
ALTER TABLE dueños ADD COLUMN mostrar_telefono BOOLEAN DEFAULT FALSE;
ALTER TABLE dueños ADD COLUMN mostrar_email BOOLEAN DEFAULT FALSE;

-- Verificar estructura de la tabla
DESCRIBE dueños;
