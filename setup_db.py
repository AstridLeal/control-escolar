# Setup de la base de datos
"""
Inicialización completa de la base de datos:
- Crea BD y schema
- Solo Primaria 1ro-6to, secciones A y B
- 15 estudiantes por sección
- Asistencias, calificaciones y pagos ene–ago 2026
- Usuarios de prueba

Uso:
  python setup_db.py          # normal (migra schema si hace falta)
  python setup_db.py --reset  # borra todas las tablas y recrea desde cero
"""

import os
import sys
import random
from pathlib import Path
from datetime import date, timedelta

from dotenv import load_dotenv
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from psycopg2.extras import execute_values
from werkzeug.security import generate_password_hash

# Directorio base del proyecto y carga de variables de entorno
BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / '.env')

# Configuración de la base de datos desde variables de entorno
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
DB_NAME = os.getenv('DB_NAME', 'control_escolar')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', 'postgres')

# Constantes para generar datos de ejemplo
NOMBRES_M = ['Luis', 'Juan', 'Pedro', 'Diego', 'Carlos', 'Andrés', 'Miguel', 'José',
             'David', 'Daniel', 'Santiago', 'Sebastián', 'Mateo', 'Nicolás', 'Alejandro']
NOMBRES_F = ['María', 'Ana', 'Laura', 'Sofía', 'Elena', 'Lucía', 'Valentina', 'Camila',
             'Isabella', 'Martina', 'Emma', 'Olivia', 'Paula', 'Carmen', 'Rosa']
APELLIDOS = ['Pérez', 'García', 'López', 'Fernández', 'Ramírez', 'Torres', 'Mendoza',
             'Herrera', 'Rojas', 'Cruz', 'Morales', 'Jiménez', 'Díaz', 'Vargas', 'Castro',
             'Romero', 'Sánchez', 'Flores', 'Ruiz', 'Ortiz']
MESES = ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto']
ESTADOS_ASIST = ['Asistió', 'Asistió', 'Asistió', 'Asistió', 'Tardanza', 'Falta', 'Justificado']

# Función para conectarse a la base de datos
def conn_db(database=DB_NAME):
    return psycopg2.connect(
        host=DB_HOST, port=DB_PORT, user=DB_USER,
        password=DB_PASSWORD, database=database
    )

# Funciones para crear la base de datos, resetear el schema, ejecutar el schema.sql y generar datos de ejemplo
def crear_base_datos():
    conn = conn_db('postgres')
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
    if cur.fetchone():
        print(f"[OK] La base de datos '{DB_NAME}' ya existe.")
    else:
        cur.execute(f'CREATE DATABASE "{DB_NAME}"')
        print(f"[OK] Base de datos '{DB_NAME}' creada.")
    cur.close()
    conn.close()

# Función para resetear el schema público de la base de datos
def reset_schema():
    """Borra todo el schema public y lo recrea vacío."""
    conn = conn_db()
    conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
    cur = conn.cursor()
    cur.execute("DROP SCHEMA public CASCADE")
    cur.execute("CREATE SCHEMA public")
    cur.execute("GRANT ALL ON SCHEMA public TO PUBLIC")
    cur.close()
    conn.close()
    print("[OK] Schema reiniciado (todas las tablas eliminadas).")

# Función para obtener las columnas de una tabla específica
def columnas_tabla(cur, tabla):
    cur.execute(
        """
        SELECT column_name FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = %s
        """,
        (tabla,)
    )
    return {r[0] for r in cur.fetchall()}

# Función para migrar la tabla materia si viene de un schema antiguo
def migrar_materia(cur):
    cols = columnas_tabla(cur, 'materia')
    if not cols:
        return  # no existe; schema.sql la creará

    print(f"[INFO] Columnas actuales de materia: {sorted(cols)}")

    # Si ya está bien, no hacer nada
    if 'id_docente' in cols and 'id_grado' in cols:
        print("[OK] Tabla materia ya tiene id_docente e id_grado.")
        return

    print("[INFO] Migrando tabla materia al schema nuevo...")

    # Quitar dependencias que referencian materia
    cur.execute("DELETE FROM horario")
    cur.execute("DELETE FROM calificacion")

    # Si existe columna 'docente' (texto o número), la eliminamos
    if 'docente' in cols:
        try:
            cur.execute("ALTER TABLE materia DROP COLUMN docente")
        except Exception as e:
            print(f"[WARN] No se pudo eliminar columna docente: {e}")

    if 'id_docente' not in cols:
        cur.execute(
            "ALTER TABLE materia ADD COLUMN id_docente INTEGER REFERENCES docente(id_docente) ON DELETE SET NULL"
        )
    if 'id_grado' not in cols:
        cur.execute(
            "ALTER TABLE materia ADD COLUMN id_grado INTEGER REFERENCES grado(id_grado) ON DELETE SET NULL"
        )
    if 'descripcion' not in columnas_tabla(cur, 'materia'):
        cur.execute("ALTER TABLE materia ADD COLUMN descripcion TEXT")
    if 'created_at' not in columnas_tabla(cur, 'materia'):
        cur.execute("ALTER TABLE materia ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP")

    # Limpiar filas viejas sin grado (se regeneran en schema seed / setup)
    cur.execute("DELETE FROM materia")
    print("[OK] Tabla materia migrada.")

