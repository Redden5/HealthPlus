"""
Receptionist appointment API + patient-facing appointment list.
All endpoints require the user to belong to the 'Receptionist' group.
"""
import json
import functools

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views.decorators.http import require_GET, require_POST

from doctor.models import DoctorProfile
from patients.models import PatientProfile
from patients.services import trigger_full_notification
from .models import Appointment, AppointmentRequest, ReceptionistProfile


# ── Auth helper ──────────────────────────────────────────────────────────────

def receptionist_required(view):
    @login_required
    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.groups.filter(name='Receptionist').exists():
            return JsonResponse({'error': 'Forbidden'}, status=403)
        return view(request, *args, **kwargs)
    return wrapper


def _receptionist(user):
    profile, _ = ReceptionistProfile.objects.get_or_create(
        user=user,
        defaults={
            'first_name': user.first_name or user.username,
            'last_name':  user.last_name or '',
            'email':      user.email or '',
        },
    )
    return profile


# ── Doctor & Patient lists ───────────────────────────────────────────────────

@receptionist_required
@require_GET
def list_doctors(request):
    """GET /receptionist/api/doctors/"""
    doctors = DoctorProfile.objects.all().order_by('last_name', 'first_name')
    return JsonResponse({'doctors': [
        {'id': d.id, 'name': f"Dr. {d.first_name} {d.last_name}", 'email': d.email}
        for d in doctors
    ]})


@receptionist_required
@require_GET
def list_patients(request):
    """GET /receptionist/api/patients/"""
    patients = PatientProfile.objects.all().order_by('last_name', 'first_name')
    return JsonResponse({'patients': [
        {'id': p.id, 'name': f"{p.first_name} {p.last_name}", 'email': p.email}
        for p in patients
    ]})


# ── Appointments CRUD ────────────────────────────────────────────────────────

@receptionist_required
@require_GET
def list_appointments(request):
    """GET /receptionist/api/appointments/?status=scheduled&date=2026-03-28"""
    qs = Appointment.objects.select_related('doctor', 'patient').all()

    status_filter = request.GET.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    date_filter = request.GET.get('date')
    if date_filter:
        qs = qs.filter(scheduled_at__date=date_filter)

    return JsonResponse({'appointments': [_serialize(a) for a in qs]})


@receptionist_required
@require_POST
def create_appointment(request):
    """POST /receptionist/api/appointments/create/"""
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    errors = {}
    doctor_id    = body.get('doctor_id')
    patient_id   = body.get('patient_id')
    title        = (body.get('title') or '').strip()
    appt_type      = body.get('appointment_type', Appointment.TYPE_CONSULTATION)
    meeting_format = body.get('meeting_format', Appointment.FORMAT_IN_PERSON)
    scheduled_str  = (body.get('scheduled_at') or '').strip()
    duration       = body.get('duration_minutes', 60)
    location       = (body.get('location') or '').strip()
    notes          = (body.get('notes') or '').strip()

    if not doctor_id:   errors['doctor_id']    = 'Required'
    if not patient_id:  errors['patient_id']   = 'Required'
    if not title:       errors['title']        = 'Required'
    if not scheduled_str: errors['scheduled_at'] = 'Required'

    if errors:
        return JsonResponse({'error': errors}, status=400)

    try:
        doctor = DoctorProfile.objects.get(id=doctor_id)
    except DoctorProfile.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)

    try:
        patient = PatientProfile.objects.get(id=patient_id)
    except PatientProfile.DoesNotExist:
        return JsonResponse({'error': 'Patient not found'}, status=404)

    scheduled_at = parse_datetime(scheduled_str)
    if scheduled_at is None:
        return JsonResponse({'error': 'scheduled_at must be ISO 8601'}, status=400)
    if timezone.is_naive(scheduled_at):
        scheduled_at = timezone.make_aware(scheduled_at)

    receptionist = _receptionist(request.user)

    appt = Appointment.objects.create(
        doctor=doctor,
        patient=patient,
        created_by=receptionist,
        appointment_type=appt_type,
        meeting_format=meeting_format,
        title=title,
        scheduled_at=scheduled_at,
        duration_minutes=int(duration),
        location=location,
        notes=notes,
    )

    # If video, create a TeamsCall so it appears on the doctor's Meetings panel
    if meeting_format == Appointment.FORMAT_VIDEO:
        from doctor.models import TeamsCall
        from doctor.teams import create_teams_meeting
        join_url, teams_id = create_teams_meeting(title, scheduled_at)
        TeamsCall.objects.create(
            doctor=doctor,
            patient=patient,
            title=title,
            scheduled_at=scheduled_at,
            join_url=join_url,
            teams_meeting_id=teams_id,
        )

    # Notify patient
    fmt_time = scheduled_at.strftime('%b %#d, %Y at %#I:%M %p')
    fmt_label = 'video call' if meeting_format == Appointment.FORMAT_VIDEO else 'appointment'
    try:
        trigger_full_notification(
            profile=patient,
            title=f"New Appointment: {title}",
            content=(
                f"You have a new {fmt_label} scheduled with Dr. {doctor.first_name} {doctor.last_name} "
                f"on {fmt_time}."
                + (f" Location: {location}." if location else "")
            ),
            doctor_name=f"Dr. {doctor.first_name} {doctor.last_name}",
        )
    except Exception:
        pass

    return JsonResponse({'ok': True, 'appointment': _serialize(appt)}, status=201)


