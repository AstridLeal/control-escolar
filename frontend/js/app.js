// SISTEMA DE CONTROL ESCOLAR - Frontend

const API = '/api'; // URL base de la API
let currentUser = null; // Usuario actual
let cache = {}; // Cache de datos para evitar recargas innecesarias

// Utilidades
// Sirve para hacer llamadas a la API y manejar errores de forma centralizada
async function api(url, options = {}) { 
    const opts = { credentials: 'include', headers: { ...(options.headers || {}) }, ...options };
    if (opts.body && typeof opts.body === 'object' && !(opts.body instanceof FormData)) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(opts.body);
    }
    const res = await fetch(API + url, opts);
    if (res.status === 401) { logout(true); throw new Error('Sesión expirada'); }
    const ct = res.headers.get('content-type') || '';
    if (ct.includes('application/json')) {
        const data = await res.json();
        if (!res.ok) throw new Error(data.error || 'Error en la solicitud');
        return data;
    }
    if (!res.ok) throw new Error('Error en la solicitud');
    return res;
}

// Muestra un mensaje tipo pop up en la esquina superior derecha
function toast(msg, type = 'success') {
    const c = document.getElementById('toastContainer');
    const el = document.createElement('div');
    el.className = `toast ${type}`;
    el.textContent = msg;
    c.appendChild(el);
    setTimeout(() => el.remove(), 3500);
}

// Muestra un modal con título, contenido y botones
function openModal(title, body, footer = '') {
    document.getElementById('modalTitle').textContent = title;
    document.getElementById('modalBody').innerHTML = body;
    document.getElementById('modalFooter').innerHTML = footer;
    document.getElementById('modalOverlay').classList.add('show');
}
// Cierra el modal
function closeModal() { document.getElementById('modalOverlay').classList.remove('show'); }

// Formatea un estado en un badge de color
function badge(estado) {
    const map = {
        'Activa': 'success', 'Pagado': 'success', 'Asistió': 'success',
        'Pendiente': 'warning', 'Tardanza': 'warning', 'Parcial': 'warning',
        'Vencido': 'danger', 'Falta': 'danger', 'Anulado': 'secondary',
        'Justificado': 'info'
    };
    return `<span class="badge badge-${map[estado] || 'secondary'}">${estado}</span>`;
}
function fmtDate(d) {
    if (!d) return '-';
    const s = String(d).substring(0, 10);
    const [y, m, day] = s.split('-');
    return `${day}/${m}/${y}`;
}
function fmtMoney(n) { return '$' + parseFloat(n || 0).toFixed(2); }
function loading(el) { el.innerHTML = '<div class="loading-overlay"><div class="spinner"></div> Cargando...</div>'; }

/* AUTH */
// Verifica si el usuario está autenticado y muestra la interfaz correspondiente
async function checkAuth() {
    try { currentUser = await api('/auth/me'); showApp(); }
    catch { showLogin(); }
}

// Muestra la página de login y oculta la aplicación
function showLogin() {
    document.getElementById('loginPage').classList.remove('page-hidden');
    document.getElementById('appLayout').classList.add('page-hidden');
    currentUser = null;
}

// Muestra la aplicación y oculta la página de login
function showApp() {
    document.getElementById('loginPage').classList.add('page-hidden');
    document.getElementById('appLayout').classList.remove('page-hidden');
    document.getElementById('userName').textContent = currentUser.nombre;
    document.getElementById('userRole').textContent = currentUser.rol_label || currentUser.rol;
    document.getElementById('userAvatar').textContent = (currentUser.nombre || 'U')[0].toUpperCase();
    buildSidebar();
    navigate('dashboard');
}

// Maneja el evento de login, enviando las credenciales al backend y mostrando la aplicación si son correctas
async function login(e) {
    e.preventDefault();
    const alertEl = document.getElementById('loginAlert');
    alertEl.innerHTML = '';
    try {
        const res = await api('/auth/login', {
            method: 'POST',
            body: {
                username: document.getElementById('loginUser').value.trim(),
                password: document.getElementById('loginPass').value
            }
        });
        currentUser = res.user;
        showApp();
        toast('Bienvenido, ' + currentUser.nombre);
    } catch (err) {
        alertEl.innerHTML = `<div class="alert alert-danger">${err.message}</div>`;
    }
}

// Cierra la sesión del usuario actual y muestra la página de login
async function logout(silent = false) {
    try { await api('/auth/logout', { method: 'POST' }); } catch {}
    showLogin();
    if (!silent) toast('Sesión cerrada');
}

/* SIDEBAR */
// Define el menú de navegación según el rol del usuario
const MENU = {
    admin: [
        { section: 'Principal' },
        { id: 'dashboard', icon: '📊', label: 'Dashboard' },
        { section: 'Académico' },
        { id: 'periodos', icon: '📅', label: 'Periodos' },
        { id: 'cursos', icon: '📖', label: 'Materias y Secciones' },
        { id: 'estudiantes', icon: '👨‍🎓', label: 'Estudiantes' },
        { id: 'docentes', icon: '👩‍🏫', label: 'Docentes' },
        { section: 'Control' },
        { id: 'asistencias', icon: '✅', label: 'Asistencias' },
        { id: 'calificaciones', icon: '📋', label: 'Calificaciones' },
        { id: 'pagos', icon: '💰', label: 'Pagos' },
        { section: 'Sistema' },
        { id: 'usuarios', icon: '👥', label: 'Usuarios' },
    ],
    secretaria: [
        { section: 'Principal' },
        { id: 'dashboard', icon: '📊', label: 'Dashboard' },
        { section: 'Gestión' },
        { id: 'estudiantes', icon: '👨‍🎓', label: 'Estudiantes' },
        { id: 'pagos', icon: '💰', label: 'Pagos' },
        { section: 'Consulta' },
        { id: 'asistencias', icon: '✅', label: 'Asistencias' },
        { id: 'calificaciones', icon: '📋', label: 'Calificaciones' },
    ],
    docente: [
        { section: 'Principal' },
        { id: 'dashboard', icon: '📊', label: 'Dashboard' },
        { section: 'Control' },
        { id: 'asistencias', icon: '✅', label: 'Asistencias' },
        { id: 'calificaciones', icon: '📋', label: 'Calificaciones' },
    ],
    estudiante: [
        { section: 'Mi Información' },
        { id: 'mis_asistencias', icon: '✅', label: 'Mis Asistencias' },
        { id: 'mis_calificaciones', icon: '📋', label: 'Mis Calificaciones' },
    ]
};

// Construye el menú lateral según el rol del usuario actual
function buildSidebar() {
    const nav = document.getElementById('sidebarNav');
    const items = MENU[currentUser.rol] || MENU.estudiante;
    nav.innerHTML = items.map(item => {
        if (item.section) return `<div class="nav-section">${item.section}</div>`;
        return `<div class="nav-item" data-page="${item.id}" onclick="navigate('${item.id}')">
            <span class="icon">${item.icon}</span> ${item.label}</div>`;
    }).join('');
}

// Navega a una página específica, actualizando el contenido y el título
function navigate(page) {
    document.querySelectorAll('.nav-item').forEach(el =>
        el.classList.toggle('active', el.dataset.page === page));
    const titles = {
        dashboard: 'Dashboard', periodos: 'Periodos Académicos', cursos: 'Materias y Secciones',
        estudiantes: 'Estudiantes', docentes: 'Docentes', matriculas: 'Matrículas',
        asistencias: 'Asistencias', calificaciones: 'Calificaciones', pagos: 'Pagos',
        usuarios: 'Usuarios', reportes: 'Reportes',
        mis_asistencias: 'Mis Asistencias', mis_calificaciones: 'Mis Calificaciones'
    };
    document.getElementById('pageTitle').textContent = titles[page] || page;
    const area = document.getElementById('contentArea');
    loading(area);
    const pages = {
        dashboard: renderDashboard, periodos: renderPeriodos, cursos: renderCursos,
        estudiantes: renderEstudiantes, docentes: renderDocentes, matriculas: renderMatriculas,
        asistencias: renderAsistencias, calificaciones: renderCalificaciones, pagos: renderPagos,
        usuarios: renderUsuarios, reportes: renderReportes,
        mis_asistencias: renderMisAsistencias, mis_calificaciones: renderMisCalificaciones
    };
    (pages[page] || renderDashboard)(area);
    document.getElementById('sidebar').classList.remove('open');
}

