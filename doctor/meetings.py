import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET, require_POST

from patients.models import InAppNotification, PatientProfile
from patients.services import trigger_full_notification
from .models import DoctorProfile, TeamsCall
from .teams import create_teams_meeting


def _doctor(user):
    return DoctorProfile.objects.get(user=user)


@login_required
@require_POST
def create_meeting(request):
    """POST /doctors/meetings/create/
    Body (JSON): { "patient_email": "...", "title": "...", "scheduled_at": "2026-03-28T14:00" }
    1. Looks up the patient by email.
    2. Creates a Teams meeting via MS Graph.
    3. Saves a TeamsCall record.
    4. Creates an InAppNotification on the patient's dashboard.
    5. Fires Courier email/SMS if the patient has external alerts enabled.
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    patient_email = (body.get('patient_email') or '').strip()
    title         = (body.get('title') or '').strip()
    scheduled_str = (body.get('scheduled_at') or '').strip()

    if not patient_email or not title or not scheduled_str:
        return JsonResponse({'error': 'patient_email, title, and scheduled_at are required'}, status=400)

    # Resolve patient
    try:
        patient = PatientProfile.objects.get(email=patient_email)
    except PatientProfile.DoesNotExist:
        return JsonResponse({'error': f'No patient found with email {patient_email}'}, status=404)

    # Parse scheduled_at
    from django.utils.dateparse import parse_datetime
    scheduled_at = parse_datetime(scheduled_str)
    if scheduled_at is None:
        return JsonResponse({'error': 'scheduled_at must be ISO 8601 (e.g. 2026-03-28T14:00)'}, status=400)
    if timezone.is_naive(scheduled_at):
        scheduled_at = timezone.make_aware(scheduled_at)

    doctor = _doctor(request.user)

    # Create the Teams meeting (no-op if MS Graph creds not configured)
    join_url, teams_id = create_teams_meeting(title, scheduled_at)

    call = TeamsCall.objects.create(
        doctor=doctor,
        patient=patient,
        title=title,
        scheduled_at=scheduled_at,
        join_url=join_url,
        teams_meeting_id=teams_id,
    )

    # Notify patient
    formatted_time = scheduled_at.strftime('%b %-d, %Y at %-I:%M %p')
    notif_title   = f"Meeting Scheduled: {title}"
    notif_message = (
        f"Dr. {doctor.first_name} {doctor.last_name} has scheduled a Teams call "
        f"with you on {formatted_time}."
        + (f" Join: {join_url}" if join_url else "")
    )

    trigger_full_notification(
        profile=patient,
        title=notif_title,
        content=notif_message,
        doctor_name=f"Dr. {doctor.first_name} {doctor.last_name}",
    )

    return JsonResponse({
        'ok': True,
        'meeting': _serialize_call(call),
    }, status=201)


@login_required
@require_GET
def list_meetings(request):
    """GET /doctors/meetings/
    Returns all non-cancelled meetings for the logged-in doctor,
    ordered soonest first.
    """
    doctor = _doctor(request.user)
    calls = TeamsCall.objects.filter(doctor=doctor).exclude(status=TeamsCall.STATUS_CANCELLED)
    return JsonResponse({'meetings': [_serialize_call(c) for c in calls]})


@login_required
@require_POST
def cancel_meeting(request, meeting_id):
    """POST /doctors/meetings/<id>/cancel/"""
    doctor = _doctor(request.user)
    try:
        call = TeamsCall.objects.get(id=meeting_id, doctor=doctor)
    except TeamsCall.DoesNotExist:
        return JsonResponse({'error': 'Meeting not found'}, status=404)

    call.status = TeamsCall.STATUS_CANCELLED
    call.save(update_fields=['status'])

    # Notify patient of cancellation
    trigger_full_notification(
        profile=call.patient,
        title=f"Meeting Cancelled: {call.title}",
        content=(
            f"Your Teams call with Dr. {doctor.first_name} {doctor.last_name} "
            f"scheduled for {call.scheduled_at.strftime('%b %-d at %-I:%M %p')} has been cancelled."
        ),
        doctor_name=f"Dr. {doctor.first_name} {doctor.last_name}",
    )

    return JsonResponse({'ok': True})


def _serialize_call(call):
    return {
        'id':           call.id,
        'title':        call.title,
        'scheduled_at': call.scheduled_at.isoformat(),
        'scheduled_fmt': call.scheduled_at.strftime('%b %-d, %Y · %-I:%M %p'),
        'join_url':     call.join_url,
        'status':       call.status,
        'patient_name': f"{call.patient.first_name} {call.patient.last_name}",
        'patient_email': call.patient.email,
    }
