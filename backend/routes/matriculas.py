# Rutas relacionadas con la matrícula de estudiantes
from flask import Blueprint, request, jsonify
from backend.models.estudiante import Estudiante
from backend.routes.auth import require_auth

# Blueprint para las rutas de matrícula
matriculas_bp = Blueprint('matriculas', __name__)

@matriculas_bp.route('/', methods=['GET']) # Listar estudiantes matriculados con filtros opcionales
def listar():
    """Lista estudiantes matriculados (con sección asignada)"""
    ok, err, code = require_auth(['admin', 'secretaria'])()
    if not ok:
        return err, code
    estudiantes = Estudiante.listar()
    matriculados = [e for e in estudiantes if e.get('id_seccion')]

    id_periodo = request.args.get('id_periodo', type=int)
    id_seccion = request.args.get('id_seccion', type=int)
    id_grado = request.args.get('id_grado', type=int)

    if id_seccion:
        matriculados = [e for e in matriculados if e.get('id_seccion') == id_seccion]
    if id_grado:
        matriculados = [e for e in matriculados if e.get('id_grado') == id_grado]
    if id_periodo:
        matriculados = [e for e in matriculados if e.get('id_periodo') == id_periodo]

    return jsonify(matriculados)

@matriculas_bp.route('/', methods=['POST']) # Matricular un estudiante (por cédula o por ID)
def matricular():
    ok, err, code = require_auth(['admin', 'secretaria'])()
    if not ok:
        return err, code
    data = request.get_json() or {}

    if data.get('cedula'):
        if not data.get('id_seccion'):
            return jsonify({'error': 'id_seccion es requerido'}), 400
        eid, error = Estudiante.matricular(data['cedula'], data['id_seccion'])
        if error:
            return jsonify({'error': error}), 404 if 'no encontrado' in error.lower() else 400
        return jsonify({'id': eid, 'message': 'Estudiante matriculado'}), 201

    if data.get('id_estudiante') and data.get('id_seccion'):
        if Estudiante.actualizar(data['id_estudiante'], {
            'id_seccion': data['id_seccion'],
            'activo': True
        }):
            return jsonify({'id': data['id_estudiante'], 'message': 'Estudiante matriculado'}), 201
        return jsonify({'error': 'No se pudo matricular'}), 400

    return jsonify({'error': 'Proporcione cedula+id_seccion o id_estudiante+id_seccion'}), 400

@matriculas_bp.route('/retirar/<int:id_estudiante>', methods=['POST']) # Retirar la matrícula de un estudiante
def retirar(id_estudiante):
    ok, err, code = require_auth(['admin', 'secretaria'])()
    if not ok:
        return err, code
    if Estudiante.actualizar(id_estudiante, {'id_seccion': None}):
        return jsonify({'message': 'Matrícula retirada'})
    return jsonify({'error': 'No se pudo retirar'}), 400