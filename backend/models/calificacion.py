# Modelo para gestionar las calificaciones de los estudiantes
from backend.utils.database import execute_query

class Calificacion:
    @staticmethod # Calcular el promedio de las notas, ignorando las que son None
    def calcular_promedio(nota1, nota2, nota3, examen_final):
        notas = [n for n in [nota1, nota2, nota3, examen_final] if n is not None]
        if not notas:
            return None
        return round(sum(float(n) for n in notas) / len(notas), 2)

    @staticmethod # Guardar o actualizar la calificación de un estudiante
    def guardar(id_estudiante, id_materia, id_periodo, nota1=None, nota2=None,
                nota3=None, examen_final=None, observacion=None, registrado_por=None):
        # Si ya existe, fusionar notas: no sobrescribir con NULL las que no se envían
        existing = execute_query(
            """
            SELECT nota1, nota2, nota3, examen_final, observacion
            FROM calificacion
            WHERE id_estudiante = %s AND id_materia = %s AND id_periodo = %s
            """,
            (id_estudiante, id_materia, id_periodo),
            fetch_one=True
        )
        if existing:
            if nota1 is None:
                nota1 = existing.get('nota1')
            if nota2 is None:
                nota2 = existing.get('nota2')
            if nota3 is None:
                nota3 = existing.get('nota3')
            if examen_final is None:
                examen_final = existing.get('examen_final')
            if observacion is None:
                observacion = existing.get('observacion')

        nota_final = Calificacion.calcular_promedio(nota1, nota2, nota3, examen_final)
        query = """
            INSERT INTO calificacion
            (id_estudiante, id_materia, id_periodo, nota1, nota2, nota3,
             examen_final, nota_final, observacion, registrado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (id_estudiante, id_materia, id_periodo)
            DO UPDATE SET
                nota1 = EXCLUDED.nota1, nota2 = EXCLUDED.nota2, nota3 = EXCLUDED.nota3,
                examen_final = EXCLUDED.examen_final, nota_final = EXCLUDED.nota_final,
                observacion = EXCLUDED.observacion, registrado_por = EXCLUDED.registrado_por,
                updated_at = CURRENT_TIMESTAMP
            RETURNING id_calificacion
        """
        result = execute_query(
            query,
            (id_estudiante, id_materia, id_periodo, nota1, nota2, nota3,
             examen_final, nota_final, observacion, registrado_por),
            fetch_one=True
        )
        return result['id_calificacion'] if result else None

    @staticmethod # Listar calificaciones con filtros opcionales
    def listar(id_estudiante=None, id_materia=None, id_periodo=None, id_seccion=None):
        conditions, params = [], []
        if id_estudiante:
            conditions.append("c.id_estudiante = %s")
            params.append(id_estudiante)
        if id_materia:
            conditions.append("c.id_materia = %s")
            params.append(id_materia)
        if id_periodo:
            conditions.append("c.id_periodo = %s")
            params.append(id_periodo)
        if id_seccion:
            conditions.append("e.id_seccion = %s")
            params.append(id_seccion)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        query = f"""
            SELECT c.*, e.nombres || ' ' || e.apellidos AS estudiante_nombre,
                   e.cedula, m.nombre AS materia_nombre, p.nombre AS periodo_nombre
            FROM calificacion c
            JOIN estudiante e ON c.id_estudiante = e.id_estudiante
            JOIN materia m ON c.id_materia = m.id_materia
            JOIN periodo_academico p ON c.id_periodo = p.id_periodo
            {where}
            ORDER BY e.apellidos, m.nombre
        """
        return execute_query(query, params if params else None, fetch_all=True)

    @staticmethod # Generar acta de calificaciones para una materia, sección y periodo
    def acta(id_materia, id_seccion, id_periodo):
        query = """
            SELECT e.id_estudiante, e.cedula, e.nombres, e.apellidos,
                   c.nota1, c.nota2, c.nota3, c.examen_final, c.nota_final, c.observacion
            FROM estudiante e
            LEFT JOIN calificacion c ON e.id_estudiante = c.id_estudiante
                AND c.id_materia = %s AND c.id_periodo = %s
            WHERE e.id_seccion = %s AND e.activo = TRUE
            ORDER BY e.apellidos, e.nombres
        """
        return execute_query(query, (id_materia, id_periodo, id_seccion), fetch_all=True)
