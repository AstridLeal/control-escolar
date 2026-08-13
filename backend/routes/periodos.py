# Rutas relacionadas con periodos académicos, grados, materias, secciones y horarios
from flask import Blueprint, request, jsonify, session
from backend.models.periodo import Periodo
from backend.models.curso import Materia, Grado, Seccion, Horario
from backend.routes.auth import require_auth

# Blueprint para las rutas de periodos académicos
periodos_bp = Blueprint('periodos', __name__)

# ---- Periodos ----
@periodos_bp.route('/periodos', methods=['GET']) # Listar periodos académicos
def listar_periodos():
    ok, err, code = require_auth(['admin', 'secretaria', 'docente', 'estudiante'])()
    if not ok:
        return err, code
    return jsonify(Periodo.listar())

@periodos_bp.route('/periodos/activo', methods=['GET']) # Obtener el periodo académico activo
def periodo_activo():
    ok, err, code = require_auth(['admin', 'secretaria', 'docente', 'estudiante'])()
    if not ok:
        return err, code
    p = Periodo.obtener_activo()
    return jsonify(dict(p) if p else None)

@periodos_bp.route('/periodos', methods=['POST']) # Crear un nuevo periodo académico
def crear_periodo():
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    if not data.get('nombre') or not data.get('fecha_inicio') or not data.get('fecha_fin'):
        return jsonify({'error': 'Nombre, fecha inicio y fin son requeridos'}), 400
    pid = Periodo.crear(data['nombre'], data['fecha_inicio'], data['fecha_fin'], data.get('activo', False))
    return jsonify({'id': pid, 'message': 'Periodo creado'}), 201

@periodos_bp.route('/periodos/<int:periodo_id>', methods=['PUT']) # Actualizar un periodo académico existente
def actualizar_periodo(periodo_id):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    if Periodo.actualizar(periodo_id, data):
        return jsonify({'message': 'Periodo actualizado'})
    return jsonify({'error': 'No se pudo actualizar'}), 400

@periodos_bp.route('/periodos/<int:periodo_id>', methods=['DELETE']) # Eliminar un periodo académico existente
def eliminar_periodo(periodo_id):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    try:
        if Periodo.eliminar(periodo_id):
            return jsonify({'message': 'Periodo eliminado'})
        return jsonify({'error': 'No se pudo eliminar'}), 400
    except Exception:
        return jsonify({'error': 'No se puede eliminar: tiene datos asociados'}), 400

# ---- Grados ----
@periodos_bp.route('/grados', methods=['GET']) # Listar grados académicos
def listar_grados():
    ok, err, code = require_auth(['admin', 'secretaria', 'docente'])()
    if not ok:
        return err, code
    return jsonify(Grado.listar())

# ---- Materias (antes cursos) ----
@periodos_bp.route('/materias', methods=['GET']) # Listar materias con filtros opcionales
def listar_materias():
    ok, err, code = require_auth(['admin', 'secretaria', 'docente'])()
    if not ok:
        return err, code
    id_grado = request.args.get('id_grado', type=int)
    id_docente = request.args.get('id_docente', type=int)
    # Docente solo ve sus materias asignadas
    if session.get('rol') == 'docente':
        id_docente = session.get('id_docente')
        if not id_docente:
            return jsonify([])
    return jsonify(Materia.listar(id_grado, id_docente))

@periodos_bp.route('/materias', methods=['POST']) # Crear una nueva materia
def crear_materia():
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    if not data.get('nombre'):
        return jsonify({'error': 'Nombre es requerido'}), 400
    mid = Materia.crear(
        data['nombre'], data.get('codigo'), data.get('horas_semana', 0),
        data.get('id_docente'), data.get('id_grado'), data.get('descripcion')
    )
    return jsonify({'id': mid, 'message': 'Materia creada'}), 201

@periodos_bp.route('/materias/<int:id_materia>', methods=['PUT']) # Actualizar una materia existente
def actualizar_materia(id_materia):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    if Materia.actualizar(id_materia, data):
        return jsonify({'message': 'Materia actualizada'})
    return jsonify({'error': 'No se pudo actualizar'}), 400

@periodos_bp.route('/materias/<int:id_materia>', methods=['DELETE']) # Eliminar una materia existente
def eliminar_materia(id_materia):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    try:
        if Materia.eliminar(id_materia):
            return jsonify({'message': 'Materia eliminada'})
        return jsonify({'error': 'No se pudo eliminar'}), 400
    except Exception:
        return jsonify({'error': 'No se puede eliminar: tiene datos asociados'}), 400

# ---- Secciones ---- 
@periodos_bp.route('/secciones', methods=['GET']) # Listar secciones con filtros opcionales
def listar_secciones():
    ok, err, code = require_auth(['admin', 'secretaria', 'docente'])()
    if not ok:
        return err, code
    id_periodo = request.args.get('id_periodo', type=int)
    id_grado = request.args.get('id_grado', type=int)
    return jsonify(Seccion.listar(id_periodo, id_grado))

@periodos_bp.route('/secciones', methods=['POST']) # Crear una nueva sección
def crear_seccion():
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    for r in ['nombre', 'id_grado', 'id_periodo']:
        if not data.get(r):
            return jsonify({'error': f'Campo requerido: {r}'}), 400
    try:
        sid = Seccion.crear(
            data['nombre'], data['id_grado'], data['id_periodo'],
            data.get('capacidad_max', 30)
        )
        return jsonify({'id': sid, 'message': 'Sección creada'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@periodos_bp.route('/secciones/<int:id_seccion>', methods=['PUT']) # Actualizar una sección existente
def actualizar_seccion(id_seccion):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    if Seccion.actualizar(id_seccion, data):
        return jsonify({'message': 'Sección actualizada'})
    return jsonify({'error': 'No se pudo actualizar'}), 400

@periodos_bp.route('/secciones/<int:id_seccion>', methods=['DELETE']) # Eliminar una sección existente
def eliminar_seccion(id_seccion):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    try:
        if Seccion.eliminar(id_seccion):
            return jsonify({'message': 'Sección eliminada'})
        return jsonify({'error': 'No se pudo eliminar'}), 400
    except Exception:
        return jsonify({'error': 'No se puede eliminar: tiene datos asociados'}), 400

# ---- Horarios ----
@periodos_bp.route('/horarios', methods=['GET']) # Listar horarios con filtros opcionales
def listar_horarios():
    ok, err, code = require_auth(['admin', 'secretaria', 'docente'])()
    if not ok:
        return err, code
    id_seccion = request.args.get('id_seccion', type=int)
    id_materia = request.args.get('id_materia', type=int)
    return jsonify(Horario.listar(id_seccion, id_materia))

@periodos_bp.route('/horarios', methods=['POST']) # Crear un nuevo horario
def crear_horario():
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    for r in ['id_materia', 'id_seccion', 'dia_semana', 'hora_inicio', 'hora_fin']:
        if not data.get(r):
            return jsonify({'error': f'Campo requerido: {r}'}), 400
    try:
        hid = Horario.crear(
            data['id_materia'], data['id_seccion'], data['dia_semana'],
            data['hora_inicio'], data['hora_fin'], data.get('aula')
        )
        return jsonify({'id': hid, 'message': 'Horario creado'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@periodos_bp.route('/horarios/<int:id_horario>', methods=['DELETE']) # Eliminar un horario existente
def eliminar_horario(id_horario):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    if Horario.eliminar(id_horario):
        return jsonify({'message': 'Horario eliminado'})
    return jsonify({'error': 'No se pudo eliminar'}), 400