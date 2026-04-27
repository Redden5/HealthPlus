import time

import jwt
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404

from receptionist.models import Appointment


@login_required
def generate_jitsi_token(request, room_name):
    """GET /patients/jitsi-token/<room_name>/
    Returns a signed JWT for the given Jitsi room.
    Doctors (is_staff) are set as moderators.
    """
    payload = {
        "context": {
            "user": {
                "name": request.user.get_full_name() or request.user.username,
                "email": request.user.email,
                "avatar": "",
            }
        },
        "iss": settings.JITSI_APP_ID,
        "aud": "jitsi",
        "sub": settings.JITSI_DOMAIN,
        "room": room_name,
        "exp": int(time.time()) + 3600,
        "nbf": int(time.time()) - 10,
        "moderator": request.user.is_staff,
    }

    token = jwt.encode(payload, settings.JITSI_APP_SECRET, algorithm="HS256")
    return JsonResponse({"token": token, "room": room_name})


@login_required
def call_room(request, room_name):
    """GET /patients/call/<room_name>/
    Renders the Jitsi call page. Verifies the user belongs to this appointment.
    """
    # Allow access if the user is the patient or the doctor for this appointment
    appointment = Appointment.objects.filter(room_name=room_name).select_related(
        "patient__user", "doctor__user"
    ).first()

    if appointment:
        is_patient = (
            hasattr(appointment.patient, "user") and
            appointment.patient.user == request.user
        )
        is_doctor = (
            hasattr(appointment.doctor, "user") and
            appointment.doctor.user == request.user
        )
        if not (is_patient or is_doctor or request.user.is_staff):
            from django.http import HttpResponseForbidden
            return HttpResponseForbidden("You are not authorized to join this call.")

    return render(request, "patients/call.html", {
        "room_name": room_name,
        "jitsi_domain": settings.JITSI_DOMAIN,
    })