# Modelo para gestionar la asistencia de los estudiantes
from backend.utils.database import execute_query

class Asistencia:
    @staticmethod # Registrar o actualizar la asistencia de un estudiante
    def registrar(id_estudiante, fecha, estado, id_seccion=None, id_horario=None,
                  observacion=None, registrado_por=None):
        query = """
            INSERT INTO asistencia
            (id_estudiante, id_seccion, id_horario, fecha, estado, observacion, registrado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id_estudiante, fecha)
            DO UPDATE SET
                estado = EXCLUDED.estado,
                observacion = EXCLUDED.observacion,
                id_seccion = COALESCE(EXCLUDED.id_seccion, asistencia.id_seccion),
                id_horario = COALESCE(EXCLUDED.id_horario, asistencia.id_horario),
                registrado_por = EXCLUDED.registrado_por
            RETURNING id_asistencia
        """
        result = execute_query(
            query,
            (id_estudiante, id_seccion, id_horario, fecha, estado, observacion, registrado_por),
            fetch_one=True
        )
        return result['id_asistencia'] if result else None

    @staticmethod # Registrar múltiples asistencias de estudiantes
    def registrar_masivo(registros, registrado_por=None):
        count = 0
        for r in registros:
            Asistencia.registrar(
                r['id_estudiante'], r['fecha'], r['estado'],
                r.get('id_seccion'), r.get('id_horario'),
                r.get('observacion'), registrado_por
            )
            count += 1
        return count

    @staticmethod # Listar asistencias
    def listar(fecha=None, id_seccion=None, id_grado=None, id_estudiante=None,
               fecha_desde=None, fecha_hasta=None):
        conditions, params = [], []
        if fecha:
            conditions.append("a.fecha = %s")
            params.append(fecha)
        if id_seccion:
            conditions.append("a.id_seccion = %s")
            params.append(id_seccion)
        if id_grado:
            conditions.append("s.id_grado = %s")
            params.append(id_grado)
        if id_estudiante:
            conditions.append("a.id_estudiante = %s")
            params.append(id_estudiante)
        if fecha_desde:
            conditions.append("a.fecha >= %s")
            params.append(fecha_desde)
        if fecha_hasta:
            conditions.append("a.fecha <= %s")
            params.append(fecha_hasta)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        query = f"""
            SELECT a.*, e.nombres || ' ' || e.apellidos AS estudiante_nombre,
                   e.cedula, s.nombre AS seccion_nombre, g.nombre AS grado_nombre
            FROM asistencia a
            JOIN estudiante e ON a.id_estudiante = e.id_estudiante
            LEFT JOIN seccion s ON COALESCE(a.id_seccion, e.id_seccion) = s.id_seccion
            LEFT JOIN grado g ON s.id_grado = g.id_grado
            {where}
            ORDER BY a.fecha DESC, e.apellidos
        """
        return execute_query(query, params if params else None, fetch_all=True)
