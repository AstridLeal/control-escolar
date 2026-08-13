# Manual de Usuario - Control Escolar

## 1. Inicio de sesión

1. Abrir el navegador en `http://localhost:5000`
2. Ingresar usuario y contraseña
3. El sistema redirige al panel según el rol

**Usuario admin:** admin / admin123
**Usuario secretaria:** secretaria / secre123
**Usuario docente:** docente1 / docente123
**Usuario alumno:** alumno1 / alumno123

---

## 2. Panel de Administración (Admin)

### Dashboard
Muestra totales de estudiantes, docentes, matrículas y estado de pagos/morosos.

### Periodos Escolares
- Crear periodos con nombre, fechas de inicio/fin
- Activar un periodo (solo uno activo a la vez)
- Editar o eliminar

### Cursos y Secciones
- **Cursos**: materias (Matemáticas, Español, etc.) asociadas a un grado
- **Secciones**: grupos (A, B, C) por grado y periodo, con capacidad

### Estudiantes
- Registro individual con datos personales y del representante
- Carga masiva mediante archivo CSV
- Búsqueda y baja lógica

### Docentes
- Alta de profesores
- Asignación de materias a secciones/periodos

### Matrículas
- Inscripción rápida: ingresar cédula + seleccionar grado/sección
- El estudiante debe existir previamente
- Retiro de matrícula

### Asistencias
1. Seleccionar fecha y sección
2. Cargar lista de estudiantes
3. Marcar Presente / Ausente / Tardanza / Justificado
4. Guardar

### Calificaciones
1. Seleccionar periodo, curso y sección
2. Cargar acta
3. Ingresar parciales y examen final
4. Guardar (se calcula el promedio automáticamente)

### Pagos
- Registrar pago buscando por cédula
- Adjuntar comprobante PDF
- Dashboard de morosos con deuda total

### Usuarios
- Crear usuarios y asignar roles (Admin, Secretaría, Docente, Alumno)
- Desactivar usuarios

### Reportes
- Exportar pagos, matrículas y asistencias a Excel o PDF

---

## 3. Secretaria

Acceso a:
- Dashboard
- Matrículas
- Pagos (registro y morosos)
- Reportes

---

## 4. Docente

Acceso a:
- Registro de asistencias
- Captura de calificaciones / actas

---

## 5. Alumno

Acceso a:
- Consulta de sus propias asistencias
- Consulta de sus calificaciones

---

## Consejos

- Active un periodo escolar antes de matricular o registrar notas
- Cree grados/secciones antes de matricular
- Para carga CSV use codificación UTF-8
- Los comprobantes de pago se almacenan en `frontend/uploads/`