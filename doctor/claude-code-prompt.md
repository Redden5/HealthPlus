# Claude Code Prompt: Refactor dDashboard.html

## Context
I have a monolithic Django template (`dDashboard.html`) for a physician dashboard in a Django app called `doctors`. It's ~1,442 lines with all CSS, JS, HTML, and Django template logic in one file. I need you to refactor it for maintainability, security, and correctness. The app uses Django's standard auth, CSRF, and view system. The dashboard has these features: stat cards, schedule meetings (Teams calls), upcoming meetings list, active patient table, messaging panel, prescribe modal, and Rx history modal.

---

## 1. Split the Monolith

Break the single file into:

- **`static/doctors/css/dashboard.css`** — all styles extracted from the `<style>` block and inline `style=` attributes. Convert significant inline styles into proper classes.
- **`static/doctors/js/dashboard.js`** — all JavaScript extracted from the `<script>` blocks.
- **`templates/doctors/dashboard.html`** — the cleaned-up Django template that uses `{% load static %}`, links the external CSS/JS, and uses `{% include %}` partials for each major section.
- **`templates/doctors/partials/`** — create includes for: `_sidebar.html`, `_stats_bar.html`, `_meeting_schedule.html`, `_meeting_list.html`, `_patient_table.html`, `_messaging_panel.html`, `_prescribe_modal.html`, `_rx_history_modal.html`, `_new_conv_modal.html`.

Each partial should be self-contained and receive its data from the parent template's context.

---

## 2. Fix XSS Vulnerabilities (Critical)

The current JS interpolates user data directly into HTML via template literals with no escaping. Fix every instance:

- Create a shared `escapeHtml()` utility function in `dashboard.js`:
  ```js
  function escapeHtml(str) {
      const div = document.createElement('div');
      div.appendChild(document.createTextNode(str));
      return div.innerHTML;
  }
  ```
- Apply it to ALL user-sourced data before inserting into DOM: patient names, emails, conditions, message text, meeting titles, prescription fields, doctor names, etc.
- Audit every `.innerHTML` assignment and template literal that includes dynamic data — there are instances in: `renderPatients()`, `renderMessages()`, `loadMeetings()`, `loadConversations()`, `openRxHistory()`, `openPrescribeModal()`, and `sendMessage()`.
- For the `onclick="openPrescribeModal(${p.id}, '${p.name.replace(...)}')"` pattern, switch to data attributes + event delegation instead of inline handlers with string interpolation.

---

## 3. Fix CSS Issues

- **Remove duplicate `.logo-icon` block** — it's defined identically twice (around lines 58-64 and 76-82). Keep one.
- **Fix font mismatch** — the body declares `font-family: 'DM Sans', sans-serif` but the Google Fonts `<link>` only loads `Inter`. Either: switch body to `'Inter', sans-serif`, or add DM Sans to the Google Fonts import. Also `'Playfair Display'` is referenced but never imported — add it or remove those references.
- **Convert inline styles to classes** — the modals, card overrides, meeting list JS rendering, and Rx history rendering all use heavy inline `style=` attributes. Create proper CSS classes for these patterns.

---

## 4. Fix JavaScript Issues

- **Add `.catch()` error handling** to all fetch chains that currently lack it: `loadMeetings()`, `loadConversations()`, `openConv()`, `loadPatients()`, `openRxHistory()`. Show a user-visible error state (not just `console.error`).
- **Deduplicate color logic** — `PT_COLORS`/`ptColor()` and `CONV_COLORS`/`convColor()` are nearly identical. Merge into one shared utility.
- **Remove hardcoded stat values** — "Patients Today: 18" and "Pending Lab Results: 7" are baked into the HTML while other stats are dynamic. Either:
  - (a) Pass them from the Django view context: `{{ patients_today }}`, `{{ pending_labs }}`, OR
  - (b) Fetch them via an API endpoint like the other stats.
  - Mark them with IDs so JS can update them, same as `statUnreadMessages`.
- **Add message polling** — the messaging panel loads once and goes stale. Add a `setInterval` that calls `loadConversations()` every 15-30 seconds when the messaging section is visible. Also refresh the active conversation if one is open.

---

## 5. Django Template Improvements

- **Replace hardcoded doctor info** — "Dr. Redden" and initial "B" should come from context: `{{ doctor.full_name }}`, `{{ doctor.initials }}`.
- **Replace hardcoded date** — "Today's Schedule - March 3, 2026" should use `{{ today|date:"F j, Y" }}`.
- **Fix inconsistent nav links** — only the Calendar link uses `{% url %}`. Either wire up all nav items to real URLs or use a consistent pattern (JS-based section switching, or real Django views).
- **Use `{% load static %}` properly** for the external CSS/JS files.
- **CSRF token** — keep `const CSRF = '{{ csrf_token }}';` in a small inline `<script>` in the template since it needs Django rendering, but move everything else to the external JS file.

---

## 6. Suggested Django View Context

The view serving this template should provide at minimum:

```python
context = {
    'doctor': request.user.doctor_profile,  # or however your model is set up
    'today': timezone.now().date(),
    'patients_today': patients_today_count,
    'pending_labs': pending_labs_count,
    # meetings and messages are loaded via AJAX, so those are fine
}
```

---

## 7. File Structure After Refactor

```
doctors/
├── static/doctors/
│   ├── css/dashboard.css
│   └── js/dashboard.js
├── templates/doctors/
│   ├── dashboard.html
│   └── partials/
│       ├── _sidebar.html
│       ├── _stats_bar.html
│       ├── _meeting_schedule.html
│       ├── _meeting_list.html
│       ├── _patient_table.html
│       ├── _messaging_panel.html
│       ├── _prescribe_modal.html
│       ├── _rx_history_modal.html
│       └── _new_conv_modal.html
└── views.py  (update context)
```

---

## Priority Order

1. **XSS fixes** — this is a security vulnerability, do it first
2. **Split into separate files** — CSS, JS, template partials
3. **CSS cleanup** — duplicates, font mismatch, inline styles
4. **JS cleanup** — error handling, dedup, hardcoded values
5. **Django context** — dynamic doctor info, date, stats
6. **Polling** — message refresh interval

Don't change the visual design or color scheme. The UI looks good — this is purely a structural and security refactor.