@receptionist_required
@require_POST
def update_appointment(request, appt_id):
    """POST /receptionist/api/appointments/<id>/update/"""
    try:
        appt = Appointment.objects.select_related('doctor', 'patient').get(id=appt_id)
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    changed_fields = []

    if 'title' in body and body['title'].strip():
        appt.title = body['title'].strip()
        changed_fields.append('title')

    if 'appointment_type' in body:
        appt.appointment_type = body['appointment_type']
        changed_fields.append('appointment_type')

    if 'scheduled_at' in body:
        new_dt = parse_datetime(body['scheduled_at'])
        if new_dt:
            if timezone.is_naive(new_dt):
                new_dt = timezone.make_aware(new_dt)
            appt.scheduled_at = new_dt
            changed_fields.append('scheduled_at')

    if 'duration_minutes' in body:
        appt.duration_minutes = int(body['duration_minutes'])
        changed_fields.append('duration_minutes')

    if 'location' in body:
        appt.location = body['location'].strip()
        changed_fields.append('location')

    if 'notes' in body:
        appt.notes = body['notes'].strip()
        changed_fields.append('notes')

    if 'status' in body:
        appt.status = body['status']
        changed_fields.append('status')

    if changed_fields:
        appt.save(update_fields=changed_fields + ['updated_at'])

        # Notify patient if time or status changed
        if 'scheduled_at' in changed_fields or 'status' in changed_fields:
            fmt_time = appt.scheduled_at.strftime('%b %#d, %Y at %#I:%M %p')
            try:
                trigger_full_notification(
                    profile=appt.patient,
                    title=f"Appointment Updated: {appt.title}",
                    content=(
                        f"Your appointment with Dr. {appt.doctor.first_name} {appt.doctor.last_name} "
                        f"has been updated. New time: {fmt_time}. Status: {appt.get_status_display()}."
                    ),
                    doctor_name=f"Dr. {appt.doctor.first_name} {appt.doctor.last_name}",
                )
            except Exception:
                pass

    return JsonResponse({'ok': True, 'appointment': _serialize(appt)})


@receptionist_required
@require_POST
def cancel_appointment(request, appt_id):
    """POST /receptionist/api/appointments/<id>/cancel/"""
    try:
        appt = Appointment.objects.select_related('doctor', 'patient').get(id=appt_id)
    except Appointment.DoesNotExist:
        return JsonResponse({'error': 'Appointment not found'}, status=404)

    appt.status = Appointment.STATUS_CANCELLED
    appt.save(update_fields=['status', 'updated_at'])

    try:
        trigger_full_notification(
            profile=appt.patient,
            title=f"Appointment Cancelled: {appt.title}",
            content=(
                f"Your appointment with Dr. {appt.doctor.first_name} {appt.doctor.last_name} "
                f"on {appt.scheduled_at.strftime('%b %#d at %#I:%M %p')} has been cancelled."
            ),
            doctor_name=f"Dr. {appt.doctor.first_name} {appt.doctor.last_name}",
        )
    except Exception:
        pass

    return JsonResponse({'ok': True})


# ── Patient-facing ───────────────────────────────────────────────────────────

@login_required
@require_GET
def patient_appointments(request):
    """GET /patients/appointments/  — called from the patient dashboard."""
    from patients.models import PatientProfile as PP
    profile = PP.objects.get(user=request.user)
    now = timezone.now()

    upcoming = Appointment.objects.filter(
        patient=profile,
        scheduled_at__gte=now,
    ).exclude(status__in=[Appointment.STATUS_CANCELLED, Appointment.STATUS_NO_SHOW]) \
     .select_related('doctor') \
     .order_by('scheduled_at')[:10]

    return JsonResponse({'appointments': [
        {
            'id':           a.id,
            'title':        a.title,
            'doctor_name':  f"Dr. {a.doctor.first_name} {a.doctor.last_name}",
            'type_display': a.get_appointment_type_display(),
            'scheduled_at': a.scheduled_at.isoformat(),
            'scheduled_fmt': a.scheduled_at.strftime('%b %#d · %#I:%M %p'),
            'location':     a.location,
            'status':       a.status,
            'status_display': a.get_status_display(),
        }
        for a in upcoming
    ]})