# Función para ejecutar el schema.sql y crear las tablas necesarias
def ejecutar_schema():
    schema_path = BASE_DIR / 'database' / 'schema.sql'
    conn = conn_db()
    cur = conn.cursor()

    # Migrar materia ANTES si la tabla ya existe con columnas viejas
    try:
        migrar_materia(cur)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print(f"[WARN] Migración materia: {e}")

    with open(schema_path, 'r', encoding='utf-8') as f:
        cur.execute(f.read())
    conn.commit()
    cur.close()
    conn.close()
    print("[OK] Schema ejecutado (tablas + grados/secciones/materias).")

# Funciones para limpiar datos de ejemplo, generar estudiantes, asistencias, calificaciones y pagos
def limpiar_datos_demo(cur):
    """Limpia datos de ejemplo previos para poder re-ejecutar el script."""
    cur.execute("DELETE FROM asistencia")
    cur.execute("DELETE FROM calificacion")
    cur.execute("DELETE FROM pago")
    cur.execute("DELETE FROM horario")
    cur.execute("DELETE FROM estudiante WHERE cedula LIKE '10%'")

    # Eliminar periodo antiguo 2025-2026 y sus secciones
    cur.execute("""
        DELETE FROM seccion WHERE id_periodo IN (
            SELECT id_periodo FROM periodo_academico WHERE nombre = '2025-2026'
        )
    """)
    cur.execute("DELETE FROM periodo_academico WHERE nombre = '2025-2026'")

    # Activar solo 2026-2027
    cur.execute("UPDATE periodo_academico SET activo = FALSE")
    cur.execute("UPDATE periodo_academico SET activo = TRUE WHERE nombre = '2026-2027'")

    # Eliminar secundaria/bachillerato si existían
    cur.execute("""
        DELETE FROM seccion WHERE id_grado IN (
            SELECT id_grado FROM grado WHERE nivel IN ('Secundaria', 'Bachillerato')
        )
    """)
    # Solo si existe la columna id_grado en materia
    cols = columnas_tabla(cur, 'materia')
    if 'id_grado' in cols:
        cur.execute("""
            DELETE FROM materia WHERE id_grado IN (
                SELECT id_grado FROM grado WHERE nivel IN ('Secundaria', 'Bachillerato')
            )
        """)
    cur.execute("DELETE FROM grado WHERE nivel IN ('Secundaria', 'Bachillerato')")

# Función para generar estudiantes de ejemplo en las secciones de primaria
def generar_estudiantes(cur):
    cur.execute("""
        SELECT s.id_seccion, g.nombre AS grado, s.nombre AS seccion, g.orden
        FROM seccion s
        JOIN grado g ON g.id_grado = s.id_grado
        JOIN periodo_academico p ON p.id_periodo = s.id_periodo
        WHERE p.activo = TRUE AND g.nivel = 'Primaria'
        ORDER BY g.orden, s.nombre
    """)
    secciones = cur.fetchall()
    if not secciones:
        print("[WARN] No hay secciones de primaria. Revisa el schema.")
        return []

    rows = []
    cedula_n = 1000000001
    for id_seccion, grado, seccion, orden in secciones:
        for i in range(15):
            genero = 'M' if i % 2 == 0 else 'F'
            nombre = random.choice(NOMBRES_M if genero == 'M' else NOMBRES_F)
            ap1, ap2 = random.sample(APELLIDOS, 2)
            apellidos = f"{ap1} {ap2}"
            year = 2026 - (5 + orden)
            fnac = date(year, random.randint(1, 12), random.randint(1, 28))
            cedula = str(cedula_n)
            cedula_n += 1
            email = f"{nombre.lower()}.{ap1.lower()}{i}@email.com"
            tel = f"09{random.randint(10000000, 99999999)}"
            rep = f"{random.choice(NOMBRES_M + NOMBRES_F)} {ap1}"
            tel_rep = f"09{random.randint(10000000, 99999999)}"
            rows.append((
                cedula, nombre, apellidos, fnac, genero, None,
                tel, email, rep, tel_rep, id_seccion, date(2026, 1, 15), True
            ))

    execute_values(cur, """
        INSERT INTO estudiante
        (cedula, nombres, apellidos, fecha_nacimiento, genero, direccion,
         telefono, email, nombre_representante, telefono_representante,
         id_seccion, fecha_inscripcion, activo)
        VALUES %s
        ON CONFLICT (cedula) DO NOTHING
    """, rows)
    print(f"[OK] {len(rows)} estudiantes generados (15 por sección × {len(secciones)} secciones).")
    return secciones