/* DASHBOARD */
// Renderiza la página principal del dashboard con estadísticas y morosos
async function renderDashboard(el) {
    try {
        if (['admin', 'secretaria'].includes(currentUser.rol)) {
            const data = await api('/reportes/dashboard');
            const p = data.pagos?.resumen || {};
            el.innerHTML = `
                <div class="stats-grid">
                    <div class="stat-card"><div class="stat-icon blue">👨‍🎓</div>
                        <div><div class="stat-value">${data.total_estudiantes}</div><div class="stat-label">Estudiantes</div></div></div>
                    <div class="stat-card"><div class="stat-icon purple">👩‍🏫</div>
                        <div><div class="stat-value">${data.total_docentes}</div><div class="stat-label">Docentes</div></div></div>
                    <div class="stat-card"><div class="stat-icon green">📝</div>
                        <div><div class="stat-value">${data.total_matriculas}</div><div class="stat-label">Matriculados</div></div></div>
                    <div class="stat-card"><div class="stat-icon orange">💰</div>
                        <div><div class="stat-value">${fmtMoney(p.monto_cobrado)}</div><div class="stat-label">Cobrado</div></div></div>
                    <div class="stat-card"><div class="stat-icon red">⚠️</div>
                        <div><div class="stat-value">${fmtMoney(p.monto_pendiente)}</div><div class="stat-label">Pendiente</div></div></div>
                </div>
                <div class="card"><div class="card-header"><h4>Estudiantes Morosos</h4></div>
                    <div class="card-body table-responsive">${renderMorososTable(data.pagos?.morosos || [])}</div></div>`;
        } else {
            el.innerHTML = `<div class="card"><div class="card-body" style="text-align:center;padding:40px;">
                <h2>Bienvenido, ${currentUser.nombre}</h2>
                <p style="color:var(--text-muted);margin-top:8px;">Rol: ${currentUser.rol_label || currentUser.rol}</p>
            </div></div>`;
        }
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Renderiza la tabla de estudiantes morosos, mostrando sus datos y deuda
function renderMorososTable(morosos) {
    if (!morosos.length) return '<div class="empty-state"><div class="icon">✅</div>No hay morosos</div>';
    return `<table><thead><tr><th>Estudiante</th><th>Cédula</th><th>Cuotas</th><th>Deuda</th><th>Últ. Venc.</th></tr></thead>
        <tbody>${morosos.map(m => `<tr>
            <td>${m.nombre}</td><td>${m.cedula}</td><td>${m.cuotas_pendientes}</td>
            <td><strong>${fmtMoney(m.deuda_total)}</strong></td><td>${fmtDate(m.ultima_vencimiento)}</td>
        </tr>`).join('')}</tbody></table>`;
}

/* PERIODOS */
// Renderiza la lista de periodos académicos, permitiendo crear, editar, activar o eliminar
async function renderPeriodos(el) {
    try {
        const periodos = await api('/periodos');
        el.innerHTML = `<div class="card"><div class="card-header">
            <h4>Periodos Académicos</h4>
            <button class="btn btn-primary btn-sm" onclick="formPeriodo()">+ Nuevo</button></div>
            <div class="card-body table-responsive"><table>
                <thead><tr><th>Nombre</th><th>Inicio</th><th>Fin</th><th>Estado</th><th>Acciones</th></tr></thead>
                <tbody>${periodos.map(p => `<tr>
                    <td><strong>${p.nombre}</strong></td>
                    <td>${fmtDate(p.fecha_inicio)}</td><td>${fmtDate(p.fecha_fin)}</td>
                    <td>${p.activo ? badge('Activa') : '<span class="badge badge-secondary">Inactivo</span>'}</td>
                    <td class="actions">
                        <button class="btn btn-outline btn-sm" onclick='formPeriodo(${JSON.stringify(p)})'>Editar</button>
                        ${!p.activo ? `<button class="btn btn-success btn-sm" onclick="activarPeriodo(${p.id_periodo})">Activar</button>` : ''}
                        <button class="btn btn-danger btn-sm" onclick="eliminarPeriodo(${p.id_periodo})">Eliminar</button>
                    </td></tr>`).join('') || '<tr><td colspan="5">Sin periodos</td></tr>'}
                </tbody></table></div></div>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Muestra un formulario para crear o editar un periodo académico, con campos para nombre, fechas y estado
function formPeriodo(p = null) {
    openModal(p ? 'Editar Periodo' : 'Nuevo Periodo', `
        <div class="form-group"><label>Nombre</label>
            <input class="form-control" id="pNombre" value="${p?.nombre || ''}"></div>
        <div class="form-grid">
            <div class="form-group"><label>Fecha Inicio</label>
                <input type="date" class="form-control" id="pInicio" value="${p?.fecha_inicio?.substring(0,10) || ''}"></div>
            <div class="form-group"><label>Fecha Fin</label>
                <input type="date" class="form-control" id="pFin" value="${p?.fecha_fin?.substring(0,10) || ''}"></div>
        </div>
        <div class="form-group"><label><input type="checkbox" id="pActivo" ${p?.activo ? 'checked' : ''}> Activo</label></div>
    `, `<button class="btn btn-outline" onclick="closeModal()">Cancelar</button>
        <button class="btn btn-primary" onclick="guardarPeriodo(${p?.id_periodo || 'null'})">Guardar</button>`);
}

// Guarda un periodo académico, ya sea creando uno nuevo o actualizando uno existente, enviando los datos al backend
async function guardarPeriodo(id) {
    const data = {
        nombre: document.getElementById('pNombre').value,
        fecha_inicio: document.getElementById('pInicio').value,
        fecha_fin: document.getElementById('pFin').value,
        activo: document.getElementById('pActivo').checked
    };
    try {
        if (id) await api(`/periodos/${id}`, { method: 'PUT', body: data });
        else await api('/periodos', { method: 'POST', body: data });
        closeModal(); toast('Periodo guardado'); navigate('periodos');
    } catch (err) { toast(err.message, 'error'); }
}

// Activa un periodo académico, enviando una solicitud al backend para marcarlo como activo y desactivar los demás
async function activarPeriodo(id) {
    try { await api(`/periodos/${id}`, { method: 'PUT', body: { activo: true } });
        toast('Activado'); navigate('periodos'); } catch (err) { toast(err.message, 'error'); }
}

// Elimina un periodo académico, enviando una solicitud al backend para borrarlo y actualizando la lista de periodos
async function eliminarPeriodo(id) {
    if (!confirm('¿Eliminar?')) return;
    try { await api(`/periodos/${id}`, { method: 'DELETE' }); toast('Eliminado'); navigate('periodos'); }
    catch (err) { toast(err.message, 'error'); }
}

/* MATERIAS Y SECCIONES */
// Renderiza la lista de materias y secciones, permitiendo crear, editar o eliminar cada una
async function renderCursos(el) {
    try {
        const [materias, secciones, grados, periodos] = await Promise.all([
            api('/materias'), api('/secciones'), api('/grados'), api('/periodos')
        ]);
        cache.grados = grados; cache.periodos = periodos;
        cache.materias = materias; cache.secciones = secciones;

        el.innerHTML = `
            <div class="card" style="margin-bottom:20px;">
                <div class="card-header"><h4>Materias</h4>
                    <button class="btn btn-primary btn-sm" onclick="formMateria()">+ Nueva</button></div>
                <div class="card-body table-responsive"><table>
                    <thead><tr><th>Código</th><th>Nombre</th><th>Grado</th><th>Docente</th><th>Hrs</th><th>Acciones</th></tr></thead>
                    <tbody>${materias.map(m => `<tr>
                        <td>${m.codigo || '-'}</td><td>${m.nombre}</td>
                        <td>${m.grado_nombre || '-'}</td><td>${m.docente_nombre || '-'}</td>
                        <td>${m.horas_semana || 0}</td>
                        <td class="actions">
                            <button class="btn btn-outline btn-sm" onclick='formMateria(${JSON.stringify(m)})'>Editar</button>
                            <button class="btn btn-danger btn-sm" onclick="eliminarMateria(${m.id_materia})">Eliminar</button>
                        </td></tr>`).join('') || '<tr><td colspan="6">Sin materias</td></tr>'}
                    </tbody></table></div></div>
            <div class="card">
                <div class="card-header"><h4>Secciones</h4>
                    <button class="btn btn-primary btn-sm" onclick="formSeccion()">+ Nueva</button></div>
                <div class="card-body table-responsive"><table>
                    <thead><tr><th>Sección</th><th>Grado</th><th>Periodo</th><th>Inscritos</th><th>Capacidad</th><th>Acciones</th></tr></thead>
                    <tbody>${secciones.map(s => `<tr>
                        <td><strong>${s.nombre}</strong></td><td>${s.grado_nombre}</td>
                        <td>${s.periodo_nombre}</td><td>${s.inscritos || 0}</td><td>${s.capacidad_max}</td>
                        <td class="actions">
                            <button class="btn btn-outline btn-sm" onclick='formSeccion(${JSON.stringify(s)})'>Editar</button>
                            <button class="btn btn-danger btn-sm" onclick="eliminarSeccion(${s.id_seccion})">Eliminar</button>
                        </td></tr>`).join('') || '<tr><td colspan="6">Sin secciones</td></tr>'}
                    </tbody></table></div></div>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Muestra un formulario para crear o editar una materia, con campos para nombre, código, horas por semana y grado asociado
function formMateria(m = null) {
    const gradosOpts = (cache.grados || []).map(g =>
        `<option value="${g.id_grado}" ${m?.id_grado == g.id_grado ? 'selected' : ''}>${g.nombre}</option>`).join('');
    openModal(m ? 'Editar Materia' : 'Nueva Materia', `
        <div class="form-group"><label>Nombre *</label>
            <input class="form-control" id="mNombre" value="${m?.nombre || ''}"></div>
        <div class="form-grid">
            <div class="form-group"><label>Código</label>
                <input class="form-control" id="mCodigo" value="${m?.codigo || ''}"></div>
            <div class="form-group"><label>Horas/semana</label>
                <input type="number" class="form-control" id="mHoras" value="${m?.horas_semana || 0}"></div>
            <div class="form-group"><label>Grado</label>
                <select class="form-control" id="mGrado"><option value="">-</option>${gradosOpts}</select></div>
        </div>`,
        `<button class="btn btn-outline" onclick="closeModal()">Cancelar</button>
         <button class="btn btn-primary" onclick="guardarMateria(${m?.id_materia || 'null'})">Guardar</button>`);
}

// Guarda una materia, ya sea creando una nueva o actualizando una existente, enviando los datos al backend
async function guardarMateria(id) {
    const data = {
        nombre: document.getElementById('mNombre').value,
        codigo: document.getElementById('mCodigo').value,
        horas_semana: parseInt(document.getElementById('mHoras').value) || 0,
        id_grado: document.getElementById('mGrado').value || null
    };
    try {
        if (id) await api(`/materias/${id}`, { method: 'PUT', body: data });
        else await api('/materias', { method: 'POST', body: data });
        closeModal(); toast('Materia guardada'); navigate('cursos');
    } catch (err) { toast(err.message, 'error'); }
}

// Elimina una materia, enviando una solicitud al backend para borrarla y actualizando la lista de materias
async function eliminarMateria(id) {
    if (!confirm('¿Eliminar?')) return;
    try { await api(`/materias/${id}`, { method: 'DELETE' }); toast('Eliminada'); navigate('cursos'); }
    catch (err) { toast(err.message, 'error'); }
}

// Muestra un formulario para crear o editar una sección, con campos para nombre, capacidad, grado y periodo asociado
function formSeccion(s = null) {
    const gradosOpts = (cache.grados || []).map(g =>
        `<option value="${g.id_grado}" ${s?.id_grado == g.id_grado ? 'selected' : ''}>${g.nombre}</option>`).join('');
    const perOpts = (cache.periodos || []).map(p =>
        `<option value="${p.id_periodo}" ${s?.id_periodo == p.id_periodo ? 'selected' : ''}>${p.nombre}</option>`).join('');
    openModal(s ? 'Editar Sección' : 'Nueva Sección', `
        <div class="form-grid">
            <div class="form-group"><label>Nombre (A, B...)</label>
                <input class="form-control" id="sNombre" value="${s?.nombre || ''}" maxlength="10"></div>
            <div class="form-group"><label>Capacidad</label>
                <input type="number" class="form-control" id="sCap" value="${s?.capacidad_max || 30}"></div>
            <div class="form-group"><label>Grado</label>
                <select class="form-control" id="sGrado">${gradosOpts}</select></div>
            <div class="form-group"><label>Periodo</label>
                <select class="form-control" id="sPeriodo">${perOpts}</select></div>
        </div>`,
        `<button class="btn btn-outline" onclick="closeModal()">Cancelar</button>
         <button class="btn btn-primary" onclick="guardarSeccion(${s?.id_seccion || 'null'})">Guardar</button>`);
}

// Guarda una sección, ya sea creando una nueva o actualizando una existente, enviando los datos al backend
async function guardarSeccion(id) {
    const data = {
        nombre: document.getElementById('sNombre').value,
        capacidad_max: parseInt(document.getElementById('sCap').value) || 30,
        id_grado: parseInt(document.getElementById('sGrado').value),
        id_periodo: parseInt(document.getElementById('sPeriodo').value)
    };
    try {
        if (id) await api(`/secciones/${id}`, { method: 'PUT', body: data });
        else await api('/secciones', { method: 'POST', body: data });
        closeModal(); toast('Sección guardada'); navigate('cursos');
    } catch (err) { toast(err.message, 'error'); }
}

// Elimina una sección, enviando una solicitud al backend para borrarla y actualizando la lista de secciones
async function eliminarSeccion(id) {
    if (!confirm('¿Eliminar?')) return;
    try { await api(`/secciones/${id}`, { method: 'DELETE' }); toast('Eliminada'); navigate('cursos'); }
    catch (err) { toast(err.message, 'error'); }
}

/* ESTUDIANTES */
// Renderiza la lista de estudiantes, permitiendo crear, editar o eliminar cada uno
async function renderEstudiantes(el) {
    try {
        const estudiantes = await api('/estudiantes/');
        el.innerHTML = `<div class="card"><div class="card-header">
            <h4>Estudiantes (${estudiantes.length})</h4>
            <div style="display:flex;gap:8px;">
                <button class="btn btn-secondary btn-sm" onclick="formCargaMasiva()">📁 CSV</button>
                <button class="btn btn-primary btn-sm" onclick="formEstudiante()">+ Nuevo</button>
            </div></div>
            <div class="card-body">
                <div class="filters-bar"><div class="form-group" style="flex:1;">
                    <input class="form-control" placeholder="Buscar..." oninput="filtrarTabla('tablaEst',this.value)">
                </div></div>
                <div class="table-responsive"><table id="tablaEst">
                    <thead><tr><th>Cédula</th><th>Nombres</th><th>Apellidos</th><th>Grado/Sección</th><th>Teléfono</th><th>Acciones</th></tr></thead>
                    <tbody>${estudiantes.map(e => `<tr>
                        <td>${e.cedula}</td><td>${e.nombres}</td><td>${e.apellidos}</td>
                        <td>${e.grado_nombre ? e.grado_nombre + ' - ' + (e.seccion_nombre || '') : '-'}</td>
                        <td>${e.telefono || '-'}</td>
                        <td class="actions">
                            <button class="btn btn-outline btn-sm" onclick='formEstudiante(${JSON.stringify(e).replace(/'/g,"&#39;")})'>Editar</button>
                            <button class="btn btn-danger btn-sm" onclick="eliminarEstudiante(${e.id_estudiante})">Baja</button>
                        </td></tr>`).join('') || '<tr><td colspan="6">Sin estudiantes</td></tr>'}
                    </tbody></table></div></div></div>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Muestra un formulario para crear o editar un estudiante, con campos para cédula, nombres, apellidos, fecha de nacimiento, género, sección, teléfono, email, dirección y representante
async function formEstudiante(e = null) {
    if (!cache.secciones) {
        try { cache.secciones = await api('/secciones'); } catch { cache.secciones = []; }
    }
    const secOpts = (cache.secciones || []).map(s =>
        `<option value="${s.id_seccion}" ${e?.id_seccion==s.id_seccion?'selected':''}>${s.grado_nombre} - ${s.nombre}</option>`
    ).join('');
    openModal(e ? 'Editar Estudiante' : 'Nuevo Estudiante', `
        <div class="form-grid">
            <div class="form-group"><label>Cédula *</label><input class="form-control" id="eCedula" value="${e?.cedula || ''}"></div>
            <div class="form-group"><label>Nombres *</label><input class="form-control" id="eNombres" value="${e?.nombres || ''}"></div>
            <div class="form-group"><label>Apellidos *</label><input class="form-control" id="eApellidos" value="${e?.apellidos || ''}"></div>
            <div class="form-group"><label>Fecha Nac.</label><input type="date" class="form-control" id="eFnac" value="${e?.fecha_nacimiento?.substring?.(0,10) || e?.fecha_nacimiento || ''}"></div>
            <div class="form-group"><label>Género</label>
                <select class="form-control" id="eGenero">
                    <option value="">-</option>
                    <option value="M" ${e?.genero==='M'?'selected':''}>Masculino</option>
                    <option value="F" ${e?.genero==='F'?'selected':''}>Femenino</option>
                </select></div>
            <div class="form-group"><label>Grado / Sección</label>
                <select class="form-control" id="eSeccion">
                    <option value="">Sin asignar</option>
                    ${secOpts}
                </select></div>
            <div class="form-group"><label>Teléfono</label><input class="form-control" id="eTel" value="${e?.telefono || ''}"></div>
            <div class="form-group"><label>Email</label><input class="form-control" id="eEmail" value="${e?.email || ''}"></div>
            <div class="form-group"><label>Dirección</label><input class="form-control" id="eDir" value="${e?.direccion || ''}"></div>
            <div class="form-group"><label>Representante</label><input class="form-control" id="eRep" value="${e?.nombre_representante || ''}"></div>
            <div class="form-group"><label>Tel. Representante</label><input class="form-control" id="eTelRep" value="${e?.telefono_representante || ''}"></div>
        </div>`,
        `<button class="btn btn-outline" onclick="closeModal()">Cancelar</button>
         <button class="btn btn-primary" onclick="guardarEstudiante(${e?.id_estudiante || 'null'})">Guardar</button>`);
}

// Guarda un estudiante, ya sea creando uno nuevo o actualizando uno existente, enviando los datos al backend
async function guardarEstudiante(id) {
    const secVal = document.getElementById('eSeccion').value;
    const data = {
        cedula: document.getElementById('eCedula').value,
        nombres: document.getElementById('eNombres').value,
        apellidos: document.getElementById('eApellidos').value,
        fecha_nacimiento: document.getElementById('eFnac').value || null,
        genero: document.getElementById('eGenero').value || null,
        telefono: document.getElementById('eTel').value,
        email: document.getElementById('eEmail').value,
        direccion: document.getElementById('eDir').value,
        nombre_representante: document.getElementById('eRep').value,
        telefono_representante: document.getElementById('eTelRep').value,
        id_seccion: secVal ? parseInt(secVal) : null
    };
    try {
        if (id) await api(`/estudiantes/${id}`, { method: 'PUT', body: data });
        else await api('/estudiantes/', { method: 'POST', body: data });
        closeModal(); toast('Guardado'); navigate('estudiantes');
    } catch (err) { toast(err.message, 'error'); }
}

// Elimina un estudiante, enviando una solicitud al backend para marcarlo como dado de baja y actualizando la lista de estudiantes
async function eliminarEstudiante(id) {
    if (!confirm('¿Dar de baja?')) return;
    try { await api(`/estudiantes/${id}`, { method: 'DELETE' }); toast('Dado de baja'); navigate('estudiantes'); }
    catch (err) { toast(err.message, 'error'); }
}

// Muestra un formulario para subir un archivo CSV con datos de estudiantes, indicando las columnas obligatorias y opcionales
function formCargaMasiva() {
    openModal('Carga Masiva CSV', `
        <div class="alert alert-info">
            <strong>Columnas obligatorias:</strong> cedula, nombres, apellidos<br>
            <strong>Opcionales:</strong> fecha_nacimiento (AAAA-MM-DD), genero (M/F), telefono, email,
            nombre_representante, telefono_representante, id_seccion<br>
            <small>Descarga el ejemplo: <a href="/docs/ejemplo_estudiantes.csv" download>ejemplo_estudiantes.csv</a></small>
        </div>
        <div class="form-group"><label>Archivo CSV</label><input type="file" class="form-control" id="csvFile" accept=".csv"></div>`,
        `<button class="btn btn-outline" onclick="closeModal()">Cancelar</button>
         <button class="btn btn-primary" onclick="subirCSV()">Subir</button>`);
}

// Envía el archivo CSV al backend para procesar la carga masiva de estudiantes, mostrando mensajes de éxito o error según corresponda
async function subirCSV() {
    const file = document.getElementById('csvFile').files[0];
    if (!file) { toast('Seleccione archivo', 'error'); return; }
    const fd = new FormData(); fd.append('file', file);
    try {
        const res = await fetch(API + '/estudiantes/masivo', { method: 'POST', body: fd, credentials: 'include' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        closeModal(); toast(data.message); navigate('estudiantes');
    } catch (err) { toast(err.message, 'error'); }
}

// Filtra las filas de una tabla según el texto ingresado en un campo de búsqueda, mostrando solo las filas que contienen el texto
function filtrarTabla(id, t) {
    document.querySelectorAll(`#${id} tbody tr`).forEach(r => {
        r.style.display = r.textContent.toLowerCase().includes(t.toLowerCase()) ? '' : 'none';
    });
}

