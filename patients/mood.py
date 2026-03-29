import json
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .models import MoodEntry, PatientProfile

MOOD_LABELS = {
    1: 'Very Low',
    2: 'Low',
    3: 'Struggling',
    4: 'Difficult',
    5: 'Neutral',
    6: 'Okay',
    7: 'Good',
    8: 'Great',
    9: 'Wonderful',
    10: 'Excellent',
}


def _get_profile(user):
    return PatientProfile.objects.get(user=user)


@login_required
@require_POST
def log_mood(request):
    """POST  /patients/mood/log/
    Body (JSON): { "score": 1-10, "note": "optional text" }
    Creates or updates today's mood entry for the logged-in patient.
    Returns the saved entry as JSON.
    """
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    score = body.get('score')
    if not isinstance(score, int) or not (1 <= score <= 10):
        return JsonResponse({'error': 'score must be an integer between 1 and 10'}, status=400)

    note = str(body.get('note', '')).strip()
    profile = _get_profile(request.user)
    today = date.today()

    entry, created = MoodEntry.objects.update_or_create(
        patient=profile,
        date=today,
        defaults={'score': score, 'note': note},
    )

    return JsonResponse({
        'ok': True,
        'created': created,
        'entry': {
            'date': entry.date.isoformat(),
            'score': entry.score,
            'label': MOOD_LABELS[entry.score],
            'note': entry.note,
        },
    })


@login_required
@require_GET
def get_mood_history(request):
    """GET  /patients/mood/history/?days=30
    Returns the patient's mood entries for the last N days (default 30).
    Missing days are returned as null so the chart always has a full date range.
    """
    try:
        days = max(1, min(int(request.GET.get('days', 30)), 365))
    except (TypeError, ValueError):
        days = 30

    profile = _get_profile(request.user)
    today = date.today()
    start = today - timedelta(days=days - 1)

    entries = {
        e.date: e
        for e in MoodEntry.objects.filter(patient=profile, date__gte=start)
    }

    result = []
    for i in range(days):
        d = start + timedelta(days=i)
        entry = entries.get(d)
        result.append({
            'date': d.isoformat(),
            'label': d.strftime('%b %-d'),
            'score': entry.score if entry else None,
            'mood_label': MOOD_LABELS.get(entry.score) if entry else None,
        })

    return JsonResponse({'history': result, 'days': days})


@login_required
@require_GET
def get_mood_stats(request):
    """GET  /patients/mood/stats/
    Returns today's mood score and the 7-day rolling average.
    """
    profile = _get_profile(request.user)
    today = date.today()
    week_start = today - timedelta(days=6)

    today_entry = MoodEntry.objects.filter(patient=profile, date=today).first()
    week_entries = MoodEntry.objects.filter(patient=profile, date__gte=week_start)

    scores = [e.score for e in week_entries]
    avg = round(sum(scores) / len(scores), 1) if scores else None

    return JsonResponse({
        'today': {
            'score': today_entry.score if today_entry else None,
            'label': MOOD_LABELS.get(today_entry.score) if today_entry else None,
            'logged': today_entry is not None,
        },
        'week_avg': avg,
        'week_entries': len(scores),
    })
