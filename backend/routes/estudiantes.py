# Rutas para gestionar estudiantes
from flask import Blueprint, request, jsonify
from backend.models.estudiante import Estudiante
from backend.routes.auth import require_auth
import csv, io

# Blueprint para las rutas de estudiantes
estudiantes_bp = Blueprint('estudiantes', __name__)

@estudiantes_bp.route('/', methods=['GET']) # Listar estudiantes
def listar():
    ok, err, code = require_auth(['admin', 'secretaria', 'docente'])()
    if not ok:
        return err, code
    return jsonify(Estudiante.listar())

@estudiantes_bp.route('/<int:est_id>', methods=['GET']) # Obtener un estudiante por ID
def obtener(est_id):
    ok, err, code = require_auth(['admin', 'secretaria', 'docente', 'estudiante'])()
    if not ok:
        return err, code
    est = Estudiante.obtener_por_id(est_id)
    if not est:
        return jsonify({'error': 'Estudiante no encontrado'}), 404
    return jsonify(dict(est))

@estudiantes_bp.route('/', methods=['POST']) # Crear un nuevo estudiante
def crear():
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    if not data.get('cedula') or not data.get('nombres') or not data.get('apellidos'):
        return jsonify({'error': 'Cédula, nombres y apellidos son requeridos'}), 400
    try:
        eid = Estudiante.crear(data)
        return jsonify({'id': eid, 'message': 'Estudiante registrado'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@estudiantes_bp.route('/masivo', methods=['POST']) # Crear estudiantes de forma masiva
def crear_masivo():
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    if 'file' not in request.files:
        return jsonify({'error': 'Archivo CSV requerido'}), 400
    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({'error': 'El archivo debe ser .csv'}), 400
    try:
        stream = io.StringIO(file.stream.read().decode('utf-8-sig'))
        reader = csv.DictReader(stream)
        lista = []
        for row in reader:
            lista.append({
                'cedula': row.get('cedula', '').strip(),
                'nombres': row.get('nombres', '').strip(),
                'apellidos': row.get('apellidos', '').strip(),
                'fecha_nacimiento': row.get('fecha_nacimiento') or None,
                'genero': row.get('genero'),
                'direccion': row.get('direccion'),
                'telefono': row.get('telefono'),
                'email': row.get('email'),
                'nombre_representante': row.get('nombre_representante'),
                'telefono_representante': row.get('telefono_representante'),
                'id_seccion': int(row['id_seccion']) if row.get('id_seccion') else None
            })
        count = Estudiante.crear_masivo(lista)
        return jsonify({'message': f'{count} estudiantes procesados', 'total': len(lista)})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@estudiantes_bp.route('/<int:est_id>', methods=['PUT']) # Actualizar un estudiante existente
def actualizar(est_id):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    if Estudiante.actualizar(est_id, data):
        return jsonify({'message': 'Estudiante actualizado'})
    return jsonify({'error': 'No se pudo actualizar'}), 400

@estudiantes_bp.route('/<int:est_id>', methods=['DELETE']) # Eliminar un estudiante
def eliminar(est_id):
    ok, err, code = require_auth(['admin'])()
    if not ok:
        return err, code
    if Estudiante.eliminar(est_id):
        return jsonify({'message': 'Estudiante desactivado'})
    return jsonify({'error': 'No se pudo eliminar'}), 400

@estudiantes_bp.route('/buscar', methods=['GET']) # Buscar estudiantes
def buscar():
    ok, err, code = require_auth(['admin', 'secretaria', 'docente'])()
    if not ok:
        return err, code
    termino = request.args.get('q', '')
    if len(termino) < 2:
        return jsonify([])
    return jsonify(Estudiante.buscar(termino))

@estudiantes_bp.route('/cedula/<cedula>', methods=['GET']) # Obtener un estudiante por cédula
def por_cedula(cedula):
    ok, err, code = require_auth(['admin', 'secretaria'])()
    if not ok:
        return err, code
    est = Estudiante.obtener_por_cedula(cedula)
    if not est:
        return jsonify({'error': 'No encontrado'}), 404
    return jsonify(dict(est))