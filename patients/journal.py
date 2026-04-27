import json
from datetime import date, timedelta

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils.formats import date_format
from django.views.decorators.http import require_GET, require_POST

from .models import JournalEntry, PatientProfile


def _get_profile(user):
    return PatientProfile.objects.get(user=user)


def _entry_payload(entry):
    return {
        'id': entry.id,
        'date': date_format(entry.created_at, 'F j, Y'),
        'created_at': entry.created_at.isoformat(),
        'mood': entry.mood_score,
        'text': entry.text,
    }


@login_required
@require_GET
def list_journal_entries(request):
    profile = _get_profile(request.user)
    entries = JournalEntry.objects.filter(patient=profile)[:50]

    return JsonResponse({
        'entries': [_entry_payload(entry) for entry in entries],
    })


@login_required
@require_POST
def create_journal_entry(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    text = str(body.get('text', '')).strip()
    if not text:
        return JsonResponse({'error': 'Journal text is required'}, status=400)

    mood_score = body.get('mood')
    if mood_score in ('', None):
        mood_score = None
    elif not isinstance(mood_score, int) or not (1 <= mood_score <= 10):
        return JsonResponse({'error': 'mood must be an integer between 1 and 10'}, status=400)

    profile = _get_profile(request.user)
    entry = JournalEntry.objects.create(
        patient=profile,
        text=text,
        mood_score=mood_score,
    )

    return JsonResponse({
        'ok': True,
        'entry': _entry_payload(entry),
    }, status=201)


@login_required
@require_POST
def delete_journal_entry(request, entry_id):
    profile = _get_profile(request.user)
    entry = get_object_or_404(JournalEntry, id=entry_id, patient=profile)
    entry.delete()
    return JsonResponse({'ok': True})


@login_required
@require_GET
def journal_stats(request):
    profile = _get_profile(request.user)
    dates = set(
        JournalEntry.objects.filter(patient=profile)
        .values_list('created_at__date', flat=True)
    )

    streak = 0
    cursor = date.today()
    while cursor in dates:
        streak += 1
        cursor -= timedelta(days=1)

    return JsonResponse({'streak': streak})