from django.conf import settings
from django.db import models

User = settings.AUTH_USER_MODEL


class DoctorProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)

    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone_number = models.IntegerField()
    doctor_id = models.IntegerField()
    accepting_patients = models.BooleanField(default=True)
    send_lab_results = models.BooleanField(default=False)
    has_meeting = models.BooleanField(default=False)

    def __str__(self):
        return f'Dr. {self.first_name} {self.last_name}'


class TeamsCall(models.Model):
    STATUS_SCHEDULED = 'scheduled'
    STATUS_ACTIVE    = 'active'
    STATUS_ENDED     = 'ended'
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_ACTIVE,    'Active'),
        (STATUS_ENDED,     'Ended'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    doctor           = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='calls')
    patient          = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE, related_name='calls')
    title            = models.CharField(max_length=200)
    scheduled_at     = models.DateTimeField()
    join_url         = models.URLField(blank=True)
    teams_meeting_id = models.CharField(max_length=300, blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    created_at       = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f"{self.doctor} → {self.patient} at {self.scheduled_at:%Y-%m-%d %H:%M}"


class Prescription(models.Model):
    doctor       = models.ForeignKey(DoctorProfile, on_delete=models.CASCADE, related_name='prescriptions')
    patient      = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE, related_name='prescriptions')
    medication   = models.CharField(max_length=200)
    dosage       = models.CharField(max_length=100)           # e.g. "500 mg"
    frequency    = models.CharField(max_length=100)           # e.g. "Twice daily"
    duration     = models.CharField(max_length=100, blank=True)  # e.g. "7 days"
    instructions = models.TextField(blank=True)
    prescribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-prescribed_at']

    def __str__(self):
        return f"{self.medication} → {self.patient} by {self.doctor}"