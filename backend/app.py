# Sirve para importar las funciones de la base de datos desde el módulo utils.database
import os
import sys
from datetime import timedelta

# Dirección base del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, BASE_DIR) # Agregar la ruta base al sys.path para importar módulos desde el directorio raíz

from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
from dotenv import load_dotenv

# Cargar variables de entorno desde un archivo .env
load_dotenv(os.path.join(BASE_DIR, '.env'))

from backend.routes.auth import auth_bp
from backend.routes.usuarios import usuarios_bp
from backend.routes.estudiantes import estudiantes_bp
from backend.routes.docentes import docentes_bp
from backend.routes.periodos import periodos_bp
from backend.routes.asistencias import asistencias_bp
from backend.routes.calificaciones import calificaciones_bp
from backend.routes.pagos import pagos_bp
from backend.routes.matriculas import matriculas_bp
from backend.routes.reportes import reportes_bp

# Crear la aplicación Flask y configurar las rutas y la seguridad
def create_app():
    app = Flask(
        __name__,
        static_folder=os.path.join(BASE_DIR, 'frontend'),
        static_url_path=''
    )
    app.secret_key = os.getenv('SECRET_KEY', 'clave_secreta_control_escolar_2024')
    app.config['UPLOAD_FOLDER'] = os.path.join(
        BASE_DIR, os.getenv('UPLOAD_FOLDER', 'frontend/uploads')
    )
    app.config['MAX_CONTENT_LENGTH'] = int(os.getenv('MAX_CONTENT_LENGTH', 16 * 1024 * 1024))
    app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=8)
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_HTTPONLY'] = True

    CORS(app, supports_credentials=True,
         origins=['http://localhost:5000', 'http://127.0.0.1:5000'])

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(usuarios_bp, url_prefix='/api/usuarios')
    app.register_blueprint(estudiantes_bp, url_prefix='/api/estudiantes')
    app.register_blueprint(docentes_bp, url_prefix='/api/docentes')
    app.register_blueprint(periodos_bp, url_prefix='/api')
    app.register_blueprint(asistencias_bp, url_prefix='/api/asistencias')
    app.register_blueprint(calificaciones_bp, url_prefix='/api/calificaciones')
    app.register_blueprint(pagos_bp, url_prefix='/api/pagos')
    app.register_blueprint(matriculas_bp, url_prefix='/api/matriculas')
    app.register_blueprint(reportes_bp, url_prefix='/api/reportes')

    @app.route('/') # Servir el archivo index.html para la ruta raíz
    def index():
        return send_from_directory(app.static_folder, 'index.html')

    @app.route('/<path:path>') # Servir archivos estáticos o index.html para rutas no encontradas
    def static_files(path):
        if path.startswith('api/'):
            return jsonify({'error': 'No encontrado'}), 404
        file_path = os.path.join(app.static_folder, path)
        if os.path.isfile(file_path):
            return send_from_directory(app.static_folder, path)
        return send_from_directory(app.static_folder, 'index.html')

    @app.errorhandler(404) # Manejar errores 404 (no encontrado)
    def not_found(e):
        return jsonify({'error': 'Recurso no encontrado'}), 404

    @app.errorhandler(500) # Manejar errores 500 (error interno del servidor)
    def server_error(e):
        return jsonify({'error': 'Error interno del servidor'}), 500

    return app

# Ejecutar la aplicación Flask si se ejecuta directamente
if __name__ == '__main__':
    app = create_app()
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    print("=" * 50)
    print("  SISTEMA DE CONTROL ESCOLAR")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=True, host='0.0.0.0', port=5000)