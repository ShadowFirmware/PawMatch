CREATE DATABASE PawMatch;
USE PawMatch;

-- Tabla de dueños
CREATE TABLE dueños (
    dueño_id INT AUTO_INCREMENT PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    contraseña VARCHAR(255) NOT NULL, -- Encriptada
    ubicación VARCHAR(255) NOT NULL, -- Ej: "19.4326,-99.1332"
    fecha_registro DATETIME DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_ubicacion (ubicación)
);

-- Tabla de mascotas (con límite de 5 por dueño)
CREATE TABLE mascotas (
    mascota_id INT AUTO_INCREMENT PRIMARY KEY,
    dueño_id INT NOT NULL,
    nombre VARCHAR(100) NOT NULL,
    especie VARCHAR(50) NOT NULL,
    raza VARCHAR(50),
    edad INT,
    género ENUM('Macho', 'Hembra', 'Otro') NOT NULL,
    descripción TEXT,
    foto_url VARCHAR(255) NOT NULL,
    FOREIGN KEY (dueño_id) REFERENCES dueños(dueño_id) ON DELETE CASCADE,
    INDEX idx_especie (especie),
    INDEX idx_edad (edad),
    INDEX idx_género (género)
);

-- Trigger para limitar a 5 mascotas por dueño
DELIMITER //
CREATE TRIGGER check_mascotas_limit
BEFORE INSERT ON mascotas
FOR EACH ROW
BEGIN
    DECLARE mascotas_count INT;
    SELECT COUNT(*) INTO mascotas_count
    FROM mascotas
    WHERE dueño_id = NEW.dueño_id;

    IF mascotas_count >= 5 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'No puedes registrar más de 5 mascotas por dueño.';
    END IF;
END//
DELIMITER ;

-- Tabla de fotos de mascotas
CREATE TABLE fotos_mascotas (
    foto_id INT AUTO_INCREMENT PRIMARY KEY,
    mascota_id INT NOT NULL,
    foto_url VARCHAR(255) NOT NULL,
    es_principal BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(mascota_id) ON DELETE CASCADE
);

-- Tabla de preferencias
CREATE TABLE preferencias (
    pref_id INT AUTO_INCREMENT PRIMARY KEY,
    dueño_id INT NOT NULL,
    especie_pref VARCHAR(50) NOT NULL, -- Ej: "Perro,Gato"
    edad_pref_min INT,
    edad_pref_max INT,
    género_pref ENUM('Macho', 'Hembra', 'Indistinto') NOT NULL,
    distancia_max INT NOT NULL, -- En kilómetros
    FOREIGN KEY (dueño_id) REFERENCES dueños(dueño_id) ON DELETE CASCADE
);

-- Tabla de matches
CREATE TABLE matches (
    match_id INT AUTO_INCREMENT PRIMARY KEY,
    mascota1_id INT NOT NULL,
    mascota2_id INT NOT NULL,
    fecha_match DATETIME DEFAULT CURRENT_TIMESTAMP,
    estado ENUM('Pendiente', 'Aceptado', 'Rechazado') DEFAULT 'Pendiente',
    FOREIGN KEY (mascota1_id) REFERENCES mascotas(mascota_id) ON DELETE CASCADE,
    FOREIGN KEY (mascota2_id) REFERENCES mascotas(mascota_id) ON DELETE CASCADE,
    UNIQUE KEY unique_match (mascota1_id, mascota2_id) -- Evita duplicados
);

-- Tabla de mensajes
CREATE TABLE mensajes (
    msg_id INT AUTO_INCREMENT PRIMARY KEY,
    match_id INT NOT NULL,
    remitente_id INT NOT NULL, -- dueño_id del remitente
    contenido TEXT NOT NULL,
    fecha_envío DATETIME DEFAULT CURRENT_TIMESTAMP,
    leído BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (match_id) REFERENCES matches(match_id) ON DELETE CASCADE,
    FOREIGN KEY (remitente_id) REFERENCES dueños(dueño_id) ON DELETE CASCADE
);

-- Tabla de reportes
CREATE TABLE reportes (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    dueño_id INT NOT NULL, -- Dueño que reporta
    mascota_id INT NOT NULL, -- Mascota reportada
    motivo TEXT NOT NULL,
    fecha_reporte DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (dueño_id) REFERENCES dueños(dueño_id) ON DELETE CASCADE,
    FOREIGN KEY (mascota_id) REFERENCES mascotas(mascota_id) ON DELETE CASCADE
);