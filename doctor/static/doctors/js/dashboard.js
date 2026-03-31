/* dashboard.js — HealthPlus Physician Dashboard
 * CSRF token must be defined before this script runs:
 *   <script>const CSRF = '{{ csrf_token }}';</script>
 */

// ── UTILITIES ────────────────────────────────────────────────────────────────
function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(String(str == null ? '' : str)));
    return div.innerHTML;
}

// Shared colour palette (used for both patient avatars and conversation avatars)
const PALETTE = ['#6d9ba0', '#5a8f6e', '#c4956a', '#5b8ec4', '#9b7ab5', '#b55a7a'];
const _convColors = {};
let _colorIdx = 0;

/** Deterministic colour by numeric id (for patient avatars). */
function palette(id) {
    return PALETTE[id % PALETTE.length];
}

/** Sequential colour assigned once per conversation id. */
function convColor(id) {
    if (!_convColors[id]) _convColors[id] = PALETTE[_colorIdx++ % PALETTE.length];
    return _convColors[id];
}

// ── SCHEDULE MEETING ─────────────────────────────────────────────────────────
function scheduleMeeting(e) {
    e.preventDefault();
    const btn      = document.getElementById('meetingSubmitBtn');
    const feedback = document.getElementById('meetingFeedback');
    btn.disabled   = true;
    feedback.className = 'meeting-feedback';
    feedback.style.display = 'none';

    const payload = {
        patient_email: document.getElementById('patientEmail').value.trim(),
        title:         document.getElementById('meetingTitle').value.trim(),
        scheduled_at:  document.getElementById('meetingTime').value,
    };

    fetch('/doctors/meetings/create/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF,
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify(payload),
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        if (data.ok) {
            feedback.textContent = `Meeting scheduled! ${data.meeting.patient_name} has been notified.`;
            feedback.className = 'meeting-feedback success';
            document.getElementById('meetingForm').reset();
            loadMeetings();
        } else {
            feedback.textContent = data.error || 'Something went wrong.';
            feedback.className = 'meeting-feedback error';
        }
    })
    .catch(() => {
        btn.disabled = false;
        feedback.textContent = 'Network error — please try again.';
        feedback.className = 'meeting-feedback error';
    });
}

// ── LOAD MEETINGS ─────────────────────────────────────────────────────────────
function loadMeetings() {
    fetch('/doctors/meetings/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        const list      = document.getElementById('meetingList');
        const countPill = document.getElementById('meetingCount');
        const meetings  = data.meetings;

        countPill.textContent = meetings.length + ' upcoming';

        if (meetings.length === 0) {
            list.innerHTML = '<div class="no-meetings">No upcoming meetings.</div>';
            return;
        }

        list.innerHTML = meetings.map(m => {
            const initials  = escapeHtml(m.patient_name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase());
            const safeTitle = escapeHtml(m.title);
            const safeName  = escapeHtml(m.patient_name);
            const safeFmt   = escapeHtml(m.scheduled_fmt);
            const joinBtn   = m.join_url
                ? `<a href="${escapeHtml(m.join_url)}" target="_blank" rel="noopener noreferrer" class="btn-join">Join</a>`
                : '';
            return `
                <div class="meeting-item" id="meeting-${m.id}">
                    <div class="meeting-avatar">${initials}</div>
                    <div class="meeting-info">
                        <div class="meeting-title-text">${safeTitle}</div>
                        <div class="meeting-meta">${safeName} · ${safeFmt}</div>
                    </div>
                    <div class="meeting-actions">
                        ${joinBtn}
                        <button class="btn-cancel" data-meeting-id="${m.id}">Cancel</button>
                    </div>
                </div>
            `;
        }).join('');

        list.querySelectorAll('.btn-cancel').forEach(btn => {
            btn.addEventListener('click', () => cancelMeeting(parseInt(btn.dataset.meetingId)));
        });
    })
    .catch(() => {
        const list = document.getElementById('meetingList');
        list.innerHTML = '<div class="meeting-error">Failed to load meetings. Please refresh.</div>';
    });
}

