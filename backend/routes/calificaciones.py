# Rutas para manejar calificaciones 
from flask import Blueprint, request, jsonify, session
from backend.models.calificacion import Calificacion
from backend.models.curso import Materia
from backend.routes.auth import require_auth

# Blueprint para calificaciones (sirve para agrupar rutas relacionadas)
calificaciones_bp = Blueprint('calificaciones', __name__)

def _docente_puede_materia(id_materia): # Verifica si el docente tiene permiso sobre la materia
    """Admin siempre puede; docente solo si la materia está asignada a él."""
    if session.get('rol') == 'admin':
        return True
    if session.get('rol') != 'docente':
        return False
    id_doc = session.get('id_docente')
    if not id_doc:
        return False
    mat = Materia.obtener_por_id(id_materia)
    if not mat:
        return False
    return mat.get('id_docente') == id_doc



@calificaciones_bp.route('/', methods=['GET']) # Listar calificaciones con filtros opcionales
def listar():
    ok, err, code = require_auth(['admin', 'secretaria', 'docente', 'estudiante'])()
    if not ok:
        return err, code

    id_periodo = request.args.get('id_periodo', type=int)
    id_materia = request.args.get('id_materia', type=int)
    id_seccion = request.args.get('id_seccion', type=int)
    id_estudiante = request.args.get('id_estudiante', type=int)

    if session.get('rol') == 'estudiante':
        id_est = session.get('id_estudiante')
        if not id_est:
            return jsonify([])
        return jsonify(Calificacion.listar(
            id_estudiante=id_est,
            id_periodo=id_periodo,
            id_materia=id_materia
        ))

    return jsonify(Calificacion.listar(
        id_estudiante=id_estudiante,
        id_materia=id_materia,
        id_periodo=id_periodo,
        id_seccion=id_seccion
    ))



@calificaciones_bp.route('/', methods=['POST']) # Guardar una nueva calificación
def guardar():
    ok, err, code = require_auth(['admin', 'docente'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    for r in ['id_estudiante', 'id_materia', 'id_periodo']:
        if not data.get(r):
            return jsonify({'error': f'Campo requerido: {r}'}), 400
    if not _docente_puede_materia(data['id_materia']):
        return jsonify({'error': 'No tiene permiso sobre esta materia'}), 403
    cid = Calificacion.guardar(
        data['id_estudiante'], data['id_materia'], data['id_periodo'],
        data.get('nota1'), data.get('nota2'), data.get('nota3'),
        data.get('examen_final'), data.get('observacion'), session.get('user_id')
    )
    return jsonify({'id': cid, 'message': 'Calificación guardada'}), 201



@calificaciones_bp.route('/acta', methods=['GET']) # Generar acta de calificaciones
def acta():
    ok, err, code = require_auth(['admin', 'docente', 'secretaria'])()
    if not ok:
        return err, code
    id_materia = request.args.get('id_materia', type=int)
    id_seccion = request.args.get('id_seccion', type=int)
    id_periodo = request.args.get('id_periodo', type=int)
    if not all([id_materia, id_seccion, id_periodo]):
        return jsonify({'error': 'id_materia, id_seccion e id_periodo son requeridos'}), 400
    if session.get('rol') == 'docente' and not _docente_puede_materia(id_materia):
        return jsonify({'error': 'No tiene permiso sobre esta materia'}), 403
    return jsonify(Calificacion.acta(id_materia, id_seccion, id_periodo))