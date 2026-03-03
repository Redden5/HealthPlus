
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

    def __str__(self):
        return f"{self.user.username}'s Profile"