// ── CANCEL MEETING ────────────────────────────────────────────────────────────
function cancelMeeting(id) {
    if (!confirm('Cancel this meeting and notify the patient?')) return;
    fetch(`/doctors/meetings/${id}/cancel/`, {
        method: 'POST',
        headers: { 'X-CSRFToken': CSRF, 'X-Requested-With': 'XMLHttpRequest' },
    })
    .then(r => r.json())
    .then(data => { if (data.ok) loadMeetings(); })
    .catch(() => alert('Failed to cancel meeting. Please try again.'));
}

// ── MESSAGING ─────────────────────────────────────────────────────────────────
let activeConvId = null;

function loadConversations() {
    fetch('/doctors/messages/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        const list = document.getElementById('convList');
        list.innerHTML = '';
        let totalUnread = 0;

        data.conversations.forEach((conv, i) => {
            totalUnread += conv.unread_count;
            const color = convColor(conv.id);

            const item = document.createElement('div');
            item.className = 'conv-item' + (i === 0 ? ' active' : '');
            item.dataset.convId = conv.id;
            item.addEventListener('click', () => openConv(conv.id));

            const avatar = document.createElement('div');
            avatar.className = 'conv-avatar';
            avatar.style.background = color;
            avatar.textContent = conv.patient_initials;

            const info = document.createElement('div');
            info.className = 'conv-info';

            const name = document.createElement('div');
            name.className = 'conv-name';
            name.textContent = conv.patient_name;

            const preview = document.createElement('div');
            preview.className = 'conv-preview';
            preview.textContent = conv.last_message || 'No messages yet';

            info.appendChild(name);
            info.appendChild(preview);
            item.appendChild(avatar);
            item.appendChild(info);

            if (conv.unread_count > 0) {
                const badge = document.createElement('span');
                badge.className = 'conv-badge';
                badge.textContent = conv.unread_count;
                item.appendChild(badge);
            }

            list.appendChild(item);
        });

        const pill   = document.getElementById('msgUnreadPill');
        const statEl = document.getElementById('statUnreadMessages');
        if (totalUnread > 0) {
            pill.textContent = totalUnread + ' new';
            pill.style.display = '';
        } else {
            pill.style.display = 'none';
        }
        if (statEl) statEl.textContent = totalUnread;

        if (data.conversations.length === 0) {
            const empty = document.createElement('div');
            empty.className = 'conv-loading';
            empty.innerHTML = 'No conversations yet.<br>Click + New to start one.';
            list.appendChild(empty);
        } else if (!activeConvId) {
            openConv(data.conversations[0].id);
        }
    })
    .catch(() => {
        const list = document.getElementById('convList');
        list.innerHTML = '<div class="conv-loading">Failed to load conversations.</div>';
    });
}

function openConv(convId) {
    activeConvId = convId;
    document.querySelectorAll('.conv-item').forEach(el => {
        el.classList.toggle('active', parseInt(el.dataset.convId) === convId);
    });

    fetch(`/doctors/messages/${convId}/`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        const color       = convColor(convId);
        const headerAvatar = document.getElementById('chatHeaderAvatar');
        const headerName   = document.getElementById('chatHeaderName');
        const header       = document.getElementById('chatHeader');
        const compose      = document.getElementById('chatCompose');
        const convItem     = document.querySelector(`.conv-item[data-conv-id="${convId}"]`);

        headerAvatar.style.background = color;
        if (convItem) {
            headerAvatar.textContent = convItem.querySelector('.conv-avatar').textContent;
            headerName.textContent   = convItem.querySelector('.conv-name').textContent;
        }

        header.style.display  = '';
        compose.style.display = '';

        renderMessages(data.messages, color);

        const badge = convItem?.querySelector('.conv-badge');
        if (badge) badge.remove();
    })
    .catch(() => {
        document.getElementById('chatMessages').innerHTML =
            '<div class="chat-empty">Failed to load messages. Please try again.</div>';
    });
}

