# Modelos para gestionar pagos de estudiantes
from backend.utils.database import execute_query

class Pago:
    @staticmethod # Registrar un nuevo pago
    def registrar(data):
        query = """
            INSERT INTO pago
            (id_estudiante, id_periodo, concepto, mes, anio, monto,
             fecha_pago, fecha_vencimiento, estado, metodo_pago, referencia,
             comprobante, observacion, registrado_por)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            RETURNING id_pago
        """
        params = (
            data.get('id_estudiante'), data.get('id_periodo'),
            data.get('concepto', 'Mensualidad'), data.get('mes'), data.get('anio'),
            data.get('monto'), data.get('fecha_pago'), data.get('fecha_vencimiento'),
            data.get('estado', 'Pagado'), data.get('metodo_pago'), data.get('referencia'),
            data.get('comprobante'), data.get('observacion'), data.get('registrado_por')
        )
        result = execute_query(query, params, fetch_one=True)
        return result['id_pago'] if result else None

    @staticmethod # Listar pagos
    def listar(id_estudiante=None, estado=None, id_periodo=None, mes=None, anio=None):
        conditions, params = [], []
        if id_estudiante:
            conditions.append("p.id_estudiante = %s")
            params.append(id_estudiante)
        if estado:
            conditions.append("p.estado = %s")
            params.append(estado)
        if id_periodo:
            conditions.append("p.id_periodo = %s")
            params.append(id_periodo)
        if mes:
            conditions.append("p.mes = %s")
            params.append(mes)
        if anio:
            conditions.append("p.anio = %s")
            params.append(anio)
        where = ("WHERE " + " AND ".join(conditions)) if conditions else ""
        query = f"""
            SELECT p.*, e.nombres || ' ' || e.apellidos AS estudiante_nombre,
                   e.cedula, per.nombre AS periodo_nombre
            FROM pago p
            JOIN estudiante e ON p.id_estudiante = e.id_estudiante
            LEFT JOIN periodo_academico per ON p.id_periodo = per.id_periodo
            {where}
            ORDER BY p.created_at DESC
        """
        return execute_query(query, params if params else None, fetch_all=True)

    @staticmethod # Obtener un pago por su ID
    def obtener_por_id(id_pago):
        query = """
            SELECT p.*, e.nombres || ' ' || e.apellidos AS estudiante_nombre, e.cedula
            FROM pago p
            JOIN estudiante e ON p.id_estudiante = e.id_estudiante
            WHERE p.id_pago = %s
        """
        return execute_query(query, (id_pago,), fetch_one=True)

    @staticmethod # Actualizar el estado de un pago
    def actualizar_estado(id_pago, estado, fecha_pago=None, comprobante=None):
        fields, values = ["estado = %s"], [estado]
        if fecha_pago:
            fields.append("fecha_pago = %s")
            values.append(fecha_pago)
        if comprobante:
            fields.append("comprobante = %s")
            values.append(comprobante)
        values.append(id_pago)
        query = f"UPDATE pago SET {', '.join(fields)} WHERE id_pago = %s"
        return execute_query(query, values) > 0

    @staticmethod # Obtener resumen de pagos y morosos
    def dashboard_morosos(id_periodo=None):
        conditions = ["p.estado IN ('Pendiente', 'Vencido')"]
        params = []
        if id_periodo:
            conditions.append("p.id_periodo = %s")
            params.append(id_periodo)
        where = "WHERE " + " AND ".join(conditions)

        morosos = execute_query(f"""
            SELECT e.id_estudiante, e.cedula,
                   e.nombres || ' ' || e.apellidos AS nombre,
                   COUNT(p.id_pago) AS cuotas_pendientes,
                   SUM(p.monto) AS deuda_total,
                   MAX(p.fecha_vencimiento) AS ultima_vencimiento
            FROM pago p
            JOIN estudiante e ON p.id_estudiante = e.id_estudiante
            {where}
            GROUP BY e.id_estudiante, e.cedula, e.nombres, e.apellidos
            ORDER BY deuda_total DESC
        """, params if params else None, fetch_all=True)

        resumen_q = f"""
            SELECT
                COUNT(*) FILTER (WHERE estado = 'Pagado') AS total_pagados,
                COUNT(*) FILTER (WHERE estado = 'Pendiente') AS total_pendientes,
                COUNT(*) FILTER (WHERE estado = 'Vencido') AS total_vencidos,
                COALESCE(SUM(monto) FILTER (WHERE estado = 'Pagado'), 0) AS monto_cobrado,
                COALESCE(SUM(monto) FILTER (WHERE estado IN ('Pendiente', 'Vencido')), 0) AS monto_pendiente
            FROM pago p
            {'WHERE p.id_periodo = %s' if id_periodo else ''}
        """
        resumen = execute_query(
            resumen_q, (id_periodo,) if id_periodo else None, fetch_one=True
        )
        return {
            'morosos': [dict(m) for m in (morosos or [])],
            'resumen': dict(resumen) if resumen else {}
        }
