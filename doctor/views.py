from django.contrib.auth.decorators import login_required
from django.shortcuts import render
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

    return render(request, 'doctors/dDashboard.html', context) #