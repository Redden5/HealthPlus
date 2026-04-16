from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404
from django.utils import timezone

from .models import DoctorProfile, TeamsCall
from scheduling.models import Appointment
from receptionist.models import Appointment as ReceptionistAppointment


@login_required
def doctor_dashboard(request):
<<<<<<< HEAD
    if not request.user.groups.filter(name='Doctor').exists():
        return redirect('/patients/dashboard/')

    # This ensures a profile exists even if you haven't made one yet
=======
>>>>>>> 0c7a8b1100ab1d41ebb18949599f65ac0e5b9a50
    profile, created = DoctorProfile.objects.get_or_create(
        user=request.user,
        defaults={
<<<<<<< HEAD
            'first_name': request.user.first_name or 'New',
            'last_name': request.user.last_name or 'Doctor',
=======
            'first_name': request.user.first_name or request.user.username,
            'last_name': request.user.last_name,
>>>>>>> 082d52b (quality of life and small bug)
            'email': request.user.email,
            'phone_number': 0,
            'doctor_id': 0
        }
    )

    today = timezone.localdate()
    now   = timezone.now()

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

    # Upcoming video meetings today
    meetings_today = TeamsCall.objects.filter(
        doctor=profile,
        scheduled_at__date=today,
        scheduled_at__gte=now,
    ).exclude(status=TeamsCall.STATUS_CANCELLED).count()

    context = {
        'profile':          profile,
        'today':            today,
        'today_appointments': today_appointments,
        'patients_today':   len(today_appointments),
        'meetings_today':   meetings_today,
    }

    return render(request, 'doctors/dDashboard.html', context)


@login_required
def doctor_profile(request, doctor_id):
    doctor = get_object_or_404(DoctorProfile, id=doctor_id)
    is_doctor = request.user.groups.filter(name='Doctor').exists()
    return render(request, 'doctors/doctor_profile.html', {'doctor': doctor, 'is_doctor': is_doctor})