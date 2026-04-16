from django.db import models
from django.conf import settings
from doctor.models import DoctorProfile
from patients.models import PatientProfile

#Appointment is for patient to doctor interaction
class Appointment(models.Model):

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('no_show', 'No Show'),
    ]

    APPOINTMENT_TYPE_CHOICES = [
        ('in_person', 'In Person'),
        ('virtual', 'Virtual'),
        ('phone', 'Phone Call'),
    ]

    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='scheduling_appointments'
    )
    patient = models.ForeignKey(
        PatientProfile,
        on_delete=models.CASCADE,
        related_name='scheduling_appointments'
    )

    title = models.CharField(max_length=255)
    appointment_type = models.CharField(
        max_length=20,
        choices=APPOINTMENT_TYPE_CHOICES,
        default='in_person'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )

    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    notes = models.TextField(blank=True)
    location = models.CharField(max_length=255, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.patient} with {self.doctor} on {self.start_time.strftime("%Y-%m-%d %H:%M")}'

    @property
    def duration_minutes(self):
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    class Meta:
        ordering = ['start_time']

#meeting is for doctor to healthcare pro interactions (Internal Meetings)
class Meeting(models.Model):

    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    RECURRENCE_CHOICES = [
        ('none', 'No Recurrence'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('biweekly', 'Bi-Weekly'),
        ('monthly', 'Monthly'),
    ]

    title = models.CharField(max_length=255)
    doctor = models.ForeignKey(
        DoctorProfile,
        on_delete=models.CASCADE,
        related_name='meetings'
    )
    attendees = models.ManyToManyField(
        DoctorProfile,
        related_name='attending_meetings',
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='scheduled'
    )
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)

    recurrence = models.CharField(
        max_length=20,
        choices=RECURRENCE_CHOICES,
        default='none'
    )
    recurrence_end_date = models.DateField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f'{self.title} - {self.start_time.strftime("%Y-%m-%d %H:%M")}'

    @property
    def duration_minutes(self):
        delta = self.end_time - self.start_time
        return int(delta.total_seconds() / 60)

    class Meta:
        ordering = ['start_time']