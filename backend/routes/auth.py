# Rutas de autenticación y gestión de sesión
from flask import Blueprint, request, jsonify, session
from backend.models.usuario import Usuario

auth_bp = Blueprint('auth', __name__)

# Mapeo de roles a etiquetas legibles
ROL_LABELS = {
    'admin': 'Admin',
    'secretaria': 'Secretaria',
    'docente': 'Docente',
    'estudiante': 'Alumno'
}

@auth_bp.route('/login', methods=['POST']) # Endpoint para iniciar sesión
def login():
    data = request.get_json() or {}
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña requeridos'}), 400

    user = Usuario.autenticar(username, password)
    if not user:
        return jsonify({'error': 'Credenciales inválidas'}), 401

    session.permanent = True
    session['user_id'] = user['id_usuario']
    session['username'] = user['username']
    session['rol'] = user['rol']
    session['nombre'] = user.get('nombre_completo') or user['username']
    session['id_estudiante'] = user.get('id_estudiante')
    session['id_docente'] = user.get('id_docente')

    return jsonify({
        'message': 'Login exitoso',
        'user': {
            'id': user['id_usuario'],
            'username': user['username'],
            'nombre': user.get('nombre_completo') or user['username'],
            'rol': user['rol'],
            'rol_label': ROL_LABELS.get(user['rol'], user['rol']),
            'email': user.get('email'),
            'id_estudiante': user.get('id_estudiante'),
            'id_docente': user.get('id_docente')
        }
    })


@auth_bp.route('/logout', methods=['POST']) # Endpoint para cerrar sesión
def logout():
    session.clear()
    return jsonify({'message': 'Sesión cerrada'})


@auth_bp.route('/me', methods=['GET']) # Endpoint para obtener información del usuario autenticado
def me():
    if 'user_id' not in session:
        return jsonify({'error': 'No autenticado'}), 401
    user = Usuario.obtener_por_id(session['user_id'])
    if not user or not user.get('activo', True):
        session.clear()
        return jsonify({'error': 'Usuario no encontrado o inactivo'}), 401
    return jsonify({
        'id': user['id_usuario'],
        'username': user['username'],
        'nombre': user.get('nombre_completo') or user['username'],
        'rol': user['rol'],
        'rol_label': ROL_LABELS.get(user['rol'], user['rol']),
        'email': user.get('email'),
        'id_estudiante': user.get('id_estudiante'),
        'id_docente': user.get('id_docente')
    })

# Función para verificar autenticación y roles
def require_auth(roles=None):
    """roles: lista de roles permitidos, ej ['admin','secretaria']"""
    def check():
        if 'user_id' not in session:
            return False, jsonify({'error': 'No autenticado'}), 401
        if roles and session.get('rol') not in roles:
            return False, jsonify({'error': 'No tiene permisos para esta acción'}), 403
        return True, None, None
    return check
