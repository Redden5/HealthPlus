from django.urls import path
from . import views, messaging, mood, meetings, journal
from receptionist.appointments import patient_appointments, submit_appointment_request, list_patient_requests
app_name = 'patients'

urlpatterns = [
    path('setup/', views.profile_setup, name='profile_setup'),
    path('preferences/', views.preferences_setup, name='preferences_setup'),
    path('consent/', views.consent_setup, name='consent_setup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('account/', views.account_profile, name='account'),
    path('edit_profile/', views.edit_profile, name='edit_profile'),

    # Messaging API
    path('messages/', messaging.list_conversations, name='list_conversations'),
    path('messages/<int:conv_id>/', messaging.get_messages, name='get_messages'),
    path('messages/<int:conv_id>/send/', messaging.send_message, name='send_message'),

    # Mood API
    path('mood/log/', mood.log_mood, name='mood_log'),
    path('mood/history/', mood.get_mood_history, name='mood_history'),
    path('mood/stats/', mood.get_mood_stats, name='mood_stats'),

    # Journal API
    path('journal/', journal.list_journal_entries, name='journal_entries'),
    path('journal/create/', journal.create_journal_entry, name='journal_create'),

    # Meetings API (patient-side)
    path('meetings/', meetings.get_upcoming_meetings, name='patient_meetings'),

    # Appointments API (patient-side)
    path('appointments/', patient_appointments, name='patient_appointments'),
    path('appointments/request/', submit_appointment_request, name='appointment_request'),
    path('appointments/requests/', list_patient_requests, name='appointment_requests_list'),
]
