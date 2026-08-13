# Modelos para gestionar materias, grados, secciones y horarios
from backend.utils.database import execute_query

class Materia: 
    @staticmethod # Crear una nueva materia
    def crear(nombre, codigo=None, horas_semana=0, id_docente=None, id_grado=None, descripcion=None):
        query = """
            INSERT INTO materia (nombre, codigo, horas_semana, id_docente, id_grado, descripcion)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_materia
        """
        result = execute_query(
            query, (nombre, codigo, horas_semana, id_docente, id_grado, descripcion),
            fetch_one=True
        )
        return result['id_materia'] if result else None

    @staticmethod # Listar materias con filtros opcionales
    def listar(id_grado=None, id_docente=None):
        conditions, params = [], []
        if id_grado:
            conditions.append("m.id_grado = %s")
            params.append(id_grado)
        if id_docente:
            conditions.append("m.id_docente = %s")
            params.append(id_docente)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        query = f"""
            SELECT m.*, d.nombres || ' ' || d.apellidos AS docente_nombre,
                   g.nombre AS grado_nombre
            FROM materia m
            LEFT JOIN docente d ON m.id_docente = d.id_docente
            LEFT JOIN grado g ON m.id_grado = g.id_grado
            {where}
            ORDER BY m.nombre
        """
        return execute_query(query, params if params else None, fetch_all=True)

    @staticmethod # Obtener una materia por su ID
    def obtener_por_id(id_materia):
        return execute_query(
            "SELECT * FROM materia WHERE id_materia = %s", (id_materia,), fetch_one=True
        )

    @staticmethod # Actualizar los datos de una materia
    def actualizar(id_materia, data):
        fields, values = [], []
        for key in ['nombre', 'codigo', 'horas_semana', 'id_docente', 'id_grado', 'descripcion']:
            if key in data:
                fields.append(f"{key} = %s")
                values.append(data[key])
        if not fields:
            return False
        values.append(id_materia)
        query = f"UPDATE materia SET {', '.join(fields)} WHERE id_materia = %s"
        return execute_query(query, values) > 0

    @staticmethod # Eliminar una materia por su ID
    def eliminar(id_materia):
        return execute_query("DELETE FROM materia WHERE id_materia = %s", (id_materia,)) > 0


class Grado:
    @staticmethod # Listar todos los grados
    def listar():
        return execute_query("SELECT * FROM grado ORDER BY orden", fetch_all=True)

    @staticmethod # Crear un nuevo grado
    def crear(nombre, nivel, orden=0):
        query = "INSERT INTO grado (nombre, nivel, orden) VALUES (%s, %s, %s) RETURNING id_grado"
        result = execute_query(query, (nombre, nivel, orden), fetch_one=True)
        return result['id_grado'] if result else None


class Seccion:
    @staticmethod # Crear una nueva sección
    def crear(nombre, id_grado, id_periodo, capacidad_max=30):
        query = """
            INSERT INTO seccion (nombre, id_grado, id_periodo, capacidad_max)
            VALUES (%s, %s, %s, %s) RETURNING id_seccion
        """
        result = execute_query(
            query, (nombre, id_grado, id_periodo, capacidad_max), fetch_one=True
        )
        return result['id_seccion'] if result else None

    @staticmethod # Listar secciones con filtros opcionales
    def listar(id_periodo=None, id_grado=None):
        conditions, params = [], []
        if id_periodo:
            conditions.append("s.id_periodo = %s")
            params.append(id_periodo)
        if id_grado:
            conditions.append("s.id_grado = %s")
            params.append(id_grado)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        query = f"""
            SELECT s.*, g.nombre AS grado_nombre, p.nombre AS periodo_nombre,
                   (SELECT COUNT(*) FROM estudiante e
                    WHERE e.id_seccion = s.id_seccion AND e.activo = TRUE) AS inscritos
            FROM seccion s
            JOIN grado g ON s.id_grado = g.id_grado
            JOIN periodo_academico p ON s.id_periodo = p.id_periodo
            {where}
            ORDER BY g.orden, s.nombre
        """
        return execute_query(query, params if params else None, fetch_all=True)

    @staticmethod # Obtener una sección por su ID
    def obtener_por_id(id_seccion):
        query = """
            SELECT s.*, g.nombre AS grado_nombre, p.nombre AS periodo_nombre
            FROM seccion s
            JOIN grado g ON s.id_grado = g.id_grado
            JOIN periodo_academico p ON s.id_periodo = p.id_periodo
            WHERE s.id_seccion = %s
        """
        return execute_query(query, (id_seccion,), fetch_one=True)

    @staticmethod # Actualizar los datos de una sección
    def actualizar(id_seccion, data):
        fields, values = [], []
        for key in ['nombre', 'id_grado', 'id_periodo', 'capacidad_max']:
            if key in data:
                fields.append(f"{key} = %s")
                values.append(data[key])
        if not fields:
            return False
        values.append(id_seccion)
        query = f"UPDATE seccion SET {', '.join(fields)} WHERE id_seccion = %s"
        return execute_query(query, values) > 0

    @staticmethod # Eliminar una sección por su ID
    def eliminar(id_seccion):
        return execute_query("DELETE FROM seccion WHERE id_seccion = %s", (id_seccion,)) > 0


class Horario:
    @staticmethod # Crear un nuevo horario para una materia y sección
    def crear(id_materia, id_seccion, dia_semana, hora_inicio, hora_fin, aula=None):
        query = """
            INSERT INTO horario (id_materia, id_seccion, dia_semana, hora_inicio, hora_fin, aula)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING id_horario
        """
        result = execute_query(
            query, (id_materia, id_seccion, dia_semana, hora_inicio, hora_fin, aula),
            fetch_one=True
        )
        return result['id_horario'] if result else None

    @staticmethod # Listar horarios con filtros opcionales
    def listar(id_seccion=None, id_materia=None):
        conditions, params = [], []
        if id_seccion:
            conditions.append("h.id_seccion = %s")
            params.append(id_seccion)
        if id_materia:
            conditions.append("h.id_materia = %s")
            params.append(id_materia)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        query = f"""
            SELECT h.*, m.nombre AS materia_nombre, s.nombre AS seccion_nombre,
                   g.nombre AS grado_nombre
            FROM horario h
            JOIN materia m ON h.id_materia = m.id_materia
            JOIN seccion s ON h.id_seccion = s.id_seccion
            JOIN grado g ON s.id_grado = g.id_grado
            {where}
            ORDER BY
                CASE h.dia_semana
                    WHEN 'Lunes' THEN 1 WHEN 'Martes' THEN 2 WHEN 'Miércoles' THEN 3
                    WHEN 'Jueves' THEN 4 WHEN 'Viernes' THEN 5 WHEN 'Sábado' THEN 6
                    ELSE 7 END,
                h.hora_inicio
        """
        return execute_query(query, params if params else None, fetch_all=True)

    @staticmethod # Eliminar un horario por su ID
    def eliminar(id_horario):
        return execute_query("DELETE FROM horario WHERE id_horario = %s", (id_horario,)) > 0