# Funciones para generar asistencias, calificaciones y pagos de ejemplo
def generar_asistencias(cur):
    cur.execute("""
        SELECT e.id_estudiante, e.id_seccion
        FROM estudiante e
        WHERE e.activo = TRUE AND e.id_seccion IS NOT NULL
    """)
    estudiantes = cur.fetchall()
    if not estudiantes:
        return

    start = date(2026, 1, 5)
    end = date(2026, 8, 28)
    fechas = []
    d = start
    while d <= end:
        if d.weekday() < 5:
            fechas.append(d)
        d += timedelta(days=1)
    fechas = [f for i, f in enumerate(fechas) if i % 5 == 0]

    rows = []
    for id_est, id_sec in estudiantes:
        for f in fechas:
            estado = random.choice(ESTADOS_ASIST)
            rows.append((id_est, id_sec, f, estado, None))

    execute_values(cur, """
        INSERT INTO asistencia (id_estudiante, id_seccion, fecha, estado, observacion)
        VALUES %s
        ON CONFLICT (id_estudiante, fecha) DO NOTHING
    """, rows)
    print(f"[OK] {len(rows)} registros de asistencia (ene–ago 2026).")

# Funciones para generar calificaciones y pagos de ejemplo
def generar_calificaciones(cur):
    cur.execute("SELECT id_periodo FROM periodo_academico WHERE activo = TRUE LIMIT 1")
    row = cur.fetchone()
    if not row:
        return
    id_periodo = row[0]

    cur.execute("""
        SELECT e.id_estudiante, e.id_seccion, s.id_grado
        FROM estudiante e
        JOIN seccion s ON s.id_seccion = e.id_seccion
        WHERE e.activo = TRUE
    """)
    estudiantes = cur.fetchall()

    cur.execute("SELECT id_materia, id_grado FROM materia")
    materias = cur.fetchall()
    mat_por_grado = {}
    for mid, gid in materias:
        mat_por_grado.setdefault(gid, []).append(mid)

    rows = []
    for id_est, id_sec, id_grado in estudiantes:
        for mid in mat_por_grado.get(id_grado, []):
            n1 = round(random.uniform(60, 100), 1)
            n2 = round(random.uniform(60, 100), 1)
            n3 = round(random.uniform(60, 100), 1)
            ef = round(random.uniform(60, 100), 1)
            nf = round((n1 + n2 + n3 + ef) / 4, 2)
            rows.append((id_est, mid, id_periodo, n1, n2, n3, ef, nf))

    if not rows:
        print("[WARN] No se generaron calificaciones (¿faltan materias con id_grado?).")
        return

    execute_values(cur, """
        INSERT INTO calificacion
        (id_estudiante, id_materia, id_periodo, nota1, nota2, nota3, examen_final, nota_final)
        VALUES %s
        ON CONFLICT (id_estudiante, id_materia, id_periodo) DO NOTHING
    """, rows)
    print(f"[OK] {len(rows)} calificaciones generadas.")

