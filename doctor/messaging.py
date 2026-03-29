import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from patients.models import Conversation, Message, PatientProfile


@login_required
@require_GET
def list_conversations(request):
    """
    GET /doctors/messages/
    Returns all conversations where the logged-in doctor is the participant.
    """
    conversations = Conversation.objects.filter(
        participant=request.user
    ).select_related('patient__user')

    data = []
    for conv in conversations:
        last_msg = conv.messages.last()
        patient_name = (
            conv.patient.user.get_full_name() or conv.patient.user.username
        )
        data.append({
            'id': conv.id,
            'patient_name': patient_name,
            'patient_initials': _initials(patient_name),
            'last_message': last_msg.text if last_msg else '',
            'last_time': _format_time(last_msg.timestamp) if last_msg else '',
            'unread_count': conv.unread_count(for_user=request.user),
        })

    return JsonResponse({'conversations': data})


@login_required
@require_GET
def get_messages(request, conv_id):
    """
    GET /doctors/messages/<conv_id>/
    Returns all messages in a conversation (doctor must be the participant).
    Marks unread patient messages as read.
    """
    try:
        conv = Conversation.objects.get(id=conv_id, participant=request.user)
    except Conversation.DoesNotExist:
        return JsonResponse({'error': 'Conversation not found.'}, status=404)

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

    patient_name = conv.patient.user.get_full_name() or conv.patient.user.username
    return JsonResponse({'messages': data, 'patient_name': patient_name})


@login_required
@require_POST
def send_message(request, conv_id):
    """
    POST /doctors/messages/<conv_id>/send/
    Body (JSON): { "text": "..." }
    """
    try:
        conv = Conversation.objects.get(id=conv_id, participant=request.user)
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
    conv.save()

    return JsonResponse({
        'id': msg.id,
        'from_me': True,
        'text': msg.text,
        'time': _format_time(msg.timestamp),
        'sender_initials': _initials(request.user.get_full_name() or request.user.username),
    })


@login_required
@require_POST
def start_conversation(request):
    """
    POST /doctors/messages/start/
    Body (JSON): { "patient_email": "..." }
    Finds or creates a conversation between this doctor and the patient.
    """
    try:
        body = json.loads(request.body)
        patient_email = body.get('patient_email', '').strip()
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    if not patient_email:
        return JsonResponse({'error': 'patient_email is required.'}, status=400)

    try:
        profile = PatientProfile.objects.select_related('user').get(user__email__iexact=patient_email)
    except PatientProfile.DoesNotExist:
        return JsonResponse({'error': 'No patient found with that email.'}, status=404)

    conv, _ = Conversation.objects.get_or_create(
        patient=profile,
        participant=request.user,
    )

    patient_name = profile.user.get_full_name() or profile.user.username
    return JsonResponse({
        'ok': True,
        'conv_id': conv.id,
        'patient_name': patient_name,
        'patient_initials': _initials(patient_name),
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
