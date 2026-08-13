# Rutas para la gestión de usuarios
from flask import Blueprint, request, jsonify, session
from backend.models.usuario import Usuario
from backend.routes.auth import require_auth

# Blueprint para las rutas de usuarios
usuarios_bp = Blueprint('usuarios', __name__)

# Rutas para listar, crear, actualizar y eliminar usuarios
@usuarios_bp.route('/', methods=['GET'])
def listar():
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    return jsonify(Usuario.listar())

@usuarios_bp.route('/', methods=['POST'])
def crear():
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    for r in ['username', 'password', 'nombre_completo', 'rol']:
        if not data.get(r):
            return jsonify({'error': f'Campo requerido: {r}'}), 400
    try:
        uid = Usuario.crear(
            data['username'], data['password'], data['nombre_completo'],
            data['rol'], data.get('email'),
            data.get('id_estudiante'), data.get('id_docente')
        )
        return jsonify({'id': uid, 'message': 'Usuario creado'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@usuarios_bp.route('/<int:user_id>', methods=['PUT'])
def actualizar(user_id):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    if Usuario.actualizar(user_id, data):
        return jsonify({'message': 'Usuario actualizado'})
    return jsonify({'error': 'No se pudo actualizar'}), 400

@usuarios_bp.route('/<int:user_id>', methods=['DELETE'])
def eliminar(user_id):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    if user_id == session.get('user_id'):
        return jsonify({'error': 'No puede eliminarse a sí mismo'}), 400
    if Usuario.eliminar(user_id):
        return jsonify({'message': 'Usuario desactivado'})
    return jsonify({'error': 'No se pudo eliminar'}), 400