# Funciones para generar pagos de ejemplo
def generar_pagos(cur):
    cur.execute("SELECT id_periodo FROM periodo_academico WHERE activo = TRUE LIMIT 1")
    row = cur.fetchone()
    if not row:
        return
    id_periodo = row[0]

    cur.execute("SELECT id_estudiante FROM estudiante WHERE activo = TRUE")
    ids = [r[0] for r in cur.fetchall()]

    rows = []
    for id_est in ids:
        rows.append((
            id_est, id_periodo, 'Matrícula', None, 2026, 150.00,
            date(2026, 1, random.randint(5, 14)), None, 'Pagado',
            random.choice(['Efectivo', 'Transferencia', 'Depósito']), None
        ))
        for i, mes in enumerate(MESES):
            r = random.random()
            if r < 0.75:
                estado = 'Pagado'
                fecha_pago = date(2026, i + 1, random.randint(1, 15))
                metodo = random.choice(['Efectivo', 'Transferencia', 'Depósito', 'Tarjeta'])
            elif r < 0.90:
                estado = 'Pendiente'
                fecha_pago = None
                metodo = None
            else:
                estado = 'Vencido'
                fecha_pago = None
                metodo = None
            vence = date(2026, i + 1, 10)
            rows.append((
                id_est, id_periodo, 'Mensualidad', mes, 2026, 80.00,
                fecha_pago, vence, estado, metodo, None
            ))

    execute_values(cur, """
        INSERT INTO pago
        (id_estudiante, id_periodo, concepto, mes, anio, monto,
         fecha_pago, fecha_vencimiento, estado, metodo_pago, referencia)
        VALUES %s
    """, rows)
    print(f"[OK] {len(rows)} pagos generados (matrícula + ene–ago 2026).")

# Función para insertar o actualizar usuarios de prueba
def upsert_usuarios(cur):
    usuarios = [
        ('admin', 'admin123', 'admin@colegio.edu', 'Administrador del Sistema', 'admin', None, None),
        ('secretaria', 'secre123', 'secretaria@colegio.edu', 'Secretaría Académica', 'secretaria', None, None),
        ('docente1', 'docente123', 'carlos.gomez@colegio.edu', 'Carlos Gómez', 'docente', None, '1234567890'),
        ('alumno1', 'alumno123', 'alumno@email.com', 'Alumno Demo', 'estudiante', None, None),
    ]

    cur.execute("SELECT id_estudiante FROM estudiante WHERE activo = TRUE ORDER BY id_estudiante LIMIT 1")
    first_est = cur.fetchone()
    id_est_demo = first_est[0] if first_est else None

    for username, password, email, nombre, rol, _, cedula_doc in usuarios:
        id_est = id_est_demo if rol == 'estudiante' else None
        id_doc = None
        if cedula_doc:
            cur.execute("SELECT id_docente FROM docente WHERE cedula = %s", (cedula_doc,))
            r = cur.fetchone()
            id_doc = r[0] if r else None

        ph = generate_password_hash(password)
        cur.execute("SELECT id_usuario FROM usuario WHERE username = %s", (username,))
        if cur.fetchone():
            cur.execute("""
                UPDATE usuario SET password_hash=%s, email=%s, nombre_completo=%s,
                    rol=%s, id_estudiante=%s, id_docente=%s, activo=TRUE
                WHERE username=%s
            """, (ph, email, nombre, rol, id_est, id_doc, username))
        else:
            cur.execute("""
                INSERT INTO usuario
                (username, password_hash, email, nombre_completo, rol, id_estudiante, id_docente, activo)
                VALUES (%s,%s,%s,%s,%s,%s,%s,TRUE)
            """, (username, ph, email, nombre, rol, id_est, id_doc))

    print("[OK] Usuarios: admin/admin123 | secretaria/secre123 | docente1/docente123 | alumno1/alumno123")

# Main function to execute the setup
def main():
    print("=" * 55)
    print("  Inicialización - Sistema de Control Escolar")
    print("=" * 55)
    print(f"Host: {DB_HOST}:{DB_PORT}  |  DB: {DB_NAME}")
    print()
    random.seed(42)

    do_reset = '--reset' in sys.argv

    try:
        crear_base_datos()
        if do_reset:
            reset_schema()
        ejecutar_schema()

        conn = conn_db()
        cur = conn.cursor()
        limpiar_datos_demo(cur)
        generar_estudiantes(cur)
        generar_asistencias(cur)
        generar_calificaciones(cur)
        generar_pagos(cur)
        upsert_usuarios(cur)
        conn.commit()
        cur.close()
        conn.close()

        print()
        print("=" * 55)
        print("  ¡Listo! Ejecuta:  python backend/app.py")
        print("  URL: http://localhost:5000")
        print("  Periodo activo: 2026-2027")
        print("  Secciones: A y B de 1ro a 6to Primaria")
        print("=" * 55)
    except psycopg2.OperationalError as e:
        print(f"\n[ERROR] PostgreSQL: {e}")
        print("Revisa que el servicio esté activo y las credenciales en .env")
        sys.exit(1)
    except Exception as e:
        print(f"\n[ERROR] {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

# Punto de entrada del script
if __name__ == '__main__':
    main()