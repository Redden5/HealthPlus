import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from .models import Conversation, Message, PatientProfile


@login_required
@require_GET
def list_conversations(request):
    """
    GET /patients/messages/
    Returns all conversations for the logged-in patient, ordered by most recent.
    """
    profile = PatientProfile.objects.get(user=request.user)
    conversations = Conversation.objects.filter(patient=profile).select_related('participant')

    data = []
    for conv in conversations:
        last_msg = conv.messages.last()
        data.append({
            'id': conv.id,
            'participant_name': conv.participant.get_full_name() or conv.participant.username,
            'participant_initials': _initials(conv.participant.get_full_name() or conv.participant.username),
            'last_message': last_msg.text if last_msg else '',
            'last_time': _format_time(last_msg.timestamp) if last_msg else '',
            'unread_count': conv.unread_count(for_user=request.user),
        })

    return JsonResponse({'conversations': data})


@login_required
@require_GET
def get_messages(request, conv_id):
    """
    GET /patients/messages/<conv_id>/
    Returns all messages in a conversation and marks received messages as read.
    """
    profile = PatientProfile.objects.get(user=request.user)
    try:
        conv = Conversation.objects.get(id=conv_id, patient=profile)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found.'}, status=404)

    # Mark incoming messages as read
    conv.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)

    messages = conv.messages.select_related('sender').all()
    data = [
        {
            'id': msg.id,
            'from_me': msg.sender == request.user,
            'text': msg.text,
            'time': _format_time(msg.timestamp),
            'sender_initials': _initials(msg.sender.get_full_name() or msg.sender.username),
        }
        for msg in messages
    ]

    return JsonResponse({'messages': data})


@login_required
@require_POST
def send_message(request, conv_id):
    """
    POST /patients/messages/<conv_id>/send/
    Body (JSON): { "text": "..." }
    Saves the message and returns the saved message data.
    """
    profile = PatientProfile.objects.get(user=request.user)
    try:
        conv = Conversation.objects.get(id=conv_id, patient=profile)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found.'}, status=404)

    try:
        body = json.loads(request.body)
        text = body.get('text', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    if not text:
        return JsonResponse({'error': 'Message text cannot be empty.'}, status=400)

    msg = Message.objects.create(
        conversation=conv,
        sender=request.user,
        text=text,
    )

    # Bump conversation timestamp so it rises to the top of the list
    conv.save()

    return JsonResponse({
        'id': msg.id,
        'from_me': True,
        'text': msg.text,
        'time': _format_time(msg.timestamp),
        'sender_initials': _initials(request.user.get_full_name() or request.user.username),
    })


# ── Helpers ──────────────────────────────────────────────────────────────────

def _initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else '?'


def _format_time(dt) -> str:
    from django.utils import timezone
    from datetime import timedelta

    now = timezone.now()
    if dt.date() == now.date():
        return 'Today ' + dt.strftime('%I:%M %p').lstrip('0')
    if dt.date() == (now - timedelta(days=1)).date():
        return 'Yesterday'
    return dt.strftime('%b %d')
