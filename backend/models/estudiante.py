# Modelos para gestionar estudiantes y sus secciones
from backend.utils.database import execute_query, execute_many

class Estudiante:
    @staticmethod # Crear un nuevo estudiante
    def crear(data):
        query = """
            INSERT INTO estudiante
            (cedula, nombres, apellidos, fecha_nacimiento, genero, direccion,
             telefono, email, nombre_representante, telefono_representante, id_seccion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_estudiante
        """
        params = (
            data.get('cedula'), data.get('nombres'), data.get('apellidos'),
            data.get('fecha_nacimiento') or None, data.get('genero'), data.get('direccion'),
            data.get('telefono'), data.get('email'), data.get('nombre_representante'),
            data.get('telefono_representante'), data.get('id_seccion')
        )
        result = execute_query(query, params, fetch_one=True)
        return result['id_estudiante'] if result else None

    @staticmethod # Crear múltiples estudiantes de forma masiva
    def crear_masivo(lista):
        query = """
            INSERT INTO estudiante
            (cedula, nombres, apellidos, fecha_nacimiento, genero, direccion,
             telefono, email, nombre_representante, telefono_representante, id_seccion)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (cedula) DO NOTHING
        """
        params = []
        for e in lista:
            if not e.get('cedula') or not e.get('nombres') or not e.get('apellidos'):
                continue
            params.append((
                e.get('cedula'), e.get('nombres'), e.get('apellidos'),
                e.get('fecha_nacimiento') or None, e.get('genero'), e.get('direccion'),
                e.get('telefono'), e.get('email'), e.get('nombre_representante'),
                e.get('telefono_representante'), e.get('id_seccion')
            ))
        if not params:
            return 0
        return execute_many(query, params)

    @staticmethod # Obtener un estudiante por su ID
    def obtener_por_id(est_id):
        query = """
            SELECT e.*, s.nombre AS seccion_nombre, g.nombre AS grado_nombre,
                   g.id_grado, p.nombre AS periodo_nombre, p.id_periodo
            FROM estudiante e
            LEFT JOIN seccion s ON e.id_seccion = s.id_seccion
            LEFT JOIN grado g ON s.id_grado = g.id_grado
            LEFT JOIN periodo_academico p ON s.id_periodo = p.id_periodo
            WHERE e.id_estudiante = %s
        """
        return execute_query(query, (est_id,), fetch_one=True)

    @staticmethod # Obtener un estudiante por su cédula
    def obtener_por_cedula(cedula):
        query = """
            SELECT e.*, s.nombre AS seccion_nombre, g.nombre AS grado_nombre,
                   g.id_grado, p.id_periodo, p.nombre AS periodo_nombre
            FROM estudiante e
            LEFT JOIN seccion s ON e.id_seccion = s.id_seccion
            LEFT JOIN grado g ON s.id_grado = g.id_grado
            LEFT JOIN periodo_academico p ON s.id_periodo = p.id_periodo
            WHERE e.cedula = %s AND e.activo = TRUE
        """
        return execute_query(query, (cedula,), fetch_one=True)

    @staticmethod # Listar estudiantes activos
    def listar(activo=True):
        query = """
            SELECT e.*, s.nombre AS seccion_nombre, g.nombre AS grado_nombre,
                   g.id_grado, p.nombre AS periodo_nombre, p.id_periodo
            FROM estudiante e
            LEFT JOIN seccion s ON e.id_seccion = s.id_seccion
            LEFT JOIN grado g ON s.id_grado = g.id_grado
            LEFT JOIN periodo_academico p ON s.id_periodo = p.id_periodo
            WHERE e.activo = %s
            ORDER BY e.apellidos, e.nombres
        """
        return execute_query(query, (activo,), fetch_all=True)

    @staticmethod # Actualizar los datos de un estudiante
    def actualizar(est_id, data):
        fields, values = [], []
        allowed = [
            'cedula', 'nombres', 'apellidos', 'fecha_nacimiento', 'genero',
            'direccion', 'telefono', 'email', 'nombre_representante',
            'telefono_representante', 'id_seccion', 'activo', 'codigo_qr'
        ]
        for key in allowed:
            if key in data:
                fields.append(f"{key} = %s")
                values.append(data[key])
        if not fields:
            return False
        values.append(est_id)
        query = f"UPDATE estudiante SET {', '.join(fields)} WHERE id_estudiante = %s"
        return execute_query(query, values) > 0

    @staticmethod # Eliminar un estudiante (marcar como inactivo)
    def eliminar(est_id):
        return execute_query(
            "UPDATE estudiante SET activo = FALSE WHERE id_estudiante = %s", (est_id,)
        ) > 0

    @staticmethod # Buscar estudiantes por término de búsqueda
    def buscar(termino):
        like = f"%{termino}%"
        query = """
            SELECT e.*, s.nombre AS seccion_nombre, g.nombre AS grado_nombre
            FROM estudiante e
            LEFT JOIN seccion s ON e.id_seccion = s.id_seccion
            LEFT JOIN grado g ON s.id_grado = g.id_grado
            WHERE e.activo = TRUE AND (
                e.cedula ILIKE %s OR e.nombres ILIKE %s OR e.apellidos ILIKE %s
            )
            ORDER BY e.apellidos LIMIT 50
        """
        return execute_query(query, (like, like, like), fetch_all=True)

    @staticmethod # Matricular un estudiante en una sección por cédula
    def matricular(cedula, id_seccion):
        """Inscripción rápida: asignar sección por cédula"""
        est = Estudiante.obtener_por_cedula(cedula)
        if not est:
            return None, "Estudiante no encontrado"
        ok = Estudiante.actualizar(est['id_estudiante'], {
            'id_seccion': id_seccion,
            'activo': True
        })
        if ok:
            execute_query(
                "UPDATE estudiante SET fecha_inscripcion = CURRENT_DATE WHERE id_estudiante = %s",
                (est['id_estudiante'],)
            )
            return est['id_estudiante'], None
        return None, "No se pudo matricular"

    @staticmethod # Listar estudiantes por sección
    def por_seccion(id_seccion):
        query = """
            SELECT id_estudiante, cedula, nombres, apellidos
            FROM estudiante
            WHERE id_seccion = %s AND activo = TRUE
            ORDER BY apellidos, nombres
        """
        return execute_query(query, (id_seccion,), fetch_all=True)
