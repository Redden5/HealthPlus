import json
from datetime import datetime, timedelta, time

from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from doctor.models import DoctorProfile
from patients.models import PatientProfile
from receptionist.models import Appointment as ReceptionistAppointment
from .models import Appointment, Meeting



@login_required
def calendar_events(request):
    """JSON endpoint for FullCalendar to fetch events."""
    try:
        doctor_profile = DoctorProfile.objects.get(user=request.user)
    except DoctorProfile.DoesNotExist:
        return JsonResponse({'error': 'Unauthorized'}, status=403)

    events = []

    status_colors = {
        'scheduled': '#5b8ec4',
        'confirmed': '#5a8f6e',
        'completed': '#7a8290',
        'cancelled': '#d46b6b',
        'no_show': '#c4956a',
    }

    # Appointments (doctor ↔ patient)
    appointments = Appointment.objects.filter(
        doctor=doctor_profile
    ).select_related('patient')

    for appt in appointments:
        events.append({
            'id': f'appt-{appt.id}',
            'title': f'{appt.patient.first_name} {appt.patient.last_name}',
            'start': appt.start_time.isoformat(),
            'end': appt.end_time.isoformat(),
            'backgroundColor': status_colors.get(appt.status, '#5b8ec4'),
            'borderColor': status_colors.get(appt.status, '#5b8ec4'),
            'extendedProps': {
                'type': 'appointment',
                'status': appt.get_status_display(),
                'appointment_type': appt.get_appointment_type_display(),
                'location': appt.location,
                'notes': appt.notes,
                'duration': appt.duration_minutes,
            },
        })

    # Receptionist-booked appointments
    for appt in ReceptionistAppointment.objects.filter(doctor=doctor_profile).select_related('patient'):
        events.append({
            'id': f'rappt-{appt.id}',
            'title': f'{appt.patient.first_name} {appt.patient.last_name}',
            'start': appt.scheduled_at.isoformat(),
            'end': appt.end_time.isoformat(),
            'backgroundColor': status_colors.get(appt.status, '#5b8ec4'),
            'borderColor': status_colors.get(appt.status, '#5b8ec4'),
            'extendedProps': {
                'type': 'appointment',
                'status': appt.get_status_display(),
                'appointment_type': appt.get_appointment_type_display(),
                'location': appt.location,
                'notes': appt.notes,
                'duration': appt.duration_minutes,
            },
        })

    # Meetings (where doctor is organizer or attendee)
    meeting_ids_as_organizer = Meeting.objects.filter(
        doctor=doctor_profile
    ).values_list('id', flat=True)
    meeting_ids_as_attendee = Meeting.objects.filter(
        attendees=doctor_profile
    ).values_list('id', flat=True)
    all_meeting_ids = set(list(meeting_ids_as_organizer) + list(meeting_ids_as_attendee))

    for meeting in Meeting.objects.filter(id__in=all_meeting_ids):
        events.append({
            'id': f'meet-{meeting.id}',
            'title': meeting.title,
            'start': meeting.start_time.isoformat(),
            'end': meeting.end_time.isoformat(),
            'backgroundColor': '#c4956a',
            'borderColor': '#c4956a',
            'extendedProps': {
                'type': 'meeting',
                'status': meeting.get_status_display(),
                'location': meeting.location,
                'notes': meeting.notes,
                'recurrence': meeting.get_recurrence_display(),
            },
        })

    return JsonResponse(events, safe=False)


@login_required
def available_slots(request):
    doctor_id = request.GET.get('doctor_id')
    date_str = request.GET.get('date')

    if not doctor_id or not date_str:
        return JsonResponse({'error': 'Missing doctor_id or date'}, status=400)

    try:
        doctor = DoctorProfile.objects.get(id=doctor_id, accepting_patients=True)
    except DoctorProfile.DoesNotExist:
        return JsonResponse({'error': 'Doctor not found'}, status=404)

    try:
        selected_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return JsonResponse({'error': 'Invalid date format'}, status=400)

    slot_duration = timedelta(minutes=30)
    work_start = time(9, 0)
    work_end = time(17, 0)
    all_slots = []
    current = timezone.make_aware(datetime.combine(selected_date, work_start))
    end_of_day = timezone.make_aware(datetime.combine(selected_date, work_end))
    while current + slot_duration <= end_of_day:
        all_slots.append(current)
        current += slot_duration

    booked = Appointment.objects.filter(
        doctor=doctor,
        start_time__date=selected_date,
    ).exclude(status='cancelled').values_list('start_time', 'end_time')

    available = []
    for slot_start in all_slots:
        slot_end = slot_start + slot_duration
        overlap = any(
            slot_start < b_end and slot_end > b_start
            for b_start, b_end in booked
        )
        if not overlap:
