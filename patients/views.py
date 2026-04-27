import json
from datetime import datetime, timedelta, time

from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, logout, update_session_auth_hash
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_POST

from patients.constants import ALLERGY_LIST, CONDITION_LIST, BLOOD_TYPE_CHOICES
from patients.forms import ConsentForm
from patients.forms import QuickEditForm
from patients.models import PatientProfile
from patients.validators import validate_profile_setup
from doctor.models import DoctorProfile
from scheduling.models import Appointment


def profile_setup(request):
    context = {
        'allergies': ALLERGY_LIST,
        'conditions': CONDITION_LIST,
        'blood_type': BLOOD_TYPE_CHOICES,
    }

    if request.method == 'POST':
        errors = validate_profile_setup(request.POST)

        email = request.POST.get('email', '').strip()
        if User.objects.filter(username=email).exists():
            errors.append('An account with this email already exists.')

        if errors:
            context['errors'] = errors
            context['form'] = ConsentForm(request.POST)
            return render(request, 'patients/profile_setup.html', context)

        password = request.POST.get('password')
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
        )


        #Add the patient to the patients group
        from django.contrib.auth.models import Group
        patient_group, _ = Group.objects.get_or_create(name='Patient')
        user.groups.add(patient_group)

        # Log the user in automatically
        login(request, user)

        profile = PatientProfile.objects.create(
            user=user,
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
            email=email,
            phone_number=request.POST.get('phone', ''),
            height=request.POST.get('height', ''),
            weight=request.POST.get('weight', ''),
            blood_type=request.POST.get('blood_type', ''),
            date_of_birth=request.POST.get('date_of_birth') or None,
            allergies=request.POST.get('allergies_hidden', ''),
            medical_conditions=request.POST.get('medical_conditions', ''),
            terms_agreed=bool(request.POST.get('terms_agreed')),
        )

        return redirect('/patients/preferences/')
    else:
        context['form'] = ConsentForm()

        return render(request, 'patients/profile_setup.html', context)


@login_required()
def preferences_setup(request):
    if request.method == 'POST':
        profile = PatientProfile.objects.get(user=request.user)
        profile.email_notifications = bool(request.POST.get('email_notifications'))
        profile.sms_notifications = bool(request.POST.get('sms_alerts'))
        profile.lab_alert_notifications = bool(request.POST.get('lab_alerts'))
        profile.prescription_alerts = bool(request.POST.get('prescription_alerts'))
        profile.track_weight = bool(request.POST.get('weight_alerts'))
        profile.track_blood_pressure = bool(request.POST.get('blood_pressure'))
        profile.track_activity = bool(request.POST.get('activity_alerts'))
        profile.track_sleep = bool(request.POST.get('sleep_alerts'))
        profile.dark_mode = bool(request.POST.get('dark_mode'))
        profile.save()
        return redirect('/patients/consent/')
    else:
        return render(request, 'patients/preferences_setup.html')


@login_required()
def consent_setup(request):
    profile = PatientProfile.objects.get(user=request.user)
    if request.method == "POST":
        action = request.POST.get('action')
        if action == 'Edit':
            form = QuickEditForm(request.POST, instance=profile)
            if form.is_valid():
                form.save()
                # refresh page

                return redirect('/patients/consent_setup/')
        elif action == 'next':
            profile.terms_agreed = bool(request.POST.get('terms_agreed'))
            profile.private_policy = bool(request.POST.get('private_policy'))
            profile.electronic_policy = bool(request.POST.get('electronic_policy'))
            profile.provider_agreement = bool(request.POST.get('provider_agreement'))
            profile.save()
            return redirect('/patients/dashboard/')
    context = {'consent_form': ConsentForm(), 'profile': profile, 'profile_form': QuickEditForm()
                   }
    return render(request, 'patients/review_consent.html',context)

@login_required
def dashboard(request):
    profile = PatientProfile.objects.get(user=request.user)
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'account':
            return redirect('/patients/account/')

    from receptionist.models import Appointment
    from doctor.models import Prescription
    latest_appt = (
        Appointment.objects
        .filter(patient=profile)
        .exclude(status=Appointment.STATUS_CANCELLED)
        .select_related('doctor')
        .order_by('-scheduled_at')
        .first()
    )
    doctor_name = (
        f"Dr. {latest_appt.doctor.first_name} {latest_appt.doctor.last_name}"
        if latest_appt else None
    )

    prescriptions = (
        Prescription.objects
        .filter(patient=profile)
        .select_related('doctor')
        .order_by('-prescribed_at')
    )

    allergies = [a.strip() for a in profile.allergies.split(',') if a.strip()] if profile.allergies else []
    conditions = [c.strip() for c in profile.medical_conditions.split(',') if c.strip()] if profile.medical_conditions else []

    return render(request, 'patients/dashboard.html', {
        'profile': profile,
        'doctor_name': doctor_name,
        'prescriptions': prescriptions,
        'allergies': allergies,
        'conditions': conditions,
    })


@login_required
def account_profile(request):
    profile = PatientProfile.objects.get(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'go_back':
            return redirect('/patients/dashboard/')
        elif action == 'edit_profile':
            return redirect('/patients/edit_profile/')
        elif action == 'change_password':
            return redirect('/patients/change_password/')
        elif action == 'delete_account':
            user = request.user
            logout(request)
            user.delete()
            return redirect('/accounts/login/')

    return render(request, 'patients/account_profile.html', {'profile': profile})


@login_required
def edit_profile(request):
    profile = PatientProfile.objects.get(user=request.user)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action == 'cancel':
            return redirect('/patients/account/')

        if action == 'save':
            profile.first_name = request.POST.get('first_name', profile.first_name)
            profile.last_name = request.POST.get('last_name', profile.last_name)
            profile.email = request.POST.get('email', profile.email)
            profile.phone_number = request.POST.get('phone', profile.phone_number)
            profile.date_of_birth = request.POST.get('date_of_birth') or profile.date_of_birth
            profile.height = request.POST.get('height', profile.height)
            profile.weight = request.POST.get('weight', profile.weight)
            profile.blood_type = request.POST.get('blood_type', profile.blood_type)
            profile.allergies = request.POST.get('allergies_hidden', profile.allergies)
            profile.medical_conditions = request.POST.get('medical_conditions', profile.medical_conditions)
            profile.save()
            return redirect('/patients/account/')

    context = {
        'profile': profile,
        'blood_types': BLOOD_TYPE_CHOICES,
        'all_allergies': ALLERGY_LIST,
        'conditions': CONDITION_LIST,
    }
    return render(request, 'patients/edit_profile.html', context)


@login_required
@require_POST
def change_password(request):
    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, ValueError):
        return JsonResponse({'error': 'Invalid JSON'}, status=400)

    current = body.get('current_password', '')
    new_pw  = body.get('new_password', '')

    if not request.user.check_password(current):
        return JsonResponse({'error': 'Current password is incorrect.'}, status=400)

    try:
        validate_password(new_pw, request.user)
    except ValidationError as e:
        return JsonResponse({'error': e.messages[0]}, status=400)

    request.user.set_password(new_pw)
    request.user.save()
    update_session_auth_hash(request, request.user)

    return JsonResponse({'ok': True})
