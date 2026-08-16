-- 1. Tabla de Territorios
CREATE TABLE IF NOT EXISTS territorios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    numero TEXT NOT NULL UNIQUE,
    estado TEXT CHECK(estado IN ('Disponible', 'En trabajo')) DEFAULT 'Disponible'
);

-- 2. Tabla de Responsables (sin login/password)
CREATE TABLE IF NOT EXISTS responsables (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    activo INTEGER DEFAULT 1, -- 1: activo, 0: inactivo
    telefono TEXT DEFAULT NULL,
    email TEXT DEFAULT NULL,
    fecha_alta TEXT DEFAULT NULL
);

-- 3. Tabla de Registros Telefónicos
CREATE TABLE IF NOT EXISTS registros (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    territorio_id INTEGER NOT NULL,
    direccion TEXT,
    telefono TEXT NOT NULL,
    observaciones TEXT,
    no_llamar INTEGER DEFAULT 0,  -- 0: False, 1: True
    funcionan INTEGER DEFAULT NULL, -- NULL: Vacío, 1: Sí, 0: No
    notas_internas TEXT,
    FOREIGN KEY (territorio_id) REFERENCES territorios(id) ON DELETE CASCADE,
    UNIQUE(territorio_id, direccion, telefono) -- Evita duplicados en importaciones
);

-- 4. Tabla de Asignaciones (Histórico de estados)
CREATE TABLE IF NOT EXISTS asignaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    territorio_id INTEGER NOT NULL,
    responsable_id INTEGER NOT NULL,
    fecha_asignado TEXT NOT NULL,      -- Formato ISO: YYYY-MM-DD HH:MM:SS
    fecha_finalizacion TEXT DEFAULT NULL,
    detalles TEXT,
    FOREIGN KEY (territorio_id) REFERENCES territorios(id),
    FOREIGN KEY (responsable_id) REFERENCES responsables(id)
);

-- 5. Tabla de Actividad / Auditoría
CREATE TABLE IF NOT EXISTS actividad (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    territorio_id INTEGER,
    registro_id INTEGER,
    responsable_id INTEGER,
    tipo TEXT NOT NULL,               -- Ej: 'EDICION', 'ASIGNACION', 'FINALIZACION'
    descripcion TEXT NOT NULL,
    fecha TEXT NOT NULL,
    FOREIGN KEY (territorio_id) REFERENCES territorios(id),
    FOREIGN KEY (registro_id) REFERENCES registros(id)
);
