// ═══════ XSS UTILITY ═══════
function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(String(str == null ? '' : str)));
    return div.innerHTML;
}

let allAppointments = [];
let currentFilter  = 'all';
let currentDate    = '';

const AVATAR_COLORS = ['#6d9ba0','#5a8f6e','#c4956a','#5b8ec4','#9b7db8','#d46b6b'];
function avatarColor(str) {
    let h = 0;
    for (let i = 0; i < str.length; i++) h = str.charCodeAt(i) + ((h << 5) - h);
    return AVATAR_COLORS[Math.abs(h) % AVATAR_COLORS.length];
}

// ── INIT ────────────────────────────────────────────────────────────────
function init() {
    // Set datetime-local min
    const now = new Date();
    now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
    document.getElementById('fDateTime').min = now.toISOString().slice(0, 16);

    loadDoctors();
    loadPatients();
    loadAppointments();
}

// ── LOAD DOCTORS ─────────────────────────────────────────────────────────
function loadDoctors() {
    fetch('/receptionist/api/doctors/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        const sel = document.getElementById('fDoctor');
        data.doctors.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.id;
            opt.textContent = d.name;
            sel.appendChild(opt);
        });
    })
    .catch(err => console.error('Failed to load doctors:', err));
}

// ── LOAD PATIENTS ────────────────────────────────────────────────────────
function loadPatients() {
    fetch('/receptionist/api/patients/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        const sel = document.getElementById('fPatient');
        data.patients.forEach(p => {
            const opt = document.createElement('option');
            opt.value = p.id;
            opt.textContent = `${p.name} (${p.email})`;
            sel.appendChild(opt);
        });
    })
    .catch(err => console.error('Failed to load patients:', err));
}

// ── LOAD APPOINTMENTS ─────────────────────────────────────────────────────
function loadAppointments() {
    let url = '/receptionist/api/appointments/';
    const params = [];
    if (currentFilter !== 'all') params.push(`status=${currentFilter}`);
    if (currentDate) params.push(`date=${currentDate}`);
    if (params.length) url += '?' + params.join('&');

    fetch(url, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        allAppointments = data.appointments;
        renderTable(allAppointments);
        updateStats(allAppointments);
    })
    .catch(err => console.error('Failed to load appointments:', err));
}

// ── RENDER TABLE ──────────────────────────────────────────────────────────
function renderTable(appts) {
    const tbody = document.getElementById('apptTableBody');
    if (appts.length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="8">No appointments found.</td></tr>';
        return;
    }

    tbody.innerHTML = appts.map(a => {
        const patInitials = escapeHtml(a.patient_name.split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase());
        const docInitials = escapeHtml(a.doctor_name.replace('Dr. ','').split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase());
        const cancelBtn = (a.status !== 'cancelled' && a.status !== 'completed')
            ? `<button class="btn-cancel-appt" data-action="cancel" data-id="${a.id}">Cancel</button>`
            : '';
        const editBtn = (a.status !== 'cancelled' && a.status !== 'completed')
            ? `<button class="btn-edit" data-action="edit" data-id="${a.id}">Edit</button>`
            : '';

        return `
            <tr>
                <td>
                    <div class="patient-cell">
                        <div class="table-avatar" style="background:${avatarColor(a.patient_name)}">${patInitials}</div>
                        <div>
                            <div class="cell-name">${escapeHtml(a.patient_name)}</div>
                            <div class="cell-sub">${escapeHtml(a.patient_email)}</div>
                        </div>
                    </div>
                </td>
                <td>
                    <div class="patient-cell">
                        <div class="table-avatar" style="background:${avatarColor(a.doctor_name)}">${docInitials}</div>
                        <div class="cell-name">${escapeHtml(a.doctor_name)}</div>
                    </div>
                </td>
                <td><span class="type-${escapeHtml(a.appointment_type)}">${escapeHtml(a.type_display)}</span></td>
                <td>${escapeHtml(a.scheduled_fmt)}</td>
                <td>${escapeHtml(String(a.duration_minutes))} min</td>
                <td>${escapeHtml(a.location || '—')}</td>
                <td><span class="status-badge status-${escapeHtml(a.status)}">${escapeHtml(a.status_display)}</span></td>
                <td><div class="row-actions">${editBtn}${cancelBtn}</div></td>
            </tr>
        `;
    }).join('');
}

