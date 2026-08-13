-- SISTEMA DE CONTROL ESCOLAR

-- Extensiones
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- 1. TABLA: periodo_academico
CREATE TABLE IF NOT EXISTS periodo_academico (
    id_periodo SERIAL PRIMARY KEY,
    nombre VARCHAR(50) NOT NULL,              -- Ej: "2025-2026"
    fecha_inicio DATE NOT NULL,
    fecha_fin DATE NOT NULL,
    activo BOOLEAN DEFAULT FALSE,             -- Solo un periodo activo a la vez
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. TABLA: grado
CREATE TABLE IF NOT EXISTS grado (
    id_grado SERIAL PRIMARY KEY,
    nombre VARCHAR(30) NOT NULL,              -- Ej: "1ro Primaria"
    nivel VARCHAR(20) NOT NULL,               -- "Primaria", "Secundaria", "Bachillerato"
    orden INTEGER NOT NULL                    -- Para ordenar: 1, 2, 3...
);

-- 3. TABLA: seccion
CREATE TABLE IF NOT EXISTS seccion (
    id_seccion SERIAL PRIMARY KEY,
    nombre VARCHAR(10) NOT NULL,              -- Ej: "A", "B", "C"
    id_grado INTEGER NOT NULL REFERENCES grado(id_grado) ON DELETE CASCADE,
    id_periodo INTEGER NOT NULL REFERENCES periodo_academico(id_periodo) ON DELETE CASCADE,
    capacidad_max INTEGER DEFAULT 30,
    UNIQUE (nombre, id_grado, id_periodo)
);

-- 4. TABLA: estudiante
CREATE TABLE IF NOT EXISTS estudiante (
    id_estudiante SERIAL PRIMARY KEY,
    cedula VARCHAR(15) UNIQUE NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    fecha_nacimiento DATE,
    genero VARCHAR(10),                       -- M / F
    direccion TEXT,
    telefono VARCHAR(15),
    email VARCHAR(100),
    nombre_representante VARCHAR(150),
    telefono_representante VARCHAR(15),
    id_seccion INTEGER REFERENCES seccion(id_seccion) ON DELETE SET NULL,
    fecha_inscripcion DATE DEFAULT CURRENT_DATE,
    activo BOOLEAN DEFAULT TRUE,
    codigo_qr VARCHAR(100) UNIQUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 5. TABLA: docente
CREATE TABLE IF NOT EXISTS docente (
    id_docente SERIAL PRIMARY KEY,
    cedula VARCHAR(15) UNIQUE NOT NULL,
    nombres VARCHAR(100) NOT NULL,
    apellidos VARCHAR(100) NOT NULL,
    especialidad VARCHAR(100),
    telefono VARCHAR(15),
    email VARCHAR(100),
    fecha_contratacion DATE,
    activo BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 6. TABLA: materia
CREATE TABLE IF NOT EXISTS materia (
    id_materia SERIAL PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL,
    codigo VARCHAR(20) UNIQUE,
    horas_semana INTEGER DEFAULT 0,
    id_docente INTEGER REFERENCES docente(id_docente) ON DELETE SET NULL,
    id_grado INTEGER REFERENCES grado(id_grado) ON DELETE SET NULL,
    descripcion TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 7. TABLA: horario (relación materia - sección)
CREATE TABLE IF NOT EXISTS horario (
    id_horario SERIAL PRIMARY KEY,
    id_materia INTEGER NOT NULL REFERENCES materia(id_materia) ON DELETE CASCADE,
    id_seccion INTEGER NOT NULL REFERENCES seccion(id_seccion) ON DELETE CASCADE,
    dia_semana VARCHAR(15) NOT NULL,          -- "Lunes", "Martes", ...
    hora_inicio TIME NOT NULL,
    hora_fin TIME NOT NULL,
    aula VARCHAR(20),
    CONSTRAINT chk_horario_horas CHECK (hora_fin > hora_inicio)
);

-- 8. TABLA: asistencia
CREATE TABLE IF NOT EXISTS asistencia (
    id_asistencia SERIAL PRIMARY KEY,
    id_estudiante INTEGER NOT NULL REFERENCES estudiante(id_estudiante) ON DELETE CASCADE,
    id_horario INTEGER REFERENCES horario(id_horario) ON DELETE SET NULL,
    id_seccion INTEGER REFERENCES seccion(id_seccion) ON DELETE SET NULL,
    fecha DATE NOT NULL,
    estado VARCHAR(15) NOT NULL,              -- 'Asistió', 'Tardanza', 'Falta', 'Justificado'
    observacion TEXT,
    registrado_por INTEGER,                   -- id_usuario
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id_estudiante, fecha)
);

-- 9. TABLA: calificacion
CREATE TABLE IF NOT EXISTS calificacion (
    id_calificacion SERIAL PRIMARY KEY,
    id_estudiante INTEGER NOT NULL REFERENCES estudiante(id_estudiante) ON DELETE CASCADE,
    id_materia INTEGER NOT NULL REFERENCES materia(id_materia) ON DELETE CASCADE,
    id_periodo INTEGER NOT NULL REFERENCES periodo_academico(id_periodo) ON DELETE CASCADE,
    nota1 DECIMAL(5,2),                       -- Primer parcial
    nota2 DECIMAL(5,2),                       -- Segundo parcial
    nota3 DECIMAL(5,2),                       -- Tercer parcial
    examen_final DECIMAL(5,2),
    nota_final DECIMAL(5,2),                  -- Promedio calculado
    observacion TEXT,
    registrado_por INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (id_estudiante, id_materia, id_periodo),
    CONSTRAINT chk_notas CHECK (
        (nota1 IS NULL OR (nota1 >= 0 AND nota1 <= 100)) AND
        (nota2 IS NULL OR (nota2 >= 0 AND nota2 <= 100)) AND
        (nota3 IS NULL OR (nota3 >= 0 AND nota3 <= 100)) AND
        (examen_final IS NULL OR (examen_final >= 0 AND examen_final <= 100))
    )
);

-- 10. TABLA: pago
CREATE TABLE IF NOT EXISTS pago (
    id_pago SERIAL PRIMARY KEY,
    id_estudiante INTEGER NOT NULL REFERENCES estudiante(id_estudiante) ON DELETE CASCADE,
    id_periodo INTEGER REFERENCES periodo_academico(id_periodo) ON DELETE SET NULL,
    concepto VARCHAR(100) DEFAULT 'Mensualidad',
    mes VARCHAR(20),
    anio INTEGER,
    monto DECIMAL(10,2) NOT NULL,
    fecha_pago DATE,
    fecha_vencimiento DATE,
    estado VARCHAR(15) DEFAULT 'Pendiente',   -- Pagado, Pendiente, Vencido, Parcial, Anulado
    metodo_pago VARCHAR(50),
    referencia VARCHAR(100),
    comprobante VARCHAR(255),                 -- Ruta del archivo PDF
    observacion TEXT,
    registrado_por INTEGER,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 11. TABLA: usuario
CREATE TABLE IF NOT EXISTS usuario (
    id_usuario SERIAL PRIMARY KEY,
    username VARCHAR(50) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    email VARCHAR(100),
    nombre_completo VARCHAR(150),
    rol VARCHAR(20) NOT NULL,                 -- admin, docente, secretaria, estudiante
    id_estudiante INTEGER REFERENCES estudiante(id_estudiante) ON DELETE SET NULL,
    id_docente INTEGER REFERENCES docente(id_docente) ON DELETE SET NULL,
    activo BOOLEAN DEFAULT TRUE,
    ultimo_acceso TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT chk_rol CHECK (rol IN ('admin', 'docente', 'secretaria', 'estudiante'))
);

-- ÍNDICES
CREATE INDEX IF NOT EXISTS idx_estudiante_cedula ON estudiante(cedula);
CREATE INDEX IF NOT EXISTS idx_estudiante_seccion ON estudiante(id_seccion);
CREATE INDEX IF NOT EXISTS idx_estudiante_activo ON estudiante(activo);
CREATE INDEX IF NOT EXISTS idx_docente_cedula ON docente(cedula);
CREATE INDEX IF NOT EXISTS idx_asistencia_fecha ON asistencia(fecha);
CREATE INDEX IF NOT EXISTS idx_asistencia_estudiante ON asistencia(id_estudiante);
CREATE INDEX IF NOT EXISTS idx_asistencia_seccion ON asistencia(id_seccion);
CREATE INDEX IF NOT EXISTS idx_calificacion_estudiante ON calificacion(id_estudiante);
CREATE INDEX IF NOT EXISTS idx_calificacion_materia ON calificacion(id_materia);
CREATE INDEX IF NOT EXISTS idx_calificacion_periodo ON calificacion(id_periodo);
CREATE INDEX IF NOT EXISTS idx_pago_estudiante ON pago(id_estudiante);
CREATE INDEX IF NOT EXISTS idx_pago_estado ON pago(estado);
CREATE INDEX IF NOT EXISTS idx_pago_mes_anio ON pago(mes, anio);
CREATE INDEX IF NOT EXISTS idx_usuario_username ON usuario(username);
CREATE INDEX IF NOT EXISTS idx_usuario_rol ON usuario(rol);
CREATE INDEX IF NOT EXISTS idx_horario_seccion ON horario(id_seccion);
CREATE INDEX IF NOT EXISTS idx_materia_docente ON materia(id_docente);
CREATE INDEX IF NOT EXISTS idx_seccion_periodo ON seccion(id_periodo);

-- DATOS INICIALES (SEED)
-- Solo Primaria 1ro-6to, secciones A y B.
-- Estudiantes, asistencias, calificaciones y pagos
-- se generan en setup_db.py para evitar duplicados.
INSERT INTO periodo_academico (nombre, fecha_inicio, fecha_fin, activo)
SELECT '2026-2027', '2026-01-15', '2026-12-20', TRUE
WHERE NOT EXISTS (SELECT 1 FROM periodo_academico WHERE nombre = '2026-2027');

INSERT INTO grado (nombre, nivel, orden)
SELECT v.nombre, v.nivel, v.orden FROM (VALUES
    ('1ro Primaria', 'Primaria', 1),
    ('2do Primaria', 'Primaria', 2),
    ('3ro Primaria', 'Primaria', 3),
    ('4to Primaria', 'Primaria', 4),
    ('5to Primaria', 'Primaria', 5),
    ('6to Primaria', 'Primaria', 6)
) AS v(nombre, nivel, orden)
WHERE NOT EXISTS (SELECT 1 FROM grado g WHERE g.nombre = v.nombre);

-- Solo secciones A y B de 1ro a 6to Primaria
INSERT INTO seccion (nombre, id_grado, id_periodo, capacidad_max)
SELECT v.nombre, g.id_grado, p.id_periodo, 30
FROM (VALUES ('A'), ('B')) AS v(nombre)
CROSS JOIN grado g
CROSS JOIN (SELECT id_periodo FROM periodo_academico WHERE nombre = '2026-2027' LIMIT 1) p
WHERE g.nivel = 'Primaria'
  AND NOT EXISTS (
    SELECT 1 FROM seccion s
    WHERE s.nombre = v.nombre AND s.id_grado = g.id_grado AND s.id_periodo = p.id_periodo
  );

INSERT INTO docente (cedula, nombres, apellidos, especialidad, telefono, email, fecha_contratacion) VALUES
    ('1234567890', 'Carlos', 'Gómez', 'Matemáticas', '0991111111', 'carlos.gomez@colegio.edu', '2020-02-01'),
    ('0987654321', 'María', 'Rodríguez', 'Lenguaje', '0992222222', 'maria.rodriguez@colegio.edu', '2019-03-15'),
    ('1122334455', 'Ana', 'Martínez', 'Ciencias', '0993333333', 'ana.martinez@colegio.edu', '2021-08-10'),
    ('5566778899', 'Pedro', 'Sánchez', 'Historia', '0994444444', 'pedro.sanchez@colegio.edu', '2018-01-20'),
    ('6677889900', 'Lucía', 'Vargas', 'Inglés', '0995555555', 'lucia.vargas@colegio.edu', '2022-05-05')
ON CONFLICT (cedula) DO NOTHING;

-- Materias por cada grado de primaria
INSERT INTO materia (nombre, codigo, horas_semana, id_docente, id_grado)
SELECT v.nombre, v.codigo || g.orden, v.horas, d.id_docente, g.id_grado
FROM (VALUES
    ('Matemáticas', 'MAT', 5, '1234567890'),
    ('Lenguaje', 'LEN', 5, '0987654321'),
    ('Ciencias Naturales', 'CIE', 4, '1122334455'),
    ('Historia', 'HIS', 3, '5566778899'),
    ('Inglés', 'ING', 4, '6677889900')
) AS v(nombre, codigo, horas, doc_cedula)
CROSS JOIN grado g
JOIN docente d ON d.cedula = v.doc_cedula
WHERE g.nivel = 'Primaria'
ON CONFLICT (codigo) DO NOTHING;

COMMENT ON TABLE periodo_academico IS 'Años lectivos / periodos académicos';
COMMENT ON TABLE grado IS 'Grados escolares';
COMMENT ON TABLE seccion IS 'Secciones por grado y periodo';
COMMENT ON TABLE estudiante IS 'Datos de los alumnos';
COMMENT ON TABLE docente IS 'Datos de los profesores';
COMMENT ON TABLE materia IS 'Materias / cursos';
COMMENT ON TABLE horario IS 'Horario de clases';
COMMENT ON TABLE asistencia IS 'Control de asistencia';
COMMENT ON TABLE calificacion IS 'Notas por materia y periodo';
COMMENT ON TABLE pago IS 'Pagos y comprobantes';
COMMENT ON TABLE usuario IS 'Usuarios: admin, docente, secretaria, estudiante';