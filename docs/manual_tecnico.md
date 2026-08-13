# Manual Técnico  
## Sistema de Control Escolar

**Versión del documento:** 1.0  
**Stack:** Python 3 · Flask · PostgreSQL · HTML/CSS/JavaScript  
**Arquitectura:** Tres capas (Presentación · Negocio · Datos) + API REST

---

## Índice

1. [Propósito y alcance técnico](#1-propósito-y-alcance-técnico)
2. [Arquitectura del sistema](#2-arquitectura-del-sistema)
3. [Estructura de directorios](#3-estructura-de-directorios)
4. [Descripción de archivos](#4-descripción-de-archivos)
5. [Modelo de datos](#5-modelo-de-datos)
6. [Capa de negocio y API REST](#6-capa-de-negocio-y-api-rest)
7. [Autenticación y autorización](#7-autenticación-y-autorización)
8. [Frontend (SPA)](#8-frontend-spa)
9. [Configuración e instalación](#9-configuración-e-instalación)
10. [Script setup_db.py](#10-script-setup_dbpy)
11. [Exportaciones PDF/Excel](#11-exportaciones-pdfexcel)
12. [Decisiones de diseño](#12-decisiones-de-diseño)
13. [Pruebas](#13-pruebas)
14. [Despliegue y operación](#14-despliegue-y-operación)
15. [Mantenimiento y extensión](#15-mantenimiento-y-extensión)
16. [Troubleshooting técnico](#16-troubleshooting-técnico)
17. [Anexos](#17-anexos)

---

## 1. Propósito y alcance técnico

### 1.1 Objetivo

Documentar la implementación del **Sistema de Control Escolar** para que un desarrollador o administrador de sistemas pueda instalarlo, operarlo, depurarlo y extenderlo.

### 1.2 Alcance funcional implementado

- Gestión de periodos, grados, secciones (primaria A/B), materias, estudiantes, docentes.
- Asistencias, calificaciones (actas), pagos con comprobante PDF.
- Usuarios con roles y vínculo a estudiante/docente.
- Exportación Excel/PDF con filtros.
- Datos de demostración (ene–ago 2026, periodo 2026-2027).

### 1.3 Fuera de alcance técnico actual

- Autenticación JWT / OAuth.
- Colas de trabajo o microservicios.
- Aplicación móvil nativa.
- Multi-tenant (varios colegios en una sola BD con aislamiento).

---

## 2. Arquitectura del sistema

### 2.1 Vista lógica (3 capas)

```
┌──────────────────────────────────────────────────────────────┐
│ PRESENTACIÓN                                                 │
│  frontend/index.html · css/style.css · js/app.js             │
│  - SPA por roles                                             │
│  - Comunicación exclusivamente vía fetch + cookies           │
└────────────────────────────┬─────────────────────────────────┘
                             │ HTTP/JSON  (prefijo /api)
┌────────────────────────────▼─────────────────────────────────┐
│ NEGOCIO                                                      │
│  backend/app.py          → fábrica de app, estáticos         │
│  backend/routes/*.py     → endpoints, validación, roles      │
│  backend/models/*.py     → reglas de dominio + SQL           │
│  backend/utils/*         → BD, serialización                 │
└────────────────────────────┬─────────────────────────────────┘
                             │ SQL (psycopg2)
┌────────────────────────────▼─────────────────────────────────┐
│ DATOS                                                        │
│  PostgreSQL  ·  database/schema.sql                          │
│  uploads/    ·  comprobantes PDF                             │
└──────────────────────────────────────────────────────────────┘
```

### 2.2 Estilo arquitectónico

| Aspecto | Elección |
|---------|----------|
| Estilo | Monolito modular con API REST |
| UI | SPA ligera sin framework JS (vanilla) |
| Persistencia | PostgreSQL relacional |
| Sesión | Server-side (Flask session + cookie firmada) |
| Archivos | Sistema de archivos local (`uploads/`) |

### 2.3 Flujo de una petición autenticada

1. Navegador envía `GET/POST /api/...` con cookie de sesión.
2. Blueprint correspondiente recibe la petición.
3. `require_auth(roles)` valida `session['user_id']` y `session['rol']`.
4. Se validan parámetros / JSON.
5. El **modelo** ejecuta SQL mediante `execute_query`.
6. Respuesta `jsonify(...)` o archivo (PDF/Excel).
7. El frontend actualiza el DOM.

### 2.4 Diagrama de contexto

```
[Usuarios: Admin, Secretaría, Docente, Alumno]
                    │
                    ▼
            [Navegador Web]
                    │
                    ▼
         [Flask App :5000]
            /api/*  |  estáticos
                    │
          ┌─────────┴─────────┐
          ▼                   ▼
   [PostgreSQL]          [uploads/]
```

---

## 3. Estructura de directorios

```
control-escolar/
├── backend/
│   ├── app.py                 # Entry point Flask
│   ├── __init__.py
│   ├── models/                # Capa de datos / dominio
│   │   ├── asistencia.py
│   │   ├── calificacion.py
│   │   ├── curso.py           # Materia, Grado, Seccion, Horario
│   │   ├── docente.py
│   │   ├── estudiante.py
│   │   ├── pago.py
│   │   ├── periodo.py
│   │   └── usuario.py
│   ├── routes/                # Capa API REST
│   │   ├── auth.py
│   │   ├── asistencias.py
│   │   ├── calificaciones.py
│   │   ├── docentes.py
│   │   ├── estudiantes.py
│   │   ├── matriculas.py
│   │   ├── pagos.py
│   │   ├── periodos.py
│   │   ├── reportes.py
│   │   └── usuarios.py
│   └── utils/
│       ├── database.py        # Conexión y execute_query
│       └── serializers.py
├── frontend/
│   ├── index.html
│   ├── css/style.css
│   └── js/app.js
├── database/
│   └── schema.sql
├── docs/
│   ├── manual_usuario.md
│   ├── manual_tecnico.md      # este documento
│   └── ejemplo_estudiantes.csv
├── uploads/                   # PDF de pagos (runtime)
├── setup_db.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

---

## 4. Descripción de archivos

### 4.1 `backend/app.py`

Responsabilidades:

- Cargar variables de entorno (`.env`).
- Instanciar `Flask`.
- Configurar `SECRET_KEY`, carpeta `uploads`, límite de carga.
- Registrar blueprints bajo prefijos `/api/...`.
- Servir `frontend/` (SPA) y archivos de `uploads/`.
- Punto de ejecución: `python backend/app.py` (host/port configurables).

### 4.2 `backend/utils/database.py`

- Lee `DB_HOST`, `DB_PORT`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`.
- Abre conexiones `psycopg2` (cursor tipo diccionario cuando aplica).
- Expone `execute_query(sql, params, fetch_one=False, fetch_all=False)`.
- Normaliza tipos no JSON-nativos (date, datetime, Decimal, RealDictRow).

### 4.3 Modelos (`backend/models/`)

Cada modelo encapsula SQL de una entidad:

| Modelo | Operaciones típicas |
|--------|---------------------|
| `Usuario` | crear, autenticar, listar, actualizar, eliminar (soft) |
| `Periodo` | CRUD, activar |
| `Materia` / `Grado` / `Seccion` / `Horario` (`curso.py`) | CRUD y listados con JOIN |
| `Estudiante` | CRUD, búsqueda, import CSV |
| `Docente` | CRUD, asignar materia |
| `Asistencia` | registrar, masivo, listar con filtros, unique (estudiante, fecha) |
| `Calificacion` | guardar (upsert lógico), acta por sección, listar |
| `Pago` | registrar, actualizar, dashboard, morosos |

### 4.4 Rutas (`backend/routes/`)

Traducen HTTP → llamadas a modelos. Aplican `require_auth` y validaciones de entrada.

### 4.5 Frontend

| Archivo | Rol |
|---------|-----|
| `index.html` | Shell: login, sidebar, content, modal |
| `style.css` | Tema visual, grids, tablas, badges, responsive |
| `app.js` | Estado `currentUser`, `MENU` por rol, `api()`, `navigate()`, renders de cada módulo |

### 4.6 `database/schema.sql`

- `CREATE TABLE IF NOT EXISTS` de todas las entidades.
- Índices en FKs y campos de búsqueda frecuentes.
- Seeds: periodo 2026-2027, grados primaria, secciones A/B, materias base, docente(s) demo.

### 4.7 `setup_db.py`

Orquestador de inicialización (ver sección 10).

---

## 5. Modelo de datos

### 5.1 Diagrama entidad-relación (textual)

```
periodo_academico ──┬──< seccion >── grado
                    │
estudiante >────────┘
    │
    ├──< asistencia
    ├──< calificacion >── materia >── docente
    │                       │
    │                       └── grado
    └──< pago

usuario ── (opcional) id_estudiante | id_docente
```

### 5.2 Tablas principales

#### `periodo_academico`
| Columna | Tipo | Notas |
|---------|------|-------|
| id_periodo | SERIAL PK | |
| nombre | VARCHAR | ej. 2026-2027 |
| fecha_inicio, fecha_fin | DATE | |
| activo | BOOLEAN | un periodo operativo |

#### `grado`
| Columna | Tipo | Notas |
|---------|------|-------|
| id_grado | SERIAL PK | |
| nombre | VARCHAR | 1ro, 2do, … |
| nivel | VARCHAR | Primaria |
| orden | INT | para ordenar |

#### `seccion`
| Columna | Tipo | Notas |
|---------|------|-------|
| id_seccion | SERIAL PK | |
| nombre | VARCHAR | A / B |
| id_grado | FK | |
| id_periodo | FK | |
| capacidad_max | INT | |
| UNIQUE (nombre, id_grado, id_periodo) | | |

#### `estudiante`
| Columna | Tipo | Notas |
|---------|------|-------|
| id_estudiante | SERIAL PK | |
| cedula | VARCHAR UNIQUE | |
| nombres, apellidos | VARCHAR | |
| fecha_nacimiento | DATE | |
| genero | CHAR | |
| id_seccion | FK nullable | sección actual |
| activo | BOOLEAN | baja lógica |
| representante, teléfonos, email, dirección | | |

#### `docente`
Similar a estudiante en datos personales; `activo` para baja lógica.

#### `materia`
| Columna | Tipo | Notas |
|---------|------|-------|
| id_materia | SERIAL PK | |
| nombre, codigo | VARCHAR | |
| horas_semana | INT | |
| id_docente | FK nullable | asignación |
| id_grado | FK nullable | |
| descripcion | TEXT | |
| created_at | TIMESTAMP | |

> **Migración:** instalaciones antiguas podían tener columna `docente` en lugar de `id_docente`/`id_grado`. `setup_db.py` corrige el esquema.

#### `asistencia`
| Columna | Tipo | Notas |
|---------|------|-------|
| id_asistencia | SERIAL PK | |
| id_estudiante | FK | |
| id_seccion | FK | |
| fecha | DATE | |
| estado | VARCHAR | Asistió, Falta, Tardanza, Justificado |
| observacion | TEXT | |
| UNIQUE (id_estudiante, fecha) | | Una marca por día |

#### `calificacion`
| Columna | Tipo | Notas |
|---------|------|-------|
| id_calificacion | SERIAL PK | |
| id_estudiante, id_materia, id_periodo | FK | |
| nota1, nota2, nota3, examen_final, nota_final | NUMERIC | |
| UNIQUE (id_estudiante, id_materia, id_periodo) | | |

#### `pago`
| Columna | Tipo | Notas |
|---------|------|-------|
| id_pago | SERIAL PK | |
| id_estudiante, id_periodo | FK | |
| concepto, mes, anio | | Matrícula / Mensualidad |
| monto | NUMERIC | |
| fecha_pago, fecha_vencimiento | DATE | |
| estado | VARCHAR | Pagado, Pendiente, Vencido, … |
| metodo_pago, referencia | | |
| comprobante | VARCHAR | nombre de archivo en `uploads/` |

#### `usuario`
| Columna | Tipo | Notas |
|---------|------|-------|
| id_usuario | SERIAL PK | |
| username | UNIQUE | |
| password_hash | VARCHAR | Werkzeug |
| rol | VARCHAR | admin, secretaria, docente, estudiante |
| id_estudiante | FK nullable | |
| id_docente | FK nullable | |
| activo | BOOLEAN | |

### 5.3 Integridad

- FKs con `ON DELETE` adecuado (CASCADE o SET NULL según el caso).
- Unicidad de cédulas y de combinaciones de negocio (asistencia diaria, nota por materia/periodo).
- Soft delete en usuarios/estudiantes/docentes vía `activo = FALSE` donde aplica.

---

## 6. Capa de negocio y API REST

Prefijo base: **`/api`**

### 6.1 Autenticación — `auth_bp`

| Método | Ruta | Descripción |
|--------|------|-------------|
| POST | `/api/auth/login` | Body: `{username, password}` → session |
| POST | `/api/auth/logout` | Limpia session |
| GET | `/api/auth/me` | Usuario actual |

### 6.2 Periodos y estructura académica — `periodos_bp`

| Método | Ruta | Roles |
|--------|------|-------|
| GET | `/api/periodos` | admin, secretaria, docente, **estudiante** |
| GET | `/api/periodos/activo` | todos autenticados |
| POST/PUT/DELETE | `/api/periodos`, `/api/periodos/<id>` | admin |
| GET | `/api/grados` | admin, secretaria, docente |
| GET/POST/PUT/DELETE | `/api/materias` … | GET: admin/secretaria/docente; escritura: admin |
| GET/POST/PUT/DELETE | `/api/secciones` … | similar |

**Regla especial:** si `session['rol'] == 'docente'`, `GET /api/materias` fuerza filtro `id_docente = session['id_docente']`.

### 6.3 Estudiantes — `estudiantes_bp`

CRUD + endpoint de importación CSV. Roles: admin, secretaria (lectura también para docente en listados necesarios para asistencias).

### 6.4 Docentes — `docentes_bp`

CRUD + `POST` asignar materia. Solo admin para escritura.

### 6.5 Asistencias — `asistencias_bp`

| Método | Ruta | Roles escritura |
|--------|------|-----------------|
| GET | `/api/asistencias/` | lectura amplia; alumno solo las suyas |
| POST | `/api/asistencias/` | admin, docente |
| POST | `/api/asistencias/masivo` | admin, docente |
| GET | `/api/asistencias/seccion/<id>/estudiantes` | lista para pasar lista |

### 6.6 Calificaciones — `calificaciones_bp`

| Método | Ruta | Notas |
|--------|------|-------|
| GET | `/api/calificaciones/` | Filtros query; alumno acotado a `id_estudiante` de sesión |
| POST | `/api/calificaciones/` | admin, docente; valida materia del docente |
| GET | `/api/calificaciones/acta` | admin, docente, **secretaria** (lectura) |

Función auxiliar `_docente_puede_materia(id_materia)` evita captura en materias ajenas.

### 6.7 Pagos — `pagos_bp`

- Listado, alta (multipart si hay PDF), actualización.
- `GET /api/pagos/dashboard` → resumen + morosos.
- `GET /api/pagos/comprobante/<filename>` → descarga segura del archivo.

### 6.8 Usuarios — `usuarios_bp`

Solo **admin**. Acepta `id_estudiante` / `id_docente` en crear y actualizar.

### 6.9 Matrículas — `matriculas_bp`

API de inscripción rápida y retiro. El menú de UI fue retirado; el backend permanece disponible para integraciones o reactivación de UI.

### 6.10 Reportes — `reportes_bp`

- `GET /api/reportes/dashboard`
- `GET /api/reportes/exportar/asistencias?formato=excel|pdf&...`
- `GET /api/reportes/exportar/calificaciones?formato=...&id_periodo&id_materia&id_seccion&id_estudiante`
- `GET /api/reportes/exportar/pagos?formato=...&estado&mes&anio&id_estudiante`

Implementación típica: **openpyxl** (Excel) y **reportlab** (PDF).

### 6.11 Códigos HTTP usados

| Código | Uso |
|--------|-----|
| 200 | OK |
| 201 | Creado |
| 400 | Validación / datos incompletos |
| 401 | No autenticado |
| 403 | Autenticado pero sin permiso de rol o de materia |
| 404 | Recurso no encontrado |
| 500 | Error no controlado (revisar logs) |

---

## 7. Autenticación y autorización

### 7.1 Sesión Flask

Tras login exitoso se guarda:

```text
session['user_id']
session['username']
session['rol']
session['nombre']
session['id_estudiante']   # puede ser None
session['id_docente']      # puede ser None
```

La cookie se firma con `SECRET_KEY`. Sin una clave fuerte, un atacante podría falsificar sesiones.

### 7.2 Generar SECRET_KEY

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

Colocar el valor en `.env`:

```env
SECRET_KEY=...valor generado...
```

### 7.3 `require_auth(roles=None)`

Definido en `backend/routes/auth.py`:

- Si no hay `user_id` en sesión → 401.
- Si `roles` está definido y `session['rol']` no está en la lista → 403.

### 7.4 Matriz de autorización (resumen)

| Recurso | admin | secretaria | docente | estudiante |
|---------|-------|------------|---------|------------|
| CRUD periodos/materias | sí | no (lectura limitada) | lectura materias propias | GET periodos |
| Estudiantes escritura | sí | sí | no | no |
| Asistencias escritura | sí | no | sí | no |
| Calificaciones escritura | sí | no | sí (sus materias) | no |
| Pagos | sí | sí | no | no |
| Usuarios | sí | no | no | no |
| Export reportes | sí | sí | sí (acotado) | sí (propios) |

### 7.5 Contraseñas

- Hash con `werkzeug.security.generate_password_hash`.
- Verificación con `check_password_hash`.
- Nunca se almacenan ni se devuelven en claro en la API.

---

## 8. Frontend (SPA)

### 8.1 Principios

- Sin React/Vue/Angular: un solo `app.js` mantiene el estado.
- `api(path, options)` centraliza `fetch`, JSON, credenciales (`credentials: 'include'`) y manejo de errores.
- `navigate(pageId)` renderiza el módulo en el contenedor principal.

### 8.2 Menús por rol (`MENU`)

Objeto JS con arreglos de ítems `{ id, icon, label }` y separadores de sección.  
Ejemplos de `id`: `dashboard`, `periodos`, `cursos`, `estudiantes`, `docentes`, `asistencias`, `calificaciones`, `pagos`, `usuarios`, `mis_asistencias`, `mis_calificaciones`.

### 8.3 Patrones de UI

- **Filtros + Cargar:** el usuario configura criterios y dispara la consulta (pagos, actas, mis calificaciones).
- **Modales:** formularios de alta/edición (`openModal` / `closeModal`).
- **Toasts:** feedback no bloqueante.
- **Export:** `window.open(`${API}/reportes/exportar/...?formato=pdf`)`.

### 8.4 Reglas de UI importantes

1. **Docente / materias:** el backend ya filtra; el select de materias refleja solo las asignadas.
2. **Secretaria / calificaciones y asistencias:** sin botones Guardar; celdas de notas en texto plano.
3. **Materia = Todas:** consulta vía `GET /api/calificaciones/?id_periodo&id_seccion&id_estudiante`; añade columna Materia; no edición masiva.
4. **Usuarios:** al elegir rol estudiante/docente se muestran selects de vínculo cargados desde `/api/estudiantes/` y `/api/docentes/`.

---

## 9. Configuración e instalación

### 9.1 Requisitos de servidor

| Componente | Versión sugerida |
|------------|------------------|
| Python | 3.10+ |
| PostgreSQL | 14+ |
| pip / venv | incluidos con Python |

### 9.2 Dependencias (`requirements.txt`)

Incluye de forma típica:

- `flask`
- `psycopg2-binary` (o `psycopg2`)
- `python-dotenv`
- `werkzeug`
- `openpyxl`
- `reportlab`

Instalación:

```bash
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate
pip install -r requirements.txt
```

### 9.3 Variables de entorno (`.env`)

```env
SECRET_KEY=cambiar_por_valor_seguro
DB_HOST=localhost
DB_PORT=5432
DB_NAME=control_escolar
DB_USER=postgres
DB_PASSWORD=su_password
FLASK_ENV=development
```

Copiar desde `.env` y ajustar.

### 9.4 Inicialización de BD

```bash
python setup_db.py
```

### 9.5 Ejecución

```bash
python backend/app.py
```

URL por defecto: `http://localhost:5000`

---

## 10. Script `setup_db.py`

### 10.1 Flujo

1. `crear_base_datos()` — conecta a `postgres`, crea `DB_NAME` si no existe.
2. Si `--reset`: `DROP SCHEMA public CASCADE` + `CREATE SCHEMA public`.
3. `migrar_materia()` — si existen columnas antiguas (`docente` sin `id_docente`/`id_grado`), altera tabla y limpia filas incompatibles.
4. Ejecuta `database/schema.sql`.
5. `limpiar_datos_demo()` — borra periodo 2025-2026, secundaria/bachillerato si existieran; activa 2026-2027.
6. Genera 15 estudiantes por sección de primaria.
7. Genera asistencias (muestra de días laborables ene–ago 2026).
8. Genera calificaciones por materia/grado.
9. Genera pagos (matrícula + mensualidades).
10. Upsert de usuarios demo.

### 10.2 Idempotencia

- Estudiantes con cédulas de patrón demo se pueden regenerar.
- `ON CONFLICT` en inserciones clave evita duplicar donde hay constraints.
- `--reset` es la vía limpia ante esquemas rotos.

---

## 11. Exportaciones PDF/Excel

### 11.1 Librerías

| Formato | Librería | Uso |
|--------|----------|-----|
| Excel (.xlsx) | openpyxl | Hojas con encabezados y filas de datos filtrados |
| PDF | reportlab | Tablas simples / listados imprimibles |

### 11.2 Parámetros de filtro (query string)

Comunes: `formato`, `id_estudiante`, `id_seccion`, `id_periodo`, `id_materia`, `fecha_desde`, `fecha_hasta`, `estado`, `mes`, `anio`.

### 11.3 Seguridad

Los endpoints de export requieren autenticación y roles permitidos. El alumno solo exporta información propia (el backend debe acotar por sesión aunque envíe query params).

---

## 12. Decisiones de diseño

| Decisión | Justificación |
|----------|----------------|
| SPA vanilla | Menor curva de aprendizaje en proyectos académicos; un solo archivo JS |
| Sesiones vs JWT | Simplicidad para app monolítica servida por el mismo origen |
| Soft delete | Conserva historial de asistencias, notas y pagos |
| Filtro de materias en backend | Seguridad real; la UI sola no basta |
| Primaria fija A/B | Reduce complejidad de seeds y de reglas de negocio del alcance pedido |
| Comprobantes en disco | Implementación directa; en producción podría migrarse a object storage |
| Reportes en el servidor | openpyxl/reportlab evitan depender de librerías pesadas en el cliente |

---

## 13. Despliegue y operación

### 13.1 Desarrollo local

Ya descrito: venv + PostgreSQL local + `python backend/app.py`.

### 13.2 Producción (recomendaciones)

| Tema | Recomendación |
|------|----------------|
| Servidor WSGI | gunicorn / waitress detrás de nginx |
| HTTPS | Terminar TLS en proxy reverso |
| SECRET_KEY | Única, larga, no versionada |
| DEBUG | `False` |
| Backups | `pg_dump` periódico de `control_escolar` |
| uploads/ | Backup + permisos de escritura solo al usuario del servicio |
| Logs | Redirigir stdout/stderr del proceso a journal o archivo rotado |

Ejemplo gunicorn (orientativo):

```bash
gunicorn -w 2 -b 0.0.0.0:5000 backend.app:app
```

(Ajustar el callable según cómo se exponga la app en `app.py`.)

### 13.3 Copias de seguridad

```bash
pg_dump -U postgres control_escolar > backup_$(date +%Y%m%d).sql
```

Restaurar:

```bash
psql -U postgres control_escolar < backup_YYYYMMDD.sql
```

---

## 14. Mantenimiento y extensión

### 14.1 Añadir un campo a una entidad

1. `ALTER TABLE` en PostgreSQL (y actualizar `schema.sql` para instalaciones nuevas).
2. Ajustar modelo (`INSERT`/`UPDATE`/`SELECT`).
3. Ajustar ruta (JSON) y formulario en `app.js`.

### 14.2 Añadir un rol

1. Incluir valor en checks de `require_auth` y en el formulario de usuarios.
2. Definir entradas en `MENU` del frontend.
3. Documentar permisos en ambos manuales.

### 14.3 Reactivar menú Matrículas

El blueprint `matriculas` sigue presente. Basta con volver a añadir el ítem en `MENU` y asegurar que `navigate` apunte a `renderMatriculas`.

### 14.4 Convención de código

- Rutas delgadas; SQL en modelos.
- Nombres de JSON en español coherentes con el dominio (`id_estudiante`, `nota_final`).
- No confiar en el cliente para autorización.

---

## 15. Troubleshooting técnico

| Síntoma | Causa probable | Acción |
|---------|----------------|--------|
| `SyntaxError` en `setup_db.py` | Script desactualizado | Usar la versión actual del repo |
| Columnas de `materia` incompletas | Schema antiguo | `python setup_db.py --reset` o migración |
| GET `/api/periodos` 403 en alumno | Rol no autorizado en ruta | Verificar que `listar_periodos` incluya `estudiante` |
| Docente sin materias | Sin `id_docente` en sesión o sin asignación | Enlazar usuario + asignar materias |
| JSON error con fechas/Decimal | Serialización | Revisar `database.py` / encoder |
| PDF de pago 404 | Archivo no está en `uploads/` | Verificar nombre en BD y disco |
| Login OK pero menú vacío | `rol` inesperado | Revisar valor en tabla `usuario` |
| CORS / cookies en otro origen | Front y API en dominios distintos | Misma origin o configurar CORS + `SameSite` |

### Logs útiles

- Consola donde corre Flask: trazas 401/403/500.
- PostgreSQL: `postgresql.log` para errores de constraint.

---

## 16. Anexos

### Anexo A — Usuarios seed

| username | password | rol | Vínculo |
|----------|----------|-----|---------|
| admin | admin123 | admin | — |
| secretaria | secre123 | secretaria | — |
| docente1 | docente123 | docente | docente demo |
| alumno1 | alumno123 | estudiante | primer estudiante activo |

### Anexo B — Estados de asistencia

`Asistió` · `Tardanza` · `Falta` · `Justificado`

### Anexo C — Estados de pago

`Pagado` · `Pendiente` · `Vencido` · `Parcial` · `Anulado`

### Anexo D — Conceptos de pago frecuentes

`Matrícula` · `Mensualidad` · `Uniforme` · `Materiales`

### Anexo E — Comando rápido de verificación post-instalación

```bash
python setup_db.py
python backend/app.py
# En otro terminal, con sesión o con script de test:
# Login admin → listar estudiantes → exportar un PDF de actas
```

### Anexo F — Relación documentación

| Documento | Audiencia |
|-----------|-----------|
| `docs/manual_usuario.md` | Usuarios finales y capacitación |
| `docs/manual_tecnico.md` | Desarrolladores y operaciones |
| `README.md` | Arranque rápido del repositorio |

---

*Fin del Manual Técnico — Sistema de Control Escolar*