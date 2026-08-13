# Modelos para gestionar usuarios
from backend.utils.database import execute_query
from werkzeug.security import generate_password_hash, check_password_hash

class Usuario:
    @staticmethod # Crear un nuevo usuario
    def crear(username, password, nombre_completo, rol, email=None, id_estudiante=None, id_docente=None):
        password_hash = generate_password_hash(password)
        query = """
            INSERT INTO usuario (username, password_hash, email, nombre_completo, rol, id_estudiante, id_docente)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING id_usuario
        """
        result = execute_query(
            query,
            (username, password_hash, email, nombre_completo, rol, id_estudiante, id_docente),
            fetch_one=True
        )
        return result['id_usuario'] if result else None

    @staticmethod # Autenticar un usuario
    def autenticar(username, password):
        query = """
            SELECT * FROM usuario
            WHERE username = %s AND activo = TRUE
        """
        user = execute_query(query, (username,), fetch_one=True)
        if user and check_password_hash(user['password_hash'], password):
            execute_query(
                "UPDATE usuario SET ultimo_acceso = CURRENT_TIMESTAMP WHERE id_usuario = %s",
                (user['id_usuario'],)
            )
            return dict(user)
        return None

    @staticmethod # Obtener un usuario por su ID
    def obtener_por_id(user_id):
        query = """
            SELECT id_usuario, username, email, nombre_completo, rol, activo,
                   id_estudiante, id_docente, ultimo_acceso, created_at
            FROM usuario WHERE id_usuario = %s
        """
        return execute_query(query, (user_id,), fetch_one=True)

    @staticmethod # Listar todos los usuarios
    def listar():
        query = """
            SELECT id_usuario, username, email, nombre_completo, rol, activo,
                   id_estudiante, id_docente, created_at
            FROM usuario ORDER BY nombre_completo
        """
        return execute_query(query, fetch_all=True)

    @staticmethod # Actualizar los datos de un usuario
    def actualizar(user_id, data):
        fields, values = [], []
        for key in ['username', 'email', 'nombre_completo', 'rol', 'activo', 'id_estudiante', 'id_docente']:
            if key in data:
                fields.append(f"{key} = %s")
                values.append(data[key])
        if data.get('password'):
            fields.append("password_hash = %s")
            values.append(generate_password_hash(data['password']))
        if not fields:
            return False
        values.append(user_id)
        query = f"UPDATE usuario SET {', '.join(fields)} WHERE id_usuario = %s"
        return execute_query(query, values) > 0

    @staticmethod # Eliminar un usuario (marcar como inactivo)
    def eliminar(user_id):
        return execute_query(
            "UPDATE usuario SET activo = FALSE WHERE id_usuario = %s", (user_id,)
        ) > 0
