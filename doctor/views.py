from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from patients.models import PatientProfile
from .models import DoctorProfile #

@login_required
def doctor_dashboard(request):
    # This ensures a profile exists even if you haven't made one yet
    profile, created = DoctorProfile.objects.get_or_create(
        user=request.user,
        defaults={
            'first_name': 'New',
            'last_name': 'Doctor',
            'email': request.user.email,
            'phone_number': 0,
            'doctor_id': 0
        }
    )

    context = {
        'profile': profile,
    }

    return render(request, 'doctors/dDashboard.html', context)


from patients.services import trigger_full_notification


def add_lab_result(request, patient_id):
    if request.method == "POST":
        # ... logic to save the lab results to your Lab model ...
        profile = PatientProfile.objects.get(id=patient_id)

        # This sends the Courier Email/SMS AND saves to InAppNotification
        trigger_full_notification(
            profile=profile,
            title="New Lab Result Available",
            content="Your blood work results from March 24th have been processed.",
            doctor_name=request.user.get_full_name()
        )
        return redirect('doctor_dashboard')