# ── Patient appointment requests ─────────────────────────────────────────────

@login_required
@require_POST
def submit_appointment_request(request):
    """POST /patients/appointments/request/
    Patient submits a request; lands in the receptionist queue as 'pending'.
    """
    from patients.models import PatientProfile as PP
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    profile = PP.objects.get(user=request.user)

    appt_type      = body.get('appointment_type', Appointment.TYPE_CONSULTATION)
    meeting_format = body.get('meeting_format', Appointment.FORMAT_IN_PERSON)
    preferred_date = body.get('preferred_date') or None
    preferred_time = body.get('preferred_time') or None
    doctor_id      = body.get('preferred_doctor_id') or None
    notes          = (body.get('notes') or '').strip()

    preferred_doctor = None
    if doctor_id:
        try:
            preferred_doctor = DoctorProfile.objects.get(id=doctor_id)
        except DoctorProfile.DoesNotExist:
            pass

    from django.utils.dateparse import parse_date, parse_time
    req = AppointmentRequest.objects.create(
        patient=profile,
        preferred_doctor=preferred_doctor,
        appointment_type=appt_type,
        meeting_format=meeting_format,
        preferred_date=parse_date(preferred_date) if preferred_date else None,
        preferred_time=parse_time(preferred_time) if preferred_time else None,
        notes=notes,
    )

    return JsonResponse({'ok': True, 'request': _serialize_request(req)}, status=201)


@login_required
@require_GET
def list_patient_requests(request):
    """GET /patients/appointments/requests/
    Returns the logged-in patient's own requests.
    """
    from patients.models import PatientProfile as PP
    profile = PP.objects.get(user=request.user)
    reqs = AppointmentRequest.objects.filter(patient=profile).select_related('preferred_doctor')
    return JsonResponse({'requests': [_serialize_request(r) for r in reqs]})


# ── Receptionist request queue ────────────────────────────────────────────────

@receptionist_required
@require_GET
def list_requests(request):
    """GET /receptionist/api/requests/  — all pending/recent requests."""
    status_filter = request.GET.get('status', 'pending')
    qs = AppointmentRequest.objects.select_related('patient', 'preferred_doctor')
    if status_filter != 'all':
        qs = qs.filter(status=status_filter)
    return JsonResponse({'requests': [_serialize_request(r) for r in qs]})


@receptionist_required
@require_POST
def book_from_request(request, req_id):
    """POST /receptionist/api/requests/<id>/book/
    Converts a patient request into a confirmed Appointment.
    Body (JSON): same fields as create_appointment, minus patient_id (taken from request).
    """
    try:
        req = AppointmentRequest.objects.select_related('patient', 'preferred_doctor').get(id=req_id)
    except AppointmentRequest.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)

    if req.status != AppointmentRequest.STATUS_PENDING:
        return JsonResponse({'error': 'Request is already processed'}, status=400)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    doctor_id      = body.get('doctor_id')
    title          = (body.get('title') or '').strip()
    scheduled_str  = (body.get('scheduled_at') or '').strip()
    duration       = body.get('duration_minutes', 60)
    location       = (body.get('location') or '').strip()
    notes          = (body.get('notes') or req.notes or '').strip()
    appt_type      = body.get('appointment_type', req.appointment_type)
    meeting_format = req.meeting_format  # carry over from the patient's request

    if not doctor_id or not title or not scheduled_str:
        return JsonResponse({'error': 'doctor_id, title, and scheduled_at are required'}, status=400)

    try:
        doctor = DoctorProfile.objects.get(id=doctor_id)
    except DoctorProfile.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)

    scheduled_at = parse_datetime(scheduled_str)
    if scheduled_at is None:
        return JsonResponse({'error': 'scheduled_at must be ISO 8601'}, status=400)
    if timezone.is_naive(scheduled_at):
        scheduled_at = timezone.make_aware(scheduled_at)

    receptionist = _receptionist(request.user)

    appt = Appointment.objects.create(
        doctor=doctor,
        patient=req.patient,
        created_by=receptionist,
        appointment_type=appt_type,
        meeting_format=meeting_format,
        title=title,
        scheduled_at=scheduled_at,
        duration_minutes=int(duration),
        location=location,
        notes=notes,
    )

    req.status = AppointmentRequest.STATUS_BOOKED
    req.booked_appointment = appt
    req.save(update_fields=['status', 'booked_appointment', 'updated_at'])

    # If video, create a TeamsCall so it appears on the doctor's Meetings panel
    if meeting_format == Appointment.FORMAT_VIDEO:
        from doctor.models import TeamsCall
        from doctor.teams import create_teams_meeting
        join_url, teams_id = create_teams_meeting(title, scheduled_at)
        TeamsCall.objects.create(
            doctor=doctor,
            patient=req.patient,
            title=title,
            scheduled_at=scheduled_at,
            join_url=join_url,
            teams_meeting_id=teams_id,
        )

    fmt_time = scheduled_at.strftime('%b %#d, %Y at %#I:%M %p')
    fmt_label = 'video call' if meeting_format == Appointment.FORMAT_VIDEO else 'appointment'
    try:
        trigger_full_notification(
            profile=req.patient,
            title=f"Appointment Confirmed: {title}",
            content=(
                f"Your {fmt_label} request has been confirmed. "
                f"You have a {fmt_label} with Dr. {doctor.first_name} {doctor.last_name} on {fmt_time}."
                + (f" Location: {location}." if location else "")
            ),
            doctor_name=f"Dr. {doctor.first_name} {doctor.last_name}",
        )
    except Exception:
        pass

    return JsonResponse({'ok': True, 'appointment': _serialize(appt)}, status=201)


