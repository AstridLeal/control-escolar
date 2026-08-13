# Rutas para gestionar asistencias
from flask import Blueprint, request, jsonify, session
from backend.models.asistencia import Asistencia
from backend.models.estudiante import Estudiante
from backend.routes.auth import require_auth

asistencias_bp = Blueprint('asistencias', __name__)

@asistencias_bp.route('/', methods=['GET']) # Listar asistencias con filtros opcionales
def listar():
    ok, err, code = require_auth(['admin', 'secretaria', 'docente', 'estudiante'])()
    if not ok:
        return err, code

    if session.get('rol') == 'estudiante':
        id_est = session.get('id_estudiante')
        if not id_est:
            return jsonify([])
        return jsonify(Asistencia.listar(id_estudiante=id_est))

    return jsonify(Asistencia.listar(
        fecha=request.args.get('fecha'),
        id_seccion=request.args.get('id_seccion', type=int),
        id_grado=request.args.get('id_grado', type=int),
        id_estudiante=request.args.get('id_estudiante', type=int),
        fecha_desde=request.args.get('fecha_desde'),
        fecha_hasta=request.args.get('fecha_hasta')
    ))


@asistencias_bp.route('/', methods=['POST']) # Registrar una nueva asistencia
def registrar():
    ok, err, code = require_auth(['admin', 'docente'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    for r in ['id_estudiante', 'fecha', 'estado']:
        if not data.get(r):
            return jsonify({'error': f'Campo requerido: {r}'}), 400
    aid = Asistencia.registrar(
        data['id_estudiante'], data['fecha'], data['estado'],
        data.get('id_seccion'), data.get('id_horario'),
        data.get('observacion'), session.get('user_id')
    )
    return jsonify({'id': aid, 'message': 'Asistencia registrada'}), 201



@asistencias_bp.route('/masivo', methods=['POST']) # Registrar múltiples asistencias
def registrar_masivo():
    ok, err, code = require_auth(['admin', 'docente'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    registros = data.get('registros', [])
    if not registros:
        return jsonify({'error': 'Lista de registros vacía'}), 400
    count = Asistencia.registrar_masivo(registros, session.get('user_id'))
    return jsonify({'message': f'{count} asistencias registradas'})



@asistencias_bp.route('/seccion/<int:id_seccion>/estudiantes', methods=['GET']) # Obtener estudiantes de una sección
def estudiantes_seccion(id_seccion):
    ok, err, code = require_auth(['admin', 'docente'])()
    if not ok:
        return err, code
    return jsonify(Estudiante.por_seccion(id_seccion))