/* DOCENTES */
async function renderDocentes(el) {
    try {
        const docentes = await api('/docentes/');
        const materias = await api('/materias');
        cache.docentes = docentes; cache.materias = materias;
        el.innerHTML = `
            <div class="card" style="margin-bottom:20px;">
                <div class="card-header"><h4>Docentes (${docentes.length})</h4>
                    <button class="btn btn-primary btn-sm" onclick="formDocente()">+ Nuevo</button></div>
                <div class="card-body table-responsive"><table>
                    <thead><tr><th>Cédula</th><th>Nombre</th><th>Especialidad</th><th>Materias</th><th>Acciones</th></tr></thead>
                    <tbody>${docentes.map(d => `<tr>
                        <td>${d.cedula}</td><td>${d.nombres} ${d.apellidos}</td>
                        <td>${d.especialidad || '-'}</td><td>${d.total_materias || 0}</td>
                        <td class="actions">
                            <button class="btn btn-outline btn-sm" onclick='formDocente(${JSON.stringify(d)})'>Editar</button>
                            <button class="btn btn-secondary btn-sm" onclick="formAsignarMateria(${d.id_docente})">Asignar Materia</button>
                            <button class="btn btn-danger btn-sm" onclick="eliminarDocente(${d.id_docente})">Baja</button>
                        </td></tr>`).join('') || '<tr><td colspan="5">Sin docentes</td></tr>'}
                    </tbody></table></div></div>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Muestra un formulario para crear o editar un docente, con campos para cédula, nombres, apellidos, especialidad, teléfono, email y fecha de contratación
function formDocente(d = null) {
    openModal(d ? 'Editar Docente' : 'Nuevo Docente', `
        <div class="form-grid">
            <div class="form-group"><label>Cédula *</label><input class="form-control" id="dCedula" value="${d?.cedula || ''}"></div>
            <div class="form-group"><label>Nombres *</label><input class="form-control" id="dNombres" value="${d?.nombres || ''}"></div>
            <div class="form-group"><label>Apellidos *</label><input class="form-control" id="dApellidos" value="${d?.apellidos || ''}"></div>
            <div class="form-group"><label>Especialidad</label><input class="form-control" id="dEsp" value="${d?.especialidad || ''}"></div>
            <div class="form-group"><label>Teléfono</label><input class="form-control" id="dTel" value="${d?.telefono || ''}"></div>
            <div class="form-group"><label>Email</label><input class="form-control" id="dEmail" value="${d?.email || ''}"></div>
            <div class="form-group"><label>Fecha Contratación</label>
                <input type="date" class="form-control" id="dFecha" value="${d?.fecha_contratacion?.substring(0,10) || ''}"></div>
        </div>`,
        `<button class="btn btn-outline" onclick="closeModal()">Cancelar</button>
         <button class="btn btn-primary" onclick="guardarDocente(${d?.id_docente || 'null'})">Guardar</button>`);
}

// Guarda un docente, ya sea creando uno nuevo o actualizando uno existente, enviando los datos al backend
async function guardarDocente(id) {
    const data = {
        cedula: document.getElementById('dCedula').value,
        nombres: document.getElementById('dNombres').value,
        apellidos: document.getElementById('dApellidos').value,
        especialidad: document.getElementById('dEsp').value,
        telefono: document.getElementById('dTel').value,
        email: document.getElementById('dEmail').value,
        fecha_contratacion: document.getElementById('dFecha').value || null
    };
    try {
        if (id) await api(`/docentes/${id}`, { method: 'PUT', body: data });
        else await api('/docentes/', { method: 'POST', body: data });
        closeModal(); toast('Guardado'); navigate('docentes');
    } catch (err) { toast(err.message, 'error'); }
}

// Elimina un docente, enviando una solicitud al backend para marcarlo como dado de baja y actualizando la lista de docentes
async function eliminarDocente(id) {
    if (!confirm('¿Dar de baja?')) return;
    try { await api(`/docentes/${id}`, { method: 'DELETE' }); toast('Dado de baja'); navigate('docentes'); }
    catch (err) { toast(err.message, 'error'); }
}

// Muestra un formulario para asignar una materia a un docente, con un campo de selección de materias disponibles
function formAsignarMateria(idDocente) {
    const opts = (cache.materias || []).map(m =>
        `<option value="${m.id_materia}">${m.nombre} (${m.codigo || '-'})</option>`).join('');
    openModal('Asignar Materia', `
        <div class="form-group"><label>Materia</label>
            <select class="form-control" id="aMateria">${opts}</select></div>`,
        `<button class="btn btn-outline" onclick="closeModal()">Cancelar</button>
         <button class="btn btn-primary" onclick="guardarAsignacion(${idDocente})">Asignar</button>`);
}

// Guarda la asignación de una materia a un docente, enviando los datos al backend y actualizando la lista de docentes
async function guardarAsignacion(idDocente) {
    try {
        await api('/docentes/asignar-materia', {
            method: 'POST',
            body: { id_docente: idDocente, id_materia: parseInt(document.getElementById('aMateria').value) }
        });
        closeModal(); toast('Materia asignada'); navigate('docentes');
    } catch (err) { toast(err.message, 'error'); }
}

/* MATRÍCULAS */
// Renderiza la lista de matrículas, permitiendo matricular o retirar estudiantes de secciones
async function renderMatriculas(el) {
    try {
        const [matriculas, secciones] = await Promise.all([api('/matriculas/'), api('/secciones')]);
        cache.secciones = secciones;
        el.innerHTML = `<div class="card"><div class="card-header">
            <h4>Matrículas (${matriculas.length})</h4>
            <button class="btn btn-primary btn-sm" onclick="formMatricula()">+ Matricular</button></div>
            <div class="card-body table-responsive"><table>
                <thead><tr><th>Cédula</th><th>Estudiante</th><th>Grado</th><th>Sección</th><th>Periodo</th><th>Fecha</th><th>Acciones</th></tr></thead>
                <tbody>${matriculas.map(m => `<tr>
                    <td>${m.cedula}</td><td>${m.nombres} ${m.apellidos}</td>
                    <td>${m.grado_nombre || '-'}</td><td>${m.seccion_nombre || '-'}</td>
                    <td>${m.periodo_nombre || '-'}</td><td>${fmtDate(m.fecha_inscripcion)}</td>
                    <td><button class="btn btn-danger btn-sm" onclick="retirarMatricula(${m.id_estudiante})">Retirar</button></td>
                </tr>`).join('') || '<tr><td colspan="7">Sin matrículas</td></tr>'}
                </tbody></table></div></div>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Muestra un formulario para matricular un estudiante en una sección, con campos para cédula y selección de sección
function formMatricula() {
    const secOpts = (cache.secciones || []).map(s =>
        `<option value="${s.id_seccion}">${s.grado_nombre} - ${s.nombre} (${s.periodo_nombre})</option>`).join('');
    openModal('Matricular por Cédula', `
        <div class="alert alert-info">El estudiante debe estar registrado previamente.</div>
        <div class="form-group"><label>Cédula *</label><input class="form-control" id="mCedula"></div>
        <div class="form-group"><label>Sección *</label><select class="form-control" id="mSeccion">${secOpts}</select></div>`,
        `<button class="btn btn-outline" onclick="closeModal()">Cancelar</button>
         <button class="btn btn-primary" onclick="guardarMatricula()">Matricular</button>`);
}

// Guarda una matrícula, enviando los datos al backend para registrar al estudiante en la sección seleccionada y actualizando la lista de matrículas
async function guardarMatricula() {
    try {
        await api('/matriculas/', {
            method: 'POST',
            body: {
                cedula: document.getElementById('mCedula').value.trim(),
                id_seccion: parseInt(document.getElementById('mSeccion').value)
            }
        });
        closeModal(); toast('Matriculado'); navigate('matriculas');
    } catch (err) { toast(err.message, 'error'); }
}

// Retira una matrícula, enviando una solicitud al backend para eliminar al estudiante de la sección y actualizando la lista de matrículas
async function retirarMatricula(id) {
    if (!confirm('¿Retirar matrícula?')) return;
    try { await api(`/matriculas/retirar/${id}`, { method: 'POST' }); toast('Retirada'); navigate('matriculas'); }
    catch (err) { toast(err.message, 'error'); }
}

/* ASISTENCIAS */
// Renderiza la sección de asistencias, mostrando un registro para el día actual y un historial filtrable por fecha, sección y estudiante
async function renderAsistencias(el) {
    try {
        const [secciones, estudiantes] = await Promise.all([
            api('/secciones'),
            api('/estudiantes/').catch(() => [])
        ]);
        cache.secciones = secciones;
        cache.estudiantes = estudiantes;
        const hoy = new Date().toISOString().substring(0, 10);
        const puedeEditar = currentUser.rol === 'admin' || currentUser.rol === 'docente';
        const registroBlock = puedeEditar ? `
            <div class="card"><div class="card-header"><h4>Registro de Asistencias</h4></div>
            <div class="card-body">
                <div class="filters-bar">
                    <div class="form-group"><label>Fecha</label>
                        <input type="date" class="form-control" id="asFecha" value="${hoy}"></div>
                    <div class="form-group"><label>Sección</label>
                        <select class="form-control" id="asSeccion">
                            <option value="">Seleccione...</option>
                            ${secciones.map(s => `<option value="${s.id_seccion}">${s.grado_nombre} - ${s.nombre}</option>`).join('')}
                        </select></div>
                    <button class="btn btn-primary" onclick="cargarListaAsistencia()">Cargar Lista</button>
                    <button class="btn btn-success" onclick="guardarAsistencias()" id="btnGuardarAsist" style="display:none;">Guardar</button>
                </div>
                <div id="listaAsistencia"></div>
            </div></div>` : '';
        el.innerHTML = `
            ${registroBlock}
            <div class="card" style="${puedeEditar ? 'margin-top:20px;' : ''}"><div class="card-header">
                <h4>Historial de Asistencias</h4>
                <div style="display:flex;gap:8px;">
                    <button class="btn btn-primary btn-sm" onclick="exportarAsistencias('excel')">Excel</button>
                    <button class="btn btn-danger btn-sm" onclick="exportarAsistencias('pdf')">PDF</button>
                </div>
            </div>
            <div class="card-body">
                <div class="filters-bar">
                    <div class="form-group"><label>Desde</label><input type="date" class="form-control" id="asDesde"></div>
                    <div class="form-group"><label>Hasta</label><input type="date" class="form-control" id="asHasta"></div>
                    <div class="form-group"><label>Sección</label>
                        <select class="form-control" id="asHistSeccion">
                            <option value="">Todas</option>
                            ${secciones.map(s => `<option value="${s.id_seccion}">${s.grado_nombre} - ${s.nombre}</option>`).join('')}
                        </select></div>
                    <div class="form-group"><label>Alumno</label>
                        <select class="form-control" id="asHistAlumno">
                            <option value="">Todos</option>
                            ${estudiantes.map(e => `<option value="${e.id_estudiante}">${e.apellidos} ${e.nombres}</option>`).join('')}
                        </select></div>
                    <button class="btn btn-secondary" onclick="buscarAsistencias()">Buscar</button>
                </div>
                <div class="table-responsive" id="historialAsist"></div>
            </div></div>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Carga la lista de estudiantes de una sección para registrar su asistencia en una fecha específica, mostrando un formulario con opciones de estado y observaciones
async function cargarListaAsistencia() {
    const idSeccion = document.getElementById('asSeccion').value;
    const fecha = document.getElementById('asFecha').value;
    if (!idSeccion || !fecha) { toast('Seleccione sección y fecha', 'error'); return; }
    const el = document.getElementById('listaAsistencia');
    loading(el);
    try {
        const estudiantes = await api(`/asistencias/seccion/${idSeccion}/estudiantes`);
        const existentes = await api(`/asistencias/?fecha=${fecha}&id_seccion=${idSeccion}`);
        const mapE = {}; existentes.forEach(a => { mapE[a.id_estudiante] = a; });
        if (!estudiantes.length) { el.innerHTML = '<div class="empty-state">Sin estudiantes</div>'; return; }
        el.innerHTML = `<table><thead><tr><th>Cédula</th><th>Estudiante</th><th>Estado</th><th>Obs.</th></tr></thead>
            <tbody>${estudiantes.map(e => {
                const ex = mapE[e.id_estudiante] || {};
                return `<tr data-est="${e.id_estudiante}">
                    <td>${e.cedula}</td><td>${e.nombres} ${e.apellidos}</td>
                    <td><select class="form-control as-estado" style="min-width:130px;">
                        <option value="Asistió" ${ex.estado==='Asistió'?'selected':''}>Asistió</option>
                        <option value="Falta" ${ex.estado==='Falta'?'selected':''}>Falta</option>
                        <option value="Tardanza" ${ex.estado==='Tardanza'?'selected':''}>Tardanza</option>
                        <option value="Justificado" ${ex.estado==='Justificado'?'selected':''}>Justificado</option>
                    </select></td>
                    <td><input class="form-control as-obs" value="${ex.observacion || ''}"></td>
                </tr>`;
            }).join('')}</tbody></table>`;
        document.getElementById('btnGuardarAsist').style.display = '';
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Guarda las asistencias registradas en la lista, enviando los datos al backend para almacenarlos y mostrando un mensaje de éxito o error según corresponda
async function guardarAsistencias() {
    const idSeccion = parseInt(document.getElementById('asSeccion').value);
    const fecha = document.getElementById('asFecha').value;
    const registros = [];
    document.querySelectorAll('#listaAsistencia tbody tr').forEach(r => {
        registros.push({
            id_estudiante: parseInt(r.dataset.est),
            id_seccion: idSeccion,
            fecha,
            estado: r.querySelector('.as-estado').value,
            observacion: r.querySelector('.as-obs').value
        });
    });
    try {
        await api('/asistencias/masivo', { method: 'POST', body: { registros } });
        toast(`${registros.length} asistencias guardadas`);
    } catch (err) { toast(err.message, 'error'); }
}

// Busca asistencias en el historial según los filtros de fecha, sección y estudiante, mostrando los resultados en una tabla o un mensaje de "sin registros" si no hay coincidencias
async function buscarAsistencias() {
    let url = '/asistencias/?';
    const desde = document.getElementById('asDesde')?.value;
    const hasta = document.getElementById('asHasta')?.value;
    const sec = document.getElementById('asHistSeccion')?.value;
    const alum = document.getElementById('asHistAlumno')?.value;
    if (desde) url += `fecha_desde=${desde}&`;
    if (hasta) url += `fecha_hasta=${hasta}&`;
    if (sec) url += `id_seccion=${sec}&`;
    if (alum) url += `id_estudiante=${alum}&`;
    const el = document.getElementById('historialAsist');
    loading(el);
    try {
        const data = await api(url);
        if (!data.length) { el.innerHTML = '<div class="empty-state">Sin registros</div>'; return; }
        el.innerHTML = `<table><thead><tr><th>Fecha</th><th>Estudiante</th><th>Cédula</th><th>Grado/Sección</th><th>Estado</th><th>Obs.</th></tr></thead>
            <tbody>${data.map(a => `<tr>
                <td>${fmtDate(a.fecha)}</td><td>${a.estudiante_nombre}</td><td>${a.cedula}</td>
                <td>${a.grado_nombre || ''} - ${a.seccion_nombre || ''}</td>
                <td>${badge(a.estado)}</td><td>${a.observacion || '-'}</td>
            </tr>`).join('')}</tbody></table>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Exporta las asistencias filtradas en el historial a un archivo Excel o PDF, abriendo una nueva ventana con la URL de exportación y los parámetros de filtro correspondientes
function exportarAsistencias(formato) {
    let url = `${API}/reportes/exportar/asistencias?formato=${formato}`;
    const desde = document.getElementById('asDesde')?.value;
    const hasta = document.getElementById('asHasta')?.value;
    const sec = document.getElementById('asHistSeccion')?.value;
    const alum = document.getElementById('asHistAlumno')?.value;
    if (desde) url += `&fecha_desde=${desde}`;
    if (hasta) url += `&fecha_hasta=${hasta}`;
    if (sec) url += `&id_seccion=${sec}`;
    if (alum) url += `&id_estudiante=${alum}`;
    window.open(url, '_blank');
}

/* CALIFICACIONES */
// Renderiza la sección de calificaciones, mostrando filtros para periodo, materia, sección y estudiante, y botones para exportar el acta a Excel o PDF
async function renderCalificaciones(el) {
    try {
        const [materias, secciones, periodos, estudiantes] = await Promise.all([
            api('/materias'), api('/secciones'), api('/periodos'),
            api('/estudiantes/').catch(() => [])
        ]);
        cache.materias = materias; cache.secciones = secciones; cache.periodos = periodos;
        cache.estudiantes = estudiantes;
        const puedeEditar = currentUser.rol === 'admin' || currentUser.rol === 'docente';
        el.innerHTML = `<div class="card"><div class="card-header">
                <h4>Actas de Calificaciones</h4>
                <div style="display:flex;gap:8px;">
                    <button class="btn btn-primary btn-sm" onclick="exportarActa('excel')">Excel</button>
                    <button class="btn btn-danger btn-sm" onclick="exportarActa('pdf')">PDF</button>
                </div>
            </div>
            <div class="card-body">
                <div class="filters-bar">
                    <div class="form-group"><label>Periodo</label>
                        <select class="form-control" id="calPeriodo">
                            ${periodos.map(p => `<option value="${p.id_periodo}" ${p.activo?'selected':''}>${p.nombre}</option>`).join('')}
                        </select></div>
                    <div class="form-group"><label>Materia</label>
                        <select class="form-control" id="calMateria">
                            <option value="">Todas</option>
                            ${materias.map(m => `<option value="${m.id_materia}">${m.nombre}${m.grado_nombre?' ('+m.grado_nombre+')':''}</option>`).join('')}
                        </select></div>
                    <div class="form-group"><label>Sección</label>
                        <select class="form-control" id="calSeccion">
                            ${secciones.map(s => `<option value="${s.id_seccion}">${s.grado_nombre} - ${s.nombre}</option>`).join('')}
                        </select></div>
                    <div class="form-group"><label>Alumno</label>
                        <select class="form-control" id="calAlumno">
                            <option value="">Todos</option>
                            ${estudiantes.map(e => `<option value="${e.id_estudiante}">${e.apellidos} ${e.nombres}</option>`).join('')}
                        </select></div>
                    <button class="btn btn-primary" onclick="cargarActa()">Cargar Acta</button>
                    ${puedeEditar ? '<button class="btn btn-success" onclick="guardarActa()" id="btnGuardarActa" style="display:none;">Guardar Notas</button>' : ''}
                </div>
                <div id="actaContainer"></div>
            </div></div>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Carga el acta de calificaciones según los filtros seleccionados, mostrando una tabla con las notas de los estudiantes y permitiendo la edición si el usuario tiene permisos
async function cargarActa() {
    const idMateria = document.getElementById('calMateria').value;
    const idSeccion = document.getElementById('calSeccion').value;
    const idPeriodo = document.getElementById('calPeriodo').value;
    const idAlumno = document.getElementById('calAlumno')?.value || '';
    const el = document.getElementById('actaContainer');
    if (!idPeriodo || !idSeccion) {
        toast('Seleccione periodo y sección', 'error');
        return;
    }
    loading(el);
    try {
        const puedeEditar = currentUser.rol === 'admin' || currentUser.rol === 'docente';
        let data = [];
        let modoTodas = !idMateria; // Materia = Todas

        if (modoTodas) {
            // Todas las materias: listado con columna Materia
            let url = `/calificaciones/?id_periodo=${idPeriodo}&id_seccion=${idSeccion}`;
            if (idAlumno) url += `&id_estudiante=${idAlumno}`;
            data = await api(url);
            // Duplicar por estudiante+materia
            const seen = new Map();
            for (const c of data) {
                const key = `${c.id_estudiante}-${c.id_materia}`;
                if (!seen.has(key)) seen.set(key, c);
            }
            data = Array.from(seen.values());
            if (!data.length) { el.innerHTML = '<div class="empty-state">Sin calificaciones</div>'; return; }
            // Solo lectura cuando son todas las materias (editar por materia individual)
            el.innerHTML = `<div class="table-responsive"><table>
                <thead><tr><th>Cédula</th><th>Estudiante</th><th>Materia</th><th>N1</th><th>N2</th><th>N3</th><th>Final</th><th>Promedio</th></tr></thead>
                <tbody>${data.map(e => `<tr>
                    <td>${e.cedula || '-'}</td>
                    <td>${e.estudiante_nombre || ((e.nombres||'') + ' ' + (e.apellidos||''))}</td>
                    <td>${e.materia_nombre || '-'}</td>
                    <td>${e.nota1 ?? '-'}</td><td>${e.nota2 ?? '-'}</td><td>${e.nota3 ?? '-'}</td>
                    <td>${e.examen_final ?? '-'}</td>
                    <td><strong>${e.nota_final != null ? parseFloat(e.nota_final).toFixed(2) : '-'}</strong></td>
                </tr>`).join('')}</tbody></table></div>`;
            const btnG = document.getElementById('btnGuardarActa');
            if (btnG) btnG.style.display = 'none';
            return;
        }

        // Una materia: acta editable (admin/docente)
        data = await api(`/calificaciones/acta?id_materia=${idMateria}&id_seccion=${idSeccion}&id_periodo=${idPeriodo}`);
        if (idAlumno) data = data.filter(e => String(e.id_estudiante) === String(idAlumno));
        if (!data.length) { el.innerHTML = '<div class="empty-state">Sin estudiantes</div>'; return; }
        const cell = (cls, val) => puedeEditar
            ? `<td><input type="number" step="0.01" min="0" max="100" class="form-control ${cls}" value="${val ?? ''}" style="width:75px;"></td>`
            : `<td>${val != null && val !== '' ? val : '-'}</td>`;
        el.innerHTML = `<div class="table-responsive"><table>
            <thead><tr><th>Cédula</th><th>Estudiante</th><th>Materia</th><th>N1</th><th>N2</th><th>N3</th><th>Final</th><th>Promedio</th></tr></thead>
            <tbody>${data.map(e => {
                const matNombre = (cache.materias || []).find(m => String(m.id_materia) === String(idMateria))?.nombre || '-';
                return `<tr data-est="${e.id_estudiante}" data-mat="${idMateria}">
                <td>${e.cedula}</td><td>${e.nombres} ${e.apellidos}</td>
                <td>${matNombre}</td>
                ${cell('n1', e.nota1)}${cell('n2', e.nota2)}${cell('n3', e.nota3)}${cell('nef', e.examen_final)}
                <td><strong>${e.nota_final != null ? parseFloat(e.nota_final).toFixed(2) : '-'}</strong></td>
            </tr>`;
            }).join('')}</tbody></table></div>`;
        const btnG = document.getElementById('btnGuardarActa');
        if (btnG && puedeEditar) btnG.style.display = '';
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Guarda las calificaciones ingresadas en el acta, enviando los datos al backend para cada estudiante y mostrando un mensaje de éxito o error según corresponda
async function guardarActa() {
    const idMateria = document.getElementById('calMateria').value;
    const idPeriodo = parseInt(document.getElementById('calPeriodo').value);
    if (!idMateria) {
        toast('Seleccione una materia específica para guardar notas', 'error');
        return;
    }
    let count = 0;
    try {
        for (const r of document.querySelectorAll('#actaContainer tbody tr')) {
            const n1El = r.querySelector('.n1'), n2El = r.querySelector('.n2');
            const n3El = r.querySelector('.n3'), efEl = r.querySelector('.nef');
            if (!n1El) continue;
            const n1 = n1El.value, n2 = n2El.value, n3 = n3El.value, ef = efEl.value;
            if (!n1 && !n2 && !n3 && !ef) continue;
            await api('/calificaciones/', {
                method: 'POST',
                body: {
                    id_estudiante: parseInt(r.dataset.est),
                    id_materia: parseInt(idMateria), id_periodo: idPeriodo,
                    nota1: n1 ? parseFloat(n1) : null, nota2: n2 ? parseFloat(n2) : null,
                    nota3: n3 ? parseFloat(n3) : null, examen_final: ef ? parseFloat(ef) : null
                }
            });
            count++;
        }
        toast(`${count} calificaciones guardadas`);
        cargarActa();
    } catch (err) { toast(err.message, 'error'); }
}

// Exporta el acta de calificaciones según los filtros seleccionados a un archivo Excel o PDF, abriendo una nueva ventana con la URL de exportación y los parámetros correspondientes
function exportarActa(formato) {
    const idMateria = document.getElementById('calMateria')?.value;
    const idSeccion = document.getElementById('calSeccion')?.value;
    const idPeriodo = document.getElementById('calPeriodo')?.value;
    const idAlumno = document.getElementById('calAlumno')?.value;
    if (!idPeriodo || !idSeccion) {
        toast('Seleccione periodo y sección', 'error');
        return;
    }
    let url = `${API}/reportes/exportar/calificaciones?formato=${formato}&id_periodo=${idPeriodo}&id_seccion=${idSeccion}`;
    if (idMateria) url += `&id_materia=${idMateria}`;
    if (idAlumno) url += `&id_estudiante=${idAlumno}`;
    window.open(url, '_blank');
}

/* PAGOS */
// Renderiza la sección de pagos, mostrando un resumen de pagos, filtros para buscar pagos por alumno, estado, mes, año, concepto y sección, y botones para exportar a Excel o PDF
async function renderPagos(el) {
    try {
        const [pagos, periodos, dash, secciones, estudiantes] = await Promise.all([
            api('/pagos/'), api('/periodos'), api('/pagos/dashboard'),
            api('/secciones').catch(() => []),
            api('/estudiantes/').catch(() => [])
        ]);
        cache.periodos = periodos;
        cache.pagosAll = pagos;
        cache.secciones = secciones;
        // Mapa estudiante -> sección para filtrar
        cache.estSeccion = {};
        (estudiantes || []).forEach(e => { cache.estSeccion[e.id_estudiante] = e.id_seccion; });
        const r = dash.resumen || {};
        el.innerHTML = `
            <div class="stats-grid">
                <div class="stat-card"><div class="stat-icon green">✅</div>
                    <div><div class="stat-value">${r.total_pagados||0}</div><div class="stat-label">Pagados</div></div></div>
                <div class="stat-card"><div class="stat-icon orange">⏳</div>
                    <div><div class="stat-value">${r.total_pendientes||0}</div><div class="stat-label">Pendientes</div></div></div>
                <div class="stat-card"><div class="stat-icon red">⚠️</div>
                    <div><div class="stat-value">${r.total_vencidos||0}</div><div class="stat-label">Vencidos</div></div></div>
                <div class="stat-card"><div class="stat-icon blue">💰</div>
                    <div><div class="stat-value">${fmtMoney(r.monto_cobrado)}</div><div class="stat-label">Cobrado</div></div></div>
            </div>
            <div class="card"><div class="card-header">
                <h4>Pagos</h4>
                <div style="display:flex;gap:8px;">
                    <button class="btn btn-primary btn-sm" onclick="exportarPagos('excel')">Excel</button>
                    <button class="btn btn-danger btn-sm" onclick="exportarPagos('pdf')">PDF</button>
                    <button class="btn btn-primary btn-sm" onclick="formPago()">+ Registrar</button>
                </div></div>
            <div class="card-body">
                <div class="filters-bar">
                    <div class="form-group"><label>Alumno</label>
                        <select class="form-control" id="pgFiltroAlumno">
                            <option value="">Todos</option>
                            ${(estudiantes || []).map(e => `<option value="${e.id_estudiante}">${e.apellidos} ${e.nombres}</option>`).join('')}
                        </select></div>
                    <div class="form-group"><label>Estado</label>
                        <select class="form-control" id="pgFiltroEstado">
                            <option value="">Todos</option>
                            <option>Pagado</option><option>Pendiente</option>
                            <option>Vencido</option><option>Parcial</option><option>Anulado</option>
                        </select></div>
                    <div class="form-group"><label>Mes</label>
                        <select class="form-control" id="pgFiltroMes">
                            <option value="">Todos</option>
                            ${['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
                                .map(m => `<option value="${m}">${m}</option>`).join('')}
                        </select></div>
                    <div class="form-group"><label>Año</label>
                        <input type="number" class="form-control" id="pgFiltroAnio" placeholder="2026" style="width:100px;"></div>
                    <div class="form-group"><label>Concepto</label>
                        <select class="form-control" id="pgFiltroConcepto">
                            <option value="">Todos</option>
                            <option>Matrícula</option><option>Mensualidad</option>
                            <option>Uniforme</option><option>Materiales</option>
                        </select></div>
                    <div class="form-group"><label>Sección</label>
                        <select class="form-control" id="pgFiltroSeccion">
                            <option value="">Todas</option>
                            ${(secciones || []).map(s => `<option value="${s.id_seccion}">${s.grado_nombre} - ${s.nombre}</option>`).join('')}
                        </select></div>
                    <button class="btn btn-primary" onclick="cargarPagosFiltrados()">Cargar</button>
                </div>
                <div class="table-responsive"><table id="tablaPagos">
                <thead><tr><th>Estudiante</th><th>Concepto</th><th>Monto</th><th>Mes/Año</th><th>Estado</th><th>Fecha</th><th>PDF</th></tr></thead>
                <tbody id="pagosBody"><tr><td colspan="7">Seleccione filtros y pulse Cargar</td></tr></tbody>
                </table></div></div></div>
            <div class="card" style="margin-top:20px;"><div class="card-header"><h4>Morosos</h4></div>
                <div class="card-body table-responsive">${renderMorososTable(dash.morosos || [])}</div></div>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Renderiza las filas de la tabla de pagos según los datos proporcionados, mostrando información del estudiante, concepto, monto, mes/año, estado, fecha y un enlace al comprobante en PDF si está disponible
function renderPagosRows(pagos) {
    if (!pagos.length) return '<tr><td colspan="7">Sin pagos</td></tr>';
    return pagos.map(p => `<tr>
        <td>${p.estudiante_nombre}<br><small>${p.cedula}</small></td>
        <td>${p.concepto || '-'}</td><td><strong>${fmtMoney(p.monto)}</strong></td>
        <td>${p.mes||''}/${p.anio||'-'}</td><td>${badge(p.estado)}</td>
        <td>${fmtDate(p.fecha_pago)}</td>
        <td>${p.comprobante ? `<a href="/api/pagos/comprobante/${p.comprobante}" target="_blank" class="btn btn-outline btn-sm">PDF</a>` : '-'}</td>
    </tr>`).join('');
}

// Obtiene los pagos filtrados según los criterios seleccionados en los filtros de la interfaz, aplicando las condiciones correspondientes a cada campo y devolviendo la lista resultante
function obtenerPagosFiltrados() {
    const alumno = document.getElementById('pgFiltroAlumno')?.value || '';
    const estado = document.getElementById('pgFiltroEstado')?.value || '';
    const mes = document.getElementById('pgFiltroMes')?.value || '';
    const anio = document.getElementById('pgFiltroAnio')?.value || '';
    const concepto = document.getElementById('pgFiltroConcepto')?.value || '';
    const seccion = document.getElementById('pgFiltroSeccion')?.value || '';
    let list = cache.pagosAll || [];
    if (alumno) list = list.filter(p => String(p.id_estudiante) === String(alumno));
    if (estado) list = list.filter(p => p.estado === estado);
    if (mes) list = list.filter(p => p.mes === mes);
    if (anio) list = list.filter(p => String(p.anio) === String(anio));
    if (concepto) list = list.filter(p => p.concepto === concepto);
    if (seccion) {
        const map = cache.estSeccion || {};
        list = list.filter(p => String(map[p.id_estudiante] || '') === String(seccion));
    }
    return list;
}

// Carga los pagos filtrados según los criterios seleccionados en los filtros de la interfaz, actualizando la tabla de pagos y mostrando un mensaje con la cantidad de registros cargados
function cargarPagosFiltrados() {
    const list = obtenerPagosFiltrados();
    cache.pagosFiltrados = list;
    const body = document.getElementById('pagosBody');
    if (body) body.innerHTML = renderPagosRows(list);
    toast(`${list.length} registro(s) cargados`);
}

// Exporta los pagos filtrados según los criterios seleccionados en los filtros de la interfaz a un archivo Excel o PDF, abriendo una nueva ventana con la URL de exportación y los parámetros correspondientes
function exportarPagos(formato) {
    // Usa los mismos filtros aplicados en Cargar
    const alumno = document.getElementById('pgFiltroAlumno')?.value;
    const estado = document.getElementById('pgFiltroEstado')?.value;
    const mes = document.getElementById('pgFiltroMes')?.value;
    const anio = document.getElementById('pgFiltroAnio')?.value;
    let url = `${API}/reportes/exportar/pagos?formato=${formato}`;
    if (alumno) url += `&id_estudiante=${alumno}`;
    if (estado) url += `&estado=${encodeURIComponent(estado)}`;
    if (mes) url += `&mes=${encodeURIComponent(mes)}`;
    if (anio) url += `&anio=${anio}`;
    window.open(url, '_blank');
}

// Muestra un formulario modal para registrar un nuevo pago, con campos para cédula del estudiante, concepto, periodo, monto, mes, año, fecha de pago, método de pago, referencia, comprobante PDF y observación
function formPago() {
    const perOpts = (cache.periodos || []).map(p =>
        `<option value="${p.id_periodo}" ${p.activo?'selected':''}>${p.nombre}</option>`).join('');
    openModal('Registrar Pago', `
        <div class="form-group"><label>Cédula *</label>
            <input class="form-control" id="pgCedula" onblur="buscarEstPago()"></div>
        <div id="pgEstInfo"></div>
        <input type="hidden" id="pgEstId">
        <div class="form-grid">
            <div class="form-group"><label>Concepto</label>
                <select class="form-control" id="pgConcepto">
                    <option value="Matrícula">Matrícula</option>
                    <option value="Mensualidad" selected>Mensualidad</option>
                    <option value="Uniforme">Uniforme</option>
                    <option value="Materiales">Materiales</option>
                </select></div>
            <div class="form-group"><label>Periodo</label>
                <select class="form-control" id="pgPeriodo">${perOpts}</select></div>
            <div class="form-group"><label>Monto *</label>
                <input type="number" step="0.01" class="form-control" id="pgMonto" value="80"></div>
            <div class="form-group"><label>Mes</label>
                <select class="form-control" id="pgMes">
                    <option value="">-</option>
                    ${['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
                        .map((m,i) => `<option value="${m}">${m}</option>`).join('')}
                </select></div>
            <div class="form-group"><label>Año</label>
                <input type="number" class="form-control" id="pgAnio" value="${new Date().getFullYear()}"></div>
            <div class="form-group"><label>Fecha Pago</label>
                <input type="date" class="form-control" id="pgFecha" value="${new Date().toISOString().substring(0,10)}"></div>
            <div class="form-group"><label>Método</label>
                <select class="form-control" id="pgMetodo">
                    <option>Efectivo</option><option>Transferencia</option>
                    <option>Tarjeta</option><option>Depósito</option>
                </select></div>
            <div class="form-group"><label>Referencia</label>
                <input class="form-control" id="pgRef"></div>
        </div>
        <div class="form-group"><label>Comprobante PDF</label>
            <input type="file" class="form-control" id="pgComp" accept=".pdf"></div>
        <div class="form-group"><label>Observación</label>
            <textarea class="form-control" id="pgObs"></textarea></div>`,
        `<button class="btn btn-outline" onclick="closeModal()">Cancelar</button>
         <button class="btn btn-primary" onclick="guardarPago()">Registrar</button>`);
}

// Busca un estudiante por cédula al registrar un pago, mostrando su información si se encuentra o un mensaje de error si no se encuentra, y llenando un campo oculto con el ID del estudiante para usarlo al guardar el pago
async function buscarEstPago() {
    const cedula = document.getElementById('pgCedula').value.trim();
    if (!cedula) return;
    try {
        const est = await api(`/estudiantes/cedula/${cedula}`);
        document.getElementById('pgEstId').value = est.id_estudiante;
        document.getElementById('pgEstInfo').innerHTML =
            `<div class="alert alert-success">✓ ${est.nombres} ${est.apellidos}</div>`;
    } catch {
        document.getElementById('pgEstId').value = '';
        document.getElementById('pgEstInfo').innerHTML =
            `<div class="alert alert-danger">No encontrado</div>`;
    }
}

// Guarda un nuevo pago registrado en el formulario, enviando los datos al backend y mostrando un mensaje de éxito o error según corresponda, y cerrando el modal y recargando la lista de pagos si se guarda correctamente
async function guardarPago() {
    const estId = document.getElementById('pgEstId').value;
    if (!estId) { toast('Busque un estudiante válido', 'error'); return; }
    const fd = new FormData();
    fd.append('id_estudiante', estId);
    fd.append('id_periodo', document.getElementById('pgPeriodo').value);
    fd.append('concepto', document.getElementById('pgConcepto').value);
    fd.append('monto', document.getElementById('pgMonto').value);
    fd.append('mes', document.getElementById('pgMes').value);
    fd.append('anio', document.getElementById('pgAnio').value);
    fd.append('fecha_pago', document.getElementById('pgFecha').value);
    fd.append('metodo_pago', document.getElementById('pgMetodo').value);
    fd.append('referencia', document.getElementById('pgRef').value);
    fd.append('observacion', document.getElementById('pgObs').value);
    fd.append('estado', 'Pagado');
    const file = document.getElementById('pgComp').files[0];
    if (file) fd.append('comprobante', file);
    try {
        const res = await fetch(API + '/pagos/', { method: 'POST', body: fd, credentials: 'include' });
        const data = await res.json();
        if (!res.ok) throw new Error(data.error);
        closeModal(); toast('Pago registrado'); navigate('pagos');
    } catch (err) { toast(err.message, 'error'); }
}

/* USUARIOS */
// Renderiza la sección de usuarios, mostrando una tabla con la lista de usuarios, sus datos y acciones para editar o desactivar, y un botón para crear un nuevo usuario
async function renderUsuarios(el) {
    try {
        const usuarios = await api('/usuarios/');
        el.innerHTML = `<div class="card"><div class="card-header">
            <h4>Usuarios</h4>
            <button class="btn btn-primary btn-sm" onclick="formUsuario()">+ Nuevo</button></div>
            <div class="card-body table-responsive"><table>
                <thead><tr><th>Usuario</th><th>Nombre</th><th>Email</th><th>Rol</th><th>Vinculado</th><th>Estado</th><th>Acciones</th></tr></thead>
                <tbody>${usuarios.map(u => `<tr>
                    <td><strong>${u.username}</strong></td>
                    <td>${u.nombre_completo || '-'}</td>
                    <td>${u.email || '-'}</td>
                    <td><span class="badge badge-primary">${u.rol}</span></td>
                    <td>${u.id_estudiante ? 'Est #'+u.id_estudiante : (u.id_docente ? 'Doc #'+u.id_docente : '-')}</td>
                    <td>${u.activo ? badge('Activa') : '<span class="badge badge-secondary">Inactivo</span>'}</td>
                    <td class="actions">
                        <button class="btn btn-outline btn-sm" onclick='formUsuario(${JSON.stringify(u)})'>Editar</button>
                        ${u.activo ? `<button class="btn btn-danger btn-sm" onclick="eliminarUsuario(${u.id_usuario})">Desactivar</button>` : ''}
                    </td></tr>`).join('')}
                </tbody></table></div></div>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Muestra un formulario modal para crear o editar un usuario, con campos para username, nombre completo, email, rol, contraseña y enlaces a estudiante o docente según corresponda, cargando las listas de estudiantes y docentes desde la caché o la API si es necesario
async function formUsuario(u = null) {
    // Cargar listas para enlazar
    let estudiantes = cache.estudiantes, docentes = cache.docentes;
    try {
        if (!estudiantes) estudiantes = await api('/estudiantes/');
        if (!docentes) docentes = await api('/docentes/');
        cache.estudiantes = estudiantes;
        cache.docentes = docentes;
    } catch (e) { estudiantes = estudiantes || []; docentes = docentes || []; }

    const estOpts = (estudiantes || []).map(e =>
        `<option value="${e.id_estudiante}" ${u?.id_estudiante==e.id_estudiante?'selected':''}>${e.apellidos} ${e.nombres} (${e.cedula})</option>`
    ).join('');
    const docOpts = (docentes || []).map(d =>
        `<option value="${d.id_docente}" ${u?.id_docente==d.id_docente?'selected':''}>${d.apellidos} ${d.nombres} (${d.cedula})</option>`
    ).join('');

    openModal(u ? 'Editar Usuario' : 'Nuevo Usuario', `
        <div class="form-grid">
            <div class="form-group"><label>Username *</label>
                <input class="form-control" id="uUser" value="${u?.username || ''}"></div>
            <div class="form-group"><label>Nombre Completo *</label>
                <input class="form-control" id="uNombre" value="${u?.nombre_completo || ''}"></div>
            <div class="form-group"><label>Email</label>
                <input class="form-control" id="uEmail" value="${u?.email || ''}"></div>
            <div class="form-group"><label>Rol *</label>
                <select class="form-control" id="uRol" onchange="toggleUsuarioVinculo()">
                    <option value="admin" ${u?.rol==='admin'?'selected':''}>Admin</option>
                    <option value="secretaria" ${u?.rol==='secretaria'?'selected':''}>Secretaría</option>
                    <option value="docente" ${u?.rol==='docente'?'selected':''}>Docente</option>
                    <option value="estudiante" ${u?.rol==='estudiante'?'selected':''}>Estudiante</option>
                </select></div>
            <div class="form-group"><label>Contraseña ${u ? '(vacío = no cambiar)' : '*'}</label>
                <input type="password" class="form-control" id="uPass"></div>
            <div class="form-group" id="uVinculoEst" style="display:none;">
                <label>Enlazar Estudiante</label>
                <select class="form-control" id="uEstudiante">
                    <option value="">— Ninguno —</option>
                    ${estOpts}
                </select>
            </div>
            <div class="form-group" id="uVinculoDoc" style="display:none;">
                <label>Enlazar Docente</label>
                <select class="form-control" id="uDocente">
                    <option value="">— Ninguno —</option>
                    ${docOpts}
                </select>
            </div>
        </div>`,
        `<button class="btn btn-outline" onclick="closeModal()">Cancelar</button>
         <button class="btn btn-primary" onclick="guardarUsuario(${u?.id_usuario || 'null'})">Guardar</button>`);
    toggleUsuarioVinculo();
}

// Muestra u oculta los campos de enlace a estudiante o docente según el rol seleccionado en el formulario de usuario, mostrando el campo correspondiente solo si el rol es "estudiante" o "docente"
function toggleUsuarioVinculo() {
    const rol = document.getElementById('uRol')?.value;
    const est = document.getElementById('uVinculoEst');
    const doc = document.getElementById('uVinculoDoc');
    if (est) est.style.display = rol === 'estudiante' ? '' : 'none';
    if (doc) doc.style.display = rol === 'docente' ? '' : 'none';
}

// Guarda un nuevo usuario o actualiza uno existente según el ID proporcionado, enviando los datos del formulario al backend y mostrando un mensaje de éxito o error según corresponda, y cerrando el modal y recargando la lista de usuarios si se guarda correctamente
async function guardarUsuario(id) {
    const rol = document.getElementById('uRol').value;
    const data = {
        username: document.getElementById('uUser').value,
        nombre_completo: document.getElementById('uNombre').value,
        email: document.getElementById('uEmail').value,
        rol
    };
    const pass = document.getElementById('uPass').value;
    if (pass) data.password = pass;
    if (!id && !pass) { toast('Contraseña requerida', 'error'); return; }

    // Enlaces
    if (rol === 'estudiante') {
        const v = document.getElementById('uEstudiante')?.value;
        data.id_estudiante = v ? parseInt(v) : null;
        data.id_docente = null;
    } else if (rol === 'docente') {
        const v = document.getElementById('uDocente')?.value;
        data.id_docente = v ? parseInt(v) : null;
        data.id_estudiante = null;
    } else {
        data.id_estudiante = null;
        data.id_docente = null;
    }

    try {
        if (id) await api(`/usuarios/${id}`, { method: 'PUT', body: data });
        else await api('/usuarios/', { method: 'POST', body: { ...data, password: pass } });
        closeModal(); toast('Guardado'); navigate('usuarios');
    } catch (err) { toast(err.message, 'error'); }
}

// Desactiva un usuario según el ID proporcionado, mostrando un mensaje de confirmación antes de enviar la solicitud al backend y mostrando un mensaje de éxito o error según corresponda, y recargando la lista de usuarios si se desactiva correctamente
async function eliminarUsuario(id) {
    if (!confirm('¿Desactivar?')) return;
    try { await api(`/usuarios/${id}`, { method: 'DELETE' }); toast('Desactivado'); navigate('usuarios'); }
    catch (err) { toast(err.message, 'error'); }
}

/* REPORTES */
// Renderiza la sección de reportes, mostrando filtros para seleccionar periodo, fechas, materia, sección y alumno, y tarjetas con botones para exportar reportes de pagos, matrículas, asistencias y calificaciones a Excel o PDF
async function renderReportes(el) {
    try {
        const [periodos, materias, secciones, estudiantes] = await Promise.all([
            api('/periodos'), api('/materias'), api('/secciones'),
            api('/estudiantes/').catch(() => [])
        ]);
        cache.periodos = periodos;
        cache.materias = materias;
        cache.secciones = secciones;
        el.innerHTML = `<div class="card"><div class="card-header"><h4>Reportes</h4></div>
            <div class="card-body">
                <div class="filters-bar">
                    <div class="form-group"><label>Periodo</label>
                        <select class="form-control" id="repPeriodo">
                            <option value="">Todos</option>
                            ${periodos.map(p => `<option value="${p.id_periodo}" ${p.activo?'selected':''}>${p.nombre}</option>`).join('')}
                        </select></div>
                    <div class="form-group"><label>Desde</label>
                        <input type="date" class="form-control" id="repDesde"></div>
                    <div class="form-group"><label>Hasta</label>
                        <input type="date" class="form-control" id="repHasta"></div>
                    <div class="form-group"><label>Materia</label>
                        <select class="form-control" id="repMateria">
                            <option value="">Todas</option>
                            ${materias.map(m => `<option value="${m.id_materia}">${m.nombre}${m.grado_nombre?' ('+m.grado_nombre+')':''}</option>`).join('')}
                        </select></div>
                    <div class="form-group"><label>Sección</label>
                        <select class="form-control" id="repSeccion">
                            <option value="">Todas</option>
                            ${secciones.map(s => `<option value="${s.id_seccion}">${s.grado_nombre} - ${s.nombre}</option>`).join('')}
                        </select></div>
                    <div class="form-group"><label>Alumno</label>
                        <select class="form-control" id="repAlumno">
                            <option value="">Todos</option>
                            ${estudiantes.map(e => `<option value="${e.id_estudiante}">${e.apellidos} ${e.nombres}</option>`).join('')}
                        </select></div>
                </div>
                <div style="display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px;margin-top:20px;">
                    <div class="card" style="padding:20px;text-align:center;">
                        <div style="font-size:2rem;">💰</div><h4 style="margin:10px 0;">Pagos</h4>
                        <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;">
                            <button class="btn btn-primary btn-sm" onclick="exportar('pagos','excel')">Excel</button>
                            <button class="btn btn-danger btn-sm" onclick="exportar('pagos','pdf')">PDF</button>
                        </div>
                    </div>
                    <div class="card" style="padding:20px;text-align:center;">
                        <div style="font-size:2rem;">📝</div><h4 style="margin:10px 0;">Matrículas</h4>
                        <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;">
                            <button class="btn btn-primary btn-sm" onclick="exportar('matriculas','excel')">Excel</button>
                            <button class="btn btn-danger btn-sm" onclick="exportar('matriculas','pdf')">PDF</button>
                        </div>
                    </div>
                    <div class="card" style="padding:20px;text-align:center;">
                        <div style="font-size:2rem;">✅</div><h4 style="margin:10px 0;">Asistencias</h4>
                        <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;">
                            <button class="btn btn-primary btn-sm" onclick="exportar('asistencias','excel')">Excel</button>
                            <button class="btn btn-danger btn-sm" onclick="exportar('asistencias','pdf')">PDF</button>
                        </div>
                    </div>
                    <div class="card" style="padding:20px;text-align:center;">
                        <div style="font-size:2rem;">📋</div><h4 style="margin:10px 0;">Calificaciones</h4>
                        <div style="display:flex;gap:8px;justify-content:center;flex-wrap:wrap;">
                            <button class="btn btn-primary btn-sm" onclick="exportar('calificaciones','excel')">Excel</button>
                            <button class="btn btn-danger btn-sm" onclick="exportar('calificaciones','pdf')">PDF</button>
                        </div>
                    </div>
                </div>
            </div></div>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Exporta un reporte según el tipo y formato seleccionados, construyendo la URL de exportación con los filtros aplicados y abriendo una nueva ventana para descargar el archivo generado
function exportar(tipo, formato) {
    let url = `${API}/reportes/exportar/${tipo}?formato=${formato}`;
    const per = document.getElementById('repPeriodo')?.value || '';
    const desde = document.getElementById('repDesde')?.value || '';
    const hasta = document.getElementById('repHasta')?.value || '';
    const mat = document.getElementById('repMateria')?.value || '';
    const sec = document.getElementById('repSeccion')?.value || '';
    const alum = document.getElementById('repAlumno')?.value || '';
    if (per) url += `&id_periodo=${per}`;
    if (desde) url += `&fecha_desde=${desde}`;
    if (hasta) url += `&fecha_hasta=${hasta}`;
    if (mat) url += `&id_materia=${mat}`;
    if (sec) url += `&id_seccion=${sec}`;
    if (alum) url += `&id_estudiante=${alum}`;
    window.open(url, '_blank');
}

/* VISTAS ALUMNO */
// Renderiza la sección de asistencias del alumno, mostrando una tabla con las asistencias registradas, filtros de fecha y un botón para descargar el reporte en PDF
async function renderMisAsistencias(el) {
    try {
        const data = await api('/asistencias/');
        el.innerHTML = `<div class="card"><div class="card-header">
                <h4>Mis Asistencias</h4>
                <button class="btn btn-danger btn-sm" onclick="exportarMisAsistencias()">Descargar PDF</button>
            </div>
            <div class="card-body">
                <div class="filters-bar">
                    <div class="form-group"><label>Desde</label>
                        <input type="date" class="form-control" id="misAsDesde" onchange="filtrarMisAsistencias()"></div>
                    <div class="form-group"><label>Hasta</label>
                        <input type="date" class="form-control" id="misAsHasta" onchange="filtrarMisAsistencias()"></div>
                </div>
                <div class="table-responsive" id="misAsistBody">
                ${data.length ? `<table><thead><tr><th>Fecha</th><th>Estado</th><th>Grado/Sección</th><th>Obs.</th></tr></thead>
                    <tbody>${data.map(a => `<tr>
                        <td>${fmtDate(a.fecha)}</td><td>${badge(a.estado)}</td>
                        <td>${a.grado_nombre || ''} ${a.seccion_nombre ? '- '+a.seccion_nombre : ''}</td>
                        <td>${a.observacion||'-'}</td>
                    </tr>`).join('')}</tbody></table>` : '<div class="empty-state">Sin registros</div>'}
                </div>
            </div></div>`;
        cache.misAsistencias = data;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Filtra las asistencias del alumno según las fechas seleccionadas en los filtros, actualizando la tabla de asistencias para mostrar solo los registros que cumplen con los criterios de fecha y mostrando un mensaje si no hay registros disponibles
function filtrarMisAsistencias() {
    const desde = document.getElementById('misAsDesde')?.value;
    const hasta = document.getElementById('misAsHasta')?.value;
    let data = cache.misAsistencias || [];
    if (desde) data = data.filter(a => String(a.fecha).substring(0,10) >= desde);
    if (hasta) data = data.filter(a => String(a.fecha).substring(0,10) <= hasta);
    const el = document.getElementById('misAsistBody');
    if (!el) return;
    el.innerHTML = data.length ? `<table><thead><tr><th>Fecha</th><th>Estado</th><th>Grado/Sección</th><th>Obs.</th></tr></thead>
        <tbody>${data.map(a => `<tr>
            <td>${fmtDate(a.fecha)}</td><td>${badge(a.estado)}</td>
            <td>${a.grado_nombre || ''} ${a.seccion_nombre ? '- '+a.seccion_nombre : ''}</td>
            <td>${a.observacion||'-'}</td>
        </tr>`).join('')}</tbody></table>` : '<div class="empty-state">Sin registros</div>';
}

// Exporta las asistencias del alumno a un archivo PDF según las fechas seleccionadas en los filtros, construyendo la URL de exportación con los parámetros correspondientes y abriendo una nueva ventana para descargar el archivo generado
function exportarMisAsistencias() {
    let url = `${API}/reportes/exportar/asistencias?formato=pdf`;
    const desde = document.getElementById('misAsDesde')?.value;
    const hasta = document.getElementById('misAsHasta')?.value;
    if (desde) url += `&fecha_desde=${desde}`;
    if (hasta) url += `&fecha_hasta=${hasta}`;
    window.open(url, '_blank');
}

// Renderiza la sección de calificaciones del alumno, mostrando un selector de periodo, un botón para cargar las calificaciones y una tabla con las calificaciones obtenidas en el periodo seleccionado, así como un botón para descargar el reporte en PDF
async function renderMisCalificaciones(el) {
    try {
        const periodos = await api('/periodos');
        el.innerHTML = `<div class="card"><div class="card-header">
                <h4>Mis Calificaciones</h4>
                <button class="btn btn-danger btn-sm" onclick="exportarMisCalificaciones()">Descargar PDF</button>
            </div>
            <div class="card-body">
                <div class="filters-bar">
                    <div class="form-group"><label>Periodo</label>
                        <select class="form-control" id="misCalPeriodo">
                            ${periodos.map(p => `<option value="${p.id_periodo}" ${p.activo?'selected':''}>${p.nombre}</option>`).join('')}
                        </select></div>
                    <button class="btn btn-primary" onclick="cargarMisCalificaciones()">Cargar</button>
                </div>
                <div class="table-responsive" id="misCalBody">
                    <div class="empty-state">Seleccione un periodo y pulse Cargar</div>
                </div>
            </div></div>`;
    } catch (err) {
        el.innerHTML = `<div class="alert alert-danger">${err.message || 'Error al cargar periodos'}</div>`;
        toast(err.message || 'Error al cargar', 'error');
    }
}

// Carga las calificaciones del alumno según el periodo seleccionado, mostrando una tabla con las materias, notas y promedios obtenidos, y almacenando los datos en caché para su posterior uso, mostrando un mensaje si no hay calificaciones disponibles o si ocurre un error al cargar los datos
async function cargarMisCalificaciones() {
    const idPeriodo = document.getElementById('misCalPeriodo')?.value;
    const el = document.getElementById('misCalBody');
    if (!idPeriodo) { toast('Seleccione un periodo', 'error'); return; }
    loading(el);
    try {
        let data = await api(`/calificaciones/?id_periodo=${idPeriodo}`);
        const seen = new Map();
        for (const c of data) {
            const key = c.id_materia ?? c.materia_nombre;
            if (!seen.has(key)) seen.set(key, c);
        }
        data = Array.from(seen.values());
        cache.misCalificaciones = data;
        if (!data.length) {
            el.innerHTML = '<div class="empty-state">Sin calificaciones en este periodo</div>';
            return;
        }
        el.innerHTML = `<table>
            <thead><tr><th>Materia</th><th>Periodo</th><th>N1</th><th>N2</th><th>N3</th><th>Final</th><th>Promedio</th></tr></thead>
            <tbody>${data.map(c => `<tr>
                <td>${c.materia_nombre}</td><td>${c.periodo_nombre}</td>
                <td>${c.nota1??'-'}</td><td>${c.nota2??'-'}</td><td>${c.nota3??'-'}</td>
                <td>${c.examen_final??'-'}</td>
                <td><strong>${c.nota_final!=null?parseFloat(c.nota_final).toFixed(2):'-'}</strong></td>
            </tr>`).join('')}</tbody></table>`;
    } catch (err) { el.innerHTML = `<div class="alert alert-danger">${err.message}</div>`; }
}

// Exporta las calificaciones del alumno a un archivo PDF según el periodo seleccionado, construyendo la URL de exportación con el parámetro correspondiente y abriendo una nueva ventana para descargar el archivo generado
function exportarMisCalificaciones() {
    const idPeriodo = document.getElementById('misCalPeriodo')?.value;
    let url = `${API}/reportes/exportar/calificaciones?formato=pdf`;
    if (idPeriodo) url += `&id_periodo=${idPeriodo}`;
    window.open(url, '_blank');
}

/* INIT */
// Inicializa los eventos de la aplicación, agregando listeners a los formularios y botones de login, logout, modal y menú lateral, y verificando la autenticación del usuario al cargar la página
document.getElementById('loginForm').addEventListener('submit', login);
document.getElementById('btnLogout').addEventListener('click', () => logout());
document.getElementById('modalClose').addEventListener('click', closeModal);
document.getElementById('modalOverlay').addEventListener('click', e => {
    if (e.target === e.currentTarget) closeModal();
});
document.getElementById('menuToggle').addEventListener('click', () => {
    document.getElementById('sidebar').classList.toggle('open');
});
checkAuth();