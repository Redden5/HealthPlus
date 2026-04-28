from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models import PatientProfile


@login_required
@require_GET
def get_upcoming_meetings(request):
    """GET /patients/meetings/
    Returns the patient's upcoming (non-cancelled) TeamsCall records as JSON,
    used by the patient dashboard to show meeting alerts.
    """
    from doctor.models import TeamsCall

    try:
        profile = PatientProfile.objects.get(user=request.user)
    except PatientProfile.DoesNotExist:
        return JsonResponse({'meetings': []})
    now = timezone.now()

    calls = TeamsCall.objects.filter(
        patient=profile,
        scheduled_at__gte=now,
    ).exclude(status=TeamsCall.STATUS_CANCELLED).select_related('doctor')

    meetings = [
        {
            'id':            c.id,
            'title':         c.title,
            'scheduled_at':  c.scheduled_at.isoformat(),
            'scheduled_fmt': c.scheduled_at.strftime('%b %-d, %Y · %-I:%M %p'),
            'join_url':      c.join_url,
            'status':        c.status,
            'doctor_name':   f"Dr. {c.doctor.first_name} {c.doctor.last_name}",
        }
        for c in calls
    ]

    return JsonResponse({'meetings': meetings})
