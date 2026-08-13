# Modelos para gestionar periodos académicos
from backend.utils.database import execute_query

class Periodo:
    @staticmethod # Crear un nuevo periodo académico
    def crear(nombre, fecha_inicio, fecha_fin, activo=False):
        if activo:
            execute_query("UPDATE periodo_academico SET activo = FALSE")
        query = """
            INSERT INTO periodo_academico (nombre, fecha_inicio, fecha_fin, activo)
            VALUES (%s, %s, %s, %s) RETURNING id_periodo
        """
        result = execute_query(query, (nombre, fecha_inicio, fecha_fin, activo), fetch_one=True)
        return result['id_periodo'] if result else None

    @staticmethod # Listar todos los periodos académicos
    def listar():
        return execute_query(
            "SELECT * FROM periodo_academico ORDER BY fecha_inicio DESC", fetch_all=True
        )

    @staticmethod # Obtener el periodo académico activo
    def obtener_activo():
        return execute_query(
            "SELECT * FROM periodo_academico WHERE activo = TRUE LIMIT 1", fetch_one=True
        )

    @staticmethod # Obtener un periodo académico por su ID
    def obtener_por_id(periodo_id):
        return execute_query(
            "SELECT * FROM periodo_academico WHERE id_periodo = %s",
            (periodo_id,), fetch_one=True
        )

    @staticmethod # Actualizar los datos de un periodo académico
    def actualizar(periodo_id, data):
        if data.get('activo'):
            execute_query("UPDATE periodo_academico SET activo = FALSE")
        fields, values = [], []
        for key in ['nombre', 'fecha_inicio', 'fecha_fin', 'activo']:
            if key in data:
                fields.append(f"{key} = %s")
                values.append(data[key])
        if not fields:
            return False
        values.append(periodo_id)
        query = f"UPDATE periodo_academico SET {', '.join(fields)} WHERE id_periodo = %s"
        return execute_query(query, values) > 0

    @staticmethod # Eliminar un periodo académico por su ID
    def eliminar(periodo_id):
        return execute_query(
            "DELETE FROM periodo_academico WHERE id_periodo = %s", (periodo_id,)
        ) > 0
