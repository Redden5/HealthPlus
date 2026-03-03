from django.contrib import admin

# Register your models here.
from django.contrib.auth.models import Group
from .models import DoctorProfile

def create_doctor(user, **doctor_data):
    doctor = DoctorProfile.objects.create(user=user, **doctor_data)

    doctor_group, _ = Group.objects.get_or_create(name="Doctor")
    user.groups.add(doctor_group)

    return doctor