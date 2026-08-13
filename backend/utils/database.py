# Sirve para importar las funciones de la base de datos desde el módulo utils.database
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from dotenv import load_dotenv
from backend.utils.serializers import serialize_row, serialize_rows

# Cargar variables de entorno desde un archivo .env
load_dotenv()

# Configuración de la base de datos usando variables de entorno
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'control_escolar'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', 'astrid123'),
    'port': os.getenv('DB_PORT', '5432')
}

# Función para obtener una conexión a la base de datos
def get_connection():
    return psycopg2.connect(**DB_CONFIG)

# Context manager para manejar la conexión a la base de datos
@contextmanager
def get_db():
    conn = None
    try:
        conn = get_connection()
        yield conn
        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        raise e
    finally:
        if conn:
            conn.close()

# Función para ejecutar consultas SQL
def execute_query(query, params=None, fetch_one=False, fetch_all=False):
    with get_db() as conn:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params)
            if fetch_one:
                return serialize_row(cur.fetchone())
            if fetch_all:
                return serialize_rows(cur.fetchall())
            return cur.rowcount

# Función para ejecutar múltiples consultas SQL con diferentes parámetros
def execute_many(query, params_list):
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.executemany(query, params_list)
            return cur.rowcount