@receptionist_required
@require_POST
def decline_request(request, req_id):
    """POST /receptionist/api/requests/<id>/decline/"""
    try:
        req = AppointmentRequest.objects.select_related('patient').get(id=req_id)
    except AppointmentRequest.DoesNotExist:
        return JsonResponse({'error': 'Request not found'}, status=404)

    req.status = AppointmentRequest.STATUS_DECLINED
    req.save(update_fields=['status', 'updated_at'])

    try:
        trigger_full_notification(
            profile=req.patient,
            title="Appointment Request Declined",
            content=(
                f"Your {req.get_appointment_type_display()} request "
                f"could not be accommodated at this time. Please contact the clinic to reschedule."
            ),
            doctor_name="HealthPlus Reception",
        )
    except Exception:
        pass

    return JsonResponse({'ok': True})


def _serialize_request(r):
    return {
        'id':               r.id,
        'patient_name':     f"{r.patient.first_name} {r.patient.last_name}",
        'patient_email':    r.patient.email,
        'patient_id':       r.patient_id,
        'appointment_type': r.appointment_type,
        'type_display':     r.get_appointment_type_display(),
        'meeting_format':   r.meeting_format,
        'format_display':   r.get_meeting_format_display(),
        'preferred_doctor_id':   r.preferred_doctor_id,
        'preferred_doctor_name': f"Dr. {r.preferred_doctor.first_name} {r.preferred_doctor.last_name}" if r.preferred_doctor else None,
        'preferred_date':   r.preferred_date.isoformat() if r.preferred_date else None,
        'preferred_time':   r.preferred_time.strftime('%H:%M') if r.preferred_time else None,
        'preferred_fmt':    _fmt_preferred(r),
        'notes':            r.notes,
        'status':           r.status,
        'status_display':   r.get_status_display(),
        'created_at':       r.created_at.isoformat(),
        'created_fmt':      r.created_at.strftime('%b %#d, %Y'),
    }


def _fmt_preferred(r):
    parts = []
    if r.preferred_date:
        parts.append(r.preferred_date.strftime('%b %#d, %Y'))
    if r.preferred_time:
        parts.append(r.preferred_time.strftime('%#I:%M %p'))
    return ' · '.join(parts) if parts else 'Flexible'


# ── Serializer ───────────────────────────────────────────────────────────────

def _serialize(a):
    return {
        'id':               a.id,
        'title':            a.title,
        'appointment_type': a.appointment_type,
        'type_display':     a.get_appointment_type_display(),
        'meeting_format':   a.meeting_format,
        'format_display':   a.get_meeting_format_display(),
        'scheduled_at':     a.scheduled_at.isoformat(),
        'scheduled_fmt':    a.scheduled_at.strftime('%b %#d, %Y · %#I:%M %p'),
        'duration_minutes': a.duration_minutes,
        'location':         a.location,
        'notes':            a.notes,
        'status':           a.status,
        'status_display':   a.get_status_display(),
        'doctor_id':        a.doctor_id,
        'doctor_name':      f"Dr. {a.doctor.first_name} {a.doctor.last_name}",
        'patient_id':       a.patient_id,
        'patient_name':     f"{a.patient.first_name} {a.patient.last_name}",
        'patient_email':    a.patient.email,
    }
