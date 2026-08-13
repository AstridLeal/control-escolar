# Modelos para gestionar docentes y sus materias asignadas
from backend.utils.database import execute_query

class Docente:
    @staticmethod # Crear un nuevo docente
    def crear(data):
        query = """
            INSERT INTO docente
            (cedula, nombres, apellidos, especialidad, telefono, email, fecha_contratacion)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            RETURNING id_docente
        """
        params = (
            data.get('cedula'), data.get('nombres'), data.get('apellidos'),
            data.get('especialidad'), data.get('telefono'), data.get('email'),
            data.get('fecha_contratacion')
        )
        result = execute_query(query, params, fetch_one=True)
        return result['id_docente'] if result else None

    @staticmethod # Obtener un docente por su ID
    def obtener_por_id(doc_id):
        return execute_query(
            "SELECT * FROM docente WHERE id_docente = %s", (doc_id,), fetch_one=True
        )

    @staticmethod # Listar docentes activos
    def listar(activo=True):
        query = """
            SELECT d.*,
                   (SELECT COUNT(*) FROM materia m WHERE m.id_docente = d.id_docente) AS total_materias
            FROM docente d
            WHERE d.activo = %s
            ORDER BY d.apellidos, d.nombres
        """
        return execute_query(query, (activo,), fetch_all=True)

    @staticmethod # Actualizar los datos de un docente
    def actualizar(doc_id, data):
        fields, values = [], []
        allowed = ['cedula', 'nombres', 'apellidos', 'especialidad', 'telefono',
                   'email', 'fecha_contratacion', 'activo']
        for key in allowed:
            if key in data:
                fields.append(f"{key} = %s")
                values.append(data[key])
        if not fields:
            return False
        values.append(doc_id)
        query = f"UPDATE docente SET {', '.join(fields)} WHERE id_docente = %s"
        return execute_query(query, values) > 0

    @staticmethod # Eliminar un docente (marcar como inactivo)
    def eliminar(doc_id):
        return execute_query(
            "UPDATE docente SET activo = FALSE WHERE id_docente = %s", (doc_id,)
        ) > 0

    @staticmethod # Asignar una materia a un docente
    def asignar_materia(id_docente, id_materia):
        return execute_query(
            "UPDATE materia SET id_docente = %s WHERE id_materia = %s",
            (id_docente, id_materia)
        ) > 0

    @staticmethod # Listar materias asignadas a un docente
    def materias(id_docente):
        query = """
            SELECT m.*, g.nombre AS grado_nombre
            FROM materia m
            LEFT JOIN grado g ON m.id_grado = g.id_grado
            WHERE m.id_docente = %s
            ORDER BY m.nombre
        """
        return execute_query(query, (id_docente,), fetch_all=True)
