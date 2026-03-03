from django.conf import settings
from django.db import models
User = settings.AUTH_USER_MODEL
# Create your models here.
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
        return f'Dr.{self.first_name} {self.last_name}'