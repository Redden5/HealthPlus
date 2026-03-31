// ═══════ XSS UTILITY ═══════
function escapeHtml(str) {
    const div = document.createElement('div');
    div.appendChild(document.createTextNode(String(str == null ? '' : str)));
    return div.innerHTML;
}

// ═══════ MOOD CONFIG ═══════
const moodLabels = [
    '', 'Very Low', 'Low', 'Struggling', 'Difficult',
    'Neutral', 'Okay', 'Good', 'Great', 'Wonderful', 'Excellent'
];

const moodColors = [
    '', '#c0392b', '#d35400', '#e67e22', '#f39c12',
    '#b8b8b8', '#7dcea0', '#52be80', '#27ae60', '#1e8449', '#0e6631'
];

// History loaded from the backend, keyed by period ('7d','14d','30d')
const moodHistoryCache = {};
let selectedMood = null;
let moodLogged = false;
let currentPeriod = '7d';

// ═══════ INIT ═══════
function initMood() {
    buildMoodScale();
    loadMoodStats();
    loadMoodHistory(currentPeriod);
}

// ═══════ STATS (today + 7-day avg) ═══════
function loadMoodStats() {
    fetch(MOOD_STATS_URL, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(r => r.json())
        .then(data => {
            if (data.today.score !== null) {
                document.getElementById('todayMoodStat').textContent = data.today.score;
                document.getElementById('todayMoodStat').style.color = moodColors[data.today.score];
                // Already logged today — show confirmation state
                if (data.today.logged) {
                    moodLogged = true;
                    showLoggedConfirmation(data.today.score);
                }
            }
            if (data.week_avg !== null) {
                document.getElementById('avgMoodStat').textContent = data.week_avg;
            }
        })
        .catch(err => console.error('Failed to load mood stats:', err));
}

// ═══════ HISTORY ═══════
function loadMoodHistory(period) {
    const days = period === '7d' ? 7 : period === '14d' ? 14 : 30;
    if (moodHistoryCache[period]) { renderChart(); return; }

    fetch(`${MOOD_HISTORY_URL}?days=${days}`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(r => r.json())
        .then(data => {
            moodHistoryCache[period] = data.history.map(d => ({
                label: d.label,
                mood: d.score,
                mood_label: d.mood_label,
            }));
            renderChart();
        })
        .catch(err => console.error('Failed to load mood history:', err));
}

// ═══════ BUILD MOOD SCALE ═══════
function buildMoodScale() {
    const container = document.getElementById('moodScale');
    for (let i = 1; i <= 10; i++) {
        const btn = document.createElement('button');
        btn.className = 'mood-btn';
        btn.textContent = i;
        btn.style.background = moodColors[i];
        btn.style.height = (24 + i * 3.5) + 'px';
        btn.onclick = () => selectMood(i);
        container.appendChild(btn);
    }
}

function selectMood(val) {
    if (moodLogged) return;
    selectedMood = val;
    document.querySelectorAll('.mood-btn').forEach((b, idx) => {
        b.classList.toggle('selected', idx + 1 === val);
    });
    document.getElementById('moodNum').textContent = val;
    document.getElementById('moodNum').style.color = moodColors[val];
    document.getElementById('moodLabel').textContent = moodLabels[val];
    document.getElementById('moodSubmitBtn').classList.add('visible');
}

function submitMood() {
    if (!selectedMood) return;

    fetch(MOOD_LOG_URL, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF,
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({ score: selectedMood }),
    })
    .then(r => r.json())
    .then(data => {
        if (!data.ok) return;
        moodLogged = true;

        // Update stat card
        document.getElementById('todayMoodStat').textContent = selectedMood;
        document.getElementById('todayMoodStat').style.color = moodColors[selectedMood];

        // Bust history cache so chart reloads fresh data next period switch
        Object.keys(moodHistoryCache).forEach(k => delete moodHistoryCache[k]);
        loadMoodHistory(currentPeriod);

        // Reload avg
        loadMoodStats();

        showLoggedConfirmation(selectedMood);
    })
    .catch(err => console.error('Failed to submit mood:', err));
}

function showLoggedConfirmation(score) {
    const area = document.getElementById('moodEntryArea');
    // moodColors[score] and moodLabels[score] are local constants — safe to use directly
    area.innerHTML = `
        <div class="mood-logged-msg">
            <div class="check-circle">
                <svg viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
            </div>
            <strong style="color:${moodColors[score]}">Mood: ${score}/10 — ${moodLabels[score]}</strong>
            <p>Logged for today. Keep it up!</p>
        </div>
    `;
}

// ═══════ CHART ═══════
function setPeriod(period, el) {
    currentPeriod = period;
    document.querySelectorAll('.period-tab').forEach(t => t.classList.remove('active'));
    el.classList.add('active');
    loadMoodHistory(period);
}

function renderChart() {
    const svg = document.getElementById('moodChart');
    const data = (moodHistoryCache[currentPeriod] || []).filter(d => d.mood !== null);

    if (data.length === 0) { svg.innerHTML = ''; return; }

    const W = svg.clientWidth || 500;
    const H = 180;
    const padL = 32, padR = 16, padT = 12, padB = 28;
    const chartW = W - padL - padR;
    const chartH = H - padT - padB;

    const avg = data.reduce((s, d) => s + d.mood, 0) / data.length;

    let svgContent = `<defs>
        <linearGradient id="moodGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stop-color="#6d9ba0" stop-opacity="0.25"/>
            <stop offset="100%" stop-color="#6d9ba0" stop-opacity="0.02"/>
        </linearGradient>
    </defs>`;

    // Y labels + grid
    for (let y = 0; y <= 10; y += 2) {
        const py = padT + chartH - (y / 10) * chartH;
        svgContent += `<line x1="${padL}" y1="${py}" x2="${W - padR}" y2="${py}" class="chart-grid-line"/>`;
        svgContent += `<text x="${padL - 6}" y="${py + 3.5}" class="chart-y-label">${y}</text>`;
    }

    // Average line
    const avgY = padT + chartH - (avg / 10) * chartH;
    svgContent += `<line x1="${padL}" y1="${avgY}" x2="${W - padR}" y2="${avgY}" stroke="${moodColors[Math.round(avg)]}" stroke-width="1" stroke-dasharray="4,4" opacity="0.5"/>`;

    // Build points
    const points = data.map((d, i) => {
        const x = padL + (i / (data.length - 1 || 1)) * chartW;
        const y = padT + chartH - (d.mood / 10) * chartH;
        return { x, y, ...d };
    });

    // Area fill
    if (points.length > 1) {
        let areaPath = `M${points[0].x},${points[0].y}`;
        points.slice(1).forEach(p => areaPath += ` L${p.x},${p.y}`);
        areaPath += ` L${points[points.length - 1].x},${padT + chartH} L${points[0].x},${padT + chartH} Z`;
        svgContent += `<path d="${areaPath}" class="chart-area-fill"/>`;
    }

    // Line
    if (points.length > 1) {
        let linePath = `M${points[0].x},${points[0].y}`;
        points.slice(1).forEach(p => linePath += ` L${p.x},${p.y}`);
        svgContent += `<path d="${linePath}" class="chart-line"/>`;
    }

    // Dots + labels (numeric data and local constants — safe)
    points.forEach((p, i) => {
        const safeLabel = p.label.replace(/'/g, "\\'");
        const safeMoodLabel = (p.mood_label || moodLabels[p.mood] || '').replace(/'/g, "\\'");
        svgContent += `<circle cx="${p.x}" cy="${p.y}" r="4" class="chart-dot" data-idx="${i}"
            onmouseenter="showTooltip(event, '${safeLabel}', ${p.mood}, '${safeMoodLabel}')"
            onmouseleave="hideTooltip()"/>`;
        const showLabel = data.length <= 14 || i % Math.ceil(data.length / 10) === 0 || i === data.length - 1;
        if (showLabel) {
            svgContent += `<text x="${p.x}" y="${H - 4}" class="chart-label">${p.label.split(' ')[1]}</text>`;
        }
    });

    svg.innerHTML = svgContent;
}

function showTooltip(e, label, mood, moodLabel) {
    const tt = document.getElementById('chartTooltip');
    const rect = document.getElementById('chartArea').getBoundingClientRect();
    tt.innerHTML = `<strong>${label}</strong> — Mood: ${mood}/10 (${moodLabel})`;
    tt.style.left = (e.clientX - rect.left + 12) + 'px';
    tt.style.top = (e.clientY - rect.top - 36) + 'px';
    tt.classList.add('visible');
}

function hideTooltip() {
    document.getElementById('chartTooltip').classList.remove('visible');
}

// ═══════ MESSAGING ═══════
let activeConvId = null;
const convColors = {};

const CONV_COLORS = ['#6d9ba0','#5a8f6e','#c4956a','#5b8ec4','#9b7db8'];
let colorIdx = 0;

function convColor(convId) {
    if (!convColors[convId]) convColors[convId] = CONV_COLORS[colorIdx++ % CONV_COLORS.length];
    return convColors[convId];
}

// Load and render conversation list
function loadConversations() {
    fetch(LIST_CONVERSATIONS_URL, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(r => r.json())
        .then(data => {
            const list = document.getElementById('convList');
            list.innerHTML = '';
            let totalUnread = 0;

            data.conversations.forEach((conv, i) => {
                totalUnread += conv.unread_count;
                const item = document.createElement('div');
                item.className = 'conv-item' + (i === 0 ? ' active' : '');
                item.dataset.convId = conv.id;
                item.onclick = () => openConv(conv.id);

                const avatar = document.createElement('div');
                avatar.className = 'conv-avatar';
                avatar.style.background = convColor(conv.id);
                avatar.textContent = conv.participant_initials;

                const info = document.createElement('div');
                info.className = 'conv-info';
                const name = document.createElement('div');
                name.className = 'conv-name';
                name.textContent = conv.participant_name;
                const last = document.createElement('div');
                last.className = 'conv-last';
                last.textContent = conv.last_message || '';
                info.appendChild(name);
                info.appendChild(last);
                item.appendChild(avatar);
                item.appendChild(info);
                if (conv.unread_count > 0) {
                    const dot = document.createElement('div');
                    dot.className = 'conv-unread-dot';
                    item.appendChild(dot);
                }

                list.appendChild(item);
            });

            const pill = document.getElementById('msgUnreadPill');
            if (totalUnread > 0) { pill.textContent = totalUnread + ' new'; pill.style.display = ''; }
            else { pill.style.display = 'none'; }

            // Open first conversation automatically
            if (data.conversations.length > 0) openConv(data.conversations[0].id);
        })
        .catch(err => console.error('Failed to load conversations:', err));
}

// Open a conversation and load its messages
function openConv(convId) {
    activeConvId = convId;

    document.querySelectorAll('.conv-item').forEach(el => {
        el.classList.toggle('active', parseInt(el.dataset.convId) === convId);
        if (parseInt(el.dataset.convId) === convId) {
            const dot = el.querySelector('.conv-unread-dot');
            if (dot) dot.remove();
        }
    });

    fetch(`/patients/messages/${convId}/`, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
        .then(r => r.json())
        .then(data => {
            // Update header
            const convItem = document.querySelector(`.conv-item[data-conv-id="${convId}"]`);
            if (convItem) {
                document.getElementById('chatHeaderAvatar').style.background = convColor(convId);
                document.getElementById('chatHeaderAvatar').textContent = convItem.querySelector('.conv-avatar').textContent;
                document.getElementById('chatHeaderName').textContent = convItem.querySelector('.conv-name').textContent;
            }

            renderMessages(data.messages);
        })
        .catch(err => console.error('Failed to open conversation:', err));
}

// Render messages in the chat window
function renderMessages(messages) {
    const container = document.getElementById('chatMessages');
    container.innerHTML = '';

    messages.forEach(msg => {
        const row = document.createElement('div');
        row.className = 'msg-bubble-row ' + (msg.from_me ? 'sent' : 'received');

        const avatarEl = document.createElement('div');
        avatarEl.className = 'bubble-avatar';
        avatarEl.style.background = msg.from_me ? '#b0bec5' : convColor(activeConvId);
        avatarEl.textContent = msg.from_me ? MY_INITIAL : msg.sender_initials;

        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = msg.text;

        const timeEl = document.createElement('div');
        timeEl.className = 'bubble-time';
        timeEl.textContent = msg.time;

        row.append(
            ...(msg.from_me ? [timeEl, bubble, avatarEl] : [avatarEl, bubble, timeEl])
        );
        container.appendChild(row);
    });

    container.scrollTop = container.scrollHeight;
}

// Send a message
function sendMessage() {
    const input = document.getElementById('composeInput');
    const text = input.value.trim();
    if (!text || activeConvId === null) return;

    fetch(`/patients/messages/${activeConvId}/send/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': CSRF,
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: JSON.stringify({ text }),
    })
    .then(r => r.json())
    .then(msg => {
        if (msg.error) { console.error(msg.error); return; }

        // Append the new message locally using DOM methods
        const container = document.getElementById('chatMessages');
        const row = document.createElement('div');
        row.className = 'msg-bubble-row sent';

        const timeEl = document.createElement('div');
        timeEl.className = 'bubble-time';
        timeEl.textContent = msg.time;

        const bubble = document.createElement('div');
        bubble.className = 'bubble';
        bubble.textContent = msg.text;

        const avatarEl = document.createElement('div');
        avatarEl.className = 'bubble-avatar';
        avatarEl.style.background = '#b0bec5';
        avatarEl.textContent = MY_INITIAL;

        row.appendChild(timeEl);
        row.appendChild(bubble);
        row.appendChild(avatarEl);
        container.appendChild(row);
        container.scrollTop = container.scrollHeight;

        // Update preview in conv list
        const convItem = document.querySelector(`.conv-item[data-conv-id="${activeConvId}"]`);
        if (convItem) convItem.querySelector('.conv-last').textContent = msg.text;

        input.value = '';
    })
    .catch(err => console.error('Failed to send message:', err));
}

function handleComposeKey(e) {
    if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        sendMessage();
    }
}

// ═══════ JOURNAL ═══════
const journalEntries = [
    {
        date: 'March 2, 2026',
        mood: 7,
        text: 'Had a productive therapy session today. Dr. Thorne helped me work through some of the anxiety around my upcoming presentation at work. We practiced the breathing technique — 4-7-8 — and I actually felt calmer afterward. Going to try it before bed tonight.'
    },
    {
        date: 'March 1, 2026',
        mood: 8,
        text: 'Woke up feeling lighter than usual. Went for a walk in the morning and noticed the trees starting to bud. Small things like that make such a difference. I\'m grateful for the medication adjustment — the side effects from last week seem to have settled.'
    },
    {
        date: 'February 28, 2026',
        mood: 7,
        text: 'Challenging day at work but I managed to use the grounding technique when I felt overwhelmed. Five things I can see, four I can touch... it really does help break the spiral. Journaling before bed is becoming a habit I actually look forward to.'
    },
    {
        date: 'February 27, 2026',
        mood: 8,
        text: 'Group session was really meaningful today. Hearing other people share similar experiences reminds me I\'m not alone in this. One person talked about their journey with panic attacks and it resonated deeply. Made plans to try the art therapy workshop next week.'
    },
    {
        date: 'February 26, 2026',
        mood: 7,
        text: 'Tried cooking a new recipe tonight — something simple but it felt like an accomplishment. My energy levels have been more consistent this week. Going to mention that to Dr. Patel at the next check-in.'
    }
];

function switchJournalTab(tab) {
    document.getElementById('tabWrite').classList.toggle('active', tab === 'write');
    document.getElementById('tabEntries').classList.toggle('active', tab === 'entries');
    document.getElementById('journalWrite').classList.toggle('hidden', tab !== 'write');
    document.getElementById('journalEntries').classList.toggle('hidden', tab !== 'entries');

    if (tab === 'entries') renderEntries();
}

function renderEntries() {
    const container = document.getElementById('journalEntries');
    container.innerHTML = journalEntries.map(e => `
        <div class="journal-entry-card">
            <div class="entry-top">
                <span class="entry-date">${e.date}</span>
                <span class="entry-mood-badge" style="background:${moodColors[e.mood]}20; color:${moodColors[e.mood]};">
                    Mood: ${e.mood}/10
                </span>
            </div>
            <div class="entry-text">${e.text}</div>
        </div>
    `).join('');
}

function insertPrompt(prompt) {
    const ta = document.getElementById('journalText');
    ta.value = ta.value ? ta.value + '\n\n' + prompt + '\n' : prompt + '\n';
    ta.focus();
    updateCharCount();
}

function updateCharCount() {
    const len = document.getElementById('journalText').value.length;
    document.getElementById('charCount').textContent = len + ' character' + (len !== 1 ? 's' : '');
    document.getElementById('journalSaveBtn').disabled = len === 0;
}

function saveJournal() {
    const text = document.getElementById('journalText').value.trim();
    if (!text) return;

    const newEntry = {
        date: 'March 3, 2026',
        mood: selectedMood || null,
        text: text
    };

    journalEntries.unshift(newEntry);
    document.getElementById('journalText').value = '';
    updateCharCount();

    // Show confirmation
    const btn = document.getElementById('journalSaveBtn');
    btn.textContent = '✓ Saved!';
    btn.style.background = 'var(--accent-green)';
    setTimeout(() => {
        btn.textContent = 'Save Entry';
        btn.style.background = '';
    }, 2000);
}

// ═══════ MEETING ALERTS ═══════
const _dismissedMeetings = new Set();

function loadMeetingAlerts() {
    fetch(PATIENT_MEETINGS_URL, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        const container = document.getElementById('meetingAlerts');
        const active = data.meetings.filter(m => !_dismissedMeetings.has(m.id));
        container.innerHTML = '';

        active.forEach(m => {
            const div = document.createElement('div');
            div.className = 'meeting-alert';
            div.id = `meeting-alert-${m.id}`;

            const iconDiv = document.createElement('div');
            iconDiv.className = 'meeting-alert-icon';
            iconDiv.innerHTML = `<svg viewBox="0 0 24 24"><rect x="3" y="4" width="18" height="18" rx="2"/><line x1="16" y1="2" x2="16" y2="6"/><line x1="8" y1="2" x2="8" y2="6"/><line x1="3" y1="10" x2="21" y2="10"/></svg>`;

            const body = document.createElement('div');
            body.className = 'meeting-alert-body';
            const titleDiv = document.createElement('div');
            titleDiv.className = 'meeting-alert-title';
            titleDiv.textContent = 'Upcoming Teams Call: ' + m.title;
            const metaDiv = document.createElement('div');
            metaDiv.className = 'meeting-alert-meta';
            metaDiv.textContent = m.doctor_name + ' · ' + m.scheduled_fmt;
            body.appendChild(titleDiv);
            body.appendChild(metaDiv);

            const actions = document.createElement('div');
            actions.className = 'meeting-alert-actions';
            if (m.join_url) {
                const joinLink = document.createElement('a');
                joinLink.href = escapeHtml(m.join_url);
                joinLink.target = '_blank';
                joinLink.className = 'btn-join-meeting';
                joinLink.textContent = 'Join Call';
                actions.appendChild(joinLink);
            }
            const dismissBtn = document.createElement('button');
            dismissBtn.className = 'btn-dismiss-meeting';
            dismissBtn.textContent = 'Dismiss';
            dismissBtn.dataset.meetingId = m.id;
            dismissBtn.onclick = () => dismissMeetingAlert(m.id);
            actions.appendChild(dismissBtn);

            div.appendChild(iconDiv);
            div.appendChild(body);
            div.appendChild(actions);
            container.appendChild(div);
        });
    })
    .catch(err => console.error('Failed to load meeting alerts:', err));
}

function dismissMeetingAlert(id) {
    _dismissedMeetings.add(id);
    const el = document.getElementById(`meeting-alert-${id}`);
    if (el) el.remove();
}

// ═══════ APPOINTMENTS ═══════
const APPT_COLORS = ['#6d9ba0','#5a8f6e','#c4956a','#5b8ec4','#9b7db8'];
function apptColor(str) {
    let h = 0;
    for (let i = 0; i < str.length; i++) h = str.charCodeAt(i) + ((h << 5) - h);
    return APPT_COLORS[Math.abs(h) % APPT_COLORS.length];
}

function loadAppointments() {
    fetch(PATIENT_APPOINTMENTS_URL, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        const list = document.getElementById('apptList');
        const pill = document.getElementById('apptCount');
        const appts = data.appointments;

        pill.textContent = appts.length ? `${appts.length} upcoming` : 'None';

        if (appts.length === 0) {
            list.innerHTML = '<div class="appt-loading">No upcoming appointments.</div>';
            return;
        }

        list.innerHTML = appts.map(a => {
            const initials = escapeHtml(a.doctor_name.replace('Dr. ','').split(' ').map(w => w[0]).join('').slice(0,2).toUpperCase());
            const color = apptColor(a.doctor_name);
            return `
                <div class="appt-item">
                    <div class="appt-avatar" style="background:${color};">${initials}</div>
                    <div class="appt-details">
                        <div class="appt-name">${escapeHtml(a.doctor_name)}</div>
                        <div class="appt-type">${escapeHtml(a.type_display)}</div>
                    </div>
                    <div class="appt-time">${escapeHtml(a.scheduled_fmt)}</div>
                </div>
            `;
        }).join('');
    })
    .catch(err => console.error('Failed to load appointments:', err));
}

// ═══════ APPOINTMENT REQUESTS ═══════
let reqDoctorsLoaded = false;

function openRequestModal() {
    document.getElementById('reqApptOverlay').classList.add('open');
    document.getElementById('rFeedback').className = 'req-feedback';
    if (!reqDoctorsLoaded) loadReqDoctors();
}

function closeRequestModal() {
    document.getElementById('reqApptOverlay').classList.remove('open');
}

function loadReqDoctors() {
    fetch('/receptionist/api/doctors/', { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        const sel = document.getElementById('rDoctor');
        data.doctors.forEach(d => {
            const opt = document.createElement('option');
            opt.value = d.id;
            opt.textContent = d.name;
            sel.appendChild(opt);
        });
        reqDoctorsLoaded = true;
    })
    .catch(err => console.error('Failed to load doctors:', err));
}

function submitRequest() {
    const btn = document.getElementById('rSubmitBtn');
    const fb  = document.getElementById('rFeedback');
    btn.disabled = true;
    fb.className = 'req-feedback';

    const payload = {
        appointment_type:    document.getElementById('rType').value,
        preferred_doctor_id: document.getElementById('rDoctor').value || null,
        preferred_date:      document.getElementById('rDate').value || null,
        preferred_time:      document.getElementById('rTime').value || null,
        notes:               document.getElementById('rNotes').value.trim(),
    };

    fetch(APPOINTMENT_REQUEST_URL, {
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
            fb.textContent = 'Request sent! The reception team will confirm your appointment.';
            fb.className = 'req-feedback success';
            document.getElementById('rType').value = 'consultation';
            document.getElementById('rDoctor').value = '';
            document.getElementById('rDate').value = '';
            document.getElementById('rTime').value = '';
            document.getElementById('rNotes').value = '';
            // Refresh history if visible
            if (document.getElementById('reqHistoryPanel').style.display !== 'none') {
                loadRequestHistory();
            }
            setTimeout(closeRequestModal, 1800);
        } else {
            fb.textContent = data.error || 'Something went wrong.';
            fb.className = 'req-feedback error';
        }
    })
    .catch(() => {
        btn.disabled = false;
        fb.textContent = 'Network error — please try again.';
        fb.className = 'req-feedback error';
    });
}

let reqHistoryOpen = false;

function toggleRequestHistory() {
    reqHistoryOpen = !reqHistoryOpen;
    document.getElementById('reqHistoryPanel').style.display = reqHistoryOpen ? 'block' : 'none';
    document.getElementById('reqHistoryArrow').textContent = reqHistoryOpen ? '▴' : '▾';
    if (reqHistoryOpen) loadRequestHistory();
}

function loadRequestHistory() {
    fetch(APPOINTMENT_REQUESTS_LIST_URL, { headers: { 'X-Requested-With': 'XMLHttpRequest' } })
    .then(r => r.json())
    .then(data => {
        const el = document.getElementById('reqHistoryList');
        if (data.requests.length === 0) {
            el.innerHTML = '<div class="req-history-loading">No requests yet.</div>';
            return;
        }
        el.innerHTML = data.requests.map(r => `
            <div class="req-history-item">
                <div>
                    <div class="req-history-type">${escapeHtml(r.type_display)}</div>
                    <div class="req-history-meta">
                        ${r.preferred_doctor_name ? escapeHtml(r.preferred_doctor_name) + ' · ' : ''}${escapeHtml(r.preferred_fmt)} · ${escapeHtml(r.created_fmt)}
                    </div>
                </div>
                <span class="req-status-${escapeHtml(r.status)}">${escapeHtml(r.status_display)}</span>
            </div>
        `).join('');
    })
    .catch(err => console.error('Failed to load request history:', err));
}

// ═══════ DOM CONTENT LOADED ═══════
document.addEventListener('DOMContentLoaded', function () {
    // Notifications modal
    const modal = document.getElementById('notif-modal');
    const btn = document.getElementById('notif-btn');
    const span = document.getElementsByClassName('close-btn')[0];

    if (btn) {
        btn.onclick = function () {
            modal.style.display = 'block';
        };
    }

    if (span) {
        span.onclick = function () {
            modal.style.display = 'none';
        };
    }

    window.onclick = function (event) {
        if (event.target == modal) {
            modal.style.display = 'none';
        }
    };

    // Request modal overlay close on backdrop click
    const reqOverlay = document.getElementById('reqApptOverlay');
    if (reqOverlay) {
        reqOverlay.addEventListener('click', function (e) {
            if (e.target === this) closeRequestModal();
        });
    }

    // Sidebar nav scroll
    document.querySelectorAll('.nav-item[data-target]').forEach(function (item) {
        item.addEventListener('click', function (e) {
            e.preventDefault();
            const targetId = this.getAttribute('data-target');
            const target = document.getElementById(targetId);
            const wrapper = document.querySelector('.main-wrapper');
            if (target && wrapper) {
                wrapper.scrollTo({ top: target.offsetTop - 20, behavior: 'smooth' });
            }
            document.querySelectorAll('.nav-item').forEach(function (n) { n.classList.remove('active'); });
            this.classList.add('active');
        });
    });

    // Initialize all features
    initMood();
    renderEntries();
    loadConversations();
    loadAppointments();
    loadMeetingAlerts();

    // Responsive chart
    window.addEventListener('resize', renderChart);

    // Poll every 30 seconds for new meetings
    setInterval(loadMeetingAlerts, 30000);
});
