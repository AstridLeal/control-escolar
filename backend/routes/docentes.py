# Rutas para manejar docentes
from flask import Blueprint, request, jsonify, session
from backend.models.docente import Docente
from backend.routes.auth import require_auth

# Blueprint para docentes (sirve para agrupar rutas relacionadas)
docentes_bp = Blueprint('docentes', __name__)

@docentes_bp.route('/', methods=['GET']) # Listar docentes
def listar():
    ok, err, code = require_auth(['admin', 'secretaria', 'docente'])()
    if not ok:
        return err, code
    return jsonify(Docente.listar())

@docentes_bp.route('/<int:doc_id>', methods=['GET']) # Obtener un docente por ID
def obtener(doc_id):
    ok, err, code = require_auth(['admin', 'secretaria', 'docente'])()
    if not ok:
        return err, code
    # Docente solo puede ver su propio perfil
    if session.get('rol') == 'docente' and session.get('id_docente') != doc_id:
        return jsonify({'error': 'No tiene permisos'}), 403
    doc = Docente.obtener_por_id(doc_id)
    if not doc:
        return jsonify({'error': 'Docente no encontrado'}), 404
    return jsonify(dict(doc) if not isinstance(doc, dict) else doc)

@docentes_bp.route('/', methods=['POST']) # Crear un nuevo docente
def crear():
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    if not data.get('cedula') or not data.get('nombres') or not data.get('apellidos'):
        return jsonify({'error': 'Cédula, nombres y apellidos son requeridos'}), 400
    try:
        did = Docente.crear(data)
        return jsonify({'id': did, 'message': 'Docente registrado'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@docentes_bp.route('/<int:doc_id>', methods=['PUT']) # Actualizar un docente existente
def actualizar(doc_id):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    if Docente.actualizar(doc_id, data):
        return jsonify({'message': 'Docente actualizado'})
    return jsonify({'error': 'No se pudo actualizar'}), 400

@docentes_bp.route('/<int:doc_id>', methods=['DELETE']) # Eliminar un docente
def eliminar(doc_id):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    if Docente.eliminar(doc_id):
        return jsonify({'message': 'Docente desactivado'})
    return jsonify({'error': 'No se pudo eliminar'}), 400

@docentes_bp.route('/<int:doc_id>/materias', methods=['GET']) # Obtener las materias de un docente
def materias(doc_id):
    ok, err, code = require_auth(['admin', 'docente'])()
    if not ok:
        return err, code
    if session.get('rol') == 'docente' and session.get('id_docente') != doc_id:
        return jsonify({'error': 'No tiene permisos'}), 403
    return jsonify(Docente.materias(doc_id))

@docentes_bp.route('/asignar-materia', methods=['POST']) # Asignar una materia a un docente
def asignar_materia():
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    if not data.get('id_docente') or not data.get('id_materia'):
        return jsonify({'error': 'id_docente e id_materia son requeridos'}), 400
    if Docente.asignar_materia(data['id_docente'], data['id_materia']):
        return jsonify({'message': 'Materia asignada'})
    return jsonify({'error': 'No se pudo asignar'}), 400