// ── STATS ─────────────────────────────────────────────────────────────────
function updateStats(appts) {
    const today = new Date().toDateString();
    const todayAppts = appts.filter(a => new Date(a.scheduled_at).toDateString() === today);
    document.getElementById('statToday').textContent     = todayAppts.length;
    document.getElementById('statScheduled').textContent = appts.filter(a => a.status === 'scheduled').length;
    document.getElementById('statConfirmed').textContent = appts.filter(a => a.status === 'confirmed').length;
    document.getElementById('statCancelled').textContent = appts.filter(a => a.status === 'cancelled').length;
}

// ── FILTER ────────────────────────────────────────────────────────────────
function setFilter(status, el) {
    currentFilter = status;
    document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    loadAppointments();
}

function applyDateFilter() {
    currentDate = document.getElementById('dateFilter').value;
    loadAppointments();
}

// ── SUBMIT FORM ───────────────────────────────────────────────────────────
function submitAppointment() {
    const btn      = document.getElementById('submitBtn');
    const feedback = document.getElementById('formFeedback');
    btn.disabled = true;
    feedback.className = 'form-feedback';

    const payload = {
        doctor_id:        parseInt(document.getElementById('fDoctor').value),
        patient_id:       parseInt(document.getElementById('fPatient').value),
        title:            document.getElementById('fTitle').value.trim(),
        appointment_type: document.getElementById('fType').value,
        scheduled_at:     document.getElementById('fDateTime').value,
        duration_minutes: parseInt(document.getElementById('fDuration').value),
        location:         document.getElementById('fLocation').value.trim(),
        notes:            document.getElementById('fNotes').value.trim(),
    };

    fetch('/receptionist/api/appointments/create/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF, 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify(payload),
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        if (data.ok) {
            feedback.textContent = `Appointment booked! ${data.appointment.patient_name} has been notified.`;
            feedback.className = 'form-feedback success';
            resetForm();
            loadAppointments();
        } else {
            const msg = typeof data.error === 'object' ? Object.values(data.error).join(' · ') : (data.error || 'Error');
            feedback.textContent = msg;
            feedback.className = 'form-feedback error';
        }
    })
    .catch(() => {
        btn.disabled = false;
        feedback.textContent = 'Network error — please try again.';
        feedback.className = 'form-feedback error';
    });
}

function resetForm() {
    ['fDoctor','fPatient','fTitle','fLocation','fNotes'].forEach(id => {
        const el = document.getElementById(id);
        if (el.tagName === 'SELECT') el.selectedIndex = 0;
        else el.value = '';
    });
    document.getElementById('fDuration').value = 60;
    document.getElementById('fDateTime').value = '';
    document.getElementById('fType').value = 'consultation';
}

function cancelEdit() {
    resetForm();
    document.getElementById('cancelEditBtn').style.display = 'none';
    document.getElementById('editingBadge').style.display = 'none';
    document.getElementById('submitBtn').textContent = 'Book & Notify Patient';
}

// ── EDIT MODAL ────────────────────────────────────────────────────────────
function openEdit(id) {
    const a = allAppointments.find(x => x.id === id);
    if (!a) return;

    document.getElementById('mApptId').value    = a.id;
    document.getElementById('mTitle').value     = a.title;
    document.getElementById('mType').value      = a.appointment_type;
    document.getElementById('mStatus').value    = a.status;
    document.getElementById('mDateTime').value  = a.scheduled_at.slice(0, 16);
    document.getElementById('mDuration').value  = a.duration_minutes;
    document.getElementById('mLocation').value  = a.location;
    document.getElementById('mNotes').value     = a.notes;

    document.getElementById('modalFeedback').className = 'form-feedback';
    document.getElementById('editModal').classList.add('open');
}

function closeModal() {
    document.getElementById('editModal').classList.remove('open');
}

