from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from .models import DoctorProfile
from scheduling.models import Appointment
from receptionist.models import Appointment as ReceptionistAppointment


@login_required
def doctor_dashboard(request):
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

    today = timezone.localdate()

    # Direct patient bookings (scheduling app)
    sched_appts = list(
        Appointment.objects.filter(
            doctor=profile,
            start_time__date=today,
        ).exclude(status='cancelled').select_related('patient').order_by('start_time')
    )

    # Receptionist-booked appointments
    recept_appts = list(
        ReceptionistAppointment.objects.filter(
            doctor=profile,
            scheduled_at__date=today,
        ).exclude(status='cancelled').select_related('patient').order_by('scheduled_at')
    )

    today_appointments = sorted(sched_appts + recept_appts, key=lambda a: a.start_time)

    context = {
        'profile': profile,
        'today': today,
        'today_appointments': today_appointments,
    }

    return render(request, 'doctors/dDashboard.html', context)


@login_required
def doctor_profile(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    is_doctor = request.user.groups.filter(name='Doctor').exists()
    return render(request, 'doctors/doctor_profile.html', {'doctor': doctor, 'is_doctor': is_doctor})