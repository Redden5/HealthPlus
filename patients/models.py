
# Create your models here.
from django.db import models
from django.conf import settings
from .constants import BLOOD_TYPE_CHOICES


class PatientProfile(models.Model):
    # Link to the User account
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)

    # Fields for person
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    height = models.CharField(max_length=10, blank=True)
    weight = models.CharField(max_length=10, blank=True)
    blood_type = models.CharField(max_length=5, choices= BLOOD_TYPE_CHOICES,blank=True)
    date_of_birth = models.DateField(null=True, blank=True)
    allergies = models.TextField(blank=True)
    medical_conditions = models.TextField(blank=True)

    #Fields for Preference View
    # Communication Preferences
    phone_number = models.CharField(max_length=15)
    email = models.EmailField(max_length=254)
    email_notifications = models.BooleanField(default=False)
    sms_alerts = models.BooleanField(default=False)
    lab_result_alerts = models.BooleanField(default=False)
    prescription_alerts = models.BooleanField(default=False)
    notification_frequency = models.CharField(max_length=50, default='Daily Summary')

    # Health Tracking
    track_weight = models.BooleanField(default=False)
    track_blood_pressure = models.BooleanField(default=False)

    # Accessibility
    large_text_mode = models.BooleanField(default=False)
    preferred_language = models.CharField(max_length=50, default='English')

    #Consent terms
    terms_agreed = models.BooleanField(default=False)
    private_policy = models.BooleanField(default=False)
    electronic_policy = models.BooleanField(default=False)

    #Mood Tracking (see MoodEntry)


    def __str__(self):
        return f"{self.user.username}'s Profile"

class MoodEntry(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='mood_entries')
    score = models.PositiveSmallIntegerField()          # 1–10
    note = models.TextField(blank=True)
    logged_at = models.DateTimeField(auto_now_add=True)
    date = models.DateField()                           # one entry per day enforced in the view

    class Meta:
        ordering = ['date']
        unique_together = ('patient', 'date')

    def __str__(self):
        return f"{self.patient} — {self.date}: {self.score}/10"


# Messaging
class Conversation(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE, related_name='conversations')
    participant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        unique_together = ('patient', 'participant')

    def __str__(self):
        return f"{self.patient} ↔ {self.participant.get_full_name() or self.participant.username}"

    def unread_count(self, for_user):
        return self.messages.filter(is_read=False).exclude(sender=for_user).count()


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_messages')
    text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ['timestamp']

    def __str__(self):
        return f"[{self.conversation}] {self.sender.username}: {self.text[:40]}"


#Notifications
class InAppNotification(models.Model):
    patient = models.ForeignKey(PatientProfile, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)  # e.g., "New Lab Result"
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField()

    def __str__(self):
        return f"Notification for {self.patient.user.username}: {self.title}"

