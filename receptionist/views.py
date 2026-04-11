import functools

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from doctor.models import DoctorProfile
from patients.models import PatientProfile
from patients.services import trigger_full_notification

from .models import Appointment, AppointmentRequest, ReceptionistProfile


def receptionist_required(view):
    @login_required
    @functools.wraps(view)
    def wrapper(request, *args, **kwargs):
        if not request.user.groups.filter(name='Receptionist').exists():
            return redirect('/accounts/login/')
        return view(request, *args, **kwargs)
    return wrapper


def _get_receptionist(user):
    profile, _ = ReceptionistProfile.objects.get_or_create(
        user=user,
        defaults={
            'first_name': user.first_name or user.username,
            'last_name':  user.last_name or '',
            'email':      user.email or '',
        },
    )
    return profile


def _notify(profile, title, content, doctor_name):
    try:
        trigger_full_notification(profile=profile, title=title, content=content, doctor_name=doctor_name)
    except Exception:
        pass


@receptionist_required
def dashboard(request):
    profile = _get_receptionist(request.user)

    status_filter = request.GET.get('status', 'all')
    date_filter   = request.GET.get('date', '')
    req_filter    = request.GET.get('req_status', 'pending')

    appts = Appointment.objects.select_related('doctor', 'patient').order_by('scheduled_at')
    if status_filter != 'all':
        appts = appts.filter(status=status_filter)
    if date_filter:
        appts = appts.filter(scheduled_at__date=date_filter)

    today     = timezone.localdate()
    all_appts = Appointment.objects.all()
    stats = {
        'today':     all_appts.filter(scheduled_at__date=today).count(),
        'scheduled': all_appts.filter(status='scheduled').count(),
        'confirmed': all_appts.filter(status='confirmed').count(),
        'cancelled': all_appts.filter(status='cancelled').count(),
    }

    reqs = AppointmentRequest.objects.select_related('patient', 'preferred_doctor').order_by('-created_at')
    if req_filter != 'all':
        reqs = reqs.filter(status=req_filter)
    pending_count = AppointmentRequest.objects.filter(status='pending').count()

    doctors  = DoctorProfile.objects.order_by('last_name', 'first_name')
    patients = PatientProfile.objects.order_by('last_name', 'first_name')

    return render(request, 'receptionist/dashboard.html', {
        'profile':        profile,
        'appointments':   appts,
        'stats':          stats,
        'requests':       reqs,
        'pending_count':  pending_count,
        'doctors':        doctors,
        'patients':       patients,
        'status_filter':  status_filter,
        'date_filter':    date_filter,
        'req_filter':     req_filter,
        'type_choices':   Appointment.TYPE_CHOICES,
        'status_choices': Appointment.STATUS_CHOICES,
    })


@receptionist_required
def create_appointment(request):
    if request.method != 'POST':
        return redirect('/receptionist/dashboard/')

    doctor_id     = request.POST.get('doctor_id', '').strip()
    patient_id    = request.POST.get('patient_id', '').strip()
    title         = request.POST.get('title', '').strip()
    appt_type     = request.POST.get('appointment_type', 'consultation')
    scheduled_str = request.POST.get('scheduled_at', '').strip()
    duration      = request.POST.get('duration_minutes', 60)
    location      = request.POST.get('location', '').strip()
    notes         = request.POST.get('notes', '').strip()

    if not all([doctor_id, patient_id, title, scheduled_str]):
        messages.error(request, 'Doctor, patient, title, and date/time are all required.')
        return redirect('/receptionist/dashboard/')

    try:
        doctor = DoctorProfile.objects.get(id=doctor_id)
    except DoctorProfile.DoesNotExist:
        messages.error(request, 'Doctor not found.')
        return redirect('/receptionist/dashboard/')

    try:
        patient = PatientProfile.objects.get(id=patient_id)
    except PatientProfile.DoesNotExist:
        messages.error(request, 'Patient not found.')
        return redirect('/receptionist/dashboard/')

    scheduled_at = parse_datetime(scheduled_str)
    if not scheduled_at:
        messages.error(request, 'Invalid date/time format.')
        return redirect('/receptionist/dashboard/')
    if timezone.is_naive(scheduled_at):
        scheduled_at = timezone.make_aware(scheduled_at)

    appt = Appointment.objects.create(
        doctor=doctor,
        patient=patient,
        created_by=_get_receptionist(request.user),
        appointment_type=appt_type,
        title=title,
        scheduled_at=scheduled_at,
        duration_minutes=int(duration),
        location=location,
        notes=notes,
    )

    fmt = scheduled_at.strftime('%b %#d, %Y at %#I:%M %p')
    _notify(
        patient,
        f"New Appointment: {title}",
        f"You have a new appointment with Dr. {doctor.first_name} {doctor.last_name} on {fmt}."
        + (f" Location: {location}." if location else ""),
        f"Dr. {doctor.first_name} {doctor.last_name}",
    )

    messages.success(request, f"Appointment booked. {patient.first_name} {patient.last_name} has been notified.")
    return redirect('/receptionist/dashboard/')


