import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_GET, require_POST

from patients.models import PatientProfile
from .models import DoctorProfile, Prescription


@login_required
@require_GET
def list_patients(request):
    """
    GET /doctors/patients/
    Returns all patient accounts with basic info for the patient list card.
    """
    patients = PatientProfile.objects.select_related('user').order_by('last_name', 'first_name')

    data = []
    for p in patients:
        last_rx = p.prescriptions.first()
        data.append({
            'id': p.id,
            'name': f"{p.first_name} {p.last_name}".strip() or p.user.username,
            'initials': _initials(f"{p.first_name} {p.last_name}".strip() or p.user.username),
            'email': p.email or p.user.email,
            'dob': p.date_of_birth.strftime('%b %d, %Y') if p.date_of_birth else '—',
            'blood_type': p.blood_type or '—',
            'conditions': p.medical_conditions[:60] + ('…' if len(p.medical_conditions) > 60 else '') if p.medical_conditions else '—',
            'last_rx': last_rx.medication if last_rx else '—',
        })

    return JsonResponse({'patients': data})


@login_required
@require_POST
def prescribe(request, patient_id):
    """
    POST /doctors/patients/<patient_id>/prescribe/
    Body (JSON): { medication, dosage, frequency, duration, instructions }
    """
    try:
        doctor = DoctorProfile.objects.get(user=request.user)
    except DoctorProfile.DoesNotExist:
        return JsonResponse({'error': 'Doctor profile not found.'}, status=403)

    try:
        patient = PatientProfile.objects.get(id=patient_id)
    except PatientProfile.DoesNotExist:
        return JsonResponse({'error': 'Patient not found.'}, status=404)

    try:
        body = json.loads(request.body)
    except (json.JSONDecodeError, AttributeError):
        return JsonResponse({'error': 'Invalid JSON body.'}, status=400)

    medication = body.get('medication', '').strip()
    dosage     = body.get('dosage', '').strip()
    frequency  = body.get('frequency', '').strip()

    if not medication or not dosage or not frequency:
        return JsonResponse({'error': 'medication, dosage, and frequency are required.'}, status=400)

    rx = Prescription.objects.create(
        doctor=doctor,
        patient=patient,
        medication=medication,
        dosage=dosage,
        frequency=frequency,
        duration=body.get('duration', '').strip(),
        instructions=body.get('instructions', '').strip(),
    )

    return JsonResponse({
        'ok': True,
        'id': rx.id,
        'medication': rx.medication,
        'prescribed_at': rx.prescribed_at.strftime('%b %d, %Y'),
    })


@login_required
@require_GET
def patient_prescriptions(request, patient_id):
    """
    GET /doctors/patients/<patient_id>/prescriptions/
    Returns prescription history for a patient.
    """
    try:
        patient = PatientProfile.objects.get(id=patient_id)
    except PatientProfile.DoesNotExist:
        return JsonResponse({'error': 'Patient not found.'}, status=404)

    rxs = patient.prescriptions.select_related('doctor').all()
    data = [
        {
            'id': rx.id,
            'medication': rx.medication,
            'dosage': rx.dosage,
            'frequency': rx.frequency,
            'duration': rx.duration or '—',
            'instructions': rx.instructions,
            'doctor': str(rx.doctor),
            'date': rx.prescribed_at.strftime('%b %d, %Y'),
        }
        for rx in rxs
    ]

    return JsonResponse({'prescriptions': data})


@login_required
@require_GET
def patient_health_records(request, patient_id):
    """
    GET /doctors/patients/<patient_id>/health-records/
    Returns full health record for a patient.
    """
    try:
        patient = PatientProfile.objects.get(id=patient_id)
    except PatientProfile.DoesNotExist:
        return JsonResponse({'error': 'Patient not found.'}, status=404)

    rxs = patient.prescriptions.select_related('doctor').all()
    prescriptions = [
        {
            'medication': rx.medication,
            'dosage': rx.dosage,
            'frequency': rx.frequency,
            'duration': rx.duration or '—',
            'instructions': rx.instructions,
            'doctor': str(rx.doctor),
            'date': rx.prescribed_at.strftime('%b %d, %Y'),
        }
        for rx in rxs
    ]

    return JsonResponse({
        'id': patient.id,
        'name': f"{patient.first_name} {patient.last_name}".strip() or patient.user.username,
        'email': patient.email or patient.user.email,
        'dob': patient.date_of_birth.strftime('%b %d, %Y') if patient.date_of_birth else '—',
        'blood_type': patient.blood_type or '—',
        'height': patient.height or '—',
        'weight': patient.weight or '—',
        'allergies': patient.allergies or '—',
        'medical_conditions': patient.medical_conditions or '—',
        'prescriptions': prescriptions,
    })


def _initials(name: str) -> str:
    parts = name.strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[-1][0]).upper()
    return name[:2].upper() if name else '?'
