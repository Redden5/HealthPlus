from django.utils import timezone

from .models import InAppNotification
from .notifications import notify_patient

def trigger_full_notification(profile, title, content, doctor_name):
    InAppNotification.objects.create(
        patient=profile,
        title=title,
        message=content,
        created_at=timezone.now(),
    )
    #Check frequency setting
    if profile.notification_frequency == 'none':
        print(f"Notifications suppressed for {profile.user.username}")
        return
    #Trigger courier if external alerts are active
    if profile.email_notifications or profile.sms_notifications:
        notify_patient(profile, title, content, doctor_name)