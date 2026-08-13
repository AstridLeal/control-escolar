# Sistema de Control Escolar

Sistema integral para gestión académica y administrativa.
Proyecto integrador de la materia "Aplicaciones de la Ingeniería en Software".

## Características
- Gestión de estudiantes, docentes y cursos
- Registro de calificaciones
- Gestión de pagos
- Reportes en PDF/Excel

## Instalación
```bash
git clone https://github.com/tu-usuario/control-escolar.git
cd control-escolar
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
python setup_db.py             # Para cargar datos demo
python backend/app.py
# http://localhost:5000