@receptionist_required
def update_appointment(request, appt_id):
    if request.method != 'POST':
        return redirect('/receptionist/dashboard/')

    appt = get_object_or_404(Appointment.objects.select_related('doctor', 'patient'), id=appt_id)
    changed = []

    title = request.POST.get('title', '').strip()
    if title:
        appt.title = title
        changed.append('title')

    appt_type = request.POST.get('appointment_type', '')
    if appt_type:
        appt.appointment_type = appt_type
        changed.append('appointment_type')

    status = request.POST.get('status', '')
    if status:
        appt.status = status
        changed.append('status')

    scheduled_str = request.POST.get('scheduled_at', '').strip()
    if scheduled_str:
        dt = parse_datetime(scheduled_str)
        if dt:
            if timezone.is_naive(dt):
                dt = timezone.make_aware(dt)
            appt.scheduled_at = dt
            changed.append('scheduled_at')

    duration = request.POST.get('duration_minutes', '')
    if duration:
        appt.duration_minutes = int(duration)
        changed.append('duration_minutes')

    appt.location = request.POST.get('location', '').strip()
    appt.notes    = request.POST.get('notes', '').strip()
    changed += ['location', 'notes']

    if changed:
        appt.save(update_fields=changed + ['updated_at'])
        if 'scheduled_at' in changed or 'status' in changed:
            fmt = appt.scheduled_at.strftime('%b %#d, %Y at %#I:%M %p')
            _notify(
                appt.patient,
                f"Appointment Updated: {appt.title}",
                f"Your appointment with Dr. {appt.doctor.first_name} {appt.doctor.last_name} "
                f"has been updated. Time: {fmt}. Status: {appt.get_status_display()}.",
                f"Dr. {appt.doctor.first_name} {appt.doctor.last_name}",
            )

    messages.success(request, 'Appointment updated.')
    return redirect('/receptionist/dashboard/')


@receptionist_required
def cancel_appointment(request, appt_id):
    if request.method != 'POST':
        return redirect('/receptionist/dashboard/')

    appt = get_object_or_404(Appointment.objects.select_related('doctor', 'patient'), id=appt_id)
    appt.status = Appointment.STATUS_CANCELLED
    appt.save(update_fields=['status', 'updated_at'])

    _notify(
        appt.patient,
        f"Appointment Cancelled: {appt.title}",
        f"Your appointment with Dr. {appt.doctor.first_name} {appt.doctor.last_name} "
        f"on {appt.scheduled_at.strftime('%b %#d at %#I:%M %p')} has been cancelled.",
        f"Dr. {appt.doctor.first_name} {appt.doctor.last_name}",
    )

    messages.success(request, 'Appointment cancelled.')
    return redirect('/receptionist/dashboard/')


@receptionist_required
def decline_request(request, req_id):
    if request.method != 'POST':
        return redirect('/receptionist/dashboard/')

    req = get_object_or_404(AppointmentRequest.objects.select_related('patient'), id=req_id)
    req.status = AppointmentRequest.STATUS_DECLINED
    req.save(update_fields=['status', 'updated_at'])

    _notify(
        req.patient,
        "Appointment Request Declined",
        f"Your {req.get_appointment_type_display()} request could not be accommodated. "
        f"Please contact the clinic to reschedule.",
        "HealthPlus Reception",
    )

    messages.success(request, 'Request declined.')
    return redirect('/receptionist/dashboard/')


@receptionist_required
def book_from_request(request, req_id):
    if request.method != 'POST':
        return redirect('/receptionist/dashboard/')

    req = get_object_or_404(
        AppointmentRequest.objects.select_related('patient', 'preferred_doctor'), id=req_id
    )

    if req.status != AppointmentRequest.STATUS_PENDING:
        messages.error(request, 'This request has already been processed.')
        return redirect('/receptionist/dashboard/')

    doctor_id     = request.POST.get('doctor_id', '').strip()
    title         = request.POST.get('title', '').strip()
    scheduled_str = request.POST.get('scheduled_at', '').strip()
    duration      = request.POST.get('duration_minutes', 60)
    location      = request.POST.get('location', '').strip()
    notes         = request.POST.get('notes', '').strip() or req.notes
    appt_type     = request.POST.get('appointment_type', req.appointment_type)

    if not all([doctor_id, title, scheduled_str]):
        messages.error(request, 'Doctor, title, and date/time are required.')
        return redirect('/receptionist/dashboard/')

    try:
        doctor = DoctorProfile.objects.get(id=doctor_id)
    except DoctorProfile.DoesNotExist:
        messages.error(request, 'Doctor not found.')
        return redirect('/receptionist/dashboard/')

    scheduled_at = parse_datetime(scheduled_str)
    if not scheduled_at:
        messages.error(request, 'Invalid date/time format.')
        return redirect('/receptionist/dashboard/')
    if timezone.is_naive(scheduled_at):
        scheduled_at = timezone.make_aware(scheduled_at)

    appt = Appointment.objects.create(
        doctor=doctor,
        patient=req.patient,
        created_by=_get_receptionist(request.user),
        appointment_type=appt_type,
        title=title,
        scheduled_at=scheduled_at,
        duration_minutes=int(duration),
        location=location,
        notes=notes,
    )

    req.status = AppointmentRequest.STATUS_BOOKED
    req.booked_appointment = appt
    req.save(update_fields=['status', 'booked_appointment', 'updated_at'])

    fmt = scheduled_at.strftime('%b %#d, %Y at %#I:%M %p')
    _notify(
        req.patient,
        f"Appointment Confirmed: {title}",
        f"Your request has been confirmed. Appointment with Dr. {doctor.first_name} {doctor.last_name} on {fmt}."
        + (f" Location: {location}." if location else ""),
        f"Dr. {doctor.first_name} {doctor.last_name}",
    )

    messages.success(request, 'Appointment booked from request. Patient notified.')
    return redirect('/receptionist/dashboard/')
