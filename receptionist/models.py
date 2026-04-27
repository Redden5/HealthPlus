import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models


class ReceptionistProfile(models.Model):
    user       = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=100)
    last_name  = models.CharField(max_length=100)
    email      = models.EmailField()
    phone      = models.CharField(max_length=20, blank=True)

    def __str__(self):
        return f"{self.first_name} {self.last_name} (Receptionist)"


class Appointment(models.Model):
    TYPE_THERAPY      = 'therapy'
    TYPE_MEDICATION   = 'medication'
    TYPE_CONSULTATION = 'consultation'
    TYPE_FOLLOWUP     = 'followup'
    TYPE_ASSESSMENT   = 'assessment'

    TYPE_CHOICES = [
        (TYPE_THERAPY,      'Therapy Session'),
        (TYPE_MEDICATION,   'Medication Check-in'),
        (TYPE_CONSULTATION, 'General Consultation'),
        (TYPE_FOLLOWUP,     'Follow-up'),
        (TYPE_ASSESSMENT,   'Assessment'),
    ]

    STATUS_SCHEDULED  = 'scheduled'
    STATUS_CONFIRMED  = 'confirmed'
    STATUS_COMPLETED  = 'completed'
    STATUS_CANCELLED  = 'cancelled'
    STATUS_NO_SHOW    = 'no_show'

    STATUS_CHOICES = [
        (STATUS_SCHEDULED, 'Scheduled'),
        (STATUS_CONFIRMED, 'Confirmed'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
        (STATUS_NO_SHOW,   'No Show'),
    ]

    FORMAT_IN_PERSON = 'in_person'
    FORMAT_VIDEO     = 'video'
    FORMAT_CHOICES   = [
        (FORMAT_IN_PERSON, 'In Person'),
        (FORMAT_VIDEO,     'Video'),
    ]

    doctor           = models.ForeignKey('doctor.DoctorProfile', on_delete=models.CASCADE, related_name='appointments')
    patient          = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE, related_name='appointments')
    created_by       = models.ForeignKey(ReceptionistProfile, on_delete=models.SET_NULL, null=True, related_name='created_appointments')

    appointment_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default=TYPE_CONSULTATION)
    meeting_format   = models.CharField(max_length=10, choices=FORMAT_CHOICES, default=FORMAT_IN_PERSON)
    title            = models.CharField(max_length=200)
    scheduled_at     = models.DateTimeField()
    duration_minutes = models.PositiveSmallIntegerField(default=60)
    location         = models.CharField(max_length=100, blank=True)
    room_name        = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    notes            = models.TextField(blank=True)
    status                = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_SCHEDULED)
    cancellation_reason   = models.TextField(blank=True)
    is_archived           = models.BooleanField(default=False)
    created_at            = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    @property
    def start_time(self):
        return self.scheduled_at

    @property
    def end_time(self):
        return self.scheduled_at + timedelta(minutes=self.duration_minutes)

    class Meta:
        ordering = ['scheduled_at']

    def __str__(self):
        return f"{self.patient} → Dr. {self.doctor} at {self.scheduled_at:%Y-%m-%d %H:%M}"


class AppointmentRequest(models.Model):
    """A patient-initiated request that lands in the receptionist's queue."""

    STATUS_PENDING   = 'pending'
    STATUS_BOOKED    = 'booked'
    STATUS_DECLINED  = 'declined'

    STATUS_CHOICES = [
        (STATUS_PENDING,  'Pending'),
        (STATUS_BOOKED,   'Booked'),
        (STATUS_DECLINED, 'Declined'),
    ]

    patient          = models.ForeignKey('patients.PatientProfile', on_delete=models.CASCADE, related_name='appointment_requests')
    preferred_doctor = models.ForeignKey('doctor.DoctorProfile', on_delete=models.SET_NULL, null=True, blank=True, related_name='appointment_requests')
    appointment_type = models.CharField(max_length=20, choices=Appointment.TYPE_CHOICES, default=Appointment.TYPE_CONSULTATION)
    meeting_format   = models.CharField(max_length=10, choices=Appointment.FORMAT_CHOICES, default=Appointment.FORMAT_IN_PERSON)
    preferred_date   = models.DateField(null=True, blank=True)
    preferred_time   = models.TimeField(null=True, blank=True)
    notes            = models.TextField(blank=True)
    status           = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    booked_appointment = models.OneToOneField(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name='from_request')
    created_at       = models.DateTimeField(auto_now_add=True)
    updated_at       = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Request by {self.patient} — {self.get_appointment_type_display()} ({self.status})"
