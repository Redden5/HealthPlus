from django.contrib import admin
from django.contrib.auth.models import Group
from .models import DoctorProfile

admin.site.register(DoctorProfile)

def create_doctor(user, **doctor_data):
    doctor = DoctorProfile.objects.create(user=user, **doctor_data)

    doctor_group, _ = Group.objects.get_or_create(name="Doctor")
    user.groups.add(doctor_group)

    return doctor