function saveEdit() {
    const id  = parseInt(document.getElementById('mApptId').value);
    const btn = document.getElementById('modalSaveBtn');
    const fb  = document.getElementById('modalFeedback');
    btn.disabled = true;
    fb.className = 'form-feedback';

    const payload = {
        title:            document.getElementById('mTitle').value.trim(),
        appointment_type: document.getElementById('mType').value,
        status:           document.getElementById('mStatus').value,
        scheduled_at:     document.getElementById('mDateTime').value,
        duration_minutes: parseInt(document.getElementById('mDuration').value),
        location:         document.getElementById('mLocation').value.trim(),
        notes:            document.getElementById('mNotes').value.trim(),
    };

    fetch(`/receptionist/api/appointments/${id}/update/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF, 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify(payload),
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        if (data.ok) {
            closeModal();
            loadAppointments();
        } else {
            fb.textContent = data.error || 'Error saving changes.';
            fb.className = 'form-feedback error';
        }
    })
    .catch(() => {
        btn.disabled = false;
        fb.textContent = 'Network error.';
        fb.className = 'form-feedback error';
    });
}

// ── CANCEL ────────────────────────────────────────────────────────────────
function cancelAppt(id) {
    const a = allAppointments.find(x => x.id === id);
    if (!confirm(`Cancel appointment for ${a ? a.patient_name : 'this patient'}? They will be notified.`)) return;

    fetch(`/receptionist/api/appointments/${id}/cancel/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF, 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then(r => r.json())
    .then(data => { if (data.ok) loadAppointments(); })
    .catch(err => console.error('Failed to cancel appointment:', err));
}

// ── REQUEST QUEUE ────────────────────────────────────────────────────────
let currentReqFilter = 'pending';
let allRequests = [];

function loadRequests() {
    fetch(`/receptionist/api/requests/?status=${currentReqFilter}`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        allRequests = data.requests;
        renderRequestTable(allRequests);

        // Update pending badge
        if (currentReqFilter === 'pending') {
            document.getElementById('pendingBadge').textContent = `${allRequests.length} pending`;
        }
    })
    .catch(err => console.error('Failed to load requests:', err));
}

function renderRequestTable(reqs) {
    const tbody = document.getElementById('reqTableBody');
    if (reqs.length === 0) {
        tbody.innerHTML = '<tr class="empty-row"><td colspan="8">No requests found.</td></tr>';
        return;
    }

    tbody.innerHTML = reqs.map(r => {
        const initials = escapeHtml(r.patient_name.split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase());
        const actionBtns = r.status === 'pending'
            ? `<div class="row-actions">
                   <button class="btn-book-req" data-action="book" data-id="${r.id}">Book</button>
                   <button class="btn-decline-req" data-action="decline" data-id="${r.id}">Decline</button>
               </div>`
            : `<span class="req-action-done">${escapeHtml(r.status_display)}</span>`;

        const preferredDoctorCell = r.preferred_doctor_name
            ? escapeHtml(r.preferred_doctor_name)
            : '<span style="color:var(--text-muted)">No preference</span>';

        return `
            <tr>
                <td>
                    <div class="patient-cell">
                        <div class="table-avatar" style="background:${avatarColor(r.patient_name)}">${initials}</div>
                        <div>
                            <div class="cell-name">${escapeHtml(r.patient_name)}</div>
                            <div class="cell-sub">${escapeHtml(r.patient_email)}</div>
                        </div>
                    </div>
                </td>
                <td><span class="type-${escapeHtml(r.appointment_type)}">${escapeHtml(r.type_display)}</span></td>
                <td>${preferredDoctorCell}</td>
                <td>${escapeHtml(r.preferred_fmt)}</td>
                <td><div class="req-notes-cell" title="${escapeHtml(r.notes)}">${escapeHtml(r.notes || '—')}</div></td>
                <td>${escapeHtml(r.created_fmt)}</td>
                <td><span class="status-badge status-${escapeHtml(r.status)}">${escapeHtml(r.status_display)}</span></td>
                <td>${actionBtns}</td>
            </tr>
        `;
    }).join('');
}

function setReqFilter(status, el) {
    currentReqFilter = status;
    document.querySelectorAll('#requestsSection .filter-btn').forEach(b => b.classList.remove('active'));
    el.classList.add('active');
    loadRequests();
}

