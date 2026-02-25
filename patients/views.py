from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required

from patients.constants import ALLERGY_LIST, CONDITION_LIST
from patients.forms import ConsentForm
from patients.models import PatientProfile
from patients.validators import validate_profile_setup


def profile_setup(request):
    context = {
        'allergies': ALLERGY_LIST,
        'conditions': CONDITION_LIST,
    }

    if request.method == 'POST':
        errors = validate_profile_setup(request.POST)

        # Check if email is already taken
        email = request.POST.get('email', '').strip()
        if User.objects.filter(username=email).exists():
            errors.append('An account with this email already exists.')

        if errors:
            context['errors'] = errors
            context['form'] = ConsentForm(request.POST)
            return render(request, 'patients/profile_setup.html', context)

        # Create the User account
        password = request.POST.get('password')
        user = User.objects.create_user(
            username=email,
            email=email,
            password=password,
            first_name=request.POST['first_name'],
            last_name=request.POST['last_name'],
        )

        # Log the user in automatically
        login(request, user)

        # Create the PatientProfile
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

        return redirect('preferences_setup')
    else:
        context['form'] = ConsentForm()

    return render(request, 'patients/profile_setup.html', context)


@login_required
def edit_profile(request):
    profile = PatientProfile.objects.get(user=request.user)
    if request.method == 'POST':
        profile.first_name = request.POST['first_name']
        profile.last_name = request.POST['last_name']
        profile.email = request.POST['email']
        profile.phone_number = request.POST['phone']
        profile.height = request.POST['height']
        profile.weight = request.POST['weight']
        profile.allergies = request.POST['allergies']
        profile.medical_conditions = request.POST['medical_conditions']
        profile.save()


@login_required
def preferences_setup(request):
    return render(request, 'patients/preferences_setup.html')


@login_required
def consent_setup(request):
    if request.method == "POST":
        profile = PatientProfile.objects.get(user=request.user)
        profile.terms_agreed = bool(request.POST.get('terms_agreed'))
        profile.private_policy = bool(request.POST.get('private_policy'))
        profile.electronic_policy = bool(request.POST.get('electronic_policy'))
        profile.save()
        return redirect('dashboard')

    form = ConsentForm()
    return render(request, 'patients/review_consent.html', {'form': form})