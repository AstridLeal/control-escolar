# Utilidades de serialización para respuestas JSON.
# Sirve para convertir los resultados de las consultas a la base de datos en formatos compatibles con JSON.
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any

# Función para serializar un valor individual a un formato compatible con JSON
def serialize_value(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, datetime):
        return value.isoformat(sep=' ', timespec='seconds')
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, time):
        return value.strftime('%H:%M:%S')
    if isinstance(value, (bytes, memoryview)):
        return bytes(value).decode('utf-8', errors='replace')
    return value

# Función para serializar una fila de resultados de la base de datos a un diccionario
def serialize_row(row) -> dict | None:
    if row is None:
        return None
    if isinstance(row, dict):
        return {k: serialize_value(v) for k, v in row.items()}
    # RealDictRow u objetos similares
    try:
        return {k: serialize_value(row[k]) for k in row.keys()}
    except Exception:
        return dict(row)

# Función para serializar múltiples filas de resultados de la base de datos a una lista de diccionarios
def serialize_rows(rows) -> list:
    if not rows:
        return []
    return [serialize_row(r) for r in rows]