function renderMessages(messages, color) {
    const container = document.getElementById('chatMessages');
    container.innerHTML = '';

    if (messages.length === 0) {
        container.innerHTML = '<div class="chat-empty">No messages yet. Say hello!</div>';
        return;
    }

    messages.forEach(msg => {
        const row = document.createElement('div');
        row.className = 'msg-row ' + (msg.from_me ? 'sent' : 'received');

        const avatarColor = msg.from_me ? 'var(--accent-green)' : (color || 'var(--accent-teal)');

        const avatar = document.createElement('div');
        avatar.className = 'msg-avatar';
        avatar.style.background = avatarColor;
        avatar.textContent = msg.sender_initials;

        const time = document.createElement('div');
        time.className = 'bubble-time';
        time.textContent = msg.time;

        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = msg.text;

        row.appendChild(avatar);
        row.appendChild(time);
        row.appendChild(bubble);
        container.appendChild(row);
    });

    container.scrollTop = container.scrollHeight;
}

function sendMessage() {
    const input = document.getElementById('composeInput');
    const text  = input.value.trim();
    if (!text || activeConvId === null) return;
    input.value = '';

    fetch(`/doctors/messages/${activeConvId}/send/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
        body: JSON.stringify({ text }),
    })
    .then(r => r.json())
    .then(msg => {
        if (msg.error) {
            const errDiv = document.createElement('div');
            errDiv.className = 'chat-empty';
            errDiv.textContent = 'Failed to send message.';
            document.getElementById('chatMessages').appendChild(errDiv);
            return;
        }

        const container = document.getElementById('chatMessages');
        container.querySelector('.chat-empty')?.remove();

        const row = document.createElement('div');
        row.className = 'msg-row sent';

        const avatar = document.createElement('div');
        avatar.className = 'msg-avatar';
        avatar.style.background = 'var(--accent-green)';
        avatar.textContent = msg.sender_initials;

        const time = document.createElement('div');
        time.className = 'bubble-time';
        time.textContent = msg.time;

        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = msg.text;

        row.appendChild(avatar);
        row.appendChild(time);
        row.appendChild(bubble);
        container.appendChild(row);
        container.scrollTop = container.scrollHeight;

        const convItem = document.querySelector(`.conv-item[data-conv-id="${activeConvId}"]`);
        if (convItem) {
            const preview = convItem.querySelector('.conv-preview');
            if (preview) preview.textContent = msg.text;
        }
    })
    .catch(() => {
        const errDiv = document.createElement('div');
        errDiv.className = 'chat-empty';
        errDiv.textContent = 'Network error — message not sent.';
        document.getElementById('chatMessages').appendChild(errDiv);
    });
}

function handleKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); }
}

// ── NEW CONVERSATION MODAL ────────────────────────────────────────────────────
function openNewConvModal() {
    document.getElementById('newConvModal').classList.add('open');
    document.getElementById('newConvEmail').value = '';
    document.getElementById('newConvError').style.display = 'none';
    document.getElementById('newConvEmail').focus();
}

function closeNewConvModal() {
    document.getElementById('newConvModal').classList.remove('open');
}

function startNewConversation() {
    const email = document.getElementById('newConvEmail').value.trim();
    const errEl = document.getElementById('newConvError');
    if (!email) { errEl.textContent = 'Please enter a patient email.'; errEl.style.display = ''; return; }

    fetch('/doctors/messages/start/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
        body: JSON.stringify({ patient_email: email }),
    })
    .then(r => r.json())
    .then(data => {
        if (!data.ok) {
            errEl.textContent = data.error || 'Something went wrong.';
            errEl.style.display = '';
            return;
        }
        closeNewConvModal();
        loadConversations();
        setTimeout(() => openConv(data.conv_id), 300);
    })
    .catch(() => {
        errEl.textContent = 'Network error — please try again.';
        errEl.style.display = '';
    });
}

// ── PATIENT LIST ──────────────────────────────────────────────────────────────
let allPatients = [];

function loadPatients() {
    fetch('/doctors/patients/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        allPatients = data.patients;
        document.getElementById('patientCountPill').textContent = allPatients.length + ' active';
        renderPatients(allPatients);
    })
    .catch(() => {
        document.getElementById('patientTableBody').innerHTML =
            '<tr><td colspan="6" class="pt-error">Failed to load patients. Please refresh.</td></tr>';
    });
}

function renderPatients(patients) {
    const tbody = document.getElementById('patientTableBody');
    if (patients.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" class="pt-loading">No patients found.</td></tr>';
        return;
    }
    tbody.innerHTML = patients.map(p => {
        const color      = palette(p.id);
        const initials   = escapeHtml(p.initials);
        const name       = escapeHtml(p.name);
        const email      = escapeHtml(p.email);
        const dob        = escapeHtml(p.dob);
        const bloodType  = escapeHtml(p.blood_type);
        const conditions = escapeHtml(p.conditions);
        const lastRx     = escapeHtml(p.last_rx);
        // Store raw name in data attribute — safe to insert as HTML attribute via escapeHtml
        const safeNameAttr = escapeHtml(p.name);
        return `
            <tr>
                <td>
                    <div class="pt-name-cell">
                        <div class="pt-avatar" style="background:${color}">${initials}</div>
                        <div>
                            <div class="pt-name">${name}</div>
                            <div class="pt-email">${email}</div>
                        </div>
                    </div>
                </td>
                <td>${dob}</td>
                <td>${bloodType}</td>
                <td><span class="condition-tag">${conditions}</span></td>
                <td class="pt-last-rx">${lastRx}</td>
                <td>
                    <div class="pt-actions">
                        <button class="btn-prescribe"
                                data-action="prescribe"
                                data-patient-id="${p.id}"
                                data-patient-name="${safeNameAttr}">Prescribe</button>
                        <button class="btn-rx-history"
                                data-action="rx-history"
                                data-patient-id="${p.id}"
                                data-patient-name="${safeNameAttr}">History</button>
                    </div>
                </td>
            </tr>
        `;
    }).join('');
}

function filterPatients(query) {
    const q = query.toLowerCase();
    renderPatients(allPatients.filter(p =>
        p.name.toLowerCase().includes(q) ||
        p.email.toLowerCase().includes(q) ||
        p.conditions.toLowerCase().includes(q)
    ));
}

// Event delegation for Prescribe / History buttons
document.addEventListener('click', e => {
    const btn = e.target.closest('[data-action]');
    if (!btn) return;
    const id   = parseInt(btn.dataset.patientId);
    const name = btn.dataset.patientName;
    if (btn.dataset.action === 'prescribe')  openPrescribeModal(id, name);
    if (btn.dataset.action === 'rx-history') openRxHistory(id, name);
});

// ── PRESCRIBE MODAL ───────────────────────────────────────────────────────────
let prescribeTargetId = null;

function openPrescribeModal(patientId, patientName) {
    prescribeTargetId = patientId;
    document.getElementById('prescribePatientLabel').textContent = 'Patient: ' + patientName;
    document.getElementById('rxMedication').value    = '';
    document.getElementById('rxDosage').value        = '';
    document.getElementById('rxFrequency').value     = '';
    document.getElementById('rxDuration').value      = '';
    document.getElementById('rxInstructions').value  = '';
    document.getElementById('prescribeError').style.display   = 'none';
    document.getElementById('prescribeSuccess').style.display = 'none';
    document.getElementById('prescribeSubmitBtn').disabled    = false;
    document.getElementById('prescribeModal').classList.add('open');
    document.getElementById('rxMedication').focus();
}

function closePrescribeModal() {
    document.getElementById('prescribeModal').classList.remove('open');
    prescribeTargetId = null;
}

function submitPrescription() {
    const errEl = document.getElementById('prescribeError');
    const okEl  = document.getElementById('prescribeSuccess');
    const btn   = document.getElementById('prescribeSubmitBtn');

    const medication   = document.getElementById('rxMedication').value.trim();
    const dosage       = document.getElementById('rxDosage').value.trim();
    const frequency    = document.getElementById('rxFrequency').value.trim();
    const duration     = document.getElementById('rxDuration').value.trim();
    const instructions = document.getElementById('rxInstructions').value.trim();

    errEl.style.display = 'none';
    okEl.style.display  = 'none';

    if (!medication || !dosage || !frequency) {
        errEl.textContent = 'Medication, dosage, and frequency are required.';
        errEl.style.display = '';
        return;
    }

    btn.disabled = true;

    fetch(`/doctors/patients/${prescribeTargetId}/prescribe/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', 'X-CSRFToken': CSRF },
        body: JSON.stringify({ medication, dosage, frequency, duration, instructions }),
    })
    .then(r => r.json())
    .then(data => {
        btn.disabled = false;
        if (!data.ok) {
            errEl.textContent = data.error || 'Something went wrong.';
            errEl.style.display = '';
            return;
        }
        okEl.textContent = `${data.medication} prescribed successfully on ${data.prescribed_at}.`;
        okEl.style.display = '';
        loadPatients();
        setTimeout(closePrescribeModal, 1800);
    })
    .catch(() => {
        btn.disabled = false;
        errEl.textContent = 'Network error — please try again.';
        errEl.style.display = '';
    });
}