function declineRequest(id) {
    if (!confirm('Decline this request? The patient will be notified.')) return;
    fetch(`/receptionist/api/requests/${id}/decline/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF, 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then(r => r.json())
    .then(data => { if (data.ok) loadRequests(); })
    .catch(err => console.error('Failed to decline request:', err));
}

// ── BOOK-FROM-REQUEST MODAL ───────────────────────────────────────────────
let cachedDoctorsForModal = null;

function openBookModal(id) {
    const req = allRequests.find(r => r.id === id);
    if (!req) return;

    document.getElementById('bReqId').value    = id;
    document.getElementById('bPatientName').textContent = req.patient_name;
    document.getElementById('bRequestMeta').textContent =
        `${req.type_display} · ${req.preferred_fmt}` +
        (req.notes ? ` · "${req.notes}"` : '');

    document.getElementById('bType').value     = req.appointment_type;
    document.getElementById('bTitle').value    = req.type_display;
    document.getElementById('bDuration').value = 60;
    document.getElementById('bLocation').value = '';
    document.getElementById('bNotes').value    = req.notes || '';
    document.getElementById('bDateTime').value = '';
    document.getElementById('bFeedback').className = 'form-feedback';

    // Pre-fill date if provided
    if (req.preferred_date && req.preferred_time) {
        document.getElementById('bDateTime').value = `${req.preferred_date}T${req.preferred_time}`;
    } else if (req.preferred_date) {
        document.getElementById('bDateTime').value = `${req.preferred_date}T09:00`;
    }

    // Load doctors into the select
    const sel = document.getElementById('bDoctor');
    if (cachedDoctorsForModal) {
        populateDoctorSelect(sel, req.preferred_doctor_id, cachedDoctorsForModal);
        document.getElementById('bookReqModal').classList.add('open');
    } else {
        fetch('/receptionist/api/doctors/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(r => r.json())
        .then(data => {
            cachedDoctorsForModal = data.doctors;
            populateDoctorSelect(sel, req.preferred_doctor_id, data.doctors);
            document.getElementById('bookReqModal').classList.add('open');
        })
        .catch(err => console.error('Failed to load doctors for modal:', err));
    }
}

function populateDoctorSelect(sel, preferredId, doctors) {
    sel.innerHTML = '<option value="">Select doctor…</option>';
    doctors.forEach(d => {
        const opt = document.createElement('option');
        opt.value = d.id;
        opt.textContent = d.name;
        if (preferredId && d.id === preferredId) opt.selected = true;
        sel.appendChild(opt);
    });
}

function closeBookModal() {
    document.getElementById('bookReqModal').classList.remove('open');
}

function saveBookFromRequest() {
    const id  = parseInt(document.getElementById('bReqId').value);
    const btn = document.getElementById('bSaveBtn');
    const fb  = document.getElementById('bFeedback');
    btn.disabled = true;
    fb.className = 'form-feedback';

    const payload = {
        doctor_id:        parseInt(document.getElementById('bDoctor').value),
        title:            document.getElementById('bTitle').value.trim(),
        appointment_type: document.getElementById('bType').value,
        scheduled_at:     document.getElementById('bDateTime').value,
        duration_minutes: parseInt(document.getElementById('bDuration').value),
        location:         document.getElementById('bLocation').value.trim(),
        notes:            document.getElementById('bNotes').value.trim(),
    };

    fetch(`/receptionist/api/requests/${id}/book/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF, 'X-Requested-With': 'XMLHttpRequest' },
        body: JSON.stringify(payload),
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        if (data.ok) {
            closeBookModal();
            loadRequests();
            loadAppointments();
        } else {
            fb.textContent = data.error || 'Error booking appointment.';
            fb.className = 'form-feedback error';
        }
    })
    .catch(() => {
        btn.disabled = false;
        fb.textContent = 'Network error.';
        fb.className = 'form-feedback error';
    });
}

// ═══════ DOM CONTENT LOADED ═══════
document.addEventListener('DOMContentLoaded', function () {
    init();
    loadRequests();

    // Poll pending requests every 60 s
    setInterval(() => { if (currentReqFilter === 'pending') loadRequests(); }, 60000);

    // Event delegation for appointment table buttons
    document.getElementById('apptTableBody').addEventListener('click', e => {
        const btn = e.target.closest('[data-action]');
        if (!btn) return;
        const id = parseInt(btn.dataset.id);
        if (btn.dataset.action === 'edit') openEdit(id);
        if (btn.dataset.action === 'cancel') cancelAppt(id);
    });

    // Event delegation for request table buttons
    document.getElementById('reqTableBody').addEventListener('click', e => {
        const btn = e.target.closest('[data-action]');
        if (!btn) return;
        const id = parseInt(btn.dataset.id);
        if (btn.dataset.action === 'book') openBookModal(id);
        if (btn.dataset.action === 'decline') declineRequest(id);
    });

    // Modal backdrop close
    document.getElementById('editModal').addEventListener('click', function (e) {
        if (e.target === this) closeModal();
    });

    document.getElementById('bookReqModal').addEventListener('click', function (e) {
        if (e.target === this) closeBookModal();
    });
});
