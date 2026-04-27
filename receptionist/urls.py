from django.urls import path
from . import views, appointments

app_name = 'receptionist'

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),

    # Receptionist — appointments
    path('api/doctors/',                             appointments.list_doctors,          name='api_doctors'),
    path('api/patients/',                            appointments.list_patients,         name='api_patients'),
    path('api/appointments/',                        appointments.list_appointments,     name='api_appointments_list'),
    path('api/appointments/create/',                 appointments.create_appointment,    name='api_appointments_create'),
    path('api/appointments/<int:appt_id>/update/',   appointments.update_appointment,    name='api_appointments_update'),
    path('api/appointments/<int:appt_id>/cancel/',   appointments.cancel_appointment,    name='api_appointments_cancel'),
    path('api/appointments/<int:appt_id>/archive/',  appointments.archive_appointment,   name='api_appointments_archive'),

    # Receptionist — request queue
    path('api/requests/',                            appointments.list_requests,         name='api_requests_list'),
    path('api/requests/<int:req_id>/book/',          appointments.book_from_request,     name='api_requests_book'),
    path('api/requests/<int:req_id>/decline/',       appointments.decline_request,       name='api_requests_decline'),
]
