from django.urls import path
from . import views, meetings, messaging, prescriptions

app_name = 'doctor'

urlpatterns = [
    path('dashboard/', views.doctor_dashboard, name='dashboard'),
    path('profile/<int:doctor_id>/', views.doctor_profile, name='profile_view'),

    # Meetings API
    path('meetings/', meetings.list_meetings, name='meetings_list'),
    path('meetings/create/', meetings.create_meeting, name='meetings_create'),
    path('meetings/<int:meeting_id>/cancel/', meetings.cancel_meeting, name='meetings_cancel'),
    path('meetings/<int:meeting_id>/delete/', meetings.delete_meeting, name='meetings_delete'),

    # Patients & Prescriptions API
    path('patients/', prescriptions.list_patients, name='patients_list'),
    path('patients/<int:patient_id>/prescribe/', prescriptions.prescribe, name='prescribe'),
    path('patients/<int:patient_id>/prescriptions/', prescriptions.patient_prescriptions, name='patient_prescriptions'),
    path('patients/<int:patient_id>/health-records/', prescriptions.patient_health_records, name='patient_health_records'),

    # Messaging API
    path('messages/', messaging.list_conversations, name='messages_list'),
    path('messages/start/', messaging.start_conversation, name='messages_start'),
    path('messages/<int:conv_id>/', messaging.get_messages, name='messages_get'),
    path('messages/<int:conv_id>/send/', messaging.send_message, name='messages_send'),
]