# Rutas relacionadas con los pagos de estudiantes
from flask import Blueprint, request, jsonify, session, current_app, send_from_directory
from backend.models.pago import Pago
from backend.routes.auth import require_auth
from werkzeug.utils import secure_filename
import os
from datetime import datetime

# Blueprint para las rutas de pagos
pagos_bp = Blueprint('pagos', __name__)
ALLOWED = {'pdf'} # Extensiones permitidas para los comprobantes de pago

def allowed_file(filename): # Verifica si el archivo tiene una extensión permitida
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED

@pagos_bp.route('/', methods=['GET']) # Listar pagos con filtros opcionales
def listar():
    ok, err, code = require_auth(['admin', 'secretaria'])()
    if not ok:
        return err, code
    return jsonify(Pago.listar(
        id_estudiante=request.args.get('id_estudiante', type=int),
        estado=request.args.get('estado'),
        id_periodo=request.args.get('id_periodo', type=int),
        mes=request.args.get('mes'),
        anio=request.args.get('anio', type=int)
    ))

@pagos_bp.route('/', methods=['POST']) # Registrar un nuevo pago
def registrar():
    ok, err, code = require_auth(['admin', 'secretaria'])()
    if not ok:
        return err, code

    if request.content_type and 'multipart/form-data' in request.content_type:
        data = {
            'id_estudiante': request.form.get('id_estudiante', type=int),
            'id_periodo': request.form.get('id_periodo', type=int),
            'concepto': request.form.get('concepto', 'Mensualidad'),
            'mes': request.form.get('mes'),
            'anio': request.form.get('anio', type=int),
            'monto': request.form.get('monto', type=float),
            'fecha_pago': request.form.get('fecha_pago'),
            'fecha_vencimiento': request.form.get('fecha_vencimiento'),
            'estado': request.form.get('estado', 'Pagado'),
            'metodo_pago': request.form.get('metodo_pago'),
            'referencia': request.form.get('referencia'),
            'observacion': request.form.get('observacion'),
            'registrado_por': session.get('user_id')
        }
        if 'comprobante' in request.files:
            f = request.files['comprobante']
            if f and f.filename and allowed_file(f.filename):
                fname = secure_filename(
                    f"pago_{data['id_estudiante']}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
                )
                folder = current_app.config.get('UPLOAD_FOLDER', 'frontend/uploads')
                os.makedirs(folder, exist_ok=True)
                f.save(os.path.join(folder, fname))
                data['comprobante'] = fname
    else:
        data = request.get_json() or {}
        data['registrado_por'] = session.get('user_id')

    if not data.get('id_estudiante') or not data.get('monto'):
        return jsonify({'error': 'id_estudiante y monto son requeridos'}), 400
    try:
        pid = Pago.registrar(data)
        return jsonify({'id': pid, 'message': 'Pago registrado'}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@pagos_bp.route('/<int:id_pago>', methods=['PUT']) # Actualizar un pago existente
def actualizar(id_pago):
    ok, err, code = require_auth(['admin', 'secretaria'])()
    if not ok:
        return err, code
    data = request.get_json() or {}
    if Pago.actualizar_estado(id_pago, data.get('estado'), data.get('fecha_pago'), data.get('comprobante')):
        return jsonify({'message': 'Pago actualizado'})
    return jsonify({'error': 'No se pudo actualizar'}), 400

@pagos_bp.route('/dashboard', methods=['GET']) # Obtener datos para el dashboard de pagos y morosidad
def dashboard():
    ok, err, code = require_auth(['admin', 'secretaria'])()
    if not ok:
        return err, code
    return jsonify(Pago.dashboard_morosos(request.args.get('id_periodo', type=int)))

@pagos_bp.route('/comprobante/<path:filename>', methods=['GET']) # Descargar un comprobante de pago
def descargar_comprobante(filename):
    ok, err, code = require_auth(['admin', 'secretaria'])()
    if not ok:
        return err, code
    folder = current_app.config.get('UPLOAD_FOLDER', 'frontend/uploads')
    return send_from_directory(folder, filename)