// ── RX HISTORY MODAL ──────────────────────────────────────────────────────────
function openRxHistory(patientId, patientName) {
    document.getElementById('rxHistoryTitle').textContent = patientName + ' — Prescription History';
    const body = document.getElementById('rxHistoryBody');
    body.innerHTML = '<div class="rx-detail" style="padding:12px 0;">Loading\u2026</div>';
    document.getElementById('rxHistoryModal').classList.add('open');

    fetch(`/doctors/patients/${patientId}/prescriptions/`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        if (data.prescriptions.length === 0) {
            body.innerHTML = '<div class="rx-detail" style="padding:12px 0;">No prescriptions on record.</div>';
            return;
        }
        body.innerHTML = '';
        data.prescriptions.forEach(rx => {
            const item = document.createElement('div');
            item.className = 'rx-item';

            const hdr = document.createElement('div');
            hdr.className = 'rx-item-header';

            const medName = document.createElement('span');
            medName.className = 'rx-med-name';
            medName.textContent = rx.medication;

            const date = document.createElement('span');
            date.className = 'rx-date';
            date.textContent = rx.date;

            hdr.appendChild(medName);
            hdr.appendChild(date);

            const detail = document.createElement('div');
            detail.className = 'rx-detail';
            detail.textContent = `${rx.dosage} \u00b7 ${rx.frequency}${rx.duration !== '\u2014' ? ' \u00b7 ' + rx.duration : ''}`;

            const doctor = document.createElement('div');
            doctor.className = 'rx-doctor';
            doctor.textContent = 'By ' + rx.doctor;

            item.appendChild(hdr);
            item.appendChild(detail);

            if (rx.instructions) {
                const instr = document.createElement('div');
                instr.className = 'rx-instructions';
                instr.textContent = rx.instructions;
                item.appendChild(instr);
            }

            item.appendChild(doctor);
            body.appendChild(item);
        });
    })
    .catch(() => {
        body.innerHTML = '<div class="rx-detail" style="padding:12px 0;">Failed to load prescriptions.</div>';
    });
}

function closeRxHistoryModal() {
    document.getElementById('rxHistoryModal').classList.remove('open');
}

// ── INIT ──────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
    const dtInput = document.getElementById('meetingTime');
    if (dtInput) {
        const now = new Date();
        now.setMinutes(now.getMinutes() - now.getTimezoneOffset());
        dtInput.min = now.toISOString().slice(0, 16);
    }

    loadMeetings();
    loadConversations();
    loadPatients();

    // Refresh messages every 30 seconds
    setInterval(() => {
        loadConversations();
        if (activeConvId !== null) openConv(activeConvId);
    }, 30000);
});
